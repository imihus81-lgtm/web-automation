import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# ==========================
# LOAD ENV
# ==========================
load_dotenv()

# OPENAI CLIENT (auto loads OPENAI_API_KEY)
client = OpenAI()


# ==========================
# SAFETY
# ==========================
def safe(v):
    return v if v else ""


# ==========================
# MAIN WEBSITE GENERATOR (NO reasoning.effort)
# ==========================
def generate_commerce_site(
    business_name,
    business_category,
    business_description,
    city,
    products=None,
    color_theme="blue",
    email="",
    phone="",
    logo_url=""
):
    products = products or []

    prompt = f"""
You are XAI Commerce — an ultra-advanced AI Shopify-style website generator.

Generate COMPLETE MULTIPAGE WEBSITE JSON.

---------------------------------------
INPUT
---------------------------------------
BUSINESS_NAME: {business_name}
BUSINESS_CATEGORY: {business_category}
BUSINESS_DESCRIPTION: {business_description}
CITY: {city}
EMAIL: {email}
PHONE: {phone}
COLOR_THEME: {color_theme}
LOGO_URL: {logo_url}
PRODUCTS: {products}

---------------------------------------
OUTPUT FORMAT (STRICT)
---------------------------------------
{{
  "home": "<html>...</html>",
  "about": "<html>...</html>",
  "services": "<html>...</html>",
  "store": "<html>...</html>",
  "products": {{
      "product1": "<html>...</html>"
  }},
  "contact": "<html>...</html>"
}}

If no products exist:
- store = ""
- products = {{}}

---------------------------------------
STYLE
---------------------------------------
- Modern clean HTML with inline CSS or TailwindCDN
- NO external JS build tools
- No lorem ipsum
- Business-ready copywriting
"""

    # ===== API CALL (NO REASONING BLOCK) =====
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "system", "content": prompt}]
    )

    # Extract text output
    try:
        raw = response.output[0].content[0].text
        data = json.loads(raw)
        return data
    except Exception as e:
        print("❌ JSON ERROR in brain.py:", e)
        return fallback_site(business_name)


# ==========================
# PREVIEW HELPER
# ==========================
def quick_preview_html(business, slug):
    url = f"https://{slug}.xaiwebsites.com"
    return f"""
    <html><body>
    <h2>{business}</h2>
    <p>Your preview:</p>
    <a href="{url}">{url}</a>
    </body></html>
    """


# ==========================
# FALLBACK (NEVER BREAK ENGINE)
# ==========================
def fallback_site(business):
    return {
        "home": f"<html><body><h1>{business}</h1><p>Site failed to generate.</p></body></html>",
        "about": "",
        "services": "",
        "store": "",
        "products": {},
        "contact": "",
    }
