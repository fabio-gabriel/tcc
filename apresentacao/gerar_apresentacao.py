#!/usr/bin/env python3
"""
Gera a apresentacao para o Prof. Gilvan e o documento de notas, a partir dos
dados versionados em pivo-reprodutibilidade-3dgs/dados/.

Regras do gerador:
- todo numero que vem de dados e calculado aqui (funcao `c`);
- numero que so existe em documento versionado (pre-registro, PLANO) entra por
  `doc`, com a secao de origem;
- numero que so existe no caderno de campo (saida de terminal colada, projecao)
  entra por `cad` e aparece no slide com o sinal de adaga;
- cada numero usado fica registrado e e listado nas notas, com a fonte.

Uso:   python3 apresentacao/gerar_apresentacao.py [--data AAAA-MM-DD]
       --data e a data da reuniao; sem ela, a contagem de dias parte da data
       de geracao, e o slide diz isso.
Saida: apresentacao/apresentacao-gilvan.html  (slides: setas, espaco ou clique;
       ?todos mostra todos os slides empilhados)
       apresentacao/notas-gilvan.html         (ressalvas completas e fontes)
"""
import argparse, datetime as dt, html, itertools, json, math, re
from pathlib import Path
import numpy as np
from scipy.stats import chi2, fligner

ap = argparse.ArgumentParser()
ap.add_argument("--data", help="data da reuniao, AAAA-MM-DD")
ARGS = ap.parse_args()

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DADOS = RAIZ / "pivo-reprodutibilidade-3dgs" / "dados"
SAIDA = AQUI / "apresentacao-gilvan.html"
SAIDA_NOTAS = AQUI / "notas-gilvan.html"
DEG = ["D0", "D1", "D2", "D3", "D4"]
SEED = 20260909          # pre-registro §5.2 e caderno 2026-09-22
B = 10000                # reamostragens bootstrap, pre-registro §5.2
LIM_H2 = 0.10            # dB, pre-registro §6

# ======================================================= registro de numeros
REG, _SL = [], [0]
F_CAD = "caderno de campo"

def _r(txt, rot, fonte, tipo):
    REG.append(dict(slide=_SL[0], valor=txt, rotulo=rot, fonte=fonte, tipo=tipo))
    return txt

def c(txt, rot, fonte):
    """numero calculado aqui a partir do arquivo citado"""
    return _r(txt, rot, fonte, "calculado")

def doc(txt, rot, fonte):
    """numero que existe so em documento versionado"""
    return _r(txt, rot, fonte, "documento")

def cad(txt, rot, fonte):
    """numero que so existe no caderno de campo: leva adaga no slide"""
    _r(txt, rot, fonte, "caderno")
    return txt + '<sup class="dag">†</sup>'

# ============================================================== formatacao
SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

def br(x, nd=2):
    s = f"{abs(x):,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 and float(s.replace(".", "").replace(",", ".")) != 0 else "") + s

def ib(x):
    return br(x, 0)

def sci(x, nd=1):
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    if round(m, nd) >= 10:
        m, e = m / 10, e + 1
    return f"{br(m, nd)}·10{str(e).translate(SUP)}"

def pct(x, nd=1):
    return br(100 * x, nd) + "%"

def faixa_pct(xs, rot, fonte):
    a, b = pct(min(xs), 0), pct(max(xs), 0)
    return c(a if a == b else f"{a} a {b}", rot, fonte)

def dm(d):
    return f"{d.day:02d}/{['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'][d.month-1]}"

esc = lambda s: html.escape(s, quote=False)

# =================================================================== dados
ANSI = re.compile(rb"\x1b\[[0-9;]*[A-Za-z]")
PAT = re.compile(rb"(\d+) dupli, (\d+) split, (\d+) prune -> (\d+) splats")
TS = re.compile(r"/(\d{8}_\d{6})_garden/")

def carregar(deg):
    runs = []
    for rd in sorted((DADOS / deg).glob("run*")):
        ev = json.load(open(rd / "eval.json"))
        tr = json.load(open(rd / "train.json"))
        env = json.load(open(rd / "env.json"))
        log = ANSI.sub(b"", next(rd.glob("run*.log")).read_bytes())
        amb = rd / "ambiente.json"
        m = TS.search(ev["images"][0]["im_render"])
        runs.append(dict(
            idx=int(rd.name[3:]), psnr=ev["mean"]["psnr"], ssim=ev["mean"]["ssim"],
            lpa=ev["mean"]["lpips_alex"], n=tr["num_splats"], t=tr["time_elapsed"],
            dens=[int(x[3]) for x in PAT.findall(log)],
            commit=env["vksplat_commit"], dirty=env["vksplat_dirty"], dev=env["train_device"],
            gpu=b"(RADV GFX1201) - VIABLE" in log, dev0=b"Using device [0]" in log,
            emul=b"USE_EMULATED" in log,
            amb=json.load(open(amb)) if amb.exists() else None,
            inicio=m.group(1) if m else None))
    hashes = [l.split("\t")[3] for l in open(DADOS / deg / "manifest.tsv")
              if l.split("\t")[1:2] == ["splat.ply"]]
    return runs, hashes

R, H = {}, {}
for d in DEG:
    R[d], H[d] = carregar(d)
arr = lambda d, k: np.array([r[k] for r in R[d]], float)
P = {d: arr(d, "psnr") for d in DEG}
NS = {d: arr(d, "n") for d in DEG}
T = {d: arr(d, "t") for d in DEG}
SS = {d: arr(d, "ssim") for d in DEG}
LA = {d: arr(d, "lpa") for d in DEG}
IDX = {d: np.array([r["idx"] for r in R[d]]) for d in DEG}
iqr = lambda v: float(np.subtract(*np.percentile(v, [75, 25])))
med = lambda v: float(np.median(v))

def boot(x, y, rng):
    """IC 95% percentilico da razao IQR(y)/IQR(x), pre-registro §5.2"""
    bs = []
    for _ in range(B):
        ix = iqr(rng.choice(x, len(x)))
        bs.append(iqr(rng.choice(y, len(y))) / ix if ix > 0 else np.nan)
    return np.nanpercentile(bs, [2.5, 97.5])

def frac_pares(x):
    pr = list(itertools.combinations(x, 2))
    k = sum(abs(a - b) >= LIM_H2 for a, b in pr)
    return k, len(pr)

# ---- H1
h_all = [h for d in DEG for h in H[d]]
n_exec, n_dist = len(h_all), len(set(h_all))
h1_d0 = (len(set(H["D0"])), len(H["D0"]))
h_d4 = (len(set(H["D4"])), len(H["D4"]))
assert n_exec == sum(len(R[d]) for d in DEG)

# ---- H2
h2_k, h2_n = frac_pares(P["D0"])
h2_frac = h2_k / h2_n
h2_por_n = {n: (lambda kn: kn[0] / kn[1])(frac_pares(P["D0"][IDX["D0"] < n])) for n in (10, 20)}
h2_bloco = [(lambda kn: kn[0] / kn[1])(frac_pares(P["D0"][(IDX["D0"] >= 10 * b) & (IDX["D0"] < 10 * b + 10)])) for b in range(3)]
h2_bloco_d2 = [(lambda kn: kn[0] / kn[1])(frac_pares(P["D2"][(IDX["D2"] >= 10 * b) & (IDX["D2"] < 10 * b + 10)])) for b in range(3)]
_rng = np.random.default_rng(SEED)
_fr = []
for _ in range(B):
    s = _rng.choice(P["D0"], len(P["D0"]))
    dd = np.abs(s[:, None] - s[None, :])[np.triu_indices(len(s), 1)]
    _fr.append(np.mean(dd >= LIM_H2))
h2_ic = np.percentile(_fr, [2.5, 97.5])
ampl_d0, iqr_d0 = float(np.ptp(P["D0"])), iqr(P["D0"])

# ---- H3.1-H3.3 (um RNG encadeado na ordem abaixo, como no caderno de 2026-09-22)
_rng = np.random.default_rng(SEED)
H3 = []
for a, b in [("D0", "D1"), ("D1", "D2"), ("D2", "D3"), ("D0", "D3")]:
    p = fligner(P[a], P[b]).pvalue
    rz = iqr(P[b]) / iqr(P[a])
    lo, hi = boot(P[a], P[b], _rng)
    H3.append(dict(a=a, b=b, p=p, rz=rz, lo=lo, hi=hi, ok=(p < 0.05 and hi < 1)))
p_global = fligner(*[P[d] for d in DEG[:4]]).pvalue
p_n20 = fligner(P["D0"][IDX["D0"] < 20], P["D3"][IDX["D3"] < 20]).pvalue
rz_n20 = iqr(P["D3"][IDX["D3"] < 20]) / iqr(P["D0"][IDX["D0"] < 20])
IQB = {d: [iqr(P[d][(IDX[d] >= 10 * b) & (IDX[d] < 10 * b + 10)]) for b in range(3)] for d in DEG[:4]}
var_d3 = max(IQB["D3"]) / min(IQB["D3"])

# ---- D3 -> D4
p34 = fligner(P["D3"], P["D4"]).pvalue
rz34 = iqr(P["D4"]) / iqr(P["D3"])
lo34, hi34 = boot(P["D3"], P["D4"], np.random.default_rng(SEED))
d3s = IDX["D3"] >= 20
p34s = fligner(P["D3"][d3s], P["D4"]).pvalue
rz34s = iqr(P["D4"]) / iqr(P["D3"][d3s])
lo34s, hi34s = boot(P["D3"][d3s], P["D4"], np.random.default_rng(SEED))
p34n = fligner(NS["D3"], NS["D4"]).pvalue
rz34n = iqr(NS["D4"]) / iqr(NS["D3"])
lo34n, hi34n = boot(NS["D3"], NS["D4"], np.random.default_rng(SEED))
dq = med(P["D4"]) - med(P["D3"])
dt_pct = med(T["D4"]) / med(T["D3"]) - 1
morton_pct = med(T["D3"]) / med(T["D2"]) - 1
run_max_d4 = R["D4"][int(np.argmax(P["D4"]))]["idx"]
P4_sem_max = np.sort(P["D4"])[:-1]

# ---- gradientes medidos em D3 (dados/gradientes/), escala do §11.2
G = [json.load(open(DADOS / f"gradientes/gradientes_rep0{i}.json")) for i in range(3)]
G_STEPS = [r["step"] for r in G[0]["registros"]]
CON = ["conic_0", "conic_1", "conic_2"]

def gmax(comp, cond):
    return max(r["componentes"][comp]["max_abs"] for g in G for r in g["registros"] if cond(r["step"]))

S_ESC = {k: math.floor(math.log2(2 ** 30 / gmax(k, lambda s: True))) for k in CON}
P99Q = {k: {r["step"]: max(g["registros"][j]["componentes"][k]["p99_abs"] for g in G) * 2 ** S_ESC[k]
            for j, r in enumerate(G[0]["registros"])} for k in CON}

def desde_abaixo_de_1(k):
    passos = [s for s in G_STEPS if s >= 1000]
    for s in passos:
        if all(P99Q[k][t] < 1 for t in passos if t >= s):
            return s

P99_DESDE = {k: desde_abaixo_de_1(k) for k in CON}
P99_REGIME = {k: [P99Q[k][s] for s in G_STEPS if s >= P99_DESDE[k]] for k in CON}
MAX_ESP_5000 = {k: gmax(k, lambda s: s >= 5000) for k in CON}
S_REGIME = {k: math.floor(math.log2(2 ** 30 / MAX_ESP_5000[k])) for k in CON}
L_ACC = 2147483520.0                                   # pre-registro §11.2
CAPAC = {k: L_ACC / 2 ** S_REGIME[k] for k in CON}
MAX_ESP_10K = {k: max(r["componentes"][k]["max_abs"] for g in G for r in g["registros"] if r["step"] in (10000, 12500)) for k in CON}
# saida de terminal do modo --custo de medir_conica_d4b.py, 50 amostras 10.010-10.500,
# colada no caderno em 2026-10-15; nao ha arquivo em dados/
CUSTO_DENSO = {"conic_0": 35.3, "conic_1": 51.6, "conic_2": 20.9}
RAZ_DENSO = {k: CUSTO_DENSO[k] / MAX_ESP_10K[k] for k in CON}

# ---- diagnostico dos .ply de D4
DPLY = json.load(open(DADOS / "D4/diagnostico_ply.json"))
pares_ply = DPLY["pares"]
mesmo_ms = sum(p["mesmo_multiconjunto"] for p in pares_ply.values())
ident_b = sum(p["identicos_byte_a_byte"] for p in pares_ply.values())
iguais_n = {k: p for k, p in pares_ply.items() if "fracao_gaussianas_diferentes" in p}
fr_gauss = [p["fracao_gaussianas_diferentes"] for p in iguais_n.values()]

def frac_prop(p, pref):
    ks = [k for k in DPLY["propriedades"] if k.startswith(pref)]
    return sum(p["valores_diferentes_por_propriedade"][k] for k in ks) / (len(ks) * p["n_b"])

fr_pos = [frac_prop(p, ("x", "y", "z")) for p in iguais_n.values()]
fr_esc = [frac_prop(p, "scale_") for p in iguais_n.values()]
fr_rot = [frac_prop(p, "rot_") for p in iguais_n.values()]

# ---- densificacao (bloco de N=10 do mesmo estrato em D0-D3; todas em D4)
REFINE_START, REFINE_EVERY = 500, 100                  # simple_trainer.py:42-44 (caderno 2026-10-05)
passo_ev = lambda i: REFINE_START + REFINE_EVERY * (i + 1)

def bloco(d):
    return [r for r in R[d] if d == "D4" or r["idx"] >= 20]

def spread(d):
    S = [r["dens"] for r in bloco(d)]
    L = min(map(len, S))
    return [max(s[i] for s in S) - min(s[i] for s in S) for i in range(L)]

SP = {d: spread(d) for d in DEG}
onset = {d: next((i for i, v in enumerate(SP[d]) if v > 0), None) for d in DEG}
n_ev = len(SP["D4"])
grupo_d4 = max(sum(1 for r in R["D4"] if r["dens"] == s["dens"]) for s in R["D4"])
seq_d4 = len({tuple(r["dens"]) for r in R["D4"]})

# ---- rastreamento de D4
def comparar_traj(fa, fb):
    A = json.load(open(DADOS / fa))["registros"]
    Bm = {r["step"]: r for r in json.load(open(DADOS / fb))["registros"]}
    ultimo, nbuf = None, sum(len(v) for k, v in A[0].items() if k != "step")
    for r in A:
        rb = Bm.get(r["step"])
        if rb is None:
            continue
        dif = [(e, b) for e in r if e != "step" for b, v in r[e].items()
               if rb[e].get(b) is None or v["h"] != rb[e][b]["h"] or v["shape"] != rb[e][b]["shape"]]
        if dif:
            com_conteudo = sum(1 for e in r if e != "step" for v in r[e].values() if np.prod(v["shape"]) > 0)
            return dict(ultimo=ultimo, primeiro=r["step"], dif=dif, amostras=len(A), nbuf=nbuf,
                        com_conteudo=com_conteudo, estagios=[e for e in r if e != "step"])
        ultimo = r["step"]
    return dict(ultimo=ultimo, primeiro=None, dif=[], amostras=len(A), nbuf=nbuf)

