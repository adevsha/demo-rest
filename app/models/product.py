from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    in_stock: bool


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    in_stock: bool | None = None


class Product(ProductBase):
    id: int
