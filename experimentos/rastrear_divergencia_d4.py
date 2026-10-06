#!/usr/bin/env python3
"""
Onde e quando nasce a divergencia residual de D4.

CONTEXTO
--------
D4 (acumulacao inteira) tem 10 hashes de `splat.ply` distintos, mas as 10
execucoes coincidem nos 129 primeiros eventos de densificacao (passos 600 a
13.400) e ~99% das gaussianas diferem em valor no fim (dados/D4/
diagnostico_ply.json). Densificacao identica nao implica parametros
bit-identicos: o passo em que a divergencia comeca e desconhecido.

O QUE FAZ
---------
Modo `--executar`: treina D4 uma vez, com a configuracao do tcc_runner.py, e
depois de cada `train_step` amostrado grava o hash (BLAKE2b-128) dos bytes de
cada buffer exposto pelo binding, agrupados pelo estagio do pipeline que os
escreve (python_bindings.cpp:532-546 em D4: forward -> grad da perda ->
backward_optimize -> post_backward_step):

    projecao   xy_vs, depths, inv_cov_vs_opacity, rgb, radii, tiles_touched
    binning    rect_tile_space, tile_ranges, index_buffer_offset
    forward    pixel_state, n_contributors
    perda      ssim_map, v_pixel_state
    backward   v_xy_vs, v_inv_cov_vs_opacity, v_rgb  (inteiros em D4)
    parametros xyz_ws, sh_coeffs, rotations, scales, opacities  (apos otimizador
               e densificacao)

Modo `--comparar A.json B.json`: acha o primeiro passo amostrado em que alguma
coisa difere e, nesse passo, o primeiro estagio do pipeline que difere. Se a
perda e o forward coincidem e o backward nao, a fonte residual esta no
backward; e assim por diante.

AMOSTRAGEM, e por que evita multiplos de 100
--------------------------------------------
Densificacao (passo > 500, passo % 100 == 0, passo < 15000) e reset de
opacidade (multiplos de 3000) redimensionam buffers: ler a regiao nova pode
pegar memoria nao inicializada, que diferiria entre execucoes sem significado.
Amostras: passos 0..99; 105, 115, ..., 995; 1050, 1150, ..., 29950; e 29999.
Nenhum e multiplo de 100 exceto o 0, que nao densifica.

LIMITACOES, declaradas
----------------------
- Ler um buffer sincroniza a GPU (copyFromDevice). Nao altera a aritmetica,
  mas esta e uma execucao instrumentada, nao uma execucao da serie medida.
- A amostragem localiza a divergencia num INTERVALO entre amostras; se
  necessario, uma segunda rodada refina o intervalo.

NAO MODIFICA O FORK. Instrumenta por substituicao de `train_step` em tempo de
execucao, como medir_gradientes_d4.py. Aborta se o fork nao estiver em D4 limpo.

USO (na Ubuntu, venv ativo)
---------------------------
    git -C ~/code/vksplatTCC checkout D4
    python3 experimentos/rastrear_divergencia_d4.py --executar \\
        --fork ~/code/vksplatTCC/vksplat --out ~/tcc-runs/trajetoria/rep00 --rep 0
    python3 experimentos/rastrear_divergencia_d4.py --executar \\
        --fork ~/code/vksplatTCC/vksplat --out ~/tcc-runs/trajetoria/rep01 --rep 1
    python3 experimentos/rastrear_divergencia_d4.py --comparar \\
        ~/tcc-runs/trajetoria/rep00/trajetoria_rep00.json \\
        ~/tcc-runs/trajetoria/rep01/trajetoria_rep01.json
"""

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

SHA_D4 = "22560858b0f23586176ea3bf03907c607d8c944f"  # pre-registro.md §11.11

