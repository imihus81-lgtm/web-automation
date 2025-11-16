import os
import json
import zipfile
import io
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
)

from dotenv import load_dotenv
import stripe

from brain import generate_commerce_site_v11

# -------------------------------------------------
# Basic config
# -------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# -------------------------------------------------
# Stripe config
# -------------------------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def slugify(text: str) -> str:
    import re
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "site"


def save_multipage_site(slug: str, site: dict) -> str:
    """
    Save multi-page site from brain_v11 into generated/<slug>/.
    Returns folder path.
    """
    folder = os.path.join(GENERATED_DIR, slug)
    os.makedirs(folder, exist_ok=True)

    # Helper to save html file
    def _save(name, html):
        if not html:
            return
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    _save("home.html", site.get("home", ""))
    _save("about.html", site.get("about", ""))
    _save("services.html", site.get("services", ""))
    _save("contact.html", site.get("contact", ""))
    _save("store.html", site.get("store", ""))

    products = site.get("products", {}) or {}
    prod_folder = os.path.join(folder, "products")
    if products:
        os.makedirs(prod_folder, exist_ok=True)
        for name, html in products.items():
            fname = slugify(name) + ".html"
            _save(os.path.join("products", fname), html)

    # Save metadata / SEO for later
    meta_path = os.path.join(folder, "meta.json")
    meta = {
        "seo": site.get("seo", {}),
        "generated_at": site.get("generated_at", str(datetime.utcnow())),
        "template_style": site.get("template_style"),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return folder


def copy_site_to_subdomain(slug: str) -> str:
    """
    Placeholder for subdomain deployment.
    For now, just returns a fake URL.
    Later: connect to real static hosting.
    """
    # Example future URL
    return f"https://{slug}.xaiwebsites.com"


# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route("/")
def home():
    is_pro = session.get("pro_user", False)
    return render_template("index.html", is_pro=is_pro)


@app.route("/pricing")
def pricing():
    is_pro = session.get("pro_user", False)
    return render_template("pricing.html", is_pro=is_pro)


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": STRIPE_PRICE_PRO, "quantity": 1}],
            success_url=request.host_url.rstrip("/")
            + "/stripe-success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.host_url.rstrip("/") + "/pricing",
        )
        return redirect(checkout.url, code=303)
    except Exception as e:
        print("Stripe error:", e)
        return "Stripe checkout failed. Please try later.", 500


@app.route("/stripe-success")
def stripe_success():
    session["pro_user"] = True
    return render_template("stripe_success.html")


# -------------------------------------------------
# Generate website (V11 Brain)
# -------------------------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    is_pro = session.get("pro_user", False)

    business = request.form.get("business_name")
    industry = request.form.get("industry")
    city = request.form.get("city")
    description = request.form.get("description")
    template_style = request.form.get("template_style", "modern_neon")

    products_raw = request.form.get("products", "")
    wants_ecommerce = request.form.get("is_ecommerce") == "yes"

    products = []
    if products_raw.strip():
        for line in products_raw.split(";"):
            if line.strip():
                # Allow "Name – Price" or "Name - Price"
                if "–" in line:
                    parts = line.split("–", 1)
                elif "-" in line:
                    parts = line.split("-", 1)
                else:
                    parts = [line]
                name = parts[0].strip()
                price = parts[1].strip() if len(parts) > 1 else ""
                products.append({"name": name, "price": price})

    # If user checked ecommerce but didn't list products,
    # create a generic placeholder product so brain knows it's a store.
    if wants_ecommerce and not products:
        products.append({"name": "Sample Product", "price": ""})

    # Free plan restriction (optional: disable ecommerce for free)
    if not is_pro:
        # You can comment this out if you want ecommerce for free too:
        # products = []
        pass

    data = {
        "business_name": business,
        "category": industry,
        "city": city,
        "description": description,
        "products": products,
        "template_style": template_style,
    }

    site = generate_commerce_site_v11(data)

    slug = slugify(business)
    save_multipage_site(slug, site)
    session["last_slug"] = slug

    return render_template(
        "result.html",
        site=site,
        slug=slug,
        is_pro=is_pro,
        template_style=template_style,
    )


# -------------------------------------------------
# Download site (Pro only)
# -------------------------------------------------
@app.route("/download")
def download():
    is_pro = session.get("pro_user", False)
    if not is_pro:
        return redirect("/pricing")

    slug = session.get("last_slug")
    if not slug:
        return "No site available to download.", 400

    folder = os.path.join(GENERATED_DIR, slug)
    if not os.path.isdir(folder):
        return "Site folder not found.", 404

    # Create in-memory ZIP
    mem_file = io.BytesIO()
    with zipfile.ZipFile(mem_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, folder)
                zf.write(full_path, rel_path)
    mem_file.seek(0)

    filename = f"{slug}.zip"
    return send_file(
        mem_file,
        as_attachment=True,
        download_name=filename,
        mimetype="application/zip",
    )


# -------------------------------------------------
# Publish (Pro only, placeholder)
# -------------------------------------------------
@app.route("/publish")
def publish():
    is_pro = session.get("pro_user", False)
    if not is_pro:
        return redirect("/pricing")

    slug = session.get("last_slug")
    if not slug:
        return "No site available to publish.", 400

    url = copy_site_to_subdomain(slug)
    # TODO: implement real deployment
    return f"Subdomain deployment coming soon. Planned URL: {url}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
