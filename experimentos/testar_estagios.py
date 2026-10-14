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
    forward()                              -> hash de pixel_state, n_contributors
    compute_pixel_loss_grad_guarded(img)   -> hash de v_pixel_state
    rasterize_backward_guarded()           -> hash de v_xy_vs, v_inv_cov_vs_opacity, v_rgb
Nenhuma dessas chamadas altera parametros nem os momentos do otimizador:
rasterize_backward so escreve nos v_* (que zera no inicio,
gs_renderer.cpp:323-325); o otimizador e outra chamada.
Se um buffer tiver mais de um hash distinto entre as K repeticoes, aquele
estagio e nao-deterministico a partir de entradas identicas.

POR QUE OS METODOS *_guarded (2026-10-14; caderno)
--------------------------------------------------
A versao de 2026-10-13 chamava compute_pixel_loss_grad e rasterize_backward
direto. Eles NAO abrem lote de comandos no binding (python_bindings.cpp:455,
483), e criam o timer de desempenho ANTES do DEVICE_GUARD interno
(gs_trainer.cpp:647, gs_renderer.cpp:316). Com ENABLE_ASSERTION 0
(config.h:6), _THROW_ERROR e no-op: o timestamp e gravado fora de lote, se
perde, e endCommandBatch espera para sempre por ele (gs_pipeline.cpp:584-589).
A execucao de 2026-10-13/14 travou assim no passo 1050.
Correcao: patch SO NO BINDING, experimentos/patches/estagios_bindings.patch,
que acrescenta as duas versoes com DeviceGuard proprio (como forward()).
Nenhum .slang/.spv muda. Aplica-se igual em D3 e D4 (python_bindings.cpp e
identico nos dois). O script exige: HEAD^ == tag do degrau, diff HEAD^..HEAD
so em python_bindings.cpp e igual ao patch, e modulo recompilado com os
metodos novos. Confere antes de treinar.

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

CAPTURA DE EVENTOS (2026-10-14, antes de rodar; caderno)
--------------------------------------------------------
Referencia = repeticao 0 de cada ponto (hash e copia do array na RAM). Quando
o hash de um buffer diverge da referencia, o script rele IMEDIATAMENTE o mesmo
buffer da GPU, sem recalcular, e grava em <out>/evento_<degrau>_p<passo>_
rep<i>_<buffer>.npz os bits crus (uint32) dos elementos que diferem: idx, ref,
obs, releitura e shape. Leitura:
- releitura == observado: o conteudo NA GPU difere -> o calculo (ou a memoria
  da GPU depois dele) produziu outro valor;
- releitura == referencia: falha TRANSITORIA da leitura (GPU->staging->RAM->
  numpy->hash), nao do calculo;
- releitura == nenhum dos dois: instavel; nao classificado.
- padrao do diff: 1 elemento com popcount 1 sugere bit trocado (memoria);
  diferenca em poucos elementos, com magnitude de termo (em D4, inteiros em
  quanta), sugere termo diferente no calculo. Sugere, nao demonstra.
Se a repeticao 0 for a anomala, todas as seguintes divergem: o limite de
MAX_EVENTOS capturas por buffer protege o disco, e as multiplicidades finais
mostram qual hash era o majoritario.

TEMPO: cada repeticao grava o tempo total e a divisao entre chamadas
(forward/perda/backward) e leitura+hash dos buffers. Cada chamada abre e
fecha o proprio lote, e ~DeviceGuard -> endCommandBatch(true) espera a fence
(gs_pipeline.h:47,229; gs_pipeline.cpp:558), entao o tempo de "chamadas"
inclui a GPU. Ressalva: em train_step os tres estagios vao num lote so; aqui
cada um e submetido e sincronizado a parte. Nao muda a aritmetica, mas muda
a temporizacao.
O JSON e regravado ao fim de cada ponto (campo "completo").

Instrumenta por patch de `train_step` (a estrategia que funcionou nas
rodadas de 2026-10-05/06). O fork muda so pelo patch do binding.

