from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.controllers import order as order_controller
from app.dependencies import get_current_user
from app.models.order import Order, OrderCreate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, current_user: dict = Depends(get_current_user)):
    try:
        return order_controller.create_order(current_user["id"], data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Order])
def list_orders(current_user: dict = Depends(get_current_user)):
    return order_controller.list_orders()


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int, current_user: dict = Depends(get_current_user)):
    order = order_controller.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, current_user: dict = Depends(get_current_user)):
    if not order_controller.delete_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
