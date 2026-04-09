from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime


def generate_report(
    browser_data,
    usb_data,
    timeline_data,
    case_id,
    case_name,
    investigator,
    md5,
    sha256
):

    filename = "forensic_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"

    pdf = SimpleDocTemplate(filename, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # =========================
    # Title
    # =========================
    elements.append(
        Paragraph("Digital Forensics Investigation Report", styles["Title"])
    )
    elements.append(Spacer(1, 20))

    # =========================
    # Case Information
    # =========================
    elements.append(
        Paragraph(f"<b>Case ID:</b> {case_id}", styles["Normal"])
    )
    elements.append(
        Paragraph(f"<b>Case Name:</b> {case_name}", styles["Normal"])
    )
    elements.append(
        Paragraph(f"<b>Investigator:</b> {investigator}", styles["Normal"])
    )
    elements.append(
        Paragraph(
            f"<b>Generated Time:</b> {datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')}",
            styles["Normal"]
        )
    )
    elements.append(Spacer(1, 20))

    # =========================
    # Hash Values
    # =========================
    elements.append(Paragraph("Hash Values", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(f"<b>MD5:</b> {md5}", styles["Normal"])
    )
    elements.append(
        Paragraph(f"<b>SHA256:</b> {sha256}", styles["Normal"])
    )
    elements.append(Spacer(1, 20))

    # =========================
    # Browser History Section
    # =========================
    elements.append(Paragraph("Browser History", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    browser_table_data = [["Title", "URL", "Visit Time"]]

    if len(browser_data) == 0:
        browser_table_data.append(["No Data", "No Data", "No Data"])
    else:
        for row in browser_data:
            browser_table_data.append([
                str(row.get("title", "N/A"))[:40],
                str(row.get("url", "N/A"))[:70],
                str(row.get("time", "N/A"))
            ])

    browser_table = Table(browser_table_data, colWidths=[140, 240, 120])

    browser_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(browser_table)
    elements.append(Spacer(1, 20))

    # =========================
    # USB Devices Section
    # =========================
    elements.append(Paragraph("USB Device Analysis", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    usb_table_data = [["Device Name", "Checked Time"]]

    if len(usb_data) == 0:
        usb_table_data.append(["No USB Device Found", "N/A"])
    else:
        for row in usb_data:
            usb_table_data.append([
                str(row.get("Device Name", "Unknown")),
                str(row.get("Checked Time", "Unknown"))
            ])

    usb_table = Table(usb_table_data, colWidths=[250, 220])

    usb_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(usb_table)
    elements.append(Spacer(1, 20))

    # =========================
    # Timeline Section
    # =========================
    elements.append(PageBreak())
    elements.append(Paragraph("Investigation Timeline", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    timeline_table_data = [["Time", "Type", "Details"]]

    if len(timeline_data) == 0:
        timeline_table_data.append(["N/A", "N/A", "No Timeline Data"])
    else:
        for row in timeline_data:
            timeline_table_data.append([
                str(row.get("Time", "N/A")),
                str(row.get("Type", "N/A")),
                str(row.get("Details", "N/A"))[:70]
            ])

    timeline_table = Table(timeline_table_data, colWidths=[140, 90, 240])

    timeline_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(timeline_table)
    elements.append(Spacer(1, 20))

    # =========================
    # Footer / Summary
    # =========================
    elements.append(Paragraph("Investigation Summary", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    summary = f"""
    Total Browser Records: {len(browser_data)}<br/>
    Total USB Devices: {len(usb_data)}<br/>
    Total Timeline Events: {len(timeline_data)}<br/><br/>

    This report was automatically generated by the Digital Forensics Tool.
    """

    elements.append(Paragraph(summary, styles["Normal"]))

    pdf.build(elements)

    return filename