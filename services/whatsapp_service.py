import os
import json
import logging
import httpx
from typing import Any, Dict

logger = logging.getLogger(__name__)

WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_RECIPIENT_NUMBER = os.environ.get("WHATSAPP_RECIPIENT_NUMBER", "")
GRAPH_BASE = "https://graph.facebook.com/v25.0"


async def send_confirmation(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send WhatsApp text message confirming property listing. Never raises — logs on failure."""
    message_body = (
        f"✅ *EasyFind Property Listed!*\n\n"
        f"🏠 *ID:* {property_data.get('property_id')}\n"
        f"📋 *Title:* {property_data.get('title')}\n"
        f"💰 *Price:* {property_data.get('price')} {property_data.get('currency', 'INR')}\n"
        f"📍 *Location:* {property_data.get('locality')}, {property_data.get('city')}\n"
        f"🖼️ *Image:* {property_data.get('image_link', 'N/A')}"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_RECIPIENT_NUMBER,
        "type": "text",
        "text": {"body": message_body},
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    url = f"{GRAPH_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    logger.info(
        "[WhatsApp] Sending message to number ending ...%s",
        WHATSAPP_RECIPIENT_NUMBER[-4:] if WHATSAPP_RECIPIENT_NUMBER else "????",
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
        response_json = resp.json()
        logger.info(
            "[WhatsApp] Response (status %d): %s",
            resp.status_code,
            json.dumps(response_json),
        )
        if resp.status_code == 200:
            return {"status": "sent", "response": response_json}
        else:
            logger.warning("[WhatsApp] Non-200 response: %s", response_json)
            return {"status": "failed", "error": response_json}
    except Exception as exc:
        logger.error("[WhatsApp] Request failed: %s", str(exc))
        return {"status": "failed", "error": str(exc)}