TR_L = comparar_traj("D4/trajetoria_rep00.json", "D4/trajetoria_rep01.json")
TR_D = comparar_traj("D4/trajetoria_denso_rep00.json", "D4/trajetoria_denso_rep01.json")
REFINE_STOP = 15000                                   # gs_trainer.cpp / simple_trainer.py (caderno 2026-10-05)
ultima_dens = passo_ev(n_ev - 1)

# ---- teste de estagios
EST = {k: json.load(open(DADOS / f"estagios/estagios_{k}.json")) for k in ("D3", "D4", "D4_fase2", "D4_captura")}
BUF = ["pixel_state", "n_contributors", "v_pixel_state", "v_xy_vs", "v_inv_cov_vs_opacity", "v_rgb"]
BWD = ["v_xy_vs", "v_inv_cov_vs_opacity", "v_rgb"]
FWD = ["pixel_state", "n_contributors", "v_pixel_state"]

def resumo_fase1(k):
    e = EST[k]
    kk, pts = e["meta"]["k"], e["resultados"]
    reps = kk * len(pts)
    bwd_dist = min(sum(r["buffers"][b]["distintos"] for r in pts) for b in BWD)
    fwd_max = max(r["buffers"][b]["distintos"] for r in pts for b in FWD)
    eventos = sum(max(kk - max(r["buffers"][b]["multiplicidades"]) for b in BUF) for r in pts)
    lim = pts[0]["buffers"]["pixel_state"]["limite_sup_95"]
    return dict(k=kk, npts=len(pts), reps=reps, bwd_dist=bwd_dist, fwd_max=fwd_max, eventos=eventos, lim=lim,
                pontos=[r["step"] for r in pts])

F1 = {k: resumo_fase1(k) for k in ("D3", "D4")}
ler_frac = []
for k in ("D3", "D4"):
    for r in EST[k]["resultados"]:
        if r["num_splats"] > 5e6:
            ler_frac.append(np.median(r["tempo"]["leitura_hash_s"]) / np.median(r["tempo"]["rep_s"]))
img_iguais = [r["image_idx"] for r in EST["D3"]["resultados"]] == [r["image_idx"] for r in EST["D4"]["resultados"]]
recomp = [(dt.datetime.fromisoformat(e["meta"]["inicio"]) - dt.datetime.fromisoformat(e["meta"]["modulo_mtime"])).total_seconds()
          for e in EST.values()]

def linhas_d4(k):
    out = []
    for r in EST[k]["resultados"]:
        kk = EST[k]["meta"]["k"]
        ev = sum(kk - max(r["buffers"][b]["multiplicidades"]) for b in BUF)
        bufs_ev = [b for b in BUF if r["buffers"][b]["distintos"] > 1]
        out.append(dict(step=r["step"], k=kk, ev=ev, bufs=bufs_ev,
                        mult=r["buffers"][bufs_ev[0]]["multiplicidades"] if bufs_ev else None,
                        lim=r["buffers"]["pixel_state"]["limite_sup_95"], n=r["num_splats"]))
    return out

F2, CAP = linhas_d4("D4_fase2"), linhas_d4("D4_captura")
reps_d4 = F1["D4"]["reps"] + sum(x["k"] for x in F2 + CAP)
ev_d4 = F1["D4"]["eventos"] + sum(x["ev"] for x in F2 + CAP)

def poisson_ic(k, n):
    lo = chi2.ppf(0.025, 2 * k) / 2 / n if k > 0 else 0.0
    return lo, chi2.ppf(0.975, 2 * k + 2) / 2 / n

ic_tot = poisson_ic(ev_d4, reps_d4)
n_fim_f1 = EST["D4"]["resultados"][-1]["num_splats"]
n_modal_d4 = max(set(NS["D4"]), key=list(NS["D4"]).count)
n_inst = [F2[-1]["n"], CAP[-1]["n"]]

# ---- integridade
INT = {d: dict(n=len(R[d]), commits={r["commit"] for r in R[d]}, limpos=sum(r["dirty"] == "" for r in R[d]),
               dev0=sum(r["dev"] == 0 and r["dev0"] for r in R[d]), gpu=sum(r["gpu"] for r in R[d]),
               emul=sum(r["emul"] for r in R[d])) for d in DEG}
AMB = [r["amb"] for d in DEG for r in R[d] if r["amb"]]
mesa_v = {a["pacotes"]["mesa-vulkan-drivers"] for a in AMB}
libc_v = {a["pacotes"]["libc6"] for a in AMB}
T0 = json.load(open(DADOS / "toolchain/reproducao.json"))
VER = json.load(open(DADOS / "toolchain/verificacao_d4.json"))
inicio_d0 = min(r["inicio"] for r in R["D0"] if r["inicio"])

# ---- mecanismo: exemplo e simulacao
f32 = np.float32
ex_a = f32(f32(16777216) + f32(1)) + f32(1)
ex_b = f32(16777216) + f32(f32(1) + f32(1))
_rs = np.random.default_rng(0)
SIM_N, SIM_ORD = 1000, 20
_g = (_rs.standard_normal(SIM_N) * 1e-6).astype(np.float32)
_q = np.rint(_g.astype(np.float64) * 2 ** 40).astype(np.int64)
_rf, _ri = set(), set()
for _ in range(SIM_ORD):
    o = _rs.permutation(SIM_N)
    acc = f32(0)
    for v in _g[o]:
        acc = f32(acc + v)
    _rf.add(acc.tobytes())
    _ri.add(int(np.sum(_q[o].astype(np.int32), dtype=np.int32)))
sim_f, sim_i = len(_rf), len(_ri)

# ---- datas
DEPOSITO = dt.date(2026, 11, 6)                         # PLANO §1
CONGELA_PROP = dt.date(2026, 10, 16)                   # caderno 2026-10-05 (proposta)
CONGELA = dt.date(2026, 10, 20)                        # caderno 2026-10-15 ("passa de ~20/out")
REF = dt.date.fromisoformat(ARGS.data) if ARGS.data else dt.date.today()
REF_ROT = "reunião" if ARGS.data else "geração"
dias_dep = (DEPOSITO - REF).days
fim_iter = max(CONGELA, REF + dt.timedelta(days=1))
janela = (DEPOSITO - fim_iter).days
serie_h = 10 * med(T["D4"]) / 3600

# ================================================================= SVG
COR = {"D0": "#c2410c", "D1": "#d97706", "D2": "#b7791f", "D3": "#64748b", "D4": "#0f766e"}

def svg_d0_lit():
    W, Hh, ml, mr = 900, 206, 290, 24
    x = P["D0"]
    lo, hi = x.min() - 0.012, x.max() + 0.012
    tx = lambda v: ml + (v - lo) / (hi - lo) * (W - ml - mr)
    y0 = 46
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="PSNR das execuções de D0 e ganhos publicados">']
    o.append(f'<text x="{ml-14}" y="{y0+5}" text-anchor="end" class="lb">{len(x)} execuções idênticas (D0)</text>')
    o.append(f'<line x1="{tx(lo):.1f}" x2="{tx(hi):.1f}" y1="{y0}" y2="{y0}" stroke="#e2e8f0" stroke-width="2"/>')
    for v in x:
        o.append(f'<circle cx="{tx(v):.1f}" cy="{y0}" r="5.5" fill="{COR["D0"]}" fill-opacity=".5"/>')
    for v in np.arange(math.ceil(lo * 20) / 20, hi, 0.05):
        o.append(f'<text x="{tx(v):.1f}" y="{y0+25}" text-anchor="middle" class="ax">{br(v)}</text>')
    o.append(f'<text x="{W-mr}" y="{y0-18}" text-anchor="end" class="ax">PSNR (dB): mesma cena, seed, commit e máquina</text>')
    lit = [("gsplat, feature", 0.03), ('gsplat, "paridade"', 0.05), ("Mip-Splatting, contra 3DGS retreinado", 0.09),
           ("gsplat, feature", 0.11), ("gsplat, feature", 0.18)]
    base = med(x)
    y = 110
    o.append(f'<text x="{ml-14}" y="{y-10}" text-anchor="end" class="ax">ganhos publicados, na mesma escala:</text>')
    for k, (nome, dv) in enumerate(lit):
        doc(f"+{br(dv)} dB", f"delta publicado: {nome}", "pre-registro §6 (levantamento de 2026-08-26)")
        yy = y + k * 19
        x1, x2 = tx(base - dv / 2), tx(base + dv / 2)
        o.append(f'<text x="{ml-14}" y="{yy+10}" text-anchor="end" class="ax">+{br(dv)} dB · {esc(nome)}</text>')
        o.append(f'<rect x="{x1:.1f}" y="{yy}" width="{x2-x1:.1f}" height="12" fill="#334155" rx="2"/>')
    o.append("</svg>")
    return "".join(o)

def svg_iqr_blocos():
    W, Hh, ml, mr, mt, mb = 640, 340, 54, 6, 44, 50
    ymax = 0.068
    ty = lambda v: mt + (1 - v / ymax) * (Hh - mt - mb)
    cw = (W - ml - mr) / 4
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="IQR de PSNR por bloco de 10 execuções">']
    for v in (0, 0.02, 0.04, 0.06):
        o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="#e2e8f0"/>')
        o.append(f'<text x="{ml-8}" y="{ty(v)+4:.1f}" text-anchor="end" class="ax">{br(v,2)}</text>')
    o.append(f'<text x="{ml}" y="14" class="ax">IQR de PSNR (dB), por bloco de 10 execuções</text>')
    o.append(f'<line x1="{ml}" x2="{ml+22}" y1="29" y2="29" stroke="#0f172a" stroke-width="2" stroke-dasharray="6 3"/><text x="{ml+28}" y="33" class="ax">IQR com N = 30</text>')
    rot = []
    for i, d in enumerate(DEG[:4]):
        x0 = ml + cw * i + cw * .1
        bw = cw * .8 / 3
        v30 = iqr(P[d])
        for b, v in enumerate(IQB[d]):
            xb = x0 + b * bw
            o.append(f'<rect x="{xb+2:.1f}" y="{ty(v):.1f}" width="{bw-4:.1f}" height="{ty(0)-ty(v):.1f}" fill="{COR[d]}" fill-opacity="{.45+.2*b:.2f}" rx="2"/>')
            rot.append(f'<text x="{xb+bw/2:.1f}" y="{ty(v)-5:.1f}" text-anchor="middle" class="vl halo">{br(v,3)}</text>')
        o.append(f'<line x1="{x0-4:.1f}" x2="{x0+3*bw+4:.1f}" y1="{ty(v30):.1f}" y2="{ty(v30):.1f}" stroke="#0f172a" stroke-width="2" stroke-dasharray="6 3"/>')
    o.extend(rot)
    for i, d in enumerate(DEG[:4]):
        x0 = ml + cw * i + cw * .1
        bw = cw * .8 / 3
        o.append(f'<text x="{x0+1.5*bw:.1f}" y="{Hh-26}" text-anchor="middle" class="lb">{d}</text>')
        o.append(f'<text x="{x0+1.5*bw:.1f}" y="{Hh-9}" text-anchor="middle" class="ax">blocos 1 · 2 · 3</text>')
    o.append("</svg>")
    return "".join(o)

def svg_d3_d4():
    W, Hh, ml, mr, mt, mb = 520, 380, 66, 16, 18, 44
    lo = math.floor((P["D4"].min() - 0.02) * 20) / 20
    hi = math.ceil((P["D3"].max() + 0.02) * 20) / 20
    ty = lambda v: mt + (hi - v) / (hi - lo) * (Hh - mt - mb)
    cols = [("D3", 0.32), ("D4", 0.74)]
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="PSNR absoluto de D3 e D4">']
    for v in np.arange(lo, hi + 1e-9, 0.1):
        o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="#e2e8f0"/>')
        o.append(f'<text x="{ml-8}" y="{ty(v)+4:.1f}" text-anchor="end" class="ax">{br(v,1)}</text>')
    o.append(f'<text x="16" y="{(mt+Hh-mb)/2:.0f}" transform="rotate(-90 16 {(mt+Hh-mb)/2:.0f})" text-anchor="middle" class="ax">PSNR (dB)</text>')
    rng = np.random.default_rng(7)
    for d, fx in cols:
        cx = ml + fx * (W - ml - mr)
        q1, q3 = np.percentile(P[d], [25, 75])
        o.append(f'<rect x="{cx-60:.1f}" y="{ty(q3):.1f}" width="120" height="{max(ty(q1)-ty(q3),1.5):.1f}" fill="{COR[d]}" fill-opacity=".16"/>')
        o.append(f'<line x1="{cx-66:.1f}" x2="{cx+66:.1f}" y1="{ty(med(P[d])):.1f}" y2="{ty(med(P[d])):.1f}" stroke="{COR[d]}" stroke-width="2.5"/>')
        for v in P[d]:
            o.append(f'<circle cx="{cx+rng.uniform(-48,48):.1f}" cy="{ty(v):.1f}" r="4.4" fill="{COR[d]}" fill-opacity=".72"/>')
        o.append(f'<text x="{cx:.0f}" y="{Hh-22}" text-anchor="middle" class="lb">{d}</text>')
        o.append(f'<text x="{cx:.0f}" y="{Hh-6}" text-anchor="middle" class="ax">N = {len(P[d])}</text>')
        yl = ty(P[d].max()) - 12 if d == "D3" else ty(P[d].max()) - 12
        o.append(f'<text x="{cx+72:.0f}" y="{ty(med(P[d]))+4:.1f}" class="vl">{br(med(P[d]),3)}</text>')
        o.append(f'<text x="{cx:.0f}" y="{yl:.1f}" text-anchor="middle" class="ax halo">IQR {br(iqr(P[d]),4)} dB</text>')
    o.append("</svg>")
    return "".join(o)

