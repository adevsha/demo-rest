from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data import kafka
from app.models.db.product import Product
from app.models.product import ProductCreate, ProductUpdate


def _to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "in_stock": product.in_stock,
        "stock": product.stock,
    }


async def list_products(session: AsyncSession) -> list[dict]:
    result = await session.execute(select(Product).order_by(Product.id))
    return [_to_dict(p) for p in result.scalars().all()]


async def get_product(session: AsyncSession, product_id: int) -> dict | None:
    product = await session.get(Product, product_id)
    return _to_dict(product) if product else None


async def create_product(session: AsyncSession, data: ProductCreate) -> dict:
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        in_stock=data.in_stock,
        stock=data.stock,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    payload = _to_dict(product)
    await kafka.publish(kafka.TOPIC_PRODUCTS, "product.created", payload)
    return payload


async def update_product(
    session: AsyncSession, product_id: int, data: ProductUpdate
) -> dict | None:
    product = await session.get(Product, product_id)
    if product is None:
        return None
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    payload = _to_dict(product)
    await kafka.publish(kafka.TOPIC_PRODUCTS, "product.updated", payload)
    return payload


async def delete_product(session: AsyncSession, product_id: int) -> bool:
    product = await session.get(Product, product_id)
    if product is None:
        return False
    payload = _to_dict(product)
    await session.delete(product)
    await session.commit()
    await kafka.publish(kafka.TOPIC_PRODUCTS, "product.deleted", payload)
    return True
