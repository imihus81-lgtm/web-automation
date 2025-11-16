import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =============================
# V8 — INDUSTRY TONE MAPPING
# =============================
INDUSTRY_TONES = {
    "restaurant": "Warm, sensory, delicious, inviting, premium dining atmosphere",
    "salon": "Luxury, beauty-focused, soft, feminine, elegant, relaxing",
    "clinic": "Trustworthy, medical, clean, professional, caring",
    "auto repair": "Technical, expert, reliable, fast service, strong customer trust",
    "roofer": "Strong, durable, trusted, safety-first, protective",
    "law firm": "Authority, justice, confidence, clarity, professionalism",
    "real estate": "Financial, premium lifestyle, trust, investment oriented",
    "e-commerce": "Modern, bold, product-centered, conversion-optimized",
    "default": "Professional, modern, clean, trustworthy business style",
}


# =============================
# MAIN BRAIN FUNCTION (V8)
# =============================
def generate_commerce_site(business_name,
                           business_category,
                           business_description,
                           business_address,
                           phone,
                           email,
                           color_theme="#1d4ed8",
                           logo_url="",
                           ecommerce_enabled=False,
                           products=None):
    """
    Generates full multi-page site JSON using OpenAI Responses API.
    """

    if products is None:
        products = []

    tone = INDUSTRY_TONES.get(business_category.lower(), INDUSTRY_TONES["default"])

    prompt = f"""
You are XAI Commerce — the world's most advanced AI website builder.

Generate a complete, multi-page business website with **premium Tailwind-style HTML**.
NO JavaScript frameworks. Pure HTML + inline Tailwind CSS classes.

===========================
BUSINESS INFO
===========================
Name: {business_name}
Category: {business_category}
Description: {business_description}
Address: {business_address}
Phone: {phone}
Email: {email}
Logo URL: {logo_url}
Color Theme: {color_theme}
Tone: {tone}

===========================
E-COMMERCE ENABLED: {ecommerce_enabled}
===========================

Products (if any):
{json.dumps(products, indent=2)}

===========================
REQUIRED OUTPUT FORMAT
===========================

Return ONLY a JSON object with keys:
- home
- about
- services
- store
- products  (dictionary of product_name → HTML)
- contact

Example:
{{
  "home": "<html>...</html>",
  "about": "<html>...</html>",
  "services": "<html>...</html>",
  "store": "<html>...</html>",
  "products": {{
      "Product Name": "<html>...</html>",
      "Another Product": "<html>...</html>"
  }},
  "contact": "<html>...</html>"
}}

===========================
PAGE REQUIREMENTS
===========================

HOME PAGE (mandatory)
- Big hero section with strong title + subtitle
- CTA buttons
- Services or product grid
- Testimonials (AI generated)
- FAQ
- Footer

ABOUT PAGE
- Company story
- Mission
- Values
- Team members (AI generated)

SERVICES PAGE
- 3–6 detailed services
- Benefits
- Pricing suggestions

STORE PAGE (if ecommerce_enabled = true)
- Product grid layout
- Product cards with image/price/description

PRODUCT PAGES
For each product:
- SEO title
- Meta description
- Features
- Benefits
- Story
- Specifications
- FAQ
- Reviews (AI generated)

CONTACT PAGE
- Contact form HTML
- Business info
- Google Maps placeholder

===========================
STYLE GUIDE
===========================
- Modern
- Tailwind style classes
- Clean structure
- No lorem ipsum
- Use the color theme

===========================
RETURN ONLY VALID JSON
===========================
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        max_output_tokens=120000
    )

    raw_text = response.output_text

    try:
        site_json = json.loads(raw_text)
        return site_json

    except Exception as e:
        # Safety fallback: wrap raw text in a JSON object
        print("JSON parsing failed — returning fallback wrapper:", e)
        return {
            "home": raw_text,
            "about": "",
            "services": "",
            "store": "",
            "products": {},
            "contact": "",
        }
