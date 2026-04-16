from fastapi import APIRouter, HTTPException, status

from app.controllers import auth as auth_controller
from app.models.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = auth_controller.authenticate(data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = auth_controller.create_access_token(user["id"], user["email"])
    return {"access_token": token, "token_type": "bearer"}
