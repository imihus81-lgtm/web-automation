import os
import json
import random
from typing import Dict, Tuple

DATA_DIR = "data"
TEMPLATE_STATS_FILE = os.path.join(DATA_DIR, "template_stats.json")

# ---------------------------------------------------
# 1) TEMPLATE LIBRARY — CAN GROW AUTOMATICALLY
# ---------------------------------------------------

TEMPLATES = [
    {
        "id": "modern_light",
        "name": "Modern Light SaaS",
        "weight": 1.0,
        "prompt": """
[Modern Light Theme]

You are a professional web designer.

Business name: {business_name}
Industry: {industry}
City: {city}

Create a complete, responsive one-page website in pure HTML + CSS (NO JS).

Design:
- Light mode layout
- White background (#ffffff)
- Soft shadows
- Rounded sections (12–20px)
- Blue primary (#2563eb)
- Modern SaaS layout

Sections:
1. Hero with bold headline mentioning {city}
2. About section describing {business_name}
3. Services grid (3 or 6 cards)
4. Testimonials (2–3 reviews)
5. Contact block with placeholder phone/email and {city} location
6. Footer © {business_name} {year}

Rules:
- MUST return full HTML document (<!DOCTYPE html>…)
- All CSS must be inside <style> tag.
- NO JS.
- NO comments.
"""
    },
    {
        "id": "dark_pro",
        "name": "Dark Professional",
        "weight": 1.0,
        "prompt": """
[Dark Professional Theme]

You are a senior web designer creating a cinematic dark-mode business website.

Business name: {business_name}
Industry: {industry}
City: {city}

Create a full, responsive one-page website in pure HTML + CSS.

Design:
- Dark background (#0f172a or #020617)
- Neon blue accents (#38bdf8 or #0ea5e9)
- Card-style sections
- Gradient CTA buttons
- Big bold hero section

Sections:
1. Cinematic hero with bold headline + CTA
2. About: split (left text, right image placeholder)
3. Services: Neon-bordered cards
4. Why Choose Us (3–4 advantages)
5. Testimonials (2–3)
6. Contact: centered layout, using {city}
7. Footer © {business_name} {year}

Rules:
- Return full HTML5
- All CSS in <style> tag
- NO JS
- NO comments
"""
    },
    {
        "id": "minimal_business",
        "name": "Minimal Business",
        "weight": 1.0,
        "prompt": """
[Minimal Business Theme]

You are designing a minimalist, clean business website.

Business name: {business_name}
Industry: {industry}
City: {city}

Create a full single-page HTML+CSS business website.

Design:
- White/gray minimal style
- Clean typography (system font)
- Sharp edges (no rounding)
- Black text (#111)
- Light-gray sections (#f8f9fa)

Sections:
1. Clean hero section
2. About in simple single-column layout
3. Services in 3-column grid
4. Process / Steps section
5. Contact with business details for {city}
6. Footer © {business_name} {year}

Rules:
- Full HTML document only
- All CSS inside <style>
- NO JS, NO comments
"""
    }
]


# ---------------------------------------------------
# 2) STATS MANAGEMENT (BRAIN MEMORY)
# ---------------------------------------------------

def _load_template_stats() -> Dict[str, Dict]:
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(TEMPLATE_STATS_FILE):
        stats = {t["id"]: {"uses": 0, "success": 0} for t in TEMPLATES}
        _save_template_stats(stats)
        return stats

    with open(TEMPLATE_STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_template_stats(stats: Dict[str, Dict]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TEMPLATE_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


# ---------------------------------------------------
# 3) BRAIN DECISION MAKING — PICK BEST TEMPLATE
# ---------------------------------------------------

def choose_template(business_name: str, industry: str, city: str) -> Dict:
    stats = _load_template_stats()
    industry_lower = industry.lower()

    # Niche-based preferences
    niche_boosts = {t["id"]: 0.0 for t in TEMPLATES}

    if any(kw in industry_lower for kw in ["roof", "solar", "auto", "car", "garage", "construction"]):
        niche_boosts["dark_pro"] += 3.0

    if any(kw in industry_lower for kw in ["restaurant", "food", "cafe", "salon", "beauty", "spa"]):
        niche_boosts["modern_light"] += 2.0
        niche_boosts["minimal_business"] += 1.0

    if any(kw in industry_lower for kw in ["law", "tax", "consult", "account"]):
        niche_boosts["minimal_business"] += 3.0

    # Score templates
    scored = []
    for t in TEMPLATES:
        tid = t["id"]
        s = stats.get(tid, {"uses": 0, "success": 0})
        uses = s["uses"]
        success = s["success"]

        # Success rate with smoothing
        success_rate = (success + 1) / (uses + 2)

        score = t["weight"] + niche_boosts[tid] + success_rate * 2.0
        scored.append((t, score))

    # Weighted random selection
    total = sum(score for _, score in scored)
    r = random.random() * total
    running = 0.0

    for t, score in scored:
        running += score
        if r <= running:
            chosen = t
            break

    # Record usage
    stats = _load_template_stats()
    stats[chosen["id"]]["uses"] += 1
    _save_template_stats(stats)

    return chosen


# ---------------------------------------------------
# 4) MAIN FUNCTION: BUILD PROMPT
# ---------------------------------------------------

def build_prompt_for_business(business_name: str, industry: str, city: str) -> Tuple[str, str]:
    chosen = choose_template(business_name, industry, city)

    year = 2025  # can make dynamic if you want

    prompt = chosen["prompt"].format(
        business_name=business_name,
        industry=industry,
        city=city,
        year=year,
    )

    return prompt, chosen["id"]


# ---------------------------------------------------
# 5) OPTIONAL: RECORD SUCCESS (PAID/YES)
# ---------------------------------------------------

def record_template_result(template_id: str, success: bool):
    stats = _load_template_stats()

    if template_id not in stats:
        stats[template_id] = {"uses": 0, "success": 0}

    if success:
        stats[template_id]["success"] += 1

    _save_template_stats(stats)