ESTAGIOS = [  # ordem de execucao dentro de train_step
    ("projecao", ["xy_vs", "depths", "inv_cov_vs_opacity", "rgb", "radii", "tiles_touched"]),
    ("binning", ["rect_tile_space", "tile_ranges", "index_buffer_offset"]),
    ("forward", ["pixel_state", "n_contributors"]),
    ("perda", ["ssim_map", "v_pixel_state"]),
    ("backward", ["v_xy_vs", "v_inv_cov_vs_opacity", "v_rgb"]),
    ("parametros", ["xyz_ws", "sh_coeffs", "rotations", "scales", "opacities"]),
]

# Modo denso (2026-10-06): TODO passo, conjunto leve. A rodada de 2026-10-05
# mostrou um par bit-identico em todos os 21 buffers ate o passo 14.050 e
# diferente em tudo no 14.150: a divergencia nasceu em algum passo de 14.051 a
# 14.149, e em um passo ela ja se espalha pelo pipeline inteiro. Como o inicio
# varia de par para par, adensar so aquela janela nao serve: e preciso amostrar
# todo passo. Estes buffers sao validos tambem nos passos de densificacao:
# pixel_state, n_contributors e v_pixel_state tem o tamanho da imagem, e
# xyz_ws e opacities sao parametros, totalmente escritos apos a densificacao.
# ~110 MB por passo no fim do treino.
ESTAGIOS_LEVE = [
    ("forward", ["pixel_state", "n_contributors"]),
    ("perda", ["v_pixel_state"]),
    ("parametros", ["xyz_ws", "opacities"]),
]


def passos_amostrados():
    s = list(range(0, 100)) + list(range(105, 1000, 10)) + list(range(1050, 30000, 100))
    s.append(29999)
    assert all(p == 0 or p % 100 != 0 for p in s)
    return s


def hash_buffer(module, nome):
    try:
        a = np.ascontiguousarray(getattr(module, nome))
    except Exception as e:  # buffer nao alocado ainda, ou acessor recusou
        return {"erro": f"{type(e).__name__}: {e}"[:200]}
    # Vista 1-D em bytes. Nao usar memoryview(a).cast("B"): falha com
    # "cannot cast view with zeros in shape" quando o buffer esta vazio, o que
    # aconteceu no passo 0 da primeira execucao real (2026-10-05). O shape vai
    # junto no registro, entao vazio x cheio continua aparecendo como diferenca.
    h = hashlib.blake2b(memoryview(a.reshape(-1).view(np.uint8)),  # type: ignore[arg-type]
                        digest_size=16).hexdigest()
    return {"h": h, "shape": list(a.shape), "dtype": str(a.dtype)}


def medir(module, step, estagios=ESTAGIOS):
    reg: dict = {"step": int(step)}
    for estagio, nomes in estagios:
        reg[estagio] = {n: hash_buffer(module, n) for n in nomes}
    return reg


