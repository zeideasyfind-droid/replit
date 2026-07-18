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


def format_title_with_utility(title, property_details):
    """Add 'with Utility' to title if fully furnished 2 BHK with 2 bathrooms & balcony."""
    furnishing = property_details.get("furnishing", "").lower()

    if (
        "fully furnished" in furnishing
        and "2 bhk" in title.lower()
        and "2 bath" in title.lower()
        and "balcony" in title.lower()
    ):
        return title + " with Utility"

    return title


def generate_drive_folder_name(property_details):
    """
    Generate Drive folder name following EasyFind format:
    EFF-{numeric}-{society/apt OR location-owner}
    """
    society = property_details.get("society", "").strip()
    apartment = property_details.get("apartment", "").strip()
    location = property_details.get("location", "").strip()
    owner = property_details.get("owner", "Unknown").strip()
    property_name = property_details.get("property_name", "").strip()
    community_type = property_details.get("community", "Gated").lower()

    numeric_id = str(random.randint(100, 999))

    if society or apartment:
        base_name = society if society else apartment
        folder_name = f"EFF-{numeric_id}-{base_name}"
    elif property_name:
        folder_name = f"EFF-{numeric_id}-{property_name}-{owner}"
    elif community_type in ("semi-gated", "non-society", "non-gated"):
        folder_name = f"EFF-{numeric_id}-{location}-{owner}"
    else:
        folder_name = f"EFF-{numeric_id}-{location}-{owner}"

    folder_name = re.sub(r"[^a-zA-Z0-9\s\-]", "", folder_name)
    folder_name = re.sub(r"\s+", " ", folder_name).strip()
    return folder_name


def format_whatsapp_message(property_details):
    """Format a single property into WhatsApp message format."""
    title = format_title_with_utility(
        property_details.get("title", ""),
        property_details,
    )

    available_from = normalize_availability(property_details.get("available_from", ""))
    preferred_tenant = normalize_tenant_preference(
        property_details.get("preferred_tenant", "Anyone"),
        property_details.get("diet_preference", ""),
    )

    rent = property_details.get("rent", "N/A")
    maintenance = property_details.get("maintenance", "N/A")
    deposit = property_details.get("deposit", "N/A")
    sqft = property_details.get("sqft", "N/A")
    floor_ = property_details.get("floor", "N/A")
    pets = property_details.get("pets", "Not Allowed")
    community = property_details.get("community", "Gated")
    location = property_details.get("location", "N/A")
    gallery_link = property_details.get("gallery_link", "")
    map_link = property_details.get("map_link", "")
    prop_display = property_details.get("property_name") or property_details.get("society") or "N/A"

    lines = [
        f"*{title}*",
        "",
        f"Rent: ₹{rent}",
        f"Maintenance: ₹{maintenance}",
        f"Deposit: ₹{deposit}",
        f"Area: {sqft} Sq. Ft.",
        f"Floor: {floor_}",
        f"Available From: {available_from}",
        f"Preferred Tenant: {preferred_tenant}",
        f"Pets: {pets}",
        f"Community: {community}",
        f"Location: *{location}*",
    ]

    if gallery_link:
        lines += ["", f"📸 *Gallery:* {gallery_link}"]

    lines += ["", f"*{prop_display}*"]

    if map_link:
        lines.append(f"📍 Map: {map_link}")

    return "\n".join(lines)
