import httpx
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .config import settings
from .cache import cache

logger = logging.getLogger("mcp_client")
logging.basicConfig(level=logging.INFO)

class SellerSpriteMCPClient:
    def __init__(self, mcp_url: str = settings.MCP_URL, secret_key: str = settings.MCP_SECRET):
        # Strictly use clean URL, NO secret in query params
        self.mcp_url = mcp_url.split("?")[0].rstrip("/")
        self.secret_key = secret_key
        self.target_url = self.mcp_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "secret-key": self.secret_key
        }

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """Calls an MCP tool securely using HTTP header authentication.
        Returns a standardized envelope.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Check cache
        if use_cache:
            cached_result = cache.get(tool_name, arguments)
            if cached_result is not None:
                logger.info(f"[CACHE HIT] {tool_name} with {json.dumps(arguments, ensure_ascii=False)}")
                if isinstance(cached_result, dict) and "data" in cached_result and "code" in cached_result:
                    extracted_data = cached_result["data"]
                else:
                    extracted_data = cached_result
                return {
                    "status": "ok",
                    "source": "sellersprite_mcp_cache",
                    "fetchedAt": now_iso,
                    "freshnessHours": 0.1,
                    "dataQuality": "high",
                    "data": extracted_data,
                    "error": None
                }

        # Safe logging: never print credentials
        logger.info(f"[MCP REQUEST] calling tool: {tool_name} | args: {json.dumps(arguments, ensure_ascii=False)}")

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
                res_json = resp.json()

                if "error" in res_json:
                    err_msg = str(res_json["error"])
                    logger.error(f"MCP RPC Error: {err_msg}")
                    return {
                        "status": "error",
                        "source": "sellersprite_mcp",
                        "fetchedAt": now_iso,
                        "freshnessHours": 0.0,
                        "dataQuality": "empty",
                        "data": None,
                        "error": err_msg
                    }

                content_list = res_json.get("result", {}).get("content", [])
                if not content_list:
                    return {
                        "status": "unavailable",
                        "source": "sellersprite_mcp",
                        "fetchedAt": now_iso,
                        "freshnessHours": 0.0,
                        "dataQuality": "empty",
                        "data": None,
                        "error": "No content returned from tool"
                    }

                raw_text = content_list[0].get("text", "{}")
                try:
                    business_data = json.loads(raw_text)
                except Exception:
                    business_data = {"raw": raw_text}

                code = business_data.get("code")
                if code == "OK":
                    extracted = business_data.get("data")
                    if use_cache:
                        cache.set(tool_name, arguments, extracted)

                    # Archive raw response to local database for traceability
                    try:
                        from .database import db
                        entity_id = arguments.get("asin") or arguments.get("keyword") or arguments.get("nodeIdPath")
                        if not entity_id and isinstance(arguments.get("request"), dict):
                            req = arguments["request"]
                            entity_id = req.get("asin") or req.get("keyword") or req.get("nodeIdPath")
                        entity_type = "asin" if (arguments.get("asin") or (isinstance(arguments.get("request"), dict) and arguments["request"].get("asin"))) else ("keyword" if (arguments.get("keyword") or (isinstance(arguments.get("request"), dict) and arguments["request"].get("keyword"))) else ("node" if (arguments.get("nodeIdPath") or (isinstance(arguments.get("request"), dict) and arguments["request"].get("nodeIdPath"))) else "general"))
                        db.archive_raw_response(tool_name, json.dumps(arguments, ensure_ascii=False), raw_text, entity_type, str(entity_id) if entity_id else None)
                    except Exception as ex:
                        logger.warning(f"Failed to archive raw response: {ex}")

                    return {
                        "status": "ok",
                        "source": "sellersprite_mcp",
                        "fetchedAt": now_iso,
                        "freshnessHours": 0.0,
                        "dataQuality": "high",
                        "data": extracted,
                        "error": None
                    }
                else:
                    msg = business_data.get("message") or f"MCP Code {code}"
                    return {
                        "status": "unavailable" if code in ("NOT_FOUND", "NO_DATA") else "error",
                        "source": "sellersprite_mcp",
                        "fetchedAt": now_iso,
                        "freshnessHours": 0.0,
                        "dataQuality": "empty",
                        "data": None,
                        "error": msg
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code}")
            return {
                "status": "error",
                "source": "sellersprite_mcp",
                "fetchedAt": now_iso,
                "freshnessHours": 0.0,
                "dataQuality": "empty",
                "data": None,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {str(e)}")
            return {
                "status": "error",
                "source": "sellersprite_mcp",
                "fetchedAt": now_iso,
                "freshnessHours": 0.0,
                "dataQuality": "empty",
                "data": None,
                "error": str(e)
            }

mcp_client = SellerSpriteMCPClient()
