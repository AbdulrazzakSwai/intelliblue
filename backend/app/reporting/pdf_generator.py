"""
PDF report generation using ReportLab.
"""
import io
from datetime import datetime, timezone
from typing import Optional, List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

SEVERITY_COLORS = {
    "CRITICAL": colors.HexColor("#dc2626"),
    "HIGH": colors.HexColor("#ea580c"),
    "MEDIUM": colors.HexColor("#d97706"),
    "LOW": colors.HexColor("#16a34a"),
}


def generate_incident_pdf(incident, events, notes, ai_summary) -> bytes:
    """Generate a PDF report for an incident."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor("#1e3a8a"),
    )
    story.append(Paragraph("IntelliBlue SOC — Incident Report", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a8a")))
    story.append(Spacer(1, 0.15 * inch))

    # Incident header
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
    body_style = styles["BodyText"]
    body_style.spaceAfter = 4

    story.append(Paragraph(f"Incident: {incident.title}", heading_style))

    sev_color = SEVERITY_COLORS.get(incident.severity, colors.black)
    data = [
        ["ID", str(incident.id)],
        ["Severity", incident.severity],
        ["Status", incident.status],
        ["Type", incident.incident_type or "—"],
        ["Confidence", f"{incident.confidence}%"],
        ["Rule", incident.rule_id or "—"],
        ["Created", incident.created_at.strftime("%Y-%m-%d %H:%M UTC") if incident.created_at else "—"],
    ]
    t = Table(data, colWidths=[1.5 * inch, 5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#334155")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.1 * inch))

    # Rule explanation
    if incident.rule_explanation:
        story.append(Paragraph("Rule Explanation", heading_style))
        story.append(Paragraph(incident.rule_explanation, body_style))
        story.append(Spacer(1, 0.1 * inch))

    # AI Summary
    if ai_summary:
        story.append(Paragraph("AI-Generated Summary", heading_style))
        if ai_summary.narrative:
            story.append(Paragraph(ai_summary.narrative, body_style))
        sj = ai_summary.summary_json or {}
        for field_name in ["what_happened", "why_it_matters", "likely_technique", "recommended_next_steps"]:
            val = sj.get(field_name)
            if val:
                story.append(Paragraph(f"<b>{field_name.replace('_', ' ').title()}:</b> {val}", body_style))
        story.append(Spacer(1, 0.1 * inch))

    # Evidence timeline
    if events:
        story.append(Paragraph("Evidence Timeline", heading_style))
        ev_data = [["Time", "Source", "Type", "Src IP", "User", "Message"]]
        for ev in sorted(events, key=lambda e: (e.event_time or datetime.min.replace(tzinfo=timezone.utc))):
            ev_data.append([
                ev.event_time.strftime("%H:%M:%S") if ev.event_time else "—",
                ev.source_type or "—",
                ev.event_type or "—",
                ev.src_ip or "—",
                ev.username or "—",
                (ev.message or ev.signature or "")[:60],
            ])
        ev_table = Table(ev_data, colWidths=[0.8*inch, 0.9*inch, 1*inch, 1.2*inch, 1*inch, 2.1*inch])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(ev_table)
        story.append(Spacer(1, 0.1 * inch))

    # Notes
    if notes:
        story.append(Paragraph("Analyst Notes", heading_style))
        for note in notes:
            ts = note.created_at.strftime("%Y-%m-%d %H:%M UTC") if note.created_at else ""
            story.append(Paragraph(f"<b>[{note.note_type}] {ts}:</b>", body_style))
            story.append(Paragraph(note.content, body_style))
        story.append(Spacer(1, 0.1 * inch))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8")))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748b"))
    story.append(Paragraph(
        f"Generated by IntelliBlue SOC | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | Offline System",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
