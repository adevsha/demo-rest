from datetime import datetime, timezone

from app.data import store
from app.models.order import OrderCreate


def _enrich_order(order: dict) -> dict:
    """Resolve user and product details for an order."""
    user = store.users.get(order["user_id"], {})
    items = []
    for item in order["items"]:
        product = store.products.get(item["product_id"], {})
        items.append({
            "product_id": item["product_id"],
            "product_name": product.get("name", "Unknown"),
            "quantity": item["quantity"],
            "price": product.get("price", 0.0),
        })
    return {
        **order,
        "user_name": user.get("name", "Unknown"),
        "items": items,
    }


def list_orders() -> list[dict]:
    return [_enrich_order(o) for o in store.orders.values()]


def get_order(order_id: int) -> dict | None:
    order = store.orders.get(order_id)
    if order is None:
        return None
    return _enrich_order(order)


def create_order(user_id: int, data: OrderCreate) -> dict:
    total = 0.0
    items_raw = []
    for item in data.items:
        product = store.products.get(item.product_id)
        if product is None:
            raise ValueError(f"Product {item.product_id} not found")
        total += product["price"] * item.quantity
        items_raw.append({"product_id": item.product_id, "quantity": item.quantity})

    order = {
        "id": store.next_order_id,
        "user_id": user_id,
        "items": items_raw,
        "total": round(total, 2),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    store.orders[store.next_order_id] = order
    store.next_order_id += 1
    return _enrich_order(order)


def delete_order(order_id: int) -> bool:
    return store.orders.pop(order_id, None) is not None
