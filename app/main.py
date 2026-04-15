from fastapi import FastAPI

from app.routes import health, product, user

app = FastAPI(title="Demo REST API", version="0.1.0")

app.include_router(health.router)
app.include_router(user.router)
app.include_router(product.router)
