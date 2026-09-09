#!/usr/bin/env python3
"""Analise de dispersao entre execucoes identicas — eixo 1 do TCC.

Plano estatistico fixado no pre-registro §5. NAO-PARAMETRICO por decisao a
priori: Hoefler e Belli (2015) registram que N de 30-40 e insuficiente para
invocar o TLC, e que normalidade e raramente observada em medicao de computador.

Reporta, por degrau:
  - mediana, Q1, Q3, minimo, maximo, amplitude, IQR
  - CI 95% nao-parametrico da mediana pela formula de rank atribuida a Le Boudec
  - fracao de pares de execucoes com |dPSNR| >= 0,10 dB   <- estatistica de H2
  - Shapiro-Wilk, se scipy estiver disponivel (diagnostico, nao decisao)

Uso: python3 analise_dispersao.py pivo-reprodutibilidade-3dgs/dados/D0
"""

import json
import math
import re
import sys
from itertools import combinations
from pathlib import Path

Z_95 = 1.959963985  # quantil normal para alpha = 0,05
LIMIAR_H2_DB = 0.10  # pre-registro §6
LARGURA_ALVO_DB = 0.02  # pre-registro §5.1

ANSI = re.compile(r"\x1B\[[0-9;]*[a-zA-Z]")


def le_boudec_ranks(n, z=Z_95):
    """CI nao-parametrico da mediana. Retorna ranks 1-based (lo, hi).

    Formula citada por Hoefler e Belli, atribuida a Le Boudec:
        do rank floor((n - z*sqrt(n))/2) ao rank ceil((n + z*sqrt(n))/2) + 1
    """
    lo = math.floor((n - z * math.sqrt(n)) / 2)
    hi = math.ceil((n + z * math.sqrt(n)) / 2) + 1
    return max(1, lo), min(n, hi)


def quantil(xs, q):
    """Interpolacao linear entre ordens (metodo 7, o default do numpy)."""
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return s[int(pos)]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def resumo(nome, xs, unidade="", casas=4):
    n = len(xs)
    s = sorted(xs)
    med = quantil(s, 0.5)
    q1, q3 = quantil(s, 0.25), quantil(s, 0.75)
    lo, hi = le_boudec_ranks(n)
    ci_lo, ci_hi = s[lo - 1], s[hi - 1]
    largura = ci_hi - ci_lo
    f = f"{{:.{casas}f}}"
    print(f"\n  {nome}  (N={n}{', ' + unidade if unidade else ''})")
    print(f"    mediana     : {f.format(med)}")
    print(f"    Q1 / Q3     : {f.format(q1)} / {f.format(q3)}   IQR={f.format(q3-q1)}")
    print(f"    min / max   : {f.format(s[0])} / {f.format(s[-1])}")
    print(f"    amplitude   : {f.format(s[-1]-s[0])}")
    print(f"    CI 95% med. : [{f.format(ci_lo)}, {f.format(ci_hi)}]  ranks {lo}..{hi} de {n}")
    print(f"    largura CI  : {f.format(largura)}")
    return {"n": n, "mediana": med, "amplitude": s[-1] - s[0], "ci_largura": largura}


def fracao_pares(xs, limiar):
    pares = list(combinations(xs, 2))
    acima = [p for p in pares if abs(p[0] - p[1]) >= limiar]
    return len(acima), len(pares)


def sched_counts(log_text):
    """Extrai contagens dos dois kernels do timing breakdown. Limpa ANSI."""
    t = ANSI.sub("", log_text)
    out = {}
    for chave in ("_RasterizeBackwardScheduling_PerSplat",
                  "_RasterizeBackwardScheduling_Tensor_0_8_8"):
        m = re.search(rf"{re.escape(chave)}\s*-\s*(\d+),", t)
        if m:
            out[chave.split("_")[-1] if "Tensor" not in chave else "Tensor"] = int(m.group(1))
    return out