def svg_onset():
    W, Hh, ml, mr, mt, mb = 900, 236, 64, 20, 30, 40
    L = n_ev
    ymax = max(max(SP[d]) for d in DEG)
    s0, s1 = passo_ev(0), passo_ev(L - 1)
    tx = lambda s: ml + (s - s0) / (s1 - s0) * (W - ml - mr)
    ty = lambda v: mt + (1 - math.log10(1 + v) / math.log10(1 + ymax)) * (Hh - mt - mb)
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="Diferença de número de gaussianas entre execuções, por evento de densificação">']
    for v in (0, 10, 100, 1000, 10000):
        if v <= ymax:
            o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="#e2e8f0"/>')
            o.append(f'<text x="{ml-8}" y="{ty(v)+4:.1f}" text-anchor="end" class="ax">{ib(v)}</text>')
    for s in (s0, 3000, 6000, 9000, 12000, s1):
        o.append(f'<text x="{tx(s):.1f}" y="{Hh-20}" text-anchor="middle" class="ax">{ib(s)}</text>')
    o.append(f'<text x="{(ml+W-mr)/2:.0f}" y="{Hh-3}" text-anchor="middle" class="ax">passo de treino dos {L} eventos de densificação</text>')
    o.append(f'<text x="{ml}" y="14" class="ax">máx − mín do nº de gaussianas entre 10 execuções (escala log)</text>')
    for d in DEG:
        pts = " ".join(f"{tx(passo_ev(i)):.1f},{ty(v):.1f}" for i, v in enumerate(SP[d]))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{COR[d]}" stroke-width="{3.4 if d=="D4" else 1.6}" stroke-opacity="{1 if d in ("D3","D4") else .55}"/>')
    s4 = passo_ev(onset["D4"])
    o.append(f'<line x1="{tx(s4):.1f}" x2="{tx(s4):.1f}" y1="{mt}" y2="{Hh-mb}" stroke="{COR["D4"]}" stroke-dasharray="4 4"/>')
    o.append(f'<text x="{tx(s4)-10:.1f}" y="{ty(2):.1f}" text-anchor="end" class="lb halo" fill="{COR["D4"]}">D4: divergem a partir do evento {onset["D4"]}, passo {ib(s4)}</text>')
    o.append(f'<text x="{tx(2600):.1f}" y="{ty(1800):.1f}" class="lb halo" fill="#334155">D0 a D3: divergem no primeiro evento</text>')
    lx = W - mr - 5 * 60
    for k, d in enumerate(DEG):
        x = lx + k * 60
        o.append(f'<line x1="{x}" x2="{x+18}" y1="10" y2="10" stroke="{COR[d]}" stroke-width="3"/><text x="{x+22}" y="14" class="ax">{d}</text>')
    o.append("</svg>")
    return "".join(o)

ROT_BUF = {"pixel_state": "imagem", "n_contributors": "contrib.", "v_pixel_state": "∂ perda",
           "v_xy_vs": "∂ xy", "v_inv_cov_vs_opacity": "∂ cônica", "v_rgb": "∂ cor"}

def svg_estagios():
    cw, ch, top, lab, gap = 50, 25, 68, 60, 34
    pw = lab + 6 * cw
    W, Hh = 2 * pw + gap + 4, 68 + 7 * 25 + 6
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="Hashes distintos por buffer e passo, D3 e D4">']
    for p_i, (k, x0) in enumerate((("D3", 2), ("D4", 2 + pw + gap))):
        e = EST[k]
        kk = e["meta"]["k"]
        o.append(f'<text x="{x0}" y="15" class="lb" fill="{COR[k]}">{k}: hashes distintos em {kk} repetições</text>')
        for gname, a, b in (("forward", 0, 2), ("perda", 2, 3), ("backward", 3, 6)):
            gx = x0 + lab + a * cw
            o.append(f'<line x1="{gx+3}" x2="{x0+lab+b*cw-3}" y1="36" y2="36" stroke="#94a3b8"/>')
            o.append(f'<text x="{(gx+x0+lab+b*cw)/2:.0f}" y="31" text-anchor="middle" class="ax">{gname}</text>')
        o.append(f'<text x="{x0+lab-8}" y="{top-12}" text-anchor="end" class="ax">passo</text>')
        for j, bname in enumerate(BUF):
            o.append(f'<text x="{x0+lab+j*cw+cw/2:.0f}" y="{top-12}" text-anchor="middle" class="ax">{ROT_BUF[bname]}</text>')
        for i, r in enumerate(e["resultados"]):
            y = top + i * ch
            o.append(f'<text x="{x0+lab-8}" y="{y+ch/2+4:.0f}" text-anchor="end" class="ax">{ib(r["step"])}</text>')
            for j, bname in enumerate(BUF):
                v = r["buffers"][bname]["distintos"]
                fill = "#f1f5f9" if v == 1 else ("#c2410c" if v == kk else "#fdba74")
                txt_c = "#0f172a" if v == 1 else "#fff"
                o.append(f'<rect x="{x0+lab+j*cw+2}" y="{y+2}" width="{cw-4}" height="{ch-4}" rx="3" fill="{fill}"/>')
                o.append(f'<text x="{x0+lab+j*cw+cw/2:.0f}" y="{y+ch/2+5:.0f}" text-anchor="middle" class="cel" fill="{txt_c}">{v}</text>')
    o.append("</svg>")
    return "".join(o)

def svg_conica():
    W, Hh, ml, mr, mt, mb = 500, 316, 56, 10, 62, 40
    lo, hi = -2, 2
    ty = lambda v: mt + (hi - math.log10(v)) / (hi - lo) * (Hh - mt - mb)
    cw = (W - ml - mr) / 3
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="Máximo do gradiente de cônica: amostragem esparsa e densa">']
    for e in range(lo, hi + 1):
        o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(10**e):.1f}" y2="{ty(10**e):.1f}" stroke="#e2e8f0"/>')
        o.append(f'<text x="{ml-8}" y="{ty(10**e)+4:.1f}" text-anchor="end" class="ax">{br(10**e, max(0,-e))}</text>')
    o.append(f'<text x="{ml}" y="14" class="ax">máximo |gradiente acumulado| perto do passo 10.000 (log)</text>')
    o.append(f'<rect x="{ml}" y="24" width="12" height="10" fill="#64748b"/><text x="{ml+17}" y="33" class="ax">esparsa: passos 10.000 e 12.500, 3 repetições</text>')
    o.append(f'<rect x="{ml+262}" y="24" width="12" height="10" fill="#c2410c"/><text x="{ml+279}" y="33" class="ax">densa: 50 passos †</text>')
    o.append(f'<line x1="{ml}" x2="{ml+14}" y1="46" y2="46" stroke="#0f172a" stroke-width="2" stroke-dasharray="5 3"/><text x="{ml+19}" y="50" class="ax">capacidade do acumulador com a escala que os dados esparsos dariam</text>')
    for i, k in enumerate(CON):
        x0 = ml + cw * i + cw * .16
        bw = cw * .3
        for b, (v, col) in enumerate(((MAX_ESP_10K[k], "#64748b"), (CUSTO_DENSO[k], "#c2410c"))):
            xb = x0 + b * (bw + 6)
            o.append(f'<rect x="{xb:.1f}" y="{ty(v):.1f}" width="{bw:.1f}" height="{ty(10**lo)-ty(v):.1f}" fill="{col}" rx="2"/>')
            o.append(f'<text x="{xb+bw/2:.1f}" y="{ty(v)-5:.1f}" text-anchor="middle" class="vl">{br(v, 2 if v < 1 else 1)}</text>')
        yc = ty(CAPAC[k])
        o.append(f'<line x1="{x0-8:.1f}" x2="{x0+2*bw+14:.1f}" y1="{yc:.1f}" y2="{yc:.1f}" stroke="#0f172a" stroke-width="2" stroke-dasharray="5 3"/>')
        o.append(f'<text x="{x0+bw+3:.1f}" y="{Hh-22}" text-anchor="middle" class="lb">{k.replace("conic_","cônica ")}</text>')
        o.append(f'<text x="{x0+bw+3:.1f}" y="{Hh-6}" text-anchor="middle" class="ax">capacidade {br(CAPAC[k],0)} (s = {S_REGIME[k]})</text>')
    o.append("</svg>")
    return "".join(o)

def svg_tempo():
    W, Hh, ml, mr = 900, 150, 20, 20
    d0, d1 = min(REF, CONGELA_PROP) - dt.timedelta(days=1), DEPOSITO + dt.timedelta(days=1)
    tx = lambda d: ml + (d - d0).days / (d1 - d0).days * (W - ml - mr)
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g" role="img" aria-label="Linha do tempo até o depósito">']
    o.append(f'<line x1="{ml}" x2="{W-mr}" y1="104" y2="104" stroke="#cbd5e1"/>')
    d = d0
    while d <= d1:
        o.append(f'<line x1="{tx(d):.1f}" x2="{tx(d):.1f}" y1="100" y2="108" stroke="#cbd5e1"/>')
        d += dt.timedelta(days=1)
    yb = 56
    o.append(f'<rect x="{tx(REF):.1f}" y="{yb}" width="{tx(fim_iter)-tx(REF):.1f}" height="26" rx="4" fill="#0f766e" fill-opacity=".85"/>')
    o.append(f'<text x="{tx(REF)+8:.1f}" y="{yb+18}" class="sm" fill="#fff">iterações restantes</text>')
    o.append(f'<rect x="{tx(fim_iter):.1f}" y="{yb}" width="{tx(DEPOSITO)-tx(fim_iter):.1f}" height="26" rx="4" fill="#c2410c" fill-opacity=".85"/>')
    o.append(f'<text x="{(tx(fim_iter)+tx(DEPOSITO))/2:.1f}" y="{yb+18}" text-anchor="middle" class="sm" fill="#fff">escrita: no máximo {janela} dias</text>')
    marcos = [(REF, f"{REF_ROT}: {dm(REF)}", "#0f172a"), (CONGELA_PROP, f"{dm(CONGELA_PROP)}: congelamento proposto em 05/out, adiado", "#64748b"),
              (CONGELA, f"~{dm(CONGELA)}: congelamento atual", "#0f172a"), (DEPOSITO, f"{dm(DEPOSITO)}: depósito", "#9a3412")]
    for k, (dd, txt, col) in enumerate(marcos):
        if dd < d0 or (dd == CONGELA_PROP and dd < REF):
            continue
        x = tx(dd)
        y = 136 if k % 2 == 0 else 24
        anc = "end" if dd == DEPOSITO else "start"
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y-10 if y>100 else y+6}" y2="{100 if y>100 else yb}" stroke="{col}" stroke-dasharray="{"" if col!="#64748b" else "3 3"}"/>')
        o.append(f'<text x="{x:.1f}" y="{y:.0f}" text-anchor="{anc}" class="ax" fill="{col}">{txt}</text>')
    o.append("</svg>")
    return "".join(o)

# ============================================================ blocos HTML
def livro(itens, cls=""):
    o = [f'<div class="livro {cls}">']
    for it in itens:
        num, rot = it[0], it[1]
        k = it[2] if len(it) > 2 else ""
        o.append(f'<div class="{k}"><b>{num}</b><span>{rot}</span></div>')
    o.append("</div>")
    return "".join(o)

def colunas(itens, n=None, cls=""):
    n = n or len(itens)
    o = [f'<div class="cols {cls}" style="--n:{n}">']
    for h, corpo, k in itens:
        o.append(f'<div class="col {k}"><h3>{h}</h3>{corpo}</div>')
    o.append("</div>")
    return "".join(o)

ul = lambda xs: "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
ol = lambda xs: "<ol>" + "".join(f"<li>{x}</li>" for x in xs) + "</ol>"

SHA = {d: next(iter(INT[d]["commits"])) for d in DEG}

def html_escada():
    itens = [("D0", "código como distribuído", "nada: é a referência"),
             ("D1", "+ semear a ordem das imagens", "ordem de visitação dos dados"),
             ("D2", "+ fixar o kernel de backward", "seleção de kernel por latência"),
             ("D3", "+ desligar a reordenação Morton", "6 atômicos float e a permutação"),
             ("D4", "+ soma em ponto fixo, int32", "9 atômicos float do backward")]
    o = ['<div class="escada">']
    for i, (d, a, b) in enumerate(itens):
        o.append(f'<div class="deg" style="--c:{COR[d]};height:{64+i*9}%"><b>{d}</b><p>{esc(a)}</p>'
                 f'<small>remove: {esc(b)}</small><em>N = {c(str(len(R[d])), f"execuções de {d}", f"dados/{d}/run*")}'
                 f' · <code>{c(SHA[d][:7], f"commit de {d}", f"dados/{d}/run*/env.json (vksplat_commit)")}</code></em></div>')
    o.append("</div>")
    return "".join(o)

# ================================================================= slides
SLIDES = []

def add(fn):
    _SL[0] = len(SLIDES) + 1
    d = fn()
    d["n"] = _SL[0]
    SLIDES.append(d)
    return fn

data_txt = f"reunião de {dm(REF)}/{REF.year}" if ARGS.data else "outubro de 2026"

@add
def s_capa():
    return dict(cls="capa", titulo="Capa e pauta", tempo=20, fontes=[], selos=[], corpo=f"""
<h1>Reprodutibilidade em treino de 3D&nbsp;Gaussian&nbsp;Splatting</h1>
<p class="sub">Dispersão entre execuções, acumulação atômica não-associativa e a comparabilidade de resultados publicados <span class="prov">título provisório</span></p>
<p class="byline">TCC · Engenharia de Computação · UFC · Orientador: Prof. Gilvan · {data_txt}</p>
<ol class="pauta">
<li>O tema mudou</li><li>O que está medido, e com que força</li><li>O que não posso afirmar</li>
<li>O que falta até {doc(dm(DEPOSITO), "data de depósito", "pivo/PLANO.md §1")}</li><li>As decisões que preciso do senhor</li></ol>
<svg class="motivo" viewBox="0 0 250 120" aria-hidden="true">{''.join(f'<rect x="{i*50+4}" y="{100-18*(i+1)}" width="42" height="{18*(i+1)}" rx="3" fill="{COR[d]}"/>' for i, d in enumerate(DEG))}</svg>""",
        ressalvas=["Sem números na capa por decisão: o mais vistoso (a redução de dispersão de D3 para D4) é também o mais confundido, e não pode abrir a apresentação.",
                   "O título é o provisório do pivo/PLANO.md §1; sua validação é a primeira decisão do slide 15."])

@add
def s_tema():
    return dict(titulo="O tema mudou, e é a primeira vez que trago isso ao senhor", tempo=70,
                fontes=["PLANO.md (raiz) §2", "pivo-reprodutibilidade-3dgs/PLANO.md §1, §2.1, §6"], selos=[], cls="solto", corpo=f"""
<div class="cols antes-agora" style="--n:2">
<div class="col antes"><h3>Antes: comparação de hardware</h3>
<p class="tit">Renderização neural em hardware heterogêneo: portabilidade e desempenho de NeRF/3DGS em GPUs AMD RDNA&nbsp;4</p>
{ul(["Hardware, backend e implementação variavam ao mesmo tempo. Nenhuma diferença medida podia ser atribuída a um deles.",
     "As hipóteses afirmavam magnitude (&quot;gap de X%&quot;), que muda a cada versão de driver, e não mecanismo.",
     "Não tenho GPU NVIDIA. O lado CUDA dependeria de aluguel.",
     "Um segundo professor apontou falta de produção de ciência no desenho. A crítica procedia."])}</div>
<div class="col agora"><h3>Agora: reprodutibilidade do treino</h3>
<p class="tit">Quão reprodutíveis são as métricas de qualidade do 3DGS, e o que a dispersão entre execuções idênticas implica para comparar resultados publicados?</p>
{ul(["Hipóteses com mecanismo e critério de refutação, fixados em commit antes dos dados.",
     "Tudo roda na minha máquina (RX 9070 XT, Vulkan). Não comparo fornecedores.",
     "Uso o VkSplat, que treina 3DGS em Vulkan. Colocá-lo para rodar em RDNA 4 fez parte do trabalho.",
     "Há código meu: uma intervenção na causa numérica, o degrau D4."])}</div></div>""",
        ressalvas=["Simplificação declarada: entre 20 e 26/ago houve formulações intermediárias (custo de backends agnósticos; MLP fundido em Vulkan, abandonado no mesmo dia). Estão no pivo/PLANO.md §1 e §6, se o professor perguntar.",
                   "A crítica do segundo professor está registrada no PLANO.md da raiz, §2 (motivação da reformulação de 20/ago). O documento não registra o nome nem a data.",
                   "Os documentos divergem na contagem de reenquadramentos (três no pivo/PLANO.md, quatro no caderno). Por isso o slide não diz um número.",
                   "A máquina foi reinstalada em 25/ago com base numa afirmação falsa sobre a matriz do ROCm. A configuração atual é válida; o episódio não muda o tema e não está no slide."])

