from app.services.billing_service import (
    create_draft_bill,
    add_item_to_bill,
    get_bill_details,
    edit_bill_item,
    remove_bill_item
)


print("\n--- CREATE BILL ---")

bill = create_draft_bill()
print(bill)


print("\n--- ADD MAGGI ---")

maggi = add_item_to_bill(
    bill_id=bill["bill_id"],
    product_name="Maggi",
    quantity=2
)

print(maggi)


print("\n--- ADD TATA SALT ---")

salt = add_item_to_bill(
    bill_id=bill["bill_id"],
    product_name="Tata Salt",
    quantity=1
)

print(salt)


print("\n--- BEFORE EDIT ---")

details = get_bill_details(bill["bill_id"])
print(details)


# Get actual item IDs from the bill
maggi_item_id = details["items"][0]["item_id"]
salt_item_id = details["items"][1]["item_id"]


print("\n--- CHANGE MAGGI 2 -> 3 ---")

result = edit_bill_item(
    bill_id=bill["bill_id"],
    item_id=maggi_item_id,
    new_quantity=3
)

print(result)


print("\n--- REMOVE TATA SALT ---")

result = remove_bill_item(
    bill_id=bill["bill_id"],
    item_id=salt_item_id
)

print(result)


print("\n--- FINAL DRAFT ---")

details = get_bill_details(bill["bill_id"])
print(details)