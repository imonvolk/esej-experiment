"""Připraví SLEPÉ hodnocení esejí.

Vytvoří:
  hodnoceni/eseje_k_hodnoceni.md   eseje pod náhodnými kódy (E01, E02, ...) bez názvů modelů
  hodnoceni/hodnotici_list.csv     tabulka k vyplnění (Excel: středníky, UTF-8)
  hodnoceni/klic/klic.json         kód -> model a varianta  (NEOTVÍRAT před hodnocením!)

Pořadí je náhodné, eseje jsou jen seřazené podle jazyka (ať se nepřepíná).
Rubrika: 1 = velmi špatné ... 5 = výborné.

    python priprav_hodnoceni.py            # nový list (nepřepíše už vyplněný)
    python priprav_hodnoceni.py --prepsat  # vytvořit znovu (smaže vyplněné hodnocení!)
"""
import argparse
import csv
import json
import random
import secrets

from spolecne import HODNOCENI, VYSTUPY, nacti_temata, rozloz_nazev

KRITERIA = {
    "gramatika": "pravopis, tvarosloví, skladba; text zní jako od rodilého mluvčího",
    "srozumitelnost": "myšlenky jsou jasné, navazují na sebe, text se dobře čte",
    "drzeni_tematu": "text odpovídá zadanému tématu a nesklouzává jinam",
    "struktura": "titulek, úvod, rozvinutí v odstavcích, závěr",
}
JAZYK_NAZEV = {"cs": "čeština", "en": "angličtina"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prepsat", action="store_true")
    a = p.parse_args()

    list_csv = HODNOCENI / "hodnotici_list.csv"
    if list_csv.exists() and not a.prepsat:
        raise SystemExit(f"{list_csv} už existuje. Pokud ho opravdu chceš přepsat "
                         "(a ztratit vyplněné hodnocení), použij --prepsat.")

    temata = {t["id"]: t for t in nacti_temata()["temata"]}
    eseje = []
    for s in sorted(VYSTUPY.glob("*.txt")):
        model, varianta, jazyk, tema_id = rozloz_nazev(s.name)
        eseje.append({"model": model, "varianta": varianta, "jazyk": jazyk,
                      "tema_id": tema_id, "soubor": s.name,
                      "text": s.read_text(encoding="utf-8").strip()})
    if not eseje:
        raise SystemExit("Ve vystupy/ nejsou žádné eseje.")

    seed = secrets.randbelow(10**9)        # náhodné míchání; seed se uloží do klíče
    rng = random.Random(seed)
    rng.shuffle(eseje)
    eseje.sort(key=lambda e: e["jazyk"])   # stabilní řazení: uvnitř jazyka zůstane náhodně

    (HODNOCENI / "klic").mkdir(parents=True, exist_ok=True)
    klic = {}
    md = ["# Eseje k hodnocení (slepé hodnocení)", "",
          "Ke každé eseji vyplň v `hodnotici_list.csv` známky **1–5** (5 = výborné):", ""]
    md += [f"- **{k}**: {popis}" for k, popis in KRITERIA.items()]
    md += ["", "Hodnoť každou esej samostatně, nesnaž se hádat, který model ji napsal.",
           "Text je přesně tak, jak ho model vrátil (včetně případného Markdownu).", ""]

    with open(list_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["kod", "jazyk", "tema_id", *KRITERIA, "poznamka"])
        for i, e in enumerate(eseje, 1):
            kod = f"E{i:02d}"
            klic[kod] = {k: e[k] for k in ("model", "varianta", "jazyk", "tema_id", "soubor")}
            w.writerow([kod, e["jazyk"], e["tema_id"], *[""] * len(KRITERIA), ""])
            tema = temata[e["tema_id"]][e["jazyk"]]
            md += ["---", "", f"## {kod} · {JAZYK_NAZEV[e['jazyk']]} · téma {e['tema_id']}",
                   "", f"*Zadání:* {tema}", "", "~~~~text", e["text"], "~~~~", ""]

    (HODNOCENI / "eseje_k_hodnoceni.md").write_text("\n".join(md), encoding="utf-8")
    with open(HODNOCENI / "klic" / "klic.json", "w", encoding="utf-8") as f:
        json.dump({"seed": seed, "eseje": klic}, f, ensure_ascii=False, indent=2)

    print(f"Připraveno {len(eseje)} esejí.")
    print(f"  čti:      {HODNOCENI / 'eseje_k_hodnoceni.md'}")
    print(f"  vyplň:    {list_csv}")
    print(f"  klíč:     {HODNOCENI / 'klic' / 'klic.json'}  (neotvírej před hodnocením)")
    print("Po vyplnění spusť: python odkryj.py")


if __name__ == "__main__":
    main()