@add
def s_mecanismo():
    return dict(titulo="O mecanismo: em ponto flutuante, a ordem da soma muda o resultado", tempo=60,
                fontes=["pre-registro §11.3", "simulação feita neste gerador (seed 0)"], selos=[], cls="solto", corpo=f"""
<div class="cols" style="--n:2">
<div class="col nada"><p>No backward do 3DGS, várias threads da GPU somam gradientes no mesmo endereço por adição atômica em float32. Nem o código nem o hardware fixam a ordem dessas somas, e em float32 a ordem altera o resultado:</p>
<div class="eq"><div>(16.777.216 + 1) + 1 = <b class="r">{c(ib(float(ex_a)), "(2^24+1)+1 em float32", "numpy float32 neste gerador")}</b></div>
<div>16.777.216 + (1 + 1) = <b class="g2">{c(ib(float(ex_b)), "2^24+(1+1) em float32", "numpy float32 neste gerador")}</b></div></div>
<p class="nota">Calculado em float32 pelo gerador.</p></div>
<div class="col nada"><p>Simulação: os mesmos {c(ib(SIM_N), "valores na simulação", "gerador")} valores, da ordem de 10⁻⁶, somados em {c(str(SIM_ORD), "ordens na simulação", "gerador")} ordens aleatórias.</p>
{livro([(c(str(sim_f), "somas float32 distintas na simulação", "gerador, seed 0"), "resultados distintos em float32", "ref"),
        (c(str(sim_i), "somas int32 distintas na simulação", "gerador, seed 0"), "resultado em inteiro de 32 bits (ponto fixo, como em D4)", "ok")])}
<p>D4 converte cada termo para inteiro antes da soma atômica. Pela especificação SPIR-V, <code>OpAtomicIAdd</code> faz <i>"integer addition"</i> e <code>OpIAdd</code> devolve os N bits baixos do resultado. Juntas, as duas cláusulas dão uma soma associativa mesmo com estouro.</p>
<p class="nota">É composição de duas cláusulas, não uma frase da especificação. A especificação Vulkan não foi conferida.</p></div></div>""",
        ressalvas=["A simulação é ilustrativa: valores sorteados (normal, σ = 10⁻⁶, seed 0, escala 2⁴⁰ no inteiro), não gradientes reais. Outra seed dá outra contagem de resultados distintos em float32; em inteiro dá sempre 1.",
                   "Não afirmar que -fp-mode fast autoriza reassociação: a documentação do Slang não diz isso.",
                   "A especificação admite que a API cliente acrescente restrições; a especificação Vulkan não foi conferida (pre-registro §11.3, §11.9 item 5).",
                   "Em D4 só o acumulado foi medido, não os termos individuais (pre-registro §11.9 item 2)."])

@add
def s_literatura():
    tl = [("2023", "Kerbl, coautor do 3DGS", 'Issue #89 do gaussian-splatting: <i>"there will always be SOME randomness caused by GPU scheduling"</i>. Fechada sem correção.', ""),
          ("2024", "Mantenedor do nerfstudio", "Issue nerfstudio #2996 atribui o fenômeno aos atômicos de ponto flutuante, sem medir.", '<span class="rec">citação a reconferir</span>'),
          ("2025", "NerfBaselines v2 (arXiv)", f"σ de PSNR sobre {doc('4', 'treinos por método no NerfBaselines v2', 'caderno 2026-09-21 (Tabela 2 do artigo)')} treinos de 3DGS: ±{doc('0,02', 'σ de PSNR do 3DGS no NerfBaselines v2', 'caderno 2026-09-21')} dB, na média das {doc('9', 'cenas do Mip-NeRF 360', 'caderno 2026-09-21')} cenas do Mip-NeRF 360. A seed não é declarada.", ""),
          ("2026", "VkSplat (EG 2026)", f"{doc('5', 'execuções no artigo do VkSplat', 'pivo/PLANO.md §2.1.1')} execuções com IC de {doc('90%', 'IC do VkSplat', 'pivo/PLANO.md §2.1.1')}. No código, o embaralhamento das imagens não é semeado: não são repetições a seed fixa.", ""),
          ("2026", "FreeTimeGS++ v3 (arXiv, 4DGS)", f"{doc('10', 'execuções no FreeTimeGS++ v3', 'caderno 2026-09-21')} execuções com seed variável e inicialização fixa. Causa atribuída a <i>\"small stochastic differences\"</i>, sem investigar.", "")]
    tlh = "".join(f'<div><span class="ano">{a}</span><b>{b}</b>{t} {x}</div>' for a, b, t, x in tl)
    return dict(titulo="O fenômeno já é conhecido. O que sobra é atribuir a causa e intervir nela", tempo=80,
                fontes=["pivo/PLANO.md §2.1.1, §2.1.3, §2.3.1, §2.5", "caderno 2026-09-21 (busca de originalidade)"], selos=[], corpo=f"""
<div class="tl">{tlh}</div>
{colunas([("Caiu", "<p>A afirmação de que o fenômeno nunca foi quantificado. NerfBaselines, FreeTimeGS++ e o próprio VkSplat reportam dispersão.</p>", "ref"),
          ("Em suspenso", "<p>Que ninguém mediu a dispersão a seed fixa. A v1 do NerfBaselines dizia fixar seeds; a v2 apagou a frase e não declara o protocolo.</p>", "neutra"),
          ("Sobrevive", "<p>Separar as fontes por ablação, localizar o não-determinismo por estágio e intervir na causa numérica, com custo medido. Os dois trabalhos mais próximos não mencionam atômicos nem associatividade.</p>", "ok")])}
<p class="nota">O ponto fixo não é método novo: o somatório reprodutível já existe (Demmel e Nguyen; Collange et al.). A contribuição é aplicá-lo ao backward do 3DGS e medir. A busca de originalidade não cobriu IEEE Xplore, ACM DL, Eurographics nem OpenReview.</p>""",
        ressalvas=["As citações literais da issue nerfstudio #2996 e do PR gsplat #970 não foram reconferidas na fonte primária (caderno, pendência de texto 5). O PR #970 não é usado nos slides; a #2996 está parafraseada e marcada.",
                   "Issue #89: o relato de 45 execuções nela tem hiperparâmetros alterados; o valor percent_dense=1e-5 está contestado e não deve ser citado (caderno 2026-09-21).",
                   "O venue NeurIPS 2025 D&B do NerfBaselines consta só do comentário dos autores no arXiv, sem DOI; para ABNT, não verificado.",
                   "Inferência minha, não número deles: se as 9 cenas fossem independentes, ±0,02 dB na média equivaleria a ~0,06 dB por cena, a ordem do IQR de D0. Não apresentar como dado do NerfBaselines.",
                   "FreeTimeGS++: o contraste certo é 'seed fixa' contra 'seed variável com inicialização fixa', e não 'sem nenhum isolamento'. Monitorar arXiv:2605.03337 até o depósito.",
                   "A afirmação sobre o VkSplat (embaralhamento não semeado) vem da leitura do código do fork, não do artigo (pivo/PLANO.md §2.3.1).",
                   "Ação pendente que decide a coluna 'em suspenso': perguntar ao autor do NerfBaselines, ou inspecionar o runner deles (slide 15)."])

@add
def s_metodo():
    crit = [("H1", "existe não-determinismo", "refutada se as N execuções de D0 tiverem <code>splat.ply</code> de hash idêntico", "§6"),
            ("H2", "a dispersão é relevante", f"sustentada se ≥ {doc('5%', 'limiar de H2 (fração de pares)', 'pre-registro §6')} dos pares de D0 diferirem ≥ {doc('0,10 dB', 'limiar de relevância de H2', 'pre-registro §6')}", "§6"),
            ("H3.1–3.3", "cada degrau reduz a dispersão", "Fligner-Killeen rejeita e o IC 95% bootstrap da razão de IQR exclui 1", "§5.2"),
            ("H3.4", "D4 elimina a dispersão", "as N execuções de D4 têm hash idêntico", "§6")]
    tab = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{x}</td><td class='src'>{s}</td></tr>" for a, b, x, s in crit)
    git = [f"<b>08/set · <code>f02183b</code></b> protocolo de D0–D3 e critérios. A pasta da primeira execução de D0 é de {dm(dt.date(int(inicio_d0[:4]), int(inicio_d0[4:6]), int(inicio_d0[6:8])))}, {inicio_d0[9:11]}h{inicio_d0[11:13]}.",
           "<b>20/set · <code>aa79cf9</code></b> desvio §5.2, o teste de escala. O texto tem data de 09/set, mas só entrou no git em 20/set, depois dos dados de N = 20. O git não prova que ele precedeu o primeiro cálculo.",
           "<b>25/set · <code>02722af</code></b> adendo de D4 (§11). Parâmetros fixados depois de ver a dispersão de D0–D3 (desvio D-3); não têm grau de liberdade sobre o hash.",
           "<b>01/out · <code>b8b766d</code></b> §11.11, com o SHA de D4, commitado depois de a série rodar. Commit e tag de D4 já estavam no remoto."]
    return dict(titulo="Método: escada de ablação em cinco degraus, com critérios fixados antes dos dados", tempo=80,
                fontes=["pre-registro §3.1, §5.2, §6, §11", "git log do repositório do TCC", "dados/D*/run*/env.json e eval.json"], selos=[], corpo=f"""
{html_escada()}
<p class="faixa">Cena garden (Mip-NeRF 360), images_4, {doc('30.000', 'passos de treino', 'pre-registro §3')} passos, densificação ADC · RX 9070 XT (RDNA 4), Ubuntu 24.04.4, RADV/Mesa 25.2.8 · ambiente congelado desde 21/set</p>
<div class="cols" style="--n:2;--g:1.15fr .85fr">
<div class="col nada"><h3>Critérios</h3><table class="tab">{tab}</table></div>
<div class="col nada"><h3>O que o histórico do git mostra</h3><ul class="git">{''.join(f"<li>{g}</li>" for g in git)}</ul></div></div>""",
        ressalvas=["Hora da primeira execução de D0 tirada do nome da pasta de saída no eval.json (hora local da máquina). O commit f02183b é de 08/set 21h57 (−03). As duas fontes indicam o protocolo antes da série, mas o fuso da pasta não está registrado.",
                   "O §5.2 declara a própria fraqueza: foi especificado depois de ver os descritivos de N=10 e N=20, e a direção do efeito já era esperada. O commit aa79cf9 (20/set) é a primeira aparição dele no git; o caderno com os resultados de 09/set entrou no git em 21/set.",
                   "O bootstrap não se ancora em Hoefler e Belli, que o excluem; a justificativa é Efron e Tibshirani, que ainda não está no fichamento.",
                   "D4 cobre só a variante per-splat do backward. É completo porque D2 é cumulativo e fixa essa variante (pre-registro §3.1).",
                   f"Desligar o Morton (D3) custou {pct(morton_pct,0)} de tempo de treino mediano contra D2 (calculado de train.json).",
                   "D0–D2 têm dois estratos de ambiente (20 + 10) e D3 tem três (10 + 10 + 10). As 80 primeiras execuções são anteriores ao congelamento de 21/set."])

@add
def s_h1h2():
    return dict(titulo="Execuções idênticas não reproduzem o modelo, e a diferença tem a ordem dos ganhos publicados", tempo=80,
                fontes=["dados/D*/manifest.tsv", "dados/D0/run*/eval.json", "pre-registro §6"],
                selos=[("cat", "H1 · confirmada"), ("sus", "H2 · sustentada, margem estreita")], corpo=f"""
{svg_d0_lit()}
{livro([(f"{c(str(n_dist), 'hashes distintos de splat.ply, D0–D4', 'dados/D*/manifest.tsv')}/{c(str(n_exec), 'execuções medidas, D0–D4', 'dados/D*/run*')}", f"modelos com hash distinto, de D0 a D4. O critério de H1 é D0: {c(str(h1_d0[0]), 'hashes distintos em D0', 'dados/D0/manifest.tsv')}/{h1_d0[1]}"),
        (f"{c(str(h2_k), 'pares de D0 com |ΔPSNR| ≥ 0,10 dB', 'dados/D0/run*/eval.json')}/{c(str(h2_n), 'pares de D0', 'C(30,2)')}", f"pares de D0 com |ΔPSNR| ≥ 0,10 dB: {c(pct(h2_frac), 'fração H2', 'dados/D0/run*/eval.json')}, contra o critério de 5%", "ok"),
        (f"[{c(pct(h2_ic[0]), 'IC 95% bootstrap de H2, limite inferior', 'dados/D0; seed 20260909, 10.000 reamostragens')}; {c(pct(h2_ic[1]), 'IC 95% bootstrap de H2, limite superior', 'idem')}]", "IC 95% bootstrap da fração. Não exclui 5%: declara a incerteza, não é o critério"),
        (" · ".join(c(br(100*f,1), f"fração H2 no bloco {i+1} de D0", "dados/D0/run*/eval.json") for i, f in enumerate(h2_bloco)) + "%", "a mesma fração em blocos de 10 execuções: o estimador oscila muito")])}
<p class="nota">Em D0, a amplitude de PSNR é {c(br(ampl_d0,2), 'amplitude de PSNR em D0', 'dados/D0/run*/eval.json')} dB e o IQR, {c(br(iqr_d0,3), 'IQR de PSNR em D0', 'idem')} dB. Com uma execução por método, uma diferença de 0,1 dB pode ser só variação entre execuções.</p>""",
        ressalvas=[f"H2 foi de {pct(h2_por_n[10])} (N=10) a {pct(h2_por_n[20])} (N=20) e {pct(h2_frac)} (N=30). Não é tendência: em blocos de 10, D2 vai de {pct(h2_bloco_d2[0])} a {pct(h2_bloco_d2[1])} e volta a {pct(h2_bloco_d2[2])}. A fração de pares é estatística U não viesada; 9,0% em N=30 é a melhor estimativa.",
                   "O IC bootstrap não pode ser promovido a critério depois de ver os dados (caderno 2026-09-22).",
                   "Os deltas publicados vêm do levantamento de 26/ago (pre-registro §6). São médias de dataset, de outros artigos; aqui a dispersão é de uma cena só (garden).",
                   "H1 é imune à heterogeneidade de ambiente por construção: hashes distintos dentro de um mesmo estrato já bastam.",
                   "Calibração lateral, não usada no slide: o 3DGS-MCMC publicou σ de 0,0276 dB sobre 3 execuções com seed variável, em nível de dataset (pivo/PLANO.md §2.3)."])

