"""UAC authentication for YoLink Multi-Home integration.

Based on YoLink UAC (User Access Credentials) authentication flow.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging

from aiohttp import ClientSession
from yolink.auth_mgr import YoLinkAuthMgr

_LOGGER = logging.getLogger(__name__)

TOKEN_REFRESH_BUFFER = 300  # Refresh token 5 minutes before expiry


class YoLinkUACAuth(YoLinkAuthMgr):
    """YoLink UAC (User Access Credentials) authentication manager.

    This auth manager uses client credentials (UAID + Secret Key) instead of OAuth2.
    Each UAC is tied to a specific YoLink home.
    """

    def __init__(
        self,
        websession: ClientSession,
        uaid: str,
        secret_key: str,
    ) -> None:
        """Initialize UAC authentication.

        Args:
            websession: aiohttp ClientSession for HTTP requests
            uaid: YoLink User Access ID (client_id)
            secret_key: YoLink Secret Key (client_secret)
        """
        super().__init__(websession)
        self._uaid = uaid
        self._secret_key = secret_key
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_url = "https://api.yosmart.com/open/yolink/token"

    async def async_get_access_token(self, use_refresh: bool = True) -> str:
        """Get access token using UAC credentials or refresh token.

        Args:
            use_refresh: Whether to use refresh token if available

        Returns:
            Access token string

        Raises:
            Exception: If token request fails
        """
        # Try refresh token first if available
        if use_refresh and self._refresh_token:
            data = {
                "grant_type": "refresh_token",
                "client_id": self._uaid,
                "refresh_token": self._refresh_token,
            }
            _LOGGER.debug("Refreshing access token using refresh_token")
        else:
            # Use client credentials
            data = {
                "grant_type": "client_credentials",
                "client_id": self._uaid,
                "client_secret": self._secret_key,
            }
            _LOGGER.debug("Getting new access token using client_credentials")

        try:
            async with asyncio.timeout(10):
                async with self._session.post(
                    self._token_url, json=data
                ) as response:
                    response.raise_for_status()
                    token_data = await response.json()

                    self._access_token = token_data.get("access_token")
                    self._refresh_token = token_data.get("refresh_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(
                        seconds=expires_in
                    )

                    _LOGGER.debug(
                        "Access token obtained, expires at %s", self._token_expires_at
                    )
                    return self._access_token

        except Exception as err:
            _LOGGER.error("Failed to obtain access token: %s", err)
            # If refresh failed, try client credentials
            if use_refresh and self._refresh_token:
                _LOGGER.info("Refresh token failed, trying client_credentials")
                self._refresh_token = None
                return await self.async_get_access_token(use_refresh=False)
            raise

    def access_token(self) -> str:
        """Return the current access token."""
        if not self._access_token:
            raise ValueError("No access token available")
        return self._access_token

    async def check_and_refresh_token(self) -> str:
        """Check token validity and refresh if needed.

        Returns:
            Valid access token
        """
        # Check if token needs refreshing
        if not self._access_token or self._should_refresh_token():
            await self.async_get_access_token(use_refresh=True)
        return self.access_token()

    def _should_refresh_token(self) -> bool:
        """Check if token should be refreshed.

        Returns:
            True if token should be refreshed
        """
        if not self._token_expires_at:
            return True

        # Refresh if within buffer time of expiry
        return datetime.now() >= (
            self._token_expires_at - timedelta(seconds=TOKEN_REFRESH_BUFFER)
        )
