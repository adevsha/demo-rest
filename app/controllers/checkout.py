import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.order import _enrich_order, reserve_stock
from app.data import kafka, mongo
from app.models.checkout import CheckoutRequest


_DISCOUNT_CODES: dict[str, Decimal] = {
    "WELCOME10": Decimal("0.10"),
    "SAVE20": Decimal("0.20"),
}


def _apply_discount(subtotal: Decimal, code: str | None) -> tuple[Decimal, Decimal]:
    if not code:
        return subtotal, Decimal("0")
    rate = _DISCOUNT_CODES.get(code.upper())
    if rate is None:
        return subtotal, Decimal("0")
    discount = (subtotal * rate).quantize(Decimal("0.01"))
    return subtotal - discount, discount


async def checkout(
    session: AsyncSession, user_id: int, data: CheckoutRequest
) -> dict:
    subtotal, items_raw = await reserve_stock(session, data.items)
    final_total, discount = _apply_discount(subtotal, data.discount_code)

    order_id = await mongo.next_sequence("orders")
    order_doc = {
        "id": order_id,
        "user_id": user_id,
        "items": items_raw,
        "total": float(round(final_total, 2)),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db = mongo.get_db()
    await db.orders.insert_one(order_doc)
    await session.commit()

    enriched = await _enrich_order(session, order_doc)
    confirmation_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
    response = {
        "confirmation_number": confirmation_number,
        "status": "completed",
        "order": enriched,
        "discount_applied": float(discount),
    }
    await kafka.publish(kafka.TOPIC_ORDERS, "checkout.completed", response)
    return response
