#!/usr/bin/env python3
"""
Diagnostico PAREADO dos splat.ply: diferencas por parametro entre pares de
execucoes, com UM instrumento comum a D3, D4 e D4b. Exploratorio, definido em
2026-10-16 depois de ver os dados (caderno), operacionaliza a grandeza
secundaria do pre-registro §4 ("diferencas por parametro entre pares").

POR QUE
-------
O diagnostico por INDICE (diagnosticar_ply_d4.py) so vale quando as execucoes
tem o mesmo N e as gaussianas estao alinhadas: D4 e D4b. Em D3, as 30 execucoes
tem 30 N distintos e divergem no evento de densificacao 0 -- nao existe "a
mesma gaussiana". Para comparar os tres degraus com o mesmo instrumento:

1. PAREAMENTO por vizinho mais proximo MUTUO na posicao (cKDTree): i em A e j
   em B formam par se j e o mais proximo de i em B e i o mais proximo de j em A.
   Mede: fracao pareada; distancia dos pares; e, nos pares, diferencas de
   opacidade (sigmoide), escala (log), rotacao (angulo do quaternio, que
   identifica q e -q) e SH (f_dc, f_rest).
2. VALIDACAO do instrumento onde a correspondencia verdadeira e conhecida (D4,
   D4b, N igual, alinhamento por indice): "acerto" = fracao dos pares mutuos com
   j == i; "cobertura" = fracao dos i de A cujo par mutuo e i. Se o pareamento
   nao recupera o indice ja em D4b, o numero de D3 nao tem interpretacao.
3. ESCALA LOCAL: distancia de cada gaussiana de A a sua vizinha mais proxima
   EM A (k=2). Distancia entre execucoes << espacamento local => pareamento
   bem condicionado; da mesma ordem => ambiguo.
4. MEDIDA ESTRITA, quando N e igual: diagnostico por indice em ULP, pela funcao
   `comparar` de diagnosticar_ply_d4.py (mesma de 2026-10-05).

Escolhas fixadas ANTES de calcular (caderno 2026-10-16): referencia contra 9
outras; D3 so run020..run029 (mesmo estrato de ambiente de D4 e D4b: kernel -31,
libc 8.9, Mesa 25.2.8); D4 e D4b run000..run009.

LEITURA: cada .ply e lido INTEIRO para a RAM numa passada sequencial (HD USB:
leitura aleatoria por memmap seria lenta), com SHA-256 calculado no caminho e
conferido contra o manifest.tsv versionado; divergencia aborta. Um par ocupa
~2,8 GB de RAM mais as arvores.

Somente leitura. Escreve um JSON (regravado a cada par, campo "completo").

USO (na Ubuntu; exige scipy)
    python3 experimentos/diagnosticar_ply_pareado.py --degrau D4b \\
        --out ~/tcc-runs/diag-pareado/D4b.json
    python3 experimentos/diagnosticar_ply_pareado.py --degrau D3 \\
        --remap "/home/fabio/tcc-runs/series=/media/fabio/Seagate Expansion Drive/tcc-runs-arquivo" \\
        --out ~/tcc-runs/diag-pareado/D3.json
  Custo: medir antes com --max-pares 1.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "..", "pivo-reprodutibilidade-3dgs", "dados")
N_PROPS = 59
PADRAO = {"D3": ("run020", [f"run{i:03d}" for i in range(21, 30)]),
          "D4": ("run000", [f"run{i:03d}" for i in range(1, 10)]),
          "D4b": ("run000", [f"run{i:03d}" for i in range(1, 10)])}
QUANTIS = (0.5, 0.9, 0.99, 1.0)
MEDIANA_MAXWELL = 1.5381722544    # mediana de |N(0, I_3)| = sqrt(qui2_3^-1(0,5))
SEMENTE_CALIBRACAO = 20261016


def ler_ply_ram(caminho, bloco=1 << 24):
    """(nomes, matriz uint32 (N, 59) em RAM, sha256 do arquivo). Uma leitura sequencial."""
    h = hashlib.sha256()
    with open(caminho, "rb") as fp:
        cab = b""
        while not cab.endswith(b"end_header\n"):
            linha = fp.readline()
            if not linha:
                raise ValueError(f"{caminho}: cabecalho sem end_header")
            cab += linha
            if len(cab) > 1 << 16:
                raise ValueError(f"{caminho}: cabecalho grande demais")
        h.update(cab)
        linhas = cab.decode("ascii").splitlines()
        if linhas[:2] != ["ply", "format binary_little_endian 1.0"]:
            raise ValueError(f"{caminho}: formato inesperado: {linhas[:2]}")
        n, nomes = None, []
        for ln in linhas[2:]:
            p = ln.split()
            if p[:2] == ["element", "vertex"]:
                n = int(p[2])
            elif p[:2] == ["property", "float"]:
                nomes.append(p[2])
            elif p and p[0] not in ("end_header", "comment"):
                raise ValueError(f"{caminho}: linha de cabecalho nao suportada: {ln!r}")
        if n is None or len(nomes) != N_PROPS:
            raise ValueError(f"{caminho}: N={n}, {len(nomes)} propriedades (esperado {N_PROPS})")
        total = 4 * n * N_PROPS
        buf = bytearray(total)
        mv, lido = memoryview(buf), 0
        while lido < total:
            k = fp.readinto(mv[lido:lido + bloco])
            if not k:
                raise ValueError(f"{caminho}: arquivo truncado ({lido} de {total} bytes)")
            h.update(mv[lido:lido + k])
            lido += k
        resto = fp.read()
        if resto:
            raise ValueError(f"{caminho}: {len(resto)} bytes alem do esperado para N={n}")
    m = np.frombuffer(buf, dtype="<u4").reshape(n, N_PROPS)
    return nomes, m, h.hexdigest()


def quantis(v):
    v = np.asarray(v, dtype=np.float64)
    if v.size == 0:
        return None
    return {f"q{int(q * 100)}": float(np.quantile(v, q)) for q in QUANTIS}


def colunas(nomes, prefixo):
    return [i for i, n in enumerate(nomes) if n.startswith(prefixo)]


class Acumulador:
    """Distribuicao de |delta| sem guardar os valores: zeros e maximo EXATOS;
    quantis por histograma de log10 com bins de 0,01 decada (erro relativo < 2,4%)."""
    LO, HI, PASSO = -20.0, 6.0, 0.01

    def __init__(self):
        self.h = np.zeros(int(round((self.HI - self.LO) / self.PASSO)) + 2, dtype=np.int64)
        self.n = self.zeros = 0
        self.max = 0.0

    def add(self, v):
        v = np.abs(np.asarray(v, dtype=np.float64)).ravel()
        v = v[np.isfinite(v)]
        if not v.size:
            return
        self.n += v.size
        z = v == 0
        self.zeros += int(z.sum())
        self.max = max(self.max, float(v.max()))
        nz = v[~z]
        if nz.size:
            k = np.clip(np.floor((np.log10(nz) - self.LO) / self.PASSO).astype(np.int64) + 1,
                        0, self.h.size - 1)
            self.h += np.bincount(k, minlength=self.h.size)

    def resumo(self):
        if not self.n:
            return None
        out = {"n": self.n, "frac_zero": self.zeros / self.n, "max": self.max}
        cum = self.zeros + np.cumsum(self.h)
        for q in (0.5, 0.9, 0.99):
            alvo = q * self.n
            if self.zeros >= alvo:
                out[f"q{int(q * 100)}"] = 0.0
            else:
                b = int(np.searchsorted(cum, alvo))
                out[f"q{int(q * 100)}"] = min(float(10 ** (self.LO + (b - 0.5) * self.PASSO)), self.max)
        return out


def xyz_de(nomes, m):
    f = m.view("<f4")
    return f[:, [nomes.index(k) for k in ("x", "y", "z")]].astype(np.float64)


def parear(ta, tb, xa, xb, workers=-1):
    """Pares mutuos (ia, ib, distancia). ta/tb: cKDTree de xa/xb."""
    if len(xa) == 0 or len(xb) == 0:
        z = np.zeros(0, dtype=np.int64)
        return z, z, np.zeros(0)
    dab, iab = ta.query(xb, k=1, workers=workers)     # para cada j em B, o mais proximo em A
    _, iba = tb.query(xa, k=1, workers=workers)       # para cada i em A, o mais proximo em B
    ia = np.arange(len(xa))
    mutuo = iab[iba] == ia
    ia, ib = ia[mutuo], iba[mutuo]
    return ia, ib, dab[ib]


def diferencas(nomes, ma, mb, ia, ib, bloco=1 << 19):
    """Diferencas nos pares, em blocos, direto dos float32 brutos (sem copia do modelo)."""
    if ia.size == 0:
        return {}
    fa, fb = ma.view("<f4"), mb.view("<f4")
    c_op, c_sc, c_rt = colunas(nomes, "opacity"), colunas(nomes, "scale_"), colunas(nomes, "rot_")
    c_dc, c_re = colunas(nomes, "f_dc_"), colunas(nomes, "f_rest_")
    acc = {k: Acumulador() for k in ("opacidade_sigmoide", "log_escala", "rotacao_angulo_rad",
                                     "f_dc", "f_rest")}
    sig = lambda x: 1.0 / (1.0 + np.exp(-x))  # noqa: E731
    for i in range(0, ia.size, bloco):
        A = fa[ia[i:i + bloco]].astype(np.float64)
        B = fb[ib[i:i + bloco]].astype(np.float64)
        with np.errstate(over="ignore"):
            acc["opacidade_sigmoide"].add(sig(A[:, c_op]) - sig(B[:, c_op]))
        acc["log_escala"].add(A[:, c_sc] - B[:, c_sc])
        qa, qb = A[:, c_rt], B[:, c_rt]
        with np.errstate(invalid="ignore", divide="ignore"):
            qa = qa / np.linalg.norm(qa, axis=1, keepdims=True)
            qb = qb / np.linalg.norm(qb, axis=1, keepdims=True)
        # angulo de ROTACAO, estavel perto de zero (arccos tem piso ~1e-8 rad).
        # Para unitarios, 2*atan2(|a - s b|, |a + s b|) = phi, o angulo entre os
        # quaternios como vetores 4D; a rotacao relativa e 2*phi. s = sinal do
        # produto interno (q e -q sao a mesma rotacao). Testado contra rotacao conhecida.
        s = np.where(np.sum(qa * qb, axis=1, keepdims=True) < 0, -1.0, 1.0)
        acc["rotacao_angulo_rad"].add(4.0 * np.arctan2(np.linalg.norm(qa - s * qb, axis=1),
                                                       np.linalg.norm(qa + s * qb, axis=1)))
        acc["f_dc"].add(A[:, c_dc] - B[:, c_dc])
        acc["f_rest"].add(A[:, c_re] - B[:, c_re])
    return {k: v.resumo() for k, v in acc.items()}


def fmtq(d, k="q50"):
    return f"{d[k]:.3g}" if d and d.get(k) is not None else "-"


def manifesto(degrau):
    out = {}
    for ln in open(os.path.join(DADOS, degrau, "manifest.tsv")):
        p = ln.rstrip("\n").split("\t")
        if len(p) == 4 and p[1] == "splat.ply":
            out[p[0]] = p[3]
    return out


def caminho_ply(degrau, run, remap):
    orig = open(os.path.join(DADOS, degrau, run, "origem.txt")).read().strip()
    if remap:
        velho, novo = remap
        if orig.startswith(velho):
            orig = novo + orig[len(velho):]
    return os.path.join(orig, "splat.ply")


def gravar(destino, rel):
    tmp = destino + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rel, f, indent=2)
    os.replace(tmp, destino)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--degrau", choices=sorted(PADRAO), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--remap", default="", help="PREFIXO_ANTIGO=PREFIXO_NOVO para origem.txt")
    ap.add_argument("--max-pares", type=int, default=0, help="limita o numero de pares (medir custo)")
    ap.add_argument("--sem-indice", action="store_true", help="pula a medida estrita por indice")
    ap.add_argument("--ref", default="", help="sobrepoe a referencia padrao (ex.: par sem a referencia)")
    ap.add_argument("--outros", default="", help="sobrepoe a lista padrao, separada por virgula")
    ap.add_argument("--calibrar", default="",
                    help="deslocamentos medianos-alvo, separados por virgula: compara a referencia "
                         "com ela mesma deslocada (correspondencia conhecida); so geometria")
    ap.add_argument("--so-calibrar", action="store_true", help="faz so a calibracao, sem pares")
    a = ap.parse_args()
    if a.max_pares < 0:
        ap.error("--max-pares precisa ser >= 0")
    remap = None
    if a.remap:
        if "=" not in a.remap:
            ap.error("--remap precisa ser PREFIXO_ANTIGO=PREFIXO_NOVO")
        remap = tuple(a.remap.split("=", 1))

    from scipy.spatial import cKDTree  # noqa: E402  (falha cedo se scipy faltar)
    sys.path.insert(0, AQUI)
    from diagnosticar_ply_d4 import comparar  # type: ignore  # medida estrita de 2026-10-05

    ref, outros = PADRAO[a.degrau]
    if a.ref:
        ref = a.ref
    if a.outros:
        outros = [x.strip() for x in a.outros.split(",") if x.strip()]
    if ref in outros:
        ap.error("a referencia nao pode estar em --outros")
    alvos = []
    if a.calibrar:
        try:
            alvos = [float(x) for x in a.calibrar.split(",") if x.strip()]
        except ValueError:
            ap.error(f"--calibrar invalido: {a.calibrar!r}")
        if not alvos or any(x <= 0 for x in alvos):
            ap.error("--calibrar precisa de deslocamentos > 0")
    if a.max_pares:
        outros = outros[:a.max_pares]
    man = manifesto(a.degrau)
    caminhos = {r: caminho_ply(a.degrau, r, remap) for r in [ref] + outros}
    faltam = [p for p in caminhos.values() if not os.path.exists(p)]
    if faltam:
        print(f"ABORTA: .ply ausente(s): {faltam[:3]}", file=sys.stderr)
        return 1
    if any(r not in man for r in caminhos):
        print("ABORTA: execucao sem sha256 no manifest.tsv", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    rel = {"gerado_em": datetime.now(timezone.utc).isoformat(),
           "proposito": "diagnostico pareado (exploratorio, caderno 2026-10-16); pre-registro §4",
           "degrau": a.degrau, "referencia": ref, "outros": outros, "remap": a.remap or None,
           "instrumento": "vizinho mais proximo mutuo em xyz (scipy cKDTree)",
           "pares": {}, "completo": False}

    t0 = time.perf_counter()
    nomes, ma, sha = ler_ply_ram(caminhos[ref])
    if sha != man[ref]:
        print(f"ABORTA: sha256 de {ref} difere do manifesto", file=sys.stderr)
        return 1
    pa_xyz = xyz_de(nomes, ma)
    ta = cKDTree(pa_xyz) if len(pa_xyz) else None
    if ta is not None and len(pa_xyz) > 1:
        dloc = ta.query(pa_xyz, k=2, workers=-1)[0][:, 1]
    else:
        dloc = np.zeros(0)
    rel["referencia_n"] = int(ma.shape[0])
    rel["espacamento_local_ref"] = quantis(dloc)
    rel["t_referencia_s"] = round(time.perf_counter() - t0, 1)
    print(f"[pareado] {a.degrau} ref {ref}: N={ma.shape[0]}, sha256 ok, "
          f"espacamento local mediano {fmtq(rel['espacamento_local_ref'])}, "
          f"{rel['t_referencia_s']} s", flush=True)

    if alvos:
        if ta is None or len(pa_xyz) < 2:
            print("ABORTA: calibracao exige referencia com N >= 2", file=sys.stderr)
            return 1
        rng = np.random.default_rng(SEMENTE_CALIBRACAO)
        sp = (rel["espacamento_local_ref"] or {}).get("q50")
        rel["calibracao"] = []
        for alvo in alvos:
            tc = time.perf_counter()
            sigma = alvo / MEDIANA_MAXWELL
            xb = pa_xyz + rng.normal(0.0, sigma, pa_xyz.shape)
            ia, ib, d = parear(ta, cKDTree(xb), pa_xyz, xb)
            n = len(pa_xyz)
            c = {"alvo_deslocamento_mediano": alvo, "sigma": sigma,
                 "deslocamento_real": quantis(np.linalg.norm(xb - pa_xyz, axis=1)),
                 "razao_alvo_espacamento": alvo / sp if sp else None,
                 "fracao_pareada": ia.size / n, "acerto": float(np.mean(ia == ib)) if ia.size else None,
                 "cobertura": float(np.sum(ia == ib) / n), "distancia_par": quantis(d),
                 "t_s": round(time.perf_counter() - tc, 1)}
            rel["calibracao"].append(c)
            gravar(a.out, rel)
            print(f"[calibracao] alvo {alvo:.3g} (razao {c['razao_alvo_espacamento']:.3g}): pareada "
                  f"{c['fracao_pareada']:.4f}, acerto {c['acerto']}, cobertura {c['cobertura']:.4f}, "
                  f"{c['t_s']} s", flush=True)
            del xb
    if a.so_calibrar:
        outros = []

    for r in outros:
        t1 = time.perf_counter()
        nb, mb, shb = ler_ply_ram(caminhos[r])
        if nb != nomes:
            print(f"ABORTA: {r} tem propriedades em ordem diferente", file=sys.stderr)
            return 1
        if shb != man[r]:
            print(f"ABORTA: sha256 de {r} difere do manifesto", file=sys.stderr)
            return 1
        t_le = time.perf_counter() - t1
        pb_xyz = xyz_de(nomes, mb)
        tb = cKDTree(pb_xyz) if len(pb_xyz) else None
        if ta is not None and tb is not None:
            ia, ib, d = parear(ta, tb, pa_xyz, pb_xyz)
        else:
            ia, ib, d = np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0)
        par = {"n_ref": int(ma.shape[0]), "n_outro": int(mb.shape[0]), "pares_mutuos": int(ia.size),
               "fracao_pareada_ref": ia.size / max(ma.shape[0], 1),
               "fracao_pareada_outro": ia.size / max(mb.shape[0], 1),
               "distancia_par": quantis(d), "diferencas_nos_pares": diferencas(nomes, ma, mb, ia, ib)}
        if ma.shape == mb.shape:
            par["validacao_indice"] = {
                "acerto": float(np.mean(ia == ib)) if ia.size else None,
                "cobertura": float(np.sum(ia == ib) / max(ma.shape[0], 1))}
            if not a.sem_indice:
                par["estrita_por_indice"] = comparar(nomes, ma, mb)
        par["t_leitura_s"] = round(t_le, 1)
        par["t_total_s"] = round(time.perf_counter() - t1, 1)
        rel["pares"][r] = par
        gravar(a.out, rel)
        v = par.get("validacao_indice", {})
        print(f"[pareado] {ref} x {r}: N {mb.shape[0]}, pareada {par['fracao_pareada_ref']:.4f}, "
              f"dist mediana {fmtq(par['distancia_par'])}, "
              f"acerto {v.get('acerto', '-')}, leitura {t_le:.0f} s, total {par['t_total_s']} s", flush=True)
        del nb, mb, pb_xyz, tb

    rel["completo"] = True
    rel["fim"] = datetime.now(timezone.utc).isoformat()
    gravar(a.out, rel)
    print(f"\nrelatorio: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
