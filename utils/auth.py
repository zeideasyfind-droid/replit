import os
from fastapi import HTTPException, Request, status


ADMIN_AUTH_TOKEN = os.environ.get("ADMIN_AUTH_TOKEN", "")


def verify_admin(request: Request) -> None:
    """Verify admin token from Authorization header or query param."""
    if not ADMIN_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_AUTH_TOKEN not configured on server.",
        )

    # Check query param
    token = request.query_params.get("token")

    # Check Authorization header
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token != ADMIN_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
