import os
import re as _re
import json
import logging
import sys
from typing import List, Optional
from urllib.parse import unquote_plus

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils.auth import verify_admin
from utils.property_normalizer import (
    parse_raw_property_dump,
    normalize_property,
    parsed_to_normalized,
    build_meta_title,
    build_meta_description,
    build_whatsapp_caption,
    build_whatsapp_title,
)
from utils.formatters import (
    canonical_normalize_property,
    render_meta_title,
    render_meta_description,
    format_whatsapp_message,
    generate_drive_folder_name,
)
from services.cloudinary_service import upload_images
from services.meta_catalog_service import create_or_update_catalog_item, get_debug_info
from services.whatsapp_service import send_confirmation, send_property_listing
from services.bulk_processor import BulkPropertyProcessor

# ── Logging ───────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Startup secret validation ───────────────────────────────────────────────────────────────────
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
    logger.info("All required secrets present \u2713")


validate_secrets()

import zipfile
from datetime import datetime
from pathlib import Path

# ── App setup ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="EasyFind Admin", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
Path("output").mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")
templates = Jinja2Templates(directory="templates")

MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("1", "true", "yes")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


# ── Routes ─────────────────────────────────────────────────────────────────────────────

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
    # Core fields
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
    # Extended fields
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
    # Location fields
    building_name: str = Form(default=""),
    flat_number: str = Form(default=""),
    street: str = Form(default=""),
    landmark: str = Form(default=""),
    state: str = Form(default=""),
    pincode: str = Form(default=""),
    maps_link_field: str = Form(default="", alias="maps_link"),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    # Image fields
    pasted_image_urls: str = Form(default=""),
    cover_image_index: str = Form(default="0"),
    images: List[UploadFile] = File(default=[]),
):
    errors = []

    # 1. Upload file images
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

    # 2. Combine with pasted URLs
    pasted_urls = [u.strip() for u in pasted_image_urls.splitlines() if u.strip()]
    all_image_urls = cloudinary_urls + pasted_urls

    if not all_image_urls and not errors:
        errors.append("At least one image is required.")

    if errors:
        return templates.TemplateResponse(
            "admin_property.html",
            {
                "request": request, "mock_mode": MOCK_MODE,
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

    # 3. Determine cover image
    try:
        cover_idx = int(cover_image_index)
        if cover_idx < 0 or cover_idx >= len(all_image_urls):
            cover_idx = 0
    except (ValueError, TypeError):
        cover_idx = 0
    if cover_idx != 0 and all_image_urls:
        cover = all_image_urls.pop(cover_idx)
        all_image_urls.insert(0, cover)
    image_link = all_image_urls[0] if all_image_urls else ""

    # 4. Build canonical property dict and normalize
    property_data = {
        "property_id": property_id,
        "title": title,
        "raw_title": title,
        "description": description,
        "price": price,
        "rent": price,
        "currency": currency,
        "city": city,
        "locality": locality,
        "location": f"{locality}, {city}".strip(", "),
        "bhk": bhk,
        "property_type": property_type,
        "availability": availability,
        "available_from": availability,
        "listing_type": listing_type,
        "deposit": deposit,
        "maintenance": maintenance,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "furnishing": furnishing,
        "area_sqft": area_super,
        "sqft": area_super,
        "area_carpet": area_carpet,
        "facing": facing,
        "floor": floor,
        "parking": parking,
        "amenities": amenities,
        "broker_name": broker_name,
        "phone": phone,
        "property_name": building_name,
        "building_name": building_name,
        "flat_number": flat_number,
        "street": street,
        "landmark": landmark,
        "state": state,
        "pincode": pincode,
        "google_maps_link": maps_link_field,
        "maps_link": maps_link_field,
        "latitude": latitude,
        "longitude": longitude,
        "image_link": image_link,
        "cover_image_url": image_link,
        "all_image_urls": all_image_urls,
    }

    # 5. Canonical normalization
    norm_prop = canonical_normalize_property(property_data)
    meta_title = build_meta_title(norm_prop)
    meta_desc = build_meta_description(norm_prop)
    wa_caption = build_whatsapp_caption(norm_prop)

    property_data["title"] = meta_title
    property_data["description"] = meta_desc

    # 6. Meta catalog
    meta_response = None
    meta_error = None
    meta_handle = ""
    if MOCK_MODE:
        meta_response = {"handles": ["mock_handle_abc123"], "mock": True}
        meta_handle = "mock_handle_abc123"
        logger.info("[MOCK] Skipping Meta catalog API.")
    else:
        try:
            meta_response = await create_or_update_catalog_item(property_data)
            if meta_response and meta_response.get("handles"):
                meta_handle = meta_response["handles"][0]
        except Exception as exc:
            meta_error = str(exc)
            logger.error("[Meta] Catalog creation failed: %s", meta_error)

    # 7. WhatsApp (non-blocking)
    whatsapp_result = {"status": "skipped"}
    if not meta_error:
        if MOCK_MODE:
            whatsapp_result = {
                "status": "skipped (mock mode)",
                "message_type": "image_with_caption" if image_link else "text_fallback",
                "cover_image": bool(image_link),
                "recipient": "*mock*",
            }
        else:
            whatsapp_result = await send_property_listing(
                caption=wa_caption,
                cover_image_url=image_link,
            )

    maps_query = f"{locality}, {city}"
    auto_maps_link = f"https://www.google.com/maps/search/?api=1&query={maps_query.replace(' ', '+')}"
    final_maps_link = maps_link_field if maps_link_field else auto_maps_link

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "mock_mode": MOCK_MODE,
            "property": property_data,
            "meta_title": meta_title,
            "meta_description": meta_desc,
            "meta_handle": meta_handle,
            "meta_response": json.dumps(meta_response, indent=2) if meta_response else None,
            "meta_error": meta_error,
            "whatsapp_result": whatsapp_result,
            "wa_caption": wa_caption,
            "maps_link": final_maps_link,
            "image_urls": all_image_urls,
        },
        status_code=200 if not meta_error else 422,
    )


