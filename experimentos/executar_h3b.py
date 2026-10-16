#!/usr/bin/env python3
"""
Executor de UMA execucao de H3b (pre-registro §6 e §11.14). Espelha
`vksplat/tcc_runner.py` de D4b -- mesma configuracao, mesmo env.json, mesmo
diretorio de saida -- e acrescenta UMA alteracao: antes do primeiro
`train_step`, inverte o bit menos significativo da mantissa da coordenada x de
UMA gaussiana inicial.

NAO MODIFICA O FORK. A perturbacao entra pelo setter do binding `_set_xyz_ws`
(DEF_ARRAY, python_bindings.cpp:593-596): `array_to_buffer` (:76-83) grava o
buffer do host e chama `copyToDevice` (buffer.cpp:312-337), que abre o proprio
DEVICE_GUARD sem timer antes dele -- valido fora de lote, verificado no codigo
em 2026-10-16. As gaussianas sao inicializadas em `set_train_config`
(python_bindings.cpp:216), ANTES do laco de treino; as escalas iniciais, que
dependem das posicoes, ja estao calculadas e NAO mudam: a perturbacao e de
exatamente um bit numa condicao inicial.

ESCOLHA DO BIT, fixada no §11.14 antes de qualquer execucao:
  rng = default_rng(20261016); ordem = rng.permutation(N_inicial);
  validas = gaussianas, nessa ordem, cuja x e finita e normal (|x| >= menor
  normal de float32); a execucao k usa a k-esima valida; inverte o bit 0
  (u32 ^= 1) de x, isto e, x passa a seu vizinho em 1 ULP.

VERIFICACOES DENTRO DA EXECUCAO (aborta se falhar):
  - releitura do buffer depois do setter: exatamente UM uint32 difere do
    estado anterior, e e o (g, x) escolhido, com o valor perturbado;
  - o SHA-256 dos bytes de xyz ANTES da perturbacao e gravado no env.json:
    tem de ser o MESMO nas N execucoes (inicializacao deterministica).

USO (chamado por run_h3b.sh, com cwd no diretorio vksplat/ do fork):
    python -u executar_h3b.py <run_idx> <out_root> H3b --fork <fork>/vksplat
"""
import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys

import numpy as np

SEMENTE_H3B = 20261016
COORD = 0          # x
BIT = 0            # bit menos significativo da mantissa (float32)


def escolher(x, run_idx, semente=SEMENTE_H3B):
    """Indice da gaussiana perturbada na execucao run_idx (deterministico)."""
    ordem = np.random.default_rng(semente).permutation(len(x))
    tiny = np.finfo(np.float32).tiny
    k = -1
    for g in ordem:
        v = float(x[g, COORD])
        if np.isfinite(v) and abs(v) >= tiny:
            k += 1
            if k == run_idx:
                return int(g)
    raise RuntimeError(f"so {k + 1} gaussianas validas para run_idx={run_idx}")


