import os
import csv
import smtplib
import ssl
import random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

from brain_leads import (
    choose_best_niche,
    choose_best_country,
    choose_subject,
    record_result,
)
from brain import generate_commerce_site
from app import save_multipage_site, copy_site_to_subdomain, slugify

# -----------------------------
# ENV + PATHS
# -----------------------------
load_dotenv()

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "email_templates")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

LEADS_CSV = os.path.join(DATA_DIR, "leads.csv")
LEADS_LOG = os.path.join(DATA_DIR, "leads_log.csv")
DO_NOT_CONTACT_FILE = os.path.join(DATA_DIR, "do_not_contact.txt")

PRICING_URL = os.getenv("PRICING_URL", "https://xaiwebsites.com/pricing")

# Single fallback SMTP (old style)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", SMTP_USER)

# -----------------------------
# SMTP ACCOUNTS (ROTATION)
# -----------------------------
SMTP_ACCOUNTS = []

for i in range(1, 6):
    host = os.getenv(f"SMTP_HOST_{i}")
    user = os.getenv(f"SMTP_USER_{i}")
    pwd = os.getenv(f"SMTP_PASS_{i}")
    sender = os.getenv(f"EMAIL_SENDER_{i}") or user
    port = int(os.getenv(f"SMTP_PORT_{i}", "587"))

    if host and user and pwd:
        SMTP_ACCOUNTS.append(
            {
                "host": host,
                "port": port,
                "user": user,
                "password": pwd,
                "sender": sender,
            }
        )

# If no numbered accounts, fall back to single Gmail config
if not SMTP_ACCOUNTS and SMTP_USER and SMTP_PASS:
    SMTP_ACCOUNTS.append(
        {
            "host": SMTP_HOST,
            "port": SMTP_PORT,
            "user": SMTP_USER,
            "password": SMTP_PASS,
            "sender": EMAIL_SENDER or SMTP_USER,
        }
    )

SEND_INDEX = 0


def choose_smtp_account():
    """Round-robin selection of SMTP accounts."""
    global SEND_INDEX
    if not SMTP_ACCOUNTS:
        raise RuntimeError("No SMTP accounts configured")
    acc = SMTP_ACCOUNTS[SEND_INDEX % len(SMTP_ACCOUNTS)]
    SEND_INDEX += 1
    return acc