@add
def s_h3():
    linhas = []
    for h in H3:
        nome = f"{h['a']} → {h['b']}"
        linhas.append(f"<tr><td>{nome}</td><td class='n'>{c(br(h['p'],3), f'Fligner p {nome}', 'dados/D*/run*/eval.json')}</td>"
                      f"<td class='n'>{c(br(h['rz'],3), f'razão de IQR {nome}', 'idem')}</td>"
                      f"<td class='n'>[{c(br(h['lo'],3), f'IC inf {nome}', 'bootstrap encadeado, seed 20260909')}; {c(br(h['hi'],3), f'IC sup {nome}', 'idem')}]</td>"
                      f"<td>{'sustentada' if h['ok'] else 'não'}</td></tr>")
    return dict(titulo="De D0 a D3, nenhuma redução de dispersão se estabelece com N = 30", tempo=60,
                fontes=["dados/D0–D3/run*/eval.json", "pre-registro §5.2", "caderno 2026-09-21/22"],
                selos=[("neg", "H3.1–H3.3 · não estabelecidas")], corpo=f"""
<div class="cols" style="--n:2;--g:1fr .95fr">
<div class="col nada"><table class="tab grande"><tr><th>Comparação</th><th class='n'>Fligner p</th><th class='n'>razão de IQR</th><th class='n'>IC 95%</th><th>§5.2</th></tr>{''.join(linhas)}
<tr><td colspan="5" class="rodape">Fligner nos quatro degraus juntos: p = {c(br(p_global,3), 'Fligner global D0–D3', 'idem')}</td></tr></table>
{ul([f"Em N = 20, D0 × D3 rejeitava (p = {c(br(p_n20,3), 'Fligner D0×D3 em N=20', 'run000–019')}). Em N = 30 não rejeita, e a razão subiu de {c(br(rz_n20,2), 'razão IQR D0×D3 em N=20', 'run000–019')} para {br(H3[3]['rz'],2)}: o efeito aparente encolheu.",
     f"Excluir 1 em D0 → D3 pediria N ≈ {cad('95', 'N por degrau para excluir 1 em D0→D3', 'caderno 2026-09-22 (projeção por 1/√N)')} por degrau, cerca de {cad('90 h', 'horas de máquina para N≈95', 'caderno 2026-09-22')} de máquina. Não ampliei: reporto como não estabelecido por falta de poder, com o N necessário."])}</div>
<div class="col nada">{svg_iqr_blocos()}
<p class="nota">O IQR de D3 varia {c(br(var_d3,1)+'×', 'variação do IQR de D3 entre blocos', 'dados/D3/run*/eval.json')} entre blocos de 10 execuções. Em D0 e D1, o bloco 1 inverte a ordem que a escada mede. A própria medida de dispersão oscila na ordem do efeito procurado.</p></div></div>""",
        ressalvas=["D3 tem três estratos de ambiente (10 + 10 + 10, por kernel e libc). Restringir D3 a um estrato está proibido sem desvio declarado, por ser o recorte favorável. O Mesa/RADV foi o mesmo nas 120 execuções (caderno 2026-09-21).",
                   "A projeção de N≈95 contrai o IC em 1/√N supondo a razão de 0,631 constante: é aproximação, não cálculo de poder formal.",
                   f"A anomalia D1 → D2 (razão 1,335 em N=20) caiu para {br(H3[1]['rz'],3)} em N=30, comportamento de ruído; reportar como episódio.",
                   "O bootstrap usa um único gerador com seed 20260909, encadeado na ordem D0→D1, D1→D2, D2→D3, D0→D3; assim reproduz os IC do caderno de 2026-09-22.",
                   "Não se pode dizer que a atualização de kernel entre os blocos de D3 alterou a dispersão, nem que não alterou: N=10 por bloco não decide."])

@add
def s_d4():
    sel = [("ref", "H3.4 · refutada"), ("sus", "§5.2 D3→D4 · sustentada, com confundidor")]
    pr = lambda k: f"{br(min(P99_REGIME[k]),2)} a {br(max(P99_REGIME[k]),2)}"
    return dict(titulo="D4 reduz muito a dispersão, mas não a elimina, e há um confundidor", tempo=100,
                fontes=["dados/D3, D4/run*/eval.json, train.json, manifest.tsv", "dados/gradientes/", "dados/D4/diagnostico_ply.json", "pre-registro §5.2, §11.2"],
                selos=sel, corpo=f"""
<div class="cols" style="--n:2;--g:.9fr 1.1fr">
<div class="col nada">{svg_d3_d4()}</div>
<div class="col nada">
{livro([(f"{c(str(h_d4[0]), 'hashes distintos em D4', 'dados/D4/manifest.tsv')}/{c(str(h_d4[1]), 'execuções de D4', 'dados/D4')}", "hashes distintos em D4. O critério de H3.4 é hash idêntico: refutada", "ref"),
        (c(br(rz34,3), 'razão de IQR de PSNR D4/D3', 'dados/D3, D4/run*/eval.json'), f"razão de IQR de PSNR, D4/D3. IC 95% [{c(br(lo34,3), 'IC inf D3→D4', 'bootstrap, seed 20260909')}; {c(br(hi34,3), 'IC sup D3→D4', 'idem')}], Fligner p = {c(br(p34,4), 'Fligner D3×D4', 'idem')}", "ok")], "duas")}
{livro([(c(br(dq,2)+" dB", 'diferença de PSNR mediano D3→D4', 'eval.json'), f"PSNR mediano, de {c(br(med(P['D3']),3), 'PSNR mediano D3', 'eval.json')} para {c(br(med(P['D4']),3), 'PSNR mediano D4', 'eval.json')}. As faixas não se sobrepõem", "ref"),
        (f"{c(br(med(SS['D3']),3), 'SSIM mediano D3', 'eval.json')} → {c(br(med(SS['D4']),3), 'SSIM mediano D4', 'eval.json')}", f"SSIM mediano; LPIPS-Alex de {c(br(med(LA['D3']),3), 'LPIPS-Alex mediano D3', 'eval.json')} para {c(br(med(LA['D4']),3), 'LPIPS-Alex mediano D4', 'eval.json')}"),
        (c(br(100*dt_pct,0)+"%", 'variação do tempo mediano D3→D4', 'train.json'), "tempo de treino mediano, D3 → D4")], "tres")}
<div class="aviso"><h3>Confundidor</h3><p>A escala de ponto fixo da cônica foi dimensionada pelo máximo do início do treino. A partir do passo ~{c(ib(min(P99_DESDE.values())), 'passo a partir do qual o p99 da cônica fica < 1 quantum', 'dados/gradientes/ com s do §11.2')}, o p99 do gradiente acumulado da cônica fica abaixo de 1 quantum (de {pr('conic_0')} quanta em cônica 0), e termo abaixo de ½ quantum vira zero. D4 mudou, na prática, duas coisas: a soma inteira e o gradiente de covariância, quase todo zerado. Nos <code>.ply</code>, escala e rotação diferem em {c(pct(min(fr_esc+fr_rot),0), 'fração mínima de valores de escala/rotação que diferem', 'diagnostico_ply.json')} a {c(pct(max(fr_esc+fr_rot),0), 'fração máxima de valores de escala/rotação que diferem', 'idem')} dos valores, contra {c(pct(min(fr_pos),0), 'fração de valores de posição que diferem', 'idem')} na posição: compatível, não demonstrado. Só o D4b separa os efeitos.</p></div>
</div></div>""",
        ressalvas=["Os dois critérios são diferentes e vão separados no texto: H3.4 (hash idêntico) refutada; §5.2 (escala de PSNR) sustentado.",
                   f"No mesmo estrato de ambiente (D3 run020–029, N=10): razão {br(rz34s,3)}, IC [{br(lo34s,3)}; {br(hi34s,3)}], Fligner p = {br(p34s,4)}. O caderno de 2026-10-05 registra IC [0,021; 0,481] para este recorte; o gerador obtém o valor acima com um gerador novo de seed 20260909. O veredito não muda.",
                   f"Nº de gaussianas: razão de IQR {br(rz34n,4)}, IC [{br(lo34n,4)}; {br(hi34n,4)}], Fligner p = {sci(p34n)} (IQR de {ib(iqr(NS['D3']))} para {br(iqr(NS['D4']),1)}).",
                   f"O 'cai ~12×' do caderno de 2026-10-01 compara com o bloco run020–029 (IQR {br(iqr(P['D3'][d3s]),4)} dB). Contra D3 com N=30, que é a comparação pré-registrada, a razão é {br(rz34,3)}, isto é ~{br(1/rz34,1)}×.",
                   f"A amplitude de PSNR de D4 é puxada por run{run_max_d4:03d} ({br(P['D4'].max(),4)} contra {br(P4_sem_max.min(),3)}–{br(P4_sem_max.max(),3)} das outras nove).",
                   f"O p99 em quanta é o maior das 3 repetições em cada passo amostrado, com s = {S_ESC['conic_0']}, {S_ESC['conic_1']}, {S_ESC['conic_2']}. No passo 1.000 ele ainda vale {br(P99Q['conic_0'][1000],1)}, {br(P99Q['conic_1'][1000],1)} e {br(P99Q['conic_2'][1000],1)} quanta: o 'zera quase tudo' vale para o regime, não para o início. Os termos individuais, antes de somar os tiles, são menores e não foram medidos.",
                   f"Em cônica 1 o p99 fica abaixo de 1 quantum a partir do passo {ib(P99_DESDE['conic_1'])}, e em cônica 2 a partir do {ib(P99_DESDE['conic_2'])}.",
                   "A perda de 0,39 dB é quase 4× o limiar de H2. A hipótese mais provável, não testada, é a escala da cônica, e não o determinismo. Erro de desenho: o máximo usado era o transiente do passo 0.",
                   "O −8% de tempo pode refletir trabalho descartado no backward, se a hipótese da cônica valer. É observação, sem interpretação.",
                   "O compilador não é confundidor: T0 deu 41/41 .spv idênticos ao upstream (caminho A, pre-registro §11.10)."])

@add
def s_onde():
    return dict(titulo="Em D4, a divergência aparece tarde no treino, não no primeiro passo", tempo=70,
                fontes=["dados/D*/run*/run*.log (linhas de densificação)", "dados/D4/trajetoria*_rep0{0,1}.json", "dados/D4/diagnostico_ply.json"],
                selos=[("exp", "exploratório · um par por rastreamento")], corpo=f"""
{svg_onset()}
<div class="cols fatos" style="--n:4">
<div class="col nada"><h3>Série, {len(R['D4'])} execuções</h3><p>Densificação idêntica até divergir no evento {c(str(onset['D4']), 'primeiro evento de densificação divergente em D4', 'logs de D4')} de {c(str(n_ev), 'eventos de densificação', 'logs')} (passo {c(ib(passo_ev(onset['D4'])), 'passo do evento 129', 'logs + simple_trainer.py:42-44')}); {c(str(grupo_d4), 'execuções de D4 idênticas nos 144 eventos', 'logs de D4')} das 10 idênticas nos {n_ev} eventos. De D0 a D3, divergem já no primeiro.</p></div>
<div class="col nada"><h3>Rastreamento, 1 par</h3><p>{c(str(TR_L['amostras']), 'amostras do rastreamento leve', 'trajetoria_rep0x.json')} amostras de {c(str(TR_L['nbuf']), 'buffers monitorados (leve)', 'idem')} buffers: estado bit-idêntico até o passo {c(ib(TR_L['ultimo']), 'último passo idêntico (leve)', 'idem')}. No {ib(TR_L['primeiro'])}, todos os estágios diferem.</p></div>
<div class="col nada"><h3>Rastreamento denso, 1 par</h3><p>Todo passo, {c(str(TR_D['nbuf']), 'buffers monitorados (denso)', 'trajetoria_denso_rep0x.json')} buffers: idênticos até {c(ib(TR_D['ultimo']), 'último passo idêntico (denso)', 'trajetoria_denso_rep0x.json')}. Primeira diferença observada no forward do passo {c(ib(TR_D['primeiro']), 'primeiro passo com diferença (denso)', 'idem')}, depois da última densificação ({c(ib(ultima_dens), 'último passo de densificação', 'logs + simple_trainer.py')}).</p></div>
<div class="col nada"><h3>.ply finais, {len(pares_ply)} pares</h3><p>Nenhum é permutação do outro ({c(str(mesmo_ms), 'pares com o mesmo multiconjunto', 'diagnostico_ply.json')} de {len(pares_ply)}). Com o mesmo N, de {c(pct(min(fr_gauss),1), 'fração mínima de gaussianas diferentes', 'idem')} a {c(pct(max(fr_gauss),2), 'fração máxima de gaussianas diferentes', 'idem')} das gaussianas diferem em valor, alinhadas por índice.</p></div></div>
<p class="nota">Cada rastreamento é um par só. Ler buffers sincroniza a GPU e pode mudar onde uma fonte dependente de temporização aparece. O modo denso não monitora SH, escala e rotação: a origem pode ser o forward de {ib(TR_D['primeiro'])} ou escala e rotação divergindo antes. Densificação idêntica não implica parâmetros idênticos.</p>""",
        ressalvas=["O passo de cada evento vem do código (refine_start_iter = 500, refine_every = 100, refine_stop_iter = 15.000; simple_trainer.py:42-44 e gs_trainer.cpp:829-830, lidos no caderno de 2026-10-05).",
                   f"Na série, as densificações de D4 já diferem no evento {onset['D4']} (passo {ib(passo_ev(onset['D4']))}); no rastreamento leve, o estado ainda era idêntico no passo {ib(TR_L['ultimo'])}. É compatível com uma fonte rara de início variável e também com interferência da instrumentação. O dado não distingue.",
                   f"No rastreamento leve, no passo {ib(TR_L['primeiro'])} diferem {len(TR_L['dif'])} buffers, todos os que têm conteúdo (o ssim_map vem vazio). Como a projeção só lê o estado deixado pelo passo anterior, a divergência nasceu entre {ib(TR_L['ultimo']+1)} e {ib(TR_L['primeiro']-1)}; nem passo nem estágio de origem são identificáveis.",
                   "No par denso, a diferença em n_contributors (que depende de geometria e ordem, não de cor) restringe a explicação alternativa a escala ou rotação.",
                   "O evento de v_rgb da fase 2 (slide 11) não explica este par: alteraria só os SH, não n_contributors.",
                   "A diferença máxima de posição no par run008 é de ~0,013 unidade de cena. É unidade do COLMAP depois da transformação do dataparser, não centímetro; o caderno escreve 'cm' sem base.",
                   "Os histogramas de ULP dos 4 pares com o mesmo N são quase idênticos; o pico em 2³⁰–2³¹ ULP é compatível com valores perto de zero de sinal oposto, leitura não verificada valor a valor.",
                   "O hash do .ply inclui a ordem dos registros, então hash distinto sozinho não prova modelo distinto; o teste de multiconjunto fecha isso."])

