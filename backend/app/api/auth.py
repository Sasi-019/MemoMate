from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.auth_service import (
    normalize_name_id,
    create_session,
    revoke_session,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------
# REQUEST / RESPONSE SCHEMAS
# ---------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    name_id: str = Field(
        min_length=3,
        max_length=50,
    )


class LoginRequest(BaseModel):
    name_id: str = Field(
        min_length=3,
        max_length=50,
    )


class AuthorizeRequest(BaseModel):
    user_id: int


class UserResponse(BaseModel):
    id: int
    name: str
    name_id: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    name = request.name.strip()
    name_id = normalize_name_id(request.name_id)

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required",
        )

    if not name_id:
        raise HTTPException(
            status_code=400,
            detail="MemoMate ID is required",
        )

    existing = (
        db.query(User)
        .filter(User.name_id == name_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="That MemoMate ID already exists",
        )

    user = User(
        name=name,
        name_id=name_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "requires_authorization": True,
        "user": UserResponse.model_validate(user),
    }


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    name_id = normalize_name_id(request.name_id)

    user = (
        db.query(User)
        .filter(User.name_id == name_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="MemoMate account not found",
        )

    return {
        "requires_authorization": True,
        "user": UserResponse.model_validate(user),
    }


# ---------------------------------------------------------
# AUTHORIZE
# ---------------------------------------------------------

@router.post("/authorize")
def authorize(
    request: AuthorizeRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == request.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    user.authorized_at = datetime.utcnow()

    token = create_session(
        db,
        user,
    )

    return {
        "message": "Authorization successful",
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


# ---------------------------------------------------------
# CURRENT USER
# ---------------------------------------------------------

@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if credentials:
        revoke_session(
            db,
            credentials.credentials,
        )

    return {
        "message": "Logged out successfully",
    }
