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
from utils.formatters import format_whatsapp_message, generate_drive_folder_name
from services.cloudinary_service import upload_images
from services.meta_catalog_service import create_or_update_catalog_item, get_debug_info
from services.whatsapp_service import send_confirmation
from services.bulk_processor import BulkPropertyProcessor

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

import zipfile
from datetime import datetime
from pathlib import Path

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="EasyFind Admin", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
Path("output").mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")
templates = Jinja2Templates(directory="templates")

MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("1", "true", "yes")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "mock_mode": MOCK_MODE},
    )


@app.get("/admin/property", response_class=HTMLResponse)
async def admin_property_form(request: Request):
    return templates.TemplateResponse(
        "admin_property.html",
        {"request": request, "mock_mode": MOCK_MODE},
    )


@app.post("/admin/property", response_class=HTMLResponse)
async def admin_property_submit(
    request: Request,
    _: None = Depends(verify_admin),
    # ── Core fields (required) ────────────────────────────────────────────────
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
    # ── Extended property fields (optional) ──────────────────────────────────
    listing_type: str = Form(default=""),
    deposit: str = Form(default=""),
    maintenance: str = Form(default=""),
    bedrooms: str = Form(default=""),
    bathrooms: str = Form(default=""),
    furnishing: str = Form(default=""),
    area_super: str = Form(default=""),
    area_carpet: str = Form(default=""),
    facing: str = Form(default=""),
    floor: str = Form(default=""),
    total_floors: str = Form(default=""),
    parking: str = Form(default=""),
    amenities: str = Form(default=""),
    broker_name: str = Form(default=""),
    phone: str = Form(default=""),
    # ── Location fields (optional) ────────────────────────────────────────────
    building_name: str = Form(default=""),
    flat_number: str = Form(default=""),
    street: str = Form(default=""),
    landmark: str = Form(default=""),
    state: str = Form(default=""),
    pincode: str = Form(default=""),
    maps_link_field: str = Form(default="", alias="maps_link"),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    # ── Image fields ──────────────────────────────────────────────────────────
    pasted_image_urls: str = Form(default=""),
    cover_image_index: str = Form(default="0"),
    images: List[UploadFile] = File(default=[]),
):
    token = request.query_params.get("token", "")
    errors = []

    # ── 1. Upload file images to Cloudinary ───────────────────────────────────
    cloudinary_urls: List[str] = []
    if MOCK_MODE:
        cloudinary_urls = [
            f"https://res.cloudinary.com/dcvwsclyc/image/upload/v1/mock_{property_id}_0.jpg"
        ]
        logger.info("[MOCK] Skipping Cloudinary upload.")
    else:
        valid_images = [f for f in images if f.filename]
        if valid_images:
            try:
                cloudinary_urls = await upload_images(valid_images, property_id)
            except Exception as exc:
                errors.append(f"Image upload failed: {exc}")

    # ── 2. Combine with pasted URLs ───────────────────────────────────────────
    pasted_urls = [u.strip() for u in pasted_image_urls.splitlines() if u.strip()]
    all_image_urls = cloudinary_urls + pasted_urls

    # Validate: at least one image
    if not all_image_urls and not errors:
        errors.append("At least one image is required.")

    if errors:
        return templates.TemplateResponse(
            "admin_property.html",
            {
                "request": request, "token": token, "mock_mode": MOCK_MODE,
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

    # ── 3. Determine cover image ───────────────────────────────────────────────
    try:
        cover_idx = int(cover_image_index)
        if cover_idx < 0 or cover_idx >= len(all_image_urls):
            cover_idx = 0
    except (ValueError, TypeError):
        cover_idx = 0

    # Put cover first
    if cover_idx != 0 and all_image_urls:
        cover = all_image_urls.pop(cover_idx)
        all_image_urls.insert(0, cover)

    image_link = all_image_urls[0] if all_image_urls else ""

    # ── Build property_data dict ──────────────────────────────────────────────
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
        "listing_type": listing_type,
        "deposit": deposit,
        "maintenance": maintenance,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "furnishing": furnishing,
        "area_super": area_super,
        "area_carpet": area_carpet,
        "facing": facing,
        "floor": floor,
        "total_floors": total_floors,
        "parking": parking,
        "amenities": amenities,
        "broker_name": broker_name,
        "phone": phone,
        "building_name": building_name,
        "flat_number": flat_number,
        "street": street,
        "landmark": landmark,
        "state": state,
        "pincode": pincode,
        "maps_link": maps_link_field,
        "latitude": latitude,
        "longitude": longitude,
        "image_link": image_link,
        "all_image_urls": all_image_urls,
    }

    # ── 4. Meta catalog creation ───────────────────────────────────────────────
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

    # ── 5. WhatsApp confirmation (non-blocking) ───────────────────────────────
    whatsapp_result = {"status": "skipped"}
    if not meta_error:
        if MOCK_MODE:
            whatsapp_result = {"status": "skipped (mock mode)"}
        else:
            whatsapp_result = await send_confirmation(property_data)

    # ── 6. Google Maps link ───────────────────────────────────────────────────
    maps_query = f"{locality}, {city}"
    auto_maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query.replace(' ', '+')}"
    final_maps_link = maps_link_field if maps_link_field else auto_maps_link

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request, "token": token, "mock_mode": MOCK_MODE,
            "property": property_data,
            "meta_response": json.dumps(meta_response, indent=2) if meta_response else None,
            "meta_error": meta_error,
            "whatsapp_result": whatsapp_result,
            "maps_link": final_maps_link,
            "image_urls": all_image_urls,
        },
        status_code=200 if not meta_error else 422,
    )


