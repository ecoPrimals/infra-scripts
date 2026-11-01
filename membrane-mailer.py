#!/usr/bin/env python3
"""
membrane-mailer.py — the chipmunk's voice beyond the membrane

Sends email from inside the Klein disc to the outside world.
Reads from neutrino channel or CLI args. Wired to SMTP relay via port 587.

Usage:
  # Direct send
  python3 membrane-mailer.py --to hn@ycombinator.com --subject "..." --body "..."

  # From neutrino queue (reads neutrino-outreach.json)
  python3 membrane-mailer.py --neutrino outreach

  # Interactive setup (first time)
  python3 membrane-mailer.py --setup

scyBorg: AGPL-3.0 + ORC + CC-BY-SA-4.0
"""

import argparse
import json
import os
import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "membrane" / "mailer.json"
NEUTRINO_DIR = Path.home() / "Development" / "ecoPrimals" / "infra" / "hud" / "site" / "public" / "data"
LOG_PATH = NEUTRINO_DIR / "mailer-log.json"

SMTP_PROVIDERS = {
    "gmail": {"host": "smtp.gmail.com", "port": 587, "note": "Use App Password (not regular password). Go to: myaccount.google.com/apppasswords"},
    "porkbun": {"host": "smtp.porkbun.com", "port": 587, "note": "Use Porkbun email credentials"},
    "outlook": {"host": "smtp.office365.com", "port": 587, "note": "Use account password or app password"},
    "icloud": {"host": "smtp.mail.me.com", "port": 587, "note": "Use App-Specific Password. Go to: appleid.apple.com"},
    "custom": {"host": "", "port": 587, "note": "Provide your own SMTP server details"}
}


def setup_config():
    """Interactive first-time setup."""
    print("\n🐿️  membrane-mailer setup")
    print("=" * 40)
    print("\nAvailable SMTP providers:")
    for key, info in SMTP_PROVIDERS.items():
        print(f"  {key:10s} — {info['host'] or 'custom'} ({info['note'][:60]})")

    provider = input("\nProvider [gmail]: ").strip().lower() or "gmail"
    if provider not in SMTP_PROVIDERS:
        print(f"Unknown provider: {provider}")
        sys.exit(1)

    info = SMTP_PROVIDERS[provider]
    host = info["host"]
    port = info["port"]

    if provider == "custom":
        host = input("SMTP host: ").strip()
        port = int(input("SMTP port [587]: ").strip() or "587")

    print(f"\n{info['note']}")
    email = input("Email address: ").strip()
    password = input("Password/App Password: ").strip()
    from_name = input("From name [ecoPrimal]: ").strip() or "ecoPrimal"

    config = {
        "provider": provider,
        "host": host,
        "port": port,
        "email": email,
        "password": password,
        "from_name": from_name,
        "created": datetime.now(timezone.utc).isoformat()
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    os.chmod(CONFIG_PATH, 0o600)
    print(f"\n✅ Config saved to {CONFIG_PATH} (mode 600)")
    return config


def load_config():
    """Load SMTP config."""
    if not CONFIG_PATH.exists():
        print("No config found. Run: python3 membrane-mailer.py --setup")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def send_email(config, to, subject, body, html=None):
    """Send email via SMTP relay."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{config['from_name']} <{config['email']}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["X-Mailer"] = "membrane-mailer/1.0 (ecoPrimals)"

    msg.attach(MIMEText(body, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))

    ctx = ssl.create_default_context()

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=30) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(config["email"], config["password"])
            server.sendmail(config["email"], to, msg.as_string())

        result = {
            "status": "sent",
            "to": to,
            "subject": subject,
            "ts": datetime.now(timezone.utc).isoformat(),
            "via": config["host"]
        }
        log_send(result)
        print(f"✅ Sent to {to} via {config['host']}")
        return result

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Auth failed: {e}")
        print(f"   Check credentials. For Gmail, use App Password: myaccount.google.com/apppasswords")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Send failed: {e}")
        sys.exit(1)


def log_send(result):
    """Append to mailer log feed."""
    log = []
    if LOG_PATH.exists():
        try:
            log = json.loads(LOG_PATH.read_text()).get("sends", [])
        except Exception:
            pass

    log.append(result)

    feed = {
        "type": "membrane-mailer-log",
        "title": "Membrane Mailer — Send Log",
        "description": "The chipmunk's outbound voice. Every email that crossed the membrane.",
        "updated": datetime.now(timezone.utc).isoformat(),
        "total_sent": len(log),
        "sends": log
    }
    LOG_PATH.write_text(json.dumps(feed, indent=2))


def send_from_neutrino(config, channel):
    """Read a neutrino message and send its content as email."""
    neutrino_file = NEUTRINO_DIR / f"neutrino-{channel}.json"
    if not neutrino_file.exists():
        print(f"No neutrino message at {neutrino_file}")
        sys.exit(1)

    data = json.loads(neutrino_file.read_text())
    to = data.get("email_to", "")
    subject = data.get("email_subject", data.get("title", ""))
    body = data.get("email_body", data.get("message", json.dumps(data, indent=2)))

    if not to:
        print(f"No 'email_to' field in {neutrino_file}")
        print("Add email_to, email_subject, email_body fields to the neutrino message.")
        sys.exit(1)

    return send_email(config, to, subject, body)


def main():
    parser = argparse.ArgumentParser(description="membrane-mailer — email from inside the Klein disc")
    parser.add_argument("--setup", action="store_true", help="Interactive SMTP setup")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--subject", "-s", help="Email subject")
    parser.add_argument("--body", "-b", help="Email body (or - for stdin)")
    parser.add_argument("--body-file", help="Read body from file")
    parser.add_argument("--neutrino", help="Send from neutrino channel (e.g., 'outreach')")
    parser.add_argument("--test", action="store_true", help="Send test email to yourself")
    args = parser.parse_args()

    if args.setup:
        setup_config()
        return

    config = load_config()

    if args.neutrino:
        send_from_neutrino(config, args.neutrino)
        return

    if args.test:
        send_email(config, config["email"], "🐿️ membrane-mailer test",
                   "The chipmunk can speak beyond the membrane.\n\nThis email was sent from inside the Klein disc.")
        return

    if not args.to or not args.subject:
        parser.print_help()
        print("\n💡 First time? Run: python3 membrane-mailer.py --setup")
        sys.exit(1)

    body = args.body or ""
    if args.body == "-":
        body = sys.stdin.read()
    elif args.body_file:
        body = Path(args.body_file).read_text()

    send_email(config, args.to, args.subject, body)


if __name__ == "__main__":
    main()
