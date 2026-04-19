from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data import kafka, mongo
from app.errors import InsufficientStockError, ProductNotFoundError
from app.models.db.product import Product
from app.models.db.user import User
from app.models.order import OrderCreate


async def _enrich_order(session: AsyncSession, order: dict) -> dict:
    user_row = await session.get(User, order["user_id"])
    user_name = user_row.name if user_row else "Unknown"

    product_ids = [item["product_id"] for item in order["items"]]
    products_by_id: dict[int, Product] = {}
    if product_ids:
        result = await session.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products_by_id = {p.id: p for p in result.scalars().all()}

    items: list[dict] = []
    for item in order["items"]:
        product = products_by_id.get(item["product_id"])
        items.append(
            {
                "product_id": item["product_id"],
                "product_name": product.name if product else "Unknown",
                "quantity": item["quantity"],
                "price": float(product.price) if product else 0.0,
            }
        )

    return {
        "id": order["id"],
        "user_id": order["user_id"],
        "user_name": user_name,
        "items": items,
        "total": order["total"],
        "created_at": order["created_at"],
    }


async def reserve_stock(
    session: AsyncSession, items: list
) -> tuple[Decimal, list[dict]]:
    """Validate + decrement stock atomically. Returns (total, items_raw).

    Items is a list with `.product_id` and `.quantity` attrs (OrderItemCreate).
    Raises ProductNotFoundError or InsufficientStockError.
    """
    product_ids = [item.product_id for item in items]
    if not product_ids:
        return Decimal("0"), []

    result = await session.execute(
        select(Product).where(Product.id.in_(product_ids)).with_for_update()
    )
    products_by_id: dict[int, Product] = {p.id: p for p in result.scalars().all()}

    total = Decimal("0")
    items_raw: list[dict] = []
    for item in items:
        product = products_by_id.get(item.product_id)
        if product is None:
            raise ProductNotFoundError(item.product_id)
        if product.stock < item.quantity:
            raise InsufficientStockError(item.product_id)
        total += product.price * item.quantity
        items_raw.append({"product_id": item.product_id, "quantity": item.quantity})

    for item in items:
        product = products_by_id[item.product_id]
        product.stock -= item.quantity
        if product.stock == 0:
            product.in_stock = False

    await session.flush()
    return total, items_raw


async def list_orders(session: AsyncSession) -> list[dict]:
    db = mongo.get_db()
    cursor = db.orders.find({}, {"_id": 0}).sort("id", 1)
    orders = await cursor.to_list(length=None)
    return [await _enrich_order(session, o) for o in orders]


async def get_order(session: AsyncSession, order_id: int) -> dict | None:
    db = mongo.get_db()
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if order is None:
        return None
    return await _enrich_order(session, order)


async def create_order(
    session: AsyncSession, user_id: int, data: OrderCreate
) -> dict:
    total, items_raw = await reserve_stock(session, data.items)

    order_id = await mongo.next_sequence("orders")
    order_doc = {
        "id": order_id,
        "user_id": user_id,
        "items": items_raw,
        "total": float(round(total, 2)),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db = mongo.get_db()
    await db.orders.insert_one(order_doc)
    await session.commit()

    enriched = await _enrich_order(session, order_doc)
    await kafka.publish(kafka.TOPIC_ORDERS, "order.created", enriched)
    return enriched


async def delete_order(order_id: int) -> bool:
    db = mongo.get_db()
    result = await db.orders.delete_one({"id": order_id})
    if result.deleted_count == 0:
        return False
    await kafka.publish(kafka.TOPIC_ORDERS, "order.deleted", {"id": order_id})
    return True
