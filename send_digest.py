"""
Sends the final curated event list as an email digest via Gmail SMTP.
"""
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def _render_html(events, config):
    if not events:
        return "<p>No toddler-friendly events found for this weekend. Check back next week!</p>"

    rows = []
    for e in events:
        rows.append(
            f"""
        <div style="margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #eee;">
          <h3 style="margin:0 0 4px 0;"><a href="{e.get('url', '#')}">{e.get('title', 'Untitled event')}</a></h3>
          <p style="margin:0 0 4px 0;color:#555;">{e.get('date', '')} {e.get('time', '')} &middot; {e.get('venue', '')}</p>
          <p style="margin:0;">{e.get('blurb', '')}</p>
        </div>
        """
        )

    return f"""
    <div style="font-family:sans-serif;max-width:600px;">
      <h2>This Weekend's Toddler-Friendly Events</h2>
      <p>Curated picks for {config['location']['city']}, {config['location']['state']}</p>
      {''.join(rows)}
    </div>
    """


def send(events, config):
    html = _render_html(events, config)
    msg = MIMEMultipart("alternative")
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = config["email"]["to"]
    msg["Subject"] = "This Weekend's Toddler-Friendly Events"
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        smtp.send_message(msg)

    print(f"Digest sent to {config['email']['to']} with {len(events)} events.")
