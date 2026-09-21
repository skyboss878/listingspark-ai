"""
Signed document PDF generation via reportlab.
"""

import base64
import io
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT


def generate_signed_pdf(document: Dict[str, Any]) -> bytes:
    """Build a PDF of a signed document, embedding the signature image and audit info."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    body_style = ParagraphStyle("DocBody", parent=styles["Normal"], fontSize=11, leading=16, alignment=TA_LEFT)
    meta_style = ParagraphStyle("DocMeta", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    elements = []
    elements.append(Paragraph(document.get("title", "Document"), title_style))
    elements.append(Spacer(1, 12))

    content = document.get("content") or ""
    for para in content.split("\n\n"):
        safe_para = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        elements.append(Paragraph(safe_para, body_style))
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 24))

    signature_data = document.get("signature_data")
    if signature_data:
        try:
            if "," in signature_data:
                signature_data = signature_data.split(",", 1)[1]
            sig_bytes = base64.b64decode(signature_data)
            sig_image = RLImage(io.BytesIO(sig_bytes), width=2.5 * inch, height=1 * inch)
            elements.append(Paragraph("Signature:", styles["Heading3"]))
            elements.append(sig_image)
        except Exception:
            elements.append(Paragraph("Signature: [on file]", body_style))

    elements.append(Spacer(1, 12))

    audit_rows = [
        ["Signed At", str(document.get("signed_at") or "")],
        ["Signed IP", str(document.get("signed_ip") or "")],
        ["Document ID", str(document.get("id") or "")],
        ["Status", str(document.get("status") or "")],
    ]
    audit_table = Table(audit_rows, colWidths=[1.5 * inch, 4 * inch])
    audit_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(audit_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