USO (na Ubuntu, venv ativo), uma vez por degrau
-----------------------------------------------
    cd ~/code/vksplatTCC
    git checkout -b estagios-D4 D4
    git apply ~/code/tcc/experimentos/patches/estagios_bindings.patch
    git commit -qam "diagnostico de estagios: loss/backward com DeviceGuard (so binding)"
    (cd vksplat && pip install -e . --no-build-isolation > ~/tcc-runs/estagios/build-D4.log 2>&1)
    cd ~/code/tcc && python3 experimentos/testar_estagios.py --degrau D4 \\
        --fork ~/code/vksplatTCC/vksplat --out ~/tcc-runs/estagios/D4
  e o mesmo com D3 no lugar de D4.
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
PATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "patches", "estagios_bindings.patch")
ARQ_PATCH = "vksplat/src/python_bindings.cpp"
METODOS = ("compute_pixel_loss_grad_guarded", "rasterize_backward_guarded")
PONTOS = [1050, 5050, 10050, 14050, 16050, 20050, 29950]
K = 20
GRUPOS = [("forward", ["pixel_state", "n_contributors"]),
          ("perda", ["v_pixel_state"]),
          ("backward", ["v_xy_vs", "v_inv_cov_vs_opacity", "v_rgb"])]


def linhas_alteradas(diff_texto):
    """Linhas +/- de um diff unificado, sem cabecalhos de arquivo."""
    return [ln for ln in diff_texto.splitlines()
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]


MAX_EVENTOS = 10        # eventos capturados por buffer por ponto (os demais so contam)
MAX_IDX = 1_000_000     # elementos diferentes gravados por evento


def ler(module, nome):
    """Le o buffer da GPU. Cada acesso a propriedade faz copyFromDevice e devolve
    array novo (python_bindings.cpp:29-30, 585-588)."""
    return np.ascontiguousarray(getattr(module, nome))


def hash_arr(a):
    return hashlib.blake2b(memoryview(a.reshape(-1).view(np.uint8)),  # type: ignore[arg-type]
                           digest_size=16).hexdigest()


def h(module, nome):
    return hash_arr(ler(module, nome))


def bits(a):
    """Bits crus por elemento: uint32 se der (float32/int32 — em D4 os v_* sao
    expostos como float mas contem int32), senao uint8."""
    b = a.reshape(-1).view(np.uint8)
    return b.view(np.uint32) if b.size % 4 == 0 else b


def comparar_bits(ref, outro):
    """(resumo, idx) dos elementos que diferem; idx=None se os tamanhos diferem."""
    r, o = bits(ref), bits(outro)
    if r.size != o.size or r.dtype != o.dtype:
        return {"tamanhos_diferentes": [int(ref.nbytes), int(outro.nbytes)]}, None
    idx = np.flatnonzero(r != o)
    resumo = {"n_diferentes": int(idx.size), "n_elementos": int(r.size),
              "bytes_por_elemento": int(r.itemsize), "primeiros_idx": idx[:20].tolist()}
    if idx.size:
        x = (r[idx] ^ o[idx]).astype(r.dtype)
        pop = np.unpackbits(x.view(np.uint8)).reshape(idx.size, -1).sum(axis=1)
        resumo["popcount_xor"] = {int(k): int(v) for k, v in zip(*np.unique(pop, return_counts=True))}
    return resumo, idx[:MAX_IDX]


def capturar(module, nome, i, a, hs, ref_hash, ref_arr, prefixo):
    """Evento: hash da repeticao i != referencia. Rele o MESMO buffer da GPU sem
    recalcular e grava o diff. releitura == observado -> o conteudo na GPU difere
    (calculo); releitura == referencia -> falha transitoria de leitura."""
    t0 = time.perf_counter()
    b = ler(module, nome)
    hb = hash_arr(b)
    res_obs, idx = comparar_bits(ref_arr, a)
    res_rel, _ = comparar_bits(ref_arr, b)
    ev = {"rep": i, "buffer": nome, "dtype": str(a.dtype), "shape": list(a.shape),
          "hash_ref": ref_hash, "hash_obs": hs, "hash_releitura": hb,
          "releitura_igual_obs": hb == hs, "releitura_igual_ref": hb == ref_hash,
          "obs_vs_ref": res_obs, "releitura_vs_ref": res_rel, "arquivo": None}
    if prefixo and idx is not None:
        arq = f"{prefixo}_rep{i:05d}_{nome}.npz"
        np.savez_compressed(arq, idx=idx, ref=bits(ref_arr)[idx], obs=bits(a)[idx],
                            releitura=bits(b)[idx] if bits(b).size == bits(a).size else np.zeros(0),
                            shape=np.array(a.shape))
        ev["arquivo"] = os.path.basename(arq)
    ev["custo_s"] = round(time.perf_counter() - t0, 3)
    print(f"[estagios] EVENTO rep {i} {nome}: releitura == "
          f"{'OBSERVADO (conteudo na GPU difere)' if ev['releitura_igual_obs'] else 'REFERENCIA (leitura)' if ev['releitura_igual_ref'] else 'NENHUM'}; "
          f"{res_obs.get('n_diferentes', res_obs)} elementos diferentes; popcount {res_obs.get('popcount_xor')}",
          flush=True)
    return ev


