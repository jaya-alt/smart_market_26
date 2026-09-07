import os

from app.services.pptx_service import generate_sales_pptx


output_file = "sales_analysis.pptx"

result = generate_sales_pptx(output_file)

print("Success:", result["success"])
print("Message:", result["message"])

if result["success"]:
    print("File:", result["file"])
    print("File exists:", os.path.exists(output_file))

    if os.path.exists(output_file):
        print(
            "File size:",
            os.path.getsize(output_file),
            "bytes"
        )