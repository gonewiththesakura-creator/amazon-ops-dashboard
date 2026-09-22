import httpx
import json
import logging
from typing import Dict, Any, Optional
from .config import settings
from .cache import cache

logger = logging.getLogger("mcp_client")
logging.basicConfig(level=logging.INFO)

class SellerSpriteMCPClient:
    def __init__(self, mcp_url: str = settings.MCP_URL, secret_key: str = settings.MCP_SECRET):
        self.mcp_url = mcp_url.rstrip("?")
        self.secret_key = secret_key
        # Both header and url param ensure maximum compatibility with SellerSprite endpoint
        self.target_url = f"{self.mcp_url}?secret-key={self.secret_key}"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "secret-key": self.secret_key
        }

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """Calls an MCP tool with caching and returns the parsed business data payload."""
        if use_cache:
            cached_result = cache.get(tool_name, arguments)
            if cached_result is not None:
                logger.info(f"[CACHE HIT] {tool_name} with {arguments}")
                return cached_result

        logger.info(f"[MCP REQUEST] calling {tool_name} with {arguments}")
        payload = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.target_url, headers=self.headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

                if "error" in data:
                    logger.error(f"MCP RPC Error: {data['error']}")
                    return {"code": "ERROR_RPC", "message": str(data["error"])}

                content_list = data.get("result", {}).get("content", [])
                if not content_list:
                    return {"code": "ERROR_EMPTY", "message": "No content in MCP response"}

                raw_text = content_list[0].get("text", "{}")
                try:
                    business_data = json.loads(raw_text)
                except Exception:
                    business_data = {"raw": raw_text}

                if use_cache and business_data.get("code") == "OK":
                    cache.set(tool_name, arguments, business_data)

                return business_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return {"code": f"HTTP_{e.response.status_code}", "message": e.response.text}
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {str(e)}")
            return {"code": "ERROR_EXCEPTION", "message": str(e)}

mcp_client = SellerSpriteMCPClient()
