import os
import re
import uuid

from flask import (
    Flask,
    render_template,
    request,
    url_for,
    send_file,
    abort,
    Response,
    redirect,
    session,
)
from dotenv import load_dotenv
from openai import OpenAI
import stripe

import brain

# -----------------------------
# ENV + CLIENTS
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or Render env vars.")

client = OpenAI()  # uses OPENAI_API_KEY from environment

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")  # sk_test_...
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")    # price_xxx from Stripe

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY is not set. Add it to .env or Render env vars.")
if not STRIPE_PRICE_PRO:
    raise RuntimeError("STRIPE_PRICE_PRO is not set. Create a Price in Stripe and add it.")

stripe.api_key = STRIPE_SECRET_KEY

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-please")
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


# -----------------------------
# HELPERS
# -----------------------------
def slugify(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "website"


def strip_code_fences(text: str) -> str:
    """Remove ```html fences if the model adds them."""
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```html"):
        t = t[len("```html") :].lstrip()
    elif t.startswith("```"):
        t = t[len("```") :].lstrip()
    if t.endswith("```"):
        t = t[:-3].rstrip()
    return t


def generate_html_with_openai(prompt: str) -> str:
    """Call OpenAI to generate raw HTML (no markdown)."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert web designer. "
                    "Return ONLY valid HTML for a full webpage. "
                    "No markdown, no code fences, no explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.65,
    )
    html = response.choices[0].message.content
    return strip_code_fences(html)


# -----------------------------
# ROUTES – MAIN APP
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    business_name = request.form.get("business_name", "").strip()
    industry = request.form.get("industry", "").strip()
    city = request.form.get("city", "").strip()
    style_choice = request.form.get("style_choice", "").strip() or None

    if not (business_name and industry and city):
        error = "Please fill in business name, industry, and city."
        return render_template(
            "index.html",
            error=error,
            business_name=business_name,
            industry=industry,
            city=city,
            style_choice=style_choice,
        )

    # Ask the brain for the best template + prompt
    prompt, template_id = brain.build_prompt_for_business(
        business_name=business_name,
        industry=industry,
        city=city,
        preferred_template_id=style_choice,
    )

    # Generate HTML from OpenAI
    html_content = generate_html_with_openai(prompt)

    # Save file for preview & download
    slug = slugify(business_name)
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{slug}-{unique_id}.html"
    file_path = os.path.join(GENERATED_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    preview_url = url_for("preview_site", file_id=filename)
    download_url = url_for("download_site", file_id=filename)

    return render_template(
        "result.html",
        preview_url=preview_url,
        download_url=download_url,
        html_content=html_content,
        is_pro=session.get("is_pro", False),
    )


@app.route("/preview/<path:file_id>", methods=["GET"])
def preview_site(file_id: str):
    safe_name = os.path.basename(file_id)
    file_path = os.path.join(GENERATED_DIR, safe_name)
    if not os.path.exists(file_path):
        abort(404)

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    return Response(html, mimetype="text/html")


@app.route("/download/<path:file_id>", methods=["GET"])
def download_site(file_id: str):
    """
    For now, still allow everyone to download.
    In the next step, we can restrict this for non-Pro users using session['is_pro'].
    """
    safe_name = os.path.basename(file_id)
    file_path = os.path.join(GENERATED_DIR, safe_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_name,
        mimetype="text/html",
    )


@app.route("/pricing", methods=["GET"])
def pricing():
    return render_template("pricing.html", is_pro=session.get("is_pro", False))


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


# -----------------------------
# STRIPE CHECKOUT (TEST MODE)
# -----------------------------
@app.route("/create-checkout-session", methods=["GET"])
def create_checkout_session():
    """
    Creates a Stripe Checkout Session (subscription for Pro).
    Uses test mode as long as STRIPE_SECRET_KEY is a test key.
    """
    domain = request.url_root.rstrip("/")

    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[
            {
                "price": STRIPE_PRICE_PRO,
                "quantity": 1,
            }
        ],
        success_url=domain + url_for("success") + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=domain + url_for("cancel"),
    )

    return redirect(checkout_session.url, code=303)


@app.route("/success", methods=["GET"])
def success():
    """
    Called after successful Stripe checkout.
    For now, we simply mark this browser session as Pro.
    Later we can verify the session_id with Stripe if needed.
    """
    session["is_pro"] = True
    return render_template("success.html")


@app.route("/cancel", methods=["GET"])
def cancel():
    return render_template("cancel.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
