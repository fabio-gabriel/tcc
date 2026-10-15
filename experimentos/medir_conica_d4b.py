#!/usr/bin/env python3
"""
Medicao DENSA do gradiente acumulado de conica (e opacidade) em D3, insumo do
adendo §11.12 (D4b). Caderno de campo, entrada de 2026-10-15.

POR QUE
-------
D4b troca a escala FIXA de conica de D4 (s = 18/18/20, que zera quase todo o
gradiente no regime) por escala POR FAIXA DE PASSOS. Os cortes e as escalas
tem de sair de dado. As 16 amostras de dados/gradientes/ nao bastam: entre os
passos 1.000 e 3.000 o maximo ainda chega a 257, so cai a partir de ~5.000, e
nenhuma amostra cai depois dos resets de opacidade de 6.000, 9.000 e 12.000.

O QUE MEDE
----------
Depois de cada `train_step` amostrado, le `v_inv_cov_vs_opacity` (N x 4:
conic_0, conic_1, conic_2, opacity) e reduz cada componente a:
  - max_abs e min_abs nao nulo, EXATOS;
  - contagem de zeros, NaN e Inf;
  - histograma de expoente base 2: hist_exp2[e] = #{ |g| em [2^(e-1), 2^e) }
    (np.frexp). Basta para avaliar, para QUALQUER escala s, quantos valores
    viram zero (|g| < 2^-(s+1)) e quantos estouram o acumulador
    (|g| >= 2^(31-s)), com resolucao de fator 2.
E o gradiente ACUMULADO por gaussiana, como em dados/gradientes/ e como a regra
de D4 (§11.2). Termos individuais NAO sao medidos — mesma limitacao de §11.9.

PONTO DE LEITURA (o mesmo de medir_gradientes_d4.py, verificado em 2026-09-22)
- os v_* so sao zerados no inicio do executeRasterizeBackward SEGUINTE
  (gs_renderer.cpp:323-325);
- o pos-backward le/escreve v_xy_vs, mas NAO toca v_inv_cov_vs_opacity
  (gs_trainer.cpp:806-818 em D4; mesmo arquivo em D3): os passos de
  densificacao sao validos para este buffer.

AMOSTRAGEM (`cronograma`)
- passos 0..99, todos (transiente inicial);
- a cada 10 passos ate o fim;
- todo passo de R a R+50 para R em 3000, 6000, 9000, 12000 — o reset de
  opacidade roda no pos-backward desses passos (gs_trainer.cpp:1027, so antes
  de refine_stop_iter=15000 por causa do return em :802), e o primeiro
  gradiente afetado e o de R+1;
- todo passo de 15000 a 15050 (fim da densificacao);
- o ultimo passo.

CUSTO: medir antes de estimar. `--custo` treina ate 10.500 e amostra 50 passos
de 10.010 a 10.500 (N ~ 5,2 M); imprime a mediana por amostra e a projecao
para o cronograma inteiro (cota superior: usa o custo de N grande em todas).

SAIDA
- <out>/conica_rep<RR>.ndjson: uma linha por amostra, gravada e descarregada
  na hora (aborto nao perde o que ja foi medido);
- <out>/conica_rep<RR>_meta.json: metadados, ambiente.json no inicio e no
  fim (mesmos pacotes de run_degree.sh), contagens, campo "completo".

NAO MODIFICA O FORK. Exige a tag D3, arvore limpa, e modulo recompilado a
partir dela: se o modulo carregado tiver os metodos *_guarded do patch de
diagnostico de estagios, ele foi compilado na branch estagios-* e aborta.

USO (na Ubuntu, venv ativo)
    cd ~/code/vksplatTCC && git checkout D3 && \\
      (cd vksplat && pip install -e . --no-build-isolation > ~/tcc-runs/conica/build.log 2>&1)
    cd ~/code/tcc
    python3 experimentos/medir_conica_d4b.py --fork ~/code/vksplatTCC/vksplat \\
        --out ~/tcc-runs/conica/custo --custo
    python3 experimentos/medir_conica_d4b.py --fork ~/code/vksplatTCC/vksplat \\
        --out ~/tcc-runs/conica --rep 0     # e --rep 1, --rep 2
"""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np

