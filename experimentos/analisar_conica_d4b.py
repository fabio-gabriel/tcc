#!/usr/bin/env python3
"""
Analise da medicao densa de conica (dados/conica/) e aplicacao da regra do
adendo §11.12 (D4b). Reproduz TODOS os numeros citados no adendo.

Regra (decidida pelo aluno em 2026-10-15, caderno): escala UNICA por
componente de conica, com clamp por termo em +-(2^18 - 1); s = MAIOR inteiro
tal que a fracao de valores acumulados nao nulos com |g| >= 2^(18-s) (proxy de
saturacao) seja <= 1e-3 no regime, passos [3051, 30000). A definicao
alternativa [5000, 30000) e calculada para mostrar robustez.

Definicoes sobre o histograma de expoente (bin e = |g| em [2^(e-1), 2^e)), exatas
nas fronteiras de potencia de 2:
  zera     : |g| <  2^-(s+1)   <=> e <= -(s+1)
  estoura  : |g| >= 2^(31-s)   <=> e >= 32-s       (sem clamp extra, como em D4)
  satura   : |g| >= 2^(18-s)   <=> e >= 19-s       (proxy: acumulado, nao termo)
Somente leitura. Uso: python3 analisar_conica_d4b.py [dir_dados]
"""
import gzip
import json
import os
import sys

import numpy as np

DADOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "pivo-reprodutibilidade-3dgs", "dados", "conica")
C = ["conic_0", "conic_1", "conic_2"]
S_D4 = {"conic_0": 18, "conic_1": 18, "conic_2": 20}
REGIME, REGIME_ALT, LIM_SAT = (3051, 30000), (5000, 30000), 1e-3
FAIXAS = [(0, 1000), (1000, 3051), (3051, 5000), (5000, 15051), (15051, 30000)]
E = np.arange(-160, 140)


def carregar():
    R = []
    for r in range(3):
        with gzip.open(os.path.join(DADOS, f"conica_rep0{r}.ndjson.gz"), "rt") as f:
            R.append([json.loads(ln) for ln in f])
    return R


def hist(rows, c, a, b):
    """Matriz (passos x bins) e vetor de passos, para passos em [a, b)."""
    sel = [x for x in rows if a <= x["step"] < b]
    H = np.zeros((len(sel), E.size), np.int64)
    for i, x in enumerate(sel):
        for k, v in x["comp"][c]["hist_exp2"].items():
            H[i, int(k) + 160] = v
    return H


frac = lambda H, m: H[:, m].sum() / H.sum()               # noqa: E731
zera = lambda H, s: frac(H, E <= -(s + 1))                 # noqa: E731
satura = lambda H, s: frac(H, E >= 19 - s)                 # noqa: E731
passos_estouro = lambda H, s: float(np.mean(H[:, E >= 32 - s].sum(axis=1) > 0))  # noqa: E731


def s_regra(H):
    ok = [s for s in range(0, 64) if satura(H, s) <= LIM_SAT]
    return max(ok) if ok else None


def main():
    R = carregar()
    todas = [x for rr in R for x in rr]
    print(f"dados: {DADOS}\namostras por repeticao: {[len(r) for r in R]}")

    print("\n1. Quantis do expoente de |g| nao nulo no regime [5000,30000) (|g| ~ 2^(e-1))")
    for c in C:
        h = hist(todas, c, 5000, 30000).sum(axis=0)
        cum = np.cumsum(h) / h.sum()
        print(f"   {c}: " + "  ".join(f"q{int(p*100)}: e={int(E[np.searchsorted(cum, p)])}"
                                     for p in (0.1, 0.5, 0.9, 0.99)))

    print("\n2. Maximo por passo (sobre as 3 reps) por faixa: max / mediana dos maximos")
    for c in C:
        cells = []
        for a, b in FAIXAS + [(20000, 30000)]:
            mx = np.array([x["comp"][c]["max_abs"] or 0.0 for x in todas if a <= x["step"] < b])
            cells.append(f"[{a},{b}) {mx.max():.3g}/{np.median(mx):.3g}")
        print(f"   {c}: " + " | ".join(cells))

    print("\n3. D4 (s = 18/18/20, sem clamp extra): fracao zerada e fracao de passos com >=1 estouro")
    for c in C:
        s = S_D4[c]
        cells = [f"[{a},{b}) zera={zera(H, s):.2f} passos_estouro={passos_estouro(H, s):.2f}"
                 for a, b in FAIXAS for H in [hist(todas, c, a, b)]]
        print(f"   {c} (s={s}): " + " | ".join(cells))
    mx = np.array([x["comp"]["opacity"]["max_abs"] or 0.0 for x in todas])
    cap = 2.0 ** (31 - 34)
    print(f"   opacity (s=34): max denso {mx.max():.4g}, capacidade {cap}, passos acima {(mx >= cap).sum()} de {mx.size}")

    print(f"\n4. Regra do §11.12: maior s com proxy de saturacao <= {LIM_SAT:g} no regime")
    escolhido = {}
    for nome, (a, b) in [("regime [3051,30000)", REGIME), ("alternativo [5000,30000)", REGIME_ALT)]:
        for c in C:
            H = hist(todas, c, a, b)
            s = s_regra(H)
            if s is None:
                raise SystemExit(f"nenhum s satisfaz a regra para {c} em {nome}")
            por_rep = [s_regra(hist(R[r], c, a, b)) for r in range(3)]
            print(f"   {nome} {c}: s={s} satura={satura(H, s):.2e} (s+1: {satura(H, s + 1):.2e}) "
                  f"zera={zera(H, s):.3f} | por repeticao {por_rep}")
            if (a, b) == REGIME:
                escolhido[c] = s
    print(f"   ESCOLHIDO: {escolhido}")

    print("\n5. Efeito previsto do s escolhido, com clamp por termo em +-(2^18-1), por faixa")
    for c in C:
        s = escolhido[c]
        cells = [f"[{a},{b}) zera={zera(H, s):.2f} satura={satura(H, s):.1e}"
                 for a, b in FAIXAS for H in [hist(todas, c, a, b)]]
        print(f"   {c} (s={s}): " + " | ".join(cells))

    k_max, lim = 4346, 2 ** 18 - 1
    print(f"\n6. Garantia: K_max = {k_max} tiles; {k_max} x {lim} = {k_max * lim} < 2^31-1 = {2**31 - 1}: "
          f"{k_max * lim < 2**31 - 1}; cota geral 2^13 x {lim} = {2**13 * lim} < 2^31-1: {2**13 * lim < 2**31 - 1}")
    print(f"   2^18-1 = {float(lim)} exato em float32: {float(np.float32(lim)) == lim}")


if __name__ == "__main__":
    main()