def perturbar(module, run_idx, placebo=False):
    """Inverte um bit (ou, em placebo, nenhum), rele e verifica. Devolve o registro.

    PLACEBO (controle acrescentado em 2026-10-16, depois de ver H3b, §11.15):
    mesmo caminho -- getter, copia, setter, releitura --, mas SEM inverter o bit.
    Separa o efeito do bit do efeito de regravar o buffer pelo setter."""
    x0 = np.array(module.xyz_ws, dtype=np.float32, copy=True)
    if x0.ndim != 2 or x0.shape[1] != 3:
        raise RuntimeError(f"xyz_ws com forma inesperada {x0.shape}")
    sha0 = hashlib.sha256(np.ascontiguousarray(x0).tobytes()).hexdigest()
    g = escolher(x0, run_idx)
    x1 = x0.copy()
    u = x1.view(np.uint32)
    antes = int(u[g, COORD])
    if not placebo:
        u[g, COORD] ^= np.uint32(1 << BIT)
    module._set_xyz_ws(x1)
    x2 = np.array(module.xyz_ws, dtype=np.float32, copy=True)
    dif = np.argwhere(x2.view(np.uint32) != x0.view(np.uint32))
    if placebo:
        ok = x2.shape == x0.shape and len(dif) == 0
    else:
        ok = (x2.shape == x0.shape and len(dif) == 1 and tuple(dif[0]) == (g, COORD)
              and int(x2.view(np.uint32)[g, COORD]) == antes ^ (1 << BIT))
    reg = {"semente": SEMENTE_H3B, "run_idx": run_idx, "n_inicial": int(len(x0)),
           "placebo": bool(placebo), "gaussiana": g, "coordenada": "x",
           "bit": None if placebo else BIT,
           "valor_antes": float(x0[g, COORD]), "valor_depois": float(x2[g, COORD]),
           "bits_antes": f"0x{antes:08x}", "bits_depois": f"0x{int(x2.view(np.uint32)[g, COORD]):08x}",
           "sha256_xyz_inicial": sha0, "uint32_diferentes_apos_releitura": int(len(dif)),
           "verificado": bool(ok)}
    if not ok:
        raise RuntimeError(f"perturbacao NAO verificada: {reg}")
    return reg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_idx", type=int)
    ap.add_argument("out_root")
    ap.add_argument("degree")
    ap.add_argument("--fork", required=True, help="diretorio vksplat/ do fork")
    ap.add_argument("--placebo", action="store_true",
                    help="controle (§11.15): regrava o buffer pelo setter SEM inverter bit")
    a = ap.parse_args()
    if a.run_idx < 0:
        ap.error("run_idx >= 0")

    fork = os.path.abspath(os.path.expanduser(a.fork))
    sys.path.insert(0, fork)
    import simple_trainer as st  # type: ignore[import-not-found]
    import vksplat  # type: ignore[import-not-found]
    if not hasattr(vksplat.VkSplat, "_set_xyz_ws"):
        print("ABORTA: binding sem _set_xyz_ws", file=sys.stderr)
        return 1

    st.TRAIN_DEVICE = 0
    cfg = st.TrainerConfig()                         # ADC, como tcc_runner.py
    cfg.dataset_dir = "/home/fabio/360_v2/garden"
    cfg.image_dir = "images_4"
    cfg.output_dir = os.path.join(a.out_root, a.degree, f"run{a.run_idx:03d}")

    def git(*x):
        return subprocess.run(["git", *x], capture_output=True, text=True, cwd=fork).stdout.strip()

    os.makedirs(cfg.output_dir, exist_ok=True)
    env = {"run_idx": a.run_idx, "degree": a.degree,
           "host": socket.gethostname(), "kernel": platform.release(),
           "python": sys.version, "train_device": st.TRAIN_DEVICE,
           "vksplat_commit": git("rev-parse", "HEAD"),
           "vksplat_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
           "vksplat_dirty": git("status", "--porcelain"),
           "dataset_dir": cfg.dataset_dir, "image_dir": cfg.image_dir,
           "train_steps": cfg.train_steps, "strategy": cfg.strategy,
           "runner": "experimentos/executar_h3b.py" + (" --placebo" if a.placebo else ""), "h3b": None}
    env_path = os.path.join(cfg.output_dir, "env.json")

    def gravar_env():
        with open(env_path, "w") as fp:
            json.dump(env, fp, indent=2)

    gravar_env()
    orig = vksplat.VkSplat.train_step
    estado = {"feito": False}

    def train_step(self, image_idx, step):
        if not estado["feito"]:
            if step != 0:
                raise RuntimeError(f"primeiro train_step com step={step}, esperado 0")
            env["h3b"] = perturbar(self, a.run_idx, placebo=a.placebo)
            gravar_env()
            print(f"[h3b]{' PLACEBO' if a.placebo else ''} run {a.run_idx}: gaussiana {env['h3b']['gaussiana']} x "
                  f"{env['h3b']['valor_antes']!r} -> {env['h3b']['valor_depois']!r} "
                  f"({env['h3b']['bits_antes']} -> {env['h3b']['bits_depois']}), verificado", flush=True)
            estado["feito"] = True
        return orig(self, image_idx, step)

    vksplat.VkSplat.train_step = train_step
    st.train_main(cfg)
    if not estado["feito"]:
        print("ABORTA: train_step nunca foi chamado; nenhuma perturbacao aplicada", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