SHA_D3 = "d222c47182f5917be0cc209f19d3257e1ebad17e"   # pre-registro §3.1
BUFFER = "v_inv_cov_vs_opacity"
NOMES = ["conic_0", "conic_1", "conic_2", "opacity"]
RESETS = (3000, 6000, 9000, 12000)
FIM_DENSIFICACAO = 15000
JANELA = 50
METODOS_PATCH_ESTAGIOS = ("compute_pixel_loss_grad_guarded", "rasterize_backward_guarded")
PACOTES = ["mesa-vulkan-drivers", "libgl1-mesa-dri", "mesa-libgallium", "libegl-mesa0",
           "libglx-mesa0", "libvulkan1", "libdrm-amdgpu1", "libdrm2",
           "libc6", "python3.12", "libpython3.12t64"]           # = run_degree.sh:56-65
CUSTO_ATE = 10501        # train_steps: o ultimo passo executado e CUSTO_ATE - 1 = 10500
CUSTO_PASSOS = list(range(10010, CUSTO_ATE, 10))   # 10010..10500, 50 amostras
EXP_OFFSET = 160          # expoentes de float32 vao de -148 a 128


def cronograma(total):
    s = set(range(0, min(100, total)))
    s |= set(range(0, total, 10))
    for r in RESETS + (FIM_DENSIFICACAO,):
        s |= set(range(r, min(r + JANELA + 1, total)))
    if total > 0:
        s.add(total - 1)
    return sorted(s)


def reduzir(col):
    """Estatisticas suficientes de uma componente (1-D, pode ser vista nao contigua)."""
    a = np.abs(np.asarray(col, dtype=np.float32).reshape(-1))
    n = int(a.size)
    n_nan = int(np.isnan(a).sum())
    n_inf = int(np.isinf(a).sum())
    if n_nan or n_inf:
        a = a[np.isfinite(a)]
    zeros = int((a == 0).sum())
    nz = a[a > 0]
    d = {"n": n, "n_nan": n_nan, "n_inf": n_inf, "zeros": zeros,
         "max_abs": float(nz.max()) if nz.size else (0.0 if a.size else None),
         "min_abs_nz": float(nz.min()) if nz.size else None, "hist_exp2": {}}
    if nz.size:
        _, e = np.frexp(nz)                       # |g| = m * 2^e, m em [0.5, 1)
        c = np.bincount(e.astype(np.int64) + EXP_OFFSET)
        d["hist_exp2"] = {int(i - EXP_OFFSET): int(v) for i, v in enumerate(c) if v}
    return d


def medir(module, step):
    t0 = time.perf_counter()
    arr = np.asarray(getattr(module, BUFFER))
    t1 = time.perf_counter()
    if arr.ndim == 1:
        if arr.size % 4:
            raise RuntimeError(f"{BUFFER}: tamanho {arr.size} nao divisivel por 4")
        arr = arr.reshape(-1, 4)
    if arr.ndim != 2 or arr.shape[1] != 4:
        raise RuntimeError(f"{BUFFER}: esperado (N, 4), veio {arr.shape}")
    reg = {"step": int(step), "n": int(arr.shape[0]),
           "comp": {nome: reduzir(arr[:, j]) for j, nome in enumerate(NOMES)}}
    t2 = time.perf_counter()
    reg["t_leitura_s"] = round(t1 - t0, 4)
    reg["t_reducao_s"] = round(t2 - t1, 4)
    return reg


