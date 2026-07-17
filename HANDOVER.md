# EasyFind Property Admin — Agent Handover

## What this project is

An **internal admin web app** for EasyFind Property Solutions. An operator fills in property details, uploads photos, and the app automatically:
1. Uploads images to **Cloudinary**
2. Creates/updates a listing in a **Meta Commerce Catalog** (linked to WhatsApp Business)
3. Sends a **WhatsApp confirmation message** to a fixed recipient number

There is no public-facing frontend — this is an operator-only tool.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Web framework | FastAPI 0.111.0 |
| Templating | Jinja2 (server-rendered HTML) |
| Frontend | Vanilla JS + CSS (no build step) |
| Image hosting | Cloudinary |
| Property catalog | Meta Graph API v25.0 (`items_batch` endpoint) |
| Notifications | WhatsApp Business API v18.0 |
| Runtime | Replit (port 5000, `python main.py`) |

---

## File structure

```
main.py                         FastAPI app entry point; all routes; startup secret validation
requirements.txt                7 packages (see below)
.replit                         Workflow config + non-sensitive env vars
services/
  cloudinary_service.py         Uploads UploadFile objects → returns secure_url list
  meta_catalog_service.py       items_batch POST; retries with UPDATE if CREATE fails; in-memory debug store
  whatsapp_service.py           Non-blocking WhatsApp text message after catalog creation
utils/
  auth.py                       Verifies ADMIN_AUTH_TOKEN via ?token= or Authorization: Bearer
templates/
  admin_property.html           The full property form (4 sections, smart paste, gallery, cover picker)
  success.html                  Result page (Meta response, WhatsApp status, image thumbnails)
static/
  style.css                     All styles — section cards, gallery grid, chip input, toast, action bar
```

---

## Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | none | Redirects to `/admin/property` (passes token through if present) |
| GET | `/admin/property?token=<tok>` | token | Renders the property submission form |
| POST | `/admin/property?token=<tok>` | token | Processes form: Cloudinary → Meta → WhatsApp → renders success.html |
| GET | `/catalog/property/{property_id}` | token | Debug endpoint — returns last Meta payload + response for that property_id |
| GET | `/health` | none | `{"status": "ok", "mock_mode": false}` |

Authentication is a shared static token (`ADMIN_AUTH_TOKEN`), accepted as `?token=VALUE` in the URL or as `Authorization: Bearer VALUE` header. Any route that requires auth will return **401** if the token is wrong or missing.

---

## Form sections

The property form (`/admin/property`) has four named sections:

- **A — Property Details**: title, type, listing type, price, currency, deposit, maintenance, BHK, bedrooms, bathrooms, furnishing, area (super/carpet), facing, floor/total floors, parking, amenities (chip input), broker name, phone
- **B — Location**: building name, flat number, street, landmark, locality, city, state, pincode, Google Maps link, lat/long; live address preview builds as you type
- **C — Images**: drag-and-drop file upload + paste image URLs (newline-separated); images stored in a gallery grid
- **D — Cover Image**: star-mark any gallery image as cover; cover becomes `image_link` sent to Meta

Additional UX: **Smart Paste** — paste raw text (WhatsApp forward, broker listing) into a text area and click "Map Fields"; client-side JS extracts BHK, price, furnishing, area, floor, facing, city, landmark, phone, Maps link, amenities, and image URLs via regex.

Auto-saves a draft to `sessionStorage` every 30 seconds; draft is cleared on successful submit.

---

## Backend flow (POST /admin/property)

1. **Validate** at least one image (file upload or pasted URL)
2. **Upload** file images to Cloudinary → get `secure_url` list
3. **Combine** Cloudinary URLs + pasted URLs into `all_image_urls`
4. **Reorder** so the selected cover image is index 0 (`image_link` for Meta)
5. **POST** to Meta `items_batch` with `method: CREATE`; if Meta returns no handles + validation errors → retry with `method: UPDATE`
6. **Send WhatsApp** confirmation (non-blocking — catalog success is unaffected by WhatsApp failure)
7. **Render** `success.html`

