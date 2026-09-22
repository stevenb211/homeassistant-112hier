"""De sensoren: laatste melding en aantal vandaag."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
# DeviceInfo woont in device_registry, niet in een eigen device_info-module —
# die laatste bestaat niet en liet de integratie stukgaan bij het opzetten.
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTIE, DOMAIN, SPOED_CODES
from .coordinator import HierCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: HierCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [LaatsteMelding(coordinator, entry), AantalMeldingen(coordinator, entry)]
    )


class Basis(CoordinatorEntity[HierCoordinator], SensorEntity):
    """Gedeelde eigenschappen van beide sensoren."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTIE

    def __init__(self, coordinator: HierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="112hier.nl",
            model="P2000-meldingen",
            configuration_url="https://112hier.nl/feed",
        )


class LaatsteMelding(Basis):
    """De meest recente melding die aan je filters voldoet."""

    _attr_icon = "mdi:alert-circle-outline"
    _attr_translation_key = "laatste_melding"

    def __init__(self, coordinator: HierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_laatste"

    @property
    def native_value(self) -> str | None:
        """De leesbare regel, afgekapt: een sensorwaarde mag niet te lang zijn.

        Home Assistant bewaart de toestand in de database en weigert waarden
        boven de 255 tekens. Het hele bericht staat in de attributen.
        """
        meldingen = self.coordinator.meldingen
        if not meldingen:
            return None
        m = meldingen[0]
        tekst = m.get("leesbaar") or m.get("bericht") or ""
        return tekst[:250]

    @property
    def extra_state_attributes(self) -> dict:
        meldingen = self.coordinator.meldingen
        if not meldingen:
            return {}
        m = meldingen[0]
        locatie = m.get("locatie") or {}
        return {
            "id": m.get("id"),
            "bericht": m.get("bericht"),
            "dienst": m.get("dienst"),
            "urgentie": m.get("urgentie"),
            "urgentie_uitleg": m.get("urgentie_uitleg"),
            "spoed": (m.get("urgentie") or "") in SPOED_CODES,
            "plaats": m.get("plaats"),
            "gemeente": m.get("gemeente"),
            "straat": m.get("straat"),
            "regio": m.get("regio"),
            "regio_code": m.get("regio_code"),
            # Met deze twee kun je de melding op een kaart-card zetten.
            "latitude": locatie.get("lat"),
            "longitude": locatie.get("lon"),
            "nauwkeurigheid": locatie.get("precisie"),
            "capcodes": m.get("capcodes"),
            "eenheden": [e.get("label") for e in (m.get("eenheden") or [])],
            "afstand_km": m.get("afstand_km"),
            "incident_id": m.get("incident_id"),
            "ontvangen": m.get("ontvangen"),
            "url": m.get("url"),
        }


class AantalMeldingen(Basis):
    """Hoeveel meldingen wij bewaard hebben sinds Home Assistant startte."""

    _attr_icon = "mdi:counter"
    _attr_translation_key = "aantal"
    _attr_state_class = "measurement"

    def __init__(self, coordinator: HierCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_aantal"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.meldingen)

    @property
    def extra_state_attributes(self) -> dict:
        """De hele lijst.

        Hier leest onze eigen kaart uit, en je kunt er met een template-card
        zelf iets mee bouwen. Genoeg velden om een rij te tonen zonder dat je
        de melding nog ergens hoeft op te halen.
        """
        return {
            "meldingen": [
                {
                    "id": m.get("id"),
                    "tijd": m.get("ontvangen"),
                    "dienst": m.get("dienst"),
                    "urgentie": m.get("urgentie"),
                    "urgentie_uitleg": m.get("urgentie_uitleg"),
                    "spoed": (m.get("urgentie") or "") in SPOED_CODES,
                    "tekst": m.get("leesbaar") or m.get("bericht"),
                    "plaats": m.get("plaats"),
                    "straat": m.get("straat"),
                    "regio": m.get("regio"),
                    "afstand_km": m.get("afstand_km"),
                    "incident_id": m.get("incident_id"),
                    "url": m.get("url"),
                }
                for m in self.coordinator.meldingen
            ]
        }
