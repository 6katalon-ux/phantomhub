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

    def _get_base_url(self) -> str:
        url = str(config.get("xui_url", "http://127.0.0.1:2053")).strip().rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        return url

    def _get_timeout(self) -> aiohttp.ClientTimeout:
        timeout_sec = config.get_int("xui_timeout", 10)
        return aiohttp.ClientTimeout(total=timeout_sec, connect=5)

    def _get_ssl_verify(self) -> bool:
        return config.get_bool("xui_tls_verify", False)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            if self._cookie_jar is None:
                self._cookie_jar = aiohttp.CookieJar(unsafe=True)
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
        session = await self._ensure_session()
        base_url = self._get_base_url()
        username = config.get("xui_username", "admin")
        password = config.get("xui_password", "admin")
        token = config.get("xui_token", "")

        # Test both common login endpoints: /login and /xui/API/inbounds (if token)
        login_url = f"{base_url}/login"
        payload = {"username": username, "password": password}
        headers = {
            "User-Agent": "Mozilla/5.0 (VPN-Store-Backend/1.0)",
            "Accept": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with session.post(login_url, data=payload, headers=headers) as resp:
                text = await resp.text()
                try:
                    data = json.loads(text)
                    if data.get("success") or resp.status == 200:
                        return True, "Login successful"
                    return False, data.get("msg", f"HTTP {resp.status}: {text[:150]}")
                except Exception:
                    # In some panels, 200 OK with session cookie is returned
                    if resp.status == 200:
                        return True, "Login session initialized"
                    return False, f"Unexpected response (HTTP {resp.status}): {text[:150]}"
        except aiohttp.ClientConnectorError as e:
            return False, f"Cannot connect to 3X-UI at {base_url}. Verify server is running and port is open: {e}"
        except Exception as e:
            return False, f"3X-UI connection failed: {str(e)}"

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
            "message": "Connected successfully to 3X-UI panel",
            "latency_ms": duration_ms,
            "inbounds_count": len(inbounds),
            "base_url": base_url
        }

    async def get_inbounds(self) -> Dict[str, Any]:
        """Fetch all inbounds from 3X-UI panel"""
        session = await self._ensure_session()
        base_url = self._get_base_url()

        endpoints = [
            f"{base_url}/panel/api/inbounds/list",
            f"{base_url}/xui/API/inbounds/"
        ]

        for url in endpoints:
            try:
                headers = {"Accept": "application/json"}
                token = config.get("xui_token", "")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                async with session.get(url, headers=headers) as resp:
                    if resp.status == 401 or resp.status == 403:
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

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """Fetch details of a single inbound by ID"""
        session = await self._ensure_session()
        base_url = self._get_base_url()
        url = f"{base_url}/panel/api/inbounds/get/{inbound_id}"
        
        try:
            async with session.get(url) as resp:
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

        try:
            async with session.post(url, json=payload) as resp:
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

        try:
            async with session.post(url, json=payload) as resp:
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

        try:
            async with session.post(url) as resp:
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

        try:
            async with session.get(url) as resp:
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
