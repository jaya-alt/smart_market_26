from app.services.billing_service import (
    create_draft_bill,
    add_item_to_bill,
    finalize_bill
)

from app.database.db import SessionLocal
from app.database.models import Product


print("\n--- CHECK CURRENT STOCK ---")

db = SessionLocal()

product = (
    db.query(Product)
    .filter(Product.name.ilike("%Maggi%"))
    .first()
)

print("Maggi stock:", product.quantity)

db.close()


print("\n--- CREATE BILL ---")

bill = create_draft_bill()
print(bill)


print("\n--- TRY TO BUY 100 MAGGI ---")

result = add_item_to_bill(
    bill_id=bill["bill_id"],
    product_name="Maggi",
    quantity=100
)

print(result)


print("\n--- CHECK STOCK AFTER FAILED SALE ---")

db = SessionLocal()

product = (
    db.query(Product)
    .filter(Product.name.ilike("%Maggi%"))
    .first()
)

print("Maggi stock:", product.quantity)

db.close()