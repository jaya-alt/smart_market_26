from app.services.sales_service import (
    get_daily_sales_summary,
    get_daily_close
)


print("\n========== DAILY SALES SUMMARY ==========")

summary = get_daily_sales_summary()

print("Success:", summary["success"])
print("Date:", summary["date"])
print("Total Bills:", summary["total_bills"])
print("Total Sales:", summary["total_sales"])
print("Subtotal:", summary["total_subtotal"])
print("CGST:", summary["total_cgst"])
print("SGST:", summary["total_sgst"])
print("Total GST:", summary["total_gst"])

print("\nPayment Breakdown:")
print("Cash:", summary["payment_breakdown"]["CASH"])
print("UPI:", summary["payment_breakdown"]["UPI"])
print("Card:", summary["payment_breakdown"]["CARD"])

print("\nTop Products:")

for product in summary["top_products"]:
    print(
        product["product"],
        "-> Qty:",
        product["quantity"],
        "Sales:",
        product["sales"]
    )


print("\n========== DAILY CLOSE ==========")

close = get_daily_close()

print("Success:", close["success"])
print("Date:", close["date"])
print("Total Bills:", close["total_bills"])
print("Total Sales:", close["total_sales"])
print("Total GST:", close["total_gst"])