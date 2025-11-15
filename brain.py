import os
import json
from openai import OpenAI

# Make sure OPENAI_API_KEY is set in Render env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_commerce_site(business, category, description, city, products):
    """
    Generate a FULL multi-page website (home, about, services, store, products, contact)
    and return it as a Python dict using this structure:

    {
      "home": "<html>...</html>",
      "about": "<html>...</html>",
      "services": "<html>...</html>",
      "store": "<html>...</html>",
      "products": {
          "PRODUCT_NAME": "<html>...</html>"
      },
      "contact": "<html>...</html>"
    }
    """

    ecommerce_enabled = "YES" if products else "NO"

    # Turn product list into text for the prompt
    product_text = ""
    for p in products:
        product_text += f"""
- Name: {p.get('name','')}
  Price: {p.get('price','')}
  Description: {p.get('description','')}
  Image URL: {p.get('image','')}
  Stock: 20
"""

    prompt = f"""
You are XAI Commerce — an ultra-advanced AI Shopify engine.

Your job is to create complete business multi-page websites and full online stores.

Generate clean, responsive HTML with simple CSS (NO Tailwind, NO JavaScript that requires build tools).

---------------------------------------
BUSINESS INFO
---------------------------------------
Name: {business}
Category: {category}
City: {city}
Description: {description}

---------------------------------------
E-COMMERCE MODE
---------------------------------------
Enabled: {ecommerce_enabled}

Products:
{product_text}

---------------------------------------
PAGES TO GENERATE
---------------------------------------

1. HOME PAGE ("home" key)
- Hero section with strong headline
- Short about section
- Featured services or products
- Testimonials
- FAQ
- Call-to-action

2. ABOUT PAGE ("about" key)
- Company story
- Mission
- Values
- Simple team section (AI generated names & roles)

3. SERVICES PAGE ("services" key)
- 4–6 services relevant to the category
- Each service: name, description, benefits
- Optional pricing suggestions

4. STORE PAGE ("store" key) — ONLY if ecommerce_enabled = YES
- Product grid with cards
- Each card: image (placeholder ok), name, price, short description
- Links to each product page

5. PRODUCT PAGES ("products" object) — ONLY if ecommerce_enabled = YES
For each product:
- Full product page HTML
- Hero with product name and price
- Detailed description
- Features list
- Specifications
- FAQ
- 1–3 short review quotes
- Add-to-cart button placeholder (no JS needed)

6. CONTACT PAGE ("contact" key)
- Contact form (HTML only, no JS required)
- Address, phone, email
- Google Maps placeholder section

---------------------------------------
STYLE GUIDE
---------------------------------------
- Modern layout, mobile-friendly
- Simple CSS in <style> tag if needed
- Use the business name and city inside the copy
- No lorem ipsum; all real-looking text
- All pages should be standalone HTML documents (<html>...</html>)

---------------------------------------
OUTPUT FORMAT (IMPORTANT)
---------------------------------------
Return ONLY a valid JSON object using EXACTLY this structure:

{
  "home": "<html>...</html>",
  "about": "<html>...</html>",
  "services": "<html>...</html>",
  "store": "<html>...</html>",
  "products": {
      "PRODUCT_NAME": "<html>...</html>",
      "PRODUCT_NAME_2": "<html>...</html>"
  },
  "contact": "<html>...</html>"
}

- If no ecommerce, set "store" to an empty string "" and "products" to an empty object {{}}.
- Do not include any explanation outside the JSON.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate full multi-page websites as JSON."},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content

    # Try to parse as JSON directly first
    try:
        data = json.loads(raw)
        return data
    except Exception:
        # Sometimes the model may add text around JSON – try to extract the JSON block
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("Model output did not contain valid JSON.")
        cleaned = raw[start:end]
        data = json.loads(cleaned)
        return data
