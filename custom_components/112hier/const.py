"""Constanten voor de 112hier-integratie."""

from datetime import timedelta

DOMAIN = "112hier"

# Waar de feed staat. Instelbaar, zodat je desgewenst je eigen ontvanger kunt
# gebruiken zonder de code aan te passen.
DEFAULT_BASIS = "https://112hier.nl"
FEED_PAD = "/feed.json"

# De feed staat 30 verzoeken per minuut toe. Elke 30 seconden kijken is ruim
# binnen die grens en snel genoeg: een uitruk duurt minuten, geen seconden.
DEFAULT_INTERVAL = timedelta(seconds=30)
MIN_INTERVAL_SECONDEN = 15

CONF_BASIS = "basis"
CONF_REGIOS = "regios"
CONF_DIENSTEN = "diensten"
CONF_PLAATS = "plaats"
CONF_STRAAL = "straal"
CONF_ALLEEN_SPOED = "alleen_spoed"
CONF_INTERVAL = "interval"
# Je eigen kazerne of post volgen. Oproepen hiervoor komen altijd door, ook
# buiten je regio en buiten de diensten die je koos — dat is het hele punt.
CONF_CAPCODES = "capcodes"
CONF_BEVAT = "bevat"

# Urgenties die als spoed tellen. A0 is de hoogste ambulance-urgentie en hoort
# er dus bij — die ontbrak lang in dit soort lijstjes omdat hij zeldzaam is.
SPOED_CODES = {"A0", "A1", "P 1", "PRIO 1"}

DIENSTEN = ["brandweer", "ambulance", "politie", "knrm"]

# Het event dat wij op de bus zetten bij elke nieuwe melding. Hier hang je je
# automatiseringen aan.
EVENT_MELDING = "112hier_melding"

ATTRIBUTIE = "Gegevens van 112hier.nl"
