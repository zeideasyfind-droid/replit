import re

def parse_property_text(raw):
    """
    Canonical parser for property descriptions.
    Handles common formats, abbreviations (k, L, Cr), and comma-separated numbers.
    """
    extracted = {
        "title": "",
        "rent": "",
        "maintenance": "",
        "deposit": "",
        "sqft": "",
        "floor": "",
        "furnishing": "",
        "available_from": "",
        "preferred_tenant": "",
        "diet_preference": "",
        "pets": "",
        "community": "",
        "location": "",
        "property_name": "",
        "map_link": "",
        "gallery_link": ""
    }

    # 1. Rent / Price
    # Look for explicit "Rent: ..." first
    rent_match = re.search(r'rent\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if rent_match:
        val = rent_match.group(1).lower()
        extracted["rent"] = normalize_number_string(val)
    else:
        # Fallback to general price patterns
        crore_m = re.search(r'([\d\.]+)\s*(?:cr|crore)', raw, re.IGNORECASE)
        lakh_m = re.search(r'([\d\.]+)\s*(?:l|lakh|lakhs)', raw, re.IGNORECASE)
        if crore_m: extracted["rent"] = str(int(float(crore_m.group(1)) * 1e7))
        elif lakh_m: extracted["rent"] = str(int(float(lakh_m.group(1)) * 1e5))

    # 2. Deposit
    deposit_match = re.search(r'deposit\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if deposit_match:
        extracted["deposit"] = normalize_number_string(deposit_match.group(1).lower())

    # 3. Maintenance
    maint_match = re.search(r'maintenance\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if maint_match:
        extracted["maintenance"] = normalize_number_string(maint_match.group(1).lower())

    # 4. Area / Sqft
    area_match = re.search(r'(?:sqft|area|size)\s*[:\-–]?\s*([\d,]+(?:\.\d+)?)', raw, re.IGNORECASE)
    if not area_match:
        area_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:sqft|sq\.?\s*ft\.?|square\s*feet)', raw, re.IGNORECASE)
    if area_match:
        extracted["sqft"] = area_match.group(1).replace(',', '')

    # 5. Floor
    floor_match = re.search(r'floor\s*[:\-–]?\s*([\d/]+)', raw, re.IGNORECASE)
    if not floor_match:
        floor_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor', raw, re.IGNORECASE)
    if floor_match:
        extracted["floor"] = floor_match.group(1)

    # 6. BHK
    bhk_match = re.search(r'(\d)\s*(?:bhk|bedroom)', raw, re.IGNORECASE)
    if bhk_match:
        extracted["bhk"] = bhk_match.group(1) + " BHK"

    # 7. Furnishing
    if re.search(r'fully\s*(?:furnished|permitted)', raw, re.IGNORECASE):
        extracted["furnishing"] = "Fully Furnished"
    elif re.search(r'semi[\s-]*(?:furnished|permitted)', raw, re.IGNORECASE):
        extracted["furnishing"] = "Semi-Furnished"
    elif re.search(r'unfurnished|bare[\s-]*shell', raw, re.IGNORECASE):
        extracted["furnishing"] = "Unfurnished"

    # 8. Available From
    avail_match = re.search(r'available\s*(?:from)?\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if avail_match:
        extracted["available_from"] = avail_match.group(1).strip()

    # 9. Preferred Tenant
    if re.search(r'\b(?:family|families)\b', raw, re.IGNORECASE) and re.search(r'working|professional', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Family / Working Professionals"
    elif re.search(r'\b(?:family|families)\b', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Family"
    elif re.search(r'working|professional', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Working Professionals"
    elif re.search(r'anyone|any', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Anyone"

    # 10. Pets
    if re.search(r'pets\s*[:\-–]?\s*(?:allowed|yes)', raw, re.IGNORECASE):
        extracted["pets"] = "Allowed"
    elif re.search(r'pets\s*[:\-–]?\s*(?:not allowed|no)', raw, re.IGNORECASE):
        extracted["pets"] = "Not Allowed"

    # 11. Community
    if re.search(r'community\s*[:\-–]?\s*gated|gated\s*community', raw, re.IGNORECASE):
        extracted["community"] = "Gated"

    # 12. Location & Property Name
    loc_match = re.search(r'location\s*[:\-–]?\s*\*?([^\*\n]+)\*?', raw, re.IGNORECASE)
    if loc_match:
        extracted["location"] = loc_match.group(1).strip()
    
    # Property Name often comes after location or in bold
    prop_name_match = re.search(r'\*([^\*\n]{3,})\*', raw)
    if prop_name_match:
        # If we already have location, the other bold text might be property name
        bold_texts = re.findall(r'\*([^\*\n]{3,})\*', raw)
        for bt in bold_texts:
            bt = bt.strip()
            if bt.lower() != extracted.get("location", "").lower() and "maps.app.goo.gl" not in bt:
                extracted["property_name"] = bt
                break

    # 13. Links
    maps_match = re.search(r'https?://(?:maps\.google\.com|goo\.gl/maps|maps\.app\.goo\.gl|www\.google\.com/maps)[^\s]*', raw, re.IGNORECASE)
    if maps_match:
        extracted["map_link"] = maps_match.group(0)

    # 14. Title Generation
    if not extracted["title"] and extracted.get("bhk"):
        loc = extracted.get("location", "")
        extracted["title"] = f"{extracted['bhk']} Property • {loc}" if loc else f"{extracted['bhk']} Property"

    return extracted

def normalize_number_string(s):
    """Convert '42k' to '42000', '2L' to '200000', etc."""
    s = s.replace('₹', '').replace('rs', '').replace('.', '').replace(',', '').strip()
    match = re.search(r'([\d\.]+)\s*([klmcr]*)', s, re.IGNORECASE)
    if not match: return s
    
    num = float(match.group(1))
    suffix = match.group(2).lower()
    
    if suffix == 'k': num *= 1000
    elif suffix == 'l': num *= 100000
    elif suffix == 'cr': num *= 10000000
    
    return str(int(num))

if __name__ == "__main__":
    test_raw = """
Semi-Furnished 2 BHK, 2 Bathrooms, 2 Balconies & Utility.

Rent: 42k
Maintenance: 3996
Deposit: 2L
Sqft: 1110
Floor: 6/14
Available from: August 10
Preferred tenant: Anyone
Pets: Allowed
Community: Gated
Location: *Varthur*

*Candeur Landmark* 
https://maps.app.goo.gl/5nqCqQtJ9jUjjx9w7?g_st=ic
"""
    import json
    print(json.dumps(parse_property_text(test_raw), indent=2))
