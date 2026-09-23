#!/usr/bin/env python3
"""
Medicao de magnitude dos gradientes e distribuicao de K — pre-registro §10.3.

Objetivo: fixar, com dado e nao por estimativa, as escalas por componente da
acumulacao em ponto fixo de D4. Produz o insumo do adendo do estagio 2.

NAO MODIFICA O FORK. Nenhuma linha de C++ ou Slang e tocada, e nenhum arquivo do
fork e alterado: a instrumentacao entra por substituicao da classe `VkSplat` no
namespace de `simple_trainer` em tempo de execucao. Isso preserva os SHAs de
`pre-registro.md` §3.1 e mantem a arvore do fork limpa.

POR QUE D3 E NAO D0
-------------------
D4 e cumulativo sobre D3. Com o escalonamento ativo (D0, D1) o numero de termos
somados por acumulador difere entre implementacoes — A=1 no `per_splat`, mas
A ∈ {8,16,32} nas outras (§10.4) — e o orcamento de estouro sairia errado. D3
tambem desliga o Morton, o que altera a permutacao e pode alterar K. As escalas
tem de vir do estado de codigo que D4 modifica.

PONTO DE LEITURA, E POR QUE ELE E VALIDO
----------------------------------------
Lemos os buffers imediatamente APOS `train_step`. Verificado no codigo em
2026-09-22, no commit da tag D3:

  1. `gs_renderer.cpp:323-325` — `clearDeviceBuffer` de `v_xy_vs`,
     `v_inv_cov_vs_opacity` e `v_rgb` acontece no INICIO de
     `executeRasterizeBackward`, isto e, no passo SEGUINTE. Os gradientes do
     passo corrente permanecem nos buffers depois que `train_step` retorna.
  2. `gs_trainer.cpp:685+` — `executeFusedProjectionBackwardOptimizerStep`
     recebe os tres buffers como bindings 5/6/7 e apenas os le.
  3. `slang/default.slang`, fase `updateState` — `v_xy_vs` e declarado
     `StructuredBuffer<float2>` (somente leitura); a escrita vai para
     `running_grad`, que e `RWStructuredBuffer`. O `COMPUTE_SHADER_READ_WRITE`
     em `gs_trainer.cpp:806` e barreira conservadora, nao escrita.

CUSTO
-----
`copyFromDevice` sincroniza o pipeline, o que e irrelevante para instrumentacao
mas nao e gratuito. Por isso so os steps da lista de amostragem sao lidos, nao
todos. Nenhuma estatistica exige guardar os arrays: eles sao reduzidos e
descartados.

USO
---
    python3 medir_gradientes_d4.py --fork ~/code/vksplatTCC/vksplat \\
        --out ~/tcc-runs/gradientes/rep00 --rep 0

Rodar 2 ou 3 repeticoes com --rep diferente. Num trabalho sobre nao-determinismo
assumir que o maximo de uma execucao e o maximo possivel seria autocontraditorio:
e a comparacao entre repeticoes que dimensiona a margem de seguranca.
"""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

# Steps amostrados. Cobrem: aquecimento; crescimento de `active_sh` de 0 a 3;
# o regime de densificacao; o fim da densificacao da ADC (perto de 15.000,
# conforme caderno de campo de 2026-09-02); e o regime final estabilizado.
STEPS_PADRAO = [0, 1, 10, 100, 500, 1000, 2000, 3000, 5000, 7500,
                10000, 12500, 15000, 20000, 25000, 29999]

# Os 9 componentes correspondem aos 9 sitios de `_ATOMIC_ADD` de
# `alphablend_shader_bwd_per_splat.slang`. Cada um recebera sua propria escala:
# as unidades diferem e uma escala unica seria grosseira para algum deles.
COMPONENTES = [
    ("v_xy_vs",                 2, ["xy_x", "xy_y"]),
    ("v_inv_cov_vs_opacity",    4, ["conic_0", "conic_1", "conic_2", "opacity"]),
    ("v_rgb",                   3, ["rgb_r", "rgb_g", "rgb_b"]),
]


