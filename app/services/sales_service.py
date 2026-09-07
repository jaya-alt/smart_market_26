from datetime import datetime, date, time, timedelta

from app.database.db import SessionLocal
from app.database.models import Bill, BillItem, Product


# ============================================================
# DAILY SALES SUMMARY
# ============================================================

def get_daily_sales_summary(target_date=None):
    """
    Generate a complete sales summary for a particular date.

    Parameters
    ----------
    target_date : date | datetime | str | None
        Supported formats:
        - None                -> today's date
        - date object
        - datetime object
        - "YYYY-MM-DD" string

    Returns
    -------
    dict
        Daily sales summary including:
        - total bills
        - total sales
        - subtotal
        - CGST
        - SGST
        - GST
        - payment breakdown
        - top-selling products
    """

    # --------------------------------------------------------
    # NORMALIZE DATE
    # --------------------------------------------------------

    try:

        if target_date is None:

            target_date = date.today()

        elif isinstance(target_date, datetime):

            target_date = target_date.date()

        elif isinstance(target_date, date):

            pass

        elif isinstance(target_date, str):

            target_date = datetime.strptime(
                target_date.strip(),
                "%Y-%m-%d"
            ).date()

        else:

            return {
                "success": False,
                "message": (
                    "Invalid date. Please use YYYY-MM-DD format."
                )
            }

    except ValueError:

        return {
            "success": False,
            "message": (
                f"Invalid date '{target_date}'. "
                "Please use YYYY-MM-DD format."
            )
        }

    # --------------------------------------------------------
    # DATE RANGE
    # --------------------------------------------------------

    start_datetime = datetime.combine(
        target_date,
        time.min
    )

    end_datetime = (
        start_datetime +
        timedelta(days=1)
    )

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # GET FINALIZED BILLS
        # ----------------------------------------------------

        bills = (
            db.query(Bill)
            .filter(
                Bill.status == "FINALIZED",
                Bill.created_at >= start_datetime,
                Bill.created_at < end_datetime
            )
            .all()
        )

        # ----------------------------------------------------
        # BASIC TOTALS
        # ----------------------------------------------------

        total_bills = len(bills)

        total_sales = sum(
            float(bill.total or 0)
            for bill in bills
        )

        total_subtotal = sum(
            float(bill.subtotal or 0)
            for bill in bills
        )

        total_cgst = sum(
            float(bill.cgst or 0)
            for bill in bills
        )

        total_sgst = sum(
            float(bill.sgst or 0)
            for bill in bills
        )

        total_gst = (
            total_cgst +
            total_sgst
        )

        # ----------------------------------------------------
        # PAYMENT BREAKDOWN
        # ----------------------------------------------------

        payment_breakdown = {
            "CASH": 0.0,
            "UPI": 0.0,
            "CARD": 0.0
        }

        for bill in bills:

            payment_mode = (
                str(bill.payment_mode).upper()
                if bill.payment_mode
                else None
            )

            if payment_mode in payment_breakdown:

                payment_breakdown[payment_mode] += float(
                    bill.total or 0
                )

        # ----------------------------------------------------
        # TOP-SELLING PRODUCTS
        # ----------------------------------------------------

        product_sales = {}

        for bill in bills:

            for item in bill.items:

                # --------------------------------------------
                # Product name
                # --------------------------------------------

                if item.product:

                    product_name = item.product.name

                else:

                    product_name = "Unknown Product"

                # --------------------------------------------
                # Create product entry
                # --------------------------------------------

                if product_name not in product_sales:

                    product_sales[product_name] = {
                        "quantity": 0.0,
                        "sales": 0.0
                    }

                # --------------------------------------------
                # Quantity
                # --------------------------------------------

                product_sales[product_name]["quantity"] += float(
                    item.quantity or 0
                )

                # --------------------------------------------
                # Sales
                # --------------------------------------------

                product_sales[product_name]["sales"] += float(
                    item.total or 0
                )

        # ----------------------------------------------------
        # CONVERT TO LIST
        # ----------------------------------------------------

        top_products = []

        for product_name, data in product_sales.items():

            top_products.append(
                {
                    "product": product_name,
                    "quantity": data["quantity"],
                    "sales": round(
                        data["sales"],
                        2
                    )
                }
            )

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        top_products.sort(
            key=lambda item: (
                item["quantity"],
                item["sales"]
            ),
            reverse=True
        )

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        return {
            "success": True,

            "date": target_date.strftime(
                "%Y-%m-%d"
            ),

            "total_bills": total_bills,

            "total_sales": round(
                total_sales,
                2
            ),

            "total_subtotal": round(
                total_subtotal,
                2
            ),

            "total_cgst": round(
                total_cgst,
                2
            ),

            "total_sgst": round(
                total_sgst,
                2
            ),

            "total_gst": round(
                total_gst,
                2
            ),

            "payment_breakdown": {
                "CASH": round(
                    payment_breakdown["CASH"],
                    2
                ),
                "UPI": round(
                    payment_breakdown["UPI"],
                    2
                ),
                "CARD": round(
                    payment_breakdown["CARD"],
                    2
                )
            },

            "top_products": top_products
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        db.close()


# ============================================================
# DAILY CLOSING REPORT
# ============================================================

def get_daily_close(target_date=None):
    """
    Generate the supermarket end-of-day closing report.

    This uses get_daily_sales_summary() and returns a
    simplified report suitable for the AI agent.
    """

    summary = get_daily_sales_summary(
        target_date
    )

    if not summary["success"]:

        return summary

    payment = summary["payment_breakdown"]

    return {
        "success": True,

        "date": summary["date"],

        "total_bills": summary["total_bills"],

        "total_sales": summary["total_sales"],

        "total_gst": summary["total_gst"],

        "cgst": summary["total_cgst"],

        "sgst": summary["total_sgst"],

        "cash_sales": payment["CASH"],

        "upi_sales": payment["UPI"],

        "card_sales": payment["CARD"],

        "top_products": summary["top_products"]
    }


# ============================================================
# REORDER SUGGESTIONS (sales-velocity based)
# ============================================================

def get_reorder_suggestions(lookback_days=14, lead_time_days=7):
    """
    Suggest how much of each product to reorder, based on recent
    sales velocity rather than just "stock <= reorder_level".

    velocity = units sold per day over the last `lookback_days`
    projected_need = velocity * lead_time_days (how much will sell
                      before a fresh order can realistically arrive)
    suggested_qty = max(0, projected_need - current_stock)

    Only products that are at/below their reorder level OR whose
    projected need exceeds current stock are returned, so the list
    stays actionable instead of listing the whole catalog.
    """

    db = SessionLocal()

    try:
        window_start = datetime.utcnow() - timedelta(days=lookback_days)

        rows = (
            db.query(BillItem)
            .join(Bill, BillItem.bill_id == Bill.id)
            .filter(
                Bill.status == "FINALIZED",
                Bill.created_at >= window_start
            )
            .all()
        )

        sold_by_product = {}

        for item in rows:
            sold_by_product[item.product_id] = (
                sold_by_product.get(item.product_id, 0) + item.quantity
            )

        products = db.query(Product).all()
        suggestions = []

        for product in products:
            total_sold = sold_by_product.get(product.id, 0)
            velocity_per_day = total_sold / lookback_days
            projected_need = velocity_per_day * lead_time_days
            suggested_qty = max(0, round(projected_need - product.quantity, 2))

            is_low = product.quantity <= product.reorder_level
            will_run_out = projected_need > product.quantity

            if is_low or will_run_out:
                suggestions.append({
                    "product": product.name,
                    "current_stock": product.quantity,
                    "reorder_level": product.reorder_level,
                    "avg_daily_sales": round(velocity_per_day, 2),
                    "suggested_reorder_qty": suggested_qty,
                    "unit": product.unit
                })

        suggestions.sort(key=lambda s: s["avg_daily_sales"], reverse=True)

        return {
            "success": True,
            "lookback_days": lookback_days,
            "lead_time_days": lead_time_days,
            "count": len(suggestions),
            "suggestions": suggestions
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        db.close()


# ============================================================
# TEST / DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("SUPERMARKET SALES SERVICE TEST")
    print("=" * 60)

    result = get_daily_sales_summary()

    print("\nDAILY SALES SUMMARY")
    print(result)

    print("\n" + "=" * 60)

    closing = get_daily_close()

    print("\nDAILY CLOSING REPORT")
    print(closing)

    print("=" * 60)