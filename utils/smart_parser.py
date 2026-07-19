import re

def parse_property_text(raw):
    """
    Parser optimized for the user's specific format.
    Ensures correct mapping of all 15 fields without swapping.
    """
    lines = [l.strip() for l in raw.split('\n') if l.strip()]
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

    if not lines:
        return extracted

    # --- 1. Title (First line is the descriptive title) ---
    extracted["title"] = lines[0].replace('*', '').strip()

    # --- 2. Furnishing (Global check) ---
    if re.search(r'fully\s*(?:furnished|permitted)', raw, re.IGNORECASE):
        extracted["furnishing"] = "Fully Furnished"
    elif re.search(r'semi[\s-]*(?:furnished|permitted)', raw, re.IGNORECASE):
        extracted["furnishing"] = "Semi-Furnished"
    elif re.search(r'unfurnished|bare[\s-]*shell', raw, re.IGNORECASE):
        extracted["furnishing"] = "Unfurnished"

    # --- 3. Rent / Price ---
    rent_m = re.search(r'rent\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if rent_m:
        extracted["rent"] = normalize_number_string(rent_m.group(1))

    # --- 4. Maintenance ---
    maint_m = re.search(r'maintenance\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if maint_m:
        extracted["maintenance"] = normalize_number_string(maint_m.group(1))

    # --- 5. Deposit ---
    deposit_m = re.search(r'deposit\s*[:\-–]?\s*([₹rs\.\s]*[\d,kL\.]+)', raw, re.IGNORECASE)
    if deposit_m:
        extracted["deposit"] = normalize_number_string(deposit_m.group(1))

    # --- 6. Area / Sqft (Look for 'Sqft:' or standalone numbers with 'sqft') ---
    sqft_m = re.search(r'sqft\s*[:\-–]?\s*([\d,]+)', raw, re.IGNORECASE)
    if not sqft_m:
        sqft_m = re.search(r'([\d,]+)\s*(?:sqft|sq\.?\s*ft|square\s*feet)', raw, re.IGNORECASE)
    if sqft_m:
        extracted["sqft"] = sqft_m.group(1).replace(',', '')

    # --- 7. Floor (Explicit check for 'Floor:' label) ---
    floor_m = re.search(r'floor\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if floor_m:
        extracted["floor"] = floor_m.group(1).strip()

    # --- 8. Available From ---
    avail_m = re.search(r'available\s*(?:from)?\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if avail_m:
        extracted["available_from"] = avail_m.group(1).strip()

    # --- 9. Preferred Tenant ---
    pref_m = re.search(r'preferred\s*tenant\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if pref_m:
        extracted["preferred_tenant"] = pref_m.group(1).strip()
    else:
        # Fallback keyword check
        if re.search(r'\b(?:family|families)\b', raw, re.IGNORECASE) and re.search(r'working|professional', raw, re.IGNORECASE):
            extracted["preferred_tenant"] = "Family / Working Professionals"
        elif re.search(r'\b(?:family|families)\b', raw, re.IGNORECASE):
            extracted["preferred_tenant"] = "Family"
        elif re.search(r'working|professional', raw, re.IGNORECASE):
            extracted["preferred_tenant"] = "Working Professionals"

    # --- 10. Diet Preference ---
    if re.search(r'vegetarian\s*only|only\s*vegetarian', raw, re.IGNORECASE):
        extracted["diet_preference"] = "Vegetarian"
    elif re.search(r'non-vegetarian|non\s*veg', raw, re.IGNORECASE):
        extracted["diet_preference"] = "Non-Vegetarian"

    # --- 11. Pets ---
    pets_m = re.search(r'pets\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if pets_m:
        val = pets_m.group(1).strip().lower()
        if 'allowed' in val or 'yes' in val: extracted["pets"] = "Allowed"
        elif 'not' in val or 'no' in val: extracted["pets"] = "Not Allowed"
    elif re.search(r'pets\s*[:\-–]?\s*(?:allowed|yes|ok)', raw, re.IGNORECASE):
        extracted["pets"] = "Allowed"

    # --- 12. Community ---
    comm_m = re.search(r'community\s*[:\-–]?\s*([^\n,]+)', raw, re.IGNORECASE)
    if comm_m:
        val = comm_m.group(1).strip().lower()
        if 'gated' in val: extracted["community"] = "Gated"
        elif 'semi' in val: extracted["community"] = "Semi-Gated"
    elif re.search(r'community\s*[:\-–]?\s*gated|gated\s*community', raw, re.IGNORECASE):
        extracted["community"] = "Gated"

    # --- 13. Location ---
    loc_m = re.search(r'location\s*[:\-–]?\s*\*?([^\*\n]+)\*?', raw, re.IGNORECASE)
    if loc_m:
        extracted["location"] = loc_m.group(1).strip()

    # --- 14. Property Name (Line above Maps link or bold text) ---
    for i, line in enumerate(lines):
        if re.search(r'https?://(?:maps\.google\.com|goo\.gl/maps|maps\.app\.goo\.gl)', line):
            if i > 0:
                potential = lines[i-1].replace('*', '').strip()
                if potential.lower() != extracted.get("location", "").lower():
                    extracted["property_name"] = potential
                    break
    
    if not extracted["property_name"]:
        bold_texts = re.findall(r'\*([^\*\n]{3,})\*', raw)
        for bt in bold_texts:
            bt = bt.strip()
            if bt.lower() != extracted.get("location", "").lower() and not re.search(r'https?://', bt):
                extracted["property_name"] = bt
                break

    # --- 15. Maps Link ---
    maps_m = re.search(r'https?://(?:maps\.google\.com|goo\.gl/maps|maps\.app\.goo\.gl|www\.google\.com/maps)[^\s]*', raw, re.IGNORECASE)
    if maps_m:
        extracted["map_link"] = maps_m.group(0)

    # --- BHK Extraction (for internal logic) ---
    bhk_m = re.search(r'(\d)\s*(?:bhk|bedroom)', raw, re.IGNORECASE)
    if bhk_m:
        extracted["bhk"] = bhk_m.group(1) + " BHK"

    return extracted

def normalize_number_string(s):
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
