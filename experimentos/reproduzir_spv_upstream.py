#!/usr/bin/env python3
"""
Teste T0 do adendo do estagio 2 — o `slangc` que vai compilar D4 reproduz, byte a
byte, os `.spv` que D0–D3 executaram?

POR QUE ESTE TESTE PRECEDE D4
-----------------------------
Os `.spv` executados em D0–D3 sao os do upstream, versionados em
`vksplat/shader/generated/` e intocados desde `b3ad2b0` (`git diff b3ad2b0 D3 --
'*.spv'` vazio). O `setup.py` nao compila shaders: o `.spv` versionado e o que
executa. Logo D4 tem de commitar `.spv` regenerados — e eles serao gerados pelo
NOSSO `slangc 2026.2.1`, nao pelo do upstream, cuja versao nao esta gravada (o
cabecalho SPIR-V traz generator 0x280000, tool 40 = Slang, versao 0).

Se o nosso compilador gerar bytes diferentes a partir das MESMAS fontes, D4
difere de D3 em duas coisas — a acumulacao e o compilador — e o custo do
determinismo (tempo, PSNR) fica confundido. H3.4 (bit-identidade dentro de D4)
nao e afetada, porque determinismo e propriedade do proprio degrau; a
comparacao D3 x D4, sim.

E nao e uma questao de 3 arquivos. O `compile_shaders.py` agrupa por fonte:
alterar `alphablend_shader_bwd_per_splat.slang` recompila as 6 saidas do grupo
`alphablend_shader.slang`, inclusive `rasterize_forward`; alterar
`default.slang` recompila as 9 fases do `default`. Sao 16 `.spv` regenerados
para 3 alteracoes semanticas.

O QUE O TESTE FAZ
-----------------
Com o fork em D3 e arvore limpa, recompila as fontes INALTERADAS de todos os
jobs Slang e compara sha256 com os `.spv` versionados. Nada e escrito no fork.

O comando replica exatamente `_compile_shader_slang` do `compile_shaders.py`:
    slangc vksplat/slang/<fonte> -D<k>=<v>... -target spirv \
           -stage compute -O -fp-mode fast -line-directive-mode none -o <saida>
executado a partir da raiz do fork. A lista de jobs e seus defines NAO e
copiada a mao: vem de `ShaderCompiler._create_shader_jobs()`, importado do
proprio `compile_shaders.py` de D3. O `compile_shaders.py` nao e usado para
compilar porque o `__init__` exige `glslc` (linha 82) mesmo para jobs Slang, e
porque o cache por checksum decide sozinho o que recompilar.

USO (na Ubuntu)
---------------
    git -C ~/code/vksplatTCC checkout D3
    python3 experimentos/reproduzir_spv_upstream.py \\
        --fork ~/code/vksplatTCC \\
        --slangc ~/opt/slang-2026.2.1/bin/slangc \\
        --out ~/tcc-runs/spv-repro

Saida: <out>/reproducao.json e resumo no terminal. Copiar o JSON para
`pivo-reprodutibilidade-3dgs/dados/toolchain/` — e dado de pesquisa (§7).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SHA_D3 = "d222c47182f5917be0cc209f19d3257e1ebad17e"  # pre-registro.md §3.1
VERSAO_SLANG = "2026.2.1"

# Grupos que D4 altera (pre-registro §10.2, corrigido pelo adendo §11).
GRUPOS_D4 = {"alphablend_shader.slang", "default.slang",
             "fused_projection_backward_optimizer.slang"}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def primeiro_byte_diferente(a: bytes, b: bytes):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fork", required=True, help="raiz do fork, em checkout de D3")
    ap.add_argument("--slangc", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    fork = Path(os.path.expanduser(args.fork)).resolve()
    slangc = Path(os.path.expanduser(args.slangc)).resolve()
    out = Path(os.path.expanduser(args.out)).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # --- pre-condicoes: cada uma e um modo de falha silencioso ---------------
    if os.environ.get("LD_LIBRARY_PATH"):
        # Documentado no "Getting Started" do Slang e registrado no caderno em
        # 2026-09-24: LD_LIBRARY_PATH sobrepoe o RUNPATH e pode carregar outra
        # libslang-compiler. Compilar com compilador diferente do declarado
        # invalidaria exatamente o que este teste mede.
        print("ABORTA: LD_LIBRARY_PATH definido. Rode com `env -u LD_LIBRARY_PATH`.",
              file=sys.stderr)
        return 1

    def git(*a):
        return subprocess.run(["git", *a], cwd=fork, capture_output=True,
                              text=True).stdout.strip()

    if git("rev-parse", "HEAD") != SHA_D3:
        print(f"ABORTA: fork nao esta em D3 ({SHA_D3[:10]}). "
              f"Rode: git -C {fork} checkout D3", file=sys.stderr)
        return 1
    if git("status", "--porcelain"):
        print("ABORTA: arvore do fork suja.", file=sys.stderr)
        return 1

    versao = subprocess.run([str(slangc), "-v"], capture_output=True,
                            text=True)
    versao_txt = (versao.stdout + versao.stderr).strip()
    if VERSAO_SLANG not in versao_txt:
        print(f"ABORTA: slangc reporta '{versao_txt}', esperado {VERSAO_SLANG}.",
              file=sys.stderr)
        return 1

    # --- lista de jobs, do proprio compile_shaders.py de D3 -------------------
    sys.dont_write_bytecode = True  # o import nao pode criar __pycache__ no fork
    sys.path.insert(0, str(fork))
    os.chdir(fork)  # CompileConfig usa caminhos relativos a raiz do fork
    import compile_shaders as cs  # type: ignore[import-not-found]

    comp = cs.ShaderCompiler.__new__(cs.ShaderCompiler)  # evita __init__ (glslc)
    comp.config = cs.CompileConfig()
    args_slangc = comp.config.slangc_compile_args.split()
    grupos = comp._create_shader_jobs()

    # diagnostico opcional, se o parser validado estiver ao lado
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from inspecionar_spirv import inspecionar  # type: ignore
    except Exception:
        inspecionar = None

    resultados = []
    with tempfile.TemporaryDirectory(prefix="spv-repro-") as tmp:
        tmp = Path(tmp)
        for fonte, jobs, _deps in grupos:
            if "." not in fonte:
                continue  # grupos GLSL (radix_sort): compilados por glslc, fora do escopo
            for job in jobs:
                saida = tmp / f"{job.name}.spv"
                cmd = [str(slangc), str(comp.config.slang_src_path / fonte)]
                cmd += [f"-D{k}={v}" for k, v in job.defines.items()]
                cmd += ["-target", "spirv", *args_slangc, "-o", str(saida)]
                p = subprocess.run(cmd, cwd=fork, capture_output=True, text=True)

                ref = comp.config.generated_dst_path / f"{job.name}.spv"
                reg = {
                    "grupo": fonte,
                    "job": job.name,
                    "grupo_alterado_por_D4": fonte in GRUPOS_D4,
                    "comando": cmd,
                    "returncode": p.returncode,
                    "stdout_stderr": (p.stdout + p.stderr).strip()[:2000],
                }
                if p.returncode != 0 or not saida.exists():
                    reg["status"] = "FALHOU_COMPILAR"
                elif not ref.exists():
                    reg["status"] = "SEM_REFERENCIA"
                else:
                    a, b = saida.read_bytes(), ref.read_bytes()
                    reg["sha256_nosso"] = hashlib.sha256(a).hexdigest()
                    reg["sha256_upstream"] = hashlib.sha256(b).hexdigest()
                    reg["bytes_nosso"], reg["bytes_upstream"] = len(a), len(b)
                    if a == b:
                        reg["status"] = "IDENTICO"
                    else:
                        reg["status"] = "DIFERENTE"
                        reg["primeiro_byte_diferente"] = primeiro_byte_diferente(a, b)
                        if inspecionar:
                            try:
                                ia, ib = inspecionar(str(saida)), inspecionar(str(ref))
                                reg["diag"] = {
                                    k: [ia[k], ib[k]] for k in
                                    ("instrucoes", "atomicos", "extensions")
                                }
                            except Exception as e:  # nao mascara o resultado principal
                                reg["diag_erro"] = str(e)
                resultados.append(reg)

    contagem = {}
    for r in resultados:
        contagem[r["status"]] = contagem.get(r["status"], 0) + 1
    d4 = [r for r in resultados if r["grupo_alterado_por_D4"]]
    d4_ident = sum(r["status"] == "IDENTICO" for r in d4)

    rel = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "proposito": "adendo estagio 2 (pre-registro §11), teste T0",
        "fork_commit": SHA_D3,
        "slangc": str(slangc),
        "slangc_versao": versao_txt,
        "args_slangc": args_slangc,
        "contagem": contagem,
        "grupos_D4": {"jobs": len(d4), "identicos": d4_ident},
        "resultados": resultados,
    }
    destino = out / "reproducao.json"
    destino.write_text(json.dumps(rel, indent=2, ensure_ascii=False))

    print(f"slangc: {versao_txt}")
    print(f"jobs Slang: {len(resultados)}  ->  {contagem}")
    print(f"grupos que D4 altera: {d4_ident}/{len(d4)} identicos ao upstream")
    for r in resultados:
        if r["status"] != "IDENTICO":
            print(f"  {r['status']:16s} {r['grupo']:44s} {r['job']}")
    veredito = ("REPRODUZ o upstream: o compilador NAO e fator de confusao"
                if contagem.get("IDENTICO", 0) == len(resultados)
                else "NAO reproduz integralmente: ver adendo §11.4, caminho B")
    print(f"\nVEREDITO T0: {veredito}")
    print(f"relatorio: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
