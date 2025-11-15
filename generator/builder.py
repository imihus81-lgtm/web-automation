import os
import uuid
import json
import zipfile
import tempfile
import openai

# Simple industry style library
INDUSTRY_STYLES = {
    "roofing": {
        "accent": "#2563eb",
        "bg": "#eff6ff",
        "emoji": "🏠",
        "default_services": [
            "Roof inspection & reports",
            "Leak repair & emergency tarping",
            "Full roof replacement",
            "Gutter installation & cleaning"
        ]
    },
    "electrician": {
        "accent": "#f97316",
        "bg": "#fff7ed",
        "emoji": "💡",
        "default_services": [
            "Residential wiring & repairs",
            "Panel upgrades",
            "EV charger installation",
            "Lighting design & installation"
        ]
    },
    "plumber": {
        "accent": "#0ea5e9",
        "bg": "#e0f2fe",
        "emoji": "🚿",
        "default_services": [
            "Emergency leak repair",
            "Drain cleaning",
            "Water heater installation",
            "Bathroom & kitchen plumbing"
        ]
    },
    "restaurant": {
        "accent": "#dc2626",
        "bg": "#fef2f2",
        "emoji": "🍽️",
        "default_services": [
            "Lunch & dinner menu",
            "Private events & catering",
            "Online reservations",
            "Take-out & delivery"
        ]
    },
    "dentist": {
        "accent": "#14b8a6",
        "bg": "#ecfeff",
        "emoji": "🦷",
        "default_services": [
            "Checkups & cleaning",
            "Cosmetic dentistry",
            "Implants & crowns",
            "Emergency appointments"
        ]
    },
    "real estate": {
        "accent": "#4f46e5",
        "bg": "#eef2ff",
        "emoji": "🏡",
        "default_services": [
            "Buying your next home",
            "Selling with expert marketing",
            "Rental property management",
            "Free home valuation"
        ]
    }
}

DEFAULT_STYLE = {
    "accent": "#2563eb",
    "bg": "#eff6ff",
    "emoji": "🏢",
    "default_services": [
        "Professional consulting",
        "Personalized service packages",
        "Dedicated customer support",
        "Flexible pricing options"
    ]
}


def _choose_style(industry: str):
    if not industry:
        return DEFAULT_STYLE
    key = industry.lower().strip()
    # map e.g. "roofer" -> "roofing"
    if key.startswith("roof"):
        key = "roofing"
    if key.startswith("electric"):
        key = "electrician"
    if key.startswith("plumb"):
        key = "plumber"
    if key in INDUSTRY_STYLES:
        return INDUSTRY_STYLES[key]
    return DEFAULT_STYLE


def _call_openai(business, industry, city):
    """
    Ask OpenAI only for TEXT content in JSON.
    We keep design (HTML/CSS) on our side for consistent, premium look.
    """
    prompt = f"""
    You are a marketing copywriter.

    Create website copy in JSON format ONLY (no explanation, no markdown)
    for this small business:

    Business: {business}
    Industry: {industry}
    City: {city}

    JSON format:
    {{
      "headline": "...",
      "subheadline": "...",
      "about": "...",
      "services": ["...", "...", "..."],
      "why_choose": ["...", "...", "..."],
      "cta": "...",
      "tagline": "short 1-line slogan"
    }}

    Keep it friendly, professional, and localized to {city}.
    """

    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    content = res.choices[0].message["content"]

    try:
        data = json.loads(content)
    except Exception:
        # Fallback if model adds text around JSON
        start = content.find("{")
        end = content.rfind("}")
        data = json.loads(content[start:end+1])

    return data


