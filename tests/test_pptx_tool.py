from app.tools.pptx_tools import generate_sales_analysis


print("========== GENERATE SALES ANALYSIS ==========")

result = generate_sales_analysis()

print("Success:", result["success"])
print("Message:", result["message"])

if result["success"]:
    print("File:", result["file"])