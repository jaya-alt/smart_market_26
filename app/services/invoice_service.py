"""
GST invoice PDF generation. A PDF can only be produced for a
FINALIZED bill (a draft has no legal standing as an invoice), and
every invoice is written into app/config.INVOICE_DIR so it is
reachable through the /download API and can be sent back to the
owner as a Telegram document.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from app.config import (
    INVOICE_DIR,
    STORE_NAME,
    STORE_ADDRESS,
    STORE_GSTIN,
    STORE_PHONE
)
from app.database.db import SessionLocal
from app.database.models import Bill


def generate_gst_invoice(bill_id, output_path=None):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {"success": False, "message": f"Bill {bill_id} not found."}

        if bill.status != "FINALIZED":
            return {
                "success": False,
                "message": "GST invoice can only be generated for a finalized bill."
            }

        if output_path is None:
            output_path = str(INVOICE_DIR / f"{bill.bill_number}_invoice.pdf")
        else:
            # Callers may pass just a filename; keep invoices together.
            candidate = Path(output_path)
            if not candidate.is_absolute() and candidate.parent == Path("."):
                output_path = str(INVOICE_DIR / candidate.name)

        document = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        styles = getSampleStyleSheet()
        story = []

        # -----------------------------------------
        # Store Header
        # -----------------------------------------

        story.append(Paragraph(f"<b>{STORE_NAME}</b>", styles["Title"]))

        header_bits = [b for b in (STORE_ADDRESS, STORE_PHONE) if b]
        if header_bits:
            story.append(Paragraph(" | ".join(header_bits), styles["Normal"]))

        if STORE_GSTIN:
            story.append(Paragraph(f"GSTIN: {STORE_GSTIN}", styles["Normal"]))

        story.append(Paragraph("GST TAX INVOICE", styles["Heading2"]))
        story.append(Spacer(1, 8))

        # -----------------------------------------
        # Bill Information
        # -----------------------------------------

        bill_info = [
            ["Bill Number", bill.bill_number],
            ["Date", bill.created_at.strftime("%d-%m-%Y %H:%M")],
            ["Payment Mode", bill.payment_mode or "-"],
            ["Status", bill.status]
        ]

        info_table = Table(bill_info, colWidths=[45 * mm, 100 * mm])
        info_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ]))

        story.append(info_table)
        story.append(Spacer(1, 12))

        # -----------------------------------------
        # Item Table
        # -----------------------------------------

        data = [["Product", "Qty", "Price", "HSN", "GST %", "Taxable", "CGST", "SGST", "Total"]]

        for item in bill.items:
            product = item.product

            data.append([
                product.name,
                str(item.quantity),
                f"Rs.{item.unit_price:.2f}",
                product.hsn_code or "-",
                f"{item.gst_rate:.0f}%",
                f"Rs.{item.taxable_amount:.2f}",
                f"Rs.{item.cgst:.2f}",
                f"Rs.{item.sgst:.2f}",
                f"Rs.{item.total:.2f}"
            ])

        item_table = Table(
            data,
            repeatRows=1,
            colWidths=[32 * mm, 10 * mm, 18 * mm, 15 * mm, 14 * mm, 20 * mm, 18 * mm, 18 * mm, 20 * mm]
        )

        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 4)
        ]))

        story.append(item_table)
        story.append(Spacer(1, 15))

        # -----------------------------------------
        # GST Summary
        # -----------------------------------------

        gst_data = [
            ["Taxable Amount", f"Rs.{bill.subtotal:.2f}"],
            ["CGST", f"Rs.{bill.cgst:.2f}"],
            ["SGST", f"Rs.{bill.sgst:.2f}"],
            ["Total GST", f"Rs.{bill.cgst + bill.sgst:.2f}"],
            ["Grand Total", f"Rs.{bill.total:.2f}"]
        ]

        gst_table = Table(gst_data, colWidths=[55 * mm, 40 * mm], hAlign="RIGHT")
        gst_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ]))

        story.append(gst_table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Thank you for shopping with us!</b>", styles["Normal"]))

        document.build(story)

        return {
            "success": True,
            "message": "GST invoice generated successfully.",
            "file": output_path,
            "bill_number": bill.bill_number,
            "total": bill.total
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        db.close()