def main(base):
    base = Path(base)
    runs = sorted(p for p in base.glob("run*") if p.is_dir())
    if not runs:
        sys.exit(f"nenhuma execucao encontrada em {base}")

    dados = []
    for r in runs:
        ev, tr, en = r / "eval.json", r / "train.json", r / "env.json"
        faltando = [p.name for p in (ev, tr) if not p.exists()]
        if faltando:
            print(f"  AVISO: {r.name} sem {faltando} — excluida", file=sys.stderr)
            continue
        e = json.loads(ev.read_text())["mean"]
        t = json.loads(tr.read_text())
        d = {
            "run": r.name,
            "psnr": e["psnr"], "ssim": e["ssim"],
            "lpips_vgg": e["lpips_vgg"], "lpips_alex": e["lpips_alex"],
            "num_splats": t["num_splats"], "time_elapsed": t["time_elapsed"],
        }
        if en.exists():
            d["commit"] = json.loads(en.read_text()).get("vksplat_commit", "?")[:10]
        log = r / f"{r.name}.log"
        if log.exists():
            d.update(sched_counts(log.read_text(errors="replace")))
        dados.append(d)

    print(f"\n{'='*66}")
    print(f" {base.name} — {len(dados)} execucoes")
    commits = {d.get("commit") for d in dados}
    print(f" commits: {commits}  {'OK' if len(commits)==1 else '<<< DIVERGENTES'}")
    print(f"{'='*66}")

    print(f"\n{'run':>8} {'PSNR':>8} {'SSIM':>7} {'LPIPSv':>7} {'LPIPSa':>7} "
          f"{'gaussianas':>11} {'seg':>7} {'PerSplat':>9} {'Tensor':>7}")
    for d in dados:
        print(f"{d['run']:>8} {d['psnr']:>8.4f} {d['ssim']:>7.4f} "
              f"{d['lpips_vgg']:>7.4f} {d['lpips_alex']:>7.4f} "
              f"{d['num_splats']:>11d} {d['time_elapsed']:>7.1f} "
              f"{d.get('PerSplat', 0):>9d} {d.get('Tensor', 0):>7d}")

    r_psnr = resumo("PSNR", [d["psnr"] for d in dados], "dB")
    resumo("SSIM", [d["ssim"] for d in dados])
    resumo("LPIPS Alex", [d["lpips_alex"] for d in dados])
    resumo("LPIPS VGG (convencao incorreta, ver §8.3)", [d["lpips_vgg"] for d in dados])
    resumo("Numero de gaussianas", [float(d["num_splats"]) for d in dados], casas=0)
    resumo("Tempo de treino", [d["time_elapsed"] for d in dados], "s", casas=1)

    print(f"\n{'-'*66}")
    print(" H2 — estatistica pre-registrada (§6)")
    a, tot = fracao_pares([d["psnr"] for d in dados], LIMIAR_H2_DB)
    frac = 100.0 * a / tot if tot else 0.0
    print(f"    pares com |dPSNR| >= {LIMIAR_H2_DB} dB : {a} de {tot}  ({frac:.1f}%)")
    print(f"    criterio: >= 5% sustenta H2  ->  {'SUSTENTADA' if frac >= 5 else 'REFUTADA'}")

    print(f"\n{'-'*66}")
    print(" H1 — identidade bit a bit")
    print("    conferir manifest.tsv: hashes distintos de splat.ply refutam identidade")

    print(f"\n{'-'*66}")
    print(" Regra de parada (§5.1)")
    print(f"    largura do CI da mediana de PSNR : {r_psnr['ci_largura']:.4f} dB")
    print(f"    largura-alvo                     : {LARGURA_ALVO_DB} dB")
    if r_psnr["ci_largura"] <= LARGURA_ALVO_DB:
        print("    -> ALVO ATINGIDO: parar")
    else:
        print(f"    -> CONTINUAR: proxima janela de k=10 (ate N_max=50)")

    try:
        from scipy import stats
        w, p = stats.shapiro([d["psnr"] for d in dados])
        print(f"\n Shapiro-Wilk sobre PSNR: W={w:.4f}, p={p:.4f} "
              f"({'nao rejeita' if p > 0.05 else 'rejeita'} normalidade)")
        print(" (diagnostico apenas; o plano e nao-parametrico por decisao a priori)")
    except ImportError:
        print("\n scipy ausente — Shapiro-Wilk nao executado")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pivo-reprodutibilidade-3dgs/dados/D0")
