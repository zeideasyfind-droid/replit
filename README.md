# EasyFind Property Admin

Internal admin web app for **EasyFind Property Solutions** — upload property images and details, auto-create/update items in your Meta Commerce catalog linked to WhatsApp Business, and send a WhatsApp confirmation message.

## Stack

- **Backend:** Python 3.11 + FastAPI
- **Frontend:** Server-rendered Jinja2 HTML/CSS/JS
- **Image storage:** Cloudinary
- **Catalog:** Meta Graph API v25.0 (`items_batch`)
- **Notifications:** WhatsApp Business API v18.0

---

## Replit Secrets Setup

Add the following keys as **Replit Secrets** (never in source files):

| Key | Description |
|-----|-------------|
| `META_CATALOG_ID` | Meta Commerce catalog ID |
| `META_APP_ID` | Meta App ID |
| `META_ACCESS_TOKEN` | Meta Graph API access token (with `catalog_management` permission) |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business access token |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp sender phone number ID |
| `WHATSAPP_RECIPIENT_NUMBER` | Recipient phone number (with country code, no `+`) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key (used for Maps links) |
| `ADMIN_AUTH_TOKEN` | Your own secure token to protect admin routes |

Non-sensitive IDs are set as plain environment variables via Replit's env var panel.

---

## Running on Replit

Click **Run** — the app starts automatically via the configured workflow.  
Access the admin form at:

```
https://<your-repl>.replit.dev/admin/property?token=<ADMIN_AUTH_TOKEN>
```

Or pass the token as a header:

```
Authorization: Bearer <ADMIN_AUTH_TOKEN>
```

---

## Optional: Mock Mode

Set `MOCK_MODE=true` as an environment variable to skip real API calls (useful for UI testing).

---

## Project Structure

```
main.py                        FastAPI app + startup secret validation
services/
  cloudinary_service.py        Upload images to Cloudinary
  meta_catalog_service.py      items_batch to Meta catalog
  whatsapp_service.py          WhatsApp Business message
utils/
  auth.py                      Admin token verification
templates/
  admin_property.html          Property submission form
  success.html                 Post-submit result page
static/
  style.css                    Mobile-first styles
requirements.txt
README.md
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/admin/property` | ✅ | Property submission form |
| `POST` | `/admin/property` | ✅ | Submit property to Meta catalog |
| `GET` | `/catalog/property/{id}` | ✅ | Debug: last payload + Meta response |
| `GET` | `/health` | ❌ | Health check |

---

## Example API Calls

### A) Get catalog details

```bash
curl -i -G \
  'https://graph.facebook.com/v25.0/$META_CATALOG_ID?fields=id,name,product_count' \
  -d 'access_token=YOUR_META_ACCESS_TOKEN'
```

### B) Create a real-estate sample product

```bash
curl -i -X POST \
  'https://graph.facebook.com/v25.0/$META_CATALOG_ID/items_batch' \
  -d 'item_type=PRODUCT_ITEM' \
  -d 'requests=[
  {
    "method": "CREATE",
    "data": {
      "id": "test_property_retailer_id_1",
      "title": "2 BHK Apartment • Sarjapur Road, Bengaluru",
      "description": "HTML <b>2 BHK</b> apartment near Sarjapur Road, Bengaluru.",
      "price": "30000 INR",
      "image_link": "https://res.cloudinary.com/dcvwsclyc/image/upload/v1/property_1.jpg",
      "link": "https://easyfindprops.com/property/test_property_retailer_id_1",
      "availability": "in stock",
      "condition": "new",
      "brand": "EasyFind Realty Solutions"
    }
  }
]' \
  -d 'access_token=YOUR_META_ACCESS_TOKEN'
```

### C) Fetch catalog products

```bash
curl -i -G \
  'https://graph.facebook.com/v25.0/$META_CATALOG_ID/products' \
  -d 'filter={"name":{"i_contains":"Apartment"}}' \
  -d 'fields=retailer_id,id,name,category,errors' \
  -d 'access_token=YOUR_META_ACCESS_TOKEN'
```
