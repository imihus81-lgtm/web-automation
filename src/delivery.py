
from __future__ import annotations
import smtplib, ssl, mimetypes, os, yaml
from email.message import EmailMessage
from pathlib import Path

CFG_PATH = Path(__file__).parent / "config.yaml"

def _load_cfg():
    data = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))
    return data.get("email", {})

def send_report(file_path: str|os.PathLike, extra_recipients: list[str]|None=None):
    cfg = _load_cfg()
    if not cfg.get("enable", False):
        print("[delivery] Email disabled in config.yaml")
        return False
    sender = cfg.get("sender")
    app_password = cfg.get("app_password")
    recipients = list(cfg.get("recipients") or [])
    if extra_recipients: recipients += extra_recipients
    if not sender or not app_password or not recipients:
        print("[delivery] Missing sender/app_password/recipients in config.yaml")
        return False
    subject = cfg.get("subject", "Lead Report")
    body = cfg.get("body", "Lead report attached.")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    fpath = Path(file_path)
    ctype, _ = mimetypes.guess_type(fpath.name)
    maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
    msg.add_attachment(fpath.read_bytes(), maintype=maintype, subtype=subtype, filename=fpath.name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(msg)
    print(f"[delivery] Sent {fpath.name} to: {recipients}")
    return True
