"""
pdf_export.py - Generate PDF visit summary reports using ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime


def generate_visit_pdf(patient: dict, visit: dict, payment: dict, previous_visits: list = None) -> bytes:
    """
    Generate a PDF visit summary report.
    Returns the PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ──────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1a73e8'),
        spaceBefore=12,
        spaceAfter=6
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10

    story.append(Paragraph("🏥 AI Patient Record System", title_style))
    story.append(Paragraph("Visit Summary Report", subtitle_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a73e8')))
    story.append(Spacer(1, 0.3 * cm))

    # ── Patient Information ────────────────────────────────────────────────
    story.append(Paragraph("Patient Information", heading_style))
    patient_data = [
        ['Patient ID', str(patient.get('patient_id', 'N/A'))],
        ['Full Name', patient.get('name', 'N/A')],
        ['Age', str(patient.get('age', 'N/A'))],
        ['Phone', patient.get('phone', 'N/A') or 'N/A'],
        ['Date of Birth', patient.get('dob', 'N/A') or 'N/A'],
    ]
    patient_table = Table(patient_data, colWidths=[5 * cm, 12 * cm])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)

    # ── Visit Details ──────────────────────────────────────────────────────
    story.append(Paragraph("Visit Details", heading_style))
    visit_data = [
        ['Visit ID', str(visit.get('visit_id', 'N/A'))],
        ['Visit Date', visit.get('date', 'N/A')],
        ['Symptoms', visit.get('symptoms', 'N/A') or 'N/A'],
        ['Duration', visit.get('duration', 'N/A') or 'N/A'],
        ['Medical History', visit.get('medical_history', 'N/A') or 'N/A'],
        ['Doctor Notes', visit.get('notes', 'N/A') or 'N/A'],
    ]
    visit_table = Table(visit_data, colWidths=[5 * cm, 12 * cm])
    visit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(visit_table)

    # ── Payment Status ─────────────────────────────────────────────────────
    story.append(Paragraph("Payment Status", heading_style))
    pay_status = payment.get('status', 'N/A')
    pay_color = colors.HexColor('#34a853') if pay_status == 'Paid' else colors.HexColor('#ea4335')
    payment_data = [
        ['Payment ID', str(payment.get('payment_id', 'N/A'))],
        ['Status', pay_status],
        ['Amount', f"₹ {payment.get('amount', 0):.2f}"],
        ['Payment Date', payment.get('date', 'N/A')],
    ]
    payment_table = Table(payment_data, colWidths=[5 * cm, 12 * cm])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TEXTCOLOR', (1, 1), (1, 1), pay_color),
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(payment_table)

    # ── Previous Visits ────────────────────────────────────────────────────
    if previous_visits:
        story.append(Paragraph("Previous Visit History", heading_style))
        prev_data = [['Visit ID', 'Date', 'Symptoms', 'Duration']]
        for pv in previous_visits:
            prev_data.append([
                str(pv.get('visit_id', '')),
                pv.get('date', ''),
                (pv.get('symptoms', '') or '')[:40],
                pv.get('duration', '') or ''
            ])
        prev_table = Table(prev_data, colWidths=[2.5 * cm, 4 * cm, 8 * cm, 2.5 * cm])
        prev_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(prev_table)

    # ── Security Hash ──────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    hash_style = ParagraphStyle(
        'HashStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_LEFT
    )
    story.append(Paragraph(f"<b>Record Integrity Hash (SHA-256):</b> {visit.get('visit_hash', 'N/A')}", hash_style))
    story.append(Paragraph("This document is system-generated and protected against tampering.", hash_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
