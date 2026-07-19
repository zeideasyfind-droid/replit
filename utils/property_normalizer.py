"""Canonical property parser, normalizer and renderer.
This is the single source of truth for all formatting logic.
No other module should parse raw text or build titles/descriptions.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ParsedProperty:
    raw_title: str = ""
    furnishing: str = ""
    bhk: str = ""
    bathrooms: str = ""
    bathroom_type: str = ""      # "Attached" | ""
    balconies: str = ""
    has_utility: bool = False

    rent: str = ""
    maintenance: str = ""
    deposit: str = ""
    area_sqft: str = ""
    floor: str = ""
    available_from: str = ""
    preferred_tenant: str = ""
    diet_preference: str = ""
    pets: str = ""
    community_type: str = ""

    location: str = ""
    property_name: str = ""
    gallery_link: str = ""
    google_maps_link: str = ""
    cover_image_url: str = ""

    unrecognized_lines: list = field(default_factory=list)
    needs_review: list = field(default_factory=list)


@dataclass
class NormalizedProperty:
    raw_title: str = ""
    furnishing: str = ""
    bhk: str = ""
    bathrooms: str = ""
    bathroom_type: str = ""
    balconies: str = ""
    has_utility: bool = False

    rent: str = ""
    maintenance: str = ""
    deposit: str = ""
    area_sqft: str = ""
    floor: str = ""
    available_from: str = ""
    preferred_tenant: str = ""
    diet_preference: str = ""
    pets: str = ""
    community_type: str = ""

    location: str = ""
    meta_location: str = ""     # derived short form for Meta title
    property_name: str = ""
    gallery_link: str = ""
    google_maps_link: str = ""
    cover_image_url: str = ""

    unrecognized_lines: list = field(default_factory=list)
    needs_review: list = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Location → Meta display location mapping
# ─────────────────────────────────────────────────────────────────────────────

# Rule: keep the first meaningful locality token before any comma/"off"/"road" qualifier
_LOCATION_OVERRIDES = {
    "hosa road": "Hosa Road",
    "off sarjapur road": "Off Sarjapur Road",
    "sarjapur road": "Sarjapur Road",
    "nallurahalli": "Nallurahalli",
    "bellandur": "Bellandur",
    "hoodi": "Hoodi",
    "kadubesanahalli": "Kadubesanahalli",
    "varthur": "Varthur",
    "harlur": "Harlur",
    "whitefield": "Whitefield",
    "marathahalli": "Marathahalli",
    "sarjapur": "Sarjapur",
    "electronic city": "Electronic City",
    "koramangala": "Koramangala",
    "indiranagar": "Indiranagar",
    "jp nagar": "JP Nagar",
    "hsr layout": "HSR Layout",
    "btm layout": "BTM Layout",
    "kr puram": "KR Puram",
    "hebbal": "Hebbal",
    "yelahanka": "Yelahanka",
    "bannerghatta": "Bannerghatta Road",
    "kanakapura": "Kanakapura Road",
    "rajarajeshwari nagar": "Rajarajeshwari Nagar",
    "doddanekundi": "Doddanekundi",
    "mahadevapura": "Mahadevapura",
}


def _derive_meta_location(full_location: str) -> str:
    """Return short display location for Meta title from full location string."""
    if not full_location:
        return ""
    loc_lower = full_location.lower().strip()

    # Direct full match first
    if loc_lower in _LOCATION_OVERRIDES:
        return _LOCATION_OVERRIDES[loc_lower]

    # Try each part split by comma
    parts = [p.strip() for p in full_location.split(",")]
    for part in parts:
        part_lower = part.lower().strip()
        if part_lower in _LOCATION_OVERRIDES:
            return _LOCATION_OVERRIDES[part_lower]

    # Try substring match against known keys (longest match wins)
    matches = [(k, v) for k, v in _LOCATION_OVERRIDES.items() if k in loc_lower]
    if matches:
        best = max(matches, key=lambda x: len(x[0]))
        return best[1]

    # Fallback: return first token before comma
    return parts[0].strip().title() if parts else full_location.title()


# ─────────────────────────────────────────────────────────────────────────────
# Number preservation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean_numeric_value(raw: str) -> str:
    """Strip currency symbols and whitespace but preserve shorthand like 2L, 5.5k."""
    if not raw:
        return ""
    s = raw.strip()
    # Remove leading ₹ / Rs
    s = re.sub(r'^[₹Rr][Ss]?\.?\s*', '', s)
    return s.strip()


def _format_currency_display(val: str) -> str:
    """Convert shorthand like 60k → ₹60,000, 2.5L → ₹2,50,000 for display.
    If already a word (Inclusive, Water charges) preserve as-is (no ₹).
    """
    if not val:
        return val
    v = val.strip()
    # If it looks like a text value (not numeric shorthand), return as-is
    if re.match(r'^[A-Za-z]', v) and not re.match(r'^[₹]', v):
        return v
    # Strip ₹
    num_str = re.sub(r'^₹', '', v).strip()
    match = re.match(r'^([\d.]+)\s*([kKlLcCrR]{0,2})$', num_str)
    if not match:
        return v
    try:
        num = float(match.group(1))
        suffix = match.group(2).lower()
        if suffix == 'k':
            num_val = int(num * 1000)
            return f'₹{num_val:,}'
        elif suffix in ('l', 'L'):
            num_val = int(num * 100000)
            # Indian formatting
            return f'₹{num_val:,}'
        elif suffix == 'cr':
            num_val = int(num * 10000000)
            return f'₹{num_val:,}'
        else:
            # pure number
            num_val = int(num)
            return f'₹{num_val:,}'
    except Exception:
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Title line parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_title_line(title_line: str) -> dict:
    """Extract furnishing, BHK, bathrooms, bathroom_type, balconies, utility from first line."""
    result = {
        "furnishing": "",
        "bhk": "",
        "bathrooms": "",
        "bathroom_type": "",
        "balconies": "",
        "has_utility": False,
    }
    raw = title_line.strip()

    # Furnishing
    if re.search(r'fully\s*(?:furnished|permitted)', raw, re.IGNORECASE):
        result["furnishing"] = "Fully Furnished"
    elif re.search(r'semi[\s-]*(?:furnished|permitted)', raw, re.IGNORECASE):
        result["furnishing"] = "Semi Furnished"
    elif re.search(r'unfurnished|bare[\s-]*shell', raw, re.IGNORECASE):
        result["furnishing"] = "Unfurnished"

    # BHK — support 2.5 BHK etc
    bhk_m = re.search(r'([\d.]+)\s*BHK', raw, re.IGNORECASE)
    if bhk_m:
        result["bhk"] = bhk_m.group(1)

    # Bathrooms — check "Attached" qualifier
    bath_m = re.search(r'(\d+)\s*(Attached\s*)?Bath(?:room)?s?', raw, re.IGNORECASE)
    if bath_m:
        result["bathrooms"] = bath_m.group(1)
        if bath_m.group(2) and bath_m.group(2).strip():
            result["bathroom_type"] = "Attached"

    # Balconies
    balc_m = re.search(r'(\d+)\s*Baicon(?:ies|y)?|([\d]+)\s*Balcon(?:ies|y)?', raw, re.IGNORECASE)
    if balc_m:
        result["balconies"] = balc_m.group(1) or balc_m.group(2)

    # Utility
    if re.search(r'\+?\s*utility|\butility\b', raw, re.IGNORECASE):
        result["has_utility"] = True

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Label-to-field mapping
# ─────────────────────────────────────────────────────────────────────────────

_LABEL_MAP = [
    (re.compile(r'^rent\s*[:\-–]\s*', re.IGNORECASE), 'rent'),
    (re.compile(r'^maintenance\s*[:\-–]\s*', re.IGNORECASE), 'maintenance'),
    (re.compile(r'^deposit\s*[:\-–]\s*', re.IGNORECASE), 'deposit'),
    (re.compile(r'^(?:sqft|sq\.?\s*ft\.?|area)\s*[:\-–]\s*', re.IGNORECASE), 'area_sqft'),
    (re.compile(r'^floor\s*[:\-–]\s*', re.IGNORECASE), 'floor'),
    (re.compile(r'^availabl?e?\s*(?:from)?\s*[:\-–]\s*', re.IGNORECASE), 'available_from'),
    (re.compile(r'^preferred\s*tenant\s*[:\-–]\s*', re.IGNORECASE), 'preferred_tenant'),
    (re.compile(r'^diet\s*preference\s*[:\-–]\s*', re.IGNORECASE), 'diet_preference'),
    (re.compile(r'^pets\s*[:\-–]\s*', re.IGNORECASE), 'pets'),
    (re.compile(r'^community\s*[:\-–]\s*', re.IGNORECASE), 'community_type'),
    (re.compile(r'^location\s*[:\-–]\s*', re.IGNORECASE), 'location'),
]

_MAPS_RE = re.compile(
    r'https?://(?:maps\.google\.com|goo\.gl/maps|maps\.app\.goo\.gl|www\.google\.com/maps)[^\s]*',
    re.IGNORECASE,
)
_DRIVE_RE = re.compile(r'https?://(?:drive\.google\.com|docs\.google\.com)[^\s]*', re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# Core parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_raw_property_dump(raw_text: str) -> ParsedProperty:
    """Parse a raw broker/WhatsApp property dump into a ParsedProperty.
    Rules:
    - Never assign by line position (except first line = raw_title)
    - Never convert 2L → 2
    - Never assign sqft to floor or vice versa
    - Unrecognized lines go to unrecognized_lines
    """
    p = ParsedProperty()
    if not raw_text or not raw_text.strip():
        return p

    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

    # First line is always raw_title
    if lines:
        p.raw_title = lines[0].replace('*', '').strip()
        title_data = _parse_title_line(p.raw_title)
        p.furnishing = title_data["furnishing"]
        p.bhk = title_data["bhk"]
        p.bathrooms = title_data["bathrooms"]
        p.bathroom_type = title_data["bathroom_type"]
        p.balconies = title_data["balconies"]
        p.has_utility = title_data["has_utility"]

    # Identify maps and drive URLs
    maps_line_indices = set()
    property_name_candidate = ""
    for i, line in enumerate(lines):
        if _MAPS_RE.search(line):
            maps_line_indices.add(i)
            p.google_maps_link = _MAPS_RE.search(line).group(0)
            # Line before maps URL → property_name candidate
            if i > 0:
                prev = lines[i - 1].replace('*', '').strip().rstrip(':')
                property_name_candidate = prev
        if _DRIVE_RE.search(line):
            p.gallery_link = _DRIVE_RE.search(line).group(0)

    # Property name from bold text or line before maps
    if property_name_candidate:
        p.property_name = property_name_candidate
    else:
        bold_texts = re.findall(r'\*([^\*\n]{3,})\*', raw_text)
        for bt in bold_texts:
            bt = bt.strip().rstrip(':')
            if not _MAPS_RE.search(bt) and not _DRIVE_RE.search(bt):
                p.property_name = bt
                break

    # Parse labeled lines (skip first line = title, skip maps/drive lines)
    skip_indices = maps_line_indices
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if i in skip_indices:
            continue
        if _DRIVE_RE.search(line) or _MAPS_RE.search(line):
            continue
        # Skip property name line (line before maps)
        is_prop_name_line = False
        for mi in maps_line_indices:
            if i == mi - 1:
                is_prop_name_line = True
                break
        if is_prop_name_line:
            continue

        matched = False
        for label_re, field_name in _LABEL_MAP:
            if label_re.match(line):
                value = label_re.sub('', line).strip()
                # Clean currency prefix but preserve shorthand
                if field_name in ('rent', 'maintenance', 'deposit'):
                    value = _clean_numeric_value(value)
                elif field_name == 'area_sqft':
                    value = re.sub(r'^[₹Rr][Ss]?\.?\s*', '', value).strip()
                    # Remove any trailing non-numeric
                    m = re.match(r'^([\d,]+)', value)
                    value = m.group(1).replace(',', '') if m else value
                elif field_name == 'available_from':
                    # Normalize immediate variants
                    if re.match(r'immediately|ready|today|now|vacant', value, re.IGNORECASE):
                        value = 'Ready to occupy'
                setattr(p, field_name, value)
                matched = True
                break

        if not matched:
            # Only flag as unrecognized if it has some content and isn't blank
            stripped = line.replace('*', '').strip()
            if stripped and not re.match(r'^https?://', stripped):
                p.unrecognized_lines.append(stripped)

    return p


# ─────────────────────────────────────────────────────────────────────────────
# Normalizer
# ─────────────────────────────────────────────────────────────────────────────

def normalize_property(data: dict) -> "NormalizedProperty":
    """Normalize a dict of canonical field values into a NormalizedProperty.
    Accepts both form-submitted data and ParsedProperty dicts.
    """
    def _get(*keys, default=''):
        for k in keys:
            v = data.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return default

    n = NormalizedProperty()
    n.raw_title = _get('raw_title', 'title')
    n.furnishing = _get('furnishing')
    n.bhk = _get('bhk')
    n.bathrooms = _get('bathrooms')
    n.bathroom_type = _get('bathroom_type')
    n.balconies = _get('balconies')
    n.has_utility = bool(data.get('has_utility', False))

    n.rent = _get('rent')
    n.maintenance = _get('maintenance')
    n.deposit = _get('deposit')
    n.area_sqft = _get('area_sqft', 'sqft')
    n.floor = _get('floor')
    n.available_from = _get('available_from')
    n.preferred_tenant = _get('preferred_tenant')
    n.diet_preference = _get('diet_preference')
    n.pets = _get('pets')
    n.community_type = _get('community_type', 'community')

    n.location = _get('location')
    n.meta_location = _derive_meta_location(n.location)
    n.property_name = _get('property_name')
    n.gallery_link = _get('gallery_link')
    n.google_maps_link = _get('google_maps_link', 'map_link', 'maps_link')
    n.cover_image_url = _get('cover_image_url', 'image_link')

    n.unrecognized_lines = data.get('unrecognized_lines', [])
    n.needs_review = data.get('needs_review', [])

    # Flag missing location
    if not n.location and not n.meta_location:
        n.needs_review.append('location: missing — please add manually')

    return n


def parsed_to_normalized(p: ParsedProperty) -> NormalizedProperty:
    """Convert ParsedProperty → NormalizedProperty via normalize_property."""
    return normalize_property({
        'raw_title': p.raw_title,
        'furnishing': p.furnishing,
        'bhk': p.bhk,
        'bathrooms': p.bathrooms,
        'bathroom_type': p.bathroom_type,
        'balconies': p.balconies,
        'has_utility': p.has_utility,
        'rent': p.rent,
        'maintenance': p.maintenance,
        'deposit': p.deposit,
        'area_sqft': p.area_sqft,
        'floor': p.floor,
        'available_from': p.available_from,
        'preferred_tenant': p.preferred_tenant,
        'diet_preference': p.diet_preference,
        'pets': p.pets,
        'community_type': p.community_type,
        'location': p.location,
        'property_name': p.property_name,
        'gallery_link': p.gallery_link,
        'google_maps_link': p.google_maps_link,
        'cover_image_url': p.cover_image_url,
        'unrecognized_lines': p.unrecognized_lines,
        'needs_review': p.needs_review,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Meta output builders
# ─────────────────────────────────────────────────────────────────────────────

def build_meta_title(prop: NormalizedProperty) -> str:
    """Format: {Furnishing} | {BHK-no-space} | {meta_location}
    BHK format: 2BHK, 3BHK, 2.5BHK (no space)
    """
    parts = []
    if prop.furnishing:
        parts.append(prop.furnishing)
    if prop.bhk:
        parts.append(f"{prop.bhk}BHK")
    if prop.meta_location:
        parts.append(prop.meta_location)
    return " | ".join(parts)


def build_meta_description(prop: NormalizedProperty) -> str:
    """Full Meta Catalogue description per spec."""
    title = build_meta_title(prop)
    lines = [title, ""]

    def _rent_display(v):
        if not v:
            return ''
        return _format_currency_display(v)

    def _plain_display(v):
        """For maintenance: preserve Inclusive/Water charges without ₹."""
        if not v:
            return ''
        if re.match(r'^[A-Za-z]', v.strip()):
            return v.strip()
        return _format_currency_display(v)

    if prop.rent:
        lines.append(f"Rent: {_rent_display(prop.rent)}")
    if prop.maintenance:
        lines.append(f"Maintenance: {_plain_display(prop.maintenance)}")
    if prop.deposit:
        lines.append(f"Deposit: {_rent_display(prop.deposit)}")
    if prop.area_sqft:
        lines.append(f"Sq. Ft.: {prop.area_sqft}")
    if prop.floor:
        lines.append(f"Floor: {prop.floor}")
    if prop.available_from:
        lines.append(f"Available From: {prop.available_from}")
    if prop.preferred_tenant:
        lines.append(f"Preferred Tenant: {prop.preferred_tenant}")
    if prop.diet_preference:
        lines.append(f"Diet Preference: {prop.diet_preference}")
    if prop.pets:
        lines.append(f"Pets: {prop.pets}")
    if prop.community_type:
        lines.append(f"Community: {prop.community_type}")
    if prop.furnishing:
        lines.append(f"Furnishing: {prop.furnishing}")
    if prop.location:
        lines.append(f"Location: {prop.location}")
    lines.append("")
    if prop.property_name:
        lines.append(f"*{prop.property_name}*")
        if prop.google_maps_link:
            lines.append(f"\U0001f4cd Maps: {prop.google_maps_link}")
    else:
        if prop.google_maps_link:
            lines.append(f"\U0001f5fa\U0001f4cd\U0001f5fa Maps: {prop.google_maps_link}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# WhatsApp title builder
# ─────────────────────────────────────────────────────────────────────────────

def _bath_phrase(bathrooms: str, bathroom_type: str) -> str:
    """Return bathroom phrase: 3 Bath / 3 Bathrooms / 3 Attached Bathrooms."""
    n = bathrooms.strip() if bathrooms else ""
    if not n:
        return ""
    try:
        count = float(n)
    except ValueError:
        count = 0
    type_prefix = "Attached " if bathroom_type and bathroom_type.lower() == "attached" else ""
    if count == 1:
        return f"{n} {type_prefix}Bath"
    return f"{n} {type_prefix}Bathrooms"


def _balcony_phrase(balconies: str) -> str:
    n = balconies.strip() if balconies else ""
    if not n:
        return ""
    try:
        count = float(n)
    except ValueError:
        count = 0
    if count == 1:
        return f"{n} Balcony"
    return f"{n} Balconies"


def build_whatsapp_title(prop: NormalizedProperty) -> str:
    """Format: {Furnishing} {BHK} BHK, {bath phrase} with {balcony phrase}{utility suffix}
    BHK format: 3 BHK (space), 2.5 BHK
    """
    furnishing = prop.furnishing or ""
    bhk_display = f"{prop.bhk} BHK" if prop.bhk else ""
    bath = _bath_phrase(prop.bathrooms, prop.bathroom_type)
    balcony = _balcony_phrase(prop.balconies)
    utility_suffix = " + Utility" if prop.has_utility else ""

    base = f"{furnishing} {bhk_display}".strip()
    if bath and balcony:
        return f"{base}, {bath} with {balcony}{utility_suffix}"
    elif bath:
        return f"{base}, {bath}{utility_suffix}"
    elif balcony:
        return f"{base} with {balcony}{utility_suffix}"
    return base


# ─────────────────────────────────────────────────────────────────────────────
# WhatsApp caption / message builder
# ─────────────────────────────────────────────────────────────────────────────

def build_whatsapp_caption(prop: NormalizedProperty) -> str:
    """Full WhatsApp listing caption per spec."""
    wa_title = build_whatsapp_title(prop)
    lines = [f"*\U0001f449{wa_title}*", ""]

    def _rent_display(v):
        if not v:
            return ''
        return _format_currency_display(v)

    def _plain_display(v):
        if not v:
            return ''
        if re.match(r'^[A-Za-z]', v.strip()):
            return v.strip()
        return _format_currency_display(v)

    if prop.rent:
        lines.append(f"Rent: {_rent_display(prop.rent)}")
    if prop.maintenance:
        lines.append(f"Maintenance: {_plain_display(prop.maintenance)}")
    if prop.deposit:
        lines.append(f"Deposit: {_rent_display(prop.deposit)}")
    if prop.area_sqft:
        lines.append(f"Sq. Ft.: {prop.area_sqft}")
    if prop.floor:
        lines.append(f"Floor: {prop.floor}")
    if prop.available_from:
        lines.append(f"Available From: {prop.available_from}")
    if prop.preferred_tenant:
        lines.append(f"Preferred Tenant: {prop.preferred_tenant}")
    # Omit Diet Preference if No Preference
    if prop.diet_preference and prop.diet_preference.lower() not in ('no preference', 'none', 'no'):
        lines.append(f"Diet Preference: {prop.diet_preference}")
    if prop.pets:
        lines.append(f"Pets: {prop.pets}")
    if prop.community_type:
        lines.append(f"Community: {prop.community_type}")
    if prop.location:
        lines.append(f"Location: *{prop.location}*")
    if prop.gallery_link:
        lines.append("")
        lines.append(f"*\U0001f4f8 Gallery:* {prop.gallery_link}")
    lines.append("")
    if prop.property_name:
        lines.append(f"*{prop.property_name}*")
    if prop.google_maps_link:
        lines.append(f"\U0001f4cd Map: {prop.google_maps_link}")
    return "\n".join(lines)


def build_whatsapp_message(prop: NormalizedProperty) -> str:
    """Alias for build_whatsapp_caption (same content, used when no image)."""
    return build_whatsapp_caption(prop)
