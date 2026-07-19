from datetime import datetime, date
import re
import random


def normalize_availability(date_str):
    """Normalize availability date to 'Ready to occupy' if immediate/today/past."""
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
    """Normalize tenant preference and add diet information."""
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
    """
    Returns a stable, normalized property object.
    Unifies Society/Apartment Name into Property Name.
    Normalizes location based on micro-location preference.
    """
    # 1. Handle Property Name (unify Society/Apartment)
    property_name = (
        raw_data.get("property_name") or 
        raw_data.get("society") or 
        raw_data.get("apartment") or 
        raw_data.get("building_name") or 
        ""
    ).strip()

    # 2. Location Normalization
    # Preference: micro-location (locality) if informative, else full location
    locality = raw_data.get("locality", "").strip()
    location_field = raw_data.get("location", "").strip()
    
    # Use locality if it's present and looks like a micro-location
    # If locality is empty, fallback to location_field
    normalized_location = locality if locality else location_field

    # 3. Basic Fields
    bhk = str(raw_data.get("bhk", "")).upper().strip()
    if bhk and "BHK" not in bhk:
        bhk = f"{bhk} BHK"
        
    furnishing = raw_data.get("furnishing", "Semi-Furnished").strip()
    # Standardize furnishing strings
    if "fully" in furnishing.lower():
        furnishing = "Fully Furnished"
    elif "semi" in furnishing.lower():
        furnishing = "Semi-Furnished"
    elif "unfurnished" in furnishing.lower():
        furnishing = "Unfurnished"

    return {
        "property_id": raw_data.get("property_id", ""),
        "property_name": property_name,
        "location": normalized_location,
        "city": raw_data.get("city", "").strip(),
        "bhk": bhk,
        "rent": raw_data.get("rent", "N/A"),
        "maintenance": raw_data.get("maintenance", "N/A"),
        "deposit": raw_data.get("deposit", "N/A"),
        "sqft": raw_data.get("sqft", "N/A"),
        "floor": raw_data.get("floor", "N/A"),
        "furnishing": furnishing,
        "bathrooms": raw_data.get("bathrooms", "").strip(),
        "balcony": raw_data.get("balcony", "").strip(),
        "utility": raw_data.get("utility", "").strip(),
        "available_from": normalize_availability(raw_data.get("available_from", "")),
        "preferred_tenant": normalize_tenant_preference(
            raw_data.get("preferred_tenant", "Anyone"),
            raw_data.get("diet_preference", "")
        ),
        "pets": raw_data.get("pets", "Not Allowed"),
        "community": raw_data.get("community", "Gated"),
        "gallery_link": raw_data.get("gallery_link", ""),
        "map_link": raw_data.get("map_link", ""),
        "description": raw_data.get("description", ""),
    }


def render_meta_title(norm_prop):
    """
    Meta Catalogue title: structured and concise.
    Example: Semi Furnished | 2BHK | Varthur
    """
    parts = []
    if norm_prop["furnishing"]:
        parts.append(norm_prop["furnishing"])
    if norm_prop["bhk"]:
        parts.append(norm_prop["bhk"].replace(" ", ""))
    if norm_prop["location"]:
        parts.append(norm_prop["location"])
    
    return " | ".join(parts)


def render_whatsapp_title(norm_prop):
    """
    WhatsApp title: human-readable and descriptive.
    Example: Semi-Furnished 2 BHK, 2 Bathrooms, 2 Balconies & Utility
    """
    title_parts = []
    if norm_prop["furnishing"]:
        title_parts.append(norm_prop["furnishing"])
    if norm_prop["bhk"]:
        title_parts.append(norm_prop["bhk"])
    
    base_title = " ".join(title_parts)
    
    extras = []
    if norm_prop["bathrooms"]:
        val = norm_prop["bathrooms"]
        suffix = "Bathrooms" if val != "1" else "Bathroom"
        extras.append(f"{val} {suffix}")
    
    if norm_prop["balcony"]:
        val = norm_prop["balcony"]
        suffix = "Balconies" if val != "1" else "Balcony"
        extras.append(f"{val} {suffix}")
        
    if norm_prop["utility"]:
        # If utility is just a flag or text, handle accordingly
        u = norm_prop["utility"].lower()
        if u in ("yes", "true", "1", "available", "utility"):
            extras.append("Utility")
        elif u not in ("no", "false", "0", "none", ""):
            extras.append(norm_prop["utility"])

    if not extras:
        return base_title
    
    if len(extras) > 1:
        return f"{base_title}, {', '.join(extras[:-1])} & {extras[-1]}"
    else:
        return f"{base_title}, {extras[0]}"


def render_meta_description(norm_prop):
    """
    Meta Catalogue description: line-by-line structured description.
    """
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
    """Format a single property into WhatsApp message format using canonical normalizer."""
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
    """
    Generate Drive folder name following EasyFind format:
    EFF-{numeric}-{property_name OR location}
    """
    norm_prop = canonical_normalize_property(raw_data)
    
    numeric_id = str(random.randint(100, 999))
    
    if norm_prop["property_name"]:
        base_name = norm_prop["property_name"]
    else:
        base_name = norm_prop["location"]

    folder_name = f"EFF-{numeric_id}-{base_name}"
    folder_name = re.sub(r"[^a-zA-Z0-9\s\-]", "", folder_name)
    folder_name = re.sub(r"\s+", " ", folder_name).strip()
    return folder_name
