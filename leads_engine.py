import os
import csv
import smtplib
import ssl
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from brain import generate_commerce_site
from app import save_multipage_site, copy_site_to_subdomain, slugify

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", SMTP_USER)

PRICING_URL = os.getenv("PRICING_URL", "https://xaiwebsites.com/pricing")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LEADS_FILE = os.path.join(DATA_DIR, "leads.csv")
LOG_FILE = os.path.join(DATA_DIR, "leads_log.csv")

os.makedirs(DATA_DIR, exist_ok=True)


# -------------------------------------------------
# EMAIL SENDER
# -------------------------------------------------
def send_email(to_email, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        print(f"📧 Email sent → {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email send error to {to_email}: {e}")
        return False


# -------------------------------------------------
# EMAIL TEMPLATE
# -------------------------------------------------
def build_email(business_name, preview_url):
    return f"""
    <div style='font-family:Arial;padding:20px'>
        <h2>We built a new website for {business_name}</h2>
        <p>Your business now has a fully generated modern website.</p>

        <p><b>Live preview:</b><br>
        <a href='{preview_url}'>{preview_url}</a></p>

        <p>To own this website and publish it on your domain:</p>

        <a href='{PRICING_URL}'
           style='display:inline-block;padding:10px 20px;
                  background:#2563eb;color:white;border-radius:6px;
                  text-decoration:none;font-weight:bold'>
            Activate My Website
        </a>

        <p style='margin-top:30px;font-size:13px;color:#555'>
            Powered by XAI Websites — AI-built websites for businesses.
        </p>
    </div>
    """


# -------------------------------------------------
# MAIN LEADS ENGINE
# -------------------------------------------------
def process_leads():
    if not os.path.exists(LEADS_FILE):
        print("❌ leads.csv not found")
        return

    with open(LEADS_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Create log if not exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["business", "email", "slug", "preview", "status"])

    for row in rows:
        business = row.get("business_name", "").strip()
        category = row.get("industry", "").strip()
        city = row.get("city", "").strip()
        email = row.get("email", "").strip()

        if not (business and email):
            continue

        slug = slugify(business)

        print(f"\n=== Processing lead: {business} → {email} ===")

        # 1) Generate site JSON with brain
        site_json = generate_commerce_site(
            business, category, f"{category} services in {city}", city, products=[]
        )

        # 2) Save pages to /generated
        folder_id, zip_path, folder_path = save_multipage_site(site_json)

        # 3) Deploy to subdomain
        copy_site_to_subdomain(slug, folder_path)

        preview_url = f"https://{slug}.xaiwebsites.com"

        # 4) Send email
        subject = f"Your new website is ready — {business}"
        html = build_email(business, preview_url)
        status = "sent" if send_email(email, subject, html) else "failed"

        # 5) Log
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([business, email, slug, preview_url, status])


if __name__ == "__main__":
    print("🚀 Running XAI Websites – Lead Engine...")
    process_leads()
    print("✔ Done.")