def ambiente():
    def sh(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            boot = f.read().strip()
    except OSError:
        boot = "INDISPONIVEL"
    vk = [ln.strip() for ln in sh(["vulkaninfo", "--summary"]).splitlines()
          if any(k in ln for k in ("driverName", "driverInfo", "driverID", "deviceName"))]
    return {"snapshot_em": datetime.now().astimezone().isoformat(), "kernel": platform.release(),
            "uname_a": " ".join(platform.uname()), "boot_id": boot,
            "pacotes": {p: (sh(["dpkg-query", "-W", "-f=${Version}", p]) or "AUSENTE") for p in PACOTES},
            "vulkan_driver": vk}


def gravar_meta(caminho, meta):
    tmp = caminho + ".tmp"
    with open(tmp, "w") as f:
        json.dump(meta, f, indent=2)
    os.replace(tmp, caminho)


def resumo(regs):
    """Maximo por componente em blocos de passos, para o planejamento das faixas."""
    blocos = [(0, 100), (100, 500), (500, 1000), (1000, 2000), (2000, 3000), (3000, 3051),
              (3051, 5000), (5000, 6000), (6000, 6051), (6051, 9000), (9000, 9051),
              (9051, 12000), (12000, 12051), (12051, 15000), (15000, 20000), (20000, 30000)]
    linhas = []
    for a, b in blocos:
        rs = [r for r in regs if a <= r["step"] < b]
        if rs:
            mx = {n: max((r["comp"][n]["max_abs"] or 0.0) for r in rs) for n in NOMES}
            linhas.append(f"  [{a:5d},{b:5d}) n={len(rs):4d}  " +
                          "  ".join(f"{n}={mx[n]:.3g}" for n in NOMES))
    return linhas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fork", required=True, help="diretorio vksplat/ do fork, na tag D3")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--custo", action="store_true",
                    help=f"so medir custo: treina ate o passo {CUSTO_ATE - 1}, 50 amostras tardias")
    ap.add_argument("--progresso", type=int, default=200, help="linha a cada N amostras (0 = nunca)")
    ap.add_argument("--dataset", default="/home/fabio/360_v2/garden")
    ap.add_argument("--image-dir", default="images_4")
    a = ap.parse_args()
    if a.rep < 0 or a.progresso < 0:
        ap.error("--rep e --progresso precisam ser >= 0")

    fork = os.path.abspath(os.path.expanduser(a.fork))
    out = os.path.abspath(os.path.expanduser(a.out))
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, fork)

    def git(*x):
        return subprocess.run(["git", *x], capture_output=True, text=True, cwd=fork).stdout.strip()

    sha = git("rev-parse", "HEAD")
    if sha != SHA_D3:
        print(f"ABORTA: fork em {sha[:10] or '?'}, esperado D3 {SHA_D3[:10]}. "
              f"Rode: git -C <fork> checkout D3 e recompile.", file=sys.stderr)
        return 1
    if git("status", "--porcelain", "--untracked-files=no"):
        print("ABORTA: arvore do fork suja.", file=sys.stderr)
        return 1

    import simple_trainer as st  # type: ignore[import-not-found]
    import vksplat  # type: ignore[import-not-found]

    if any(hasattr(vksplat.VkSplat, m) for m in METODOS_PATCH_ESTAGIOS):
        print(f"ABORTA: o modulo carregado ({getattr(vksplat, '__file__', '?')}) tem os metodos "
              f"do patch de estagios: foi compilado numa branch estagios-*, nao em D3. "
              f"Rode, no fork: (cd vksplat && pip install -e . --no-build-isolation)",
              file=sys.stderr)
        return 1

    total = CUSTO_ATE if a.custo else st.TrainerConfig().train_steps
    passos = CUSTO_PASSOS if a.custo else cronograma(total)
    alvo = set(passos)
    rotulo = "custo" if a.custo else f"rep{a.rep:02d}"
    nd_path = os.path.join(out, f"conica_{rotulo}.ndjson")
    meta_path = os.path.join(out, f"conica_{rotulo}_meta.json")
    if os.path.exists(nd_path):
        print(f"ABORTA: {nd_path} ja existe; nao sobrescrevo dados.", file=sys.stderr)
        return 1

    so = getattr(vksplat, "__file__", "")
    meta = {"gerado_em": datetime.now(timezone.utc).isoformat(),
            "proposito": "medicao densa de conica em D3 para o adendo §11.12 (D4b)",
            "modo": "custo" if a.custo else "completo", "rep": a.rep,
            "host": socket.gethostname(), "python": sys.version,
            "vksplat_commit": sha, "vksplat_tag_esperada": "D3",
            "modulo": so, "modulo_mtime": (datetime.fromtimestamp(os.path.getmtime(so), timezone.utc)
                                           .isoformat() if so and os.path.exists(so) else None),
            "buffer": BUFFER, "componentes": NOMES, "train_steps": total,
            "n_passos_amostrados": len(passos), "resets": list(RESETS), "janela": JANELA,
            "ponto_de_leitura": "imediatamente apos train_step",
            "instrumentacao": "patch de metodo em VkSplat.train_step",
            "ambiente_inicio": ambiente(), "completo": False}
    gravar_meta(meta_path, meta)

    contador = {"chamadas": 0, "amostras": 0}
    regs, tempos = [], []
    nd = open(nd_path, "w")
    t_ini = time.perf_counter()
    orig = vksplat.VkSplat.train_step

    def train_step(self, image_idx, step):
        r = orig(self, image_idx, step)
        contador["chamadas"] += 1
        if step in alvo:
            reg = medir(self, step)
            nd.write(json.dumps(reg) + "\n")
            nd.flush()
            regs.append({"step": reg["step"], "comp": {n: {"max_abs": reg["comp"][n]["max_abs"]}
                                                       for n in NOMES}})
            tempos.append(reg["t_leitura_s"] + reg["t_reducao_s"])
            contador["amostras"] += 1
            if a.progresso and contador["amostras"] % a.progresso == 0:
                print(f"[conica] {contador['amostras']}/{len(passos)} amostras, passo {step}, "
                      f"N {reg['n']}, mediana {np.median(tempos):.3f} s/amostra, "
                      f"{time.perf_counter() - t_ini:.0f} s", flush=True)
        return r

    vksplat.VkSplat.train_step = train_step
    st.TRAIN_DEVICE = 0
    cfg = st.TrainerConfig()
    cfg.dataset_dir, cfg.image_dir = a.dataset, a.image_dir
    cfg.output_dir = os.path.join(out, f"treino_{rotulo}")
    cfg.train_steps = total
    try:
        st.train_main(cfg)
    finally:
        nd.close()

    meta.update({"train_step_chamadas": contador["chamadas"], "amostras": contador["amostras"],
                 "fim": datetime.now(timezone.utc).isoformat(), "ambiente_fim": ambiente(),
                 "mediana_s_por_amostra": float(np.median(tempos)) if tempos else None})
    faltando = sorted(alvo - {r["step"] for r in regs})
    if contador["chamadas"] == 0 or faltando:
        meta["passos_faltando"] = faltando[:50]
        gravar_meta(meta_path, meta)
        print(f"ABORTA: {contador['amostras']} de {len(passos)} amostras "
              f"(parcial em {nd_path}).", file=sys.stderr)
        return 2
    meta["completo"] = True
    gravar_meta(meta_path, meta)

    med = float(np.median(tempos))
    print(f"\n{rotulo}: {contador['amostras']} amostras, mediana {med:.3f} s/amostra")
    if a.custo:
        n_full = len(cronograma(st.TrainerConfig().train_steps))
        print(f"projecao para o cronograma completo ({n_full} amostras): "
              f"<= {n_full * med / 60:.0f} min de amostragem por repeticao, mais o treino "
              f"(cota superior: custo de N ~ 5,2 M aplicado a todas)")
    print("maximo de |grad| acumulado por bloco de passos:")
    print("\n".join(resumo(regs)))
    ini, fim = meta["ambiente_inicio"], meta["ambiente_fim"]
    if (ini["boot_id"], ini["pacotes"]) != (fim["boot_id"], fim["pacotes"]):
        print("ATENCAO: ambiente mudou durante a execucao (boot_id ou pacotes).")
    print(f"\nsaida: {nd_path}\n       {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
