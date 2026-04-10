"""
PDF export for doctor visit summaries using recall() from Hindsight.
"""
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER

from memory import recall_memories


def generate_visit_pdf(child: dict, health_data: dict) -> bytes:
    """Generate a doctor visit summary PDF for the given child."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    teal = colors.HexColor("#00C4A1")
    dark = colors.HexColor("#0D1117")

    title_style = ParagraphStyle("title", parent=styles["Title"], textColor=teal, fontSize=22, spaceAfter=4)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"], textColor=dark, fontSize=13, spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    caption_style = ParagraphStyle("caption", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story = []

    # Header
    story.append(Paragraph("Pēds — Doctor Visit Summary", title_style))
    story.append(Paragraph(f"Generated: {date.today().strftime('%B %d, %Y')}", caption_style))
    story.append(HRFlowable(width="100%", thickness=1, color=teal, spaceAfter=10))

    # Child info
    story.append(Paragraph("Child Information", heading_style))
    child_data = [
        ["Name", child.get("name", "—")],
        ["Date of Birth", child.get("dob", "—")],
        ["Blood Type", child.get("blood_type", "—")],
        ["Known Conditions", ", ".join(child.get("conditions", [])) or "None"],
    ]
    t = Table(child_data, colWidths=[4*cm, 12*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F8F9FA"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    # Allergies
    allergies = health_data.get("allergies", [])
    if allergies:
        story.append(Paragraph("⚠️ Known Allergies", heading_style))
        allergy_rows = [["Substance", "Severity", "EpiPen"]]
        for a in allergies:
            allergy_rows.append([
                a.get("substance", ""),
                a.get("severity", "").capitalize(),
                "Yes ⚡" if a.get("epipen") else "No",
            ])
        t2 = Table(allergy_rows, colWidths=[6*cm, 6*cm, 4*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFEBEB")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t2)

    # Vaccines
    vaccines = health_data.get("vaccines", [])
    if vaccines:
        story.append(Paragraph("💉 Vaccination Record", heading_style))
        vax_rows = [["Vaccine", "Date Given", "Status"]]
        for v in vaccines:
            vax_rows.append([
                v.get("name", ""),
                v.get("date_given") or "Not given",
                v.get("status", "").capitalize(),
            ])
        t3 = Table(vax_rows, colWidths=[8*cm, 5*cm, 4*cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t3)

    # Medications
    medications = health_data.get("medications", [])
    if medications:
        story.append(Paragraph("💊 Current Medications", heading_style))
        med_rows = [["Medication", "Dose", "Frequency"]]
        for m in medications:
            med_rows.append([m.get("name", ""), m.get("dose", ""), m.get("frequency", "")])
        t4 = Table(med_rows, colWidths=[7*cm, 4*cm, 6*cm])
        t4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t4)

    # Hindsight recall — recent illness history
    story.append(Paragraph("🧠 Recent Health Summary (AI-generated)", heading_style))
    child_id = child.get("id", "")
    recalled = recall_memories(child_id, "recent illness episodes and symptom history") if child_id else ""
    if recalled:
        story.append(Paragraph(recalled, body_style))
    else:
        story.append(Paragraph("No recent episodes on record.", body_style))

    # Disclaimer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This summary was generated by Pēds and is intended to assist in doctor consultations only. "
        "It is not a medical record and does not replace professional medical advice.",
        caption_style
    ))

    doc.build(story)
    return buffer.getvalue()
