"""UAC authentication for YoLink Multi-Home integration.

Based on YoLink UAC (User Access Credentials) authentication flow.
"""

from __future__ import annotations

import asyncio
import logging
import time

from aiohttp import ClientError, ClientResponseError, ClientSession
from yolink.auth_mgr import YoLinkAuthMgr
from yolink.exception import YoLinkAuthFailError, YoLinkClientError

_LOGGER = logging.getLogger(__name__)

TOKEN_REFRESH_BUFFER = 300  # Refresh token 5 minutes before expiry
TOKEN_URL = "https://api.yosmart.com/open/yolink/token"


# Token-endpoint error messages (HTTP 200, {"state": "error", "msg": ...})
# that mean the UAID / secret key themselves are wrong.
_CREDENTIAL_REJECTED_MSGS = frozenset({"auth failed", "client_id not existed"})

class YoLinkUACAuth(YoLinkAuthMgr):
    """YoLink UAC (User Access Credentials) authentication manager.

    This auth manager uses client credentials (UAID + Secret Key) instead of OAuth2.
    Each UAC is tied to a specific YoLink home.

    Auth failures are raised as YoLinkAuthFailError so the integration's
    reauth machinery (ConfigEntryAuthFailed / async_start_reauth) can react.
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
        # Monotonic deadline so wall-clock changes (DST, NTP) can't extend
        # a token's perceived lifetime.
        self._token_expires_at: float | None = None
        self._refresh_lock = asyncio.Lock()

    async def _async_retry_with_client_credentials(self) -> str:
        """Discard the refresh token and retry with client credentials."""
        self._refresh_token = None
        return await self.async_get_access_token(use_refresh=False)

    async def async_get_access_token(self, use_refresh: bool = True) -> str:
        """Get access token using UAC credentials or refresh token.

        Args:
            use_refresh: Whether to use refresh token if available

        Returns:
            Access token string

        Raises:
            YoLinkAuthFailError: If the credentials are rejected
            YoLinkClientError: If the token request fails for other reasons
            TimeoutError: If the token request times out
        """
        refreshing = use_refresh and self._refresh_token is not None
        if refreshing:
            data = {
                "grant_type": "refresh_token",
                "client_id": self._uaid,
                "refresh_token": self._refresh_token,
            }
            _LOGGER.debug("Refreshing access token using refresh_token")
        else:
            data = {
                "grant_type": "client_credentials",
                "client_id": self._uaid,
                "client_secret": self._secret_key,
            }
            _LOGGER.debug("Getting new access token using client_credentials")

        try:
            async with asyncio.timeout(10):
                async with self._session.post(TOKEN_URL, json=data) as response:
                    response.raise_for_status()
                    token_data = await response.json()
        except ClientResponseError as err:
            if refreshing:
                _LOGGER.info(
                    "Token refresh failed (HTTP %s), retrying with client credentials",
                    err.status,
                )
                return await self._async_retry_with_client_credentials()
            if err.status in (401, 403):
                raise YoLinkAuthFailError(
                    str(err.status), "UAC credentials were rejected"
                ) from err
            _LOGGER.error("Failed to obtain access token: %s", err)
            raise YoLinkClientError(
                str(err.status), "Failed to obtain access token"
            ) from err
        except TimeoutError:
            if refreshing:
                _LOGGER.info(
                    "Token refresh timed out, retrying with client credentials"
                )
                return await self._async_retry_with_client_credentials()
            _LOGGER.error("Timeout obtaining access token")
            raise
        except ClientError as err:
            if refreshing:
                _LOGGER.info(
                    "Token refresh failed (%s), retrying with client credentials", err
                )
                return await self._async_retry_with_client_credentials()
            _LOGGER.error("Failed to obtain access token: %s", err)
            raise YoLinkClientError(
                "client_error", f"Failed to obtain access token: {err}"
            ) from err

        # The YoLink API can report errors with HTTP 200 and an error body
        access_token = token_data.get("access_token")
        if not access_token:
            if refreshing:
                _LOGGER.info(
                    "Token refresh rejected (%s), retrying with client credentials",
                    token_data,
                )
                return await self._async_retry_with_client_credentials()
            # Only a real credential rejection may start reauth. Throttling
            # and outage bodies also arrive as HTTP 200 without a token and
            # must stay retryable (ConfigEntryNotReady / UpdateFailed).
            code = str(token_data.get("code", "unknown"))
            msg = str(token_data.get("msg") or token_data.get("desc") or "")
            if msg.strip().lower() in _CREDENTIAL_REJECTED_MSGS:
                raise YoLinkAuthFailError(
                    code, f"UAC credentials were rejected: {msg}"
                )
            _LOGGER.error("Token endpoint returned no access token: %s", token_data)
            raise YoLinkClientError(
                code, f"Token endpoint returned no access token: {msg or token_data}"
            )

        self._access_token = access_token
        self._refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = time.monotonic() + expires_in

        _LOGGER.debug("Access token obtained, expires in %s seconds", expires_in)
        return access_token

    def access_token(self) -> str:
        """Return the current access token."""
        if not self._access_token:
            raise YoLinkAuthFailError("no_token", "No access token available")
        return self._access_token

    async def check_and_refresh_token(self) -> str:
        """Check token validity and refresh if needed.

        Serialized with a lock: every device coordinator and the MQTT client
        funnel through here, and concurrent refreshes would race on the
        single-use refresh token.

        Returns:
            Valid access token
        """
        async with self._refresh_lock:
            if not self._access_token or self._should_refresh_token():
                await self.async_get_access_token(use_refresh=True)
        return self.access_token()

    def _should_refresh_token(self) -> bool:
        """Check if token should be refreshed.

        Returns:
            True if token should be refreshed
        """
        if self._token_expires_at is None:
            return True

        # Refresh if within buffer time of expiry
        return time.monotonic() >= self._token_expires_at - TOKEN_REFRESH_BUFFER
