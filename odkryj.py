"""Odkryje modely ve vyplněném hodnoticím listu a spojí hodnocení s metrikami.

Vstup:  hodnoceni/hodnotici_list.csv (vyplněný), hodnoceni/klic/klic.json,
        vysledky/metriky.csv (z metriky.py), vysledky/generace.jsonl
Výstup: vysledky/spojene.csv  (jedna řádka = jedna esej, všechno dohromady)

    python odkryj.py
    python odkryj.py --list cesta/k/jinemu_listu.csv
"""
import argparse
import json

import pandas as pd

from priprav_hodnoceni import KRITERIA
from spolecne import HODNOCENI, VYSLEDKY

KLIC = ["model", "varianta", "jazyk", "tema_id"]


def nacti_generace():
    cesta = VYSLEDKY / "generace.jsonl"
    if not cesta.exists():
        return None
    g = pd.read_json(cesta, lines=True)
    # při opakovaném generování platí poslední záznam
    return g.drop_duplicates(subset=KLIC, keep="last")[
        KLIC + ["eval_count", "tokeny_za_s", "cas_celkem_s", "done_reason"]]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--list", default=HODNOCENI / "hodnotici_list.csv")
    a = p.parse_args()

    # sep=None: Excel může soubor uložit se středníky i čárkami
    h = pd.read_csv(a.list, sep=None, engine="python", encoding="utf-8-sig", dtype={"kod": str})
    h = h.drop(columns=["jazyk", "tema_id"], errors="ignore")

    chyby = []
    for k in KRITERIA:
        h[k] = pd.to_numeric(h[k], errors="coerce")
        spatne = h[h[k].isna() | ~h[k].between(1, 5)]
        chyby += [f"{r.kod}: {k}" for r in spatne.itertuples()]
    if chyby:
        print("Pozor, chybějící nebo neplatné známky (mimo 1–5):")
        print("  " + ", ".join(chyby[:40]) + (" ..." if len(chyby) > 40 else ""))
        print("Tyto buňky se do průměrů nezapočítají.\n")

    with open(HODNOCENI / "klic" / "klic.json", encoding="utf-8") as f:
        klic = pd.DataFrame.from_dict(json.load(f)["eseje"], orient="index")
    klic.index.name = "kod"
    spojene = klic.reset_index().merge(h, on="kod", how="left")
    spojene["hodnoceni_prumer"] = spojene[list(KRITERIA)].mean(axis=1)

    metriky = VYSLEDKY / "metriky.csv"
    if metriky.exists():
        m = pd.read_csv(metriky, encoding="utf-8-sig").drop(columns=["soubor"])
        spojene = spojene.merge(m, on=KLIC, how="left")
    else:
        print("vysledky/metriky.csv chybí, spusť nejdřív metriky.py (spojuji jen hodnocení)")
    g = nacti_generace()
    if g is not None:
        spojene = spojene.merge(g, on=KLIC, how="left")

    spojene = spojene.sort_values(KLIC)
    spojene.to_csv(VYSLEDKY / "spojene.csv", index=False, encoding="utf-8-sig")
    print(f"Uloženo: {VYSLEDKY / 'spojene.csv'} ({len(spojene)} esejí)\n")
    print(spojene.groupby(["jazyk", "model", "varianta"])[[*KRITERIA, "hodnoceni_prumer"]]
          .mean().round(2).to_string())


if __name__ == "__main__":
    main()