def estatisticas(col: np.ndarray) -> dict:
    """Reduz uma coluna a estatisticas suficientes para dimensionar ponto fixo.

    Reporta minimo nao-nulo e maximo absoluto, nao media: sao os extremos que
    fixam bits fracionarios e risco de estouro (§10.3). Conta NaN e Inf
    separadamente — se houver, a escala e o menor dos problemas.
    """
    col = np.asarray(col, dtype=np.float64).ravel()
    n = col.size
    finito = np.isfinite(col)
    n_nan = int(np.isnan(col).sum())
    n_inf = int(np.isinf(col).sum())
    v = col[finito]
    a = np.abs(v)
    nz = a[a > 0.0]

    d = {
        "n": int(n),
        "n_nan": n_nan,
        "n_inf": n_inf,
        "n_zeros": int((a == 0.0).sum()),
        "frac_zeros": float((a == 0.0).sum() / n) if n else None,
        "min_signed": float(v.min()) if v.size else None,
        "max_signed": float(v.max()) if v.size else None,
        "max_abs": float(a.max()) if a.size else None,
        "min_abs_nonzero": float(nz.min()) if nz.size else None,
    }
    if a.size:
        for p in (50.0, 90.0, 99.0, 99.9, 99.99):
            d[f"p{p:g}_abs"] = float(np.percentile(a, p))
    return d


