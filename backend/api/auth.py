from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.dependencies import get_current_admin
from core.rate_limit import enforce_rate_limit
from core.security import create_access_token, verify_password
from crud.admin import get_admin_by_username
from crud.security_audit import create_security_audit_event
from models.admin import Admin
from schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    enforce_rate_limit(
        request,
        scope="auth_login",
        limit=settings.auth_login_rate_limit,
        window_seconds=settings.auth_login_rate_window_seconds,
    )

    admin = await get_admin_by_username(db, payload.username)
    if admin is None or not verify_password(payload.password, admin.hashed_password):
        await create_security_audit_event(
            db,
            event_type="login",
            actor=payload.username,
            success=False,
            details="Invalid credentials",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=admin.username, extra_claims={"role": admin.role.value})
    await create_security_audit_event(
        db,
        event_type="login",
        actor=admin.username,
        success=True,
        details="Authentication successful",
    )
    return TokenResponse(access_token=token, role=admin.role.value)


@router.get("/me")
async def me(current_admin: Admin = Depends(get_current_admin)) -> dict[str, str]:
    return {"username": current_admin.username, "role": current_admin.role.value}
