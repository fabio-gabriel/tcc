#!/usr/bin/env python3
"""
Gera a apresentacao para o Prof. Gilvan a partir dos dados versionados.

Nenhum numero e digitado a mao: todos sao calculados aqui a partir de
pivo-reprodutibilidade-3dgs/dados/. Gera um unico HTML autocontido (graficos em
SVG inline, sem internet). Navegacao: setas, espaco, ou clique.

Uso:  python3 apresentacao/gerar_apresentacao.py
Saida: apresentacao/apresentacao-gilvan.html
"""
import glob, html, itertools, json, math, os, re, statistics as st
from pathlib import Path
import numpy as np
from scipy.stats import fligner

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "pivo-reprodutibilidade-3dgs" / "dados"
SAIDA = Path(__file__).resolve().parent / "apresentacao-gilvan.html"
DEGRAUS = ["D0", "D1", "D2", "D3", "D4"]

# ----------------------------------------------------------------- dados
def _psnr(rd):
    def f(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.lower() == "psnr" and isinstance(v, (int, float)):
                    return v
                r = f(v)
                if r is not None:
                    return r
    return f(json.load(open(rd / "eval.json")))

PAT = re.compile(rb"(\d+) dupli, (\d+) split, (\d+) prune -> (\d+) splats")

def carregar(deg):
    runs = []
    for rd in sorted((DADOS / deg).glob("run*")):
        tr = json.load(open(rd / "train.json"))
        log = next(rd.glob("run*.log"))
        runs.append({
            "idx": int(rd.name[3:]),
            "psnr": _psnr(rd),
            "n": tr["num_splats"],
            "t": tr["time_elapsed"],
            "dens": [int(m[3]) for m in PAT.findall(log.read_bytes())],
        })
    hashes = [l.split("\t")[3] for l in open(DADOS / deg / "manifest.tsv")
              if l.split("\t")[1:2] == ["splat.ply"]]
    return runs, hashes

R, H = {}, {}
for d in DEGRAUS:
    R[d], H[d] = carregar(d)

iqr = lambda v: float(np.subtract(*np.percentile(v, [75, 25])))
P = {d: np.array([r["psnr"] for r in R[d]]) for d in DEGRAUS}
NS = {d: np.array([r["n"] for r in R[d]], float) for d in DEGRAUS}
T = {d: np.array([r["t"] for r in R[d]]) for d in DEGRAUS}

n_exec = sum(len(R[d]) for d in DEGRAUS)
h_d0d3 = [h for d in DEGRAUS[:4] for h in H[d]]
h1_total, h1_dist = len(h_d0d3), len(set(h_d0d3))
h4_total, h4_dist = len(H["D4"]), len(set(H["D4"]))
pares = list(itertools.combinations(P["D0"], 2))
h2_k = sum(abs(a - b) >= 0.10 for a, b in pares); h2_n = len(pares)
h2_frac = 100 * h2_k / h2_n
ampl_d0 = float(P["D0"].max() - P["D0"].min())
horas = sum(T[d].sum() for d in DEGRAUS) / 3600

def boot(x, y, seed=20260909, B=10000):
    rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        ix = iqr(rng.choice(x, len(x)))
        bs.append(iqr(rng.choice(y, len(y))) / ix if ix > 0 else np.nan)
    return np.nanpercentile(bs, [2.5, 97.5])

fl_p = fligner(P["D3"], P["D4"])[1]
razao = iqr(P["D4"]) / iqr(P["D3"]); ic_lo, ic_hi = boot(P["D3"], P["D4"])
red_psnr = iqr(P["D3"]) / iqr(P["D4"])
red_n = iqr(NS["D3"]) / iqr(NS["D4"])
dq = float(np.median(P["D4"]) - np.median(P["D3"]))
dt = 100 * (np.median(T["D4"]) / np.median(T["D3"]) - 1)

# primeiro evento de densificacao em que as execucoes divergem (bloco de N=10
# do mesmo estrato de ambiente: run020-029 em D0-D3, todas em D4)
def bloco(d):
    return [r for r in R[d] if d == "D4" or r["idx"] >= 20]
def spread(d):
    S = [r["dens"] for r in bloco(d)]
    L = min(map(len, S))
    return [max(s[i] for s in S) - min(s[i] for s in S) for i in range(L)]
SP = {d: spread(d) for d in DEGRAUS}
onset = {d: next((i for i, v in enumerate(SP[d]) if v > 0), None) for d in DEGRAUS}
n_eventos = len(SP["D4"])
grupo5 = max(sum(1 for r in R["D4"] if r["dens"] == s["dens"]) for s in R["D4"])

# ----------------------------------------------------------- utilitarios SVG
COR = {"D0": "#c2410c", "D1": "#d97706", "D2": "#ca8a04", "D3": "#64748b", "D4": "#0f766e"}
def br(x, nd=2):
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def svg_strip():
    """PSNR de cada execucao, centrado na mediana do proprio degrau."""
    W, Hh, ml, mr, mt, mb = 620, 340, 64, 16, 34, 46
    ymax = 0.11
    def ty(v): return mt + (ymax - v) / (2 * ymax) * (Hh - mt - mb)
    cw = (W - ml - mr) / len(DEGRAUS)
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g">']
    o.append(f'<rect x="{ml}" y="{ty(0.05):.1f}" width="{W-ml-mr}" height="{ty(-0.05)-ty(0.05):.1f}" fill="#fff7ed"/>')
    for v in (-0.10, -0.05, 0, 0.05, 0.10):
        o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="{"#94a3b8" if v==0 else "#e2e8f0"}"/>')
        o.append(f'<text x="{ml-8}" y="{ty(v)+4:.1f}" text-anchor="end" class="ax">{"+" if v>0 else ""}{br(v)}</text>')
    o.append(f'<text x="14" y="{(mt+Hh-mb)/2:.0f}" transform="rotate(-90 14 {(mt+Hh-mb)/2:.0f})" text-anchor="middle" class="ax">PSNR − mediana do degrau (dB)</text>')
    rng = np.random.default_rng(7)
    for i, d in enumerate(DEGRAUS):
        cx = ml + cw * (i + .5); m = np.median(P[d])
        for v in P[d]:
            o.append(f'<circle cx="{cx + rng.uniform(-cw*.28, cw*.28):.1f}" cy="{ty(v-m):.1f}" r="4.2" fill="{COR[d]}" fill-opacity=".75"/>')
        o.append(f'<text x="{cx:.0f}" y="{Hh-24}" text-anchor="middle" class="lb">{d}</text>')
        o.append(f'<text x="{cx:.0f}" y="{Hh-8}" text-anchor="middle" class="ax">N={len(P[d])}</text>')
    o.append(f'<rect x="{ml}" y="6" width="14" height="10" fill="#fff7ed" stroke="#fed7aa"/>')
    o.append(f'<text x="{ml+20}" y="15" class="ax">faixa de ±0,05 dB em torno da mediana: dois pontos fora dela, em lados opostos, diferem 0,10 dB ou mais</text>')
    o.append("</svg>"); return "".join(o)

def svg_iqr_gauss():
    W, Hh, ml, mr, mt, mb = 360, 330, 60, 12, 18, 46
    vals = {d: iqr(NS[d]) for d in DEGRAUS}
    lo, hi = 1, 1e5
    def ty(v): return mt + (math.log10(hi) - math.log10(max(v, lo))) / (math.log10(hi) - math.log10(lo)) * (Hh - mt - mb)
    cw = (W - ml - mr) / len(DEGRAUS)
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g">']
    for e in range(0, 6):
        v = 10 ** e
        o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="#e2e8f0"/>')
        o.append(f'<text x="{ml-8}" y="{ty(v)+4:.1f}" text-anchor="end" class="ax">{br(v,0)}</text>')
    o.append(f'<text x="14" y="{(mt+Hh-mb)/2:.0f}" transform="rotate(-90 14 {(mt+Hh-mb)/2:.0f})" text-anchor="middle" class="ax">IQR do nº de gaussianas (escala log)</text>')
    for i, d in enumerate(DEGRAUS):
        x = ml + cw * i + cw * .18; w = cw * .64; y = ty(vals[d])
        o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{Hh-mb-y:.1f}" fill="{COR[d]}" rx="3"/>')
        o.append(f'<text x="{x+w/2:.1f}" y="{y-6:.1f}" text-anchor="middle" class="vl">{br(vals[d],0)}</text>')
        o.append(f'<text x="{x+w/2:.1f}" y="{Hh-24}" text-anchor="middle" class="lb">{d}</text>')
    o.append("</svg>"); return "".join(o)

def svg_onset():
    W, Hh, ml, mr, mt, mb = 900, 250, 64, 20, 30, 42
    L = n_eventos; ymax = max(max(SP[d]) for d in DEGRAUS)
    def tx(i): return ml + i / (L - 1) * (W - ml - mr)
    def ty(v): return mt + (1 - math.log10(1 + v) / math.log10(1 + ymax)) * (Hh - mt - mb)
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g">']
    for v in (0, 10, 100, 1000, 10000):
        if v <= ymax:
            o.append(f'<line x1="{ml}" x2="{W-mr}" y1="{ty(v):.1f}" y2="{ty(v):.1f}" stroke="#e2e8f0"/>')
            o.append(f'<text x="{ml-8}" y="{ty(v)+4:.1f}" text-anchor="end" class="ax">{br(v,0)}</text>')
    for i in (0, 24, 48, 72, 96, 120, L - 1):
        o.append(f'<text x="{tx(i):.1f}" y="{Hh-22}" text-anchor="middle" class="ax">{i}</text>')
    o.append(f'<text x="{(ml+W-mr)/2:.0f}" y="{Hh-4}" text-anchor="middle" class="ax">evento de densificação (de {L}), na ordem do treino</text>')
    o.append(f'<text x="{ml}" y="14" class="ax">diferença máx − mín do nº de gaussianas entre 10 execuções (escala log)</text>')
    for d in DEGRAUS:
        pts = " ".join(f"{tx(i):.1f},{ty(v):.1f}" for i, v in enumerate(SP[d]))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{COR[d]}" stroke-width="{3.4 if d=="D4" else 1.6}" stroke-opacity="{1 if d in ("D3","D4") else .6}"/>')
    i4 = onset["D4"]
    o.append(f'<line x1="{tx(i4):.1f}" x2="{tx(i4):.1f}" y1="{mt}" y2="{Hh-mb}" stroke="#0f766e" stroke-dasharray="4 4"/>')
    o.append(f'<text x="{tx(i4)-10:.1f}" y="{ty(3):.1f}" text-anchor="end" class="lb halo" fill="#0f766e">D4: as 10 execuções são idênticas até o evento {i4}</text>')
    o.append(f'<text x="{tx(30):.1f}" y="{ty(1500):.1f}" class="lb halo" fill="#475569">D0 a D3: divergem já no evento 0</text>')
    # legenda
    lx = W - mr - 5 * 62
    for k, d in enumerate(DEGRAUS):
        x = lx + k * 62
        o.append(f'<line x1="{x}" x2="{x+18}" y1="10" y2="10" stroke="{COR[d]}" stroke-width="3"/>')
        o.append(f'<text x="{x+22}" y="14" class="ax">{d}</text>')
    o.append("</svg>"); return "".join(o)

def svg_d0_vs_literatura():
    W, Hh, ml, mr = 900, 200, 250, 24
    lo, hi = float(P["D0"].min()) - 0.01, float(P["D0"].max()) + 0.01
    def tx(v): return ml + (v - lo) / (hi - lo) * (W - ml - mr)
    o = [f'<svg viewBox="0 0 {W} {Hh}" class="g">']
    y0 = 40
    o.append(f'<text x="{ml-14}" y="{y0+5}" text-anchor="end" class="lb">30 execuções idênticas (D0)</text>')
    o.append(f'<line x1="{tx(lo)}" x2="{tx(hi)}" y1="{y0}" y2="{y0}" stroke="#e2e8f0" stroke-width="2"/>')
    for v in P["D0"]:
        o.append(f'<circle cx="{tx(v):.1f}" cy="{y0}" r="5.5" fill="#c2410c" fill-opacity=".55"/>')
    for v in np.arange(math.ceil(lo * 20) / 20, hi, 0.05):
        o.append(f'<text x="{tx(v):.1f}" y="{y0+24}" text-anchor="middle" class="ax">{br(v)}</text>')
    o.append(f'<text x="{tx(hi)}" y="{y0-16}" text-anchor="end" class="ax">PSNR (dB), com mesma cena, seed e commit</text>')
    lit = [("gsplat, feature", 0.03), ('gsplat, "paridade"', 0.05), ("Mip-Splatting", 0.09),
           ("gsplat, feature", 0.11), ("gsplat, feature", 0.18)]
    base = float(np.median(P["D0"]))
    y = 96
    o.append(f'<text x="{ml-14}" y="{y-8}" text-anchor="end" class="ax">ganhos publicados, na mesma escala:</text>')
    for k, (nome, dv) in enumerate(lit):
        yy = y + k * 19
        x1, x2 = tx(base - dv / 2), tx(base + dv / 2)
        o.append(f'<text x="{ml-14}" y="{yy+10}" text-anchor="end" class="ax">+{br(dv)} dB · {html.escape(nome, quote=False)}</text>')
        o.append(f'<rect x="{x1:.1f}" y="{yy}" width="{x2-x1:.1f}" height="12" fill="#334155" rx="2"/>')
    o.append("</svg>"); return "".join(o)

def html_escada():
    itens = [("D0", "código como distribuído", "nada (é a referência)"),
             ("D1", "+ semear a ordem das imagens", "ordem dos dados"),
             ("D2", "+ fixar o kernel de backward", "escalonador por latência"),
             ("D3", "+ desligar a reordenação Morton", "6 atômicos float + permutação"),
             ("D4", "+ acumulação em ponto fixo (int32)", "9 atômicos float do backward")]
    o = ['<div class="escada">']
    for i, (d, o1, o2) in enumerate(itens):
        o.append(f'<div class="deg" style="--c:{COR[d]};height:{52+i*12}%"><b>{d}</b>'
                 f'<p>{html.escape(o1)}</p><small>remove: {html.escape(o2)}</small>'
                 f'<em>N = {len(R[d])}</em></div>')
    o.append("</div>"); return "".join(o)

# ------------------------------------------------------------------- slides
mediana = lambda d: br(float(np.median(P[d])), 3)
S = []

S.append(f"""
<section class="capa">
  <p class="kicker">TCC · Engenharia de Computação · UFC · orientação: Prof. Gilvan · outubro de 2026</p>
  <h1>Reprodutibilidade em treino de<br>3D Gaussian Splatting</h1>
  <p class="sub">Treinos com a mesma cena, a mesma seed, o mesmo código e a mesma máquina terminam em modelos diferentes.
  O trabalho mede o tamanho dessa diferença e testa uma correção na causa.</p>
  <div class="kpis">
    <div><b>{n_exec}</b><span>execuções de treino medidas<br>(~{br(horas,0)} h de GPU)</span></div>
    <div><b>{h1_dist}/{h1_total}</b><span>modelos com hash distinto<br>no código original</span></div>
    <div><b>{br(h2_frac,1)}%</b><span>dos pares diferem 0,10 dB ou mais,<br>a ordem de vários ganhos publicados</span></div>
    <div class="ok"><b>{br(red_psnr,0)}×</b><span>menos dispersão de PSNR<br>com a intervenção D4</span></div>
  </div>
</section>""")

S.append("""
<section class="solto">
  <h2>Por que o tema mudou</h2>
  <div class="duas">
    <div class="card antes">
      <h3>Antes: comparação de desempenho entre backends</h3>
      <p class="tit">"Renderização neural em hardware heterogêneo: custo de backends agnósticos"</p>
      <ul>
        <li>Hardware, backend e implementação mudavam ao mesmo tempo, então nenhuma diferença podia ser atribuída a um deles.</li>
        <li>Não tenho GPU NVIDIA; a comparação dependeria de aluguel.</li>
        <li>O resultado seria um speedup, sem explicar o mecanismo.</li>
        <li>A variante com MLP fundido em Vulkan esbarrou em limitações de API que não cabiam em 10 semanas.</li>
      </ul>
    </div>
    <div class="seta">→</div>
    <div class="card agora">
      <h3>Agora: reprodutibilidade do treino</h3>
      <p class="tit">Quão reprodutíveis são as métricas de 3DGS, e o que a dispersão entre execuções implica para os resultados publicados?</p>
      <ul>
        <li>As hipóteses declaram o mecanismo e o que as refutaria.</li>
        <li>Tudo roda no meu hardware (RX 9070 XT, Vulkan), sem comparar fornecedores.</li>
        <li>Reaproveito o VkSplat, que treina 3DGS em Vulkan; colocá-lo para rodar em RDNA 4 já foi parte do trabalho.</li>
        <li>Há código meu: uma intervenção que testa a causa.</li>
      </ul>
    </div>
  </div>
  <p class="nota">O protocolo foi registrado em commit antes das execuções. Mudanças posteriores entraram como desvios declarados e datados.</p>
</section>""")

S.append("""
<section class="solto">
  <h2>O mecanismo: em ponto flutuante, a ordem da soma muda o resultado</h2>
  <div class="duas">
    <div>
      <p>No backward do 3DGS, milhares de threads da GPU somam gradientes no mesmo endereço com adição atômica em float32. A ordem dessas somas varia de uma execução para outra, e em float32 a ordem altera o resultado:</p>
      <div class="eq">
        <div>(16.777.216 + 1) + 1 = <b class="r">16.777.216</b></div>
        <div>16.777.216 + (1 + 1) = <b class="g2">16.777.218</b></div>
      </div>
      <p class="nota">Valores calculados em float32.</p>
    </div>
    <div>
      <p>Simulação: os mesmos 1.000 gradientes, da ordem de 10<sup>−6</sup>, somados em 20 ordens diferentes.</p>
      <div class="kpis dois">
        <div><b>9</b><span>resultados distintos<br>em float32</span></div>
        <div class="ok"><b>1</b><span>resultado em inteiro<br>(ponto fixo, como em D4)</span></div>
      </div>
      <p>A soma inteira é associativa (módulo 2<sup>32</sup>, pela especificação SPIR-V). D4 converte cada gradiente para ponto fixo antes da soma atômica, e com isso a ordem deixa de importar.</p>
    </div>
  </div>
</section>""")

S.append(f"""
<section class="solto">
  <h2>O que a literatura já tem e o que ainda falta</h2>
  <div class="tl">
    <div><i>2023</i><b>Kerbl, coautor do 3DGS</b>Issue #89: "sempre haverá ALGUMA aleatoriedade causada pelo escalonamento da GPU". A issue foi fechada sem correção.</div>
    <div><i>2024</i><b>Mantenedor do gsplat</b>Issue nerfstudio #2996: atribui o fenômeno aos atômicos de ponto flutuante, sem medir.</div>
    <div><i>2025</i><b>NerfBaselines v2</b>NeurIPS D&amp;B: σ de PSNR sobre 4 treinos do 3DGS, agregado por dataset (±0,02 dB).</div>
    <div><i>2026</i><b>FreeTimeGS++</b>10 execuções em 4DGS, com seed variável; a causa é atribuída a "small stochastic differences".</div>
  </div>
  <div class="duas lit">
    <div class="card"><h3>Já existe</h3><ul><li>O fenômeno já é conhecido; este trabalho não o descobre.</li><li>Alguns trabalhos já reportam a dispersão.</li></ul></div>
    <div class="card agora"><h3>Onde está a contribuição</h3><ul><li>Não encontrei trabalho que separe as fontes por ablação.</li><li>Nem que intervenha na causa numérica e meça o custo de eliminá-la.</li></ul></div>
  </div>
  <p class="nota">A busca de originalidade ainda não cobriu IEEE Xplore, ACM DL, Eurographics e OpenReview.</p>
</section>""")

S.append(f"""
<section>
  <h2>Método: escada de ablação em cinco degraus</h2>
  {html_escada()}
  <div class="faixa">
    <div>Cena: garden (Mip-NeRF 360), images_4, 30.000 passos, densificação ADC.</div>
    <div>Máquina: RX 9070 XT (RDNA 4), Ubuntu 24.04, RADV/Mesa 25.2.8, ambiente congelado.</div>
    <div>Por execução: PSNR, SSIM, LPIPS, número de gaussianas, tempo, hash do modelo e ambiente.</div>
  </div>
  <p class="nota">Cada degrau acrescenta uma intervenção ao anterior e tem um commit próprio no fork. Os testes de dispersão (Fligner-Killeen e IC bootstrap da razão de IQRs) estão no pré-registro.</p>
</section>""")

S.append(f"""
<section>
  <h2>Resultado 1: o código original não é reprodutível</h2>
  {svg_d0_vs_literatura()}
  <div class="kpis">
    <div><b>{h1_dist}/{h1_total}</b><span>hashes distintos de D0 a D3<br><em>H1 confirmada</em></span></div>
    <div><b>{h2_k}/{h2_n}</b><span>pares de D0 com |ΔPSNR| ≥ 0,10 dB ({br(h2_frac,1)}%)<br><em>H2 sustentada (critério: ≥ 5%)</em></span></div>
    <div><b>{br(ampl_d0,2)} dB</b><span>amplitude de PSNR entre<br>30 execuções idênticas</span></div>
  </div>
  <p class="nota">Com uma execução por método, uma diferença de 0,1 dB pode ser só variação entre execuções.</p>
</section>""")

S.append(f"""
<section>
  <h2>Resultado 2: só D4 reduz a dispersão de forma mensurável</h2>
  <div class="duas g">
    <div>{svg_strip()}</div>
    <div>{svg_iqr_gauss()}</div>
  </div>
  <div class="duas">
    <div class="card"><h3>D0 → D3</h3><p>O efeito não se estabelece: com N = 30, nenhuma das hipóteses H3.1 a H3.3 passa no teste. Seria preciso N ≈ 95 por degrau, o que não cabe no prazo. A própria medida de dispersão varia 3,6× entre blocos de 10 execuções.</p></div>
    <div class="card agora"><h3>D3 → D4</h3><p>O IQR de PSNR fica {br(red_psnr,0)}× menor e o de gaussianas, {br(red_n,0)}× menor. Fligner p = {br(fl_p,3)}; razão de IQRs {br(razao,3)}, IC 95% [{br(ic_lo,3)}; {br(ic_hi,3)}], que exclui 1.<br><small>É uma análise complementar com o método do pré-registro. O critério de H3.4 é o hash idêntico, tratado no próximo slide.</small></p></div>
  </div>
</section>""")

S.append(f"""
<section>
  <h2>Resultado 3: com D4, as execuções só divergem no fim do treino</h2>
  {svg_onset()}
  <div class="kpis">
    <div><b>0 → {onset['D4']}</b><span>evento (de {n_eventos}) em que as execuções<br>começam a divergir, D3 → D4</span></div>
    <div><b>{grupo5}/10</b><span>execuções de D4 com densificação<br>idêntica do início ao fim</span></div>
    <div class="ruim"><b>{h4_dist}/{h4_total}</b><span>hashes ainda distintos em D4<br><em>H3.4 refutada pelo critério</em></span></div>
    <div class="ruim"><b>{br(dq,2)} dB</b><span>PSNR mediano, D3 → D4<br>(tempo {br(-dt,0)}% menor)</span></div>
  </div>
  <p class="nota">A acumulação atômica em float é a fonte dominante e aparece desde o início do treino. Sobra uma fonte rara, que só se manifesta no fim e ainda não foi identificada.
  A perda de qualidade provavelmente vem da escala de quantização escolhida para a cônica, que zera quase todo esse gradiente, e não do determinismo em si. Isso ainda precisa ser testado (D4b).</p>
</section>""")

S.append("""
<section class="solto">
  <h2>Situação atual e próximos passos (depósito em 06/11)</h2>
  <div class="tres">
    <div class="card"><h3>Feito</h3><ul>
      <li>Pré-registro em commit, com desvios declarados</li>
      <li>Degraus D0 a D4 implementados, cada um num commit</li>
      <li>130 execuções medidas; H1 e H2 confirmadas</li>
      <li>D4 cabe em 4 arquivos de shader, sem mudar o C++, e foi conferido no binário</li>
      <li>Busca de literatura e de originalidade, ainda parcial</li>
    </ul></div>
    <div class="card agora"><h3>Falta no experimento</h3><ul>
      <li>D4b: dimensionar a escala da cônica pelo regime do treino, para separar o artefato do custo real do determinismo (~3 h de GPU)</li>
      <li>Comparar os modelos de D4 entre si para localizar a fonte residual (minutos)</li>
    </ul><h3>Falta no texto</h3><ul>
      <li>Nenhum capítulo escrito ainda; o pré-registro já cobre boa parte do capítulo de método</li>
      <li>Fechar a busca de originalidade</li>
    </ul></div>
    <div class="card pergunta"><h3>Preciso validar com o senhor</h3><ul>
      <li>O tema e o título novos</li>
      <li>Se o escopo atual basta ou se o D4b é necessário</li>
      <li>A estrutura dos capítulos e os prazos intermediários</li>
      <li>A composição da banca</li>
    </ul></div>
  </div>
</section>""")

S.append("""
<section>
  <h2>Extensões possíveis, além do prazo</h2>
  <div class="tres">
    <div class="card"><h3>Fechar o que D4 deixou aberto</h3><ul>
      <li>Identificar a fonte residual que separa as execuções no fim do treino.</li>
      <li>Tornar determinística só a fase ComputeStats do Morton. Desligá-lo inteiro, como em D3, custou 14% de tempo.</li>
      <li>Trocar o ponto fixo por somatório reprodutível (Demmel e Nguyen; Collange et al.), que dispensa escolher escala.</li>
      <li>Rodar o teste H3b (perturbar 1 bit a partir de D4), previsto no pré-registro.</li>
    </ul></div>
    <div class="card"><h3>Ampliar o alcance</h3><ul>
      <li>Outras cenas do Mip-NeRF 360 e outras resoluções; hoje há uma cena só.</li>
      <li>A estratégia MCMC de densificação, que fixa o número de gaussianas.</li>
      <li>Outras GPUs e drivers Vulkan. O mecanismo vale para qualquer implementação que use atômicos de float.</li>
    </ul></div>
    <div class="card agora"><h3>Outros algoritmos</h3><ul>
      <li>A escada de ablação, o teste por hash e o ponto fixo servem para qualquer treino em GPU que some gradientes com atômicos de float.</li>
      <li>O 3DGS original em CUDA e o gsplat (com GPU NVIDIA), e métodos que reaproveitam o rasterizador do 3DGS.</li>
      <li>NeRF e outros campos neurais, se o backward deles usar atômicos de float; é preciso conferir caso a caso.</li>
      <li>Abrir uma issue no VkSplat com as medições e o patch de D4.</li>
    </ul></div>
  </div>
</section>""")


CSS = """
*{box-sizing:border-box}html,body{margin:0;height:100%;background:#0f172a;font-family:-apple-system,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;color:#0f172a}
section{display:none;position:absolute;inset:0;margin:auto;width:min(100vw,177.78vh);height:min(56.25vw,100vh);background:#fff;padding:3.2% 4.2%;overflow:hidden;font-size:min(1.45vw,2.58vh)}
section.ativo{display:block}
h1{font-size:3.1em;line-height:1.05;margin:.4em 0 .35em;letter-spacing:-.02em}
h2{font-size:1.85em;margin:0 0 .55em;letter-spacing:-.01em}
h3{font-size:1.05em;margin:.1em 0 .4em}
p{line-height:1.42;margin:.35em 0}ul{margin:.2em 0;padding-left:1.15em}li{margin:.28em 0;line-height:1.35}
.kicker{color:#64748b;font-size:.9em;letter-spacing:.02em;text-transform:uppercase}
.sub{font-size:1.18em;max-width:60em;color:#334155}
.capa{background:linear-gradient(135deg,#fff 60%,#f0fdfa)}
section.capa.ativo{display:flex;flex-direction:column;justify-content:center}
body.todos section{display:block!important;position:relative;inset:auto;margin:0 0 4px;width:1600px;height:900px;font-size:23.2px}
body.todos section.capa{display:flex!important;flex-direction:column;justify-content:center}
.kpis{display:flex;gap:1.1em;margin:1.1em 0 .6em}.kpis>div{flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-left:5px solid #c2410c;border-radius:10px;padding:.7em .9em}
.kpis b{display:block;font-size:2.05em;line-height:1.05;letter-spacing:-.02em}.kpis span{color:#475569;font-size:.86em;line-height:1.3;display:block;margin-top:.25em}
.kpis em{color:#0f172a;font-style:normal;font-weight:600}
.kpis .ok{border-left-color:#0f766e}.kpis .ok b{color:#0f766e}.kpis .ruim{border-left-color:#64748b}
.kpis.dois>div{flex:none;width:46%}
.duas{display:flex;gap:1.6em;align-items:stretch}.duas>div{flex:1}.duas.g>div:first-child{flex:1.7}
.tres{display:flex;gap:1.1em}.tres>div{flex:1}
.card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:.8em 1em;font-size:.95em}
.card.agora{background:#f0fdfa;border-color:#99f6e4}.card.antes{background:#fff7ed;border-color:#fed7aa}.card.pergunta{background:#eff6ff;border-color:#bfdbfe}
.tit{font-style:italic;color:#475569}
.seta{flex:none!important;align-self:center;font-size:2.6em;color:#94a3b8}
.nota{color:#475569;font-size:.88em;margin-top:.8em}
.eq{background:#0f172a;color:#e2e8f0;border-radius:10px;padding:.9em 1.1em;font-family:ui-monospace,Menlo,monospace;font-size:1.2em;line-height:1.8;margin:.6em 0}
.eq .r{color:#fb923c}.eq .g2{color:#5eead4}
.tl{display:grid;grid-template-columns:repeat(4,1fr);gap:.8em;margin-bottom:.9em}.tl>div{border-top:4px solid #334155;padding-top:.5em;font-size:.86em;line-height:1.35}
.tl i{display:block;font-style:normal;font-weight:700;color:#c2410c;font-size:1.15em}.tl b{display:block}
.lit .card{font-size:.92em}
.faixa{display:flex;gap:1em;margin-top:.6em}.faixa>div{flex:1;font-size:.85em;color:#334155;background:#f8fafc;border-radius:8px;padding:.55em .8em}
svg.g{width:100%;height:auto;display:block}
svg .ax{font-size:12px;fill:#64748b}svg .lb{font-size:14px;font-weight:600;fill:#0f172a}svg .vl{font-size:12px;font-weight:700;fill:#0f172a}
svg .big{font-size:26px;font-weight:800}svg .sm{font-size:13px;fill:#0f172a;font-weight:600}
section.solto{font-size:min(1.78vw,3.17vh)}
body.todos section.solto{font-size:28.5px}
.escada{display:flex;gap:1%;align-items:flex-end;height:54%;margin:.4em 0 .8em}
.deg{flex:1;border:1.5px solid var(--c);border-radius:10px;padding:.55em .7em;background:color-mix(in srgb,var(--c) 10%,#fff);display:flex;flex-direction:column}
.deg b{font-size:1.9em;color:var(--c);line-height:1}.deg p{font-weight:600;font-size:.92em;margin:.35em 0 .2em;line-height:1.25}
.deg small{color:#475569;font-size:.8em;line-height:1.3}.deg em{margin-top:auto;font-style:normal;color:#64748b;font-size:.8em}
section.solto .eq{font-size:1em}
svg .halo{paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}
#nav{position:fixed;right:1.2em;bottom:.8em;color:#94a3b8;font:12px system-ui;z-index:9}
@media print{html,body{background:#fff}section{display:block!important;position:relative;page-break-after:always;width:100vw;height:56.25vw}#nav{display:none}}
"""
JS = """
if(location.search.includes('todos')){document.body.classList.add('todos');}
const s=[...document.querySelectorAll('section')];let i=0;const n=document.getElementById('nav');
function go(k){i=Math.max(0,Math.min(s.length-1,k));s.forEach((e,j)=>e.classList.toggle('ativo',j===i));n.textContent=(i+1)+' / '+s.length;history.replaceState(null,'','#'+(i+1));}
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){go(i+1);e.preventDefault()}if(['ArrowLeft','PageUp'].includes(e.key)){go(i-1);e.preventDefault()}if(e.key==='Home')go(0);if(e.key==='End')go(s.length-1)});
addEventListener('click',e=>{go(e.clientX>innerWidth/3?i+1:i-1)});
go((parseInt(location.hash.slice(1))||1)-1);
"""
doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reprodutibilidade em treino de 3DGS — TCC</title><style>{CSS}</style></head>
<body>{''.join(S)}<div id="nav"></div><script>{JS}</script></body></html>"""
SAIDA.write_text(doc, encoding="utf-8")

print(f"escrito: {SAIDA}  ({len(S)} slides, {len(doc)//1024} KB)")
print(f"execucoes={n_exec}  horas_treino={horas:.1f}  H1={h1_dist}/{h1_total}  D4 hashes={h4_dist}/{h4_total}")
print(f"H2={h2_k}/{h2_n}={h2_frac:.1f}%  ampl_D0={ampl_d0:.4f}  red_psnr={red_psnr:.1f}x red_n={red_n:.0f}x")
print(f"Fligner D3xD4 p={fl_p:.4f} razao={razao:.4f} IC=[{ic_lo:.4f},{ic_hi:.4f}]  dPSNR={dq:.3f} dT={dt:.1f}%")
print(f"onset={onset}  eventos={n_eventos}  grupo identico D4={grupo5}")