def medir(module, step: int) -> dict:
    """Le os tres buffers de gradiente mais tiles_touched e radii, e reduz."""
    reg = {"step": int(step), "componentes": {}}

    for atributo, ncomp, nomes in COMPONENTES:
        arr = np.asarray(getattr(module, atributo))
        # O binding expoe (N, ncomp) via DEF_BUFFER_ARRAY; se vier achatado,
        # reconstroi. Nao se assume o layout: verifica-se.
        if arr.ndim == 1:
            if arr.size % ncomp != 0:
                raise RuntimeError(
                    f"{atributo}: tamanho {arr.size} nao divisivel por {ncomp}")
            arr = arr.reshape(-1, ncomp)
        if arr.shape[1] != ncomp:
            raise RuntimeError(
                f"{atributo}: esperado {ncomp} componentes, veio {arr.shape[1]}")
        reg["num_splats_vistos"] = int(arr.shape[0])
        for j, nome in enumerate(nomes):
            reg["componentes"][nome] = estatisticas(arr[:, j])

    # K = tiles por gaussiana. Governa o orcamento de estouro: o acumulador
    # recebe da ordem de K*A termos, com A=1 no per_splat (§10.4). Nao ha limite
    # dedicado de tiles por gaussiana — K <= grid_width*grid_height.
    k = np.asarray(module.tiles_touched).ravel().astype(np.int64)
    reg["K"] = {
        "n": int(k.size),
        "min": int(k.min()) if k.size else None,
        "max": int(k.max()) if k.size else None,
        "sum": int(k.sum()) if k.size else None,
    }
    if k.size:
        for p in (50.0, 90.0, 99.0, 99.9, 99.99):
            reg["K"][f"p{p:g}"] = float(np.percentile(k, p))

    radii = np.asarray(module.radii).ravel().astype(np.int64)
    reg["radii"] = {
        "max": int(radii.max()) if radii.size else None,
        "p99.9": float(np.percentile(radii, 99.9)) if radii.size else None,
    }

    # Pior caso de acumulacao por componente: K_max * max|grad|. E cota superior
    # frouxa (assume que a gaussiana de maior K tambem tem o maior gradiente),
    # e e deliberadamente frouxa: para dimensionar escala, errar para o lado
    # conservador custa bits, errar para o outro custa saturacao silenciosa.
    if k.size:
        kmax = int(k.max())
        reg["pior_caso_acumulador"] = {
            nome: (st["max_abs"] * kmax if st["max_abs"] is not None else None)
            for nome, st in reg["componentes"].items()
        }
        reg["K_max_usado"] = kmax
    return reg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fork", required=True,
                    help="diretorio vksplat/ do fork, em checkout da tag D3")
    ap.add_argument("--out", required=True, help="diretorio de saida")
    ap.add_argument("--rep", type=int, default=0,
                    help="indice da repeticao, apenas para rotular a saida")
    ap.add_argument("--dataset", default="/home/fabio/360_v2/garden")
    ap.add_argument("--image-dir", default="images_4")
    ap.add_argument("--steps", default="",
                    help="lista de steps separada por virgula; vazio usa o padrao")
    args = ap.parse_args()

    fork = os.path.abspath(os.path.expanduser(args.fork))
    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, fork)

    steps = ([int(s) for s in args.steps.split(",") if s.strip()]
             if args.steps else list(STEPS_PADRAO))
    alvo = set(steps)

    # `simple_trainer` vive no fork, nao neste repositorio; o analisador estatico
    # nao o resolve, e isso e esperado.
    import simple_trainer as st  # type: ignore[import-not-found]  # noqa: E402

    # Confere que o fork esta na tag D3. O SHA de D3 vem de pre-registro.md
    # §3.1 e foi conferido contra os env.json das 120 execucoes em 2026-09-22.
    SHA_D3 = "d222c47182f5917be0cc209f19d3257e1ebad17e"

    def git(*a):
        return subprocess.run(["git", *a], capture_output=True, text=True,
                              cwd=fork).stdout.strip()

    sha = git("rev-parse", "HEAD")
    sujo = git("status", "--porcelain")
    if sha != SHA_D3:
        print(f"ABORTA: fork em {sha or '(desconhecido)'}, esperado D3 {SHA_D3}.",
              file=sys.stderr)
        print("        Rode: git -C <fork> checkout D3", file=sys.stderr)
        return 1
    if sujo:
        print("ABORTA: arvore do fork suja. A medicao tem de refletir o degrau.",
              file=sys.stderr)
        return 1

    # --- instrumentacao, sem tocar no fork --------------------------------
    # `simple_trainer` importa `vksplat` DENTRO da funcao (linha 118 em D3), nao
    # no topo do arquivo, e so entao faz `module = vksplat.VkSplat()` (linha 121)
    # e `module.train_step(image_idx, step)` no laco (linha 213). Portanto NAO
    # existe `st.vksplat`: uma tentativa anterior de patch por esse caminho
    # falhou com AttributeError em 2026-09-22.
    #
    # O que funciona: importar `vksplat` aqui e substituir o atributo no objeto
    # de modulo. O `import vksplat` interno de `simple_trainer` resolve por
    # `sys.modules` e recebe o MESMO objeto, ja com a substituicao aplicada.
    import vksplat  # type: ignore[import-not-found]

    registros = []
    contador = {"chamadas": 0, "medicoes": 0}

    def _envolver(chamada_original):
        def train_step(self, image_idx, step):
            r = chamada_original(self, image_idx, step)
            contador["chamadas"] += 1
            if step in alvo:
                registros.append(medir(self, step))
                contador["medicoes"] += 1
            return r
        return train_step

    # Duas estrategias, porque o comportamento de uma classe pybind11 quanto a
    # heranca e a setattr nao e garantido e nao pode ser verificado sem o modulo
    # compilado em maos. Tenta-se a menos invasiva primeiro.
    estrategia = None
    try:
        # (a) substituir o metodo na propria classe
        original = vksplat.VkSplat.train_step
        vksplat.VkSplat.train_step = _envolver(original)
        estrategia = "patch de metodo em VkSplat.train_step"
    except (AttributeError, TypeError) as e_metodo:
        try:
            # (b) subclasse com o metodo definido NO CORPO da classe, nao por
            # atribuicao posterior. Isto importa: se a classe base tiver uma
            # metaclass que recusa setattr, a subclasse herda essa metaclass e
            # `Sub.train_step = ...` falharia do mesmo modo que (a). Definir no
            # corpo insere no namespace antes de o tipo ser criado, e escapa
            # dessa restricao. Verificado em teste com stand-in em 2026-09-22.
            base = vksplat.VkSplat
            _orig_ts = base.train_step

            class VkSplatInstrumentado(base):  # type: ignore[misc, valid-type]
                def train_step(self, image_idx, step):
                    r = _orig_ts(self, image_idx, step)
                    contador["chamadas"] += 1
                    if step in alvo:
                        registros.append(medir(self, step))
                        contador["medicoes"] += 1
                    return r

            vksplat.VkSplat = VkSplatInstrumentado
            estrategia = "subclasse VkSplatInstrumentado"
        except (AttributeError, TypeError) as e_sub:
            print("ABORTA: nao foi possivel instrumentar `train_step`.",
                  file=sys.stderr)
            print(f"        patch de metodo: {e_metodo}", file=sys.stderr)
            print(f"        subclasse      : {e_sub}", file=sys.stderr)
            print("        Sem instrumentacao a medicao nao acontece; nao ha "
                  "fallback silencioso.", file=sys.stderr)
            return 3

    print(f"instrumentacao ativa via: {estrategia}")

    st.TRAIN_DEVICE = 0  # nunca -1: evita cair no llvmpipe (armadilha 1)

    cfg = st.TrainerConfig()  # ADC, identica a do tcc_runner.py
    cfg.dataset_dir = args.dataset
    cfg.image_dir = args.image_dir
    cfg.output_dir = os.path.join(out, "treino")

    meta = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "proposito": "pre-registro.md §10.3 — escalas de ponto fixo para D4",
        "rep": args.rep,
        "host": socket.gethostname(),
        "kernel": platform.release(),
        "python": sys.version,
        "vksplat_commit": sha,
        "vksplat_tag_esperada": "D3",
        "train_device": st.TRAIN_DEVICE,
        "dataset_dir": cfg.dataset_dir,
        "image_dir": cfg.image_dir,
        "train_steps": cfg.train_steps,
        "strategy": str(cfg.strategy),
        "steps_amostrados": steps,
        "ponto_de_leitura": "imediatamente apos train_step; buffers sao zerados "
                            "no inicio do executeRasterizeBackward seguinte",
    }

    st.train_main(cfg)

    # Falha alto se o patch nao pegou. Sem isto, um patch silenciosamente
    # ineficaz produziria um JSON vazio que pareceria resultado.
    if contador["chamadas"] == 0:
        print("ABORTA: train_step instrumentado nunca foi chamado — o patch da "
              "classe nao pegou. NAO use a saida.", file=sys.stderr)
        return 2
    faltando = sorted(alvo - {r["step"] for r in registros})
    if faltando:
        print(f"AVISO: steps sem medicao: {faltando}", file=sys.stderr)

    meta["train_step_chamadas"] = contador["chamadas"]
    meta["medicoes_feitas"] = contador["medicoes"]

    destino = os.path.join(out, f"gradientes_rep{args.rep:02d}.json")
    with open(destino, "w") as fp:
        json.dump({"meta": meta, "registros": registros}, fp, indent=2)

    print(f"\nescrito: {destino}")
    print(f"  chamadas a train_step : {contador['chamadas']}")
    print(f"  medicoes              : {contador['medicoes']}")
    print("\nmaximo absoluto por componente, sobre todos os steps amostrados:")
    if registros:
        nomes = list(registros[0]["componentes"].keys())
        for nome in nomes:
            vals = [r["componentes"][nome]["max_abs"] for r in registros
                    if r["componentes"][nome]["max_abs"] is not None]
            mins = [r["componentes"][nome]["min_abs_nonzero"] for r in registros
                    if r["componentes"][nome]["min_abs_nonzero"] is not None]
            if not vals:
                continue
            linha = f"  {nome:10s} max|.|={max(vals):.6e}"
            if mins:
                linha += f"  min nao-nulo={min(mins):.6e}"
                # faixa dinamica em bits: quantos bits separam o menor nao-nulo
                # do maior. E o numero que decide se int32 basta.
                import math
                bits = math.log2(max(vals) / min(mins)) if min(mins) > 0 else float("inf")
                linha += f"  faixa={bits:.1f} bits"
            print(linha)
        kmax = [r["K"]["max"] for r in registros if r["K"]["max"] is not None]
        if kmax:
            print(f"  K max = {max(kmax)}")
    nan_total = sum(s["n_nan"] for r in registros
                    for s in r["componentes"].values())
    inf_total = sum(s["n_inf"] for r in registros
                    for s in r["componentes"].values())
    if nan_total or inf_total:
        print(f"\nATENCAO: {nan_total} NaN e {inf_total} Inf observados. "
              "Investigar antes de fixar escalas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
