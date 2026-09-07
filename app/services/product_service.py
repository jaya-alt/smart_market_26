from app.database.db import SessionLocal
from app.database.models import Product


def create_product(
    name,
    sku,
    unit,
    is_loose,
    cost_price,
    selling_price,
    mrp,
    quantity,
    reorder_level,
    hsn_code,
    gst_rate
):
    db = SessionLocal()

    try:
        # Basic validation
        if not name or not name.strip():
            return {
                "success": False,
                "message": "Product name is required."
            }

        if not sku or not sku.strip():
            return {
                "success": False,
                "message": "SKU is required."
            }

        if cost_price < 0:
            return {
                "success": False,
                "message": "Cost price cannot be negative."
            }

        if selling_price < cost_price:
            return {
                "success": False,
                "message": "Selling price cannot be below cost price."
            }

        if mrp is not None and mrp < selling_price:
            return {
                "success": False,
                "message": "MRP cannot be below selling price."
            }

        if quantity < 0:
            return {
                "success": False,
                "message": "Stock quantity cannot be negative."
            }

        if reorder_level < 0:
            return {
                "success": False,
                "message": "Reorder level cannot be negative."
            }

        if gst_rate < 0 or gst_rate > 100:
            return {
                "success": False,
                "message": "GST rate must be between 0 and 100."
            }

        # Check duplicate SKU
        existing_sku = (
            db.query(Product)
            .filter(Product.sku == sku.strip())
            .first()
        )

        if existing_sku:
            return {
                "success": False,
                "message": f"SKU '{sku}' already exists."
            }

        # Check duplicate product name
        existing_name = (
            db.query(Product)
            .filter(Product.name.ilike(name.strip()))
            .first()
        )

        if existing_name:
            return {
                "success": False,
                "message": f"Product '{name}' already exists."
            }

        # Create product
        product = Product(
            name=name.strip(),
            sku=sku.strip(),
            unit=unit.strip(),
            is_loose=is_loose,
            cost_price=cost_price,
            selling_price=selling_price,
            mrp=mrp,
            quantity=quantity,
            reorder_level=reorder_level,
            hsn_code=hsn_code,
            gst_rate=gst_rate
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "success": True,
            "message": "Product created successfully.",
            "product": {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "unit": product.unit,
                "is_loose": product.is_loose,
                "cost_price": product.cost_price,
                "selling_price": product.selling_price,
                "mrp": product.mrp,
                "quantity": product.quantity,
                "reorder_level": product.reorder_level,
                "hsn_code": product.hsn_code,
                "gst_rate": product.gst_rate
            }
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()