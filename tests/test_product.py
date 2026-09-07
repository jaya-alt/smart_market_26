from app.services.product_service import create_product


print("\n========== CREATE PRODUCT ==========")

result = create_product(
    name="Aashirvaad Sugar 1kg",
    sku="SUGAR-1KG",
    unit="packet",
    is_loose=False,
    cost_price=40,
    selling_price=48,
    mrp=50,
    quantity=20,
    reorder_level=5,
    hsn_code="1701",
    gst_rate=5
)

print("Success:", result["success"])
print("Message:", result["message"])

if result["success"]:
    print("\nCreated Product:")

    product = result["product"]

    for key, value in product.items():
        print(f"{key}: {value}")


print("\n========== DUPLICATE SKU TEST ==========")

duplicate = create_product(
    name="Another Sugar",
    sku="SUGAR-1KG",
    unit="packet",
    is_loose=False,
    cost_price=35,
    selling_price=45,
    mrp=50,
    quantity=10,
    reorder_level=5,
    hsn_code="1701",
    gst_rate=5
)

print("Success:", duplicate["success"])
print("Message:", duplicate["message"])


print("\n========== BELOW-COST TEST ==========")

invalid = create_product(
    name="Test Product",
    sku="TEST-001",
    unit="packet",
    is_loose=False,
    cost_price=100,
    selling_price=80,
    mrp=100,
    quantity=10,
    reorder_level=5,
    hsn_code="1234",
    gst_rate=5
)

print("Success:", invalid["success"])
print("Message:", invalid["message"])