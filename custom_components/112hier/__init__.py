"""112hier — live 112-meldingen in Home Assistant."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ALLEEN_SPOED,
    CONF_BEVAT,
    CONF_CAPCODES,
    CONF_BASIS,
    CONF_DIENSTEN,
    CONF_INTERVAL,
    CONF_PLAATS,
    CONF_REGIOS,
    CONF_STRAAL,
    DEFAULT_BASIS,
    DOMAIN,
    MIN_INTERVAL_SECONDEN,
)
from .coordinator import HierCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.GEO_LOCATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Eén coördinator per configuratie opzetten."""
    # Opties winnen van de oorspronkelijke invoer: zo werkt "Configureren" in de UI.
    inst = {**entry.data, **entry.options}

    straal = float(inst.get(CONF_STRAAL) or 0)
    punt = None
    if straal and inst.get("lat") is not None and inst.get("lon") is not None:
        punt = (float(inst["lat"]), float(inst["lon"]))

    seconden = max(MIN_INTERVAL_SECONDEN, int(inst.get(CONF_INTERVAL) or 30))

    coordinator = HierCoordinator(
        hass,
        basis=inst.get(CONF_BASIS) or DEFAULT_BASIS,
        interval=timedelta(seconds=seconden),
        regios=inst.get(CONF_REGIOS) or [],
        diensten=inst.get(CONF_DIENSTEN) or [],
        plaats=(inst.get(CONF_PLAATS) or "").strip().lower().replace(" ", "-") or None,
        punt=punt,
        straal=straal or None,
        alleen_spoed=bool(inst.get(CONF_ALLEEN_SPOED)),
        # Komma-gescheiden invoer opknippen; lege stukken eruit.
        capcodes=[c.strip() for c in str(inst.get(CONF_CAPCODES) or "").split(",") if c.strip()],
        bevat=[w.strip() for w in str(inst.get(CONF_BEVAT) or "").split(",") if w.strip()],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Bij het wijzigen van opties opnieuw laden, anders blijft het oude filter staan.
    entry.async_on_unload(entry.add_update_listener(_herlaad))
    return True


async def _herlaad(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ontladen = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ontladen:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ontladen
