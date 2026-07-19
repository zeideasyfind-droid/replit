"""WhatsApp sender — sends property listing as image+caption or text fallback."""
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


async def send_property_listing(
    caption: str,
    cover_image_url: str = "",
    recipient: str = "",
) -> Dict[str, Any]:
    """Send WhatsApp property listing.
    - If cover_image_url is set: send image message with caption.
    - Otherwise: send text message.
    Never raises — logs on failure.
    """
    to = recipient or WHATSAPP_RECIPIENT_NUMBER
    masked_to = f"******{to[-4:]}" if to and len(to) >= 4 else "??????"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"{GRAPH_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    if cover_image_url:
        message_type = "image_with_caption"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {
                "link": cover_image_url,
                "caption": caption,
            },
        }
    else:
        message_type = "text_fallback"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": caption},
        }

    logger.info(
        "[WhatsApp] Sending %s to %s",
        message_type,
        masked_to,
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
            msg_id = ""
            if isinstance(response_json.get("messages"), list) and response_json["messages"]:
                msg_id = response_json["messages"][0].get("id", "")
            return {
                "status": "sent",
                "message_type": message_type,
                "recipient": masked_to,
                "message_id": msg_id,
                "cover_image": bool(cover_image_url),
                "response": response_json,
            }
        else:
            logger.warning("[WhatsApp] Non-200 response: %s", response_json)
            return {
                "status": "failed",
                "message_type": message_type,
                "recipient": masked_to,
                "error": response_json,
            }
    except Exception as exc:
        logger.error("[WhatsApp] Request failed: %s", str(exc))
        return {
            "status": "failed",
            "message_type": message_type if cover_image_url else "text_fallback",
            "recipient": masked_to,
            "error": str(exc),
        }


# Backwards-compat shim so existing callers of send_confirmation still work
async def send_confirmation(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy entry point. Builds caption from property_data and delegates."""
    from utils.property_normalizer import (
        normalize_property, build_whatsapp_caption, parsed_to_normalized,
        parse_raw_property_dump
    )
    from utils.formatters import canonical_normalize_property

    raw_dump = property_data.get('raw_dump') or property_data.get('raw_text', '')
    if raw_dump:
        parsed = parse_raw_property_dump(raw_dump)
        norm = parsed_to_normalized(parsed)
    else:
        norm = canonical_normalize_property(property_data)

    caption = build_whatsapp_caption(norm)
    cover_image_url = (
        property_data.get('cover_image_url')
        or property_data.get('image_link')
        or ""
    )
    recipient = property_data.get('whatsapp_recipient', '')
    return await send_property_listing(caption, cover_image_url, recipient)
