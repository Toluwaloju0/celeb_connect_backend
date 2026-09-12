"""Helpers for issuing and clearing authentication cookies."""

from os import getenv

from fastapi import Response

ACCESS_TOKEN_MAX_AGE = 5 * 60
REFRESH_TOKEN_MAX_AGE = 60 * 60

def _cookie_options() -> dict:
    """Return cookie attributes appropriate for the configured environment."""

    return {
        "httponly": True,
        "secure": True,
        "samesite": "none",
        "path": "/",
    }


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Attach the access and refresh tokens using the same secure attributes."""
    if not access_token or not refresh_token:
        raise ValueError("Access and refresh tokens are required before setting auth cookies")

    options = _cookie_options()
    response.headers["Cache-Control"] = "no-store"

    response.set_cookie(
        key="access_token",
        value=str(access_token),
        max_age=ACCESS_TOKEN_MAX_AGE,
        **options,
    )
    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        max_age=REFRESH_TOKEN_MAX_AGE,
        **options,
    )


def clear_auth_cookies(response: Response) -> None:
    """Expire the authentication cookies using the attributes used to create them."""
    options = _cookie_options()
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie("access_token", **options)
    response.delete_cookie("refresh_token", **options)
