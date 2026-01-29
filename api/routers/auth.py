"""
Authentication router for Open Notebook API.
Provides endpoints to check authentication status.
"""

import os

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
async def get_auth_status():
    """
    Check if authentication is enabled.

    檢查是否啟用認證。

    Returns whether a password is required to access the API.
    返回是否需要密碼才能訪問 API。
    """
    auth_enabled = bool(os.environ.get("OPEN_NOTEBOOK_PASSWORD"))

    return {
        "auth_enabled": auth_enabled,
        "message": "Authentication is required"
        if auth_enabled
        else "Authentication is disabled",
    }