# -------------------------------------------------
# Load do-not-contact list
# -------------------------------------------------
def load_do_not_contact():
    blocked = set()
    if not os.path.exists(DO_NOT_CONTACT_FILE):
        return blocked
    with open(DO_NOT_CONTACT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            email = line.strip().lower()
            if email:
                blocked.add(email)
    return blocked


# -------------------------------------------------
# Load already-sent emails from log
# -------------------------------------------------
def load_already_sent_emails():
    sent = set()
    if not os.path.exists(LEADS_LOG):
        return sent
    with open(LEADS_LOG, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return sent
        try:
            email_idx = header.index("email")
        except ValueError:
            # older logs may not have "email" header in that name
            # fallback: assume second column is email
            email_idx = 1
        for row in reader:
            if len(row) <= email_idx:
                continue
            email = (row[email_idx] or "").strip().lower()
            if email:
                sent.add(email)
    return sent


# -------------------------------------------------
# Load email templates & select random one
# -------------------------------------------------
def load_template():
    files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]
    if not files:
        raise Exception("❌ No email templates found in email_templates/")
    filename = random.choice(files)
    with open(os.path.join(TEMPLATES_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


# -------------------------------------------------
# Send email (with rotation)
# -------------------------------------------------
def send_email(to_email, subject, html):
    if not SMTP_ACCOUNTS:
        print("❌ No SMTP accounts available, cannot send email")
        return False

    account = choose_smtp_account()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = account["sender"]
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(account["host"], account["port"]) as server:
            server.starttls(context=context)
            server.login(account["user"], account["password"])
            server.sendmail(account["sender"], to_email, msg.as_string())

        print(f"📧 Email sent via {account['sender']} → {to_email}")
        return True

    except Exception as e:
        print(f"❌ Email send error via {account['sender']} to {to_email}: {e}")
        return False


# -------------------------------------------------
# REAL LEADS: load from CSV if present
# -------------------------------------------------
def load_leads_from_csv(max_leads=None, skip_emails=None):
    """
    Reads data/leads.csv if it exists.
    Expected header: business_name,industry,city,email
    Returns a list of dicts, skipping emails in skip_emails.
    """
    if not os.path.exists(LEADS_CSV):
        return []

    skip_emails = skip_emails or set()
    leads = []

    with open(LEADS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            business = (row.get("business_name") or "").strip()
            email = (row.get("email") or "").strip()
            if not business or not email:
                continue

            email_lower = email.lower()
            if email_lower in skip_emails:
                print(f"⏭ Skipping {email} (already sent or do-not-contact).")
                continue

            lead = {
                "business": business,
                "niche": (row.get("industry") or "").strip() or choose_best_niche(),
                "city": (row.get("city") or "").strip() or "Global",
                "country": choose_best_country(),
                "email": email,
            }
            leads.append(lead)
            if max_leads and len(leads) >= max_leads:
                break
    return leads


# -------------------------------------------------
# FALLBACK LEADS: brain-generated placeholders
# -------------------------------------------------
def generate_lead(skip_emails=None):
    skip_emails = skip_emails or set()

    # Try a few times to avoid duplicate fake emails
    for _ in range(10):
        niche = choose_best_niche()
        country = choose_best_country()

        business_names = [
            f"{country} {niche.capitalize()} Solutions",
            f"{niche.capitalize()} Experts {country}",
            f"{country} Premium {niche.capitalize()}",
            f"{niche.capitalize()} Masters {country}",
            f"{country} Elite {niche.capitalize()}",
        ]

        business_name = random.choice(business_names)
        city = "Global"
        email = f"info@{slugify(business_name)}.com"
        email_lower = email.lower()
        if email_lower not in skip_emails:
            return {
                "business": business_name,
                "niche": niche,
                "country": country,
                "city": city,
                "email": email,
            }

    # Fallback if all attempts hit skip list
    return {
        "business": "Global Demo Business",
        "niche": "general",
        "country": "Global",
        "city": "Global",
        "email": f"info-demo-{random.randint(1000,9999)}@example.com",
    }


# -------------------------------------------------
# MAIN ENGINE (V7.1 – CSV + rotation + brain + safety)
# -------------------------------------------------
def run_engine(batch_size=3):
    print("\n🚀 Starting Global AI Leads Engine (V7.1 – CSV + rotation + safety)")

    # Ensure log file initialized
    if not os.path.exists(LEADS_LOG):
        with open(LEADS_LOG, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "business",
                    "email",
                    "slug",
                    "preview",
                    "niche",
                    "country",
                    "email_status",
                    "sender",
                    "source",
                ]
            )

    # Safety: load already sent + do-not-contact
    dnc = load_do_not_contact()
    already_sent = load_already_sent_emails()
    skip_emails = dnc.union(already_sent)

    if dnc:
        print(f"🔒 Do-not-contact entries loaded: {len(dnc)}")
    if already_sent:
        print(f"📜 Emails already sent (from log): {len(already_sent)}")

    # 1) Try to load real leads from CSV, skipping blocked emails
    csv_leads = load_leads_from_csv(max_leads=batch_size, skip_emails=skip_emails)
    use_csv = len(csv_leads) > 0

    if use_csv:
        print(f"📂 Using {len(csv_leads)} lead(s) from data/leads.csv")
        leads_to_process = csv_leads
    else:
        print("ℹ️ No suitable CSV leads found, using brain-generated leads")
        leads_to_process = [generate_lead(skip_emails=skip_emails) for _ in range(batch_size)]

    for lead in leads_to_process:
        business = lead["business"]
        niche = lead["niche"]
        country = lead["country"]
        city = lead["city"]
        email = lead["email"]

        email_lower = email.lower()
        if email_lower in skip_emails:
            print(f"⏭ Skipping {email} (blocked mid-loop).")
            continue

        slug = slugify(business)

        print(f"\n=== Lead: {business} ({niche} / {country}) → {email} ===")

        # 1) Generate website with brain
        site_json = generate_commerce_site(
            business,
            niche,
            f"{niche} services in {country}",
            city,
            products=[],
        )

        # 2) Save site pages
        folder_id, zip_path, folder_path = save_multipage_site(site_json)

        # 3) Deploy to subdomain
        copy_site_to_subdomain(slug, folder_path)

        preview_url = f"https://{slug}.xaiwebsites.com"

        # 4) Pick subject from brain
        subject = choose_subject()

        # 5) Load email template
        html_template = load_template()

        # 6) Fill template
        html = (
            html_template.replace("{{BUSINESS}}", business)
            .replace("{{PREVIEW}}", preview_url)
            .replace("{{PRICING}}", PRICING_URL)
        )

        # 7) Send email (rotation)
        email_status = send_email(email, subject, html)
        sender_used = (
            SMTP_ACCOUNTS[(SEND_INDEX - 1) % len(SMTP_ACCOUNTS)]["sender"]
            if SMTP_ACCOUNTS
            else "unknown"
        )

        # 8) Log result
        with open(LEADS_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    str(datetime.now()),
                    business,
                    email,
                    slug,
                    preview_url,
                    niche,
                    country,
                    "sent" if email_status else "failed",
                    sender_used,
                    "csv" if use_csv else "brain",
                ]
            )

        # Mark as now sent (so multiple runs in same session skip)
        skip_emails.add(email_lower)

        # 9) Train the brain on the result (basic – we don't know opens yet)
        record_result(niche, country, subject, opened=False, clicked=False, converted=False)

    print("\n✔ DONE — V7.1 engine finished batch.\n")


if __name__ == "__main__":
    run_engine(batch_size=1)
