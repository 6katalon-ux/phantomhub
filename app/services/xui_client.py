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

    async def test_connection(self) -> Dict[str, Any]:
        """Comprehensive check for admin dashboard test button"""
        base_url = self._get_base_url()
        import time
        t0 = time.time()
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

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": origin,
            "Referer": f"{base_url}/"
        }
        token = config.get("xui_token", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        endpoints = [
            f"{base_url}/panel/api/inbounds/list",
            f"{base_url}/xui/API/inbounds/"
        ]
        if parsed.path and parsed.path != "/":
            endpoints.append(f"{origin}/panel/api/inbounds/list")
            endpoints.append(f"{origin}/xui/API/inbounds/")

        for url in endpoints:
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status in (401, 403):
                        # Session may have expired, re-login once
                        logged, _ = await self.login()
                        if not logged:
                            continue
                        async with session.get(url, headers=headers) as retry_resp:
                            if retry_resp.status == 200:
                                return await retry_resp.json()
                    elif resp.status == 200:
                        data = await resp.json()
                        return data
            except Exception as e:
                logger.warning(f"Error requesting {url}: {e}")

        # If failed, attempt re-login and fallback
        await self.login()
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
        token = config.get("xui_token", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """Fetch details of a single inbound by ID"""
        session = await self._ensure_session()
        base_url = self._get_base_url()
        url = f"{base_url}/panel/api/inbounds/get/{inbound_id}"
        headers = self._get_headers()
        
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("obj")
        except Exception as e:
            logger.error(f"Error fetching inbound {inbound_id}: {e}")
        
        # Fallback search from get_inbounds list
        all_inbounds = await self.get_inbounds()
        if all_inbounds.get("success"):
            for item in all_inbounds.get("obj", []):
                if item.get("id") == inbound_id:
                    return item
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
        Properly handles JSON structures expected by standard 3X-UI.
        """
        session = await self._ensure_session()
        base_url = self._get_base_url()
        url = f"{base_url}/panel/api/inbounds/addClient"

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
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_settings]})
        }

        headers = self._get_headers()
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                text = await resp.text()
                try:
                    data = json.loads(text)
                    if data.get("success"):
                        return True, "Client created successfully"
                    return False, data.get("msg", f"3X-UI Error: {text[:150]}")
                except Exception:
                    if resp.status == 200:
                        return True, "Client created"
                    return False, f"HTTP {resp.status}: {text[:150]}"
        except Exception as e:
            return False, f"Network error adding client: {str(e)}"

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
