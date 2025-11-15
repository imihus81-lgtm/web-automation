import os
import json
from typing import Dict, Tuple, Optional
import random

DATA_DIR = "data"
TEMPLATE_STATS_FILE = os.path.join(DATA_DIR, "template_stats.json")

# ---------------------------------------------------
# 1) TEMPLATE LIBRARY — 6 BEAUTIFUL PATTERNS
# ---------------------------------------------------

TEMPLATES = [
    {
        "id": "basic_clean",
        "name": "Basic Clean",
        "weight": 1.0,
        "prompt": """
[Template: Basic Clean]

You are a professional web designer and copywriter.

Business name: {business_name}
Industry: {industry}
City: {city}
Year: {year}

Create a complete, responsive one-page business website in pure HTML + CSS (NO JavaScript).

Design style:
- Very clean and simple
- White background (#fafafa)
- Subtle shadows
- Rounded cards (6px)
- Classic body font (Arial, system font)
- Neutral color palette (dark gray text, soft accent color)

Layout:
1) Header / Hero
   - Business name as big heading
   - Short tagline mentioning {industry} in {city}
   - Centered content

2) About section
   - Heading "About Us"
   - 1–2 paragraphs describing what {business_name} does

3) Services section
   - Heading "Our Services"
   - 3 or 4 service cards in a responsive flex layout
   - Each card: title + 1 short paragraph

4) Contact section
   - Heading "Contact"
   - Email placeholder (info@businessname.com style)
   - Phone placeholder
   - Address in {city}

5) Footer
   - Simple © {business_name} {year}

Requirements:
- Return a full HTML5 document starting with <!DOCTYPE html>.
- Include <html>, <head>, <body>.
- Put all CSS inside a <style> tag in the <head>.
- Do NOT use any JavaScript or <script> tags.
- Do NOT include comments or explanations, only the final HTML.
"""
    },
    {
        "id": "pro_modern",
        "name": "Pro Modern",
        "weight": 1.0,
        "prompt": """
[Template: Pro Modern]

You are a senior web designer creating a modern, professional business website.

Business name: {business_name}
Industry: {industry}
City: {city}
Year: {year}

Create a full one-page website in pure HTML + CSS (NO JS).

Design style:
- Modern SaaS look
- Light background (#f5f7fa)
- Card components with soft shadows and 12px rounded corners
- Use a modern font stack (e.g. "Inter", system fallback)
- Strong section headings
- Blue accent color (#2563eb) for links and buttons

Layout:
1) Hero section
   - White hero card with subtle shadow
   - Centered headline showing {business_name}
   - Subheadline mentioning {industry} services in {city}
   - One primary call-to-action button (e.g. "Get a Free Quote")

2) About section
   - Card with heading "About {business_name}"
   - 1–2 paragraphs of persuasive copy

3) Services section
   - Heading "Our Services"
   - Responsive grid (3 or 4 columns on desktop, stacked on mobile)
   - Each service card: title, short description

4) Testimonials section
   - Card with 2–3 short testimonials

5) Contact section
   - Card with clear contact details:
     - Email
     - Phone
     - Address in {city}

6) Footer
   - White background
   - Small text: © {business_name} {year}

Requirements:
- Full HTML5 document, starting with <!DOCTYPE html>.
- All CSS in a single <style> tag in the <head>.
- Use flexbox or CSS grid for layout.
- No JavaScript, no external CSS files.
- No comments or extra explanations in the output.
"""
    },
    {
        "id": "premium_gradient",
        "name": "Premium Gradient",
        "weight": 1.0,
        "prompt": """
[Template: Premium Gradient]

You are designing a premium, high-conversion marketing site.

Business name: {business_name}
Industry: {industry}
City: {city}
Year: {year}

Create a polished, single-page HTML + CSS website (NO JS).

Design style:
- Gradient hero background (e.g. linear-gradient(135deg,#6a11cb,#2575fc))
- Rounded, elevated cards
- Poppins / modern sans-serif style typography
- White content cards on soft gray background (#f2f2f7)
- Strong visual hierarchy
- Clear call-to-action buttons

Layout:
1) Gradient Hero
   - Large hero with gradient background
   - Business name as big headline
   - Subheadline describing {industry} services in {city}
   - Primary CTA button (e.g. "Request a Free Estimate")
   - Secondary CTA as simple text link

2) About card
   - White card with heading "About Us"
   - 1–2 paragraphs of persuasive, benefit-focused text

3) Services grid
   - Heading "Our Services"
   - 3–6 cards in a responsive grid
   - Each card: title + short description

4) Process section
   - Heading "How It Works" or "Our Process"
   - 3–4 steps listed in a clear layout

5) Contact card
   - Heading "Contact Us"
   - Email, phone, address (use {city})

6) Footer
   - White footer with small, muted text: © {business_name} {year}

Requirements:
- Output a complete HTML5 document with <html>, <head>, <body>.
- Put all CSS inside a <style> tag in the head.
- No JavaScript or external files.
- No comments; output only the HTML.
"""
    },
    {
        "id": "ultra_dark",
        "name": "Ultra Luxury Dark",
        "weight": 1.0,
        "prompt": """
[Template: Ultra Luxury Dark]

You are designing a high-end, luxury style website.

Business name: {business_name}
Industry: {industry}
City: {city}
Year: {year}

Create a one-page HTML + CSS site in a dark, premium style (NO JS).

Design style:
- Dark background (#0c0c0c to #141414)
- Card backgrounds (#141414 to #181818)
- Gold accent color (#f5c542) for headlines and key elements
- Thin, subtle borders (#333)
- Elegant typography (modern sans-serif)
- Generous spacing

Layout:
1) Dark hero section
   - Full-width hero with centered content
   - Business name in gold
   - Subheadline in muted gray describing {industry} services in {city}

2) About card
   - Heading "About Us" in gold
   - 1–2 paragraphs of refined text

3) Services grid
   - Heading "Our Services"
   - 3–4 service cards in a responsive grid
   - Each card: gold title + soft gray description

4) Highlights / Why Choose Us
   - List of 3–5 bullet-point benefits or features

5) Contact section
   - Card with heading "Contact"
   - Email, phone, and address (use {city})

6) Footer
   - Small, centered text in gray:
     © {business_name} {year}

Requirements:
- Full HTML5 document starting with <!DOCTYPE html>.
- All CSS in a <style> tag in the <head>.
- No JavaScript or script tags.
- No external CSS or JS files.
- No comments or explanations outside the HTML.
"""
    },
    {
        "id": "restaurant_premium",
        "name": "Restaurant Premium",
        "weight": 1.0,
        "prompt": """
[Template: Restaurant Premium]

You are designing a modern, high-conversion website for a restaurant or café.

Business name: {business_name}
Industry: {industry}
City: {city}
Year: {year}

Create a beautiful single-page HTML + CSS website (NO JavaScript).

Design:
- Warm, appetizing colors (deep red / orange / dark slate)
- Big hero section with restaurant name, short tagline, and "Reserve a Table" button
- Background image placeholders using CSS (no real images required)
- Menu section grid for 6–9 featured dishes
- Opening hours block
- Location map placeholder box (just styled div, no iframe)
- Contact / reservation section

Sections:
1) Hero (name + tagline + main CTA)
2) About (short story, chef or concept)
3) Featured Menu (grid of items with name + 1 line description)
4) Gallery placeholder row (3 boxes with "Photo" text)
5) Visit Us (address in {city}, opening hours)
6) Contact (phone and email)
7) Footer (© {business_name} {year})

Requirements:
- Full HTML5 document with <!DOCTYPE html>.
- All CSS inside a <style> tag in the head.
- No JavaScript, no external CSS.
- No comments, only HTML.
"""
    },
    {
        "id": "realtor_premium",
        "name": "Real Estate Premium",
        "weight": 1.0,
        "prompt": """
[Template: Real Estate Premium]

You are designing a premium landing page for a real estate agent or agency.

Business name: {business_name}
Industry: {industry}
City: {city}
Year: {year}

Create a polished one-page HTML + CSS site (NO JS).

Design:
- Clean, upscale look (white + dark gray + accent blue or gold)
- Large hero with agent/agency name and "Request a Call" button
- Property cards with highlight info
- Neighborhood highlights section
- Testimonials

Sections:
1) Hero: headline with {business_name}, subheadline about helping people buy/sell in {city}, CTA button.
2) Featured Listings: 3–6 property cards (price, beds/baths, short description, "View details" placeholder link).
3) About the Agent/Team: 1–2 paragraphs.
4) Why Work With Us: 3–4 bullet reasons.
5) Testimonials: 2 short quotes.
6) Contact section: phone, email, office address in {city}.
7) Footer: © {business_name} {year}.

Requirements:
- Full HTML5 document starting with <!DOCTYPE html>.
- All CSS in a <style> tag.
- No JavaScript or external files.
- No comments; only HTML.
"""
    },
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
    industry_lower = (industry or "").lower()

    # Start with neutral boost
    niche_boosts = {t["id"]: 0.0 for t in TEMPLATES}

    # Trade / construction / auto
    if any(
        kw in industry_lower
        for kw in [
            "roof",
            "solar",
            "auto",
            "car",
            "garage",
            "construction",
            "plumb",
            "electric",
        ]
    ):
        niche_boosts["pro_modern"] += 1.5
        niche_boosts["ultra_dark"] += 1.0

    # Restaurant / food
    if any(kw in industry_lower for kw in ["restaurant", "cafe", "café", "food", "dining", "bistro"]):
        niche_boosts["restaurant_premium"] += 3.0
        niche_boosts["premium_gradient"] += 1.0

    # Real estate / property
    if any(kw in industry_lower for kw in ["real estate", "realtor", "property", "estate agent", "broker"]):
        niche_boosts["realtor_premium"] += 3.0
        niche_boosts["pro_modern"] += 1.0

    # Professional / corporate
    if any(kw in industry_lower for kw in ["law", "tax", "consult", "account", "firm", "agency"]):
        niche_boosts["basic_clean"] += 1.5
        niche_boosts["pro_modern"] += 1.0

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

    total = sum(score for _, score in scored)
    r = random.random() * total
    running = 0.0
    chosen = scored[0][0]

    for t, score in scored:
        running += score
        if r <= running:
            chosen = t
            break

    # Record usage
    stats = _load_template_stats()
    if chosen["id"] not in stats:
        stats[chosen["id"]] = {"uses": 0, "success": 0}
    stats[chosen["id"]]["uses"] += 1
    _save_template_stats(stats)

    return chosen


# ---------------------------------------------------
# 4) MAIN FUNCTION: BUILD PROMPT
# ---------------------------------------------------

def build_prompt_for_business(
    business_name: str,
    industry: str,
    city: str,
    preferred_template_id: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Returns (prompt, template_id).
    preferred_template_id can be one of:
      basic_clean, pro_modern, premium_gradient,
      ultra_dark, restaurant_premium, realtor_premium
    """
    # If user explicitly chose a template, try to use it
    chosen = None
    if preferred_template_id:
        for t in TEMPLATES:
            if t["id"] == preferred_template_id:
                chosen = t
                break

    # Otherwise let the brain choose based on stats + niche
    if chosen is None:
        chosen = choose_template(business_name, industry, city)

    year = 2025  # simple; you can make this dynamic if you like

    prompt = chosen["prompt"].format(
        business_name=business_name,
        industry=industry,
        city=city,
        year=year,
    )

    return prompt, chosen["id"]


# ---------------------------------------------------
# 5) OPTIONAL: RECORD SUCCESS (WHEN PAYMENT HAPPENS)
# ---------------------------------------------------

def record_template_result(template_id: str, success: bool):
    """
    Call this from payment webhook when a customer pays
    and accepts the site -> success=True.
    """
    stats = _load_template_stats()

    if template_id not in stats:
        stats[template_id] = {"uses": 0, "success": 0}

    if success:
        stats[template_id]["success"] += 1

    _save_template_stats(stats)
