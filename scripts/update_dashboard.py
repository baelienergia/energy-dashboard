#!/usr/bin/env python3
"""
Energy Dashboard — Updater giornaliero
Eseguito da GitHub Actions ogni giorno alle 06:30 UTC.

Scarica i dati più recenti, li fonde con lo storico (cache/history.json),
sostituisce i placeholder nel template e produce public/index.html.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ============================================================
# CONFIG
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "template" / "template.html"
OUTPUT_PATH = ROOT / "public" / "index.html"
CACHE_DIR = ROOT / "cache"
HISTORY_PATH = CACHE_DIR / "history.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
(ROOT / "public").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("updater")

MONTHS_IT = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


def month_label(date: datetime) -> str:
    """Es. 'Apr 2026'"""
    return f"{MONTHS_IT[date.month - 1]} {date.year}"


# ============================================================
# CARICAMENTO STORICO (seed iniziale)
# ============================================================
SEED_HISTORY = [
    # [label, F0, F1, F2, F3, psv_smc, partial, brent, ttf, igi, co2, eurusd, disp, cm_peak, cm_off]
    ["Gen 2022", 224.50, 257.19, 242.35, 196.39, 0.910400, False, 83.5, 80.2, 78.0, 84.1, 1.1328, 4.20, 39.799, 1.296],
    ["Feb 2022", 211.69, 224.88, 225.68, 193.65, 0.862000, False, 95.7, 77.3, 75.2, 90.5, 1.1327, 5.80, 39.799, 1.296],
    ["Mar 2022", 308.07, 320.08, 329.12, 286.19, 1.340000, False, 117.9, 128.4, 125.8, 78.9, 1.1013, 4.90, 39.799, 1.296],
    ["Apr 2022", 245.97, 256.23, 266.58, 228.86, 1.060200, False, 104.6, 103.9, 101.2, 82.9, 1.0819, 4.10, 39.799, 1.296],
    ["Mag 2022", 230.06, 237.21, 253.52, 212.33, 0.950600, False, 112.6, 95.8, 93.1, 85.7, 1.0556, 3.85, 39.799, 1.296],
    ["Giu 2022", 271.31, 297.17, 293.31, 241.03, 1.098000, False, 117.0, 120.3, 117.5, 85.4, 1.0566, 3.95, 39.799, 1.296],
    ["Lug 2022", 441.65, 495.24, 473.26, 386.07, 1.829600, False, 104.0, 175.7, 172.5, 80.9, 1.0198, 6.20, 39.799, 1.296],
    ["Ago 2022", 543.15, 553.96, 602.78, 503.55, 2.471465, False, 99.6, 235.2, 232.0, 89.1, 1.0123, 4.10, 39.799, 1.296],
    ["Set 2022", 429.92, 460.24, 471.34, 382.07, 1.941062, False, 91.6, 187.6, 184.2, 72.7, 0.9900, 4.00, 39.799, 1.296],
    ["Ott 2022", 211.50, 235.87, 242.14, 177.15, 0.835182, False, 92.8, 120.3, 118.5, 72.4, 0.9830, 3.90, 39.799, 1.296],
    ["Nov 2022", 224.51, 272.35, 240.71, 181.43, 0.975849, False, 87.9, 115.2, 113.0, 74.8, 1.0205, 4.30, 39.799, 1.296],
    ["Dic 2022", 294.91, 360.73, 309.96, 244.94, 1.247659, False, 79.9, 132.6, 130.5, 85.1, 1.0605, 5.40, 39.799, 1.296],
    ["Gen 2023", 174.49, 196.24, 184.24, 155.10, 0.731604, False, 82.2, 68.9, 67.0, 82.6, 1.0780, 6.95, 46.620, 1.510],
    ["Feb 2023", 161.07, 174.33, 172.89, 144.22, 0.608549, False, 82.6, 54.8, 53.2, 84.0, 1.0722, 8.20, 46.620, 1.510],
    ["Mar 2023", 136.38, 139.78, 151.95, 124.66, 0.498408, False, 77.3, 47.1, 45.8, 87.5, 1.0702, 5.80, 46.620, 1.510],
    ["Apr 2023", 134.97, 135.55, 152.05, 126.40, 0.475300, False, 83.4, 41.9, 40.5, 89.9, 1.0968, 4.95, 46.620, 1.510],
    ["Mag 2023", 105.73, 109.99, 119.81, 95.11, 0.363400, False, 75.7, 31.1, 30.0, 86.0, 1.0874, 4.60, 46.620, 1.510],
    ["Giu 2023", 105.34, 108.20, 117.96, 96.61, 0.354598, False, 74.9, 33.5, 32.2, 83.8, 1.0876, 4.75, 46.620, 1.510],
    ["Lug 2023", 112.09, 114.91, 122.32, 104.34, 0.336170, False, 80.1, 29.5, 28.4, 85.8, 1.1121, 7.85, 46.620, 1.510],
    ["Ago 2023", 111.89, 110.26, 128.12, 104.48, 0.352390, False, 86.2, 33.3, 32.0, 87.3, 1.0920, 4.80, 46.620, 1.510],
    ["Set 2023", 115.70, 118.55, 128.08, 105.99, 0.392680, False, 94.0, 36.1, 34.8, 84.8, 1.0672, 4.70, 46.620, 1.510],
    ["Ott 2023", 134.26, 144.56, 148.63, 119.08, 0.467879, False, 90.8, 46.2, 44.9, 82.0, 1.0566, 4.85, 46.620, 1.510],
    ["Nov 2023", 121.74, 139.73, 128.26, 105.30, 0.450730, False, 82.9, 45.5, 44.2, 77.1, 1.0881, 5.10, 46.620, 1.510],
    ["Dic 2023", 115.46, 131.87, 118.69, 105.36, 0.384870, False, 77.1, 36.3, 35.0, 72.5, 1.0909, 6.20, 46.620, 1.510],
    ["Gen 2024", 99.16, 109.65, 105.07, 89.06, 0.330600, False, 80.1, 30.4, 29.2, 68.5, 1.0874, 7.40, 44.900, 2.767],
    ["Feb 2024", 87.63, 96.15, 94.92, 76.81, 0.294950, False, 83.5, 26.5, 25.3, 58.7, 1.0780, 8.85, 44.900, 2.767],
    ["Mar 2024", 88.86, 94.93, 94.62, 81.32, 0.304590, False, 85.4, 27.5, 26.4, 61.7, 1.0875, 6.40, 44.900, 2.767],
    ["Apr 2024", 86.80, 85.57, 101.29, 80.54, 0.323170, False, 89.9, 28.9, 27.7, 68.5, 1.0722, 5.95, 44.900, 2.767],
    ["Mag 2024", 94.88, 94.66, 111.48, 86.24, 0.349680, False, 82.0, 31.8, 30.5, 72.8, 1.0815, 5.80, 44.900, 2.767],
    ["Giu 2024", 103.17, 103.81, 116.16, 95.43, 0.382350, False, 82.3, 34.2, 32.9, 67.8, 1.0760, 5.95, 44.900, 2.767],
    ["Lug 2024", 112.32, 108.67, 130.63, 104.78, 0.375040, False, 85.1, 33.0, 31.6, 67.5, 1.0835, 8.50, 44.900, 2.767],
    ["Ago 2024", 128.44, 121.67, 147.95, 122.19, 0.429520, False, 78.9, 37.8, 36.3, 68.4, 1.1015, 6.10, 44.900, 2.767],
    ["Set 2024", 117.13, 122.33, 131.74, 105.65, 0.411190, False, 73.5, 36.2, 34.7, 64.0, 1.1118, 5.95, 44.900, 2.767],
    ["Ott 2024", 116.69, 123.78, 126.63, 105.27, 0.432690, False, 74.9, 39.1, 37.5, 64.5, 1.0876, 6.10, 44.900, 2.767],
    ["Nov 2024", 130.89, 145.59, 137.38, 117.13, 0.477990, False, 74.6, 44.6, 43.0, 66.5, 1.0597, 6.45, 44.900, 2.767],
    ["Dic 2024", 135.06, 158.47, 145.93, 115.81, 0.504170, False, 74.0, 43.9, 42.3, 71.8, 1.0476, 7.65, 44.900, 2.767],
    ["Gen 2025", 143.03, 158.32, 151.61, 128.54, 0.528080, False, 78.5, 49.2, 47.4, 77.5, 1.0387, 11.40, 59.050, 3.350],
    ["Feb 2025", 150.36, 157.64, 158.95, 139.91, 0.560590, False, 75.5, 50.5, 48.6, 73.9, 1.0412, 13.20, 59.050, 3.350],
    ["Mar 2025", 120.55, 121.68, 134.86, 111.65, 0.450460, False, 72.4, 41.1, 39.4, 70.5, 1.0815, 7.80, 59.050, 3.350],
    ["Apr 2025", 99.85, 95.84, 115.08, 95.05, 0.398350, False, 67.9, 35.0, 33.4, 68.2, 1.1070, 6.60, 59.050, 3.350],
    ["Mag 2025", 93.58, 89.09, 110.64, 87.11, 0.403990, False, 65.0, 34.3, 32.8, 68.0, 1.1276, 6.45, 59.050, 3.350],
    ["Giu 2025", 111.78, 113.06, 126.76, 103.63, 0.399710, False, 72.8, 34.8, 33.3, 71.9, 1.1423, 7.10, 59.050, 3.350],
    ["Lug 2025", 113.13, 108.96, 127.10, 108.49, 0.388520, False, 68.9, 33.5, 32.0, 72.3, 1.1681, 12.60, 59.050, 3.350],
    ["Ago 2025", 108.79, 105.58, 117.97, 106.04, 0.377180, False, 67.5, 31.8, 30.4, 73.0, 1.1650, 6.80, 59.050, 3.350],
    ["Set 2025", 109.08, 109.59, 120.93, 101.88, 0.369520, False, 66.9, 31.5, 30.1, 74.1, 1.1754, 6.65, 59.050, 3.350],
    ["Ott 2025", 111.04, 117.83, 121.66, 99.48, 0.353959, False, 64.0, 31.2, 29.8, 76.2, 1.1615, 6.80, 59.050, 3.350],
    ["Nov 2025", 117.09, 129.59, 124.02, 105.51, 0.345300, False, 63.5, 32.1, 30.7, 74.8, 1.1553, 7.20, 59.050, 3.350],
    ["Dic 2025", 115.49, 130.09, 119.98, 104.52, 0.324670, False, 69.0, 31.3, 29.9, 73.4, 1.1432, 8.95, 59.050, 3.350],
    ["Gen 2026", 132.66, 151.26, 137.41, 118.29, 0.404227, False, 78.0, 38.2, 37.9, 78.0, 1.0483, 13.10, 61.200, 4.200],
    ["Feb 2026", 114.41, 122.28, 119.84, 105.30, 0.377233, False, 72.5, 35.1, 35.1, 76.2, 1.0620, 14.85, 61.200, 4.200],
    ["Mar 2026", 143.40, 143.02, 153.91, 138.00, 0.561332, False, 96.5, 52.1, 51.3, 75.0, 1.0730, 8.90, 61.200, 4.200],
]


def load_history() -> list:
    """Carica history.json se esiste, altrimenti usa SEED_HISTORY."""
    if HISTORY_PATH.exists():
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info(f"History caricata: {len(data)} mesi")
            return data
        except Exception as e:
            log.warning(f"Impossibile caricare history: {e} — uso seed")
    log.info(f"History non presente, uso seed iniziale ({len(SEED_HISTORY)} mesi)")
    return [list(r) for r in SEED_HISTORY]


def save_history(history: list) -> None:
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    log.info(f"History salvata: {HISTORY_PATH}")


# ============================================================
# FETCHERS
# ============================================================

def fetch_eurusd() -> float | None:
    """EUR/USD via Frankfurter API (gratis, no key)."""
    try:
        r = requests.get(
            "https://api.frankfurter.app/latest?from=EUR&to=USD",
            timeout=10,
        )
        r.raise_for_status()
        rate = r.json().get("rates", {}).get("USD")
        log.info(f"EUR/USD: {rate}")
        return float(rate) if rate else None
    except Exception as e:
        log.error(f"EUR/USD fetch fallito: {e}")
        return None


def fetch_brent() -> float | None:
    """Brent via Yahoo Finance (BZ=F)."""
    try:
        import yfinance as yf
        t = yf.Ticker("BZ=F")
        h = t.history(period="5d", interval="1d")
        if h.empty:
            return None
        val = float(h["Close"].iloc[-1])
        log.info(f"Brent: {val}")
        return val
    except ImportError:
        log.warning("yfinance non disponibile, skip Brent")
        return None
    except Exception as e:
        log.error(f"Brent fetch fallito: {e}")
        return None


def fetch_ttf() -> float | None:
    """TTF via Yahoo Finance (TTF=F)."""
    try:
        import yfinance as yf
        t = yf.Ticker("TTF=F")
        h = t.history(period="5d", interval="1d")
        if h.empty:
            return None
        val = float(h["Close"].iloc[-1])
        log.info(f"TTF: {val}")
        return val
    except Exception as e:
        log.error(f"TTF fetch fallito: {e}")
        return None


# ============================================================
# AGGIORNAMENTO MESE CORRENTE
# ============================================================

def update_current_month(history: list) -> list:
    """
    Aggiorna l'ultimo mese (parziale, MTD) con i valori live più recenti.
    Se il mese corrente non è in history, lo aggiunge.
    """
    today = datetime.now()
    current_label = month_label(today)
    
    # Live data
    eurusd = fetch_eurusd()
    brent = fetch_brent()
    ttf = fetch_ttf()
    
    # Cerca il mese corrente
    last_row = history[-1] if history else None
    
    if last_row and last_row[0] == current_label:
        log.info(f"Aggiorno mese corrente: {current_label}")
        # Aggiorna SOLO i valori che abbiamo recuperato (gli altri restano i precedenti)
        if eurusd is not None:
            last_row[11] = round(eurusd, 4)
        if brent is not None:
            last_row[7] = round(brent, 2)
        if ttf is not None:
            last_row[8] = round(ttf, 2)
        last_row[6] = True  # è ancora parziale
    else:
        # Nuovo mese: copia gli ultimi valori non-parziali come baseline
        log.info(f"Aggiungo nuovo mese parziale: {current_label}")
        baseline = history[-1] if history else SEED_HISTORY[-1]
        new_row = list(baseline)
        new_row[0] = current_label
        new_row[6] = True  # parziale
        if eurusd is not None:
            new_row[11] = round(eurusd, 4)
        if brent is not None:
            new_row[7] = round(brent, 2)
        if ttf is not None:
            new_row[8] = round(ttf, 2)
        # Marca il mese precedente come definitivo (toglie parziale)
        if last_row and last_row[6]:
            last_row[6] = False
            log.info(f"Mese {last_row[0]} marcato come definitivo")
        history.append(new_row)
    
    return history


# ============================================================
# RENDER TEMPLATE
# ============================================================

def render_template(history: list) -> str:
    """Sostituisce i placeholder nel template con dati e data correnti."""
    if not TEMPLATE_PATH.exists():
        log.error(f"Template non trovato: {TEMPLATE_PATH}")
        sys.exit(1)
    
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    
    # Serializza il dataset come JSON (ricordando che JS usa true/false minuscoli)
    data_json = json.dumps(history, ensure_ascii=False)
    
    today = datetime.now()
    months_short_it = ["gen", "feb", "mar", "apr", "mag", "giu",
                       "lug", "ago", "set", "ott", "nov", "dic"]
    today_str = f"{today.day} {months_short_it[today.month - 1]} {today.year}"
    
    output = template.replace("__DATA_PLACEHOLDER__", data_json)
    output = output.replace("__DATE_PLACEHOLDER__", today_str)
    
    return output


# ============================================================
# MAIN
# ============================================================

def main():
    log.info("=" * 60)
    log.info(f"Update Energy Dashboard — {datetime.now().isoformat()}")
    log.info("=" * 60)
    
    # 1. Carica storico
    history = load_history()
    
    # 2. Aggiorna mese corrente con valori live
    history = update_current_month(history)
    
    # 3. Salva storico
    save_history(history)
    
    # 4. Renderizza template e scrivi public/index.html
    html = render_template(history)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    log.info(f"Output scritto: {OUTPUT_PATH} ({len(html):,} bytes)")
    
    log.info("✅ Aggiornamento completato")


if __name__ == "__main__":
    main()
