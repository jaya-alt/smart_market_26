"""
Inventory tools: search, stock lookup, receiving stock, low-stock
alerts. All product matching goes through find_matching_products()
so search/stock/receive all behave consistently (exact match ->
normalized match -> word-overlap match, in that order), and always
return an unambiguous single product or a clear list of candidates
instead of silently guessing.
"""

import re

from sqlalchemy import or_

from app.database.db import SessionLocal
from app.database.models import Product, StockMovement


# ============================================================
# HELPERS
# ============================================================

def normalize_text(text):
    """
    Normalize product text for flexible searching.

    'Maggi 70 g' -> 'maggi70g'
    'MAGGI-70G'  -> 'maggi70g'
    """
    if not text:
        return ""

    return re.sub(r"[^a-zA-Z0-9]", "", str(text).lower())


def format_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "unit": product.unit,
        "quantity": product.quantity,
        "selling_price": product.selling_price,
        "mrp": product.mrp,
        "gst_rate": product.gst_rate,
        "reorder_level": product.reorder_level
    }


def find_matching_products(db, query):
    """
    Find products using flexible matching.

    Search order:
    1. Product name / SKU contains query (case-insensitive)
    2. Normalized comparison (ignores spaces/punctuation/case)
    3. Word-overlap matching, best match first
    """
    if not query or not str(query).strip():
        return []

    query = str(query).strip()

    products = (
        db.query(Product)
        .filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.sku.ilike(f"%{query}%")
            )
        )
        .all()
    )

    if products:
        return products

    normalized_query = normalize_text(query)
    all_products = db.query(Product).all()

    normalized_matches = [
        product for product in all_products
        if normalized_query in normalize_text(product.name)
        or normalized_query in normalize_text(product.sku or "")
    ]

    if normalized_matches:
        return normalized_matches

    words = [
        normalize_text(word)
        for word in query.split()
        if normalize_text(word)
    ]

    word_matches = []

    for product in all_products:
        searchable_text = (
            normalize_text(product.name) + " " + normalize_text(product.sku or "")
        )

        matched_words = sum(word in searchable_text for word in words)

        if matched_words > 0:
            word_matches.append((matched_words, product))

    if word_matches:
        word_matches.sort(key=lambda item: item[0], reverse=True)
        return [product for _, product in word_matches]

    return []


# ============================================================
# SEARCH PRODUCT
# ============================================================

def search_product(query):
    db = SessionLocal()

    try:
        products = find_matching_products(db, query)

        if not products:
            return {
                "success": False,
                "message": f"No products found matching '{query}'.",
                "products": []
            }

        return {
            "success": True,
            "count": len(products),
            "products": [format_product(p) for p in products]
        }

    except Exception as e:
        return {"success": False, "message": str(e), "products": []}

    finally:
        db.close()


# ============================================================
# GET ALL PRODUCTS
# ============================================================

def get_all_products():
    db = SessionLocal()

    try:
        products = db.query(Product).order_by(Product.name).all()

        return {
            "success": True,
            "count": len(products),
            "products": [format_product(p) for p in products]
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        db.close()


# ============================================================
# GET STOCK
# ============================================================

def get_stock(product_name):
    db = SessionLocal()

    try:
        products = find_matching_products(db, product_name)

        if not products:
            return {
                "success": False,
                "message": f"No product found matching '{product_name}'."
            }

        if len(products) == 1:
            product = products[0]

            return {
                "success": True,
                "product": product.name,
                "quantity": product.quantity,
                "unit": product.unit,
                "reorder_level": product.reorder_level
            }

        # Multiple candidates -- don't guess, ask.
        suggestions = [
            {"name": p.name, "quantity": p.quantity, "unit": p.unit}
            for p in products[:5]
        ]

        return {
            "success": False,
            "message": (
                f"Multiple products match '{product_name}'. "
                "Please specify which product you mean."
            ),
            "matches": suggestions
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        db.close()


# ============================================================
# RECEIVE STOCK
# ============================================================

def receive_stock(product_name, quantity, cost_price=None, mrp=None):
    db = SessionLocal()

    try:
        if quantity is None or quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be greater than zero."
            }

        products = find_matching_products(db, product_name)

        if not products:
            return {
                "success": False,
                "message": f"No product found matching '{product_name}'."
            }

        if len(products) > 1:
            return {
                "success": False,
                "message": (
                    f"Multiple products match '{product_name}'. "
                    "Please specify the exact product."
                ),
                "matches": [p.name for p in products[:5]]
            }

        product = products[0]

        if cost_price is not None:
            if cost_price < 0:
                return {"success": False, "message": "Cost price cannot be negative."}
            product.cost_price = cost_price

        if mrp is not None:
            if mrp < 0:
                return {"success": False, "message": "MRP cannot be negative."}
            product.mrp = mrp

        product.quantity += quantity

        db.add(StockMovement(
            product_id=product.id,
            change=quantity,
            reason="RECEIVE",
            reference=None
        ))

        db.commit()

        return {
            "success": True,
            "message": f"Received {quantity} {product.unit}(s) of {product.name}.",
            "product": product.name,
            "current_stock": product.quantity
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

    finally:
        db.close()


# ============================================================
# LOW STOCK
# ============================================================

def get_low_stock():
    db = SessionLocal()

    try:
        products = (
            db.query(Product)
            .filter(Product.quantity <= Product.reorder_level)
            .order_by(Product.quantity)
            .all()
        )

        results = [
            {
                "product": p.name,
                "quantity": p.quantity,
                "reorder_level": p.reorder_level,
                "unit": p.unit
            }
            for p in products
        ]

        return {
            "success": True,
            "count": len(results),
            "products": results
        }

    except Exception as e:
        return {"success": False, "message": str(e), "products": []}

    finally:
        db.close()
