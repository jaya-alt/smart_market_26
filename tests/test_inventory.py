from app.tools.inventory_tools import (
    search_product,
    get_stock,
    receive_stock,
    get_low_stock
)


print("\n--- SEARCH PRODUCT ---")

result = search_product("Maggi")
print(result)


print("\n--- CHECK STOCK ---")

result = get_stock("Maggi 70g")
print(result)


print("\n--- RECEIVE STOCK ---")

result = receive_stock(
    "Maggi 70g",
    10,
    cost_price=12,
    mrp=14
)

print(result)


print("\n--- CHECK STOCK AGAIN ---")

result = get_stock("Maggi 70g")
print(result)


print("\n--- LOW STOCK ---")

result = get_low_stock()
print(result)