def executar(args) -> int:
    fork = os.path.abspath(os.path.expanduser(args.fork))
    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, fork)

    def git(*a):
        return subprocess.run(["git", *a], capture_output=True, text=True,
                              cwd=fork).stdout.strip()

    sha = git("rev-parse", "HEAD")
    if sha != SHA_D4:
        print(f"ABORTA: fork em {sha[:10] or '?'}, esperado D4 {SHA_D4[:10]}. "
              f"Rode: git -C <fork> checkout D4", file=sys.stderr)
        return 1
    if git("status", "--porcelain", "--untracked-files=no"):
        print("ABORTA: arvore do fork suja.", file=sys.stderr)
        return 1

    import simple_trainer as st  # type: ignore[import-not-found]
    import vksplat  # type: ignore[import-not-found]
    # simple_trainer importa vksplat DENTRO da funcao (linha 118): o import
    # resolve por sys.modules e recebe este mesmo objeto ja instrumentado.

    if args.modo == "denso":
        alvo, estagios = set(range(0, 30000)), ESTAGIOS_LEVE
    else:
        alvo, estagios = set(passos_amostrados()), ESTAGIOS
    registros, contador = [], {"chamadas": 0}

    def _envolver(orig):
        def train_step(self, image_idx, step):
            r = orig(self, image_idx, step)
            contador["chamadas"] += 1
            if step in alvo:
                registros.append(medir(self, step, estagios))
            return r
        return train_step

    estrategia = None
    try:
        orig = vksplat.VkSplat.train_step
        vksplat.VkSplat.train_step = _envolver(orig)
        estrategia = "patch de metodo em VkSplat.train_step"
    except (AttributeError, TypeError) as e_metodo:
        try:
            base = vksplat.VkSplat
            _orig_ts = base.train_step

            class VkSplatInstrumentado(base):  # type: ignore[misc, valid-type]
                def train_step(self, image_idx, step):
                    r = _orig_ts(self, image_idx, step)
                    contador["chamadas"] += 1
                    if step in alvo:
                        registros.append(medir(self, step, estagios))
                    return r

            vksplat.VkSplat = VkSplatInstrumentado
            estrategia = "subclasse VkSplatInstrumentado"
        except (AttributeError, TypeError) as e_sub:
            print(f"ABORTA: instrumentacao falhou ({e_metodo} / {e_sub})", file=sys.stderr)
            return 3
    print(f"instrumentacao ativa via: {estrategia}", flush=True)

    st.TRAIN_DEVICE = 0
    cfg = st.TrainerConfig()                       # ADC, como tcc_runner.py
    cfg.dataset_dir = args.dataset
    cfg.image_dir = args.image_dir
    cfg.output_dir = os.path.join(out, "treino")
    meta = {
        "gerado_em_inicio": datetime.now(timezone.utc).isoformat(),
        "proposito": "localizar passo e estagio do inicio da divergencia residual de D4",
        "rep": args.rep, "host": socket.gethostname(), "kernel": platform.release(),
        "python": sys.version, "virtual_env": os.environ.get("VIRTUAL_ENV", ""),
        "vksplat_commit": sha, "train_device": st.TRAIN_DEVICE,
        "dataset_dir": cfg.dataset_dir, "image_dir": cfg.image_dir,
        "train_steps": cfg.train_steps, "estrategia_instrumentacao": estrategia,
        "modo": args.modo,
        "estagios": [[e, n] for e, n in estagios],
    }
    st.train_main(cfg)

    if contador["chamadas"] == 0:
        print("ABORTA: train_step instrumentado nunca chamado. NAO use a saida.",
              file=sys.stderr)
        return 2
    meta["train_step_chamadas"] = contador["chamadas"]
    meta["amostras"] = len(registros)
    meta["gerado_em_fim"] = datetime.now(timezone.utc).isoformat()
    sufixo = "_denso" if args.modo == "denso" else ""
    destino = os.path.join(out, f"trajetoria{sufixo}_rep{args.rep:02d}.json")
    with open(destino, "w") as fp:
        json.dump({"meta": meta, "registros": registros}, fp)
    print(f"escrito: {destino}  ({len(registros)} amostras, "
          f"{contador['chamadas']} chamadas)")
    return 0


def eh_densificacao(step):
    """Condicao lida em gs_trainer.cpp:829-830 e simple_trainer.py:42-44 (D4):
    step > refine_start_iter (500), step % refine_every (100) == 0,
    step < refine_stop_iter (15000)."""
    return 500 < step < 15000 and step % 100 == 0


