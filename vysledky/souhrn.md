# Souhrn výsledků

Automaticky vygenerováno skriptem `vyhodnoceni.py`. Hodnoty jsou průměry přes témata.

## Automatické metriky

| jazyk | model | varianta | n | slov | odchylka délky % | odstavců | chyb/100 slov | cizí jazyk % | slov v azbuce ap. | opakované věty (podíl) | Markdown (podíl) | useknuto (podíl) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cs | gemma3 | custom | 3 | 275.67 | 8.13 | 4.33 | 0.60 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| cs | gemma3 | zakladni | 3 | 259.00 | 13.70 | 4.67 | 0.78 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 |
| cs | llama3.2 | custom | 3 | 201.67 | 32.77 | 4.33 | 9.47 | 0.00 | 1.67 | 0.08 | 0.00 | 0.00 |
| cs | llama3.2 | zakladni | 3 | 315.33 | 19.10 | 8.67 | 9.22 | 0.00 | 0.00 | 0.00 | 0.33 | 0.00 |
| en | gemma3 | custom | 3 | 298.33 | 2.30 | 4.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| en | gemma3 | zakladni | 3 | 310.33 | 3.43 | 8.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 |
| en | llama3.2 | custom | 3 | 301.33 | 1.57 | 4.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| en | llama3.2 | zakladni | 3 | 312.67 | 7.10 | 5.33 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Rychlost (jen procesor)

| jazyk | model | varianta | tok/s | tokenů | čas [s] |
|---|---|---|---|---|---|
| cs | gemma3 | custom | 19.60 | 559.00 | 31.70 |
| cs | gemma3 | zakladni | 20.20 | 527.70 | 26.70 |
| cs | llama3.2 | custom | 23.50 | 398.30 | 18.40 |
| cs | llama3.2 | zakladni | 24.20 | 601.00 | 25.30 |
| en | gemma3 | custom | 20.00 | 358.30 | 20.20 |
| en | gemma3 | zakladni | 20.10 | 393.70 | 20.10 |
| en | llama3.2 | custom | 23.50 | 344.30 | 15.00 |
| en | llama3.2 | zakladni | 25.10 | 365.30 | 14.90 |

## Rozdíl gemma3 − llama3.2

U chyb, cizího jazyka a odchylky délky je lepší **záporné** číslo (Gemma má méně), u hodnocení **kladné**.

| jazyk | varianta | chyb_na_100_slov | podil_spatny_jazyk_pct | abs_odchylka_pct |
|---|---|---|---|---|
| cs | custom | -8.87 | 0.00 | -24.63 |
| cs | zakladni | -8.44 | 0.00 | -5.40 |
| en | custom | 0.00 | 0.00 | 0.73 |
| en | zakladni | 0.00 | 0.00 | -3.67 |
