"""Bulk property processor — uses canonical normalizer for all properties."""
import logging
from typing import Any, Dict, List

from utils.property_normalizer import (
    parse_raw_property_dump,
    normalize_property,
    parsed_to_normalized,
    build_meta_title,
    build_meta_description,
    build_whatsapp_caption,
)
from utils.formatters import canonical_normalize_property, generate_drive_folder_name

logger = logging.getLogger(__name__)


class BulkPropertyProcessor:
    """Process a batch of properties into Meta + WhatsApp outputs."""

    def process_properties_batch(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        messages = []
        meta_outputs = []
        drive_folders = []
        errors = []

        for i, prop in enumerate(properties):
            label = f"Property {i + 1}"
            try:
                # Support raw_dump key for text-based input
                raw_dump = prop.get('raw_dump') or prop.get('raw_text', '')
                if raw_dump:
                    parsed = parse_raw_property_dump(raw_dump)
                    norm = parsed_to_normalized(parsed)
                    # Allow form fields to override parsed values if supplied
                    for k, v in prop.items():
                        if k not in ('raw_dump', 'raw_text') and v and hasattr(norm, k):
                            setattr(norm, k, v)
                else:
                    norm = canonical_normalize_property(prop)

                meta_title = build_meta_title(norm)
                meta_desc = build_meta_description(norm)
                wa_caption = build_whatsapp_caption(norm)
                folder_name = generate_drive_folder_name(prop)

                label = meta_title or norm.property_name or label

                messages.append({
                    "title": label,
                    "message": wa_caption,
                    "meta_title": meta_title,
                    "meta_description": meta_desc,
                    "needs_review": norm.needs_review,
                    "unrecognized_lines": norm.unrecognized_lines,
                })
                drive_folders.append({"folder_name": folder_name})
                meta_outputs.append({"title": meta_title, "description": meta_desc})
                logger.info("[Bulk] Processed property %d: %s", i + 1, label)
            except Exception as exc:
                err = f"Property {i + 1} ({label}): {exc}"
                errors.append(err)
                logger.error("[Bulk] Failed property %d: %s", i + 1, exc, exc_info=True)

        return {
            "messages": messages,
            "meta_outputs": meta_outputs,
            "drive_folders": drive_folders,
            "processed_count": len(messages),
            "errors": errors,
        }
