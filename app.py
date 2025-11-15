import os
from flask import Flask, request, render_template, make_response, abort
from dotenv import load_dotenv
from openai import OpenAI
from brain import build_prompt_for_business  # <<— BRAIN INTEGRATION
import datetime

# -------------------------------------
# Initial Setup
# -------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY missing in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# -------------------------------------
# BRAIN + AI WEBSITE GENERATOR
# -------------------------------------
def generate_website_html(business_name: str, industry: str, city: str) -> str:
    """
    Brain chooses best template → OpenAI generates custom HTML website.
    """

    # Brain selects best template
    prompt, template_id = build_prompt_for_business(business_name, industry, city)

    print(f"[BRAIN] Using template: {template_id}")

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate production-ready HTML + CSS websites."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=4000,
    )

    html = response.choices[0].message.content

    return html


# -------------------------------------
# ROUTES
# -------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    # Get form inputs
    business_name = request.form.get("business_name", "").strip()
    industry = request.form.get("industry", "").strip()
    city = request.form.get("city", "").strip()

    if not business_name or not industry or not city:
        return "All fields are required", 400

    try:
        html_content = generate_website_html(business_name, industry, city)
    except Exception as e:
        return f"Error generating website: {str(e)}", 500

    # Save generated HTML
    safe_name = (
        business_name.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("\\", "-")
        .replace("&", "")
    )

    filename = f"{safe_name}-{datetime.datetime.utcnow().timestamp()}.html"
    filepath = os.path.join("generated", filename)

    os.makedirs("generated", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Show preview page
    return render_template(
        "result.html",
        iframe_content=html_content,
        download_url=f"/download/{filename}",
    )


@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join("generated", filename)
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    response = make_response(content)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# -------------------------------------
# START
# -------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
