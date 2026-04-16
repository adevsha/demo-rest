from fastapi import FastAPI

from app.routes import auth, health, order, product, user

app = FastAPI(title="Demo REST API", version="0.1.0")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(product.router)
app.include_router(order.router)
