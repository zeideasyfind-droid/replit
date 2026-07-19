"""Formatter shim — delegates all real work to property_normalizer.py.
This file is kept for backwards compatibility but all formatting logic
has been moved to utils/property_normalizer.py.

DELETED: format_title_with_utility() — was incompatible with canonical spec.
"""
from datetime import datetime, date
import re
import random

from .property_normalizer import (
    parse_raw_property_dump,
    normalize_property,
    parsed_to_normalized,
    build_meta_title,
    build_meta_description,
    build_whatsapp_caption,
    build_whatsapp_title,
    build_whatsapp_message,
    NormalizedProperty,
)


# ─────────────────────────────────────────────────────────────────────────────
# Legacy helpers (kept for API compatibility)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_availability(date_str):
    if not date_str:
        return "Ready to occupy"
    date_str = str(date_str).lower().strip()
    immediate_terms = ["immediate", "ready", "today", "now", "vacant", "available now"]
    if any(term in date_str for term in immediate_terms):
        return "Ready to occupy"
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if parsed_date <= date.today():
            return "Ready to occupy"
        return parsed_date.strftime("%d %b %Y")
    except (ValueError, TypeError):
        pass
    return date_str.title()


def canonical_normalize_property(raw_data: dict) -> NormalizedProperty:
    """Delegates to property_normalizer.normalize_property.
    Handles both legacy field names and canonical field names.
    """
    # Map legacy field names to canonical
    mapped = dict(raw_data)
    if 'sqft' in mapped and 'area_sqft' not in mapped:
        mapped['area_sqft'] = mapped.pop('sqft')
    if 'map_link' in mapped and 'google_maps_link' not in mapped:
        mapped['google_maps_link'] = mapped.pop('map_link')
    if 'maps_link' in mapped and 'google_maps_link' not in mapped:
        mapped['google_maps_link'] = mapped.pop('maps_link')
    if 'community' in mapped and 'community_type' not in mapped:
        mapped['community_type'] = mapped.pop('community')
    # building_name -> property_name fallback
    if not mapped.get('property_name') and mapped.get('building_name'):
        mapped['property_name'] = mapped['building_name']
    # locality / location merge
    if not mapped.get('location') and mapped.get('locality'):
        loc_parts = [mapped['locality']]
        if mapped.get('city'):
            loc_parts.append(mapped['city'])
        mapped['location'] = ', '.join(filter(None, loc_parts))
    return normalize_property(mapped)


def render_meta_title(norm_prop) -> str:
    """Delegates to build_meta_title from property_normalizer."""
    if isinstance(norm_prop, dict):
        norm_prop = canonical_normalize_property(norm_prop)
    return build_meta_title(norm_prop)


def render_meta_description(norm_prop) -> str:
    """Delegates to build_meta_description from property_normalizer."""
    if isinstance(norm_prop, dict):
        norm_prop = canonical_normalize_property(norm_prop)
    return build_meta_description(norm_prop)


def render_whatsapp_title(norm_prop) -> str:
    """Delegates to build_whatsapp_title from property_normalizer."""
    if isinstance(norm_prop, dict):
        norm_prop = canonical_normalize_property(norm_prop)
    return build_whatsapp_title(norm_prop)


def format_whatsapp_message(raw_data: dict) -> str:
    """Full WhatsApp caption from a raw data dict. Delegates to property_normalizer."""
    norm_prop = canonical_normalize_property(raw_data)
    return build_whatsapp_caption(norm_prop)


def generate_drive_folder_name(raw_data: dict) -> str:
    """Drive folder name uses property_name only (no society/apartment fallback)."""
    norm_prop = canonical_normalize_property(raw_data)
    numeric_id = str(random.randint(100, 999))
    # Use property_name only
    base_name = norm_prop.property_name if norm_prop.property_name else norm_prop.meta_location or norm_prop.location
    if not base_name:
        base_name = "Property"
    folder_name = f"EFF-{numeric_id}-{base_name}"
    folder_name = re.sub(r"[^a-zA-Z0-9\s\-]", "", folder_name)
    folder_name = re.sub(r"\s+", " ", folder_name).strip()
    return folder_name