@app.get("/catalog/property/{property_id}")
async def catalog_debug(property_id: str, request: Request):
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


# ── Parse Property Endpoints ───────────────────────────────────────────────────────────────────────

@app.post("/api/parse-property")
async def api_parse_property(request: Request):
    """Parse a raw property dump and return canonical normalized fields + preview outputs."""
    try:
        body = await request.json()
        raw_text = body.get("raw_text", "") or body.get("raw_dump", "")
        # Allow caller to pass additional override fields
        overrides = {k: v for k, v in body.items() if k not in ("raw_text", "raw_dump")}

        if not raw_text.strip():
            return JSONResponse({"success": False, "error": "raw_text is required"}, status_code=400)

        parsed = parse_raw_property_dump(raw_text)
        norm = parsed_to_normalized(parsed)

        # Apply overrides (manual form fields take precedence)
        for k, v in overrides.items():
            if v and hasattr(norm, k):
                setattr(norm, k, v)

        meta_title = build_meta_title(norm)
        meta_desc = build_meta_description(norm)
        wa_title = build_whatsapp_title(norm)
        wa_caption = build_whatsapp_caption(norm)

        return JSONResponse({
            "success": True,
            "fields": {
                "raw_title": norm.raw_title,
                "furnishing": norm.furnishing,
                "bhk": norm.bhk,
                "bathrooms": norm.bathrooms,
                "bathroom_type": norm.bathroom_type,
                "balconies": norm.balconies,
                "has_utility": norm.has_utility,
                "rent": norm.rent,
                "maintenance": norm.maintenance,
                "deposit": norm.deposit,
                "area_sqft": norm.area_sqft,
                "floor": norm.floor,
                "available_from": norm.available_from,
                "preferred_tenant": norm.preferred_tenant,
                "diet_preference": norm.diet_preference,
                "pets": norm.pets,
                "community_type": norm.community_type,
                "location": norm.location,
                "property_name": norm.property_name,
                "gallery_link": norm.gallery_link,
                "google_maps_link": norm.google_maps_link,
            },
            "meta_title": meta_title,
            "meta_description": meta_desc,
            "whatsapp_title": wa_title,
            "whatsapp_caption": wa_caption,
            "needs_review": norm.needs_review,
            "unrecognized_lines": norm.unrecognized_lines,
        })
    except Exception as exc:
        logger.error("[parse-property] %s", exc, exc_info=True)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/parse-properties-bulk")
