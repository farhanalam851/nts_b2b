from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

def e(x):
    return escape(str(x))


R = "Rs. "   # core PDF fonts lack the rupee glyph


def build_invoice(order):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    st = getSampleStyleSheet()
    s = []
    s.append(Paragraph(f"<b>{'TAX INVOICE' if order.payment_status == 'paid' else 'PROFORMA INVOICE (payment pending)'}</b> - {e(order.number)}", st["Title"]))
    s.append(Paragraph(f"<b>{e(settings.SELLER_LEGAL_NAME)}</b><br/>{e(settings.SELLER_ADDRESS)}<br/>GSTIN: {e(settings.SELLER_GSTIN)}", st["Normal"]))
    s.append(Spacer(1, 6))
    s.append(Paragraph(
        f"<b>Bill / Ship to:</b> {e(order.ship_name)}, {e(order.ship_phone)}<br/>"
        f"{e(order.ship_line1)} {e(order.ship_line2)}<br/>{e(order.ship_city)}, {e(order.ship_state)} - {e(order.ship_pincode)}<br/>"
        f"Email: {e(order.user.email)}<br/>Date: {order.created:%d %b %Y} | Place of supply: {e(order.ship_state)}", st["Normal"]))
    s.append(Spacer(1, 8))
    data = [["#", "Item", "HSN", "Qty", "Price", "GST%", "Amount"]]
    for i, it in enumerate(order.items.all(), 1):
        data.append([i, f"{it.name}\n{it.sku}", it.hsn_code, it.quantity, f"{it.unit_price:.2f}", f"{it.gst_rate:g}", f"{it.line_total:.2f}"])
    data.append(["", "Items total (incl. GST)", "", "", "", "", f"{order.subtotal:.2f}"])
    data.append(["", "Delivery (incl. GST)", "", "", "", "", f"{order.shipping:.2f}"])
    taxable = order.total - order.tax_total
    data.append(["", "Taxable value", "", "", "", "", f"{taxable:.2f}"])
    if order.is_intra_state:
        data.append(["", "CGST (included)", "", "", "", "", f"{order.cgst:.2f}"])
        data.append(["", "SGST (included)", "", "", "", "", f"{order.sgst:.2f}"])
    else:
        data.append(["", "IGST (included)", "", "", "", "", f"{order.igst:.2f}"])
    data.append(["", "TOTAL", "", "", "", "", f"{R}{order.total:.2f}"])
    t = Table(data, colWidths=[8 * mm, 70 * mm, 18 * mm, 14 * mm, 22 * mm, 14 * mm, 30 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    s.append(t)
    s.append(Spacer(1, 10))
    s.append(Paragraph(f"Payment: {e(order.get_payment_method_display())} - {e(order.get_payment_status_display())}. "
                       "This is a computer-generated invoice.", st["Italic"]))
    doc.build(s)
    return buf.getvalue()
