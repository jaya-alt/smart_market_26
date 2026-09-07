"""
Tool registry for the Supermarket Ops Agent.

TOOLS is the JSON-schema function list handed to the LLM.
execute_tool() is the single dispatch point that turns a
(tool_name, arguments) pair into an actual call against the service
layer. All business rules (oversell guard, GST math, idempotency,
khata math) live in app/services and app/tools/*_tools.py -- this
file only routes calls, it never contains business logic itself.
"""

from app.tools.inventory_tools import (
    search_product,
    get_all_products,
    get_stock,
    receive_stock,
    get_low_stock
)

from app.services.product_service import create_product

from app.services.billing_service import (
    create_draft_bill,
    add_item_to_bill,
    get_bill_details,
    edit_bill_item_by_name,
    remove_bill_item_by_name,
    finalize_bill
)

from app.services.khata_service import (
    find_or_create_customer,
    get_customer_balance,
    add_credit,
    record_payment,
    get_customer_ledger,
    get_customers_with_outstanding_balance
)

from app.services.preference_service import (
    set_preference,
    get_preference,
    get_all_preferences
)

from app.services.invoice_service import generate_gst_invoice

from app.tools.pptx_tools import generate_sales_analysis

from app.services.sales_service import (
    get_daily_close,
    get_reorder_suggestions
)


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS = [

    # ========================================================
    # INVENTORY
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "Search for products by name or keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product name or search keyword."
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_all_products",
            "description": (
                "Get and list every product available in the supermarket "
                "inventory. Use for: show/list all products, display "
                "inventory, what items are available."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "Get current stock quantity of a specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Name of the product."}
                },
                "required": ["product_name"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "receive_stock",
            "description": "Add received stock to an existing product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "cost_price": {"type": "number"},
                    "mrp": {"type": "number"}
                },
                "required": ["product_name", "quantity"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_product",
            "description": (
                "Register a brand-new product (SKU) in the inventory. "
                "Only use this when the product does not already exist -- "
                "use receive_stock for restocking an existing product."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "sku": {"type": "string"},
                    "unit": {"type": "string", "description": "e.g. packet, kg, litre, piece."},
                    "is_loose": {"type": "boolean"},
                    "cost_price": {"type": "number"},
                    "selling_price": {"type": "number"},
                    "mrp": {"type": "number"},
                    "quantity": {"type": "number", "description": "Opening stock quantity."},
                    "reorder_level": {"type": "number"},
                    "hsn_code": {"type": "string"},
                    "gst_rate": {"type": "number"}
                },
                "required": [
                    "name", "sku", "unit", "cost_price",
                    "selling_price", "quantity", "reorder_level", "gst_rate"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_low_stock",
            "description": "Get all products whose stock is at or below reorder level.",
            "parameters": {"type": "object", "properties": {}}
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_reorder_suggestions",
            "description": (
                "Get reorder quantity suggestions based on recent sales "
                "velocity, not just the reorder-level flag. Use when the "
                "owner asks what to reorder or how much to order."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },

    # ========================================================
    # BILLING
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "create_draft_bill",
            "description": "Create a new draft bill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_mode": {"type": "string", "enum": ["CASH", "UPI", "CARD"]}
                }
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "add_item_to_bill",
            "description": "Add a product to an existing draft bill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bill_id": {"type": "integer"},
                    "product_name": {"type": "string"},
                    "quantity": {"type": "number"}
                },
                "required": ["bill_id", "product_name", "quantity"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_bill_details",
            "description": "Get details of a bill, including its line items and item_id values.",
            "parameters": {
                "type": "object",
                "properties": {"bill_id": {"type": "integer"}},
                "required": ["bill_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "edit_bill_item",
            "description": "Change the quantity of a product already on a draft bill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bill_id": {"type": "integer"},
                    "product_name": {"type": "string"},
                    "quantity": {"type": "number", "description": "The new total quantity."}
                },
                "required": ["bill_id", "product_name", "quantity"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "remove_bill_item",
            "description": "Remove a product from a draft bill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bill_id": {"type": "integer"},
                    "product_name": {"type": "string"}
                },
                "required": ["bill_id", "product_name"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "finalize_bill",
            "description": "Finalize a draft bill, deduct stock, and complete the sale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bill_id": {"type": "integer"},
                    "payment_mode": {"type": "string", "enum": ["CASH", "UPI", "CARD"]}
                },
                "required": ["bill_id", "payment_mode"]
            }
        }
    },

    # ========================================================
    # KHATA
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "find_or_create_customer",
            "description": "Find an existing customer or create a new customer by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"}
                },
                "required": ["name"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_customer_balance",
            "description": "Get a customer's outstanding khata balance.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "integer"}},
                "required": ["customer_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "add_credit",
            "description": "Add a credit (amount owed) transaction to a customer's khata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "amount": {"type": "number"},
                    "reference": {"type": "string", "description": "Optional note, e.g. a bill number."}
                },
                "required": ["customer_id", "amount"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "record_payment",
            "description": "Record a customer's payment against their khata balance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"},
                    "amount": {"type": "number"},
                    "reference": {"type": "string", "description": "Optional note, e.g. payment mode."}
                },
                "required": ["customer_id", "amount"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_customer_ledger",
            "description": "Get a customer's full khata transaction history.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "integer"}},
                "required": ["customer_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_customers_with_outstanding_balance",
            "description": (
                "List every customer who currently owes money on khata, "
                "for sending payment reminders."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },

    # ========================================================
    # PREFERENCES
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "set_preference",
            "description": "Set a store-owner preference (persists across chats and restarts).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["key", "value"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_preference",
            "description": "Get a specific saved preference.",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_all_preferences",
            "description": "Get all saved preferences.",
            "parameters": {"type": "object", "properties": {}}
        }
    },

    # ========================================================
    # GST INVOICE
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "generate_gst_invoice",
            "description": "Generate a GST invoice PDF for a finalized bill.",
            "parameters": {
                "type": "object",
                "properties": {"bill_id": {"type": "integer"}},
                "required": ["bill_id"]
            }
        }
    },

    # ========================================================
    # SALES ANALYSIS
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "generate_sales_analysis",
            "description": (
                "Generate a sales analysis PowerPoint report (with charts) "
                "for today or a specified date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {"type": "string", "description": "Date in YYYY-MM-DD format. Optional."}
                }
            }
        }
    },

    # ========================================================
    # DAILY CLOSING
    # ========================================================

    {
        "type": "function",
        "function": {
            "name": "get_daily_close",
            "description": (
                "Get the daily closing report: total bills, total sales, "
                "GST, CGST, SGST, cash/UPI/card sales and top-selling products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {"type": "string", "description": "Date in YYYY-MM-DD format. Optional."}
                }
            }
        }
    }

]


