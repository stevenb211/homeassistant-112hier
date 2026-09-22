/**
 * De 112hier-kaart voor je Lovelace-dashboard.
 *
 * Twee sensoren zijn genoeg om automatiseringen op te bouwen, maar ze laten
 * zich slecht lezen: de standaardkaart toont één regel tekst en daaronder een
 * rij attributen. Deze kaart toont de meldingen zoals je ze op een
 * meldkamerscherm zou willen zien — nieuwste boven, kleur per dienst, urgentie
 * ernaast, en hoe lang geleden het was.
 *
 * Hij wordt door de integratie zelf ingeladen, dus je hoeft niets toe te
 * voegen aan je Lovelace-bronnen.
 *
 * Gebruik:
 *   type: custom:112hier-card
 *   entity: sensor.112_haaglanden_meldingen_bewaard
 *   aantal: 8            (optioneel, standaard 8)
 *   alleen_spoed: false  (optioneel)
 *   titel: "112 in de buurt"  (optioneel)
 */

const KLEUR = {
  brandweer: '#ea580c',
  ambulance: '#dc2626',
  politie: '#2563eb',
  knrm: '#0891b2',
};

const ICOON = {
  brandweer: 'mdi:fire-truck',
  ambulance: 'mdi:ambulance',
  politie: 'mdi:car-emergency',
  knrm: 'mdi:ferry',
};

/** "net nu", "4 min", "2 uur" — korter leest op een dashboard beter dan een klok. */
function geleden(iso) {
  if (!iso) return '';
  const sec = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (sec < 60) return 'net nu';
  if (sec < 3600) return `${Math.floor(sec / 60)} min`;
  if (sec < 86400) return `${Math.floor(sec / 3600)} uur`;
  return `${Math.floor(sec / 86400)} d`;
}

