import logging
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import BulkWriteError
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.product import Product
from app.models.db.user import User
from app.security import hash_password

logger = logging.getLogger(__name__)


_DEFAULT_PASSWORD = "password123"


_USER_SEEDS = [
    (1, "Alice Johnson", "alice@example.com", 30),
    (2, "Bob Smith", "bob@example.com", 25),
    (3, "Charlie Brown", "charlie@example.com", 35),
    (4, "Diana Prince", "diana@example.com", 28),
    (5, "Eve Wilson", "eve@example.com", 32),
    (6, "Frank Miller", "frank@example.com", 45),
    (7, "Grace Lee", "grace@example.com", 27),
    (8, "Henry Davis", "henry@example.com", 38),
    (9, "Ivy Chen", "ivy@example.com", 22),
    (10, "Jack Taylor", "jack@example.com", 55),
]

_PRODUCT_SEEDS = [
    (1, "Laptop", "A powerful laptop", Decimal("999.99"), True, 25),
    (2, "Wireless Mouse", "Ergonomic wireless mouse", Decimal("29.99"), True, 100),
    (3, "Mechanical Keyboard", "RGB mechanical keyboard", Decimal("149.99"), True, 50),
    (4, "Monitor", "27-inch 4K monitor", Decimal("399.99"), False, 0),
    (5, "USB-C Hub", "7-in-1 USB-C hub", Decimal("49.99"), True, 75),
    (6, "Webcam", "1080p HD webcam", Decimal("79.99"), True, 40),
    (7, "Headphones", "Noise-cancelling headphones", Decimal("199.99"), False, 0),
    (8, "Desk Lamp", "LED desk lamp with dimmer", Decimal("34.99"), True, 60),
    (9, "Mouse Pad", "Large extended mouse pad", Decimal("14.99"), True, 200),
    (10, "External SSD", "1TB portable SSD", Decimal("119.99"), True, 30),
]

_ORDER_SEEDS = [
    {
        "id": 1,
        "user_id": 1,
        "items": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 2},
        ],
        "total": 1059.97,
        "created_at": "2026-04-10T10:00:00",
    },
    {
        "id": 2,
        "user_id": 3,
        "items": [
            {"product_id": 3, "quantity": 1},
            {"product_id": 5, "quantity": 1},
        ],
        "total": 199.98,
        "created_at": "2026-04-12T14:30:00",
    },
    {
        "id": 3,
        "user_id": 5,
        "items": [
            {"product_id": 7, "quantity": 1},
            {"product_id": 10, "quantity": 2},
        ],
        "total": 439.97,
        "created_at": "2026-04-15T09:15:00",
    },
]


async def _seed_users(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(User))
    if count and count > 0:
        return
    password_hash = hash_password(_DEFAULT_PASSWORD)
    session.add_all(
        [
            User(id=uid, name=name, email=email, age=age, password=password_hash)
            for uid, name, email, age in _USER_SEEDS
        ]
    )
    await session.flush()
    await session.execute(text("ALTER TABLE users AUTO_INCREMENT = 11"))
    logger.info("Seeded %d users", len(_USER_SEEDS))


async def _seed_products(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Product))
    if count and count > 0:
        return
    session.add_all(
        [
            Product(
                id=pid,
                name=name,
                description=description,
                price=price,
                in_stock=in_stock,
                stock=stock,
            )
            for pid, name, description, price, in_stock, stock in _PRODUCT_SEEDS
        ]
    )
    await session.flush()
    await session.execute(text("ALTER TABLE products AUTO_INCREMENT = 11"))
    logger.info("Seeded %d products", len(_PRODUCT_SEEDS))


async def seed_mysql(session: AsyncSession) -> None:
    await _seed_users(session)
    await _seed_products(session)
    await session.commit()


async def seed_mongo(db: AsyncIOMotorDatabase) -> None:
    existing = await db.orders.count_documents({})
    if existing > 0:
        return
    try:
        await db.orders.insert_many(_ORDER_SEEDS, ordered=False)
    except BulkWriteError as exc:
        logger.warning("Mongo order seed partial (dup tolerated): %s", exc.details)
    await db.counters.update_one(
        {"_id": "orders"},
        {"$set": {"seq": len(_ORDER_SEEDS)}},
        upsert=True,
    )
    logger.info("Seeded %d orders", len(_ORDER_SEEDS))
