from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime


def generate_report(browser_data, usb_data, timeline_data,
                    case_id, case_name, investigator, md5, sha256):

    filename = "forensic_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"

    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("Digital Forensics Investigation Report", styles['Title']))
    elements.append(Spacer(1,20))

    # Case Information
    elements.append(Paragraph(f"<b>Case ID :</b> {case_id}", styles['Normal']))
    elements.append(Paragraph(f"<b>Case Name :</b> {case_name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Investigator :</b> {investigator}", styles['Normal']))
    elements.append(Spacer(1,20))

    # Hash values
    elements.append(Paragraph(f"<b>MD5 Hash :</b> {md5}", styles['Normal']))
    elements.append(Paragraph(f"<b>SHA256 Hash :</b> {sha256}", styles['Normal']))
    elements.append(Spacer(1,20))


    # =========================
    # Browser History Section
    # =========================

    elements.append(Paragraph("Browser History", styles['Heading2']))
    elements.append(Spacer(1,10))

    browser_table = [["URL", "Visit Time"]]

    for row in browser_data:

        url = Paragraph(str(row.get("url","N/A")), styles['Normal'])
        visit = Paragraph(str(row.get("visit_time","N/A")), styles['Normal'])

        browser_table.append([url, visit])

    browser_table_style = Table(browser_table, colWidths=[350,150])

    browser_table_style.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))

    elements.append(browser_table_style)
    elements.append(Spacer(1,20))


    # =========================
    # USB Devices Section
    # =========================

    elements.append(Paragraph("USB Devices", styles['Heading2']))
    elements.append(Spacer(1,10))

    usb_table = [["Device Name", "Checked Time"]]

    for row in usb_data:

        device = Paragraph(str(row.get("Device Name","N/A")), styles['Normal'])
        time = Paragraph(str(row.get("Checked Time","N/A")), styles['Normal'])

        usb_table.append([device, time])

    usb_table_style = Table(usb_table, colWidths=[350,150])

    usb_table_style.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))

    elements.append(usb_table_style)
    elements.append(Spacer(1,20))


    # =========================
    # Timeline Section
    # =========================

    elements.append(Paragraph("File Timeline", styles['Heading2']))
    elements.append(Spacer(1,10))

    timeline_table = [["File", "Created", "Modified"]]

    for row in timeline_data:

        file = Paragraph(str(row.get("file","N/A")), styles['Normal'])
        created = Paragraph(str(row.get("created","N/A")), styles['Normal'])
        modified = Paragraph(str(row.get("modified","N/A")), styles['Normal'])

        timeline_table.append([file, created, modified])

    timeline_table_style = Table(timeline_table, colWidths=[200,150,150])

    timeline_table_style.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))

    elements.append(timeline_table_style)


    pdf = SimpleDocTemplate(filename, pagesize=A4)

    pdf.build(elements)

    return filename