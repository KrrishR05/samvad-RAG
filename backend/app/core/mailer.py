"""
SAMVAD Mailer & Transactional Notification Service

Dispatches emails using standard library smtplib + email.mime.
Gracefully logs and queues delivery when SMTP settings are not configured in backend/.env.
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("core.mailer")


def send_waitlist_confirmation_email(
    to_email: str,
    name: Optional[str] = None,
    position: int = 1,
) -> bool:
    """
    Dispatch a branded confirmation email to a user who joined the SAMVAD Pro waitlist.

    Returns True if the email was successfully sent over SMTP, or False if SMTP
    is not configured or delivery encountered a transient network issue.
    """
    settings = get_settings()
    recipient_name = name.strip() if name and name.strip() else "Researcher"

    subject = f"You're on the SAMVAD Pro Early Access Waitlist ✦ (#{position})"

    # Plain text version
    text_content = f"""Hello {recipient_name},

Thank you for requesting early access to SAMVAD Pro!

You have been successfully added to our priority waitlist at position #{position}.

Here is what you will unlock when SAMVAD Pro goes live:
• Unlimited knowledge base document indexing (PDF, DOCX, TXT)
• Priority Indic voice synthesis (Sarvam Bulbul v3 across 10+ languages)
• Deep multi-pass intensity reranking & reasoning
• Custom domain embeddings & SVD models
• Multi-turn research workspaces & full evidence export

We will email you at {to_email} the moment your early access tier is ready.

Until then, you have full access to SAMVAD Free with 1,500 daily requests:
http://localhost:3000

Warm regards,
The SAMVAD Research Team
https://samvad.ai
"""

    # HTML version with high-class typography & branding
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0c100e;
      color: #e4e9e6;
      margin: 0;
      padding: 32px 16px;
    }}
    .container {{
      max-width: 540px;
      margin: 0 auto;
      background-color: #121815;
      border: 1px solid #1f2a24;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .header {{
      background: linear-gradient(135deg, #1b2621 0%, #171d2b 100%);
      padding: 28px 24px;
      border-bottom: 1px solid #23312a;
      text-align: center;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      background-color: rgba(139, 92, 246, 0.15);
      border: 1px solid rgba(139, 92, 246, 0.4);
      color: #c4b5fd;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .title {{
      font-size: 22px;
      font-weight: 700;
      color: #ffffff;
      margin: 0;
    }}
    .content {{
      padding: 28px 24px;
      font-size: 14px;
      line-height: 1.6;
      color: #cbd5d1;
    }}
    .position-box {{
      background-color: #161e1a;
      border: 1px solid #28372f;
      border-radius: 12px;
      padding: 16px;
      margin: 20px 0;
      text-align: center;
    }}
    .position-num {{
      font-size: 28px;
      font-weight: 800;
      color: #a78bfa;
      font-family: monospace;
    }}
    .feature-list {{
      list-style: none;
      padding: 0;
      margin: 16px 0;
    }}
    .feature-list li {{
      padding: 8px 0;
      border-bottom: 1px solid #1d2621;
      font-size: 13px;
    }}
    .feature-list li:last-child {{
      border-bottom: none;
    }}
    .cta-button {{
      display: block;
      width: fit-content;
      margin: 24px auto 0;
      padding: 12px 24px;
      background-color: #8b5cf6;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 10px;
      font-weight: 600;
      font-size: 13px;
    }}
    .footer {{
      padding: 20px 24px;
      background-color: #0e1310;
      border-top: 1px solid #1a231e;
      text-align: center;
      font-size: 11px;
      color: #7d8f86;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">Early Access Waitlist</div>
      <h1 class="title">SAMVAD Pro ✦</h1>
    </div>
    <div class="content">
      <p>Hello <strong>{recipient_name}</strong>,</p>
      <p>Thank you for your interest in SAMVAD Pro. Your request for early access has been recorded!</p>
      
      <div class="position-box">
        <div style="font-size: 12px; color: #9bb0a5; margin-bottom: 4px;">YOUR PRIORITY WAITLIST POSITION</div>
        <div class="position-num">#{position}</div>
      </div>

      <p style="font-weight: 600; color: #ffffff;">Upcoming Pro Features in Active Development:</p>
      <ul class="feature-list">
        <li>✦ <strong>Unlimited Knowledge Base:</strong> High-scale PDF, DOCX, and TXT parsing without caps.</li>
        <li>✦ <strong>Priority Indic Voice:</strong> Instant Sarvam Bulbul v3 TTS across 10+ languages.</li>
        <li>✦ <strong>Deep Multi-Pass Reranking:</strong> Extended reasoning for complex document queries.</li>
        <li>✦ <strong>Custom Embedding Models:</strong> Domain-specific fine-tuned vector representations.</li>
        <li>✦ <strong>Multi-Turn Workspaces:</strong> Save and export full evidence audit trails.</li>
      </ul>

      <p>We will email <strong>{to_email}</strong> the moment your early-access seat opens.</p>

      <a href="http://localhost:3000" class="cta-button">Open Research Workspace</a>
    </div>
    <div class="footer">
      SAMVAD | संवाद — Intelligence Through Evidence<br>
      Voice-First Multilingual Retrieval-Augmented Generation Platform
    </div>
  </div>
</body>
</html>"""

    # Check if SMTP is configured
    if not settings.smtp_host or not settings.smtp_user:
        logger.info(
            "Waitlist entry confirmed for %s at position #%d. "
            "(SMTP credentials not configured in backend/.env — email delivery logged)",
            to_email,
            position,
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12)
            if settings.smtp_use_tls:
                server.starttls()

        if settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)

        server.send_message(msg)
        server.quit()
        logger.info("Successfully dispatched waitlist confirmation email to %s", to_email)
        return True
    except Exception as exc:
        logger.warning("Failed to send waitlist confirmation email to %s: %s", to_email, exc)
        return False