def comparar(a_path, b_path) -> int:
    A, B = json.load(open(a_path)), json.load(open(b_path))
    for k in ("vksplat_commit", "train_steps", "dataset_dir", "image_dir"):
        if A["meta"][k] != B["meta"][k]:
            print(f"ABORTA: meta['{k}'] difere entre as execucoes", file=sys.stderr)
            return 1
    # estagios vem do proprio JSON (o modo denso grava um conjunto menor)
    est_a = [(e, list(n)) for e, n in A["meta"].get("estagios", ESTAGIOS)]
    est_b = [(e, list(n)) for e, n in B["meta"].get("estagios", ESTAGIOS)]
    if est_a != est_b:
        print("ABORTA: as duas execucoes gravaram conjuntos de buffers diferentes",
              file=sys.stderr)
        return 1
    estagios = est_a
    ra = {r["step"]: r for r in A["registros"]}
    rb = {r["step"]: r for r in B["registros"]}
    passos = sorted(set(ra) & set(rb))
    print(f"modo: {A['meta'].get('modo', 'completo')}  |  amostras em comum: "
          f"{len(passos)}  (A={len(ra)}, B={len(rb)})")

    ultimo_igual = None
    for p in passos:
        dif = []
        for estagio, nomes in estagios:
            for n in nomes:
                x, y = ra[p][estagio][n], rb[p][estagio][n]
                if "erro" in x or "erro" in y:
                    if x != y:
                        dif.append((estagio, n, "erro em uma das execucoes"))
                    continue
                if x["h"] != y["h"]:
                    dif.append((estagio, n, f"shape {x['shape']} vs {y['shape']}"
                                if x["shape"] != y["shape"] else "conteudo"))
        if not dif:
            ultimo_igual = p
            continue
        print(f"\nULTIMO passo amostrado com TUDO identico: {ultimo_igual}")
        print(f"PRIMEIRO passo amostrado com diferenca : {p}")
        print("  diferencas nesse passo, na ordem do pipeline:")
        for estagio, n, motivo in dif:
            print(f"    {estagio:11s} {n:22s} {motivo}")
        primeiro = dif[0][0]
        print(f"\n  primeiro estagio que difere: {primeiro}")
        ordem = [e for e, _ in estagios]
        anteriores = ordem[:ordem.index(primeiro)]
        if anteriores:
            print(f"  estagios anteriores, identicos nesse passo: {', '.join(anteriores)}")
        # contexto: a divergencia nasceu em algum passo de (ultimo_igual, p]
        if ultimo_igual is not None:
            janela = list(range(ultimo_igual + 1, p + 1))
            dens = [s for s in janela if eh_densificacao(s)]
            print(f"\n  a divergencia nasceu em algum passo de {janela[0]} a {janela[-1]} "
                  f"({len(janela)} passo(s))")
            print(f"  passos de densificacao nessa janela: {dens if dens else 'nenhum'}")
            if len(janela) == 1:
                print(f"  -> janela de 1 passo: o passo {p} e o de origem; "
                      f"densificacao nele: {'SIM' if eh_densificacao(p) else 'nao'}")
        # Salvaguarda contra falso positivo (caderno, 2026-10-06): uma diferenca
        # que aparece SO nos parametros so e aceita como divergencia real se a
        # imagem renderizada tambem divergir no passo seguinte.
        if primeiro == "parametros" and (p + 1) in ra and (p + 1) in rb \
                and "forward" in ordem:
            x = ra[p + 1]["forward"]["pixel_state"]
            y = rb[p + 1]["forward"]["pixel_state"]
            if "h" in x and "h" in y:
                prop = x["h"] != y["h"]
                print(f"\n  salvaguarda: pixel_state em {p + 1} "
                      f"{'TAMBEM difere -> divergencia real' if prop else 'NAO difere -> suspeita de falso positivo; investigar antes de concluir'}")
        return 0
    print(f"\nNENHUMA diferenca em {len(passos)} passos amostrados (ultimo: {ultimo_igual}).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--executar", action="store_true")
    g.add_argument("--comparar", nargs=2, metavar=("A.json", "B.json"))
    ap.add_argument("--fork")
    ap.add_argument("--out")
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--modo", choices=["completo", "denso"], default="completo",
                    help="completo: 481 passos, 21 buffers; denso: todo passo, 5 buffers")
    ap.add_argument("--dataset", default="/home/fabio/360_v2/garden")
    ap.add_argument("--image-dir", default="images_4")
    a = ap.parse_args()
    if a.comparar:
        return comparar(*a.comparar)
    if not (a.fork and a.out):
        ap.error("--executar exige --fork e --out")
    return executar(a)


if __name__ == "__main__":
    sys.exit(main())