def _render_index_html(style, data, business, industry, city):
    accent = style["accent"]
    bg = style["bg"]
    emoji = style["emoji"]

    services = data.get("services") or style["default_services"]
    why_choose = data.get("why_choose") or [
        "Local experts you can trust.",
        "Fast response and clear communication.",
        "Transparent pricing with no hidden fees."
    ]

    headline = data.get("headline", f"Premium {industry.title()} in {city}")
    subheadline = data.get("subheadline", "")
    about = data.get("about", "")
    tagline = data.get("tagline", "")
    cta = data.get("cta", "Call today to get your free quote!")

    services_html = "".join(
        f"<li>{s}</li>" for s in services
    )
    why_html = "".join(
        f"<li>{w}</li>" for w in why_choose
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{business} - {industry.title()} in {city}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{tagline}">
  <style>
    :root {{
      --accent: {accent};
      --bg: {bg};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(135deg, #0f172a, #020617);
      color: #0f172a;
    }}
    .shell {{
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 32px 16px;
    }}
    .card {{
      width: 100%;
      max-width: 1100px;
      background: white;
      border-radius: 24px;
      box-shadow: 0 40px 80px rgba(15,23,42,.35);
      display: grid;
      grid-template-columns: 3fr 2fr;
      overflow: hidden;
    }}
    @media (max-width: 900px) {{
      .card {{ grid-template-columns: 1fr; }}
      .side {{ order: -1; }}
    }}
    .main {{
      padding: 40px 40px 32px 40px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(37,99,235,.08);
      color: #1d4ed8;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 16px;
    }}
    h1 {{
      font-size: 34px;
      line-height: 1.1;
      margin-bottom: 10px;
    }}
    .sub {{
      color: #4b5563;
      margin-bottom: 22px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.4fr 1.3fr;
      gap: 24px;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
    h2 {{
      font-size: 18px;
      margin-bottom: 8px;
    }}
    ul {{
      list-style: none;
      padding-left: 0;
      color: #4b5563;
      font-size: 14px;
    }}
    ul li::before {{
      content: "• ";
      color: var(--accent);
      font-weight: 700;
    }}
    .cta-box {{
      margin-top: 24px;
      padding: 16px 18px;
      border-radius: 14px;
      background: {bg};
      border: 1px solid rgba(15,23,42,.06);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }}
    .cta-box p {{
      font-size: 14px;
      color: #374151;
    }}
    .cta-btn {{
      padding: 10px 20px;
      border-radius: 999px;
      border: none;
      background: var(--accent);
      color: white;
      font-size: 14px;
      font-weight: 600;
    }}
    .side {{
      padding: 32px 32px 28px 32px;
      background: radial-gradient(circle at top left, var(--accent), #0f172a);
      color: white;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .side-tag {{
      font-size: 12px;
      letter-spacing: .12em;
      text-transform: uppercase;
      opacity: .8;
      margin-bottom: 8px;
    }}
    .side-title {{
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 10px;
    }}
    .side-city {{
      font-size: 14px;
      opacity: .9;
    }}
    .side-footer {{
      font-size: 11px;
      opacity: .75;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
<div class="shell">
  <div class="card">
    <div class="main">
      <div class="badge">{emoji} {industry.title()} · {city}</div>
      <h1>{headline}</h1>
      <p class="sub">{subheadline}</p>
      <div class="grid">
        <div>
          <h2>About {business}</h2>
          <p style="color:#4b5563;font-size:14px;margin-bottom:12px;">{about}</p>
          <h2 style="margin-top:10px;">Why customers choose us</h2>
          <ul>
            {why_html}
          </ul>
        </div>
        <div>
          <h2>Services</h2>
          <ul>
            {services_html}
          </ul>
        </div>
      </div>
      <div class="cta-box">
        <p><strong>Ready to get started?</strong><br>{cta}</p>
        <button class="cta-btn">Call today</button>
      </div>
    </div>
    <div class="side">
      <div>
        <div class="side-tag">PRO WEBSITE · POWERED BY XAIWEBSITES</div>
        <div class="side-title">{business}</div>
        <div class="side-city">{city} · {industry.title()}</div>
      </div>
      <div class="side-footer">
        This website was generated automatically. Replace this text with your
        phone number, email, and business address when you publish it.
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""
    return html


def _render_about_html(style, data, business, industry, city):
    # Simple about page using same content
    accent = style["accent"]
    bg = style["bg"]
    emoji = style["emoji"]
    about = data.get("about", "")
    tagline = data.get("tagline", "")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>About {business}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: {bg};
      color: #0f172a;
    }}
    .wrap {{
      max-width: 800px;
      margin: 40px auto;
      padding: 0 16px 40px;
    }}
    h1 {{
      font-size: 32px;
      margin-bottom: 6px;
    }}
    .tag {{
      color: #6b7280;
      font-size: 14px;
      margin-bottom: 20px;
    }}
    .pill {{
      display:inline-flex;
      align-items:center;
      padding:4px 10px;
      border-radius:999px;
      background:white;
      border:1px solid rgba(15,23,42,.08);
      font-size:12px;
      margin-bottom:10px;
    }}
    a {{
      color: {accent};
      text-decoration:none;
      font-weight:600;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="pill">{emoji} About {business}</div>
    <h1>Our story</h1>
    <div class="tag">{tagline}</div>
    <p style="line-height:1.7;font-size:15px;">{about}</p>
    <p style="margin-top:26px;font-size:14px;">
      Back to <a href="index.html">{business} homepage</a>
    </p>
  </div>
</body>
</html>
"""
    return html


def build_site(business, industry, city):
    # Fetch content
    data = _call_openai(business, industry, city)
    style = _choose_style(industry)

    index_html = _render_index_html(style, data, business, industry, city)
    about_html = _render_about_html(style, data, business, industry, city)

    # Create temp folder + files
    folder = tempfile.mkdtemp()
    index_path = os.path.join(folder, "index.html")
    about_path = os.path.join(folder, "about.html")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    with open(about_path, "w", encoding="utf-8") as f:
        f.write(about_html)

    # Zip them
    zip_filename = f"website_{uuid.uuid4().hex}.zip"
    zip_path = os.path.join(folder, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(index_path, "index.html")
        zipf.write(about_path, "about.html")

    return zip_path
