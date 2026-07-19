"""All 11 mandatory regression fixtures.
Each entry: raw_dump, expected canonical fields, expected Meta title/description heading, expected WhatsApp heading.
"""

FIXTURES = [
    # 1. Mahaveer Ranches
    {
        "id": 1,
        "name": "Mahaveer Ranches",
        "raw": """Semi Furnished 3 BHK, 3 Bath with 1 balcony + utility

Rent: 60k
Maintenance: 5.5k
Deposit : 2.5L
Sqft : 1726
Floor : 12/14
Available from : August 1
Preferred tenant : anyone
Pets : not allowed
Community: Gated
Location: Hosa Road, Off Sarjapur Road

*Mahaveer Ranches*
https://maps.app.goo.gl/NEK12TbhnSQNT8ni6?g_st=ic""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "3",
            "bathrooms": "3",
            "balconies": "1",
            "has_utility": True,
            "rent": "60k",
            "maintenance": "5.5k",
            "deposit": "2.5L",
            "area_sqft": "1726",
            "floor": "12/14",
            "available_from": "August 1",
            "property_name": "Mahaveer Ranches",
            "location": "Hosa Road, Off Sarjapur Road",
        },
        "meta_title": "Semi Furnished | 3BHK | Hosa Road",
        "whatsapp_heading": "Semi Furnished 3 BHK, 3 Bath with 1 Balcony + Utility",
    },
    # 2. Orchid Lakeview
    {
        "id": 2,
        "name": "Orchid Lakeview",
        "raw": """Fully Furnished 3 BHK with 3 Bathrooms, 5 balconies & Utility

Rent: 1L
Maintenance: Inclusive
Deposit: 4L
Sqft: 1800
Floor: 13/14
Available from: September 1
Preferred tenant: Anyone
Pets: not allowed
Community: Gated Community
Location: Bellandur

*Orchid Lakeview*
https://maps.app.goo.gl/ccbUb3wm3qrybCkw9?g_st=iwb""",
        "expected": {
            "furnishing": "Fully Furnished",
            "bhk": "3",
            "bathrooms": "3",
            "balconies": "5",
            "has_utility": True,
            "rent": "1L",
            "maintenance": "Inclusive",
            "deposit": "4L",
            "area_sqft": "1800",
            "floor": "13/14",
            "available_from": "September 1",
            "property_name": "Orchid Lakeview",
            "location": "Bellandur",
        },
        "meta_title": "Fully Furnished | 3BHK | Bellandur",
        "whatsapp_heading": "Fully Furnished 3 BHK, 3 Bathrooms with 5 Balconies + Utility",
    },
    # 3. SJR Primecorp Vogue Residences
    {
        "id": 3,
        "name": "SJR Primecorp Vogue Residences",
        "raw": """Fully Furnished 3 BHK with 3 Bathrooms, 2 Balconies & Utility.

Rent: \u20b990k
Maintenance: \u20b96.7k
Deposit: \u20b93.6L
Sqft: 1775
Floor: 6/14
Available from: September 1
Preferred tenant: Anyone
Pets: Allowed
Community: Gated Community
Location: Hoodi

*SJR Primecorp Vogue Residences*
https://maps.app.goo.gl/aHL7XDcHMCESAg8U8?g_st=ic""",
        "expected": {
            "furnishing": "Fully Furnished",
            "bhk": "3",
            "bathrooms": "3",
            "balconies": "2",
            "has_utility": True,
            "rent": "90k",
            "maintenance": "6.7k",
            "deposit": "3.6L",
            "area_sqft": "1775",
            "floor": "6/14",
            "available_from": "September 1",
            "property_name": "SJR Primecorp Vogue Residences",
            "location": "Hoodi",
        },
        "meta_title": "Fully Furnished | 3BHK | Hoodi",
        "whatsapp_heading": "Fully Furnished 3 BHK, 3 Bathrooms with 2 Balconies + Utility",
    },
    # 4. Signifa Springs
    {
        "id": 4,
        "name": "Signifa Springs",
        "raw": """Semi-Furnished 2 BHK with 2 Bathrooms and 1 balcony

Rent: 42k
Maintenance: 5k
Deposit: 1.5L
Sqft: 1200
Floor: 2/3
Available from: September 1
Preferred tenant: Family
Pets: not allowed
Community: Gated
Location: Kadubesanahalli

*Signifa Springs*
https://maps.app.goo.gl/PGYNRt3xw1pPpEd77?g_st=ic""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "2",
            "bathrooms": "2",
            "balconies": "1",
            "has_utility": False,
            "rent": "42k",
            "maintenance": "5k",
            "deposit": "1.5L",
            "area_sqft": "1200",
            "floor": "2/3",
            "available_from": "September 1",
            "property_name": "Signifa Springs",
            "location": "Kadubesanahalli",
        },
        "meta_title": "Semi Furnished | 2BHK | Kadubesanahalli",
        "whatsapp_heading": "Semi Furnished 2 BHK, 2 Bathrooms with 1 Balcony",
    },
    # 5. Meda Heights
    {
        "id": 5,
        "name": "Meda Heights",
        "raw": """Semi Furnished 2 BHK with 2 Bathrooms, 1 Balcony & Utility

Rent : 60k
Maintenance : 4.5k
Deposit : 2.5L
Sqft : 1200
Floor : 1/14
Available from : August 16
Preferred tenant : Family
Pets : allowed
Community: Gated
Location: Bellandur

*Meda Heights*
https://maps.app.goo.gl/JZ1SkmRUgZzuV3wSA?g_st=iwb""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "2",
            "bathrooms": "2",
            "balconies": "1",
            "has_utility": True,
            "rent": "60k",
            "maintenance": "4.5k",
            "deposit": "2.5L",
            "area_sqft": "1200",
            "floor": "1/14",
            "available_from": "August 16",
            "property_name": "Meda Heights",
            "location": "Bellandur",
        },
        "meta_title": "Semi Furnished | 2BHK | Bellandur",
        "whatsapp_heading": "Semi Furnished 2 BHK, 2 Bathrooms with 1 Balcony + Utility",
    },
    # 6. Prima Hilife (no location)
    {
        "id": 6,
        "name": "Prima Hilife",
        "raw": """Fully Furnished 3 BHK with 3 Attached Bathrooms, 5 Balcony & Utility

Rent: 90k
Maintenance : Water charges
Deposit : 3L
Sqft : 2320
Floor : 5/8
Available from : August 10
Preferred tenant : Anyone
Pets : Not Allowed
Community: Gated

*Prima Hilife*
https://maps.app.goo.gl/hLK5ckHXX3p3jgUu6?g_st=iwb""",
        "expected": {
            "furnishing": "Fully Furnished",
            "bhk": "3",
            "bathrooms": "3",
            "bathroom_type": "Attached",
            "balconies": "5",
            "has_utility": True,
            "rent": "90k",
            "maintenance": "Water charges",
            "deposit": "3L",
            "area_sqft": "2320",
            "floor": "5/8",
            "available_from": "August 10",
            "property_name": "Prima Hilife",
            "location": "",  # no location in raw
        },
        "meta_title": "Fully Furnished | 3BHK",
        "whatsapp_heading": "Fully Furnished 3 BHK, 3 Attached Bathrooms with 5 Balconies + Utility",
    },
    # 7. Trifecta Joli
    {
        "id": 7,
        "name": "Trifecta Joli",
        "raw": """Semi-Furnished 3 BHK with 2 Bathrooms, 2 Balconies & Utility

Rent: 40k
Maintenance: 3826
Deposit: 2L
Sqft: 1280
Floor: 1/5
Available from: Immediately
Preferred tenant: Family
Pets: Allowed
Community: Gated
Location: Sarjapur Road

*Trifecta Joli*
https://maps.app.goo.gl/nNmy76NnwDh1qHGDA?g_st=ic""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "3",
            "bathrooms": "2",
            "balconies": "2",
            "has_utility": True,
            "rent": "40k",
            "maintenance": "3826",
            "deposit": "2L",
            "area_sqft": "1280",
            "floor": "1/5",
            "available_from": "Ready to occupy",
            "property_name": "Trifecta Joli",
            "location": "Sarjapur Road",
        },
        "meta_title": "Semi Furnished | 3BHK | Sarjapur Road",
        "whatsapp_heading": "Semi Furnished 3 BHK, 2 Bathrooms with 2 Balconies + Utility",
    },
    # 8. Candeur Landmark
    {
        "id": 8,
        "name": "Candeur Landmark",
        "raw": """Semi-Furnished 2 BHK, 2 Bathrooms, 2 Balconies & Utility.

Rent: 42k
Maintenance: 3996
Deposit: 2L
Sqft: 1110
Floor: 6/14
Available from: August 10
Preferred tenant: Anyone
Pets: Allowed
Community: Gated
Location: Varthur

*Candeur Landmark*
https://maps.app.goo.gl/5nqCqQtJ9jUjjx9w7?g_st=ic""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "2",
            "bathrooms": "2",
            "balconies": "2",
            "has_utility": True,
            "rent": "42k",
            "maintenance": "3996",
            "deposit": "2L",
            "area_sqft": "1110",
            "floor": "6/14",
            "available_from": "August 10",
            "property_name": "Candeur Landmark",
            "location": "Varthur",
        },
        "meta_title": "Semi Furnished | 2BHK | Varthur",
        "whatsapp_heading": "Semi Furnished 2 BHK, 2 Bathrooms with 2 Balconies + Utility",
    },
    # 9. Amrutha Heights
    {
        "id": 9,
        "name": "Amrutha Heights",
        "raw": """Semi Furnished 2.5 BHK with 2 Bathrooms 2 Balcony & Utility

Rent: \u20b943k
Maintenance: 5.1k
Deposit: 2.5l
Sq.ft: 1143
Floor: 6/14
Available From: Ready to occupy
Preferred Tenant: Anyone
Pets: Allowed
Community: Gated
Location: Nallurahalli, Whitefield

*Amrutha Heights*
https://maps.app.goo.gl/8CKXZdMXEC7mmctx5?g_st=ac""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "2.5",
            "bathrooms": "2",
            "balconies": "2",
            "has_utility": True,
            "rent": "43k",
            "maintenance": "5.1k",
            "deposit": "2.5l",
            "area_sqft": "1143",
            "floor": "6/14",
            "available_from": "Ready to occupy",
            "property_name": "Amrutha Heights",
            "location": "Nallurahalli, Whitefield",
        },
        "meta_title": "Semi Furnished | 2.5BHK | Nallurahalli",
        "whatsapp_heading": "Semi Furnished 2.5 BHK, 2 Bathrooms with 2 Balconies + Utility",
    },
    # 10. Mana Tropicale
    {
        "id": 10,
        "name": "Mana Tropicale",
        "raw": """Semi Furnished 2 BHK with 2 Bathrooms, 1 Balcony & Utility.

Rent : 40k
Maintenance : 3750
Deposit : 1.2L
Sqft : 1166
Floor : 1/5
Availabl from : August 1
Preferred tenant : Anyone
Pets : allowed
Community: Gated
Location: Off Sarjapur Road

*Mana Tropicale*
https://maps.app.goo.gl/k1paefa4oN7rtuP48?g_st=ic""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "2",
            "bathrooms": "2",
            "balconies": "1",
            "has_utility": True,
            "rent": "40k",
            "maintenance": "3750",
            "deposit": "1.2L",
            "area_sqft": "1166",
            "floor": "1/5",
            "available_from": "August 1",
            "property_name": "Mana Tropicale",
            "location": "Off Sarjapur Road",
        },
        "meta_title": "Semi Furnished | 2BHK | Off Sarjapur Road",
        "whatsapp_heading": "Semi Furnished 2 BHK, 2 Bathrooms with 1 Balcony + Utility",
    },
    # 11. Micasa
    {
        "id": 11,
        "name": "Micasa",
        "raw": """Semi-Furnished 2 BHK with 2 Bathrooms, 1 Balcony & Utility.

Rent: 45k
Maintenance: Inclusive
Deposit: 1L
Sqft: 1100
Floor: 3/4
Available from: August 1
Preferred tenant: Anyone
Pets: Allowed
Community: Semi Gated
Location: Shubh Enclave, Harlur

*Micasa:*
https://maps.app.goo.gl/bjTYNi6gWG6ceNy96?g_st=ac""",
        "expected": {
            "furnishing": "Semi Furnished",
            "bhk": "2",
            "bathrooms": "2",
            "balconies": "1",
            "has_utility": True,
            "rent": "45k",
            "maintenance": "Inclusive",
            "deposit": "1L",
            "area_sqft": "1100",
            "floor": "3/4",
            "available_from": "August 1",
            "property_name": "Micasa",
            "location": "Shubh Enclave, Harlur",
        },
        "meta_title": "Semi Furnished | 2BHK | Harlur",
        "whatsapp_heading": "Semi Furnished 2 BHK, 2 Bathrooms with 1 Balcony + Utility",
    },
]
