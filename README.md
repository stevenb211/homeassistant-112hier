# 112hier voor Home Assistant

Live 112-meldingen van brandweer, ambulance, politie en KNRM in Home Assistant,
met de gegevens van [112hier.nl](https://112hier.nl).

Instellen doe je via de interface: je klikt je regio's, diensten en eventueel een
straal rond je huis bij elkaar. Geen capcodes opzoeken, geen regels in
`configuration.yaml`.

## Wat je krijgt

**Meldingen op de kaart**

Elke melding wordt een eigen `geo_location`-entiteit, dus je ziet ze allemaal
tegelijk op een kaart staan in plaats van één marker die door Nederland springt.

```yaml
type: map
geo_location_sources:
  - 112hier
hours_to_show: 2
```

**Twee sensoren**

| Entiteit | Waarde |
|---|---|
| `sensor.laatste_melding` | de meest recente melding in jouw gebied |
| `sensor.meldingen_bewaard` | hoeveel er sinds het opstarten binnenkwamen |

De laatste melding heeft alles wat je nodig hebt in zijn attributen: `dienst`,
`urgentie`, `spoed` (true/false), `plaats`, `straat`, `latitude`, `longitude`,
`nauwkeurigheid`, `afstand_km` (vanaf je huis), `capcodes`, `eenheden`,
`incident_id` en een `url` naar de melding op de kaart.

**Een event waar je automatiseringen aan hangt**

Bij elke nieuwe melding gaat er een `112hier_melding` de bus op, met dezelfde
gegevens. Dat is handiger dan op een sensor triggeren, omdat je dan niets mist
als er twee meldingen kort na elkaar binnenkomen.

```yaml
automation:
  - alias: "Lamp rood bij spoed in mijn buurt"
    trigger:
      - platform: event
        event_type: 112hier_melding
    condition:
      - condition: template
        value_template: >
          {{ trigger.event.data.urgentie in ['A0', 'A1', 'P 1']
             and (trigger.event.data.afstand_km or 99) < 10 }}
    action:
      - service: light.turn_on
        target: { entity_id: light.woonkamer }
        data: { color_name: red, flash: short }
      - service: notify.mobile_app_telefoon
        data:
          title: "{{ trigger.event.data.urgentie }} in {{ trigger.event.data.plaats }}"
          message: "{{ trigger.event.data.leesbaar }}"
          data:
            url: "{{ trigger.event.data.url }}"
```

De melding op een kaart zetten:

```yaml
type: map
entities:
  - entity: sensor.laatste_melding
```

## Installeren

**Via HACS** (aanbevolen)

1. HACS → Integraties → ⋮ → Aangepaste repositories
2. Voeg `https://github.com/stevenb211/homeassistant-112hier` toe, categorie *Integratie*
3. Zoek op "112hier", installeer, herstart Home Assistant
4. Instellingen → Apparaten & diensten → Integratie toevoegen → **112hier**

**Handmatig**

Kopieer `custom_components/112hier` naar je `config`-map en herstart.

## Instellingen

| Instelling | Betekenis |
|---|---|
| Veiligheidsregio's | laat leeg voor heel Nederland |
| Diensten | brandweer, ambulance, politie, KNRM |
| Woonplaats | alleen meldingen in die plaats |
| Punt + straal | alles binnen zoveel kilometer van een plek op de kaart |
| Eigen post volgen | capcodes van je kazerne — die oproepen komen **altijd** door, ook buiten je regio en buiten je diensten |
| Trefwoord | alleen meldingen waarin een bepaald woord staat, bijvoorbeeld `reanimatie,beknelling` |
| Alleen spoed | alleen A0, A1, P 1 en PRIO 1 |
| Hoe vaak kijken | standaard elke 30 seconden |

Laat je alles leeg, dan krijg je heel Nederland. Dat zijn er honderden per dag —
kies op zijn minst een regio.

## Waar de gegevens vandaan komen

112hier.nl ontvangt het P2000-netwerk rechtstreeks met een eigen antenne en
maakt er leesbare meldingen van:

- **dienst uit de capcodes**, niet uit de berichtkop — die kop is niet
  waterdicht, meldkamer Amsterdam-Amstelland stuurt politie-oproepen met "P 1"
- **straatnamen getoetst aan alle 171.664 Nederlandse straatnamen**, dus ook
  "Balatonmeer" en "Het Zand" komen eruit, niet alleen wat op ‑straat eindigt
- **coördinaten met een nauwkeurigheidsniveau** erbij: adres, straat, postcode
  of alleen de woonplaats
- **`incident_id`**, zodat zes oproepen voor één brand als één gebeurtenis te
  herkennen zijn

## Eerlijk over de beperkingen

Eén antenne op één plek. Wat die niet haalt, staat ook niet in deze integratie.
Hoe goed dat gaat wordt gemeten en gepubliceerd: berichten per uur, het aandeel
dat op de kaart komt en de langste stilte staan op
[112hier.nl/ontvangst](https://112hier.nl/ontvangst). Kijk daar even voordat je
er iets op bouwt.

Niet elke regio stuurt een adres mee. In Haaglanden en Amsterdam-Amstelland
heeft ruim 95% van de meldingen een straatnaam; in Brabant-Noord en
Midden- en West-Brabant stuurt de meldkamer alleen de plaatsnaam en is er dus
geen straat om te tonen.

Er zit geen garantie op en geen serviceafspraak. Dit is een hobbyontvanger, geen
C2000-aansluiting — **bouw er niets mee waar levens van afhangen, en bel bij nood 112.**

## De feed zelf

De integratie leest [`https://112hier.nl/feed.json`](https://112hier.nl/feed.json).
Die is vrij te gebruiken, ook zonder Home Assistant: geen sleutel, geen account,
maximaal 30 verzoeken per minuut. Documentatie op
[112hier.nl/feed](https://112hier.nl/feed).

## Licentie

MIT. 112hier is een merk van [Boonstra Works](https://boonstraworks.nl).