function veilig(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

class HierCard extends HTMLElement {
  static getStubConfig(hass) {
    // Bij "kaart toevoegen" meteen de juiste sensor invullen, anders staat de
    // gebruiker tegen een lege kaart aan te kijken en moet hij zelf zoeken.
    const kandidaat = Object.keys(hass.states).find(
      (e) => e.startsWith('sensor.') && hass.states[e].attributes.meldingen,
    );
    return { type: 'custom:112hier-card', entity: kandidaat || '', aantal: 8 };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Kies de sensor "Meldingen bewaard" van 112hier.');
    }
    this._config = { aantal: 8, alleen_spoed: false, ...config };
    this._vorigeSleutel = null;
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
  }

  getCardSize() {
    return 1 + Math.min(this._config.aantal, 8);
  }

  set hass(hass) {
    this._hass = hass;
    this._teken();
  }

  connectedCallback() {
    // De tijden ("4 min") lopen anders pas door als er een nieuwe melding komt.
    this._tik = setInterval(() => this._teken(true), 30000);
  }

  disconnectedCallback() {
    clearInterval(this._tik);
  }

  _teken(alleenTijden = false) {
    if (!this._hass || !this._config) return;
    const staat = this._hass.states[this._config.entity];
    if (!staat) {
      this.shadowRoot.innerHTML = this._omhulsel(
        `<div class="leeg">Sensor <code>${veilig(this._config.entity)}</code> bestaat niet.</div>`,
      );
      return;
    }

    let meldingen = staat.attributes.meldingen || [];
    if (this._config.alleen_spoed) meldingen = meldingen.filter((m) => m.spoed);
    meldingen = meldingen.slice(0, this._config.aantal);

    // Alleen opnieuw opbouwen als er werkelijk iets veranderd is; anders
    // knippert de kaart elke keer dat Home Assistant een update stuurt.
    const sleutel = meldingen.map((m) => m.id).join(',');
    if (alleenTijden && sleutel === this._vorigeSleutel) {
      this.shadowRoot.querySelectorAll('.tijd').forEach((el) => {
        el.textContent = geleden(el.dataset.tijd);
      });
      return;
    }
    this._vorigeSleutel = sleutel;

    const titel = this._config.titel || staat.attributes.friendly_name || '112-meldingen';
    const rijen = meldingen.length
      ? meldingen.map((m) => this._rij(m)).join('')
      : '<div class="leeg">Rustig op dit moment. Er is nog niets binnengekomen dat aan je filters voldoet.</div>';

    this.shadowRoot.innerHTML = this._omhulsel(`
      <div class="kop">
        <span class="naam">${veilig(titel)}</span>
        <span class="telling">${meldingen.length}</span>
      </div>
      <div class="lijst">${rijen}</div>
    `);

    this.shadowRoot.querySelectorAll('.rij').forEach((el) => {
      el.addEventListener('click', () => {
        if (el.dataset.url) window.open(el.dataset.url, '_blank', 'noopener');
      });
    });
  }

  _rij(m) {
    const kleur = KLEUR[m.dienst] || '#64748b';
    const plek = [m.straat, m.plaats].filter(Boolean).join(', ');
    const afstand = m.afstand_km != null ? `${m.afstand_km} km` : '';
    return `
      <div class="rij${m.spoed ? ' spoed' : ''}" data-url="${veilig(m.url || '')}">
        <span class="streep" style="background:${kleur}"></span>
        <div class="inhoud">
          <div class="boven">
            ${m.urgentie ? `<span class="code" style="background:${kleur}">${veilig(m.urgentie)}</span>` : ''}
            <span class="tekst">${veilig(m.tekst || '')}</span>
          </div>
          <div class="onder">
            ${plek ? `<span>${veilig(plek)}</span>` : ''}
            ${afstand ? `<span class="punt">·</span><span>${veilig(afstand)}</span>` : ''}
            ${m.regio ? `<span class="punt">·</span><span>${veilig(m.regio)}</span>` : ''}
          </div>
        </div>
        <span class="tijd" data-tijd="${veilig(m.tijd || '')}">${geleden(m.tijd)}</span>
      </div>`;
  }

  _omhulsel(binnen) {
    return `
      <style>
        ha-card { padding: 12px 0 4px; overflow: hidden; }
        .kop {
          display: flex; align-items: baseline; gap: 8px;
          padding: 0 16px 10px; border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        .naam { font-size: 1.05rem; font-weight: 600; color: var(--primary-text-color); }
        .telling {
          margin-left: auto; font-size: .8rem; color: var(--secondary-text-color);
          background: var(--secondary-background-color, #f1f1f1);
          border-radius: 999px; padding: 1px 8px;
        }
        .lijst { display: flex; flex-direction: column; }
        .rij {
          display: flex; align-items: flex-start; gap: 10px;
          padding: 9px 16px 9px 0; cursor: pointer;
          border-bottom: 1px solid var(--divider-color, #ececec);
        }
        .rij:last-child { border-bottom: none; }
        .rij:hover { background: var(--secondary-background-color, #f7f7f7); }
        .streep { width: 4px; align-self: stretch; border-radius: 0 3px 3px 0; flex: 0 0 4px; }
        .inhoud { flex: 1; min-width: 0; }
        .boven { display: flex; align-items: baseline; gap: 7px; }
        .code {
          flex: 0 0 auto; color: #fff; font-size: .7rem; font-weight: 700;
          letter-spacing: .02em; border-radius: 4px; padding: 1px 5px; white-space: nowrap;
        }
        .tekst {
          color: var(--primary-text-color); font-size: .92rem; line-height: 1.35;
          display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .onder {
          margin-top: 2px; font-size: .78rem; color: var(--secondary-text-color);
          display: flex; flex-wrap: wrap; gap: 4px;
        }
        .punt { opacity: .5; }
        .tijd {
          flex: 0 0 auto; font-size: .75rem; color: var(--secondary-text-color);
          padding-top: 2px; white-space: nowrap;
        }
        .spoed .tekst { font-weight: 600; }
        .leeg {
          padding: 18px 16px; color: var(--secondary-text-color);
          font-size: .88rem; line-height: 1.45;
        }
        code { font-size: .85em; }
      </style>
      <ha-card>${binnen}</ha-card>`;
  }
}

if (!customElements.get('112hier-card')) {
  customElements.define('112hier-card', HierCard);

  // Zo verschijnt de kaart in de lijst bij "Kaart toevoegen" in plaats van dat
  // je de naam uit je hoofd moet typen.
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: '112hier-card',
    name: '112hier — meldingen',
    description: 'De laatste 112-meldingen uit jouw gebied, nieuwste boven.',
    preview: true,
    documentationURL: 'https://github.com/stevenb211/homeassistant-112hier',
  });

  // eslint-disable-next-line no-console
  console.info('%c112hier-card%c geladen', 'color:#ef4444;font-weight:700', '');
}
