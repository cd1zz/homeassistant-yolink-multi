"""Support for YoLink Device."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from yolink.client_request import ClientRequest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import YoLinkCoordinator


class YoLinkEntity(CoordinatorEntity[YoLinkCoordinator]):
    """YoLink Device Basic Entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: YoLinkCoordinator,
    ) -> None:
        """Init YoLink Entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def device_id(self) -> str:
        """Return the device id of the YoLink device."""
        return self.coordinator.device.device_id

    async def async_added_to_hass(self) -> None:
        """Update state."""
        await super().async_added_to_hass()
        return self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update state."""
        data = self.coordinator.data
        if data is not None and len(data) > 0:
            self.update_entity_state(data)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info for HA."""
        # Include home_id in identifier to support multiple homes
        home_id = self.config_entry.data.get("home_id")
        home_name = self.config_entry.data.get("home_name", "YoLink")

        # Create unique device identifier including home_id
        device_identifier = (
            f"{home_id}_{self.coordinator.device.device_id}"
            if home_id
            else self.coordinator.device.device_id
        )

        return DeviceInfo(
            identifiers={(DOMAIN, device_identifier)},
            manufacturer=MANUFACTURER,
            model=self.coordinator.device.device_type,
            model_id=self.coordinator.device.device_model_name,
            name=self.coordinator.device.device_name,
            # Add suggested area based on home name to help organize
            suggested_area=home_name if home_name != "YoLink" else None,
        )

    @callback
    @abstractmethod
    def update_entity_state(self, state: dict) -> None:
        """Parse and update entity state, should be overridden."""

    async def call_device(self, request: ClientRequest) -> dict[str, Any]:
        """Call device api."""
        return await self.coordinator.call_device(request)
