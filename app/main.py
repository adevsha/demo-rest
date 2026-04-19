import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.data import kafka, mongo, mysql, seed
from app.routes import auth, checkout, health, order, product, user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mysql.init_engine()
    await mongo.init_mongo()
    await kafka.start_producer()

    factory = mysql.get_session_factory()
    async with factory() as session:
        await seed.seed_mysql(session)
    await seed.seed_mongo(mongo.get_db())

    logger.info("demo-rest startup complete")
    try:
        yield
    finally:
        await kafka.stop_producer()
        await mongo.close_mongo()
        await mysql.close_engine()


app = FastAPI(title="Demo REST API", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(checkout.router)
