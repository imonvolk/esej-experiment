"""Souhrnné tabulky a grafy podle modelu, jazyka a varianty.

Vstup:  vysledky/metriky.csv, vysledky/generace.jsonl,
        volitelně vysledky/spojene.csv (po slepém hodnocení a odkryj.py)
Výstup: vysledky/souhrn.md, vysledky/grafy/*.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from priprav_hodnoceni import KRITERIA
from spolecne import VYSLEDKY

KLIC = ["model", "varianta", "jazyk", "tema_id"]
SKUPINA = ["jazyk", "model", "varianta"]

# Barva = model (validovaná kategoriální paleta, sloty 1 a 2), varianta = šrafování
BARVA = {"gemma3": "#2a78d6", "llama3.2": "#eb6834"}
SRAF = {"zakladni": "", "custom": "///"}
NAZEV_VARIANTY = {"zakladni": "základní", "custom": "customizovaná"}
NAZEV_JAZYKA = {"cs": "čeština", "en": "angličtina"}
INK, INK2, MRIZKA = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "Segoe UI", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "hatch.color": "#fcfcfb", "hatch.linewidth": 1.5,
})


def nacti():
    m = pd.read_csv(VYSLEDKY / "metriky.csv", encoding="utf-8-sig")
    g = pd.read_json(VYSLEDKY / "generace.jsonl", lines=True).drop_duplicates(KLIC, keep="last")
    df = m.merge(g[KLIC + ["eval_count", "tokeny_za_s", "cas_celkem_s", "done_reason"]],
                 on=KLIC, how="left")
    spojene = VYSLEDKY / "spojene.csv"
    if spojene.exists():
        h = pd.read_csv(spojene, encoding="utf-8-sig")[KLIC + list(KRITERIA) + ["hodnoceni_prumer"]]
        df = df.merge(h, on=KLIC, how="left")
    df["podil_spatny_jazyk_pct"] = df["podil_spatny_jazyk"] * 100
    df["useknuto"] = df["done_reason"].eq("length")
    return df


def md_tabulka(df):
    df = df.reset_index()
    radky = ["| " + " | ".join(map(str, df.columns)) + " |",
             "|" + "|".join("---" for _ in df.columns) + "|"]
    for r in df.itertuples(index=False):
        radky.append("| " + " | ".join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(radky)


def sloupce(ax, df, sloupec, titulek, jednotka=""):
    """Skupiny = jazyk, uvnitř 4 sloupce (model × varianta), tečky = jednotlivé eseje."""
    sirka, mezera = 0.19, 0.02
    poradi = [(m, v) for m in BARVA for v in SRAF]
    for gi, jazyk in enumerate(["cs", "en"]):
        for i, (model, var) in enumerate(poradi):
            x = gi + (i - 1.5) * (sirka + mezera)
            hodnoty = df[(df.jazyk == jazyk) & (df.model == model) & (df.varianta == var)][sloupec].dropna()
            if hodnoty.empty:
                continue
            ax.bar(x, hodnoty.mean(), sirka, color=BARVA[model], hatch=SRAF[var],
                   edgecolor="#fcfcfb", linewidth=0, zorder=2)
            ax.scatter([x] * len(hodnoty), hodnoty, s=14, color=INK, alpha=0.55,
                       zorder=3, linewidths=0)
    ax.set_xticks([0, 1], [NAZEV_JAZYKA["cs"], NAZEV_JAZYKA["en"]])
    ax.set_title(titulek, loc="left", color=INK, fontsize=11)
    if jednotka:
        ax.set_ylabel(jednotka)
    ax.grid(axis="y", color=MRIZKA, linewidth=0.8, zorder=0)
    ax.tick_params(length=0)


def legenda(fig):
    from matplotlib.patches import Patch
    prvky = [Patch(facecolor=BARVA[m], hatch=SRAF[v], edgecolor="#fcfcfb",
                   label=f"{m} – {NAZEV_VARIANTY[v]}") for m in BARVA for v in SRAF]
    fig.legend(handles=prvky, loc="upper center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 1.0), fontsize=9)


def graf(df, sloupce_def, soubor, nadpis, ncol=2):
    n = len(sloupce_def)
    nrow = (n + ncol - 1) // ncol
    fig, osy = plt.subplots(nrow, ncol, figsize=(5 * ncol, 3.4 * nrow + 0.8), squeeze=False)
    for ax, (sl, tit, jed) in zip(osy.flat, sloupce_def):
        sloupce(ax, df, sl, tit, jed)
    for ax in list(osy.flat)[n:]:
        ax.set_visible(False)
    legenda(fig)
    fig.suptitle(nadpis + "  (sloupec = průměr, tečky = jednotlivé eseje)",
                 y=0.955, fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    (VYSLEDKY / "grafy").mkdir(exist_ok=True)
    fig.savefig(VYSLEDKY / "grafy" / soubor, dpi=150)
    plt.close(fig)


def main():
    df = nacti()
    ma_hodnoceni = "hodnoceni_prumer" in df and df["hodnoceni_prumer"].notna().any()

    auto = {"slov": "slov", "abs_odchylka_pct": "odchylka délky %", "odstavcu": "odstavců",
            "chyb_na_100_slov": "chyb/100 slov", "podil_spatny_jazyk_pct": "cizí jazyk %",
            "markdown": "Markdown (podíl)", "useknuto": "useknuto (podíl)"}
    rychlost = {"tokeny_za_s": "tok/s", "eval_count": "tokenů", "cas_celkem_s": "čas [s]"}

    agg = df.groupby(SKUPINA)
    t_auto = agg[list(auto)].mean().rename(columns=auto)
    t_auto.insert(0, "n", agg.size())
    t_rych = agg[list(rychlost)].mean().rename(columns=rychlost)

    md = ["# Souhrn výsledků", "",
          "Automaticky vygenerováno skriptem `vyhodnoceni.py`. Hodnoty jsou průměry přes témata.", "",
          "## Automatické metriky", "", md_tabulka(t_auto.round(2)), "",
          "## Rychlost (jen procesor)", "", md_tabulka(t_rych.round(1)), ""]

    if ma_hodnoceni:
        hodn = {k: k for k in KRITERIA} | {"hodnoceni_prumer": "průměr"}
        t_h = agg[list(hodn)].mean().rename(columns=hodn)
        md += ["## Slepé lidské hodnocení (1–5)", "", md_tabulka(t_h.round(2)), ""]

    # Hypotéza: rozdíl gemma3 − llama3.2 po jazycích a variantách
    porovnani = ["chyb_na_100_slov", "podil_spatny_jazyk_pct", "abs_odchylka_pct"]
    if ma_hodnoceni:
        porovnani.append("hodnoceni_prumer")
    p = df.groupby(["jazyk", "varianta", "model"])[porovnani].mean().unstack("model")
    rozdil = pd.DataFrame({c: p[(c, "gemma3")] - p[(c, "llama3.2")] for c in porovnani})
    md += ["## Rozdíl gemma3 − llama3.2", "",
           "U chyb, cizího jazyka a odchylky délky je lepší **záporné** číslo (Gemma má méně), "
           "u hodnocení **kladné**.", "", md_tabulka(rozdil.round(2)), ""]

    (VYSLEDKY / "souhrn.md").write_text("\n".join(md), encoding="utf-8")

    graf(df, [("chyb_na_100_slov", "Pravopisné chyby", "na 100 slov"),
              ("podil_spatny_jazyk_pct", "Věty ve špatném jazyce", "%"),
              ("abs_odchylka_pct", "Odchylka od 300 slov", "% (absolutně)"),
              ("odstavcu", "Počet odstavců", "odstavců")],
         "automaticke_metriky.png", "Automatické metriky")
    graf(df, [("tokeny_za_s", "Rychlost generování", "tokenů/s"),
              ("cas_celkem_s", "Čas na jednu esej", "s")],
         "rychlost.png", "Rychlost na procesoru")
    if ma_hodnoceni:
        graf(df, [(k, f"Hodnocení: {k}", "1–5") for k in KRITERIA],
             "hodnoceni.png", "Slepé lidské hodnocení")

    print((VYSLEDKY / "souhrn.md").read_text(encoding="utf-8"))
    print("Grafy:", ", ".join(p.name for p in (VYSLEDKY / "grafy").glob("*.png")))


if __name__ == "__main__":
    main()
