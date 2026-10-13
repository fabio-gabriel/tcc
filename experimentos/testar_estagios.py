#!/usr/bin/env python3
"""
Teste de determinismo POR ESTAGIO, em estado de parametros fixo.

PERGUNTA
--------
No par denso de D4 (dados/D4/trajetoria_denso_rep0{0,1}.json) tudo o que foi
monitorado coincide ate o passo 16.164, e a primeira diferenca aparece no
FORWARD do passo 16.165. O modo denso nao monitorava SH, escalas e rotacoes,
entao ha duas explicacoes compativeis:
  (a) o forward produz resultados diferentes a partir de entradas identicas;
  (b) algum parametro nao monitorado ja divergira antes.
Este teste decide (a) diretamente.

COMO
----
Em pontos escolhidos do treino, depois do `train_step`, com os parametros
congelados naquele estado, repete K vezes:
    forward()                      -> hash de pixel_state, n_contributors
    compute_pixel_loss_grad(img)   -> hash de v_pixel_state
    rasterize_backward()           -> hash de v_xy_vs, v_inv_cov_vs_opacity, v_rgb
Nenhuma dessas chamadas altera parametros nem os momentos do otimizador:
rasterize_backward so escreve nos v_* (que zera no inicio,
gs_renderer.cpp:323-325); o otimizador e outra chamada. Cada funcao abre o
proprio DEVICE_GUARD (gs_renderer.cpp:91,171,204,322; gs_trainer.cpp:649), e
DeviceGuard e aninhavel (gs_pipeline.h:207-240).
Se um buffer tiver mais de um hash distinto entre as K repeticoes, aquele
estagio e nao-deterministico a partir de entradas identicas.

CONTROLE POSITIVO, obrigatorio
------------------------------
Rodar tambem em D3. La o backward usa InterlockedAddF32 e os v_* TEM de variar
entre repeticoes. Se o teste disser "deterministico" tambem em D3, ele e
insensivel e o resultado em D4 nao vale nada.

PONTOS: 1050, 5050, 10050, 14050, 16050, 20050, 29950 — nenhum multiplo de 100
(evita passos de densificacao/reset) — com K=20. Ambos configuraveis por
--pontos e --k (padrao = esses valores).

LEITURA (corrigida em 2026-10-13, antes de qualquer execucao; caderno)
---------------------------------------------------------------------
- buffer com >1 hash distinto: evidencia DIRETA de nao-determinismo daquele
  estagio a partir de entradas identicas.
- tudo identico em K repeticoes: NAO refuta (a). Refuta apenas um estagio
  FREQUENTEMENTE nao-deterministico naquele estado. Com zero eventos em K
  tentativas, o limite superior de 95% da taxa por repeticao e
  1 - 0.05**(1/K) (~3/K), sob a premissa — nao verificada — de tentativas
  independentes com taxa constante. O script imprime esse limite.
- o par denso sugere taxa da ordem de 1 evento a cada ~3e4 passos; K=20
  nao tem poder para isso.

TEMPO: cada repeticao grava o tempo total e a divisao entre chamadas
(forward/perda/backward) e leitura+hash dos buffers. A divisao NAO separa
GPU de CPU: nao se verificou se o DeviceGuard espera a GPU ao sair, entao
parte do tempo de GPU pode cair na leitura (copyFromDevice espera a fence).
O JSON e regravado ao fim de cada ponto (campo "completo").

NAO MODIFICA O FORK. Instrumenta por patch de `train_step` (a estrategia que
funcionou nas rodadas de 2026-10-05/06).

USO (na Ubuntu, venv ativo)
---------------------------
    git -C ~/code/vksplatTCC checkout D4
    python3 experimentos/testar_estagios.py --degrau D4 \\
        --fork ~/code/vksplatTCC/vksplat --out ~/tcc-runs/estagios/D4
    git -C ~/code/vksplatTCC checkout D3
    python3 experimentos/testar_estagios.py --degrau D3 \\
        --fork ~/code/vksplatTCC/vksplat --out ~/tcc-runs/estagios/D3
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone

import numpy as np

SHA = {"D3": "d222c47182f5917be0cc209f19d3257e1ebad17e",   # pre-registro §3.1
       "D4": "22560858b0f23586176ea3bf03907c607d8c944f"}   # pre-registro §11.11
PONTOS = [1050, 5050, 10050, 14050, 16050, 20050, 29950]
K = 20
GRUPOS = [("forward", ["pixel_state", "n_contributors"]),
          ("perda", ["v_pixel_state"]),
          ("backward", ["v_xy_vs", "v_inv_cov_vs_opacity", "v_rgb"])]


def h(module, nome):
    a = np.ascontiguousarray(getattr(module, nome))
    return hashlib.blake2b(memoryview(a.reshape(-1).view(np.uint8)),  # type: ignore[arg-type]
                           digest_size=16).hexdigest()


def limite_sup_95(k):
    """Limite superior 95% da taxa por repeticao, com zero eventos em k tentativas."""
    return 1.0 - 0.05 ** (1.0 / k)


def repetir(module, image_idx, k=K):
    """K repeticoes forward -> perda -> backward sobre o MESMO estado, com tempo."""
    hashes = {n: [] for _, ns in GRUPOS for n in ns}
    chamadas = [module.forward,
                lambda: module.compute_pixel_loss_grad(image_idx),
                module.rasterize_backward]
    t_rep, t_cham, t_leit = [], [], []
    for _ in range(k):
        tc = tl = 0.0
        for chamar, (_, nomes) in zip(chamadas, GRUPOS):
            t0 = time.perf_counter()
            chamar()
            t1 = time.perf_counter()
            for n in nomes:
                hashes[n].append(h(module, n))
            t2 = time.perf_counter()
            tc += t1 - t0
            tl += t2 - t1
        t_rep.append(tc + tl)
        t_cham.append(tc)
        t_leit.append(tl)
    buffers = {}
    for n, v in hashes.items():
        mult = sorted(Counter(v).values(), reverse=True)
        buffers[n] = {"distintos": len(mult), "k": len(v), "multiplicidades": mult,
                      "limite_sup_95": limite_sup_95(len(v)) if len(mult) == 1 else None}
    r = lambda xs: [round(x, 4) for x in xs]  # noqa: E731
    tempo = {"rep_s": r(t_rep), "chamadas_s": r(t_cham), "leitura_hash_s": r(t_leit),
             "mediana_rep_s": round(float(np.median(t_rep)), 4) if t_rep else None}
    return buffers, tempo


def ler_pontos(texto):
    """'1050,5050' -> [1050, 5050]; rejeita vazio, repetido, negativo e multiplo de 100."""
    try:
        ps = [int(x) for x in texto.split(",") if x.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"pontos invalidos: {texto!r}")
    if not ps:
        raise argparse.ArgumentTypeError("lista de pontos vazia")
    if len(set(ps)) != len(ps):
        raise argparse.ArgumentTypeError(f"ponto repetido em {ps}")
    ruins = [p for p in ps if p < 0 or p % 100 == 0]
    if ruins:
        raise argparse.ArgumentTypeError(
            f"pontos negativos ou multiplos de 100 (densificacao/reset): {ruins}")
    return sorted(ps)


def ler_k(texto):
    k = int(texto)
    if k < 2:
        raise argparse.ArgumentTypeError("K precisa ser >= 2 para haver comparacao")
    return k


def gravar(destino, meta, resultados, completo):
    tmp = destino + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"meta": {**meta, "completo": completo}, "resultados": resultados}, f, indent=2)
    os.replace(tmp, destino)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--degrau", choices=sorted(SHA), required=True)
    ap.add_argument("--fork", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset", default="/home/fabio/360_v2/garden")
    ap.add_argument("--image-dir", default="images_4")
    ap.add_argument("--pontos", type=ler_pontos, default=PONTOS,
                    help="passos separados por virgula; padrao: %(default)s")
    ap.add_argument("--k", type=ler_k, default=K, help="repeticoes por ponto; padrao: %(default)s")
    a = ap.parse_args()
    pontos, k = a.pontos, a.k

    fork = os.path.abspath(os.path.expanduser(a.fork))
    out = os.path.abspath(os.path.expanduser(a.out))
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, fork)

    def git(*x):
        return subprocess.run(["git", *x], capture_output=True, text=True, cwd=fork).stdout.strip()

    sha = git("rev-parse", "HEAD")
    if sha != SHA[a.degrau]:
        print(f"ABORTA: fork em {sha[:10] or '?'}, esperado {a.degrau} {SHA[a.degrau][:10]}. "
              f"Rode: git -C <fork> checkout {a.degrau}", file=sys.stderr)
        return 1
    if git("status", "--porcelain", "--untracked-files=no"):
        print("ABORTA: arvore do fork suja.", file=sys.stderr)
        return 1

    import simple_trainer as st  # type: ignore[import-not-found]
    import vksplat  # type: ignore[import-not-found]

    destino = os.path.join(out, f"estagios_{a.degrau}.json")
    meta = {"inicio": datetime.now(timezone.utc).isoformat(),
            "proposito": "determinismo por estagio em estado fixo (forward/perda/backward)",
            "degrau": a.degrau, "vksplat_commit": sha, "kernel": platform.release(),
            "virtual_env": os.environ.get("VIRTUAL_ENV", ""), "pontos": pontos, "k": k,
            "instrumentacao": "patch de metodo em VkSplat.train_step"}
    alvo = set(pontos)
    resultados, contador = [], {"chamadas": 0}
    orig = vksplat.VkSplat.train_step

    def train_step(self, image_idx, step):
        r = orig(self, image_idx, step)
        contador["chamadas"] += 1
        if step in alvo:
            print(f"[estagios] passo {step}: {k} repeticoes ...", flush=True)
            t0 = time.perf_counter()
            buffers, tempo = repetir(self, image_idx, k)
            resultados.append({"step": step, "image_idx": int(image_idx),
                               "num_splats": int(len(self.opacities)),
                               "buffers": buffers, "tempo": tempo})
            gravar(destino, meta, resultados, completo=False)
            print(f"[estagios] passo {step}: {time.perf_counter() - t0:.1f} s, "
                  f"mediana {tempo['mediana_rep_s']} s/repeticao", flush=True)
        return r

    vksplat.VkSplat.train_step = train_step  # estrategia (a), confirmada em 2026-10-05

    st.TRAIN_DEVICE = 0
    cfg = st.TrainerConfig()
    cfg.dataset_dir, cfg.image_dir = a.dataset, a.image_dir
    cfg.output_dir = os.path.join(out, "treino")
    st.train_main(cfg)
    if contador["chamadas"] == 0 or len(resultados) != len(pontos):
        print(f"ABORTA: {len(resultados)} de {len(pontos)} pontos medidos "
              f"(parcial em {destino} se > 0).", file=sys.stderr)
        return 2
    meta["fim"] = datetime.now(timezone.utc).isoformat()
    gravar(destino, meta, resultados, completo=True)

    print(f"\n{a.degrau}: hashes distintos em {k} repeticoes sobre o MESMO estado "
          f"(1 = nenhuma diferenca observada)")
    nomes = [n for _, ns in GRUPOS for n in ns]
    print(f"{'passo':>6s} {'N':>9s} " + " ".join(f"{n[:14]:>14s}" for n in nomes)
          + f" {'s/rep':>7s}")
    for r in resultados:
        print(f"{r['step']:6d} {r['num_splats']:9d} " +
              " ".join(f"{r['buffers'][n]['distintos']:>14d}" for n in nomes)
              + f" {r['tempo']['mediana_rep_s']:>7.3f}")
    print(f"\nOnde 1: zero eventos em {k} repeticoes; limite superior 95% da taxa por "
          f"repeticao = {limite_sup_95(k):.3g} (premissa: independencia e taxa constante).")
    print("Isso NAO refuta um nao-determinismo raro. Ver docstring, LEITURA.")
    print(f"\nrelatorio: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
