import os
import re
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    abort,
    Response,
)
from dotenv import load_dotenv
import openai

import brain

# -----------------------------
# ENV + OPENAI
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Put it in .env or Render env vars.")

openai.api_key = OPENAI_API_KEY

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

GENERATED_DIR = "generated"
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
        t = t[: -3].rstrip()
    return t


def generate_html_with_openai(prompt: str) -> str:
    """Call OpenAI to generate raw HTML (no markdown)."""
    response = openai.ChatCompletion.create(
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
        temperature=0.6,
    )
    html = response["choices"][0]["message"]["content"]
    return strip_code_fences(html)


# -----------------------------
# ROUTES
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
        )

    # Ask the brain to build the right prompt
    prompt, template_id = brain.build_prompt_for_business(
        business_name=business_name,
        industry=industry,
        city=city,
        preferred_template_id=style_choice,
    )

    # Generate HTML with OpenAI
    html_content = generate_html_with_openai(prompt)

    # Save file for preview / download
    slug = slugify(business_name)
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{slug}-{unique_id}.html"
    file_path = os.path.join(GENERATED_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    preview_url = url_for("preview_site", file_id=filename)
    download_url = url_for("download_site", file_id=filename)

    # Optionally you can log the template used here
    # brain.record_template_result(template_id, success=False)

    return render_template(
        "result.html",
        preview_url=preview_url,
        download_url=download_url,
        html_content=html_content,
    )


@app.route("/preview/<path:file_id>")
def preview_site(file_id: str):
    safe_name = os.path.basename(file_id)
    file_path = os.path.join(GENERATED_DIR, safe_name)
    if not os.path.exists(file_path):
        abort(404)

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    return Response(html, mimetype="text/html")


@app.route("/download/<path:file_id>")
def download_site(file_id: str):
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


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # For local testing
    app.run(debug=True, host="0.0.0.0", port=5000)