async def api_parse_properties_bulk(request: Request):
    """Parse multiple raw property dumps in one call."""
    try:
        body = await request.json()
        raw_dumps = body.get("raw_dumps", [])  # list of strings
        if not raw_dumps:
            return JSONResponse({"success": False, "error": "raw_dumps list is required"}, status_code=400)

        results = []
        for i, raw_text in enumerate(raw_dumps):
            if not raw_text.strip():
                results.append({"index": i, "success": False, "error": "empty"})
                continue
            try:
                parsed = parse_raw_property_dump(raw_text)
                norm = parsed_to_normalized(parsed)
                results.append({
                    "index": i,
                    "success": True,
                    "fields": {
                        "raw_title": norm.raw_title,
                        "furnishing": norm.furnishing,
                        "bhk": norm.bhk,
                        "bathrooms": norm.bathrooms,
                        "bathroom_type": norm.bathroom_type,
                        "balconies": norm.balconies,
                        "has_utility": norm.has_utility,
                        "rent": norm.rent,
                        "maintenance": norm.maintenance,
                        "deposit": norm.deposit,
                        "area_sqft": norm.area_sqft,
                        "floor": norm.floor,
                        "available_from": norm.available_from,
                        "preferred_tenant": norm.preferred_tenant,
                        "diet_preference": norm.diet_preference,
                        "pets": norm.pets,
                        "community_type": norm.community_type,
                        "location": norm.location,
                        "property_name": norm.property_name,
                        "gallery_link": norm.gallery_link,
                        "google_maps_link": norm.google_maps_link,
                    },
                    "meta_title": build_meta_title(norm),
                    "whatsapp_title": build_whatsapp_title(norm),
                    "whatsapp_caption": build_whatsapp_caption(norm),
                    "needs_review": norm.needs_review,
                    "unrecognized_lines": norm.unrecognized_lines,
                })
            except Exception as exc:
                results.append({"index": i, "success": False, "error": str(exc)})

        return JSONResponse({"success": True, "count": len(results), "results": results})
    except Exception as exc:
        logger.error("[parse-properties-bulk] %s", exc, exc_info=True)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


# ── Single Upload Flow ────────────────────────────────────────────────────────────────────────

@app.get("/single_upload", response_class=HTMLResponse)
async def single_upload_page(request: Request):
    return templates.TemplateResponse(
        "single_upload.html",
        {"request": request},
    )


@app.post("/api/preview-single")
async def api_preview_single(request: Request):
    try:
        data = await request.json()
        # Support raw_dump for text-based input
        raw_dump = data.get('raw_dump') or data.get('raw_text', '')
        if raw_dump:
            parsed = parse_raw_property_dump(raw_dump)
            norm = parsed_to_normalized(parsed)
            # Apply overrides
            for k, v in data.items():
                if k not in ('raw_dump', 'raw_text') and v and hasattr(norm, k):
                    setattr(norm, k, v)
        else:
            norm = canonical_normalize_property(data)
        message = build_whatsapp_caption(norm)
        meta_title = build_meta_title(norm)
        drive_folder = generate_drive_folder_name(data)
        return JSONResponse({
            "success": True,
            "message": message,
            "meta_title": meta_title,
            "whatsapp_title": build_whatsapp_title(norm),
            "drive_folder_name": drive_folder,
            "needs_review": norm.needs_review,
            "unrecognized_lines": norm.unrecognized_lines,
        })
    except Exception as exc:
        logger.error("[preview-single] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/generate-single")
