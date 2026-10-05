#!/usr/bin/env python3
"""
Diagnostico dos `splat.ply` de D4 — onde as execucoes diferem.

Grandeza secundaria ja pre-registrada em pre-registro.md §4: "distribuicao das
diferencas por parametro entre pares de execucoes". Nao e metrica nova.

POR QUE
-------
Em D4 os 10 hashes sao distintos (H3.4 refutada), mas 5 execucoes tem trajetoria
de densificacao identica nos 144 eventos e `splat.ply` de tamanho identico. O
hash nao diz se a diferenca e:
  (a) so de ORDEM dos registros (mesmo modelo, gravado em ordem diferente),
  (b) de VALOR, e entao em quantas gaussianas, em quais parametros, e com que
      magnitude (em ULP de float32, a unidade natural para nao-determinismo de
      acumulacao).
O diagnostico separa os dois casos e e o que localiza a fonte residual.

FORMATO, lido do codigo e nao suposto — `VulkanGSTrainer::writePLY`,
`vksplat/src/gs_trainer.cpp:1398` em D4:
  cabecalho ASCII; `format binary_little_endian 1.0`; `element vertex N`;
  59 `property float` por gaussiana (x,y,z; f_dc_0..2, f_rest_0..44; opacity,
  scale_0..2; rot_0..3); registros escritos na ordem do buffer da GPU.
O script le os nomes e a contagem do proprio cabecalho e recusa qualquer coisa
fora desse formato.

NAO MODIFICA NADA. Le os .ply por memmap (1,4 GB cada; nao carrega dois de uma
vez na RAM). Escreve um JSON pequeno com os resultados.

USO (na Ubuntu, onde estao os .ply de D4)
-----------------------------------------
    python3 experimentos/diagnosticar_ply_d4.py \\
        --dados pivo-reprodutibilidade-3dgs/dados/D4 \\
        --out   pivo-reprodutibilidade-3dgs/dados/D4/diagnostico_ply.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

N_PROPS_ESPERADO = 59


def ler_ply(caminho):
    """Retorna (nomes, matriz memmap uint32 (N, P)). Recusa formato inesperado."""
    with open(caminho, "rb") as fp:
        cab = b""
        while not cab.endswith(b"end_header\n"):
            linha = fp.readline()
            if not linha:
                raise ValueError(f"{caminho}: cabecalho sem end_header")
            cab += linha
            if len(cab) > 1 << 16:
                raise ValueError(f"{caminho}: cabecalho grande demais")
        inicio = fp.tell()
    linhas = cab.decode("ascii").splitlines()
    if linhas[0] != "ply" or linhas[1] != "format binary_little_endian 1.0":
        raise ValueError(f"{caminho}: formato inesperado: {linhas[:2]}")
    n = None
    nomes = []
    for l in linhas[2:]:
        p = l.split()
        if p[:2] == ["element", "vertex"]:
            n = int(p[2])
        elif p[:2] == ["property", "float"]:
            nomes.append(p[2])
        elif p and p[0] not in ("end_header", "comment"):
            raise ValueError(f"{caminho}: linha de cabecalho nao suportada: {l!r}")
    if n is None or len(nomes) != N_PROPS_ESPERADO:
        raise ValueError(f"{caminho}: N={n}, {len(nomes)} propriedades "
                         f"(esperado {N_PROPS_ESPERADO})")
    tam = os.path.getsize(caminho)
    if tam != inicio + 4 * n * len(nomes):
        raise ValueError(f"{caminho}: tamanho {tam} incompativel com N={n}")
    m = np.memmap(caminho, dtype="<u4", mode="r", offset=inicio, shape=(n, len(nomes)))
    return nomes, m


def ordenavel(u32):
    """Mapeia o padrao de bits de float32 para inteiro monotonico: a diferenca
    entre dois desses inteiros e a distancia em ULP. Negativos: ~u; positivos:
    u ^ 0x80000000. Assim -0.0 e +0.0 ficam a 1 ULP, e a ordem e preservada
    atravessando o zero."""
    u = u32.astype(np.int64)
    neg = (u & 0x80000000) != 0
    return np.where(neg, 0xFFFFFFFF - u, u + 0x80000000)


def hash_linhas(m, bloco=1 << 20):
    """Hash de 64 bits por registro (mistura multiplicativa com wraparound),
    para o teste de permutacao. Colisao e irrelevante para este diagnostico."""
    n, p = m.shape
    rng = np.random.default_rng(20261002)
    pesos = rng.integers(1, 2**63, size=p, dtype=np.uint64) | np.uint64(1)
    out = np.empty(n, dtype=np.uint64)
    with np.errstate(over="ignore"):
        for i in range(0, n, bloco):
            b = m[i:i + bloco].astype(np.uint64)
            h = np.zeros(len(b), dtype=np.uint64)
            for j in range(p):
                h = (h ^ (b[:, j] * pesos[j])) * np.uint64(0x9E3779B97F4A7C15)
            out[i:i + bloco] = h
    return out


def comparar(nomes, a, b, ha_ordenado=None, bloco=1 << 20):
    """Compara duas execucoes. a, b: memmaps uint32 (N, P). ha_ordenado: hash
    ordenado de `a`, se ja calculado (a referencia e a mesma em todos os pares)."""
    res: dict = {"n_a": int(a.shape[0]), "n_b": int(b.shape[0])}
    res["identicos_byte_a_byte"] = bool(a.shape == b.shape and all(
        np.array_equal(a[i:i + bloco], b[i:i + bloco]) for i in range(0, a.shape[0], bloco)))
    if res["identicos_byte_a_byte"]:
        return res

    # --- teste de permutacao: mesmo multiconjunto de registros? -------------
    ha = ha_ordenado if ha_ordenado is not None else np.sort(hash_linhas(a))
    hb = np.sort(hash_linhas(b))
    so_a = np.setdiff1d(ha, hb, assume_unique=False)
    so_b = np.setdiff1d(hb, ha, assume_unique=False)
    res["registros_so_em_a"] = int(len(so_a))
    res["registros_so_em_b"] = int(len(so_b))
    res["mesmo_multiconjunto"] = bool(a.shape == b.shape and np.array_equal(ha, hb))

    # --- comparacao posicional, quando N e igual -----------------------------
    if a.shape != b.shape:
        return res
    n, p = a.shape
    linhas_dif = 0
    primeira = ultima = None
    por_prop = np.zeros(p, dtype=np.int64)
    max_ulp = np.zeros(p, dtype=np.int64)
    max_abs = np.zeros(p, dtype=np.float64)
    hist_ulp = np.zeros(33, dtype=np.int64)  # log2 do ULP, 0..32
    for i in range(0, n, bloco):
        x, y = a[i:i + bloco], b[i:i + bloco]
        dif = x != y
        lin = dif.any(axis=1)
        k = int(lin.sum())
        if k:
            idx = np.nonzero(lin)[0] + i
            primeira = int(idx[0]) if primeira is None else primeira
            ultima = int(idx[-1])
            linhas_dif += k
            por_prop += dif.sum(axis=0)
            u = np.abs(ordenavel(x) - ordenavel(y))
            max_ulp = np.maximum(max_ulp, u.max(axis=0))
            fx = x.view("<f4").astype(np.float64)
            fy = y.view("<f4").astype(np.float64)
            with np.errstate(invalid="ignore"):
                max_abs = np.maximum(max_abs, np.nan_to_num(np.abs(fx - fy)).max(axis=0))
            uv = u[dif]
            hist_ulp += np.bincount(np.minimum(np.floor(np.log2(uv)).astype(int), 32),
                                    minlength=33)[:33]
    res["gaussianas_com_alguma_diferenca"] = linhas_dif
    res["fracao_gaussianas_diferentes"] = linhas_dif / n
    res["indice_primeira_diferente"] = primeira
    res["indice_ultima_diferente"] = ultima
    res["valores_diferentes_por_propriedade"] = {nomes[j]: int(por_prop[j]) for j in range(p)}
    res["max_ulp_por_propriedade"] = {nomes[j]: int(max_ulp[j]) for j in range(p)}
    res["max_abs_por_propriedade"] = {nomes[j]: float(max_abs[j]) for j in range(p)}
    res["histograma_log2_ulp"] = {f"2^{e}": int(c) for e, c in enumerate(hist_ulp) if c}
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dados", required=True, help="pivo-reprodutibilidade-3dgs/dados/D4")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="run000", help="execucao de referencia")
    a = ap.parse_args()

    runs = sorted(d for d in os.listdir(a.dados) if d.startswith("run"))
    plys = {}
    for r in runs:
        orig = open(os.path.join(a.dados, r, "origem.txt")).read().strip()
        p = os.path.join(orig, "splat.ply")
        if not os.path.exists(p):
            print(f"ABORTA: {p} nao existe (o .ply foi movido?)", file=sys.stderr)
            return 1
        plys[r] = p
    if a.ref not in plys:
        print(f"ABORTA: referencia {a.ref} ausente", file=sys.stderr)
        return 1

    nomes, ref = ler_ply(plys[a.ref])
    print(f"hash da referencia {a.ref} ...", flush=True)
    ha_ref = np.sort(hash_linhas(ref))
    pares = {}
    for r in runs:
        if r == a.ref:
            continue
        n2, m = ler_ply(plys[r])
        if n2 != nomes:
            print(f"ABORTA: {r} tem propriedades em ordem diferente", file=sys.stderr)
            return 1
        print(f"comparando {a.ref} x {r} ...", flush=True)
        pares[r] = comparar(nomes, ref, m, ha_ordenado=ha_ref)

    rel = {"gerado_em": datetime.now(timezone.utc).isoformat(),
           "proposito": "pre-registro §4: diferencas por parametro entre pares de execucoes, D4",
           "referencia": a.ref, "propriedades": nomes, "pares": pares}
    with open(a.out, "w") as fp:
        json.dump(rel, fp, indent=2)

    print(f"\nreferencia {a.ref}: N={ref.shape[0]}")
    print(f"{'run':7s} {'N':>9s} {'byte=':>6s} {'multic=':>8s} {'so_ref':>7s} {'so_run':>7s} "
          f"{'gauss≠':>8s} {'1a≠':>9s} {'max ULP':>9s}")
    for r, x in pares.items():
        mu = max(x.get("max_ulp_por_propriedade", {"-": 0}).values()) if "max_ulp_por_propriedade" in x else "-"
        print(f"{r:7s} {x['n_b']:9d} {str(x['identicos_byte_a_byte'])[0]:>6s} "
              f"{str(x.get('mesmo_multiconjunto', '-'))[0]:>8s} {x.get('registros_so_em_a', '-'):>7} "
              f"{x.get('registros_so_em_b', '-'):>7} {x.get('gaussianas_com_alguma_diferenca', '-'):>8} "
              f"{str(x.get('indice_primeira_diferente', '-')):>9s} {mu:>9}")
    print(f"\nrelatorio: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
