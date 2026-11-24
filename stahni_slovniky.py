"""Jednorázově stáhne Hunspell slovníky cs_CZ a en_US z repozitáře LibreOffice.

Pak už kontrola pravopisu (metriky.py) běží úplně offline.
Slovníky jsou v .gitignore (mají vlastní licence a jdou kdykoli stáhnout znovu).

Stahování jde přes internet, proto tady školní proxy ponecháváme
(urllib ji převezme z proměnných prostředí).
"""
import urllib.request
from pathlib import Path

ZAKLAD = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/"
SOUBORY = {
    "cs_CZ.aff": "cs_CZ/cs_CZ.aff",
    "cs_CZ.dic": "cs_CZ/cs_CZ.dic",
    "en_US.aff": "en/en_US.aff",
    "en_US.dic": "en/en_US.dic",
    # britský pravopis (colour, organise) nebereme jako chybu
    "en_GB.aff": "en/en_GB.aff",
    "en_GB.dic": "en/en_GB.dic",
}

cil = Path(__file__).parent / "slovniky"
cil.mkdir(exist_ok=True)

for nazev, cesta in SOUBORY.items():
    soubor = cil / nazev
    if soubor.exists() and soubor.stat().st_size > 0:
        print(f"{nazev}: už existuje, přeskakuji")
        continue
    print(f"{nazev}: stahuji {ZAKLAD + cesta}")
    urllib.request.urlretrieve(ZAKLAD + cesta, soubor)
    print(f"  {soubor.stat().st_size / 1024:.0f} KiB")

print("Hotovo, slovníky jsou ve složce", cil)
