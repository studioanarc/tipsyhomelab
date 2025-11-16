"""Config flow for Wine Monitor integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_URL,
    CONF_UPDATE_INTERVAL,
    CONF_WEBHOOK_ID,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ENDPOINT_STATUS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_API_URL): str,
        vol.Optional(
            CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
        ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        vol.Optional(CONF_WEBHOOK_ID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api_url = data[CONF_API_URL]

    # Remove trailing slash if present
    if api_url.endswith("/"):
        api_url = api_url[:-1]

    session = async_get_clientsession(hass)

    try:
        # Test connection to the API
        async with session.get(f"{api_url}{ENDPOINT_STATUS}", timeout=10) as response:
            if response.status != 200:
                raise CannotConnect(
                    f"API returned status code {response.status}"
                )

            # Try to parse the response
            status_data = await response.json()

            if not isinstance(status_data, dict):
                raise InvalidData("API response is not valid JSON")

    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to Wine Monitor API: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {
        "title": data[CONF_NAME],
        "api_url": api_url,
        "version": status_data.get("version", "unknown"),
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wine Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidData:
                errors["base"] = "invalid_data"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on the API URL
                await self.async_set_unique_id(user_input[CONF_API_URL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_API_URL: info["api_url"],
                        CONF_UPDATE_INTERVAL: user_input.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                        CONF_WEBHOOK_ID: user_input.get(CONF_WEBHOOK_ID),
                        "version": info["version"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "example_url": "http://homeassistant.local:5000"
            },
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidData(HomeAssistantError):
    """Error to indicate the API returned invalid data."""
