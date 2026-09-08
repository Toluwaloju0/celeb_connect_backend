"""Helpers for issuing and clearing authentication cookies."""

from os import getenv

from fastapi import Response


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
    options = _cookie_options()
    response.set_cookie("access_token", access_token, **options)
    response.set_cookie("refresh_token", refresh_token, **options)


def clear_auth_cookies(response: Response) -> None:
    """Expire the authentication cookies using the attributes used to create them."""
    options = _cookie_options()
    response.delete_cookie("access_token", **options)
    response.delete_cookie("refresh_token", **options)
