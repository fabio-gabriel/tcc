#!/usr/bin/env python3
"""
Analise da serie D4b pelos criterios de pre-registro.md §11.12.6. Somente leitura.

Procedimento do §5.2 IDENTICO ao usado em D3 -> D4 (apresentacao/
gerar_apresentacao.py:127-136, 179-189): Fligner-Killeen sobre PSNR; razao
IQR(degrau)/IQR(D3); IC 95% bootstrap percentilico com default_rng(20260909)
NOVO por comparacao e 10.000 reamostragens; criterio conjuntivo p < 0,05 e
limite superior do IC < 1. Sanidade: recalcula D3 -> D4, que tem de dar
p = 2,2e-3, razao 0,115, IC [0,028 ; 0,606] (caderno 2026-10-05).

Criterios de D4b (§11.12.6):
  H3.4b : os N splat.ply com hash identico (sustentada) ou nao (refutada);
  §5.2  : D3 (N=30) x D4b em PSNR; num_splats secundario;
  QD4b  : |mediana PSNR D4b - mediana PSNR D3| < 0,10 dB.
Leitura dos desfechos: tabela do §11.12.6.
"""
import json
import re
from pathlib import Path

import numpy as np
from scipy.stats import fligner

DADOS = Path(__file__).resolve().parent.parent / "pivo-reprodutibilidade-3dgs" / "dados"
SEED, B, LIM = 20260909, 10000, 0.10
ANSI = re.compile(rb"\x1b\[[0-9;]*[A-Za-z]")
PAT = re.compile(rb"(\d+) dupli, (\d+) split, (\d+) prune -> (\d+) splats")


def carregar(deg):
    runs = []
    for rd in sorted((DADOS / deg).glob("run*")):
        ev = json.load(open(rd / "eval.json"))
        tr = json.load(open(rd / "train.json"))
        log = ANSI.sub(b"", next(rd.glob("run*.log")).read_bytes())
        runs.append(dict(idx=int(rd.name[3:]), psnr=ev["mean"]["psnr"], ssim=ev["mean"]["ssim"],
                         lpa=ev["mean"]["lpips_alex"], n=tr["num_splats"], t=tr["time_elapsed"],
                         dens=tuple(PAT.findall(log))))
    hashes = [ln.split("\t")[3] for ln in open(DADOS / deg / "manifest.tsv")
              if ln.split("\t")[1:2] == ["splat.ply"]]
    return runs, hashes


iqr = lambda v: float(np.subtract(*np.percentile(v, [75, 25])))  # noqa: E731
med = lambda v: float(np.median(v))                                # noqa: E731


def boot(x, y, rng):
    bs = []
    for _ in range(B):
        ix = iqr(rng.choice(x, len(x)))
        bs.append(iqr(rng.choice(y, len(y))) / ix if ix > 0 else np.nan)
    return np.nanpercentile(bs, [2.5, 97.5])


def s52(x, y):
    p = fligner(x, y).pvalue
    rz = iqr(y) / iqr(x)
    lo, hi = boot(x, y, np.random.default_rng(SEED))
    return dict(p=p, rz=rz, lo=lo, hi=hi, ok=bool(p < 0.05 and hi < 1))


def fmt(r):
    return (f"Fligner p = {r['p']:.2e} | razao IQR = {r['rz']:.3f} | IC 95% [{r['lo']:.3f} ; {r['hi']:.3f}]"
            f" | §5.2: {'SUSTENTADA' if r['ok'] else 'nao sustentada'}")


def primeiro_evento_divergente(runs):
    seqs = [r["dens"] for r in runs]
    n = min(len(s) for s in seqs)
    for k in range(n):
        if len({s[k] for s in seqs}) > 1:
            return k, n
    return None, n


def main():
    D = {d: carregar(d) for d in ("D3", "D4", "D4b")}
    R = {d: D[d][0] for d in D}
    P = {d: np.array([r["psnr"] for r in R[d]]) for d in D}
    N = {d: np.array([r["n"] for r in R[d]], float) for d in D}

    print("== N por degrau:", {d: len(R[d]) for d in D})
    assert len(R["D3"]) == 30 and len(R["D4"]) == 10 and len(R["D4b"]) == 10

    print("\n== Sanidade: D3 -> D4 (esperado p=2,2e-3, razao 0,115, IC [0,028 ; 0,606])")
    print("   PSNR:", fmt(s52(P["D3"], P["D4"])))

    h = D["D4b"][1]
    print(f"\n== H3.4b: {len(set(h))} hashes distintos em {len(h)} -> "
          f"{'SUSTENTADA' if len(set(h)) == 1 else 'REFUTADA'}")

    print("\n== §5.2, D3 (N=30) x D4b")
    print("   PSNR (pre-registrada):", fmt(s52(P["D3"], P["D4b"])))
    print("   num_splats (secundaria):", fmt(s52(N["D3"], N["D4b"])))

    q = abs(med(P["D4b"]) - med(P["D3"]))
    print(f"\n== QD4b: |mediana D4b - mediana D3| = |{med(P['D4b']):.4f} - {med(P['D3']):.4f}| = {q:.4f} dB "
          f"-> {'SATISFEITO' if q < LIM else 'NAO satisfeito'} (limiar {LIM})")
    print(f"   D4b - D4 = {med(P['D4b']) - med(P['D4']):+.4f} dB "
          f"({'>=' if med(P['D4b']) - med(P['D4']) >= LIM else '<'} 0,10 dB)")

    print("\n== Descritivos (mediana | IQR | min | max | amplitude)")
    for k, nome in (("psnr", "PSNR"), ("ssim", "SSIM"), ("lpa", "LPIPS-Alex"), ("n", "num_splats"), ("t", "tempo s")):
        for d in D:
            v = np.array([r[k] for r in R[d]], float)
            print(f"   {nome:10s} {d:4s} {med(v):12.4f} | {iqr(v):10.4f} | {v.min():12.4f} | {v.max():12.4f} | {np.ptp(v):10.4f}")
    print("   valores distintos de num_splats:", {d: len(set(N[d])) for d in D})

    print("\n== Densificacao (grandeza secundaria do §4): primeiro evento em que as execucoes divergem")
    for d in D:
        k, n = primeiro_evento_divergente(R[d])
        print(f"   {d}: evento {k} de {n}; sequencias completas distintas: {len({r['dens'] for r in R[d]})} de {len(R[d])}")


if __name__ == "__main__":
    main()
