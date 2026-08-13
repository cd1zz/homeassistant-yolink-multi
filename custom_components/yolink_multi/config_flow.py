"""Config flow for YoLink Multi-Home integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import voluptuous as vol
from yolink.exception import YoLinkAuthFailError

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import YoLinkUACAuth
from .const import CONF_HOME_ID, CONF_HOME_NAME, CONF_SECRET_KEY, CONF_UAID, DOMAIN

_LOGGER = logging.getLogger(__name__)

API_URL = "https://api.yosmart.com/open/yolink/v2/api"


class YoLinkMultiHomeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YoLink Multi-Home.

    This config flow uses UAC (User Access Credentials) authentication
    instead of OAuth2, allowing multiple homes to be configured.
    """

    VERSION = 1

    async def _async_validate_credentials(
        self, uaid: str, secret_key: str
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Validate UAC credentials and fetch home info.

        Returns (home_data, error_key); exactly one of the two is None.
        """
        session = async_get_clientsession(self.hass)
        auth_mgr = YoLinkUACAuth(session, uaid, secret_key)

        try:
            access_token = await auth_mgr.async_get_access_token(use_refresh=False)

            # Get home info directly via API (no MQTT setup needed)
            async with asyncio.timeout(10):
                async with session.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "method": "Home.getGeneralInfo",
                        "time": int(time.time() * 1000),
                    },
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
        except YoLinkAuthFailError as err:
            _LOGGER.error("Invalid UAC credentials: %s", err.message)
            return None, "invalid_auth"
        except TimeoutError:
            _LOGGER.error("Timeout connecting to YoLink API")
            return None, "timeout_connect"
        except Exception:
            _LOGGER.exception("Unexpected error during authentication")
            return None, "cannot_connect"

        if result.get("code") != "000000":
            _LOGGER.error("API error: %s", result)
            return None, "invalid_home"

        home_data = result.get("data", {})
        if not home_data.get("id"):
            _LOGGER.error("No home_id returned from API")
            return None, "invalid_home"

        return home_data, None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - UAC credentials entry.

        User enters their YoLink UAID and Secret Key, which are tied
        to a specific home in their YoLink account.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            home_data, error = await self._async_validate_credentials(
                user_input[CONF_UAID], user_input[CONF_SECRET_KEY]
            )
            if error is not None:
                errors["base"] = error
            else:
                home_id = home_data["id"]
                home_name = home_data.get("name", "YoLink Home")

                # Check if this home is already configured
                await self.async_set_unique_id(f"{DOMAIN}_{home_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=home_name,
                    data={
                        CONF_UAID: user_input[CONF_UAID],
                        CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                        CONF_HOME_ID: home_id,
                        CONF_HOME_NAME: home_name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UAID): str,
                    vol.Required(CONF_SECRET_KEY): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "uac_docs": "http://doc.yosmart.com/docs/overall/qsg_uac/",
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth flow when credentials expire."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation step."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            home_data, error = await self._async_validate_credentials(
                user_input[CONF_UAID], user_input[CONF_SECRET_KEY]
            )
            stored_home_id = reauth_entry.data.get(CONF_HOME_ID)
            if error is not None:
                errors["base"] = error
            elif stored_home_id is not None and home_data["id"] != stored_home_id:
                errors["base"] = "wrong_home"
            else:
                # Entries created before home_id was stored have no home_id
                # to compare against; accept the credentials and backfill it.
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_UAID: user_input[CONF_UAID],
                        CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                        CONF_HOME_ID: home_data["id"],
                        CONF_HOME_NAME: home_data.get(
                            "name",
                            reauth_entry.data.get(CONF_HOME_NAME, "YoLink Home"),
                        ),
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UAID, default=reauth_entry.data[CONF_UAID]): str,
                    vol.Required(CONF_SECRET_KEY): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "home_name": reauth_entry.data.get(CONF_HOME_NAME, "YoLink Home"),
            },
        )
