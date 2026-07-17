import os
import json
import logging
import sys
from typing import List, Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils.auth import verify_admin
from services.cloudinary_service import upload_images
from services.meta_catalog_service import create_or_update_catalog_item, get_debug_info
from services.whatsapp_service import send_confirmation

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Startup secret validation ─────────────────────────────────────────────────
REQUIRED_SECRETS = [
    "META_CATALOG_ID",
    "META_APP_ID",
    "META_ACCESS_TOKEN",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_RECIPIENT_NUMBER",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
    "GOOGLE_MAPS_API_KEY",
    "ADMIN_AUTH_TOKEN",
]


def validate_secrets() -> None:
    missing = [key for key in REQUIRED_SECRETS if not os.environ.get(key)]
    if missing:
        msg = (
            "FATAL: The following required environment variables are not set:\n  "
            + "\n  ".join(missing)
            + "\nPlease add them as Replit Secrets and restart the app."
        )
        logger.error(msg)
        sys.exit(1)
    logger.info("All required secrets present ✓")


validate_secrets()

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="EasyFind Admin", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("1", "true", "yes")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to admin property form (with same auth)."""
    token = request.query_params.get("token", "")
    url = f"/admin/property?token={token}" if token else "/admin/property"
    return HTMLResponse(content=f'<meta http-equiv="refresh" content="0; url={url}">', status_code=302)


@app.get("/admin/property", response_class=HTMLResponse)
async def admin_property_form(request: Request, _: None = Depends(verify_admin)):
    token = request.query_params.get("token", "")
    return templates.TemplateResponse(
        "admin_property.html",
        {"request": request, "token": token, "mock_mode": MOCK_MODE},
    )


@app.post("/admin/property", response_class=HTMLResponse)
async def admin_property_submit(
    request: Request,
    _: None = Depends(verify_admin),
    property_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    price: str = Form(...),
    currency: str = Form("INR"),
    city: str = Form(...),
    locality: str = Form(...),
    bhk: str = Form(...),
    property_type: str = Form(...),
    availability: str = Form(...),
    images: List[UploadFile] = File(...),
):
    token = request.query_params.get("token", "")
    errors = []
    result_ctx = {}

    # ── 1. Upload images to Cloudinary ────────────────────────────────────────
    image_urls: List[str] = []
    if MOCK_MODE:
        image_urls = [
            f"https://res.cloudinary.com/dcvwsclyc/image/upload/v1/mock_{property_id}_0.jpg"
        ]
        logger.info("[MOCK] Skipping Cloudinary upload, using mock URL.")
    else:
        valid_images = [f for f in images if f.filename]
        if not valid_images:
            errors.append("At least one image is required.")
        else:
            try:
                image_urls = await upload_images(valid_images, property_id)
            except Exception as exc:
                errors.append(f"Image upload failed: {exc}")

    if errors:
        return templates.TemplateResponse(
            "admin_property.html",
            {
                "request": request,
                "token": token,
                "mock_mode": MOCK_MODE,
                "errors": errors,
                "form_data": {
                    "property_id": property_id, "title": title,
                    "description": description, "price": price,
                    "currency": currency, "city": city,
                    "locality": locality, "bhk": bhk,
                    "property_type": property_type, "availability": availability,
                },
            },
            status_code=400,
        )

    image_link = image_urls[0] if image_urls else ""

    property_data = {
        "property_id": property_id,
        "title": title,
        "description": description,
        "price": price,
        "currency": currency,
        "city": city,
        "locality": locality,
        "bhk": bhk,
        "property_type": property_type,
        "availability": availability,
        "image_link": image_link,
        "all_image_urls": image_urls,
    }

    # ── 2. Meta catalog creation ───────────────────────────────────────────────
    meta_response = None
    meta_error = None
    if MOCK_MODE:
        meta_response = {"handles": ["mock_handle_abc123"], "mock": True}
        logger.info("[MOCK] Skipping Meta catalog API.")
    else:
        try:
            meta_response = await create_or_update_catalog_item(property_data)
        except Exception as exc:
            meta_error = str(exc)
            logger.error("[Meta] Catalog creation failed: %s", meta_error)

    # ── 3. WhatsApp confirmation (non-blocking) ───────────────────────────────
    whatsapp_result = {"status": "skipped"}
    if not meta_error:
        if MOCK_MODE:
            whatsapp_result = {"status": "skipped (mock mode)"}
        else:
            whatsapp_result = await send_confirmation(property_data)

    # ── 4. Google Maps link ───────────────────────────────────────────────────
    maps_query = f"{locality}, {city}"
    maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query.replace(' ', '+')}"

    result_ctx = {
        "request": request,
        "token": token,
        "mock_mode": MOCK_MODE,
        "property": property_data,
        "meta_response": json.dumps(meta_response, indent=2) if meta_response else None,
        "meta_error": meta_error,
        "whatsapp_result": whatsapp_result,
        "maps_link": maps_link,
        "image_urls": image_urls,
    }

    return templates.TemplateResponse("success.html", result_ctx, status_code=200 if not meta_error else 422)


@app.get("/catalog/property/{property_id}")
async def catalog_debug(property_id: str, request: Request, _: None = Depends(verify_admin)):
    """Return last payload and raw Meta response for a property. Protected by admin token."""
    info = get_debug_info(property_id)
    if not info.get("payload") and not info.get("response"):
        raise HTTPException(status_code=404, detail=f"No debug data found for property_id: {property_id}")
    return JSONResponse(content={
        "property_id": property_id,
        "last_payload_sent_to_meta": info.get("payload"),
        "last_meta_response": info.get("response"),
    })


@app.get("/health")
async def health():
    return {"status": "ok", "mock_mode": MOCK_MODE}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
