from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_admin
from core.security import create_access_token, verify_password
from crud.admin import get_admin_by_username
from models.admin import Admin
from schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    admin = await get_admin_by_username(db, payload.username)
    if admin is None or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=admin.username)
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(current_admin: Admin = Depends(get_current_admin)) -> dict[str, str]:
    return {"username": current_admin.username}
