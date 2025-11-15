import os
import uuid
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    session,
    abort,
)
from dotenv import load_dotenv
import stripe
from brain import generate_website_html

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

stripe.api_key = STRIPE_SECRET_KEY

# ----------------------------
# Flask App
# ----------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


# ----------------------------
# Helpers
# ----------------------------
def create_temp_html(content: str):
    """Store generated HTML into a unique file and return its ID"""
    file_id = f"{uuid.uuid4().hex}.html"
    path = os.path.join(GENERATED_DIR, file_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_id


# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ------------ RESULT PAGE (preview only for free users)
@app.route("/generate", methods=["POST"])
def generate():
    business = request.form.get("business") or ""
    industry = request.form.get("industry") or ""
    city = request.form.get("city") or ""

    # Call your brain engine
    html = generate_website_html(business, industry, city)

    # Save HTML file
    file_id = create_temp_html(html)

    # Links for iframe + download
    preview_url = url_for("preview_site", file_id=file_id)
    download_url = url_for("download_site", file_id=file_id)

    return render_template(
        "result.html",
        html_content=html,
        preview_url=preview_url,
        download_url=download_url,
        is_pro=session.get("is_pro", False),
    )


# ------------ LIVE PREVIEW
@app.route("/preview/<path:file_id>")
def preview_site(file_id):
    safe = os.path.basename(file_id)
    path = os.path.join(GENERATED_DIR, safe)

    if not os.path.exists(path):
        abort(404)

    return send_file(path, mimetype="text/html")


# ------------ DOWNLOAD (LOCKED FOR FREE USERS)
@app.route("/download/<path:file_id>")
def download_site(file_id):
    if not session.get("is_pro"):
        return redirect(url_for("pricing"))  # 🔒 LOCKED

    safe = os.path.basename(file_id)
    path = os.path.join(GENERATED_DIR, safe)

    if not os.path.exists(path):
        abort(404)

    return send_file(
        path,
        as_attachment=True,
        download_name=safe,
        mimetype="text/html",
    )


# ------------ PRICING PAGE
@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


# ------------ STRIPE CHECKOUT SESSION (PRO PLAN)
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout = stripe.checkout.Session.create(
            line_items=[
                {"price": STRIPE_PRICE_PRO, "quantity": 1}
            ],
            mode="subscription",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("cancel", _external=True),
        )
        return redirect(checkout.url)

    except Exception as e:
        return f"Stripe Error: {e}", 400


# ------------ SUCCESS PAGE
@app.route("/success")
def success():
    session["is_pro"] = True
    return render_template("success.html")


# ------------ CANCEL PAGE
@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


# ------------ HEALTH CHECK (Render)
@app.route("/health")
def health():
    return "OK", 200


# ------------ RUN LOCAL
if __name__ == "__main__":
    app.run(debug=True, port=5000)
