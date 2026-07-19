from datetime import datetime, date
import re
import random
from .smart_parser import parse_property_text


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


def normalize_tenant_preference(tenant_str, diet_pref=None):
    tenant_str = str(tenant_str).lower() if tenant_str else ""
    has_family = "family" in tenant_str or "families" in tenant_str
    has_professional = any(t in tenant_str for t in ["working", "professional"])
    has_anyone = any(t in tenant_str for t in ["anyone", "any", "open", "all"])
    if has_anyone or (not has_family and not has_professional):
        result = "Anyone"
    else:
        parts = []
        if has_family:
            parts.append("Families")
        if has_professional:
            parts.append("Working Professionals")
        result = " / ".join(parts) if parts else "Anyone"
    if diet_pref:
        diet_pref = str(diet_pref).lower().strip()
        if "vegetarian" in diet_pref and "non" not in diet_pref:
            result += ", Vegetarian"
        elif "non-vegetarian" in diet_pref or "non veg" in diet_pref:
            result += ", Non-Vegetarian"
    return result


def canonical_normalize_property(raw_data):
    property_name = (
        raw_data.get("property_name") or 
        raw_data.get("building_name") or 
        ""
    ).strip()
    locality = raw_data.get("locality", "").strip()
    location_field = raw_data.get("location", "").strip()
    normalized_location = locality if locality else location_field
    bhk = str(raw_data.get("bhk", "")).upper().strip()
    if bhk and "BHK" not in bhk:
        bhk = f"{bhk} BHK"
    furnishing = raw_data.get("furnishing", "Semi-Furnished").strip()
    return {
        "property_id": raw_data.get("property_id", ""),
        "property_name": property_name,
        "location": normalized_location,
        "city": raw_data.get("city", "").strip(),
        "bhk": bhk,
        "rent": raw_data.get("rent", raw_data.get("price", "N/A")),
        "maintenance": raw_data.get("maintenance", "N/A"),
        "deposit": raw_data.get("deposit", "N/A"),
        "sqft": raw_data.get("sqft", raw_data.get("area_super", "N/A")),
        "floor": raw_data.get("floor", "N/A"),
        "furnishing": furnishing,
        "bathrooms": str(raw_data.get("bathrooms", "")).strip(),
        "balcony": str(raw_data.get("balcony", "")).strip(),
        "utility": str(raw_data.get("utility", "")).strip(),
        "available_from": normalize_availability(raw_data.get("available_from", "")),
        "preferred_tenant": normalize_tenant_preference(
            raw_data.get("preferred_tenant", "Anyone"),
            raw_data.get("diet_preference", "")
        ),
        "pets": raw_data.get("pets", "Not Allowed"),
        "community": raw_data.get("community", "Gated"),
        "gallery_link": raw_data.get("gallery_link", ""),
        "map_link": raw_data.get("map_link", raw_data.get("maps_link", "")),
        "description": raw_data.get("description", ""),
        "raw_title": raw_data.get("title", "")
    }


def render_meta_title(norm_prop):
    """Meta Title: Furnishing BHK - Location"""
    furnish = norm_prop["furnishing"]
    bhk = norm_prop["bhk"].replace(" ", "")
    loc = norm_prop["location"]
    return f"{furnish} {bhk} - {loc}"


def render_whatsapp_title(norm_prop):
    """WhatsApp Title: Use the descriptive title from the first line"""
    return norm_prop["raw_title"]


def render_meta_description(norm_prop):
    lines = [
        render_meta_title(norm_prop),
        f"Price: ₹{norm_prop['rent']}",
        f"Maintenance: ₹{norm_prop['maintenance']}",
        f"Deposit: ₹{norm_prop['deposit']}",
        f"Area: {norm_prop['sqft']} Sq. Ft.",
        f"Floor: {norm_prop['floor']}",
        f"Furnishing: {norm_prop['furnishing']}",
        f"Available From: {norm_prop['available_from']}",
        f"Preferred Tenant: {norm_prop['preferred_tenant']}",
        f"Pets: {norm_prop['pets']}",
        f"Community: {norm_prop['community']}",
        f"Location: {norm_prop['location']}, {norm_prop['city']}",
    ]
    if norm_prop["property_name"]:
        lines.append(f"Society: {norm_prop['property_name']}")
    if norm_prop["map_link"]:
        lines.append("")
        lines.append(f"📍 Map: {norm_prop['map_link']}")
    return "\n".join(lines)


def format_whatsapp_message(raw_data):
    norm_prop = canonical_normalize_property(raw_data)
    title = render_whatsapp_title(norm_prop)
    lines = [
        f"*{title}*",
        "",
        f"Rent: ₹{norm_prop['rent']}",
        f"Maintenance: ₹{norm_prop['maintenance']}",
        f"Deposit: ₹{norm_prop['deposit']}",
        f"Area: {norm_prop['sqft']} Sq. Ft.",
        f"Floor: {norm_prop['floor']}",
        f"Available From: {norm_prop['available_from']}",
        f"Preferred Tenant: {norm_prop['preferred_tenant']}",
        f"Pets: {norm_prop['pets']}",
        f"Community: {norm_prop['community']}",
        f"Location: *{norm_prop['location']}*",
    ]
    if norm_prop["gallery_link"]:
        lines += ["", f"📸 *Gallery:* {norm_prop['gallery_link']}"]
    if norm_prop["property_name"]:
        lines += ["", f"*{norm_prop['property_name']}*"]
    if norm_prop["map_link"]:
        lines.append(f"📍 Map: {norm_prop['map_link']}")
    return "\n".join(lines)


def generate_drive_folder_name(raw_data):
    norm_prop = canonical_normalize_property(raw_data)
    numeric_id = str(random.randint(100, 999))
    base_name = norm_prop["property_name"] if norm_prop["property_name"] else norm_prop["location"]
    folder_name = f"EFF-{numeric_id}-{base_name}"
    folder_name = re.sub(r"[^a-zA-Z0-9\s\-]", "", folder_name)
    folder_name = re.sub(r"\s+", " ", folder_name).strip()
    return folder_name
