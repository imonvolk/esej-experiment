"""Sdílené cesty, konfigurace a funkce pro práci s textem."""
import json
import re
from pathlib import Path

KOREN = Path(__file__).parent
DATA = KOREN / "data"
VYSTUPY = KOREN / "vystupy"          # vygenerované eseje (.txt)
VYSLEDKY = KOREN / "vysledky"        # měření, metriky, souhrny, grafy
HODNOCENI = KOREN / "hodnoceni"      # slepé hodnocení
SLOVNIKY = KOREN / "slovniky"        # Hunspell slovníky (ne v gitu)

OLLAMA_HOST = "http://localhost:11434"

# Název modelu v experimentu -> jméno v Ollamě pro obě varianty
MODELY = {
    "gemma3": {"zakladni": "gemma3:4b", "custom": "gemma3-esej"},
    "llama3.2": {"zakladni": "llama3.2:3b", "custom": "llama3.2-esej"},
}
VARIANTY = ["zakladni", "custom"]
JAZYKY = ["cs", "en"]

# Slovo je správně, když ho zná aspoň jeden ze slovníků daného jazyka
HUNSPELL = {"cs": ["cs_CZ"], "en": ["en_US", "en_GB"]}


def nacti_temata():
    with open(DATA / "temata.json", encoding="utf-8") as f:
        return json.load(f)


def klient():
    """Ollama klient, který obchází školní proxy (server běží lokálně)."""
    import ollama
    return ollama.Client(host=OLLAMA_HOST, trust_env=False)


def nazev_souboru(model, varianta, jazyk, tema_id):
    return f"{model}__{varianta}__{jazyk}__t{tema_id}.txt"


def rozloz_nazev(nazev):
    """'gemma3__custom__cs__t2.txt' -> ('gemma3', 'custom', 'cs', 2)"""
    model, varianta, jazyk, t = Path(nazev).stem.split("__")
    return model, varianta, jazyk, int(t.lstrip("t"))


# ---------------------------------------------------------------- text

_MARKDOWN = re.compile(r"(\*\*|__|\*|`|^#{1,6}\s*|^\s*[-*•]\s+|^\s*\d+[.)]\s+)", re.M)
SLOVO = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")


def bez_markdownu(text):
    return _MARKDOWN.sub("", text)


def slova(text):
    """Slova (jen písmena, s vnitřní pomlčkou/apostrofem)."""
    return SLOVO.findall(bez_markdownu(text))


def je_nadpis(radek):
    r = radek.strip()
    if r.startswith("#"):
        return True
    holy = bez_markdownu(r).strip()
    # krátký řádek bez koncové interpunkce = nadpis / titulek
    return len(slova(holy)) < 15 and not re.search(r"[.!?…:;\"“”»]$", holy)


def odstavce(text):
    """Neprázdné řádky, které nejsou nadpis. Modely nezalamují řádky,
    takže jeden řádek = jeden odstavec (funguje pro oddělení \\n i \\n\\n)."""
    return [r.strip() for r in text.splitlines() if r.strip() and not je_nadpis(r)]


def nadpisy(text):
    return [r.strip() for r in text.splitlines() if r.strip() and je_nadpis(r)]


def vety(text):
    vysledek = []
    for odst in odstavce(text):
        for v in re.split(r"(?<=[.!?…])\s+", bez_markdownu(odst)):
            if v.strip():
                vysledek.append(v.strip())
    return vysledek
