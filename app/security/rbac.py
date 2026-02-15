"""
RBAC module — FastAPI dependencies for JWT-validated, department-scoped access.

Usage in routes:
    @router.get("/protected")
    async def protected(user = Depends(get_current_user)):
        ...

    @router.post("/dept-resource")
    async def dept_resource(user = Depends(require_department("radiology"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import jwt as pyjwt

from app.security.auth import decode_access_token, user_db, ROLE_HIERARCHY

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Decode JWT from Authorization header, return full user dict.
    Raises 401 if missing / invalid / expired.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = user_db.get_user(username)
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    return user


def require_role(min_role: str):
    """Dependency: require the user to have at least `min_role` level."""
    min_level = ROLE_HIERARCHY.get(min_role, 0)

    async def _check(user: dict = Depends(get_current_user)):
        user_level = ROLE_HIERARCHY.get(user["role"], 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{min_role}' or higher",
            )
        return user

    return _check


def require_department(department: str):
    """Dependency: require the user to have access to a specific department."""

    async def _check(user: dict = Depends(get_current_user)):
        if user["role"] == "admin":
            return user  # admin bypasses
        if department not in user.get("departments", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have access to the '{department}' department",
            )
        return user

    return _check


def get_user_departments(user: dict) -> List[str]:
    """Return the list of departments this user can access."""
    if user["role"] == "admin":
        from app.core.config import settings
        return settings.departments_list
    return user.get("departments", [])
