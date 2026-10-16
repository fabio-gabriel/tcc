#!/usr/bin/env python3
"""
Analise da serie H3b pelos criterios de pre-registro.md §11.14.5. Somente leitura.
Reusa carregar/s52/boot/iqr de analisar_d4b.py: procedimento do §5.2 IDENTICO
(Fligner; razao de IQR; IC 95% bootstrap percentilico com default_rng(20260909)
novo por comparacao; 10.000 reamostragens).

  Primario  (§6, D-12): D0 (N=30) x H3b (N=10), PSNR. "Substancialmente menor"
            <=> p < 0,05 e limite superior do IC de IQR(H3b)/IQR(D0) < 1
            -> H3b REFUTADA; caso contrario SUSTENTADA.
  Secundario: D4b (N=10) x H3b (N=10). Aumento sustentado <=> p < 0,05 e
            limite inferior do IC de IQR(H3b)/IQR(D4b) > 1.
  Contexto  : IQR(H3b)/IQR(D3) com IC; descritivos; hashes; densificacao.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import fligner

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analisar_d4b import (SEED, boot, carregar, iqr, med,  # type: ignore  # noqa: E402
                          primeiro_evento_divergente, s52, fmt)


def aumento(x, y):
    """Teste de AUMENTO de dispersao de x para y (mesmo procedimento, sentido oposto)."""
    p = fligner(x, y).pvalue
    rz = iqr(y) / iqr(x)
    lo, hi = boot(x, y, np.random.default_rng(SEED))
    return dict(p=p, rz=rz, lo=lo, hi=hi, ok=bool(p < 0.05 and lo > 1))


def main():
    D = {d: carregar(d) for d in ("D0", "D3", "D4b", "H3b")}
    R = {d: D[d][0] for d in D}
    P = {d: np.array([r["psnr"] for r in R[d]]) for d in D}
    print("== N:", {d: len(R[d]) for d in D})
    assert len(R["D0"]) == 30 and len(R["H3b"]) == 10 and len(R["D4b"]) == 10

    print("\n== Sanidade: D3 -> D4b deve dar p=6,1e-4, razao 0,120, IC [0,038 ; 0,311] (caderno 2026-10-16)")
    print("   ", fmt(s52(P["D3"], P["D4b"])))

    r1 = s52(P["D0"], P["H3b"])
    print("\n== PRIMARIO (§6): D0 (N=30) x H3b, PSNR")
    print(f"   Fligner p = {r1['p']:.3e} | razao IQR(H3b)/IQR(D0) = {r1['rz']:.3f} | IC 95% [{r1['lo']:.3f} ; {r1['hi']:.3f}]")
    print(f"   'substancialmente menor' (p<0,05 e IC_sup<1): {r1['ok']} -> H3b {'REFUTADA' if r1['ok'] else 'SUSTENTADA'}")

    r2 = aumento(P["D4b"], P["H3b"])
    print("\n== SECUNDARIO: D4b x H3b, PSNR")
    print(f"   Fligner p = {r2['p']:.3e} | razao IQR(H3b)/IQR(D4b) = {r2['rz']:.3f} | IC 95% [{r2['lo']:.3f} ; {r2['hi']:.3f}]")
    print(f"   aumento sustentado (p<0,05 e IC_inf>1): {r2['ok']}")

    lb = {(True, False): "ESTAVEL", (True, True): "ESTABILIDADE PARCIAL",
          (False, True): "INSTABILIDADE (repetibilidade nao implica estabilidade)",
          (False, False): "INCONCLUSIVO (falta de poder)"}[(r1["ok"], r2["ok"])]
    print(f"\n== LEITURA pela tabela do §11.14.5: {lb}")

    r3 = s52(P["D3"], P["H3b"])
    print(f"\n== Contexto: IQR(H3b)/IQR(D3) = {r3['rz']:.3f}, IC [{r3['lo']:.3f} ; {r3['hi']:.3f}], Fligner p = {r3['p']:.3e}")

    h = D["H3b"][1]
    print(f"\n== Hashes de H3b: {len(set(h))} distintos em {len(h)}")
    print("\n== Descritivos (mediana | IQR | min | max | amplitude)")
    for k, nome in (("psnr", "PSNR"), ("ssim", "SSIM"), ("lpa", "LPIPS-Alex"), ("n", "num_splats"), ("t", "tempo s")):
        for d in D:
            v = np.array([r[k] for r in R[d]], float)
            print(f"   {nome:10s} {d:4s} {med(v):12.4f} | {iqr(v):10.4f} | {v.min():12.4f} | {v.max():12.4f} | {np.ptp(v):10.4f}")
    print("   valores distintos de num_splats:", {d: len({r['n'] for r in R[d]}) for d in D})
    print("\n== Densificacao: primeiro evento em que as execucoes divergem")
    for d in D:
        k, n = primeiro_evento_divergente(R[d])
        print(f"   {d}: evento {k} de {n}; sequencias distintas {len({r['dens'] for r in R[d]})} de {len(R[d])}")

    placebo(R["D4b"])


def placebo(r_d4b):
    """Controle do §11.15. Setter inocuo <=> as execucoes placebo terminam com o
    N de D4b e com a sequencia de densificacao IDENTICA a (unica) de D4b."""
    import json
    from analisar_d4b import DADOS  # type: ignore
    d = DADOS / "H3b_placebo"
    print("\n== Controle placebo (§11.15)")
    if not d.exists():
        print("   (sem dados em dados/H3b_placebo)")
        return
    seqs_d4b = {r["dens"] for r in r_d4b}
    ns_d4b = {r["n"] for r in r_d4b}
    assert len(seqs_d4b) == 1 and len(ns_d4b) == 1, "D4b deveria ter sequencia e N unicos"
    seq, n_ref = next(iter(seqs_d4b)), next(iter(ns_d4b))
    rp, _ = carregar("H3b_placebo")
    inocuo = True
    for r in rp:
        env = json.load(open(d / f"run{r['idx']:03d}" / "env.json"))
        h = env.get("h3b") or {}
        ok_env = h.get("placebo") is True and h.get("verificado") is True and h.get("uint32_diferentes_apos_releitura") == 0
        igual = r["dens"] == seq and r["n"] == n_ref
        inocuo &= igual and ok_env
        primeiro = next((i for i, (a, b) in enumerate(zip(r["dens"], seq)) if a != b), None)
        print(f"   run{r['idx']:03d}: env placebo/verificado/0 bits = {ok_env} | N {r['n']} (D4b {n_ref}) | "
              f"densificacao identica a D4b: {r['dens'] == seq} (1o evento diferente: {primeiro}) | PSNR {r['psnr']:.4f}")
    print(f"   N = {len(rp)} | LEITURA (§11.15): {'SETTER INOCUO -> aumento de H3b atribuido ao bit' if inocuo and len(rp) >= 3 else 'SETTER PERTURBA (ou N < 3) -> aumento atribuido a perturbacao + regravacao'}")


if __name__ == "__main__":
    main()
