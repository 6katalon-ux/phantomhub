"""
Comprehensive 3X-UI REST API Client.
Compatible with standard 3X-UI, MHSanaei, FranzKafkaYu, and alireza0 forks.
Handles session cookies, token authentication, error recovery, client provisioning,
traffic querying, and real VPN configuration link generation.
"""

import json
import base64
import urllib.parse
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import config
from app.core.logging import logger

class XUIClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cookie_jar: Optional[aiohttp.CookieJar] = None
        self._active_base_url: Optional[str] = None

    def _clean_url(self, raw_url: str) -> str:
        url = str(raw_url).strip().lstrip(".").rstrip("/")
        return url

    def _get_candidate_urls(self) -> List[str]:
        raw = self._clean_url(config.get("xui_url", "http://127.0.0.1:2053"))
        candidates: List[str] = []
        if raw.startswith("http://") or raw.startswith("https://"):
            candidates.append(raw)
            if raw.startswith("http://"):
                candidates.append("https://" + raw[7:])
            elif raw.startswith("https://"):
                candidates.append("http://" + raw[8:])
        else:
            # If domain or port 2053, try https first then http
            candidates.append(f"https://{raw}")
            candidates.append(f"http://{raw}")
        return candidates

    def _get_base_url(self) -> str:
        if self._active_base_url:
            return self._active_base_url
        candidates = self._get_candidate_urls()
        return candidates[0] if candidates else "http://127.0.0.1:2053"

    def _get_timeout(self) -> aiohttp.ClientTimeout:
        timeout_sec = config.get_int("xui_timeout", 12)
        return aiohttp.ClientTimeout(total=timeout_sec, connect=6)

    def _get_ssl_verify(self) -> bool:
        return config.get_bool("xui_tls_verify", False)

    async def _ensure_session(self, reset: bool = False) -> aiohttp.ClientSession:
        if reset and self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        if self._session is None or self._session.closed:
            self._cookie_jar = aiohttp.CookieJar(unsafe=True)
            # ssl=False allows self-signed certificates or domain cert mismatches common on 3X-UI VPS
            connector = aiohttp.TCPConnector(ssl=self._get_ssl_verify())
            self._session = aiohttp.ClientSession(
                cookie_jar=self._cookie_jar,
                connector=connector,
                timeout=self._get_timeout()
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def login(self) -> Tuple[bool, str]:
        """Authenticate with 3X-UI panel and capture session cookie"""
        session = await self._ensure_session(reset=True)
        username = str(config.get("xui_username", "admin")).strip()
        password = str(config.get("xui_password", "admin")).strip()
        token = str(config.get("xui_token", "")).strip()

        candidates = self._get_candidate_urls()
        last_error = ""
        had_403 = False

        for base_url in candidates:
            parsed = urllib.parse.urlsplit(base_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": origin,
                "Referer": f"{base_url}/"
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"

            login_urls = [f"{base_url}/login"]
            if parsed.path and parsed.path != "/":
                # If a subpath was entered e.g. /iMKbdWvTPsp4qgcsyZ, also try root /login if subpath fails
                login_urls.append(f"{origin}/login")

            payload = {"username": username, "password": password}

            for login_url in login_urls:
                # 1. Try form-encoded data
                try:
                    async with session.post(login_url, data=payload, headers=headers) as resp:
                        text = await resp.text()
                        if resp.status == 403:
                            had_403 = True
                            last_error = f"HTTP 403: {text[:150]}"
                        elif resp.status == 200:
                            try:
                                data = json.loads(text)
                                if data.get("success", False):
                                    self._active_base_url = base_url
                                    return True, "Login successful"
                                elif "msg" in data:
                                    last_error = data.get("msg")
                            except Exception:
                                # 200 OK without JSON error -> session cookie established
                                self._active_base_url = base_url
                                return True, "Login session initialized"
                except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError) as conn_err:
                    last_error = f"Connection failed to {login_url}: {conn_err}"
                    continue
                except Exception as e:
                    last_error = str(e)
                    continue

                # 2. Try JSON payload as fallback (some 3X-UI versions expect application/json)
                try:
                    json_headers = dict(headers)
                    json_headers["Content-Type"] = "application/json"
                    async with session.post(login_url, json=payload, headers=json_headers) as resp:
                        text = await resp.text()
                        if resp.status == 403:
                            had_403 = True
                            last_error = f"HTTP 403: {text[:150]}"
                        elif resp.status == 200:
                            try:
                                data = json.loads(text)
                                if data.get("success", False):
                                    self._active_base_url = base_url
                                    return True, "Login successful"
                            except Exception:
                                self._active_base_url = base_url
                                return True, "Login session initialized"
                except Exception:
                    pass

        if had_403:
            return False, (
                "خطا: پاسخ ۴۰۳ (دسترسی غیرمجاز) از 3X-UI دریافت شد. "
                "این خطا در ۹۹٪ مواقع به دلیل اشتباه بودن «نام کاربری» یا «کلمه عبور» پنل 3X-UI است. "
                "لطفاً دقت کنید که حروف کوچک و بزرگ کلمه عبور دقیقاً رعایت شده باشد. "
                "همچنین اگر روی پنل تایید دو مرحله‌ای (2FA) فعال است موقتاً غیرفعال کنید "
                "و در ابتدای آدرس پنل حتماً پروتکل (https:// یا http://) را دقیق وارد نمایید."
            )

        return False, last_error or "عدم امکان برقراری ارتباط با پنل 3X-UI. آدرس و پورت را بررسی کنید."

    async def _test_direct_token(self, token: str) -> Tuple[bool, str, List[Any], str]:
        """Try authenticating with API Token directly on panel/api/inbounds/list without login"""
        candidates = self._get_candidate_urls()
        session = await self._ensure_session()
        last_err = ""
        for base_url in candidates:
            parsed = urllib.parse.urlsplit(base_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": origin,
                "Referer": f"{base_url}/",
                "Authorization": f"Bearer {token}",
                "token": token,
                "X-Token": token
            }
            endpoints = [
                f"{base_url}/panel/api/inbounds/list",
                f"{base_url}/xui/API/inbounds/"
            ]
            if parsed.path and parsed.path != "/":
                endpoints.append(f"{origin}/panel/api/inbounds/list")

            for ep in endpoints:
                for param_payload in [{"token": token}, {}]:
                    try:
                        async with session.get(ep, headers=headers, params=param_payload) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if data.get("success", False):
                                    inbounds = data.get("obj", []) or []
                                    self._active_base_url = base_url
                                    return True, "اتصال با توکن API با موفقیت برقرار شد", inbounds, base_url
                    except Exception as e:
                        last_err = str(e)
        return False, last_err, [], ""

    async def test_connection(self) -> Dict[str, Any]:
        """Comprehensive check for admin dashboard test button"""
        base_url = self._get_base_url()
        token = str(config.get("xui_token", "")).strip()
        import time
        t0 = time.time()

        # 1. If API Token is provided, try direct token authentication first!
        if token:
            ok_token, token_msg, inbounds, active_url = await self._test_direct_token(token)
            if ok_token:
                duration_ms = int((time.time() - t0) * 1000)
                return {
                    "success": True,
                    "message": f"اتصال با موفقیت از طریق توکن API (بدون نیاز به رمز عبور) برقرار گردید ({len(inbounds)} اینباند شناسایی شد)",
                    "latency_ms": duration_ms,
                    "inbounds_count": len(inbounds),
                    "base_url": active_url or base_url
                }

        # 2. Otherwise perform standard session login
        ok, msg = await self.login()
        duration_ms = int((time.time() - t0) * 1000)
        
        if not ok:
            return {
                "success": False,
                "message": msg,
                "latency_ms": duration_ms,
                "inbounds_count": 0,
                "base_url": base_url
            }

        inbounds_res = await self.get_inbounds()
        inbounds = inbounds_res.get("obj", []) if inbounds_res.get("success") else []

        return {
            "success": True,
            "message": f"اتصال به پنل 3X-UI با موفقیت برقرار شد ({len(inbounds)} اینباند شناسایی گردید)",
            "latency_ms": duration_ms,
            "inbounds_count": len(inbounds),
            "base_url": self._get_base_url()
        }

    async def get_inbounds(self) -> Dict[str, Any]:
        """Fetch all inbounds from 3X-UI panel"""
        session = await self._ensure_session()
        base_url = self._get_base_url()
        parsed = urllib.parse.urlsplit(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        headers = self._get_headers()
        token = str(config.get("xui_token", "")).strip()
        params = {"token": token} if token else {}

        endpoints = [
            f"{base_url}/panel/api/inbounds/list",
            f"{base_url}/xui/API/inbounds/"
        ]
        if parsed.path and parsed.path != "/":
            endpoints.append(f"{origin}/panel/api/inbounds/list")
            endpoints.append(f"{origin}/xui/API/inbounds/")

        for url in endpoints:
            for query_params in [params, {}]:
                try:
                    async with session.get(url, headers=headers, params=query_params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success", False) or "obj" in data:
                                return data
                        elif resp.status in (401, 403):
                            # Try re-login if token is not set
                            if not token:
                                logged, _ = await self.login()
                                if logged:
                                    async with session.get(url, headers=headers) as retry_resp:
                                        if retry_resp.status == 200:
                                            return await retry_resp.json()
                except Exception as e:
                    logger.warning(f"Error requesting {url}: {e}")

        return {"success": False, "msg": "Failed to retrieve inbounds list", "obj": []}

    def _get_headers(self) -> Dict[str, str]:
        base_url = self._get_base_url()
        parsed = urllib.parse.urlsplit(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": origin,
            "Referer": f"{base_url}/"
        }
        token = str(config.get("xui_token", "")).strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["token"] = token
            headers["X-Token"] = token
        return headers

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """Fetch details of a single inbound by ID with robust fallbacks"""
        target_str = str(inbound_id).strip()

        # 1. First search via get_inbounds list (most reliable across all 3X-UI forks)
        all_inbounds = await self.get_inbounds()
        inbounds_list = all_inbounds.get("obj", []) if all_inbounds.get("success") else []
        
        if inbounds_list:
            # Exact ID match
            for item in inbounds_list:
                if str(item.get("id")).strip() == target_str or str(item.get("inbound_id")).strip() == target_str:
                    return item
            
            # Port or remark match (in case user entered port like 88 or 443 instead of ID)
            for item in inbounds_list:
                if str(item.get("port")).strip() == target_str:
                    return item
                if str(item.get("tag", "")).strip().lower() == target_str.lower():
                    return item
                if str(item.get("remark", "")).strip().lower() == target_str.lower():
                    return item

        # 2. Try direct /get/:id endpoint as fallback
        session = await self._ensure_session()
        base_url = self._get_base_url()
        token = str(config.get("xui_token", "")).strip()
        params = {"token": token} if token else {}
        headers = self._get_headers()
        url = f"{base_url}/panel/api/inbounds/get/{inbound_id}"
        
        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and data.get("obj"):
                        return data.get("obj")
        except Exception as e:
            logger.error(f"Error fetching inbound {inbound_id}: {e}")

        # 3. Intelligent fallback: if inbounds exist, use the first available active inbound
        if inbounds_list:
            logger.warning(f"Inbound ID {inbound_id} not explicitly found. Auto-selecting first active inbound #{inbounds_list[0].get('id')}")
            return inbounds_list[0]

        return None

    async def add_client(
        self,
        inbound_id: int,
        client_uuid: str,
        email: str,
        total_gb: int,
        expire_time_ms: int,
        max_ips: int = 2,
        flow: str = "xtls-rprx-vision"
    ) -> Tuple[bool, str]:
        """
        Add a client to a specific inbound in 3X-UI.
        Handles both token-based and cookie-based authentication, and URL subpath variations.
        """
        session = await self._ensure_session()
        base_url = self._get_base_url()
        parsed = urllib.parse.urlsplit(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        token = str(config.get("xui_token", "")).strip()
        params = {"token": token} if token else {}

        # 3X-UI expects client settings inside client object
        client_settings = {
            "id": client_uuid,
            "email": email,
            "limitIp": max_ips,
            "totalGB": total_gb * 1024 * 1024 * 1024, # Bytes
            "expiryTime": expire_time_ms,
            "enable": True,
            "tgId": "",
            "subId": client_uuid[:16],
            "flow": flow
        }

        payload = {
            "id": int(inbound_id),
            "settings": json.dumps({"clients": [client_settings]})
        }

        headers = self._get_headers()
        urls_to_try = [f"{base_url}/panel/api/inbounds/addClient"]
        if parsed.path and parsed.path != "/":
            urls_to_try.append(f"{origin}/panel/api/inbounds/addClient")

        last_error = ""
        for target_url in urls_to_try:
            try:
                async with session.post(target_url, json=payload, headers=headers, params=params) as resp:
                    text = await resp.text()
                    try:
                        data = json.loads(text)
                        if data.get("success"):
                            return True, "Client created successfully"
                        last_error = data.get("msg", text[:150])
                    except Exception:
                        if resp.status == 200:
                            return True, "Client created"
                        last_error = f"HTTP {resp.status}: {text[:150]}"
            except Exception as e:
                last_error = f"Network error adding client: {str(e)}"

        return False, last_error or "Failed to add client to 3X-UI"

    async def update_client(
        self,
        inbound_id: int,
        client_uuid: str,
        email: str,
        total_bytes: int,
        expire_time_ms: int,
        enable: bool = True
    ) -> Tuple[bool, str]:
        """Update client quota, expiration, or enable/disable state"""
        session = await self._ensure_session()
        base_url = self._get_base_url()
        url = f"{base_url}/panel/api/inbounds/updateClient/{client_uuid}"

        client_settings = {
            "id": client_uuid,
            "email": email,
            "totalGB": total_bytes,
            "expiryTime": expire_time_ms,
            "enable": enable
        }

        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_settings]})
        }
        headers = self._get_headers()

        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                if data.get("success"):
                    return True, "Client updated"
                return False, data.get("msg", "Update failed")
        except Exception as e:
            return False, str(e)

    async def delete_client(self, inbound_id: int, client_uuid: str) -> Tuple[bool, str]:
        """Delete client from 3X-UI"""
        session = await self._ensure_session()
        base_url = self._get_base_url()
        url = f"{base_url}/panel/api/inbounds/delClient/{inbound_id}/{client_uuid}"
        headers = self._get_headers()

        try:
            async with session.post(url, headers=headers) as resp:
                data = await resp.json()
                if data.get("success"):
                    return True, "Client deleted from 3X-UI"
                return False, data.get("msg", "Delete failed")
        except Exception as e:
            return False, str(e)

    async def get_client_traffic(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve upload, download, and total traffic for a client by email"""
        session = await self._ensure_session()
        base_url = self._get_base_url()
        url = f"{base_url}/panel/api/inbounds/getClientTraffics/{email}"
        headers = self._get_headers()

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("obj")
        except Exception as e:
            logger.warning(f"Failed to fetch traffic for {email}: {e}")
        return None

    def generate_config_link(self, inbound: Dict[str, Any], client_uuid: str, remark: str = "VPNStore") -> str:
        """
        Generate authentic VPN client configuration links (VLESS Reality, VMess, Trojan, etc.)
        strictly reading parameters from the actual 3X-UI inbound configuration.
        """
        protocol = inbound.get("protocol", "vless").lower()
        port = inbound.get("port", 443)
        host = config.get("vpn_server_host", "127.0.0.1")
        
        # Parse streamSettings and settings JSON
        stream = {}
        if isinstance(inbound.get("streamSettings"), str):
            try:
                stream = json.loads(inbound["streamSettings"])
            except Exception:
                stream = {}
        elif isinstance(inbound.get("streamSettings"), dict):
            stream = inbound["streamSettings"]

        network = stream.get("network", "tcp")
        security = stream.get("security", "none")

        clean_remark = urllib.parse.quote(remark.replace(" ", "_"))

        # 1. VLESS Reality Link Generation
        if protocol == "vless":
            params = {}
            if security == "reality":
                params["security"] = "reality"
                reality_settings = stream.get("realitySettings", {})
                
                # Extract real public key and shortIds from inbound
                settings_data = reality_settings.get("settings", {})
                pbk = reality_settings.get("publicKey") or settings_data.get("publicKey", "")
                
                short_ids = reality_settings.get("shortIds") or settings_data.get("shortIds", [])
                sid = short_ids[0] if short_ids else ""
                
                server_names = reality_settings.get("serverNames") or settings_data.get("serverNames", [])
                sni = server_names[0] if server_names else host
                
                fp = reality_settings.get("fingerprint", "chrome")

                params["pbk"] = pbk
                params["fp"] = fp
                params["sni"] = sni
                if sid:
                    params["sid"] = sid
                params["type"] = network
                params["flow"] = "xtls-rprx-vision"
            
            elif security == "tls":
                params["security"] = "tls"
                tls_settings = stream.get("tlsSettings", {})
                params["sni"] = tls_settings.get("serverName", host)
                params["type"] = network

            else:
                params["security"] = "none"
                params["type"] = network

            # Network specific parameters (WebSocket, gRPC, HTTPUpgrade)
            if network == "ws":
                ws_settings = stream.get("wsSettings", {})
                params["path"] = ws_settings.get("path", "/")
                params["host"] = ws_settings.get("headers", {}).get("Host", host)
            elif network == "grpc":
                grpc_settings = stream.get("grpcSettings", {})
                params["serviceName"] = grpc_settings.get("serviceName", "")

            query = urllib.parse.urlencode(params)
            return f"vless://{client_uuid}@{host}:{port}?{query}#{clean_remark}"

        # 2. VMess Link Generation (Standard Base64 JSON format)
        elif protocol == "vmess":
            vmess_obj = {
                "v": "2",
                "ps": remark,
                "add": host,
                "port": str(port),
                "id": client_uuid,
                "aid": "0",
                "scy": "auto",
                "net": network,
                "type": "none",
                "host": "",
                "path": "",
                "tls": "tls" if security == "tls" else "",
                "sni": host if security == "tls" else ""
            }
            if network == "ws":
                ws_settings = stream.get("wsSettings", {})
                vmess_obj["path"] = ws_settings.get("path", "/")
                vmess_obj["host"] = ws_settings.get("headers", {}).get("Host", host)
            
            json_str = json.dumps(vmess_obj)
            b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
            return f"vmess://{b64}"

        # 3. Trojan Link Generation
        elif protocol == "trojan":
            params = {}
            if security == "tls":
                params["security"] = "tls"
                tls_settings = stream.get("tlsSettings", {})
                params["sni"] = tls_settings.get("serverName", host)
            params["type"] = network
            query = urllib.parse.urlencode(params)
            return f"trojan://{client_uuid}@{host}:{port}?{query}#{clean_remark}"

        # Default fallback
        return f"{protocol}://{client_uuid}@{host}:{port}#{clean_remark}"

# Singleton client instance
xui_client = XUIClient()
