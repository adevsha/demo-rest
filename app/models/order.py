from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class OrderItemDetail(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float


class Order(BaseModel):
    id: int
    user_id: int
    user_name: str
    items: list[OrderItemDetail]
    total: float
    created_at: str
