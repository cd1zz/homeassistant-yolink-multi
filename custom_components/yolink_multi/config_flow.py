"""Config flow for YoLink Multi-Home integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from yolink.home_manager import YoLinkHome

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import YoLinkUACAuth
from .const import CONF_SECRET_KEY, CONF_UAID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class YoLinkMultiHomeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YoLink Multi-Home.

    This config flow uses UAC (User Access Credentials) authentication
    instead of OAuth2, allowing multiple homes to be configured.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - UAC credentials entry.

        User enters their YoLink UAID and Secret Key, which are tied
        to a specific home in their YoLink account.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate UAC credentials and get home info
                session = async_get_clientsession(self.hass)
                auth_mgr = YoLinkUACAuth(
                    session, user_input[CONF_UAID], user_input[CONF_SECRET_KEY]
                )

                # Get access token first
                await auth_mgr.async_get_access_token(use_refresh=False)

                # Test connection and get home info
                yolink_home = YoLinkHome()
                try:
                    async with asyncio.timeout(10):
                        await yolink_home.async_setup(auth_mgr, None)
                        home_info = await yolink_home.async_get_home_info()
                finally:
                    # Always clean up
                    await yolink_home.async_unload()

                home_id = home_info.get("id")
                home_name = home_info.get("name", "YoLink Home")

                if not home_id:
                    _LOGGER.error("No home_id returned from API")
                    errors["base"] = "invalid_home"
                else:
                    # Check if this home is already configured
                    await self.async_set_unique_id(f"{DOMAIN}_{home_id}")
                    self._abort_if_unique_id_configured()

                    # Create the config entry
                    return self.async_create_entry(
                        title=home_name,
                        data={
                            CONF_UAID: user_input[CONF_UAID],
                            CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                            "home_id": home_id,
                            "home_name": home_name,
                        },
                    )

            except asyncio.TimeoutError:
                _LOGGER.error("Timeout connecting to YoLink API")
                errors["base"] = "timeout_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error during authentication: %s", err)
                errors["base"] = "cannot_connect"

        # Show the form
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
                "uac_url": "https://www.yosmart.com/user/uac",
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
            try:
                # Validate new credentials
                session = async_get_clientsession(self.hass)
                auth_mgr = YoLinkUACAuth(
                    session, user_input[CONF_UAID], user_input[CONF_SECRET_KEY]
                )

                # Get access token to verify credentials
                await auth_mgr.async_get_access_token(use_refresh=False)

                # Test connection
                yolink_home = YoLinkHome()
                try:
                    async with asyncio.timeout(10):
                        await yolink_home.async_setup(auth_mgr, None)
                        home_info = await yolink_home.async_get_home_info()
                finally:
                    await yolink_home.async_unload()

                # Verify same home
                home_id = home_info.get("id")
                if home_id != reauth_entry.data.get("home_id"):
                    errors["base"] = "wrong_home"
                else:
                    # Update credentials
                    return self.async_update_reload_and_abort(
                        reauth_entry,
                        data_updates={
                            CONF_UAID: user_input[CONF_UAID],
                            CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                        },
                    )

            except asyncio.TimeoutError:
                errors["base"] = "timeout_connect"
            except Exception:
                _LOGGER.exception("Error during reauth")
                errors["base"] = "cannot_connect"

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
                "home_name": reauth_entry.data.get("home_name", "YoLink Home"),
            },
        )
