from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.data import kafka, mongo
from app.errors import EmailAlreadyRegisteredError
from app.models.db.user import User
from app.models.user import UserCreate, UserUpdate
from app.security import hash_password


def _to_dict(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "age": user.age}


async def list_users(session: AsyncSession) -> list[dict]:
    result = await session.execute(select(User).order_by(User.id))
    return [_to_dict(u) for u in result.scalars().all()]


async def get_user(session: AsyncSession, user_id: int) -> dict | None:
    user = await session.get(User, user_id)
    return _to_dict(user) if user else None


async def create_user(session: AsyncSession, data: UserCreate) -> dict:
    user = User(
        name=data.name,
        email=data.email,
        age=data.age,
        password=hash_password(data.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise EmailAlreadyRegisteredError()
    await session.refresh(user)
    payload = _to_dict(user)
    await kafka.publish(kafka.TOPIC_USERS, "user.created", payload)
    return payload


async def update_user(session: AsyncSession, user_id: int, data: UserUpdate) -> dict | None:
    user = await session.get(User, user_id)
    if user is None:
        return None
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise EmailAlreadyRegisteredError()
    await session.refresh(user)
    payload = _to_dict(user)
    await kafka.publish(kafka.TOPIC_USERS, "user.updated", payload)
    return payload


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    user = await session.get(User, user_id)
    if user is None:
        return False
    user_payload = _to_dict(user)

    db = mongo.get_db()
    cascade_ids = [
        doc["id"]
        async for doc in db.orders.find({"user_id": user_id}, {"id": 1, "_id": 0})
    ]
    if cascade_ids:
        await db.orders.delete_many({"user_id": user_id})

    await session.delete(user)
    await session.commit()

    for order_id in cascade_ids:
        await kafka.publish(
            kafka.TOPIC_ORDERS,
            "order.deleted",
            {"id": order_id, "user_id": user_id, "cascade": True},
        )
    await kafka.publish(kafka.TOPIC_USERS, "user.deleted", user_payload)
    return True


async def get_user_summary(session: AsyncSession, user_id: int) -> dict | None:
    from app.models.db.product import Product

    user = await session.get(User, user_id)
    if user is None:
        return None

    db = mongo.get_db()
    orders = await db.orders.find({"user_id": user_id}, {"_id": 0}).sort("id", 1).to_list(None)

    total_spent = 0.0
    quantity_by_product: dict[int, int] = {}
    for order in orders:
        total_spent += float(order.get("total", 0.0))
        for item in order.get("items", []):
            pid = item["product_id"]
            quantity_by_product[pid] = quantity_by_product.get(pid, 0) + item["quantity"]

    product_by_id: dict[int, Product] = {}
    if quantity_by_product:
        result = await session.execute(
            select(Product).where(Product.id.in_(quantity_by_product.keys()))
        )
        product_by_id = {p.id: p for p in result.scalars().all()}

    top_product = None
    if quantity_by_product:
        top_pid = max(quantity_by_product, key=quantity_by_product.get)
        top_p = product_by_id.get(top_pid)
        top_product = {
            "product_id": top_pid,
            "product_name": top_p.name if top_p else "Unknown",
            "total_quantity": quantity_by_product[top_pid],
        }

    from app.controllers.order import _enrich_order

    enriched_orders = [await _enrich_order(session, order) for order in orders]

    return {
        "user_id": user.id,
        "user_name": user.name,
        "order_count": len(orders),
        "total_spent": round(total_spent, 2),
        "top_product": top_product,
        "orders": enriched_orders,
    }
