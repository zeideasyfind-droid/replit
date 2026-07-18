# EasyFind Property Admin

Internal admin web app for **EasyFind Property Solutions**. Three tools in one app, all protected by `ADMIN_AUTH_TOKEN`.

## Stack
- **Backend:** Python 3.11 + FastAPI
- **Frontend:** Server-rendered Jinja2 HTML + Vanilla JS/CSS (no build step)
- **Image storage:** Cloudinary
- **Catalog:** Meta Graph API v25.0 (`items_batch`)
- **Notifications:** WhatsApp Business API v18.0

## Running the app
```
python main.py
```
Server starts on port 5000. Open:
```
https://<your-repl>.replit.dev/?token=<ADMIN_AUTH_TOKEN>
```

## Tools

| URL | Description |
|-----|-------------|
| `/` | Home — landing page linking all three tools |
| `/single_upload` | WhatsApp Single Upload — fill one property, preview formatted message, download .txt + .json |
| `/bulk_upload` | WhatsApp Bulk Upload — add N properties, preview all messages, download ZIP |
| `/admin/property` | Meta Catalog Admin — submit property to Meta Commerce Catalog via Cloudinary + WhatsApp confirmation |

All routes require `?token=<ADMIN_AUTH_TOKEN>` in the URL (or `Authorization: Bearer` header).

## Project structure
```
main.py                         FastAPI entry point; all routes; startup secret validation
requirements.txt
utils/
  auth.py                       ADMIN_AUTH_TOKEN verification dependency
  formatters.py                 WhatsApp message formatter, Drive folder name generator
services/
  cloudinary_service.py         Upload images to Cloudinary
  meta_catalog_service.py       items_batch POST to Meta catalog
  whatsapp_service.py           WhatsApp Business API confirmation message
  bulk_processor.py             Batch-process properties into messages + folder names
templates/
  home.html                     Landing page (3 tool cards)
  single_upload.html            4-step single property wizard
  bulk_upload.html              4-step bulk property wizard
  admin_property.html           Meta catalog form
  success.html                  Meta catalog submission result
static/
  style.css                     Shared CSS design system
output/                         Generated .txt / .json / .zip files (served at /output/)
```

## Required secrets (Replit Secrets)
| Key | Used by |
|-----|---------|
| `ADMIN_AUTH_TOKEN` | All admin routes |
| `META_ACCESS_TOKEN` | Meta Graph API |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API |
| `CLOUDINARY_API_KEY` | Cloudinary upload |
| `CLOUDINARY_API_SECRET` | Cloudinary upload |
| `GOOGLE_MAPS_API_KEY` | Reserved (geocoding) |
| `SESSION_SECRET` | Reserved (future login page) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Reserved (future Google Sheets logging) |
| `CLIENT_MAIL` | Reserved (future Google Sheets logging) |

## Non-sensitive env vars (already in .replit)
`CLOUDINARY_CLOUD_NAME`, `META_APP_ID`, `META_CATALOG_ID`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_RECIPIENT_NUMBER`

## Optional
| Var | Effect |
|-----|--------|
| `MOCK_MODE=true` | Skip all real API calls (Cloudinary, Meta, WhatsApp) |
| `PORT` | Override server port (default: 5000) |

## User preferences
- Token passed as `?token=VALUE` URL query param (standard across all pages)
- No database — Meta debug store is in-memory; generated files saved to `output/`
- WhatsApp failure is non-blocking — catalog creation always completes
