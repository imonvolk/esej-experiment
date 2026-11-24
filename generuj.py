"""Vygeneruje eseje pro všechny kombinace téma × jazyk × model × varianta.

Každá esej se uloží do vystupy/<model>__<varianta>__<jazyk>__t<id>.txt
a měření (čas, tokeny/s, ...) se připíše do vysledky/generace.jsonl.

Hotové eseje se přeskakují, takže skript jde přerušit (Ctrl+C) a spustit znovu.

Příklady:
    python generuj.py                       # vše (40 esejí)
    python generuj.py --tema 1 --tema 2 --tema 3   # jen vybraná témata (24 esejí)
    python generuj.py --limit 1             # rychlý test: 1 esej
    python generuj.py --model gemma3 --jazyk cs --tema 1
    python generuj.py --prepsat             # vygenerovat znovu i hotové
"""
import argparse
import json
import platform
import time
from datetime import datetime

from spolecne import (JAZYKY, MODELY, VARIANTY, VYSLEDKY, VYSTUPY, klient,
                      nacti_temata, nazev_souboru)

SEED = 42
# Pojistka jen pro základní variantu, která nemá v Modelfile num_predict:
# bez ní by model teoreticky mohl generovat donekonečna. Customizované
# varianty mají vlastní limit 1024 v Modelfile.
POJISTKA_ZAKLADNI = 1500


def zapis_prostredi(k):
    try:
        verze = k._client.get("/api/version").json().get("version")
    except Exception:
        verze = None
    info = {
        "datum": datetime.now().isoformat(timespec="seconds"),
        "ollama_verze": verze,
        "os": platform.platform(),
        "procesor": platform.processor(),
        "python": platform.python_version(),
        "seed": SEED,
        "pojistka_num_predict_zakladni": POJISTKA_ZAKLADNI,
    }
    with open(VYSLEDKY / "prostredi.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", choices=list(MODELY), action="append")
    p.add_argument("--varianta", choices=VARIANTY, action="append")
    p.add_argument("--jazyk", choices=JAZYKY, action="append")
    p.add_argument("--tema", type=int, action="append")
    p.add_argument("--limit", type=int, help="vygeneruj nejvýš N esejí")
    p.add_argument("--prepsat", action="store_true", help="přegeneruj i hotové eseje")
    a = p.parse_args()

    VYSTUPY.mkdir(exist_ok=True)
    VYSLEDKY.mkdir(exist_ok=True)
    data = nacti_temata()
    delka = data["cilova_delka_slov"]

    k = klient()
    try:
        dostupne = {m.model for m in k.list().models}
    except Exception as e:
        raise SystemExit(f"Nedá se připojit k Ollamě na {k._client.base_url}: {e}\n"
                         "Běží server (ollama.exe serve)?")
    zapis_prostredi(k)

    # Pořadí: téma -> jazyk -> model -> varianta. Když se běh přeruší po
    # dokončeném tématu, mají všechny kombinace model/varianta/jazyk stejná
    # témata a data zůstanou vyvážená (cenou je častější přepínání modelů).
    ukoly = []
    for t in data["temata"]:
        if a.tema and t["id"] not in a.tema:
            continue
        for jazyk in a.jazyk or JAZYKY:
            for model in a.model or MODELY:
                for varianta in a.varianta or VARIANTY:
                    jmeno = MODELY[model][varianta]
                    if jmeno not in dostupne and f"{jmeno}:latest" not in dostupne:
                        print(f"! Model {jmeno} v Ollamě chybí, přeskakuji")
                        continue
                    soubor = VYSTUPY / nazev_souboru(model, varianta, jazyk, t["id"])
                    if soubor.exists() and not a.prepsat:
                        continue
                    ukoly.append((model, varianta, jmeno, jazyk, t, soubor))
    if a.limit:
        ukoly = ukoly[: a.limit]
    print(f"K vygenerování: {len(ukoly)} esejí")

    for i, (model, varianta, jmeno, jazyk, t, soubor) in enumerate(ukoly, 1):
        zadani = data["zadani_sablona"][jazyk].format(tema=t[jazyk], delka=delka)
        moznosti = {"seed": SEED}
        if varianta == "zakladni":
            moznosti["num_predict"] = POJISTKA_ZAKLADNI

        print(f"[{i}/{len(ukoly)}] {jmeno:15} {jazyk} téma {t['id']} ... ", end="", flush=True)
        start = time.perf_counter()
        r = k.chat(model=jmeno, messages=[{"role": "user", "content": zadani}], options=moznosti)
        cas = time.perf_counter() - start

        text = r.message.content.strip()
        soubor.write_text(text + "\n", encoding="utf-8")

        eval_s = (r.eval_duration or 0) / 1e9
        zaznam = {
            "model": model, "varianta": varianta, "ollama_model": jmeno,
            "jazyk": jazyk, "tema_id": t["id"], "zadani": zadani,
            "soubor": soubor.name,
            "eval_count": r.eval_count,
            "eval_duration_s": round(eval_s, 3),
            "tokeny_za_s": round(r.eval_count / eval_s, 2) if eval_s else None,
            "prompt_eval_count": r.prompt_eval_count,
            "prompt_eval_duration_s": round((r.prompt_eval_duration or 0) / 1e9, 3),
            "load_duration_s": round((r.load_duration or 0) / 1e9, 3),
            "total_duration_s": round((r.total_duration or 0) / 1e9, 3),
            "cas_celkem_s": round(cas, 2),
            "done_reason": r.done_reason,   # "length" = useknuto limitem tokenů
            "seed": SEED, "options": moznosti,
            "cas_zapisu": datetime.now().isoformat(timespec="seconds"),
        }
        with open(VYSLEDKY / "generace.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(zaznam, ensure_ascii=False) + "\n")
        print(f"{r.eval_count} tok, {zaznam['tokeny_za_s']} tok/s, {cas:.0f} s, {r.done_reason}")


if __name__ == "__main__":
    main()