def limite_sup_95(k):
    """Limite superior 95% da taxa por repeticao, com zero eventos em k tentativas."""
    return 1.0 - 0.05 ** (1.0 / k)


def repetir(module, image_idx, k=K, prefixo=None, progresso=0, rotulo=""):
    """K repeticoes forward -> perda -> backward sobre o MESMO estado, com tempo.

    Usa so metodos que abrem o proprio lote de comandos (ver docstring do modulo).
    Referencia = repeticao 0. Hash diferente dela dispara `capturar` (ate
    MAX_EVENTOS por buffer); custo extra so quando ha evento."""
    hashes = {n: [] for _, ns in GRUPOS for n in ns}
    chamadas = [module.forward,
                lambda: module.compute_pixel_loss_grad_guarded(image_idx),
                module.rasterize_backward_guarded]
    ref, eventos, n_ev = {}, [], Counter()
    t_rep, t_cham, t_leit = [], [], []
    t_ini = time.perf_counter()
    for i in range(k):
        tc = tl = 0.0
        for chamar, (_, nomes) in zip(chamadas, GRUPOS):
            t0 = time.perf_counter()
            chamar()
            t1 = time.perf_counter()
            for n in nomes:
                a = ler(module, n)
                hs = hash_arr(a)
                hashes[n].append(hs)
                if i == 0:
                    ref[n] = (hs, a.copy())
                elif hs != ref[n][0]:
                    n_ev[n] += 1
                    if n_ev[n] <= MAX_EVENTOS:
                        eventos.append(capturar(module, n, i, a, hs, ref[n][0], ref[n][1], prefixo))
            t2 = time.perf_counter()
            tc += t1 - t0
            tl += t2 - t1
        t_rep.append(tc + tl)
        t_cham.append(tc)
        t_leit.append(tl)
        if progresso and (i + 1) % progresso == 0 and i + 1 < k:
            print(f"[estagios] {rotulo}rep {i + 1}/{k}, {time.perf_counter() - t_ini:.0f} s, "
                  f"divergencias da ref: {dict(n_ev) or 0}", flush=True)
    buffers = {}
    for n, v in hashes.items():
        mult = sorted(Counter(v).values(), reverse=True)
        buffers[n] = {"distintos": len(mult), "k": len(v), "multiplicidades": mult,
                      "limite_sup_95": limite_sup_95(len(v)) if len(mult) == 1 else None,
                      "divergencias_da_ref": n_ev[n],
                      "eventos_capturados": min(n_ev[n], MAX_EVENTOS)}
    r = lambda xs: [round(x, 4) for x in xs]  # noqa: E731
    tempo = {"rep_s": r(t_rep), "chamadas_s": r(t_cham), "leitura_hash_s": r(t_leit),
             "mediana_rep_s": round(float(np.median(t_rep)), 4) if t_rep else None}
    return buffers, tempo, eventos


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
    ap.add_argument("--progresso", type=int, default=100,
                    help="linha de progresso a cada N repeticoes (0 = nunca); padrao: %(default)s")
    a = ap.parse_args()
    pontos, k = a.pontos, a.k
    if a.progresso < 0:
        ap.error("--progresso precisa ser >= 0")

    fork = os.path.abspath(os.path.expanduser(a.fork))
    out = os.path.abspath(os.path.expanduser(a.out))
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, fork)

    def git(*x):
        return subprocess.run(["git", *x], capture_output=True, text=True, cwd=fork).stdout.strip()

    base = SHA[a.degrau]
    sha, pai = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^")
    receita = (f"cd <repo do fork> && git checkout -b estagios-{a.degrau} {a.degrau} && "
               f"git apply {PATCH} && git commit -qam 'diagnostico de estagios' && "
               f"(cd vksplat && pip install -e . --no-build-isolation)")
    if sha == base:
        print(f"ABORTA: fork na tag {a.degrau} sem o patch do binding. Rode:\n  {receita}",
              file=sys.stderr)
        return 1
    if pai != base:
        print(f"ABORTA: HEAD^ = {pai[:10] or '?'}, esperado {a.degrau} {base[:10]}. "
              f"O commit de diagnostico tem de ser filho direto da tag. Rode:\n  {receita}",
              file=sys.stderr)
        return 1
    if git("status", "--porcelain", "--untracked-files=no"):
        print("ABORTA: arvore do fork suja.", file=sys.stderr)
        return 1
    alterados = git("diff", "--name-only", "HEAD^", "HEAD").splitlines()
    if alterados != [ARQ_PATCH]:
        print(f"ABORTA: o commit de diagnostico altera {alterados}; so pode alterar "
              f"[{ARQ_PATCH!r}].", file=sys.stderr)
        return 1
    with open(PATCH) as f:
        esperado = linhas_alteradas(f.read())
    if linhas_alteradas(git("diff", "HEAD^", "HEAD", "--", f":/{ARQ_PATCH}")) != esperado:
        print(f"ABORTA: o diff HEAD^..HEAD difere de {PATCH}.", file=sys.stderr)
        return 1

    import simple_trainer as st  # type: ignore[import-not-found]
    import vksplat  # type: ignore[import-not-found]

    faltam = [m for m in METODOS if not hasattr(vksplat.VkSplat, m)]
    if faltam:
        print(f"ABORTA: o modulo carregado ({getattr(vksplat, '__file__', '?')}) nao tem "
              f"{faltam}: nao foi recompilado depois do patch. Rode, no fork:\n"
              f"  (cd vksplat && pip install -e . --no-build-isolation)", file=sys.stderr)
        return 1

    with open(PATCH, "rb") as f:
        patch_sha256 = hashlib.sha256(f.read()).hexdigest()
    so = getattr(vksplat, "__file__", "")
    destino = os.path.join(out, f"estagios_{a.degrau}.json")
    meta = {"inicio": datetime.now(timezone.utc).isoformat(),
            "proposito": "determinismo por estagio em estado fixo (forward/perda/backward)",
            "degrau": a.degrau, "base_commit": base, "vksplat_commit": sha,
            "patch_binding_sha256": patch_sha256,
            "modulo": so, "modulo_mtime": (datetime.fromtimestamp(os.path.getmtime(so), timezone.utc)
                                           .isoformat() if so and os.path.exists(so) else None),
            "kernel": platform.release(),
            "virtual_env": os.environ.get("VIRTUAL_ENV", ""), "pontos": pontos, "k": k,
            "instrumentacao": "patch de metodo em VkSplat.train_step; estagios via *_guarded",
            "captura": {"referencia": "repeticao 0", "max_eventos_por_buffer": MAX_EVENTOS,
                        "max_idx_por_evento": MAX_IDX,
                        "releitura": "mesmo buffer relido da GPU sem recalcular"}}
    alvo = set(pontos)
    resultados, contador = [], {"chamadas": 0}
    orig = vksplat.VkSplat.train_step

    def train_step(self, image_idx, step):
        r = orig(self, image_idx, step)
        contador["chamadas"] += 1
        if step in alvo:
            print(f"[estagios] passo {step}: {k} repeticoes ...", flush=True)
            t0 = time.perf_counter()
            prefixo = os.path.join(out, f"evento_{a.degrau}_p{step}")
            buffers, tempo, eventos = repetir(self, image_idx, k, prefixo=prefixo,
                                              progresso=a.progresso, rotulo=f"passo {step}: ")
            resultados.append({"step": step, "image_idx": int(image_idx),
                               "num_splats": int(len(self.opacities)),
                               "buffers": buffers, "tempo": tempo, "eventos": eventos})
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
    evs = [(r["step"], e) for r in resultados for e in r["eventos"]]
    print(f"\nEventos capturados: {len(evs)}")
    for s, e in evs:
        o = e["obs_vs_ref"]
        print(f"  passo {s} rep {e['rep']} {e['buffer']}: releitura == "
              f"{'observado' if e['releitura_igual_obs'] else 'referencia' if e['releitura_igual_ref'] else 'nenhum'}; "
              f"{o.get('n_diferentes', o)} elementos; popcount {o.get('popcount_xor')}; {e['arquivo']}")
    print(f"\nrelatorio: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