@app.get("/catalog/property/{property_id}")
async def catalog_debug(property_id: str, request: Request, _: None = Depends(verify_admin)):
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


# ── Single Upload Flow ────────────────────────────────────────────────────────

@app.get("/single_upload", response_class=HTMLResponse)
async def single_upload_page(request: Request):
    return templates.TemplateResponse(
        "single_upload.html",
        {"request": request},
    )


@app.post("/api/preview-single")
async def api_preview_single(request: Request, _: None = Depends(verify_admin)):
    try:
        data = await request.json()
        message = format_whatsapp_message(data)
        drive_folder = generate_drive_folder_name(data)
        return JSONResponse({"success": True, "message": message, "drive_folder_name": drive_folder})
    except Exception as exc:
        logger.error("[preview-single] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/generate-single")
async def api_generate_single(request: Request, _: None = Depends(verify_admin)):
    try:
        data = await request.json()
        message = format_whatsapp_message(data)
        drive_folder = generate_drive_folder_name(data)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        txt_path = f"output/whatsapp_{ts}.txt"
        json_path = f"output/property_{ts}.json"

        Path(txt_path).write_text(message, encoding="utf-8")
        Path(json_path).write_text(
            json.dumps({"property_data": data, "drive_folder_name": drive_folder,
                        "generated_message": message, "timestamp": ts}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("[generate-single] Saved %s and %s", txt_path, json_path)
        return JSONResponse({
            "success": True,
            "whatsapp_file": f"/{txt_path}",
            "json_file": f"/{json_path}",
            "drive_folder_name": drive_folder,
        })
    except Exception as exc:
        logger.error("[generate-single] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


# ── Bulk Upload Flow ──────────────────────────────────────────────────────────

@app.get("/bulk_upload", response_class=HTMLResponse)
async def bulk_upload_page(request: Request):
    return templates.TemplateResponse(
        "bulk_upload.html",
        {"request": request},
    )


@app.post("/api/preview-bulk")
async def api_preview_bulk(request: Request, _: None = Depends(verify_admin)):
    try:
        body = await request.json()
        properties = body.get("properties", [])
        previews = []
        for prop in properties:
            previews.append({
                "title": prop.get("title", "Untitled"),
                "message": format_whatsapp_message(prop),
                "drive_folder_name": generate_drive_folder_name(prop),
            })
        return JSONResponse({"success": True, "previews": previews})
    except Exception as exc:
        logger.error("[preview-bulk] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/generate-bulk")
async def api_generate_bulk(request: Request, _: None = Depends(verify_admin)):
    try:
        body = await request.json()
        properties = body.get("properties", [])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        processor = BulkPropertyProcessor()
        results = processor.process_properties_batch(properties)

        zip_path = f"output/bulk_{ts}.zip"
        txt_path = f"output/bulk_messages_{ts}.txt"
        json_path = f"output/bulk_data_{ts}.json"

        # ZIP: one txt + one json per property
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, (msg_data, folder_data) in enumerate(
                zip(results["messages"], results["drive_folders"])
            ):
                zf.writestr(f"property_{idx + 1}_whatsapp.txt", msg_data["message"])
                zf.writestr(
                    f"property_{idx + 1}_data.json",
                    json.dumps({
                        "property": properties[idx] if idx < len(properties) else {},
                        "drive_folder": folder_data["folder_name"],
                    }, indent=2, ensure_ascii=False),
                )

        # Combined text file
        combined_txt = ""
        for msg_data in results["messages"]:
            combined_txt += f"=== {msg_data['title']} ===\n{msg_data['message']}\n\n{'─' * 60}\n\n"
        Path(txt_path).write_text(combined_txt, encoding="utf-8")

        # Combined JSON
        Path(json_path).write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        logger.info("[generate-bulk] Processed %d properties → %s", results["processed_count"], zip_path)
        return JSONResponse({
            "success": True,
            "processed_count": results["processed_count"],
            "zip_file": f"/{zip_path}",
            "txt_file": f"/{txt_path}",
            "json_file": f"/{json_path}",
            "errors": results["errors"],
        })
    except Exception as exc:
        logger.error("[generate-bulk] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
