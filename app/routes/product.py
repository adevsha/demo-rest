from fastapi import APIRouter, HTTPException, Response, status

from app.controllers import product as product_controller
from app.models.product import Product, ProductCreate, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate):
    return product_controller.create_product(data)


@router.get("/", response_model=list[Product])
def list_products():
    return product_controller.list_products()


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = product_controller.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=Product)
def update_product(product_id: int, data: ProductUpdate):
    product = product_controller.update_product(product_id, data)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    if not product_controller.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
