import logging
from typing import Any, Dict, List

from utils.formatters import (
    format_whatsapp_message, 
    generate_drive_folder_name, 
    canonical_normalize_property,
    render_meta_title
)

logger = logging.getLogger(__name__)


class BulkPropertyProcessor:
    """Process a batch of properties into WhatsApp messages and Drive folder names."""

    def process_properties_batch(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        messages = []
        drive_folders = []
        errors = []

        for i, prop in enumerate(properties):
            try:
                norm_prop = canonical_normalize_property(prop)
                label = render_meta_title(norm_prop) or prop.get("title") or f"Property {i + 1}"
                
                message = format_whatsapp_message(prop)
                folder_name = generate_drive_folder_name(prop)
                messages.append({"title": label, "message": message})
                drive_folders.append({"folder_name": folder_name})
                logger.info("[Bulk] Processed property %d: %s", i + 1, label)
            except Exception as exc:
                err = f"Property {i + 1} ({label}): {exc}"
                errors.append(err)
                logger.error("[Bulk] Failed property %d: %s", i + 1, exc)

        return {
            "messages": messages,
            "drive_folders": drive_folders,
            "processed_count": len(messages),
            "errors": errors,
        }