@add
def s_estagios():
    f3, f4 = F1["D3"], F1["D4"]
    return dict(titulo="Em estado fixo, o não-determinismo de D3 está todo no backward. Em D4, não aparece", tempo=100,
                fontes=["dados/estagios/estagios_D3.json, estagios_D4.json", "caderno 2026-10-13/14"],
                selos=[("cat", f"observação direta · {f3['reps']} repetições por degrau")], corpo=f"""
<p class="intro">Parâmetros congelados em {c(str(f3['npts']), 'pontos do teste de estágios', 'estagios_D3.json')} passos do treino. Em cada um, {c(str(f3['k']), 'repetições por ponto (fase 1)', 'idem')} repetições de forward → perda → backward, contando os hashes distintos de cada buffer.</p>
<div class="cols" style="--n:2;--g:1.6fr 1fr">
<div class="col nada">{svg_estagios()}
{livro([(f"{c(str(f3['bwd_dist']), 'repetições de backward distintas em D3', 'estagios_D3.json')}/{f3['reps']}", f"repetições do backward de D3 com gradiente diferente; forward e perda: {c(str(f3['fwd_max']), 'hashes de forward/perda em D3', 'idem')} hash em {f3['reps']}", "ref"),
        (f"{c(str(f4['eventos']), 'repetições de D4 com diferença (fase 1)', 'estagios_D4.json')}/{f4['reps']}", "repetições de D4 com qualquer diferença, nos 6 buffers. Controle positivo (D3) aprovado", "ok")], "duas")}</div>
<div class="col nada"><div class="aviso neutro" style="margin-top:0"><h3>Ressalvas</h3>{ol([f"{faixa_pct(ler_frac, 'fração do tempo de cada repetição gasta em leitura e hash', 'estagios_D*.json (tempo), pontos com N > 5 M')} do tempo de cada repetição é leitura e hash na CPU, com a GPU ociosa. Uma corrida dependente de temporização pode estar suprimida, nos dois degraus.",
     "Buffers zerados dariam hash constante. Excluído só de forma indireta: eles alimentam o otimizador, e D4 treina até PSNR ≈ 27.",
     f"Tudo idêntico em {f4['k']} repetições não refuta um evento raro: limite superior de 95% de {c(br(f4['lim'],3), 'limite superior 95% por repetição, K=20', 'estagios_D4.json')} por repetição, por passo.",
     "Cada estágio é submetido e sincronizado em separado (patch só no binding). No treino, vão num lote só: mesma aritmética, outra temporização."])}</div></div></div>""",
        ressalvas=["É a localização por estágio que o mecanismo prevê: o backward é onde estão os atômicos de float. Contraste com instrumentação idêntica nos dois degraus.",
                   "A leitura pré-definida foi corrigida em 13/out, antes dos dados, no sentido desfavorável à tese: 'tudo idêntico' em D4 não refuta forward raramente não-determinístico. A correção é diagnóstico exploratório, não desvio do pré-registro.",
                   "O JSON não grava os valores dos buffers, só hashes e contagens. Por isso a exclusão de buffers nulos é indireta.",
                   f"Agregar os 7 pontos daria um limite menor, mas supõe taxa constante entre estados, o que não foi fixado nem verificado. Não se reporta.",
                   f"Integridade: commit-base igual às tags D3 e D4; mesmas imagens sorteadas nos mesmos passos nos dois degraus ({'sim' if img_iguais else 'NÃO'}); módulo recompilado {br(min(recomp),1)} a {br(max(recomp),1)} s antes de cada execução; D4 termina com {ib(n_fim_f1)} gaussianas, o valor modal da série de D4.",
                   "A primeira tentativa travou no passo 1.050 por uso errado da API do fork (timer gravado fora de lote). A causa foi inferida pela leitura do código e corroborada pela correção; o stack da execução travada não foi capturado.",
                   "Os contadores de timers do fork confirmam que as repetições executaram forward, perda e backward e nunca o otimizador (30.140 contra 30.000; D4.log, não versionado, citado no caderno de 2026-10-14)."])

@add
def s_residual():
    f2a, f2b = F2
    cp = CAP[0]
    linhas = [("fase 1", f"{F1['D4']['npts']} passos", ib(F1['D4']['reps']), str(F1['D4']['eventos']), f"{br(F1['D4']['lim'],3)} por passo"),
              ("fase 2", ib(f2a['step']), ib(f2a['k']), f"{f2a['ev']}, só em <code>{f2a['bufs'][0] if f2a['bufs'] else ''}</code> [{', '.join(ib(m) for m in (f2a['mult'] or []))}]", "—"),
              ("fase 2", ib(f2b['step']), ib(f2b['k']), str(f2b['ev']), sci(f2b['lim'])),
              ("captura com releitura", ib(cp['step']), ib(cp['k']), str(cp['ev']), sci(cp['lim']))]
    for l in linhas:
        c(l[2], f"repetições: {l[0]} passo {l[1]}", "dados/estagios/estagios_D4*.json")
        c(l[3], f"eventos: {l[0]} passo {l[1]}", "idem")
        if l[4] != "—":
            c(l[4], f"limite sup. 95%: {l[0]} passo {l[1]}", "idem")
    tab = "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'>{x}</td><td>{e}</td><td class='n'>{l}</td></tr>" for a, b, x, e, l in linhas)
    tab += (f"<tr class='soma'><td>soma</td><td></td><td class='n'>{c(ib(reps_d4), 'repetições de estágio em D4, total', 'estagios_D4*.json')}</td><td>{c(str(ev_d4), 'eventos em D4, total', 'idem')}</td>"
            f"<td class='n'>Poisson [{c(sci(ic_tot[0]), 'IC Poisson inf, total', 'idem')}; {c(sci(ic_tot[1]), 'IC Poisson sup, total', 'idem')}], descritivo</td></tr>")
    return dict(titulo="Em D4 resta uma fonte rara, que não consegui caracterizar", tempo=60,
                fontes=["dados/estagios/estagios_D4.json, _fase2.json, _captura.json", "caderno 2026-10-14/15"],
                selos=[("neg", "não caracterizada"), ("exp", "caça encerrada")], corpo=f"""
<table class="tab grande"><tr><th>Execução</th><th class="n">Passo</th><th class="n">Repetições</th><th>Eventos</th><th class="n">Limite sup. 95% por repetição</th></tr>{tab}</table>
{colunas([("O que se sabe", f"<p>O evento foi isolado: {ib(f2a['mult'][0])} repetições iguais e 1 diferente, sem mudança de estado. Em D4, v_rgb é soma inteira, e a ordem das invocações não produz esse evento. Se veio do cálculo, a fonte é de outra natureza (corrida, dado velho). Isso é inferência.</p>", "neutra"),
          ("O que não se sabe", f"<p>Se foi cálculo ou leitura (GPU → RAM → hash; memória sem ECC). A captura que separaria os dois não viu nenhum evento em {ib(cp['k'])} repetições, numa trajetória nova.</p>", "neutra"),
          ("Frase para o texto", "<p>A acumulação em float é a fonte dominante. Em D4 resta uma fonte rara, não identificada; por inferência, não é a não-associatividade.</p>", "ok")], cls="depois")}
<p class="nota">As duas execuções instrumentadas sem repetições antes do passo 15.000 terminaram com {c(ib(n_inst[0]), 'N final da fase 2', 'estagios_D4_fase2.json')} e {c(ib(n_inst[1]), 'N final da captura', 'estagios_D4_captura.json')} gaussianas, acima da faixa da série ({c(ib(NS['D4'].min()), 'N mínimo da série D4', 'train.json')} a {c(ib(NS['D4'].max()), 'N máximo da série D4', 'train.json')}). Pode ser acaso (~{cad('3%', 'probabilidade de duas execuções acima da faixa', 'caderno 2026-10-15, por permutabilidade')}); essas execuções não gravaram <code>ambiente.json</code>.</p>""",
        ressalvas=["O JSON da fase 2 grava contagens, não a sequência de hashes: não se sabe em qual repetição o evento ocorreu.",
                   "'Entradas idênticas' só foram verificadas nos buffers com hash. O backward também lê intermediários da projeção e da ordenação que o forward recalcula a cada repetição e não têm hash; nessa repetição, a imagem, as contribuições e o gradiente da perda coincidiram.",
                   "A captura rodou numa trajetória nova: o estado no passo 16.050 não é o da fase 2, porque as execuções de D4 divergem depois de ~13.500. Se a taxa depende do estado, pode ser outra.",
                   "O IC de Poisson da soma supõe a mesma taxa em estados diferentes, o que não foi fixado. É descritivo.",
                   f"A fase 2 sozinha: 1 evento em {ib(2*f2a['k'])} repetições, IC exato de Poisson [{sci(poisson_ic(1, 2*f2a['k'])[0])}; {sci(poisson_ic(1, 2*f2a['k'])[1])}].",
                   "A caça à fonte residual foi encerrada por decisão minha em 15/out. A afirmação que vai para o texto é a do quadro verde, com a força declarada.",
                   "O testar_estagios.py não gravava ambiente.json; não se pode excluir mudança de ambiente entre a série e as execuções instrumentadas. Corrigido para os scripts seguintes."])

@add
def s_nao():
    itens = ["Que o trabalho descobre o não-determinismo. Kerbl o reconheceu em 2023; um mantenedor do nerfstudio o atribuiu aos atômicos em 2024.",
             "Que o tema é inédito, ou que o fenômeno nunca foi quantificado. NerfBaselines v2 e FreeTimeGS++ quantificam; a busca está incompleta.",
             "Que nenhum trabalho mede a dispersão a seed fixa. O protocolo de seed do NerfBaselines v2 é indeterminado.",
             "Que D3 reduz a dispersão. Nenhuma H3.1–H3.3 se sustenta em N = 30.",
             f"Que as {len(R['D3'])} execuções de D3 são nominalmente idênticas entre si. Há três estratos de ambiente.",
             f"Que a queda de H2 ({br(100*h2_por_n[10],1)}% → {br(100*h2_por_n[20],1)}% → {br(100*h2_frac,1)}%) é tendência. O estimador oscila entre blocos.",
             f"Que D4 é bit-idêntico, ou \"quase determinístico\" em sentido formal. São {h_d4[0]} hashes distintos em {h_d4[1]}.",
             "Que a redução de dispersão de D3 para D4 se deve só à soma inteira. Há o confundidor da cônica.",
             f"Que os {br(-dq,2)} dB perdidos em D4 são o custo do determinismo.",
             "Que a fonte residual é X, ou que o evento de v_rgb foi cálculo e não leitura.",
             "Que D4 elimina a dependência de VK_EXT_shader_atomic_float. Elimina só no shader per-splat.",
             "Que -fp-mode fast autoriza reassociação, ou que o modo de denormais foi controlado em algum degrau."]
    return dict(titulo="O que eu não posso afirmar", tempo=60, fontes=["caderno, seção 'O que NÃO pode ser afirmado'", "dados/D*/"],
                selos=[], cls="solto", corpo=f'<ol class="nao">{"".join(f"<li>{x}</li>" for x in itens)}</ol>',
                ressalvas=["Itens tirados da lista do caderno. Dois itens daquela lista estão superados e não entraram: 'que D4 funciona: nunca foi executado' (já foi, 10 execuções) e, em parte, 'que se sabe quando a divergência de D4 começa' (há dois pares rastreados, slide 9).",
                           "Também ficam de fora do slide, mas valem: que o Mesa/RADV mudou durante as 120 execuções (não mudou); que a atualização de libc6 de 21/set afeta as métricas (hipótese não testada); que o acumulador de D4 nunca estoura (só o acumulado foi medido); que D0–D3 e D4 foram compilados pelo mesmo compilador (T0 só diz que os bytes coincidem)."])

@add
def s_d4b():
    passos = [f"Medição densa em D3: {doc('3', 'repetições da medição densa', 'caderno 2026-10-15')} repetições, ~{cad('2 h 20', 'tempo de máquina estimado da medição densa', 'caderno 2026-10-15, a partir do custo medido')} de máquina. <b>Em execução.</b>",
              "Adendo §11.12, commitado antes da série. A regra de escala passa a usar a cauda do histograma, não só o máximo. Em aberto: <code>clamp</code> por termo em ±L/2ᵏ.",
              "Implementação só em shader, sem C++, e verificações V1–V5.",
              f"Série com N = 10: ~{c(br(serie_h,1)+' h', 'horas de treino estimadas para a série D4b', '10 × mediana de time_elapsed de D4')} de treino (10 × a mediana de D4).",
              "Análise pelo §5.2, contra D3 e contra D4."]
    rz = [RAZ_DENSO[k] for k in CON]
    return dict(titulo="D4b: separar o efeito da soma inteira do efeito da escala da cônica", tempo=70,
                fontes=["dados/gradientes/", "caderno 2026-10-15 (saída do modo --custo)", "pre-registro §11.2"],
                selos=[("and", "medição densa em execução")], corpo=f"""
<div class="cols" style="--n:2;--g:1fr 1fr">
<div class="col nada"><h3>Por que</h3><p>D4 mudou duas coisas. O D4b mantém a soma inteira e dimensiona a escala da cônica por faixa de passos, pelo regime do treino. A leitura do resultado será fixada no adendo §11.12, antes de rodar. H3.4 continua refutada em qualquer caso.</p>
<h3>O que falta</h3>{ol(passos)}</div>
<div class="col nada"><h3>O que a medição já mudou</h3>{svg_conica()}
<p class="nota">Nos passos 10.000 e 12.500, os dados esparsos davam máximos de {c(br(min(MAX_ESP_10K.values()),2), 'máximo esparso mínimo perto de 10.000', 'dados/gradientes/')} a {c(br(max(MAX_ESP_10K.values()),2), 'máximo esparso máximo perto de 10.000', 'idem')}. Em 50 passos densos, de 10.010 a 10.500, o máximo foi de {cad(br(min(CUSTO_DENSO.values()),1), 'máximo denso mínimo (cônica 2)', 'caderno 2026-10-15, saída de terminal')} a {cad(br(max(CUSTO_DENSO.values()),1), 'máximo denso máximo (cônica 1)', 'idem')}: {c(br(min(rz),0), 'razão denso/esparso mínima', 'gerador')}× a {c(br(max(rz),0), 'razão denso/esparso máxima', 'gerador')}× maior. A escala que os dados esparsos dariam teria estourado.</p></div></div>""",
        ressalvas=["Os máximos densos vêm de uma execução e 50 amostras (modo --custo). Não há arquivo em dados/; a saída foi colada no caderno.",
                   "O padrão sugere picos raros: o máximo por passo varia em ordens de grandeza entre passos próximos. Nem a amostragem a cada 10 passos garante o máximo verdadeiro; por isso a regra usará a cauda do histograma.",
                   f"A capacidade no gráfico é L/2^s com L = 2.147.483.520 e s pela regra floor(log2(2³⁰/máx)) aplicada ao máximo esparso a partir do passo 5.000 ({', '.join(f'{k}: {br(MAX_ESP_5000[k],3)}' for k in CON)}).",
                   "Os 16 passos esparsos não incluem nenhum reset de opacidade (3.000, 6.000, 9.000, 12.000) nem os passos logo depois; a medição densa inclui as janelas R a R+50.",
                   "O 'erro de duas ordens de grandeza' do caderno vale para cônica 0 e 1; para cônica 2 a razão é menor (ver números no slide).",
                   "A estimativa de ~2,4 h da série supõe que o D4b custe o mesmo que D4. Não foi medido.",
                   "A cônica é corrigida por faixa de passos; o produtor recebe step = S e o otimizador S+1, então a escala tem de vir de uma função única compartilhada (caderno 2026-10-15)."])