async def api_generate_single(request: Request):
    try:
        data = await request.json()
        raw_dump = data.get('raw_dump') or data.get('raw_text', '')
        if raw_dump:
            parsed = parse_raw_property_dump(raw_dump)
            norm = parsed_to_normalized(parsed)
            for k, v in data.items():
                if k not in ('raw_dump', 'raw_text') and v and hasattr(norm, k):
                    setattr(norm, k, v)
        else:
            norm = canonical_normalize_property(data)
        message = build_whatsapp_caption(norm)
        meta_title = build_meta_title(norm)
        drive_folder = generate_drive_folder_name(data)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        txt_path = f"output/whatsapp_{ts}.txt"
        json_path = f"output/property_{ts}.json"

        Path(txt_path).write_text(message, encoding="utf-8")
        Path(json_path).write_text(
            json.dumps({
                "property_data": data,
                "meta_title": meta_title,
                "drive_folder_name": drive_folder,
                "generated_message": message,
                "timestamp": ts,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("[generate-single] Saved %s and %s", txt_path, json_path)
        return JSONResponse({
            "success": True,
            "whatsapp_file": f"/{txt_path}",
            "json_file": f"/{json_path}",
            "meta_title": meta_title,
            "drive_folder_name": drive_folder,
        })
    except Exception as exc:
        logger.error("[generate-single] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


# ── Bulk Upload Flow ───────────────────────────────────────────────────────────────────────

@app.get("/bulk_upload", response_class=HTMLResponse)
async def bulk_upload_page(request: Request):
    return templates.TemplateResponse(
        "bulk_upload.html",
        {"request": request},
    )


@app.post("/api/preview-bulk")
async def api_preview_bulk(request: Request):
    try:
        body = await request.json()
        properties = body.get("properties", [])
        previews = []
        for prop in properties:
            raw_dump = prop.get('raw_dump') or prop.get('raw_text', '')
            if raw_dump:
                parsed = parse_raw_property_dump(raw_dump)
                norm = parsed_to_normalized(parsed)
                for k, v in prop.items():
                    if k not in ('raw_dump', 'raw_text') and v and hasattr(norm, k):
                        setattr(norm, k, v)
            else:
                norm = canonical_normalize_property(prop)
            previews.append({
                "meta_title": build_meta_title(norm),
                "whatsapp_title": build_whatsapp_title(norm),
                "message": build_whatsapp_caption(norm),
                "drive_folder_name": generate_drive_folder_name(prop),
                "needs_review": norm.needs_review,
            })
        return JSONResponse({"success": True, "previews": previews})
    except Exception as exc:
        logger.error("[preview-bulk] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.post("/api/generate-bulk")
async def api_generate_bulk(request: Request):
    try:
        body = await request.json()
        properties = body.get("properties", [])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        processor = BulkPropertyProcessor()
        results = processor.process_properties_batch(properties)

        zip_path = f"output/bulk_{ts}.zip"
        txt_path = f"output/bulk_messages_{ts}.txt"
        json_path = f"output/bulk_data_{ts}.json"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, (msg_data, folder_data) in enumerate(
                zip(results["messages"], results["drive_folders"])
            ):
                zf.writestr(f"property_{idx + 1}_whatsapp.txt", msg_data["message"])
                zf.writestr(
                    f"property_{idx + 1}_data.json",
                    json.dumps({
                        "property": properties[idx] if idx < len(properties) else {},
                        "meta_title": msg_data.get("meta_title", ""),
                        "drive_folder": folder_data["folder_name"],
                    }, indent=2, ensure_ascii=False),
                )

        combined_txt = ""
        for msg_data in results["messages"]:
            combined_txt += f"=== {msg_data['title']} ===\n{msg_data['message']}\n\n{'\u2500' * 60}\n\n"
        Path(txt_path).write_text(combined_txt, encoding="utf-8")
        Path(json_path).write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        logger.info("[generate-bulk] Processed %d properties \u2192 %s", results["processed_count"], zip_path)
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


# ── Geocode Maps URL ─────────────────────────────────────────────────────────────────────────

@app.post("/api/geocode-location")
async def api_geocode_location(request: Request):
    """Resolve a Google Maps URL, extract place name + coords, reverse-geocode via Maps API."""
    try:
        import httpx
        body = await request.json()
        maps_url = body.get("maps_url", "").strip()
        if not maps_url:
            return JSONResponse({"success": False, "error": "No Maps URL provided"}, status_code=400)

        result: dict = {}
        headers = {"User-Agent": "Mozilla/5.0 (compatible; EasyFindAdmin/1.0)"}

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(maps_url, headers=headers)
            final_url = str(resp.url)
        logger.info("[geocode-location] Resolved URL: %s", final_url[:120])

        place_m = _re.search(r"/maps/place/([^/@?&]+)", final_url)
        if place_m:
            place_name = unquote_plus(place_m.group(1).replace("+", " ")).strip()
            if place_name and place_name.lower() not in ("", "place"):
                result["place_name"] = place_name

        coord_m = _re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if not coord_m:
            coord_m = _re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", final_url)

        if coord_m and GOOGLE_MAPS_API_KEY:
            lat, lng = coord_m.group(1), coord_m.group(2)
            result["lat"] = lat
            result["lng"] = lng
            async with httpx.AsyncClient(timeout=10.0) as gc:
                geo = await gc.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"latlng": f"{lat},{lng}", "key": GOOGLE_MAPS_API_KEY},
                )
            geo_data = geo.json()
            logger.info("[geocode-location] Geocode status: %s", geo_data.get("status"))
            if geo_data.get("status") == "OK" and geo_data.get("results"):
                for comp in geo_data["results"][0].get("address_components", []):
                    types = comp.get("types", [])
                    if ("sublocality_level_1" in types or "sublocality" in types) and "locality" not in result:
                        result["locality"] = comp["long_name"]
                    elif "locality" in types:
                        result["city"] = comp["long_name"]
                    elif "administrative_area_level_1" in types:
                        result["state"] = comp["long_name"]
                first = geo_data["results"][0]
                if any(t in first.get("types", []) for t in ("establishment", "premise", "point_of_interest")):
                    estab = first.get("formatted_address", "").split(",")[0].strip()
                    if estab:
                        result["establishment"] = estab

        return JSONResponse({"success": True, **result})
    except Exception as exc:
        logger.error("[geocode-location] %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
