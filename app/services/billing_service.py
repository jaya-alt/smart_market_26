"""
Billing service.

Business rules enforced here (not in the agent's system prompt):

- A bill is DRAFT -> FINALIZED. Only a DRAFT bill can be edited.
- Stock is only deducted at finalize time (never on add/edit), and
  the oversell guard is re-checked at add time AND again at finalize
  time, since stock can move between those two moments (another
  draft bill finalizing, a stock correction, etc).
- GST is computed per line item (taxable_amount split into CGST/SGST
  from the product's gst_rate), then summed for the bill -- this is
  the standard "line-item GST" convention used on Indian retail
  invoices, and avoids rounding drift between item totals and the
  bill total.
- Bill numbers are assigned from the row's own primary key AFTER
  insert, not from `SELECT COUNT(*)`, so concurrent bill creation
  can never collide on the same bill_number.
"""

from app.database.db import SessionLocal
from app.database.models import Bill, BillItem, Product, StockMovement
from app.tools.inventory_tools import find_matching_products


VALID_PAYMENT_MODES = ["CASH", "UPI", "CARD"]


# ============================================================
# CREATE DRAFT BILL
# ============================================================

def create_draft_bill(payment_mode=None):
    db = SessionLocal()

    try:
        if payment_mode is not None:
            payment_mode = str(payment_mode).upper()

            if payment_mode not in VALID_PAYMENT_MODES:
                return {
                    "success": False,
                    "message": "Invalid payment mode. Use CASH, UPI, or CARD."
                }

        bill = Bill(
            bill_number="PENDING",
            status="DRAFT",
            subtotal=0,
            cgst=0,
            sgst=0,
            total=0,
            payment_mode=payment_mode
        )

        db.add(bill)
        db.commit()
        db.refresh(bill)

        # Assign a collision-free bill number from the real primary
        # key now that the row exists.
        bill.bill_number = f"BILL-{bill.id:05d}"
        db.commit()

        return {
            "success": True,
            "bill_id": bill.id,
            "bill_number": bill.bill_number,
            "status": bill.status
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


# ============================================================
# ADD ITEM TO BILL
# ============================================================

def add_item_to_bill(bill_id, product_name, quantity):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {
                "success": False,
                "message": "Bill not found."
            }

        if bill.status != "DRAFT":
            return {
                "success": False,
                "message": "Items can only be added to a draft bill."
            }

        if quantity is None or quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be greater than zero."
            }

        products = find_matching_products(db, product_name)

        if not products:
            return {
                "success": False,
                "message": f"No product found for '{product_name}'."
            }

        if len(products) > 1:
            return {
                "success": False,
                "message": (
                    f"Multiple products match '{product_name}'. "
                    "Please specify which one you mean."
                ),
                "matches": [p.name for p in products[:5]]
            }

        product = products[0]

        # Oversell guard: quantity already in THIS bill for this
        # product counts too, so repeated "add 2 Maggi" calls in the
        # same draft bill can't sneak past the stock check.
        already_in_bill = sum(
            item.quantity
            for item in bill.items
            if item.product_id == product.id
        )

        if (already_in_bill + quantity) > product.quantity:
            return {
                "success": False,
                "message": (
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.quantity} {product.unit}, "
                    f"already in this bill: {already_in_bill}."
                )
            }

        taxable_amount = round(product.selling_price * quantity, 2)
        gst_amount = round(taxable_amount * (product.gst_rate / 100), 2)
        cgst = round(gst_amount / 2, 2)
        sgst = round(gst_amount / 2, 2)
        total = round(taxable_amount + cgst + sgst, 2)

        bill_item = BillItem(
            bill_id=bill.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.selling_price,
            gst_rate=product.gst_rate,
            taxable_amount=taxable_amount,
            cgst=cgst,
            sgst=sgst,
            total=total
        )

        db.add(bill_item)
        db.flush()
        db.refresh(bill)  # reload bill.items so the new row is included

        recalculate_bill(db, bill)
        db.commit()

        return {
            "success": True,
            "bill_number": bill.bill_number,
            "product": product.name,
            "quantity": quantity,
            "unit_price": product.selling_price,
            "gst_rate": product.gst_rate,
            "taxable_amount": taxable_amount,
            "cgst": cgst,
            "sgst": sgst,
            "total": total,
            "bill_total": bill.total,
            "stock_available": product.quantity
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


# ============================================================
# GET BILL DETAILS
# ============================================================

def get_bill_details(bill_id):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {
                "success": False,
                "message": "Bill not found."
            }

        items = []

        for item in bill.items:
            items.append({
                "item_id": item.id,
                "product": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "gst_rate": item.gst_rate,
                "taxable_amount": round(item.taxable_amount, 2),
                "cgst": round(item.cgst, 2),
                "sgst": round(item.sgst, 2),
                "total": round(item.total, 2)
            })

        return {
            "success": True,
            "bill_id": bill.id,
            "bill_number": bill.bill_number,
            "status": bill.status,
            "items": items,
            "subtotal": round(bill.subtotal, 2),
            "cgst": round(bill.cgst, 2),
            "sgst": round(bill.sgst, 2),
            "total": round(bill.total, 2),
            "payment_mode": bill.payment_mode
        }

    finally:
        db.close()


# ============================================================
# RECALCULATE BILL
# ============================================================

def recalculate_bill(db, bill):
    """Recalculate all bill totals from its current items."""

    subtotal = 0
    cgst = 0
    sgst = 0
    total = 0

    for item in bill.items:
        item.taxable_amount = round(item.unit_price * item.quantity, 2)
        gst_amount = round(item.taxable_amount * item.gst_rate / 100, 2)
        item.cgst = round(gst_amount / 2, 2)
        item.sgst = round(gst_amount / 2, 2)
        item.total = round(item.taxable_amount + item.cgst + item.sgst, 2)

        subtotal += item.taxable_amount
        cgst += item.cgst
        sgst += item.sgst
        total += item.total

    bill.subtotal = round(subtotal, 2)
    bill.cgst = round(cgst, 2)
    bill.sgst = round(sgst, 2)
    bill.total = round(total, 2)


# ============================================================
# EDIT BILL ITEM (by item_id -- canonical, used by API/tests)
# ============================================================

def edit_bill_item(bill_id, item_id, new_quantity):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {"success": False, "message": "Bill not found."}

        if bill.status != "DRAFT":
            return {"success": False, "message": "Only draft bills can be edited."}

        if new_quantity is None or new_quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be greater than zero."
            }

        item = (
            db.query(BillItem)
            .filter(BillItem.id == item_id, BillItem.bill_id == bill_id)
            .first()
        )

        if not item:
            return {"success": False, "message": "Bill item not found."}

        # Oversell guard: stock available to THIS edit is what's on
        # the shelf plus whatever this same line item already holds
        # (since that quantity isn't "extra" demand).
        available_for_this_item = item.product.quantity + item.quantity

        if new_quantity > available_for_this_item:
            return {
                "success": False,
                "message": (
                    f"Insufficient stock for {item.product.name}. "
                    f"Available: {available_for_this_item}."
                )
            }

        item.quantity = new_quantity

        recalculate_bill(db, bill)
        db.commit()

        return {
            "success": True,
            "message": f"Updated {item.product.name} quantity.",
            "product": item.product.name,
            "quantity": item.quantity,
            "bill_total": bill.total
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

    finally:
        db.close()


# ============================================================
# REMOVE BILL ITEM (by item_id -- canonical, used by API/tests)
# ============================================================

def remove_bill_item(bill_id, item_id):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {"success": False, "message": "Bill not found."}

        if bill.status != "DRAFT":
            return {"success": False, "message": "Only draft bills can be edited."}

        item = (
            db.query(BillItem)
            .filter(BillItem.id == item_id, BillItem.bill_id == bill_id)
            .first()
        )

        if not item:
            return {"success": False, "message": "Bill item not found."}

        product_name = item.product.name

        db.delete(item)
        db.flush()

        recalculate_bill(db, bill)
        db.commit()

        return {
            "success": True,
            "message": f"Removed {product_name} from the bill.",
            "bill_total": bill.total
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

    finally:
        db.close()


# ============================================================
# EDIT / REMOVE BY PRODUCT NAME
#
# The AI agent talks about products by name, not internal item_id.
# These thin wrappers resolve "which line item on this bill matches
# this product name" and then defer to the canonical item_id-based
# functions above, so there is exactly one place that implements the
# actual edit/remove/recalculate logic.
# ============================================================

def _find_bill_item_by_name(bill, product_name):
    query = product_name.strip().lower()

    matches = [
        item for item in bill.items
        if query in item.product.name.lower()
    ]

    return matches


def edit_bill_item_by_name(bill_id, product_name, quantity):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {"success": False, "message": "Bill not found."}

        matches = _find_bill_item_by_name(bill, product_name)

        if not matches:
            return {
                "success": False,
                "message": f"'{product_name}' is not on bill {bill.bill_number}."
            }

        if len(matches) > 1:
            return {
                "success": False,
                "message": (
                    f"Multiple items on this bill match '{product_name}'. "
                    "Please be more specific."
                ),
                "matches": [m.product.name for m in matches]
            }

        item_id = matches[0].id

    finally:
        db.close()

    return edit_bill_item(bill_id, item_id, quantity)


def remove_bill_item_by_name(bill_id, product_name):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {"success": False, "message": "Bill not found."}

        matches = _find_bill_item_by_name(bill, product_name)

        if not matches:
            return {
                "success": False,
                "message": f"'{product_name}' is not on bill {bill.bill_number}."
            }

        if len(matches) > 1:
            return {
                "success": False,
                "message": (
                    f"Multiple items on this bill match '{product_name}'. "
                    "Please be more specific."
                ),
                "matches": [m.product.name for m in matches]
            }

        item_id = matches[0].id

    finally:
        db.close()

    return remove_bill_item(bill_id, item_id)


# ============================================================
# FINALIZE BILL
# ============================================================

def finalize_bill(bill_id, payment_mode=None):
    db = SessionLocal()

    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()

        if not bill:
            return {"success": False, "message": "Bill not found."}

        if bill.status == "FINALIZED":
            return {
                "success": False,
                "message": (
                    f"Bill {bill.bill_number} has already been finalized. "
                    "Nothing was charged again."
                )
            }

        if bill.status != "DRAFT":
            return {"success": False, "message": "Only draft bills can be finalized."}

        if not bill.items:
            return {"success": False, "message": "Cannot finalize an empty bill."}

        payment_mode = payment_mode or bill.payment_mode

        if not payment_mode:
            return {
                "success": False,
                "message": (
                    "A payment mode is required to finalize a bill. "
                    "Use CASH, UPI, or CARD."
                )
            }

        payment_mode = str(payment_mode).upper()

        if payment_mode not in VALID_PAYMENT_MODES:
            return {
                "success": False,
                "message": "Invalid payment mode. Use CASH, UPI, or CARD."
            }

        # Final oversell guard, re-checked at the moment of truth
        # since time has passed since items were added.
        for item in bill.items:
            if item.quantity > item.product.quantity:
                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for {item.product.name}. "
                        f"Available: {item.product.quantity}, "
                        f"required: {item.quantity}."
                    )
                }

        for item in bill.items:
            item.product.quantity -= item.quantity

            db.add(StockMovement(
                product_id=item.product_id,
                change=-item.quantity,
                reason="SALE",
                reference=bill.bill_number
            ))

        bill.payment_mode = payment_mode
        bill.status = "FINALIZED"

        db.commit()

        return {
            "success": True,
            "message": "Bill finalized successfully.",
            "bill_id": bill.id,
            "bill_number": bill.bill_number,
            "status": bill.status,
            "payment_mode": bill.payment_mode,
            "subtotal": round(bill.subtotal, 2),
            "cgst": round(bill.cgst, 2),
            "sgst": round(bill.sgst, 2),
            "total": round(bill.total, 2)
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

    finally:
        db.close()
