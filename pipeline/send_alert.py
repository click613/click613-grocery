#!/usr/bin/env python3
"""Optional email alert over SMTP (the workflow runs this only when the run failed AND the SMTP secrets are set).
GitHub already emails the repo owner when a scheduled run fails; this is a second, plain email you control.

Secrets (repo Settings -> Secrets and variables -> Actions):
  SMTP_SERVER      e.g. smtp.gmail.com
  SMTP_PORT        e.g. 465 (SSL) or 587 (STARTTLS)
  SMTP_USERNAME    the mailbox that sends, e.g. admin@click613.com
  SMTP_PASSWORD    for Gmail/Google Workspace: an App Password (Google account -> Security -> App passwords), never the real password
  ALERT_EMAIL_TO   comma-separated recipients, e.g. admin@click613.com
  ALERT_EMAIL_FROM optional; defaults to SMTP_USERNAME"""
import os, sys, ssl, json, smtplib
from email.message import EmailMessage
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    srv = os.environ.get("SMTP_SERVER"); to = os.environ.get("ALERT_EMAIL_TO")
    if not srv or not to:
        print("SMTP_SERVER / ALERT_EMAIL_TO not set: no email sent (GitHub's own failed-run email still goes to the owner)"); return 0
    port = int(os.environ.get("SMTP_PORT") or 465); user = os.environ.get("SMTP_USERNAME", ""); pw = os.environ.get("SMTP_PASSWORD", "")
    frm = os.environ.get("ALERT_EMAIL_FROM") or user
    run_url = "%s/%s/actions/runs/%s" % (os.environ.get("GITHUB_SERVER_URL", "https://github.com"), os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", ""))
    try: md = open(os.path.join(ROOT, "status", "STATUS.md")).read()
    except Exception: md = "(no status report: the run stopped before it could write one)"
    try: stale = json.load(open(os.path.join(ROOT, "status", "status.json"))).get("stale_areas") or []
    except Exception: stale = []
    msg = EmailMessage()
    msg["Subject"] = "Grocery prices: daily update needs attention" + (" (" + ", ".join(stale) + " not updated for 2+ days)" if stale else "")
    msg["From"] = frm; msg["To"] = to
    msg.set_content("The daily grocery price update did not finish cleanly.\n\nRun log: " + run_url + "\n\n" + md)
    if port == 465:
        with smtplib.SMTP_SSL(srv, port, context=ssl.create_default_context(), timeout=60) as s:
            if user: s.login(user, pw)
            s.send_message(msg)
    else:
        with smtplib.SMTP(srv, port, timeout=60) as s:
            s.starttls(context=ssl.create_default_context())
            if user: s.login(user, pw)
            s.send_message(msg)
    print("alert email sent to", to); return 0

if __name__ == "__main__":
    sys.exit(main())