---

## Environment variables

See `.env.example` (in this repo) for the complete list with descriptions.

**Sensitive (Replit Secrets):**

| Variable | Used by |
|----------|---------|
| `ADMIN_AUTH_TOKEN` | `utils/auth.py` — gate on all admin routes |
| `META_ACCESS_TOKEN` | `services/meta_catalog_service.py` — Meta Graph API |
| `WHATSAPP_ACCESS_TOKEN` | `services/whatsapp_service.py` — WhatsApp Business API |
| `CLOUDINARY_API_KEY` | `services/cloudinary_service.py` |
| `CLOUDINARY_API_SECRET` | `services/cloudinary_service.py` |
| `GOOGLE_MAPS_API_KEY` | Available in env; currently not called server-side (reserved for future geocoding) |
| `SESSION_SECRET` | Declared in Replit Secrets; not yet used in code (reserved for cookie-based login — Task #2) |

**Non-sensitive (already in `.replit` `[userenv.shared]`):**

| Variable | Value |
|----------|-------|
| `CLOUDINARY_CLOUD_NAME` | `dcvwsclyc` |
| `META_APP_ID` | `1897860514267804` |
| `META_CATALOG_ID` | `1674288420320509` |
| `WHATSAPP_PHONE_NUMBER_ID` | `1085572627976973` |
| `WHATSAPP_RECIPIENT_NUMBER` | `919148338801` |

**Optional:**

| Variable | Effect |
|----------|--------|
| `MOCK_MODE=true` | Skips all real API calls (Cloudinary, Meta, WhatsApp); safe for local testing |
| `PORT` | Override server port (default: `5000`) |

---

## Startup behaviour

`validate_secrets()` runs at import time in `main.py`. If **any** of the 11 required variables is unset, the process logs `FATAL:` and exits with code 1. The app will not start at all with missing config — this is intentional so misconfiguration is obvious rather than silent.

---

## Dependencies (`requirements.txt`)

```
aiofiles==23.2.1
cloudinary==1.40.0
fastapi==0.111.0
httpx==0.27.0
jinja2==3.1.4
python-multipart==0.0.9
uvicorn[standard]==0.29.0
```

No build step. Install with `pip install -r requirements.txt`.

---

## How to run locally (or in a fresh Replit)

1. Set all secrets listed in `.env.example` (see Replit Secrets panel or export them in your shell)
2. `pip install -r requirements.txt`
3. `python main.py`
4. Open `http://localhost:5000/admin/property?token=<ADMIN_AUTH_TOKEN>`

Or set `MOCK_MODE=true` to skip all external API calls during development.

---

## Proposed / open tasks (as of handover)

| Task | Description |
|------|-------------|
| **Task #2** | Login page — so the operator doesn't have to paste the token into the URL every visit. `SESSION_SECRET` is already in Replit Secrets, reserved for this. |
| **Task #3** | Persist the Meta debug store to disk — currently it's an in-memory dict in `meta_catalog_service.py` and is wiped on every restart. |
| **Task #4** | Image upload error handling — if Cloudinary fails, the current form shows an error page; consider surfacing the error inline and letting the operator retry rather than losing the whole form state. |

---

## Key decisions to preserve

- **WhatsApp failure is non-blocking.** Catalog creation always completes; WhatsApp is best-effort.
- **Cover image is always index 0** in the array sent to Meta (`image_link`). The backend reorders the array before building the Meta payload — do not change this without also updating `_build_item()` in `meta_catalog_service.py`.
- **Smart paste is entirely client-side.** No AI API. Pure regex extraction in `admin_property.html`.
- **No database.** The Meta debug store is in-memory only. There is no persistence layer yet (that's Task #3).
- **Secrets are never in source files.** Non-sensitive IDs live in `.replit` `[userenv.shared]`; tokens/keys live only in Replit Secrets.
