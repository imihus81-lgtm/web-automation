import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from dotenv import load_dotenv
import stripe
from brain import generate_commerce_site

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")

# =====================
# Stripe config
# =====================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")


# =============================
# HOME PAGE
# =============================
@app.route("/")
def home():
    is_pro = session.get("pro_user", False)
    return render_template("index.html", is_pro=is_pro)


# =============================
# CREATE CHECKOUT SESSION
# =============================
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": STRIPE_PRICE_PRO, "quantity": 1}],
            success_url=request.host_url.rstrip("/") + "/stripe-success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.host_url.rstrip("/") + "/pricing",
        )
        return redirect(checkout.url, code=303)
    except Exception as e:
        print("Stripe error:", e)
        return "Stripe checkout failed.", 500


# =============================
# STRIPE SUCCESS PAGE
# =============================
@app.route("/stripe-success")
def stripe_success():
    session["pro_user"] = True
    return render_template("stripe_success.html")


# =============================
# PRICING PAGE
# =============================
@app.route("/pricing")
def pricing():
    is_pro = session.get("pro_user", False)
    return render_template("pricing.html", is_pro=is_pro)


# =============================
# WEBSITE GENERATION
# =============================
@app.route("/generate", methods=["POST"])
def generate():
    is_pro = session.get("pro_user", False)

    business_name = request.form.get("business_name")
    business_category = request.form.get("business_category")
    business_description = request.form.get("business_description")
    business_address = request.form.get("business_address")
    phone = request.form.get("phone")
    email = request.form.get("email")
    color_theme = request.form.get("color_theme") or "#1d4ed8"
    ecommerce = request.form.get("ecommerce") == "yes"

    # Free plan restrictions
    if not is_pro:
        ecommerce = False  # Free users cannot generate ecommerce stores

    # Generate website using V8 Brain
    site_json = generate_commerce_site(
        business_name,
        business_category,
        business_description,
        business_address,
        phone,
        email,
        color_theme,
        "",
        ecommerce,
        products=[]
    )

    return render_template("result.html", site=site_json, is_pro=is_pro)


# =============================
# DOWNLOAD WEBSITE (Pro Only)
# =============================
@app.route("/download")
def download():
    is_pro = session.get("pro_user", False)
    if not is_pro:
        return redirect("/pricing")

    return "Download system coming in V10."


# =============================
# PUBLISH WEBSITE (Pro Only)
# =============================
@app.route("/publish")
def publish():
    is_pro = session.get("pro_user", False)
    if not is_pro:
        return redirect("/pricing")

    return "Subdomain deployment coming in V10."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
