from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import checkout as checkout_controller
from app.data.mysql import get_session
from app.dependencies import get_current_user
from app.errors import InsufficientStockError, ProductNotFoundError
from app.models.checkout import CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await checkout_controller.checkout(session, current_user["id"], data)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"Product {e.product_id} not found")
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=400, detail=f"Insufficient stock for product {e.product_id}"
        )
