from app.services.khata_service import (
    find_or_create_customer,
    add_credit,
    get_customer_balance,
    record_payment,
    get_customer_ledger
)


print("\n--- CREATE CUSTOMER ---")

customer = find_or_create_customer(
    name="Arun",
    phone="9876543210"
)

print(customer)


customer_id = customer["customer_id"]


print("\n--- ADD CREDIT ₹500 ---")

result = add_credit(
    customer_id=customer_id,
    amount=500,
    reference="Bill BILL-00007"
)

print(result)


print("\n--- CHECK BALANCE ---")

result = get_customer_balance(customer_id)

print(result)


print("\n--- RECORD PAYMENT ₹200 ---")

result = record_payment(
    customer_id=customer_id,
    amount=200,
    reference="UPI"
)

print(result)


print("\n--- CHECK BALANCE AGAIN ---")

result = get_customer_balance(customer_id)

print(result)


print("\n--- CUSTOMER LEDGER ---")

result = get_customer_ledger(customer_id)

print(result)