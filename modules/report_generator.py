import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER


def safe_text(value):
    if value is None:
        return "N/A"
    return str(value)


def generate_report(browser_data, usb_data, timeline_data, case_id, case_name, investigator, md5, sha256):

    # 🔥 FIXED PATH (IMPORTANT)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    report_dir = os.path.join(base_dir, "..", "reports")

    os.makedirs(report_dir, exist_ok=True)

    filename = os.path.join(
        report_dir,
        f"forensic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="CustomTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        spaceAfter=8
    )

    normal_style = styles["Normal"]

    elements = []

    generated_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    # Title
    elements.append(Paragraph("Digital Forensics Investigation Report", title_style))
    elements.append(Spacer(1, 10))

    # Case Details
    elements.append(Paragraph(f"<b>Case ID:</b> {safe_text(case_id)}", normal_style))
    elements.append(Paragraph(f"<b>Case Name:</b> {safe_text(case_name)}", normal_style))
    elements.append(Paragraph(f"<b>Investigator:</b> {safe_text(investigator)}", normal_style))
    elements.append(Paragraph(f"<b>Generated Time:</b> {generated_time}", normal_style))
    elements.append(Spacer(1, 12))

    # Hash Values
    elements.append(Paragraph("Hash Values", section_style))
    elements.append(Paragraph(f"<b>MD5:</b> {safe_text(md5)}", normal_style))
    elements.append(Paragraph(f"<b>SHA256:</b> {safe_text(sha256)}", normal_style))
    elements.append(Spacer(1, 12))

    # Browser History
    elements.append(Paragraph("Browser History", section_style))

    browser_table = [["Title", "URL", "Visit Time"]]
    for item in browser_data[:20]:
        browser_table.append([
            Paragraph(safe_text(item.get("title", "N/A")), normal_style),
            Paragraph(safe_text(item.get("url", "N/A")), normal_style),
            Paragraph(safe_text(item.get("display_time", item.get("time", "N/A"))), normal_style)
        ])

    browser_t = Table(browser_table, colWidths=[120, 250, 110], repeatRows=1)
    browser_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(browser_t)
    elements.append(Spacer(1, 12))

    # USB Devices
    elements.append(Paragraph("USB Device Analysis", section_style))

    usb_table = [["Device Name", "Friendly Name", "Checked Time"]]
    for device in usb_data[:10]:
        usb_table.append([
            Paragraph(safe_text(device.get("Device Name", "N/A")), normal_style),
            Paragraph(safe_text(device.get("Friendly Name", "N/A")), normal_style),
            Paragraph(safe_text(device.get("Checked Time", "N/A")), normal_style)
        ])

    usb_t = Table(usb_table, colWidths=[180, 220, 100], repeatRows=1)
    usb_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(usb_t)
    elements.append(Spacer(1, 12))

    # Timeline
    elements.append(Paragraph("Investigation Timeline", section_style))

    timeline_table = [["Time", "Type", "Details"]]
    for entry in timeline_data[:20]:
        timeline_table.append([
            Paragraph(safe_text(entry.get("Time", "N/A")), normal_style),
            Paragraph(safe_text(entry.get("Type", "N/A")), normal_style),
            Paragraph(safe_text(entry.get("Details", "N/A")), normal_style)
        ])

    timeline_t = Table(timeline_table, colWidths=[110, 80, 310], repeatRows=1)
    timeline_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(timeline_t)
    elements.append(Spacer(1, 12))

    # Summary
    elements.append(Paragraph("Investigation Summary", section_style))
    elements.append(Paragraph(f"Total Browser Records: {len(browser_data)}", normal_style))
    elements.append(Paragraph(f"Total USB Devices: {len(usb_data)}", normal_style))
    elements.append(Paragraph(f"Total Timeline Events: {len(timeline_data)}", normal_style))

    # 🔥 SAFE PDF BUILD
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        doc.build(elements)
    except Exception as e:
        print("PDF Error:", e)

    return filename