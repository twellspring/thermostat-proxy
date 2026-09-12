"""Tests that supported features survive real-thermostat unavailability."""

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.components.climate import ClimateEntityFeature, HVACMode
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from custom_components.thermostat_proxy.climate import CustomThermostatEntity


def create_proxy(hass, thermostat="climate.real"):
    """Helper to create a configured CustomThermostatEntity."""
    proxy = CustomThermostatEntity(
        hass=hass,
        name="Test Proxy",
        real_thermostat=thermostat,
        sensors=[{"name": "Remote", "entity_id": "sensor.remote"}],
        default_sensor="Remote",
        unique_id="123",
        physical_sensor_name="Physical",
        use_last_active_sensor=False,
    )

    supported = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.PRESET_MODE
    )

    hass.states.async_set(
        thermostat,
        HVACMode.HEAT_COOL,
        {
            "current_temperature": 22.0,
            "target_temp_low": 18.0,
            "target_temp_high": 24.0,
            "target_temp_step": 1.0,
            "supported_features": supported,
        },
    )
    proxy._real_state = hass.states.get(thermostat)
    proxy._update_real_temperature_limits()
    return proxy


@pytest.mark.asyncio
async def test_is_range_mode_with_range_support(hass: HomeAssistant):
    """Range mode must be reported for heat_cool when range is supported."""
    proxy = create_proxy(hass)
    assert proxy.supported_features & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    assert proxy.is_range_mode


@pytest.mark.parametrize("unavailable_state", [STATE_UNAVAILABLE, STATE_UNKNOWN])
@pytest.mark.asyncio
async def test_features_preserved_when_real_thermostat_unavailable(
    hass: HomeAssistant, unavailable_state: str
):
    """supported_features must not be lost while the real thermostat is unavailable."""
    proxy = create_proxy(hass)
    features_before = proxy.supported_features

    hass.states.async_set("climate.real", unavailable_state)
    proxy._real_state = hass.states.get("climate.real")
    proxy._update_real_temperature_limits()

    assert proxy.supported_features == features_before
    assert proxy.supported_features & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE