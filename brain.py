import os
import json
from openai import OpenAI

# Make sure OPENAI_API_KEY is set in Render/ENV
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _fallback_site(business, category, description, city):
    """Safe backup if OpenAI or JSON fails."""
    title = business or "Your Business"
    city_text = f"in {city}" if city else ""

    home = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title} – {category}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background:#f1f5f9; color:#0f172a; }}
    header {{ background:#0f172a; color:#e5e7eb; padding:24px 32px; }}
    main {{ max-width:960px; margin:0 auto; padding:32px 16px 40px; }}
    section {{ background:#ffffff; border-radius:12px; padding:20px 22px; margin-bottom:20px;
              box-shadow:0 16px 40px rgba(15,23,42,0.10); }}
    h1,h2 {{ margin:0 0 10px; }}
    ul {{ margin:0 0 0 18px; }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p>{category.title()} services {city_text}</p>
  </header>
  <main>
    <section>
      <h2>About Us</h2>
      <p>{description or "We provide reliable local services with a focus on quality and customer satisfaction."}</p>
    </section>
    <section>
      <h2>Our Services</h2>
      <ul>
        <li>Core service #1</li>
        <li>Core service #2</li>
        <li>Core service #3</li>
      </ul>
    </section>
    <section>
      <h2>Contact</h2>
      <p>Email: info@example.com<br>Phone: 000-000-0000</p>
    </section>
  </main>
</body>
</html>
"""

    empty_page = "<html><body></body></html>"

    return {
        "home": home,
        "about": empty_page,
        "services": empty_page,
        "store": "",
        "products": {},
        "contact": empty_page,
    }


def generate_commerce_site(business, category, description, city, products):
    """
    Main brain function.

    Returns dict with keys:
    home, about, services, store, products, contact

    Never crashes: if OpenAI/JSON fails, returns a simple fallback site.
    """

    ecommerce_enabled = "YES" if products else "NO"

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

Generate clean, responsive HTML with simple CSS (NO Tailwind, NO JavaScript requiring build tools).

BUSINESS:
- Name: {business}
- Category: {category}
- City: {city}
- Description: {description}

E-COMMERCE:
- Enabled: {ecommerce_enabled}

PRODUCTS:
{product_text if product_text else "- (no specific products; create generic store if needed)"}

PAGES TO GENERATE:

1. HOME PAGE ("home")
2. ABOUT PAGE ("about")
3. SERVICES PAGE ("services")
4. STORE PAGE ("store") — only if ecommerce_enabled = YES (otherwise "")
5. PRODUCT PAGES ("products") — object mapping name→HTML; empty object if no products
6. CONTACT PAGE ("contact")

STYLE:
- Mobile friendly
- Simple CSS in <style> tag
- Real copy, no lorem ipsum.

OUTPUT (IMPORTANT):
Return ONLY valid JSON with this structure:

{{
  "home": "<html>...</html>",
  "about": "<html>...</html>",
  "services": "<html>...</html>",
  "store": "<html>...</html>",
  "products": {{
      "PRODUCT_NAME": "<html>...</html>"
  }},
  "contact": "<html>...</html>"
}}

If no ecommerce: "store" = "" and "products" = {{}}.
No explanations, no markdown, no backticks — only JSON.
"""

    # 1) Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate full multi-page websites as JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content
    except Exception as e:
        print("OpenAI error in generate_commerce_site:", repr(e), flush=True)
        return _fallback_site(business, category, description, city)

    # 2) Parse JSON safely
    try:
        data = json.loads(raw)
    except Exception:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            cleaned = raw[start:end]
            data = json.loads(cleaned)
        except Exception as e:
            print("JSON parse error in generate_commerce_site:", repr(e), "RAW:", raw[:300], flush=True)
            return _fallback_site(business, category, description, city)

    # 3) Ensure all keys exist
    for key in ["home", "about", "services", "store", "products", "contact"]:
        if key not in data:
            if key == "products":
                data[key] = {}
            elif key == "store":
                data[key] = ""
            else:
                data[key] = "<html><body></body></html>"

    return data
