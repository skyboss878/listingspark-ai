"""
Document signing email notifications via Resend.
"""

import os
import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_document_email(
    to_email: str,
    client_name: str,
    document_title: str,
    signing_link: str,
    agent_name: str = "Your Agent",
) -> dict:
    """Send a 'please sign this document' email. Returns {"success": bool, "error": str|None}."""
    if not RESEND_API_KEY:
        return {"success": False, "error": "RESEND_API_KEY not configured"}

    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 560px; margin: 0 auto;">
        <h2 style="color: #1e293b;">Document Ready for Your Signature</h2>
        <p>Hi {client_name},</p>
        <p><strong>{agent_name}</strong> has sent you a document to review and sign:</p>
        <p style="font-size: 18px; font-weight: 600; color: #1e293b;">{document_title}</p>
        <a href="{signing_link}"
           style="display: inline-block; background: #7c3aed; color: white; padding: 12px 28px;
                  border-radius: 8px; text-decoration: none; font-weight: 600; margin: 16px 0;">
            Review &amp; Sign Document
        </a>
        <p style="color: #64748b; font-size: 14px;">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{signing_link}">{signing_link}</a>
        </p>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from": f"Real360 <{RESEND_FROM_EMAIL}>",
            "to": [to_email],
            "subject": f"Please sign: {document_title}",
            "html": html,
        })
        return {"success": True, "email_id": result.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}