# ============================================================
# TOOL EXECUTOR
# ============================================================

def execute_tool(tool_name, arguments):

    # ========================================================
    # INVENTORY
    # ========================================================

    if tool_name == "search_product":
        return search_product(arguments["query"])

    elif tool_name == "get_all_products":
        return get_all_products()

    elif tool_name == "get_stock":
        return get_stock(arguments["product_name"])

    elif tool_name == "receive_stock":
        return receive_stock(
            product_name=arguments["product_name"],
            quantity=arguments["quantity"],
            cost_price=arguments.get("cost_price"),
            mrp=arguments.get("mrp")
        )

    elif tool_name == "create_product":
        return create_product(
            name=arguments["name"],
            sku=arguments["sku"],
            unit=arguments["unit"],
            is_loose=arguments.get("is_loose", False),
            cost_price=arguments["cost_price"],
            selling_price=arguments["selling_price"],
            mrp=arguments.get("mrp"),
            quantity=arguments["quantity"],
            reorder_level=arguments["reorder_level"],
            hsn_code=arguments.get("hsn_code"),
            gst_rate=arguments["gst_rate"]
        )

    elif tool_name == "get_low_stock":
        return get_low_stock()

    elif tool_name == "get_reorder_suggestions":
        return get_reorder_suggestions()

    # ========================================================
    # BILLING
    # ========================================================

    elif tool_name == "create_draft_bill":
        return create_draft_bill(payment_mode=arguments.get("payment_mode"))

    elif tool_name == "add_item_to_bill":
        return add_item_to_bill(
            bill_id=arguments["bill_id"],
            product_name=arguments["product_name"],
            quantity=arguments["quantity"]
        )

    elif tool_name == "get_bill_details":
        return get_bill_details(arguments["bill_id"])

    elif tool_name == "edit_bill_item":
        return edit_bill_item_by_name(
            bill_id=arguments["bill_id"],
            product_name=arguments["product_name"],
            quantity=arguments["quantity"]
        )

    elif tool_name == "remove_bill_item":
        return remove_bill_item_by_name(
            bill_id=arguments["bill_id"],
            product_name=arguments["product_name"]
        )

    elif tool_name == "finalize_bill":
        return finalize_bill(
            bill_id=arguments["bill_id"],
            payment_mode=arguments.get("payment_mode")
        )

    # ========================================================
    # KHATA
    # ========================================================

    elif tool_name == "find_or_create_customer":
        return find_or_create_customer(
            name=arguments["name"],
            phone=arguments.get("phone")
        )

    elif tool_name == "get_customer_balance":
        return get_customer_balance(arguments["customer_id"])

    elif tool_name == "add_credit":
        return add_credit(
            customer_id=arguments["customer_id"],
            amount=arguments["amount"],
            reference=arguments.get("reference")
        )

    elif tool_name == "record_payment":
        return record_payment(
            customer_id=arguments["customer_id"],
            amount=arguments["amount"],
            reference=arguments.get("reference")
        )

    elif tool_name == "get_customer_ledger":
        return get_customer_ledger(arguments["customer_id"])

    elif tool_name == "get_customers_with_outstanding_balance":
        return get_customers_with_outstanding_balance()

    # ========================================================
    # PREFERENCES
    # ========================================================

    elif tool_name == "set_preference":
        return set_preference(key=arguments["key"], value=arguments["value"])

    elif tool_name == "get_preference":
        return get_preference(arguments["key"])

    elif tool_name == "get_all_preferences":
        return get_all_preferences()

    # ========================================================
    # GST INVOICE
    # ========================================================

    elif tool_name == "generate_gst_invoice":
        return generate_gst_invoice(arguments["bill_id"])

    # ========================================================
    # SALES ANALYSIS
    # ========================================================

    elif tool_name == "generate_sales_analysis":
        return generate_sales_analysis(target_date=arguments.get("target_date"))

    # ========================================================
    # DAILY CLOSE
    # ========================================================

    elif tool_name == "get_daily_close":
        return get_daily_close(arguments.get("target_date"))

    # ========================================================
    # UNKNOWN TOOL
    # ========================================================

    else:
        return {"success": False, "message": f"Unknown tool: {tool_name}"}
