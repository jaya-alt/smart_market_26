from app.database.db import SessionLocal
from app.database.models import Product


products = [
    {
        "name": "Aashirvaad Atta 5kg",
        "sku": "AASH-ATTA-5KG",
        "unit": "packet",
        "is_loose": False,
        "cost_price": 240,
        "selling_price": 275,
        "mrp": 285,
        "quantity": 10,
        "reorder_level": 5,
        "hsn_code": "1101",
        "gst_rate": 5
    },
    {
        "name": "Tata Salt 1kg",
        "sku": "TATA-SALT-1KG",
        "unit": "packet",
        "is_loose": False,
        "cost_price": 22,
        "selling_price": 28,
        "mrp": 30,
        "quantity": 20,
        "reorder_level": 5,
        "hsn_code": "2501",
        "gst_rate": 5
    },
    {
        "name": "Amul Butter 100g",
        "sku": "AMUL-BUTTER-100G",
        "unit": "packet",
        "is_loose": False,
        "cost_price": 50,
        "selling_price": 60,
        "mrp": 62,
        "quantity": 15,
        "reorder_level": 5,
        "hsn_code": "0405",
        "gst_rate": 12
    },
    {
        "name": "Fortune Sunflower Oil 1L",
        "sku": "FORTUNE-OIL-1L",
        "unit": "litre",
        "is_loose": False,
        "cost_price": 120,
        "selling_price": 145,
        "mrp": 150,
        "quantity": 12,
        "reorder_level": 4,
        "hsn_code": "1512",
        "gst_rate": 5
    },
    {
        "name": "Maggi 70g",
        "sku": "MAGGI-70G",
        "unit": "packet",
        "is_loose": False,
        "cost_price": 12,
        "selling_price": 14,
        "mrp": 14,
        "quantity": 20,
        "reorder_level": 5,
        "hsn_code": "1902",
        "gst_rate": 12
    },
    {
        "name": "Parle-G",
        "sku": "PARLE-G",
        "unit": "packet",
        "is_loose": False,
        "cost_price": 8,
        "selling_price": 10,
        "mrp": 10,
        "quantity": 30,
        "reorder_level": 10,
        "hsn_code": "1905",
        "gst_rate": 18
    },
    {
        "name": "Surf Excel",
        "sku": "SURF-EXCEL",
        "unit": "packet",
        "is_loose": False,
        "cost_price": 45,
        "selling_price": 55,
        "mrp": 60,
        "quantity": 10,
        "reorder_level": 4,
        "hsn_code": "3402",
        "gst_rate": 18
    },
    {
        "name": "Loose Sugar",
        "sku": "LOOSE-SUGAR",
        "unit": "kg",
        "is_loose": True,
        "cost_price": 42,
        "selling_price": 50,
        "mrp": None,
        "quantity": 50,
        "reorder_level": 10,
        "hsn_code": "1701",
        "gst_rate": 0
    },
    {
        "name": "Loose Rice",
        "sku": "LOOSE-RICE",
        "unit": "kg",
        "is_loose": True,
        "cost_price": 55,
        "selling_price": 65,
        "mrp": None,
        "quantity": 100,
        "reorder_level": 20,
        "hsn_code": "1006",
        "gst_rate": 0
    },
    {
        "name": "Loose Toor Dal",
        "sku": "LOOSE-TOOR-DAL",
        "unit": "kg",
        "is_loose": True,
        "cost_price": 130,
        "selling_price": 150,
        "mrp": None,
        "quantity": 40,
        "reorder_level": 10,
        "hsn_code": "0713",
        "gst_rate": 0
    }
]


def seed_products():
    db = SessionLocal()

    try:
        for product_data in products:

            existing_product = (
                db.query(Product)
                .filter(
                    Product.sku == product_data["sku"]
                )
                .first()
            )

            if not existing_product:
                product = Product(**product_data)
                db.add(product)

        db.commit()

        print("Products added successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()