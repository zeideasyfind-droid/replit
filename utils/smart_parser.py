import re

def parse_property_text(raw):
    """
    Highly robust canonical parser for property descriptions.
    Handles all 15 UI fields with improved keyword detection and edge case handling.
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

    # --- 1. Furnishing (Check entire text for keywords) ---
    if re.search(r'fully\s*(?:furnished|permitted)', raw, re.IGNORECASE):
        extracted["furnishing"] = "Fully Furnished"
    elif re.search(r'semi[\s-]*(?:furnished|permitted)', raw, re.IGNORECASE):
        extracted["furnishing"] = "Semi-Furnished"
    elif re.search(r'unfurnished|bare[\s-]*shell', raw, re.IGNORECASE):
        extracted["furnishing"] = "Unfurnished"

    # --- 2. BHK ---
    bhk_match = re.search(r'(\d)\s*(?:bhk|bedroom)', raw, re.IGNORECASE)
    if bhk_match:
        extracted["bhk"] = bhk_match.group(1) + " BHK"

    # --- 3. Rent / Price ---
    rent_match = re.search(r'rent\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if rent_match:
        extracted["rent"] = normalize_number_string(rent_match.group(1))
    else:
        # Look for standalone price patterns
        crore_m = re.search(r'([\d\.]+)\s*(?:cr|crore)', raw, re.IGNORECASE)
        lakh_m = re.search(r'([\d\.]+)\s*(?:l|lakh|lakhs)', raw, re.IGNORECASE)
        if crore_m: extracted["rent"] = str(int(float(crore_m.group(1)) * 1e7))
        elif lakh_m: extracted["rent"] = str(int(float(lakh_m.group(1)) * 1e5))

    # --- 4. Deposit ---
    deposit_match = re.search(r'deposit\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if deposit_match:
        extracted["deposit"] = normalize_number_string(deposit_match.group(1))

    # --- 5. Maintenance ---
    maint_match = re.search(r'maintenance\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if maint_match:
        extracted["maintenance"] = normalize_number_string(maint_match.group(1))

    # --- 6. Area / Sqft ---
    area_match = re.search(r'(?:sqft|area|size|sq\.?\s*ft\.?)\s*[:\-–]?\s*([\d,]+(?:\.\d+)?)', raw, re.IGNORECASE)
    if not area_match:
        area_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:sqft|sq\.?\s*ft\.?|square\s*feet)', raw, re.IGNORECASE)
    if area_match:
        extracted["sqft"] = area_match.group(1).replace(',', '')

    # --- 7. Floor (Handle "Villa" or numeric) ---
    floor_match = re.search(r'floor\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if floor_match:
        val = floor_match.group(1).strip()
        # If it says "Villa", use it, otherwise keep the value
        extracted["floor"] = val
    else:
        floor_num_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor', raw, re.IGNORECASE)
        if floor_num_match:
            extracted["floor"] = floor_num_match.group(1)

    # --- 8. Available From ---
    avail_match = re.search(r'available\s*(?:from)?\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if avail_match:
        extracted["available_from"] = avail_match.group(1).strip()

    # --- 9. Preferred Tenant ---
    if re.search(r'\b(?:family|families)\b', raw, re.IGNORECASE) and re.search(r'working|professional', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Family / Working Professionals"
    elif re.search(r'\b(?:family|families)\b', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Family"
    elif re.search(r'working|professional', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Working Professionals"
    elif re.search(r'anyone|any', raw, re.IGNORECASE):
        extracted["preferred_tenant"] = "Anyone"

    # --- 10. Diet Preference ---
    if re.search(r'vegetarian\s*only|only\s*vegetarian', raw, re.IGNORECASE):
        extracted["diet_preference"] = "Vegetarian"
    elif re.search(r'non-vegetarian|non\s*veg', raw, re.IGNORECASE):
        extracted["diet_preference"] = "Non-Vegetarian"
    else:
        extracted["diet_preference"] = "" # Left blank for "No Preference" in UI

    # --- 11. Pets ---
    if re.search(r'pets\s*[:\-–]?\s*(?:allowed|yes|ok)', raw, re.IGNORECASE):
        extracted["pets"] = "Allowed"
    elif re.search(r'pets\s*[:\-–]?\s*(?:not allowed|no|not permitted)', raw, re.IGNORECASE):
        extracted["pets"] = "Not Allowed"

    # --- 12. Community Type ---
    if re.search(r'community\s*[:\-–]?\s*gated|gated\s*community|gated\s*society|society\s*[:\-–]?\s*gated', raw, re.IGNORECASE):
        extracted["community"] = "Gated"
    elif re.search(r'semi-gated', raw, re.IGNORECASE):
        extracted["community"] = "Semi-Gated"
    elif re.search(r'non-society|independent', raw, re.IGNORECASE):
        extracted["community"] = "Non-Society"

    # --- 13. Location ---
    loc_match = re.search(r'location\s*[:\-–]?\s*\*?([^\*\n]+)\*?', raw, re.IGNORECASE)
    if loc_match:
        extracted["location"] = loc_match.group(1).strip()

    # --- 14. Property Name (Improved detection) ---
    # 1. Look for bold text that isn't the location or a link
    bold_texts = re.findall(r'\*([^\*\n]{3,})\*', raw)
    for bt in bold_texts:
        bt = bt.strip()
        if bt.lower() != extracted.get("location", "").lower() and not re.search(r'https?://', bt):
            extracted["property_name"] = bt
            break
    
    # 2. Fallback: Check line immediately above the maps link
    if not extracted["property_name"]:
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            if re.search(r'https?://(?:maps\.google\.com|goo\.gl/maps|maps\.app\.goo\.gl)', line):
                if i > 0:
                    potential_name = lines[i-1].replace('*', '').strip()
                    if potential_name.lower() != extracted.get("location", "").lower():
                        extracted["property_name"] = potential_name
                        break

    # --- 15. Links ---
    maps_match = re.search(r'https?://(?:maps\.google\.com|goo\.gl/maps|maps\.app\.goo\.gl|www\.google\.com/maps)[^\s]*', raw, re.IGNORECASE)
    if maps_match:
        extracted["map_link"] = maps_match.group(0)

    # --- 16. Title Generation ---
    if not extracted["title"] and extracted.get("bhk"):
        furnish = extracted.get("furnishing", "")
        loc = extracted.get("location", "")
        title_base = f"{furnish} {extracted['bhk']}" if furnish else f"{extracted['bhk']} Property"
        extracted["title"] = f"{title_base} • {loc}" if loc else title_base

    return extracted

def normalize_number_string(s):
    """Convert '42k' to '42000', '2L' to '200000', etc."""
    s = s.lower().replace('₹', '').replace('rs', '').replace('.', '').replace(',', '').strip()
    match = re.search(r'([\d\.]+)\s*([klmcr]*)', s)
    if not match: return s
    
    try:
        num = float(match.group(1))
        suffix = match.group(2)
        if suffix == 'k': num *= 1000
        elif suffix == 'l': num *= 100000
        elif suffix == 'cr': num *= 10000000
        return str(int(num))
    except:
        return s

if __name__ == "__main__":
    test_raw = """
Semi-Furnished 2 BHK, 2 Bathrooms, 2 Balconies & Utility.

Rent: 42k
Maintenance: 3996
Deposit: 2L
Sqft: 1110
Floor: Villa
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
