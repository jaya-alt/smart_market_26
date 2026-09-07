from app.services.billing_service import (
    create_draft_bill,
    add_item_to_bill,
    get_bill_details,
    finalize_bill
)

from app.database.db import SessionLocal
from app.database.models import Product


print("\n--- CREATE BILL ---")

bill = create_draft_bill()

print(bill)


print("\n--- ADD MAGGI ---")

item = add_item_to_bill(
    bill_id=bill["bill_id"],
    product_name="Maggi",
    quantity=2
)

print(item)


print("\n--- STOCK BEFORE FINALIZE ---")

db = SessionLocal()

product = (
    db.query(Product)
    .filter(Product.name.ilike("%Maggi%"))
    .first()
)

print("Maggi stock:", product.quantity)

db.close()


print("\n--- FINALIZE BILL ---")

result = finalize_bill(
    bill_id=bill["bill_id"],
    payment_mode="UPI"
)

print(result)


print("\n--- STOCK AFTER FINALIZE ---")

db = SessionLocal()

product = (
    db.query(Product)
    .filter(Product.name.ilike("%Maggi%"))
    .first()
)

print("Maggi stock:", product.quantity)

db.close()


print("\n--- TRY FINALIZE AGAIN ---")

result = finalize_bill(
    bill_id=bill["bill_id"],
    payment_mode="UPI"
)

print(result)