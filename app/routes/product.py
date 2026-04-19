from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import product as product_controller
from app.data.mysql import get_session
from app.dependencies import get_current_user
from app.models.product import Product, ProductCreate, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    return await product_controller.create_product(session, data)


@router.get("/", response_model=list[Product])
async def list_products(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    return await product_controller.list_products(session)


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    product = await product_controller.get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    product = await product_controller.update_product(session, product_id, data)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    if not await product_controller.delete_product(session, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
