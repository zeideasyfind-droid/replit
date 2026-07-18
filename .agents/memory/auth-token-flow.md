---
name: Auth token flow
description: How ADMIN_AUTH_TOKEN is threaded through all pages and JS API calls
---

All admin routes use `Depends(verify_admin)` from `utils/auth.py`. Token accepted via:
1. `?token=VALUE` query param (primary — used in all HTML links)
2. `Authorization: Bearer VALUE` header

In multi-step JS wizards (single_upload.html, bulk_upload.html), the token is extracted at page load:
```js
const TOKEN = new URLSearchParams(window.location.search).get('token') || '';
```
Then passed to every fetch() call:
```js
fetch(`/api/preview-single?token=${encodeURIComponent(TOKEN)}`, ...)
```

**Why:** FastAPI's `verify_admin` dependency reads `request.query_params`, so the token must be in the URL for JSON API calls (no form body to read from).

**How to apply:** Any new API route added to the JS wizard flows must include `_: None = Depends(verify_admin)` and the JS must append `?token=...` to the fetch URL.
