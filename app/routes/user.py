from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.controllers import user as user_controller
from app.dependencies import get_current_user
from app.models.user import User, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, current_user: dict = Depends(get_current_user)):
    return user_controller.create_user(data)


@router.get("/", response_model=list[User])
def list_users(current_user: dict = Depends(get_current_user)):
    return user_controller.list_users()


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    user = user_controller.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=User)
def update_user(user_id: int, data: UserUpdate, current_user: dict = Depends(get_current_user)):
    user = user_controller.update_user(user_id, data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if not user_controller.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
