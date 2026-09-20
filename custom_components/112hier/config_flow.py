"""Instellen via de interface.

De bestaande P2000-integraties vragen om YAML-regels in configuration.yaml met
capcodes en regionummers die je zelf moet opzoeken. Dat is precies waar de
issues over gaan ("Krijg het niet werkend", "Regio vraag"). Hier klik je je
gebied bij elkaar en hoef je niets op te zoeken.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    LocationSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

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
    DIENSTEN,
    DOMAIN,
    MIN_INTERVAL_SECONDEN,
)

# De 25 veiligheidsregio's. Vast in de code, want ze veranderen zelden en zo
# werkt het instellen ook als de feed even niet bereikbaar is.
REGIOS: list[tuple[str, str]] = [
    ("VR01", "Groningen"), ("VR02", "Fryslân"), ("VR03", "Drenthe"),
    ("VR04", "IJsselland"), ("VR05", "Twente"), ("VR06", "Noord- en Oost-Gelderland"),
    ("VR07", "Gelderland-Midden"), ("VR08", "Gelderland-Zuid"), ("VR09", "Utrecht"),
    ("VR10", "Noord-Holland-Noord"), ("VR11", "Zaanstreek-Waterland"),
    ("VR12", "Kennemerland"), ("VR13", "Amsterdam-Amstelland"),
    ("VR14", "Gooi en Vechtstreek"), ("VR15", "Haaglanden"), ("VR16", "Hollands-Midden"),
    ("VR17", "Rotterdam-Rijnmond"), ("VR18", "Zuid-Holland-Zuid"), ("VR19", "Zeeland"),
    ("VR20", "Midden- en West-Brabant"), ("VR21", "Brabant-Noord"),
    ("VR22", "Brabant-Zuidoost"), ("VR23", "Limburg-Noord"), ("VR24", "Limburg-Zuid"),
    ("VR25", "Flevoland"),
]


def _schema(hass, standaard: dict[str, Any] | None = None) -> vol.Schema:
    s = standaard or {}
    return vol.Schema(
        {
            vol.Optional(CONF_REGIOS, default=s.get(CONF_REGIOS, [])): SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=c, label=n) for c, n in REGIOS],
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_DIENSTEN, default=s.get(CONF_DIENSTEN, DIENSTEN)): SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=d, label=d.capitalize()) for d in DIENSTEN],
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
            vol.Optional(CONF_PLAATS, default=s.get(CONF_PLAATS, "")): TextSelector(),
            vol.Optional("punt"): LocationSelector(),
            vol.Optional(CONF_STRAAL, default=s.get(CONF_STRAAL, 0)): NumberSelector(
                NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="km")
            ),
            # Capcodes als tekst: HA kan hier geen zoekveld tonen dat onze site
            # bevraagt, dus we verwijzen naar de plek waar je ze op naam vindt.
            # Oproepen voor deze codes komen altijd door, ook buiten je filters.
            vol.Optional(CONF_CAPCODES, default=s.get(CONF_CAPCODES, "")): TextSelector(),
            vol.Optional(CONF_BEVAT, default=s.get(CONF_BEVAT, "")): TextSelector(),
            vol.Optional(CONF_ALLEEN_SPOED, default=s.get(CONF_ALLEEN_SPOED, False)): BooleanSelector(),
            vol.Optional(CONF_INTERVAL, default=s.get(CONF_INTERVAL, 30)): NumberSelector(
                NumberSelectorConfig(min=MIN_INTERVAL_SECONDEN, max=600, step=5, unit_of_measurement="s")
            ),
            vol.Optional(CONF_BASIS, default=s.get(CONF_BASIS, DEFAULT_BASIS)): TextSelector(),
        }
    )


def _titel(gegevens: dict[str, Any]) -> str:
    """Een naam waaraan je de configuratie herkent in de lijst."""
    if gegevens.get(CONF_PLAATS):
        return f"112 · {gegevens[CONF_PLAATS]}"
    if gegevens.get(CONF_STRAAL):
        return f"112 · {int(gegevens[CONF_STRAAL])} km rond je punt"
    regios = gegevens.get(CONF_REGIOS) or []
    if len(regios) == 1:
        naam = dict(REGIOS).get(regios[0], regios[0])
        return f"112 · {naam}"
    if regios:
        return f"112 · {len(regios)} regio's"
    return "112 · heel Nederland"


class HierConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Eerste keer instellen."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        fouten: dict[str, str] = {}

        if user_input is not None:
            basis = (user_input.get(CONF_BASIS) or DEFAULT_BASIS).rstrip("/")
            # Meteen controleren of de feed antwoordt: een typefout in het adres
            # merk je anders pas als de sensor "onbekend" blijft.
            try:
                sessie = async_get_clientsession(self.hass)
                antwoord = await sessie.get(f"{basis}/feed.json?limiet=1", timeout=15)
                if antwoord.status != 200:
                    fouten["base"] = "geen_verbinding"
                else:
                    data = await antwoord.json()
                    if "meldingen" not in data:
                        fouten["base"] = "geen_feed"
            except Exception:  # noqa: BLE001 — elke fout betekent hier hetzelfde
                fouten["base"] = "geen_verbinding"

            if not fouten:
                punt = user_input.pop("punt", None)
                if punt and user_input.get(CONF_STRAAL):
                    user_input["lat"] = punt.get("latitude")
                    user_input["lon"] = punt.get("longitude")
                user_input[CONF_BASIS] = basis
                return self.async_create_entry(title=_titel(user_input), data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=_schema(self.hass), errors=fouten
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return HierOptionsFlow(entry)


class HierOptionsFlow(config_entries.OptionsFlow):
    """Achteraf je keuzes aanpassen zonder opnieuw toe te voegen."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            punt = user_input.pop("punt", None)
            if punt and user_input.get(CONF_STRAAL):
                user_input["lat"] = punt.get("latitude")
                user_input["lon"] = punt.get("longitude")
            return self.async_create_entry(title="", data=user_input)

        huidig = {**self._entry.data, **self._entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(self.hass, huidig))
