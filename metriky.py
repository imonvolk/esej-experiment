"""Automatické metriky pro všechny eseje ve vystupy/ -> vysledky/metriky.csv

Metriky:
- slov, odchylka_pct      počet slov a odchylka od cílové délky v % (se znaménkem)
- odstavcu, nadpisu       odstavce = neprázdné řádky, které nejsou nadpis
- chyb_na_100_slov        slova, která Hunspell (cs_CZ / en_US) nezná, na 100 slov
- podil_spatny_jazyk      podíl vět v jiném než zadaném jazyce
                          (langdetect + kontrola slovníkem, viz README)
- podil_spatny_jazyk_ld   totéž jen podle langdetect (pro srovnání)
- markdown                obsahuje text Markdown (**, #, odrážky)?

Vše běží offline (slovníky stáhne jednou stahni_slovniky.py).
"""
import re

import pandas as pd
from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException
from spylls.hunspell import Dictionary

from spolecne import (HUNSPELL, SLOVNIKY, VYSLEDKY, VYSTUPY, nacti_temata,
                      nadpisy, odstavce, rozloz_nazev, slova, vety)

DetectorFactory.seed = 0          # langdetect je jinak nedeterministický
MIN_SLOV_VETY = 3                 # kratší věty langdetect neumí spolehlivě
PRAH_SLOVNIK = 0.7                # věta se slovy z >= 70 % ve slovníku = správný jazyk

_slovniky = {}


class Slovnik:
    """Jeden nebo více Hunspell slovníků; slovo je OK, když ho zná některý."""

    def __init__(self, nazvy):
        self.d = []
        for n in nazvy:
            cesta = SLOVNIKY / n
            if not cesta.with_suffix(".dic").exists():
                raise SystemExit("Chybí Hunspell slovníky, spusť: python stahni_slovniky.py")
            self.d.append(Dictionary.from_files(str(cesta)))

    def lookup(self, slovo):
        return any(d.lookup(slovo) for d in self.d)


def slovnik(jazyk):
    if jazyk not in _slovniky:
        _slovniky[jazyk] = Slovnik(HUNSPELL[jazyk])
    return _slovniky[jazyk]


def slovo_ok(slovo, d):
    slovo = slovo.replace("’", "'")
    if d.lookup(slovo):
        return True
    if "-" in slovo:                        # "e-books", "well-being" -> po částech
        return all(d.lookup(c) for c in slovo.split("-") if c)
    if slovo.isupper() and len(slovo) <= 5:  # zkratky: AI, IT, EU
        return True
    return False


def jazyk_vety(veta, jazyk):
    """Vrátí (spatne_podle_langdetect, spatne_finalne, detekovany_jazyk)."""
    try:
        top = detect_langs(veta)[0].lang
    except LangDetectException:
        return False, False, None
    if top == jazyk:
        return False, False, top
    # langdetect plete krátké české věty se slovenštinou apod. -> ověř slovníkem
    sl = slova(veta)
    d = slovnik(jazyk)
    podil_ok = sum(slovo_ok(s, d) for s in sl) / len(sl) if sl else 1
    return True, podil_ok < PRAH_SLOVNIK, top


def zmer(text, jazyk, cil):
    sl = slova(text)
    d = slovnik(jazyk)
    chybna = [s for s in sl if not slovo_ok(s, d)]

    vety_hodnocene = [v for v in vety(text) if len(slova(v)) >= MIN_SLOV_VETY]
    vysl = [jazyk_vety(v, jazyk) for v in vety_hodnocene]
    spatne_ld = sum(r[0] for r in vysl)
    spatne = sum(r[1] for r in vysl)
    cizi = sorted({r[2] for r in vysl if r[1] and r[2]})
    n_vet = len(vety_hodnocene) or 1

    return {
        "slov": len(sl),
        "odchylka_slov": len(sl) - cil,
        "odchylka_pct": round((len(sl) - cil) / cil * 100, 1),
        "abs_odchylka_pct": round(abs(len(sl) - cil) / cil * 100, 1),
        "odstavcu": len(odstavce(text)),
        "nadpisu": len(nadpisy(text)),
        "chyb": len(chybna),
        "chyb_na_100_slov": round(len(chybna) / len(sl) * 100, 2) if sl else None,
        "vet": len(vety_hodnocene),
        "vet_spatny_jazyk": spatne,
        "podil_spatny_jazyk": round(spatne / n_vet, 3),
        "podil_spatny_jazyk_ld": round(spatne_ld / n_vet, 3),
        "cizi_jazyky": ",".join(cizi),
        "markdown": bool(re.search(r"\*\*|^#|^\s*[-*•]\s", text, re.M)),
        "chybna_slova": ", ".join(chybna[:30]),
    }


def main():
    cil = nacti_temata()["cilova_delka_slov"]
    soubory = sorted(VYSTUPY.glob("*.txt"))
    if not soubory:
        raise SystemExit("Ve vystupy/ nejsou žádné eseje, nejdřív spusť generuj.py")
    radky = []
    for s in soubory:
        model, varianta, jazyk, tema_id = rozloz_nazev(s.name)
        m = zmer(s.read_text(encoding="utf-8"), jazyk, cil)
        radky.append({"model": model, "varianta": varianta, "jazyk": jazyk,
                      "tema_id": tema_id, "soubor": s.name, **m})
        print(f"{s.name:35} {m['slov']:4} slov  {m['chyb_na_100_slov']:5} chyb/100  "
              f"{m['podil_spatny_jazyk']:.0%} cizí jazyk  {m['odstavcu']} odst.")
    VYSLEDKY.mkdir(exist_ok=True)
    pd.DataFrame(radky).to_csv(VYSLEDKY / "metriky.csv", index=False, encoding="utf-8-sig")
    print(f"\nUloženo: {VYSLEDKY / 'metriky.csv'} ({len(radky)} esejí)")


if __name__ == "__main__":
    main()
