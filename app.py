import os
import re
import uuid
import zipfile
import shutil

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    session,
    abort,
)
from dotenv import load_dotenv
import stripe

from brain import generate_commerce_site

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-key")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(BASE_DIR, "generated")
SITES_DIR = os.path.join(BASE_DIR, "sites")

os.makedirs(GEN_DIR, exist_ok=True)
os.makedirs(SITES_DIR, exist_ok=True)


# ----------------------------
# Helpers
# ----------------------------
def slugify(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "site"


def save_multipage_site(site_json):
    """Save pages from JSON and create a ZIP. Returns (folder_id, zip_path, folder_path)."""
    folder_id = uuid.uuid4().hex
    folder_path = os.path.join(GEN_DIR, folder_id)
    os.makedirs(folder_path, exist_ok=True)

    for key, html in site_json.items():
        if key == "products":
            for p_name, p_html in html.items():
                safe = slugify(p_name)
                file_path = os.path.join(folder_path, f"product-{safe}.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(p_html)
        else:
            file_path = os.path.join(folder_path, f"{key}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)

    zip_path = os.path.join(GEN_DIR, folder_id + ".zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                full = os.path.join(root, filename)
                arc = os.path.relpath(full, folder_path)
                zipf.write(full, arc)

    return folder_id, zip_path, folder_path


def copy_site_to_subdomain(business_slug: str, folder_path: str):
    """Copies generated site to sites/<business_slug>/."""
    dest_folder = os.path.join(SITES_DIR, business_slug)
    if os.path.isdir(dest_folder):
        shutil.rmtree(dest_folder)
    shutil.copytree(folder_path, dest_folder)
    return dest_folder


# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
def index():
    """
    If host is <slug>.xaiwebsites.com → serve that site's home.
    Otherwise show generator UI.
    """
    host = (request.host or "").split(":")[0].lower()

    if host.endswith("xaiwebsites.com") and host not in ("xaiwebsites.com", "www.xaiwebsites.com"):
        subdomain = host.split(".")[0]
        site_folder = os.path.join(SITES_DIR, subdomain)
        home_path = os.path.join(site_folder, "home.html")
        if os.path.exists(home_path):
            return send_file(home_path, mimetype="text/html")
        return "Site not found (not deployed yet).", 404

    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    business = request.form.get("business") or ""
    category = request.form.get("category") or ""
    description = request.form.get("description") or ""
    city = request.form.get("city") or ""

    # Products only for future ecommerce versions – kept but optional
    products = []
    if category == "ecommerce":
        names = request.form.getlist("product_name[]")
        prices = request.form.getlist("product_price[]")
        descs = request.form.getlist("product_desc[]")
        images = request.form.getlist("product_image[]")
        for n, p, d, i in zip(names, prices, descs, images):
            if n.strip():
                products.append(
                    {
                        "name": n,
                        "price": p,
                        "description": d,
                        "image": i,
                    }
                )

    try:
        site_json = generate_commerce_site(business, category, description, city, products)
    except Exception as e:
        print("ERROR in /generate route:", repr(e), flush=True)
        return "Error while generating website. Please try again later.", 500

    folder_id, zip_path, folder_path = save_multipage_site(site_json)

    preview_url = url_for("preview_file", folder=folder_id, file="home.html")
    download_url = url_for("download_zip", folder=folder_id)
    business_slug = slugify(business)

    return render_template(
        "result.html",
        preview_url=preview_url,
        download_url=download_url,
        folder_id=folder_id,
        business_slug=business_slug,
        is_pro=session.get("is_pro", False),
    )


@app.route("/preview/<folder>/<file>", methods=["GET"])
def preview_file(folder, file):
    safe_folder = os.path.basename(folder)
    safe_file = os.path.basename(file)
    path = os.path.join(GEN_DIR, safe_folder, safe_file)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="text/html")


@app.route("/download/<folder>", methods=["GET"])
def download_zip(folder):
    if not session.get("is_pro"):
        return redirect(url_for("pricing"))

    safe_folder = os.path.basename(folder)
    zip_path = os.path.join(GEN_DIR, safe_folder + ".zip")
    if not os.path.exists(zip_path):
        abort(404)

    return send_file(
        zip_path,
        as_attachment=True,
        download_name="website.zip",
        mimetype="application/zip",
    )


@app.route("/deploy/<folder>", methods=["POST"])
def deploy(folder):
    if not session.get("is_pro"):
        return redirect(url_for("pricing"))

    business_slug = slugify(request.form.get("business_slug") or "")
    if not business_slug:
        return "Missing business name/slug", 400

    safe_folder = os.path.basename(folder)
    src_folder = os.path.join(GEN_DIR, safe_folder)
    if not os.path.isdir(src_folder):
        abort(404)

    copy_site_to_subdomain(business_slug, src_folder)
    live_url = f"https://{business_slug}.xaiwebsites.com"

    return (
        f"Deployed successfully! Your live site will be available at {live_url} "
        "once DNS wildcard for *.xaiwebsites.com is configured."
    )


@app.route("/pricing", methods=["GET"])
def pricing():
    try:
        return render_template("pricing.html", is_pro=session.get("is_pro", False))
    except Exception:
        return "Pricing page not set up yet.", 200


@app.route("/create-checkout-session", methods=["GET"])
def create_checkout_session():
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_PRO:
        return "Stripe is not configured.", 500

    domain = request.url_root.rstrip("/")
    checkout = stripe.checkout.Session.create(
        line_items=[{"price": STRIPE_PRICE_PRO, "quantity": 1}],
        mode="subscription",
        success_url=domain + url_for("success"),
        cancel_url=domain + url_for("cancel"),
    )
    return redirect(checkout.url, code=303)


@app.route("/success", methods=["GET"])
def success():
    session["is_pro"] = True
    return "Pro subscription active! (Replace with nice template later.)"


@app.route("/cancel", methods=["GET"])
def cancel():
    return "Payment canceled."


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
