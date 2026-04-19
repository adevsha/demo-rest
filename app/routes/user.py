from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import user as user_controller
from app.data.mysql import get_session
from app.dependencies import get_current_user
from app.errors import EmailAlreadyRegisteredError
from app.models.user import User, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await user_controller.create_user(session, data)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="Email already registered")


@router.get("/", response_model=list[User])
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    return await user_controller.list_users(session)


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user = await user_controller.get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/orders")
async def get_user_orders(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    summary = await user_controller.get_user_summary(session, user_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="User not found")
    return summary


@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        user = await user_controller.update_user(session, user_id, data)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="Email already registered")
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    if not await user_controller.delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
