import uuid

from pydantic import BaseModel, Field

from app.models.order import Order, OrderItemCreate


class CheckoutRequest(BaseModel):
    items: list[OrderItemCreate]
    discount_code: str | None = None


class CheckoutResponse(BaseModel):
    confirmation_number: str = Field(default_factory=lambda: f"ORD-{uuid.uuid4().hex[:12].upper()}")
    status: str = "completed"
    order: Order
    discount_applied: float = 0.0