@add
def s_cronograma():
    itens = ["D4b: medição densa → adendo §11.12 → implementação → série → análise",
             "Diagnóstico dos .ply de D3, com os arquivos no HD externo",
             "H4: comparar com os valores publicados do VkSplat (JPEG × PNG e convenção de LPIPS limitam)",
             "H3b: executar, com adendo próprio, ou declarar não executada",
             "Cópia em nuvem dos .ply"]
    return dict(titulo=f"Até {dm(DEPOSITO)}, o plano atual deixa no máximo {janela} dias para escrever", tempo=70,
                fontes=["pivo/PLANO.md §1 (depósito)", "caderno 2026-10-05 e 2026-10-15 (plano e congelamento)"], selos=[], corpo=f"""
{svg_tempo()}
<p class="nota tempo">Contagem a partir de {dm(REF)} ({'data da reunião' if ARGS.data else 'data de geração; passe --data com a data da reunião'}): {c(str(dias_dep), 'dias até o depósito', 'gerador, a partir das datas')} dias até o depósito. Nenhum capítulo escrito.</p>
<div class="cols" style="--n:2;--g:1fr 1fr">
<div class="col nada"><h3>Plano atual: todas as iterações antes de escrever</h3>{ol(itens)}
<p class="nota">Decisão minha, reconfirmada em 15/out. O congelamento dos dados, proposto para {dm(CONGELA_PROP)}, já passou para depois de ~{dm(CONGELA)}.</p></div>
<div class="col pergunta"><h3>Decisão que peço ao senhor</h3>
<ol class="opcoes" type="A"><li><b>Manter.</b> Todas as iterações primeiro; escrever depois de ~{dm(CONGELA)}.</li>
<li><b>Escrever já, em paralelo,</b> os capítulos que não dependem do D4b: fundamentação, trabalhos relacionados e método.</li>
<li><b>Cortar escopo</b> para proteger a escrita: declarar H3b não executada e/ou reduzir H4.</li></ol></div></div>""",
        ressalvas=["As datas do slide: depósito 06/nov (institucional); congelamento proposto 16/out (caderno, 2026-10-05); 'passa de ~20/out' (caderno, 2026-10-15). A janela de escrita é contada de 20/out ao depósito, e por isso é um máximo.",
                   "O orientador da sessão principal alertou uma vez, em 15/out, que a escrita começaria sobre uma janela menor que 17 dias; a decisão de manter o plano é minha.",
                   "Só há estimativa de tempo de máquina para a medição densa e para a série do D4b. Para diagnóstico de .ply de D3, H4 e H3b não há estimativa medida, e o slide não inventa uma.",
                   "H4 é exploratória por desenho (pivo/PLANO.md §2.3.1): o artigo usa images_4_png, e aqui são os JPEG de images_4; o LPIPS-VGG herdado usa convenção errada (pre-registro §8)."])

@add
def s_validar():
    itens = [("Tema e título", "<i>Reprodutibilidade em treino de 3D Gaussian Splatting: dispersão entre execuções, acumulação atômica não-associativa e a comparabilidade de resultados publicados.</i>"),
             ("Escopo", "D4b é necessário, ou basta declarar o confundidor? H3b: executar (exige adendo próprio) ou declarar não executada? H4: manter, reduzir ou cortar?"),
             ("Calendário", "A, B ou C do slide anterior."),
             ("Capítulos e prazos", "Proposta: " + " · ".join(f'<span class="nw">{x}</span>' for x in ["1 Introdução", "2 Trabalhos relacionados", "3 Fundamentação (3DGS, backward, ponto flutuante, atômicos)", "4 Método e pré-registro", "5 Resultados", "6 Conclusão"]) + ". E datas de rascunho para o senhor ler."),
             ("Banca", "Nomes e data da defesa."),
             ("Contato externo", "Posso perguntar ao autor do NerfBaselines qual foi o protocolo de seed? A resposta decide se a medição a seed fixa é diferencial do trabalho.")]
    return dict(titulo="O que preciso validar com o senhor", tempo=60, fontes=["pivo/PLANO.md §1, §7", "caderno 2026-09-21 (pendência 2)"], selos=[], cls="solto",
                corpo='<ol class="decisoes">' + "".join(f"<li><h3>{a}</h3><p>{b}</p></li>" for a, b in itens) + "</ol>",
                ressalvas=["A estrutura de seis capítulos é proposta minha, montada a partir das menções a Cap. 1, 2, 4, 5 e 6 no pivo/PLANO.md; o Cap. 3 não tinha conteúdo definido.",
                           "Se o professor não puder decidir o escopo na reunião, a pergunta mínima é a do calendário, porque ela tem prazo."])

@add
def s_extensoes():
    return dict(titulo="Extensões, fora do prazo", tempo=20, fontes=["pivo/PLANO.md §2.5", "dados/D2, D3/run*/train.json"], selos=[], cls="solto", corpo=colunas([
        ("Fechar o que D4 deixou", ul(["Caracterizar o evento raro, com mais repetições de captura.",
                                         f"Tornar determinística só a fase ComputeStats do Morton; desligá-lo inteiro custou {c(pct(morton_pct,0), 'custo de tempo de D3 contra D2', 'train.json')} de tempo.",
                                         "Somatório reprodutível (Demmel e Nguyen; Collange et al.) no lugar do ponto fixo, sem escolher escala.",
                                         "H3b, se não couber agora."]), "neutra"),
        ("Ampliar o alcance", ul(["Outras cenas do Mip-NeRF 360 e a densificação MCMC.", "Outras GPUs e drivers Vulkan.", "O 3DGS em CUDA e o gsplat, com GPU NVIDIA."]), "neutra"),
        ("Devolver", ul(["Issue no VkSplat com as medições e o patch de D4."]), "ok")]),
        ressalvas=["Slide de fechamento rápido; pode ser pulado se o tempo apertar."])

@add
def s_apendice():
    tot_ok = sum(INT[d]["limpos"] == INT[d]["n"] == INT[d]["dev0"] == INT[d]["gpu"] and INT[d]["emul"] == 0 and len(INT[d]["commits"]) == 1 for d in DEG)
    v3 = VER["V3"]["itens"]
    linhas = [("Séries", f"{c(str(n_exec), 'execuções conferidas', 'dados/D*/run*')} execuções: {c(str(tot_ok), 'degraus com todas as checagens ok', 'env.json e logs')} de 5 degraus com um único commit por degrau, árvore limpa, TRAIN_DEVICE 0, GPU RADV GFX1201 selecionada e nenhum USE_EMULATED nos logs."),
              ("Ambiente", f"{c(str(len(AMB)), 'execuções com ambiente.json', 'dados/D*/run*/ambiente.json')} execuções com <code>ambiente.json</code>, todas com Mesa {esc(', '.join(sorted(mesa_v)))} e libc {esc(', '.join(sorted(libc_v)))}. Para as 80 anteriores, o dpkg.log não registra {cad('mudança de Mesa', 'Mesa constante nas 80 primeiras execuções', 'caderno 2026-09-21 (dpkg.log, não versionado)')}."),
              ("Binário", f"O orquestrador recompila a cada degrau (§3.2). Nos testes de estágio, o módulo foi recompilado {c(br(min(recomp),1), 'segundos mín. entre recompilação e início', 'estagios_*.json')} a {c(br(max(recomp),1), 'segundos máx. entre recompilação e início', 'idem')} s antes do início."),
              ("Compilador", f"T0: o slangc {esc(T0['slangc_versao'])} reproduziu {c(str(T0['contagem'].get('IDENTICO',0)), '.spv idênticos no T0', 'dados/toolchain/reproducao.json')} de {len(T0['resultados'])} .spv do upstream bit a bit ({T0['grupos_D4']['identicos']} de {T0['grupos_D4']['jobs']} nos grupos de D4)."),
              ("D3 → D4", f"V2: {c(str(len(VER['V2']['alterados'])), 'arquivos alterados D3→D4', 'dados/toolchain/verificacao_d4.json')} arquivos alterados ({sum(x.endswith('.slang') for x in VER['V2']['alterados'])} .slang, um deles novo, e {sum(x.endswith('.spv') for x in VER['V2']['alterados'])} .spv), {len(VER['V2']['extra'])} a mais. V3 ({sum(v3.values())} de {len(v3)} checagens ok): <code>OpAtomicIAdd</code> ×9 e <code>OpAtomicFAddEXT</code> ×0 no backward per-splat, com +{VER['V3']['deltas']['round']} round, +{VER['V3']['deltas']['clamp']} clamp e +{VER['V3']['deltas']['OpConvertFToS']} conversões para inteiro, um por sítio."),
              ("Estágios", f"Mesmas imagens sorteadas nos mesmos passos em D3 e D4; D4 terminou com {ib(n_fim_f1)} gaussianas, o valor modal da série ({ib(n_modal_d4)}).")]
    return dict(titulo="Apêndice: integridade das séries e do binário", tempo=0, cls="solto", fontes=["dados/D*/run*/env.json, ambiente.json, run*.log", "dados/toolchain/", "dados/estagios/"],
                selos=[("exp", "reserva")], corpo='<table class="tab app">' + "".join(f"<tr><th>{a}</th><td>{b}</td></tr>" for a, b in linhas) + "</table>"
                + '<p class="nota">D4 ainda exige VK_EXT_shader_atomic_float: as outras variantes de backward e o morton_sort.slang continuam com atômicos de float.</p>',
                ressalvas=["Slide de reserva: só se o professor perguntar sobre integridade.",
                           "'Nenhum USE_EMULATED' e 'GPU selecionada' são conferidos nos logs sem códigos ANSI; os logs originais têm cor.",
                           "Os 80 primeiros runs não têm ambiente.json; a constância do Mesa neles vem do dpkg.log e do inventário de 25/ago (caderno 2026-09-21)."])

