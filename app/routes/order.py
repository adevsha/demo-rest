from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import order as order_controller
from app.data.mysql import get_session
from app.dependencies import get_current_user
from app.errors import InsufficientStockError, ProductNotFoundError
from app.models.order import Order, OrderCreate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await order_controller.create_order(session, current_user["id"], data)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"Product {e.product_id} not found")
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=400, detail=f"Insufficient stock for product {e.product_id}"
        )


@router.get("/", response_model=list[Order])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    return await order_controller.list_orders(session)


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    order = await order_controller.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
):
    if not await order_controller.delete_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
