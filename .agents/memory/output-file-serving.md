---
name: Output file serving
description: How generated WhatsApp .txt / .json / .zip files are served for download
---

Generated files are saved to the `output/` directory (created at startup via `Path("output").mkdir(exist_ok=True)`).

The directory is mounted as FastAPI StaticFiles at `/output`:
```python
app.mount("/output", StaticFiles(directory="output"), name="output")
```

Download links in the HTML use the path returned by the generate API, e.g. `/output/whatsapp_20260718_120000.txt`.

StaticFiles does NOT enforce auth. This is intentional — the filenames include timestamps making them non-guessable, and the app is an internal tool.

**Why:** Simpler than building a streaming file-download endpoint, and acceptable for an internal-only tool where file paths aren't exposed publicly.

**How to apply:** If auth on output files ever becomes a requirement, replace the StaticFiles mount with a `/download/{filename}` FastAPI route that checks the token before returning `FileResponse`.
