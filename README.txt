
WEB_AUTOMATION — Scrape Google Maps leads, export Excel, and email the report

1) Create & activate venv (Windows)
   python -m venv .venv
   .\.venv\Scripts\activate

2) Install deps
   pip install -r requirements.txt
   python -m playwright install

3) Configure email (optional but recommended)
   - Edit src\config.yaml
   - Set your Gmail and App Password (Google Account > Security > 2FA > App Passwords)
   - Keep email.enable: true

4) Run
   python -m src.cli --niche "roofing contractor" --city "Dallas" --country "USA" --rows 60 --email

Outputs:
- Excel saved to data\leads\<niche>_<city>_<country>.xlsx
- If --email, the file is sent via Gmail SMTP to the configured recipients.