# ================================================================== render
CSS = """
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#0f172a}
::selection{background:#99f6e4;color:#0f172a}
section{display:none;position:absolute;inset:0;margin:auto;width:min(100vw,177.78vh);height:min(56.25vw,100vh);background:#fff;padding:2.9% 4% 4.6%;overflow:hidden;font-size:min(1.38vw,2.45vh);font-variant-numeric:tabular-nums;line-height:1.38}
section.ativo{display:block}
body.todos section{display:block!important;position:relative;inset:auto;margin:0 auto 6px;width:1600px;height:900px;font-size:22px}
body.todos section.capa{display:flex!important}
section.capa.ativo{display:flex}
section.capa{flex-direction:column;justify-content:center;padding-left:6%;padding-right:6%}
h1{font-size:3em;line-height:1.04;margin:0 0 .35em;letter-spacing:-.025em;max-width:16em;text-wrap:balance}
h2{font-size:1.62em;line-height:1.14;margin:0;letter-spacing:-.015em;text-wrap:balance;max-width:30em}
h3{font-size:1em;margin:0 0 .35em;line-height:1.25}
p{margin:.3em 0}ul,ol{margin:.2em 0;padding-left:1.2em}li{margin:.24em 0}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;background:#f1f5f9;padding:.05em .3em;border-radius:4px}
.sub{font-size:1.25em;color:#334155;max-width:34em;margin:0 0 .6em}
.prov{display:inline-block;font-size:.6em;vertical-align:middle;color:#475569;border:1px solid #cbd5e1;border-radius:999px;padding:.15em .6em;margin-left:.3em}
.byline{color:#475569;font-size:.92em;margin:0 0 2.2em}
.pauta{display:grid;grid-template-columns:repeat(5,1fr);gap:1em;padding:0;margin:0;list-style:none;counter-reset:p;max-width:62em}
.pauta li{counter-increment:p;border-top:2px solid #0f172a;padding-top:.5em;font-size:.95em;line-height:1.3}
.pauta li::before{content:counter(p);display:block;font-weight:750;font-size:1.3em;color:#0f766e;margin-bottom:.15em}
.motivo{position:absolute;right:6%;top:9%;width:13%;opacity:.95}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:1.2em;margin-bottom:.7em}
.selos{display:flex;flex-direction:column;align-items:flex-end;gap:.32em;flex:none}
.selo{font-size:.64em;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:.42em .8em;border-radius:999px;white-space:nowrap}
.selo.cat{background:#0f172a;color:#fff}.selo.sus{background:#ccfbf1;color:#134e4a}.selo.ref{background:#ffedd5;color:#9a3412}
.selo.neg{background:#e2e8f0;color:#1e293b}.selo.exp{background:#fff;color:#334155;box-shadow:inset 0 0 0 1.5px #94a3b8}.selo.and{background:#fef9c3;color:#713f12}
footer{position:absolute;left:4%;right:4%;bottom:1.3%;display:flex;justify-content:space-between;gap:2em;font-size:.64em;color:#64748b;border-top:1px solid #e2e8f0;padding-top:.45em}
.dag{color:#9a3412;font-weight:700;font-size:.7em;margin-left:.08em}
.livro{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;border-top:1px solid #cbd5e1;margin:.7em 0 .5em}
.livro>div{padding:.5em 1em .1em 0}.livro>div+div{padding-left:1em;border-left:1px solid #e2e8f0}
.livro b{display:block;font-size:1.6em;font-weight:750;letter-spacing:-.02em;line-height:1.08;white-space:nowrap}
.livro span{display:block;font-size:.8em;color:#475569;line-height:1.3;margin-top:.3em}
.livro .ok b{color:#0f766e}.livro .ref b{color:#9a3412}
.livro.duas{grid-auto-flow:row;grid-template-columns:1fr 1fr}.livro.tres{margin-top:.2em}
.livro.tres b{font-size:1.25em}
.cols{display:grid;grid-template-columns:var(--g,repeat(var(--n),1fr));gap:1.7em;align-items:start}
.col>h3{border-top:2px solid #0f172a;padding-top:.45em}
.col.nada>h3{border-top:0;padding-top:0}
.col>h3:not(:first-child){margin-top:.9em}
.tab th.n{text-align:right;padding-right:1.1em}
.depois{margin-top:1em}
.nw{white-space:nowrap}
.livro.pilha{grid-auto-flow:row;grid-auto-columns:auto;margin-top:0}
.livro.pilha>div+div{border-left:0;padding-left:0;border-top:1px solid #e2e8f0;margin-top:.3em}
.col.ok>h3{border-top-color:#0f766e;color:#115e59}.col.ref>h3{border-top-color:#c2410c;color:#9a3412}.col.neutra>h3{border-top-color:#94a3b8;color:#334155}
.col.antes>h3{border-top-color:#c2410c}.col.agora>h3{border-top-color:#0f766e}
.col.pergunta{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:.8em 1em}
.col.pergunta h3{border:0;padding:0;color:#1e3a8a}
.tit{font-style:italic;color:#334155;margin-bottom:.6em}
.nota{color:#475569;font-size:.84em;margin-top:.6em}
.intro{margin:0 0 .4em;color:#334155}
.eq{background:#0f172a;color:#e2e8f0;border-radius:10px;padding:.8em 1.1em;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:1.05em;line-height:1.8;margin:.6em 0}
.eq .r{color:#fdba74}.eq .g2{color:#5eead4}
.tl{display:grid;grid-template-columns:repeat(5,1fr);gap:1em;margin:.2em 0 1.1em}
.tl>div{border-top:3px solid #334155;padding-top:.45em;font-size:.8em;line-height:1.34;color:#334155}
.tl .ano{display:block;font-weight:750;color:#c2410c;font-size:1.2em}.tl b{display:block;color:#0f172a;margin-bottom:.15em}
.rec{display:inline-block;font-size:.85em;color:#9a3412;border:1px dashed #fdba74;border-radius:4px;padding:0 .35em;margin-top:.2em}
.faixa{font-size:.8em;color:#334155;background:#f8fafc;border-radius:8px;padding:.45em .8em;margin:.1em 0 .8em}
.tab{width:100%;border-collapse:collapse;font-size:.8em}
.tab th{text-align:left;font-weight:650;border-bottom:1.5px solid #0f172a;padding:.3em .5em .3em 0;color:#0f172a}
.tab td{border-bottom:1px solid #e2e8f0;padding:.34em .6em .34em 0;vertical-align:top}
.tab td.n{text-align:right;white-space:nowrap;padding-right:1.1em}
.tab td.src{color:#64748b;white-space:nowrap}
.tab.grande{font-size:.9em}.tab .rodape{color:#475569;border-bottom:0}
.tab tr.soma td{border-top:1.5px solid #0f172a;font-weight:600}
.tab.app th{width:9em;vertical-align:top;border-bottom:1px solid #e2e8f0;padding-top:.5em}.tab.app td{padding:.5em 0}
.tab.app{font-size:.86em}
ul.git{list-style:none;padding:0;font-size:.8em}ul.git li{margin:.0 0 .5em;line-height:1.32}ul.git b{display:block;font-weight:650}
.aviso{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:.6em .9em;font-size:.82em;margin-top:.5em}
.aviso h3{color:#9a3412;margin-bottom:.2em}.aviso p{margin:0}
.aviso.neutro{background:#f8fafc;border-color:#e2e8f0}.aviso.neutro h3{color:#0f172a}.aviso ol{margin:0;padding-left:1.1em}.aviso li{margin:.15em 0}
.fatos .col h3{font-size:.9em;margin-bottom:.2em}.fatos p{font-size:.82em;line-height:1.33;margin:0}
ol.nao{columns:2;column-gap:2.4em;font-size:.94em;padding-left:1.5em;margin-top:.2em}ol.nao li{break-inside:avoid;margin:0 0 .55em;padding-left:.2em}
ol.nao li::marker{color:#9a3412;font-weight:700}
ol.decisoes{display:grid;grid-template-columns:1fr 1fr;gap:.9em 2.2em;padding-left:1.3em;margin-top:.3em}
ol.decisoes li::marker{font-weight:750;color:#1e3a8a}ol.decisoes h3{margin:0 0 .15em}ol.decisoes p{margin:0;color:#334155;font-size:.9em}
ol.opcoes{padding-left:1.4em}ol.opcoes li{margin:.4em 0}ol.opcoes li::marker{font-weight:750;color:#1e3a8a}
section.solto{font-size:min(1.6vw,2.84vh)}body.todos section.solto{font-size:25.5px}
.escada{display:flex;gap:1%;align-items:flex-end;height:31%;margin:.1em 0 .5em}
.deg{flex:1;border:1.5px solid var(--c);border-radius:9px;padding:.45em .65em;background:color-mix(in srgb,var(--c) 9%,#fff);display:flex;flex-direction:column}
.deg b{font-size:1.5em;color:color-mix(in srgb,var(--c) 78%,#000);line-height:1}.deg p{font-weight:600;font-size:.82em;margin:.25em 0 .1em;line-height:1.22}
.deg small{color:#475569;font-size:.76em;line-height:1.25}.deg em{margin-top:auto;font-style:normal;color:#475569;font-size:.76em}
.deg code{font-size:.95em;background:none;padding:0}
svg.g{width:100%;height:auto;display:block}
svg .ax{font-size:12.5px;fill:#475569}svg .lb{font-size:14px;font-weight:650;fill:#0f172a}svg .vl{font-size:11.5px;font-weight:700;fill:#0f172a}
svg .sm{font-size:13px;font-weight:650}svg .cel{font-size:13px;font-weight:700}
svg .halo{paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}
.tempo{margin:.1em 0 .8em}
#nav{display:none}
@media print{html,body{background:#fff}section{display:block!important;position:relative;page-break-after:always;width:100vw;height:56.25vw}section.capa{display:flex!important}#nav{display:none}}
"""
JS = """
if(location.search.includes('todos')){document.body.classList.add('todos');}
const s=[...document.querySelectorAll('section')];let i=0;const n=document.getElementById('nav');
function go(k){i=Math.max(0,Math.min(s.length-1,k));s.forEach((e,j)=>e.classList.toggle('ativo',j===i));n.textContent=(i+1)+' / '+s.length;history.replaceState(null,'','#'+(i+1));}
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){go(i+1);e.preventDefault()}if(['ArrowLeft','PageUp'].includes(e.key)){go(i-1);e.preventDefault()}if(e.key==='Home')go(0);if(e.key==='End')go(s.length-1)});
addEventListener('click',e=>{if(e.target.closest('a'))return;go(e.clientX>innerWidth/3?i+1:i-1)});
go((parseInt(location.hash.slice(1))||1)-1);
"""

total = len(SLIDES)
partes = []
for d in SLIDES:
    tem_dag = any(r["tipo"] == "caderno" and r["slide"] == d["n"] for r in REG)
    fontes = " · ".join(esc(f) for f in d["fontes"])
    nota_dag = '<span class="dag">†</span> número só no caderno de campo, sem arquivo em dados/' if tem_dag else ""
    rod = " · ".join(x for x in (f"Fontes: {fontes}" if fontes else "", nota_dag) if x)
    foot = f'<footer><span>{rod}</span><span>{d["n"]} / {total}</span></footer>'
    if d.get("cls") == "capa":
        partes.append(f'<section class="capa">{d["corpo"]}{foot}</section>')
        continue
    selos = "".join(f'<span class="selo {k}">{esc(t)}</span>' for k, t in d["selos"])
    head = f'<header><h2>{d["titulo"]}</h2>{f"<div class=selos>{selos}</div>" if selos else ""}</header>'
    partes.append(f'<section class="{d.get("cls", "")}">{head}{d["corpo"]}{foot}</section>')

doc_html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reprodutibilidade em treino de 3DGS: TCC</title><style>{CSS}</style></head>
<body>{''.join(partes)}<div id="nav"></div><script>{JS}</script></body></html>"""
SAIDA.write_text(doc_html, encoding="utf-8")

# =================================================================== notas
CSS_N = """
body{margin:0;background:#fff;color:#0f172a;font:17px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-variant-numeric:tabular-nums}
::selection{background:#99f6e4}
main{max-width:78ch;margin:0 auto;padding:3em 1.5em 5em}
h1{font-size:1.8em;line-height:1.15;margin:0 0 .3em;letter-spacing:-.015em}
h2{font-size:1.2em;margin:2.4em 0 .2em;padding-top:1em;border-top:2px solid #0f172a;line-height:1.25}
h3{font-size:.95em;margin:1.1em 0 .3em;color:#334155}
.meta{color:#475569;margin:0 0 .6em}
ol,ul{padding-left:1.3em}li{margin:.35em 0}
table{width:100%;border-collapse:collapse;font-size:.86em}
th{text-align:left;border-bottom:1.5px solid #0f172a;padding:.3em .5em .3em 0}
td{border-bottom:1px solid #e2e8f0;padding:.3em .6em .3em 0;vertical-align:top}
td.v{white-space:nowrap;font-weight:650}
.t-caderno td.v{color:#9a3412}.tipo{color:#64748b;white-space:nowrap}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em}
@media print{h2{break-before:page}}
"""
tot_s = sum(d["tempo"] for d in SLIDES)
blocos = []
for d in SLIDES:
    nums = [r for r in REG if r["slide"] == d["n"]]
    vistos, uniq = set(), []
    for r in nums:
        k = (r["valor"], r["rotulo"])
        if k not in vistos:
            vistos.add(k)
            uniq.append(r)
    tab = "".join(f'<tr class="t-{r["tipo"]}"><td class="v">{r["valor"]}</td><td>{esc(r["rotulo"])}</td><td>{esc(r["fonte"])}</td><td class="tipo">{r["tipo"]}</td></tr>' for r in uniq)
    tit = re.sub(r"<[^>]+>", "", d["titulo"])
    tempo = f"~{d['tempo']//60} min {d['tempo']%60:02d} s" if d["tempo"] else "reserva, fora do tempo"
    blocos.append(f"""<h2>{d['n']}. {tit}</h2><p class="meta">Tempo-alvo: {tempo}</p>
<h3>Ressalvas completas</h3><ol>{''.join(f'<li>{x}</li>' for x in d['ressalvas'])}</ol>
{f'<h3>Números e fontes</h3><table><tr><th>valor</th><th>o que é</th><th>fonte</th><th>tipo</th></tr>{tab}</table>' if tab else ''}""")
notas = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Notas da apresentação ao Prof. Gilvan</title><style>{CSS_N}</style></head><body><main>
<h1>Notas da apresentação ao Prof. Gilvan</h1>
<p class="meta">Gerado por <code>apresentacao/gerar_apresentacao.py</code>. {total} slides; tempo-alvo somado: {tot_s//60} min {tot_s%60:02d} s, para um limite de 20 min. Contagem de dias a partir de {dm(REF)}/{REF.year} ({'data da reunião' if ARGS.data else 'data de geração'}).</p>
<p class="meta">Tipos de fonte: <b>calculado</b> = calculado pelo gerador a partir do arquivo citado; <b>documento</b> = número que existe só em documento versionado; <b>caderno</b> = número que existe só no caderno de campo (saída de terminal ou projeção), marcado com † no slide.</p>
{''.join(blocos)}
</main></body></html>"""
SAIDA_NOTAS.write_text(notas, encoding="utf-8")

# ============================================================ conferencia
print(f"escrito: {SAIDA.name} ({total} slides, {len(doc_html)//1024} KB) e {SAIDA_NOTAS.name}; tempo-alvo {tot_s/60:.1f} min")
print(f"H1 {n_dist}/{n_exec}  D0 {h1_d0}  D4 {h_d4}")
print(f"H2 {h2_k}/{h2_n}={100*h2_frac:.2f}%  IC={np.round(100*h2_ic,2)}  N10={100*h2_por_n[10]:.1f} N20={100*h2_por_n[20]:.1f}  blocos={[round(100*x,1) for x in h2_bloco]}  D2 blocos={[round(100*x,1) for x in h2_bloco_d2]}")
for h in H3:
    print(f"  {h['a']}->{h['b']}: p={h['p']:.4f} rz={h['rz']:.3f} IC=[{h['lo']:.3f},{h['hi']:.3f}] {'SUST' if h['ok'] else 'nao'}")
print(f"  global p={p_global:.3f}  N20 D0xD3 p={p_n20:.4f} rz={rz_n20:.3f}  var IQR D3 blocos={var_d3:.2f}  IQB={ {d:[round(x,4) for x in v] for d,v in IQB.items()} }")
print(f"D3xD4 p={p34:.4f} rz={rz34:.4f} IC=[{lo34:.4f},{hi34:.4f}] | estrato p={p34s:.4f} rz={rz34s:.4f} IC=[{lo34s:.4f},{hi34s:.4f}] | N p={p34n:.2e} rz={rz34n:.5f} IC=[{lo34n:.5f},{hi34n:.5f}]")
print(f"dPSNR={dq:.4f} dT={100*dt_pct:.1f}% morton={100*morton_pct:.1f}%  S={S_ESC} p99<1 desde {P99_DESDE}  S_reg={S_REGIME} capac={ {k:round(v,2) for k,v in CAPAC.items()} }")
print(f"esp10k={ {k:round(v,3) for k,v in MAX_ESP_10K.items()} } razao denso={ {k:round(v,1) for k,v in RAZ_DENSO.items()} }")
print(f"ply: ms={mesmo_ms} byte={ident_b} fr_gauss=[{min(fr_gauss):.4f},{max(fr_gauss):.4f}] pos=[{min(fr_pos):.3f},{max(fr_pos):.3f}] esc=[{min(fr_esc):.3f},{max(fr_esc):.3f}] rot=[{min(fr_rot):.3f},{max(fr_rot):.3f}]")
print(f"onset={onset} ev={n_ev} grupo={grupo_d4} seqs={seq_d4}  TR_L={TR_L['ultimo']}->{TR_L['primeiro']} ({len(TR_L['dif'])} buf)  TR_D={TR_D['ultimo']}->{TR_D['primeiro']} {[b for _,b in TR_D['dif']]}")
print(f"F1={F1}  ler={[round(x,3) for x in ler_frac]}  img_iguais={img_iguais} recomp={[round(x,2) for x in recomp]}")
print(f"F2={F2}  CAP={CAP}  reps={reps_d4} ev={ev_d4} IC={ic_tot}  n_inst={n_inst} modal={n_modal_d4}")
print(f"INT={ {d:(v['n'],len(v['commits']),v['limpos'],v['dev0'],v['gpu'],v['emul']) for d,v in INT.items()} } AMB={len(AMB)} mesa={mesa_v} libc={libc_v}")
print(f"sim float32={sim_f} int32={sim_i}  ex=({ex_a},{ex_b})  inicio_d0={inicio_d0}  dias_dep={dias_dep} janela={janela}  serie_h={serie_h:.2f}")
