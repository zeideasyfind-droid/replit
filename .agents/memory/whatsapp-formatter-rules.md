---
name: WhatsApp formatter rules
description: Business logic in utils/formatters.py for message generation
---

All formatting lives in `utils/formatters.py`. Key rules:

**"with Utility" rule** — appended to title only when ALL THREE conditions hold: furnishing == "Fully Furnished", "2 BHK" in title, "2 bath" in title, AND "balcony" in title.

**Availability normalization** — any of: "immediate", "ready", "today", "now", "vacant", "available now", OR a date ≤ today → "Ready to occupy". Future dates formatted as "DD Mon YYYY".

**Tenant + diet normalization** — "family"/"families" → "Families"; "working"/"professional" → "Working Professionals"; "anyone"/"any"/"open"/"all" (or nothing recognizable) → "Anyone". Diet appended as ", Vegetarian" or ", Non-Vegetarian" after the tenant string.

**Drive folder name format** — `EFF-{3-digit random}-{name}` where name is: society/apt name if present, else property_name-owner, else location-owner (for non-gated), else location-owner default. Numeric ID is random per call — not stable across re-runs.

**Why:** These rules match EasyFind's internal listing format standards per the implementation plan.
