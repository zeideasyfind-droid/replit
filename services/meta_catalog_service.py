import os
import json
import logging
import httpx
from typing import Any, Dict

logger = logging.getLogger(__name__)

META_CATALOG_ID = os.environ.get("META_CATALOG_ID", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
GRAPH_BASE = "https://graph.facebook.com/v25.0"

# In-memory store: property_id -> {"payload": ..., "response": ...}
_debug_store: Dict[str, Dict[str, Any]] = {}


def _build_item(data: Dict[str, Any]) -> Dict[str, Any]:
    availability = "in stock"
    if str(data.get("availability", "")).lower() in ("sold", "out of stock"):
        availability = "out of stock"

    price_str = f"{data['price']} {data.get('currency', 'INR')}"

    return {
        "id": data["property_id"],
        "title": data["title"],
        "description": data["description"],
        "price": price_str,
        "image_link": data["image_link"],
        "link": f"https://easyfindprops.com/property/{data['property_id']}",
        "availability": availability,
        "condition": "new",
        "brand": "EasyFind Realty Solutions",
    }


async def create_or_update_catalog_item(data: Dict[str, Any]) -> Dict[str, Any]:
    """Push item to Meta catalog via items_batch endpoint. Returns parsed response."""
    item = _build_item(data)
    payload = {
        "item_type": "PRODUCT_ITEM",
        "requests": json.dumps([{"method": "CREATE", "data": item}]),
        "access_token": META_ACCESS_TOKEN,
    }

    # Log sanitized payload (no token)
    sanitized = {k: v for k, v in payload.items() if k != "access_token"}
    logger.info("[Meta] items_batch request: %s", json.dumps(sanitized, indent=2))

    _debug_store.setdefault(data["property_id"], {})["payload"] = sanitized

    url = f"{GRAPH_BASE}/{META_CATALOG_ID}/items_batch"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, data=payload)

    response_json = resp.json()
    # Sanitize response in logs (no tokens)
    logger.info("[Meta] items_batch response (status %d): %s", resp.status_code, json.dumps(response_json))
    _debug_store[data["property_id"]]["response"] = response_json

    if resp.status_code != 200:
        raise RuntimeError(
            f"Meta API error {resp.status_code}: {json.dumps(response_json)}"
        )

    # Check for errors in response handles array
    handles = response_json.get("handles", [])
    if not handles:
        # Try upsert: if method CREATE failed due to existing ID, retry with UPDATE
        errors = response_json.get("validation_status", [])
        if errors:
            logger.warning("[Meta] CREATE may have failed, attempting UPDATE: %s", errors)
            payload["requests"] = json.dumps([{"method": "UPDATE", "data": item}])
            sanitized["requests"] = payload["requests"]
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, data=payload)
            response_json = resp.json()
            logger.info("[Meta] UPDATE response (status %d): %s", resp.status_code, json.dumps(response_json))
            _debug_store[data["property_id"]]["response"] = response_json
            if resp.status_code != 200:
                raise RuntimeError(f"Meta API UPDATE error {resp.status_code}: {json.dumps(response_json)}")

    return response_json


def get_debug_info(property_id: str) -> Dict[str, Any]:
    """Return last payload and response for a property."""
    return _debug_store.get(property_id, {"payload": None, "response": None})
