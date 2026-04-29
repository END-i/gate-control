from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import decode_access_token
from crud.admin import get_admin_by_username
from models.admin import Admin, AdminRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    return await get_admin_from_token(token, db)


async def get_admin_from_token(token: str, db: AsyncSession) -> Admin:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
    except Exception as exc:
        raise credentials_error from exc

    if not username:
        raise credentials_error

    admin = await get_admin_by_username(db, username)
    if admin is None:
        raise credentials_error

    return admin


def require_roles(*allowed_roles: AdminRole):
    allowed = {role.value for role in allowed_roles}

    async def _require(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        if current_admin.role.value not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_admin

    return _require
