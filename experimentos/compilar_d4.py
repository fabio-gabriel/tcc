#!/usr/bin/env python3
"""
Compila os shaders de D4 e executa as verificacoes V2, V3 e V4 do adendo do
estagio 2 (pre-registro.md §11.6), ANTES de qualquer commit e de qualquer
execucao medida.

NAO COMMITA. Nao roda treino. Escreve apenas os `.spv` dos jobs afetados em
`vksplat/shader/generated/` do fork e um relatorio em --out.

PRE-REQUISITO
-------------
Fork em D3 (`tcc-base` = D3), com o patch de D4 aplicado na arvore de trabalho:

    cd ~/code/vksplatTCC
    git checkout tcc-base            # deve estar em d222c47182...
    git apply ~/code/tcc/experimentos/d4/d4.patch

O QUE FAZ
---------
1. Recusa rodar se o estado do fork nao for exatamente "D3 + fontes de D4".
2. Recompila os 16 jobs dos 3 grupos que D4 altera (`alphablend_shader.slang`,
   `default.slang`, `fused_projection_backward_optimizer.slang`) com o comando
   exato de `compile_shaders.py` — o mesmo validado pelo teste T0, que
   reproduziu 41/41 `.spv` do upstream byte a byte.
3. V2 — o conjunto de arquivos alterados em relacao a D3 tem de ser
   EXATAMENTE: 3 `.slang` modificados, `d4_fixed_point.slang` novo, e 3 `.spv`
   (`rasterize_backward_1`, `fused_projection_backward_optimizer`,
   `default_update_state`). Os outros 13 `.spv` regenerados tem de sair
   bit-identicos a D3. Qualquer `.spv` a mais e defeito a investigar.
4. V3 — `rasterize_backward_1.spv`: `OpAtomicIAdd` x9, zero `OpAtomicFAddEXT`,
   sem `SPV_EXT_shader_atomic_float_add`; e, contra D3, aumento de
   arredondamento (GLSL.std.450 Round/RoundEven), de clamp (FClamp/NClamp, ou
   o par min/max) e de `OpConvertFToS`.
5. V4 — nos dois consumidores: nenhum atomico novo em relacao a D3, e presenca
   de `OpConvertSToF` a mais (a desquantizacao).

NUMEROS DE INSTRUCAO — todos conferidos literalmente nas especificacoes em
2026-09-30, e nao de memoria:
  SPIR-V unificada, version 1.6, Revision 8:
    OpExtInstImport = 11, OpExtInst = 12 (palavras: tipo, id, set, instrucao, ...),
    OpConvertFToS = 110, OpConvertSToF = 111, OpAtomicIAdd = 234.
  GLSL.std.450, version 1.00, Revision 17:
    Round = 1, RoundEven = 2, FMin = 37, FMax = 40, FClamp = 43,
    NMin = 79, NMax = 80, NClamp = 81.

USO (na Ubuntu)
---------------
    env -u LD_LIBRARY_PATH python3 experimentos/compilar_d4.py \\
        --fork ~/code/vksplatTCC \\
        --slangc ~/opt/slang-2026.2.1/bin/slangc \\
        --out ~/tcc-runs/d4-build

Saida: codigo 0 so se V2, V3 e V4 passarem. Relatorio em <out>/verificacao_d4.json,
a copiar para pivo-reprodutibilidade-3dgs/dados/toolchain/.
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

SHA_D3 = "d222c47182f5917be0cc209f19d3257e1ebad17e"
VERSAO_SLANG = "2026.2.1"
GRUPOS_D4 = ["alphablend_shader.slang", "default.slang",
             "fused_projection_backward_optimizer.slang"]

FONTES_MODIFICADAS = {
    "vksplat/slang/alphablend_shader_bwd_per_splat.slang",
    "vksplat/slang/fused_projection_backward_optimizer.slang",
    "vksplat/slang/default.slang",
}
FONTE_NOVA = "vksplat/slang/d4_fixed_point.slang"
SPV_ALTERADOS = {
    "vksplat/shader/generated/rasterize_backward_1.spv",
    "vksplat/shader/generated/fused_projection_backward_optimizer.spv",
    "vksplat/shader/generated/default_update_state.spv",
}
ESPERADO_V2 = FONTES_MODIFICADAS | {FONTE_NOVA} | SPV_ALTERADOS

OP_EXTINSTIMPORT, OP_EXTINST = 11, 12
OP_CONVERT_F_TO_S, OP_CONVERT_S_TO_F = 110, 111
GLSL = {1: "Round", 2: "RoundEven", 37: "FMin", 40: "FMax", 43: "FClamp",
        79: "NMin", 80: "NMax", 81: "NClamp"}


def perfil(palavras, strings_de, ops_nomes, atomicos):
    """Conta instrucoes relevantes de um modulo ja lido como palavras."""
    glsl_set = set()
    # primeira passada: ids dos OpExtInstImport "GLSL.std.450"
    i = 5
    while i < len(palavras):
        wc, op = palavras[i] >> 16, palavras[i] & 0xFFFF
        if wc == 0:
            raise ValueError("wordCount=0: modulo corrompido")
        if op == OP_EXTINSTIMPORT and strings_de(palavras, i + 2, i + wc) == "GLSL.std.450":
            glsl_set.add(palavras[i + 1])
        i += wc
    cont = {"atomicos": {}, "glsl": {}, "OpConvertFToS": 0, "OpConvertSToF": 0,
            "extensions": []}
    i = 5
    while i < len(palavras):
        wc, op = palavras[i] >> 16, palavras[i] & 0xFFFF
        if op in atomicos:
            n = ops_nomes.get(op, f"Op#{op}")
            cont["atomicos"][n] = cont["atomicos"].get(n, 0) + 1
        elif op == OP_EXTINST and wc >= 5 and palavras[i + 3] in glsl_set:
            num = palavras[i + 4]
            if num in GLSL:
                cont["glsl"][GLSL[num]] = cont["glsl"].get(GLSL[num], 0) + 1
        elif op == OP_CONVERT_F_TO_S:
            cont["OpConvertFToS"] += 1
        elif op == OP_CONVERT_S_TO_F:
            cont["OpConvertSToF"] += 1
        elif op == 10:  # OpExtension
            cont["extensions"].append(strings_de(palavras, i + 1, i + wc))
        i += wc
    return cont


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fork", required=True)
    ap.add_argument("--slangc", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    fork = Path(os.path.expanduser(a.fork)).resolve()
    slangc = Path(os.path.expanduser(a.slangc)).resolve()
    out = Path(os.path.expanduser(a.out)).resolve()
    out.mkdir(parents=True, exist_ok=True)

    aqui = Path(__file__).resolve().parent
    sys.path.insert(0, str(aqui))
    from inspecionar_spirv import (ler_palavras, strings_de,  # type: ignore
                                   OPCODES, ATOMICOS)

    def git(*args, texto=True):
        return subprocess.run(["git", *args], cwd=fork, capture_output=True,
                              text=texto).stdout

    # --- 1. pre-condicoes ---------------------------------------------------
    erros = []
    if os.environ.get("LD_LIBRARY_PATH"):
        erros.append("LD_LIBRARY_PATH definido (use `env -u LD_LIBRARY_PATH`)")
    v = subprocess.run([str(slangc), "-v"], capture_output=True, text=True)
    versao = (v.stdout + v.stderr).strip()
    if VERSAO_SLANG not in versao:
        erros.append(f"slangc reporta '{versao}', esperado {VERSAO_SLANG}")
    if git("rev-parse", "HEAD").strip() != SHA_D3:
        erros.append("HEAD nao e D3: aplique o patch sobre tcc-base = D3, sem commitar")
    antes = set()
    for linha in git("status", "--porcelain", "--untracked-files=all").splitlines():
        antes.add(linha[3:].strip().strip('"'))
    if antes != FONTES_MODIFICADAS | {FONTE_NOVA}:
        erros.append("arvore do fork nao e exatamente 'D3 + fontes de D4' antes da "
                     f"compilacao. Encontrado: {sorted(antes)}")
    if erros:
        for e in erros:
            print("ABORTA:", e, file=sys.stderr)
        return 1

    # --- 2. compilacao dos 16 jobs, comando identico ao de T0 ----------------
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(fork))
    os.chdir(fork)
    import compile_shaders as cs  # type: ignore[import-not-found]
    comp = cs.ShaderCompiler.__new__(cs.ShaderCompiler)
    comp.config = cs.CompileConfig()
    args_slangc = comp.config.slangc_compile_args.split()

    compilados = []
    for fonte, jobs, _ in comp._create_shader_jobs():
        if fonte not in GRUPOS_D4:
            continue
        for job in jobs:
            destino = comp.config.generated_dst_path / f"{job.name}.spv"
            cmd = [str(slangc), str(comp.config.slang_src_path / fonte)]
            cmd += [f"-D{k}={v}" for k, v in job.defines.items()]
            cmd += ["-target", "spirv", *args_slangc, "-o", str(destino)]
            p = subprocess.run(cmd, cwd=fork, capture_output=True, text=True)
            msg = (p.stdout + p.stderr).strip()
            compilados.append({"job": job.name, "grupo": fonte,
                               "returncode": p.returncode, "saida": msg[:4000]})
            if p.returncode != 0:
                print(f"FALHA DE COMPILACAO em {job.name}:\n{msg}", file=sys.stderr)
    falhas_comp = [c for c in compilados if c["returncode"] != 0]
    avisos = [c for c in compilados if c["returncode"] == 0 and c["saida"]]

    # --- 3. V2: conjunto exato de arquivos alterados -------------------------
    depois = set()
    for linha in git("status", "--porcelain", "--untracked-files=all").splitlines():
        depois.add(linha[3:].strip().strip('"'))
    v2_extra = sorted(depois - ESPERADO_V2)
    v2_falta = sorted(ESPERADO_V2 - depois)
    v2 = not v2_extra and not v2_falta and not falhas_comp

    # --- 4 e 5. V3/V4: perfil de instrucoes, D4 contra D3 --------------------
    def perfil_de(caminho_rel, de_d3):
        if de_d3:
            with tempfile.NamedTemporaryFile(suffix=".spv", delete=False) as fp:
                fp.write(subprocess.run(["git", "show", f"D3:{caminho_rel}"],
                                        cwd=fork, capture_output=True).stdout)
                tmp = fp.name
            try:
                pal, _ = ler_palavras(tmp)
            finally:
                os.unlink(tmp)
        else:
            pal, _ = ler_palavras(str(fork / caminho_rel))
        return perfil(pal, strings_de, OPCODES, ATOMICOS)

    rel = {}
    for s in sorted(SPV_ALTERADOS):
        rel[s] = {"D3": perfil_de(s, True), "D4": perfil_de(s, False),
                  "sha256_D4": hashlib.sha256((fork / s).read_bytes()).hexdigest()}

    def soma(c, nomes):
        return sum(c["glsl"].get(n, 0) for n in nomes)

    r1 = rel["vksplat/shader/generated/rasterize_backward_1.spv"]
    d3, d4 = r1["D3"], r1["D4"]
    d_round = soma(d4, ["Round", "RoundEven"]) - soma(d3, ["Round", "RoundEven"])
    d_clamp = soma(d4, ["FClamp", "NClamp"]) - soma(d3, ["FClamp", "NClamp"])
    d_minmax = min(soma(d4, ["FMin", "NMin"]) - soma(d3, ["FMin", "NMin"]),
                   soma(d4, ["FMax", "NMax"]) - soma(d3, ["FMax", "NMax"]))
    d_cvt = d4["OpConvertFToS"] - d3["OpConvertFToS"]
    v3_itens = {
        "OpAtomicIAdd == 9": d4["atomicos"].get("OpAtomicIAdd", 0) == 9,
        "OpAtomicFAddEXT == 0": d4["atomicos"].get("OpAtomicFAddEXT", 0) == 0,
        "sem SPV_EXT_shader_atomic_float_add":
            "SPV_EXT_shader_atomic_float_add" not in d4["extensions"],
        "arredondamento aumentou (Round/RoundEven)": d_round >= 1,
        "clamp aumentou (FClamp/NClamp ou par min/max)": d_clamp >= 1 or d_minmax >= 1,
        "OpConvertFToS aumentou": d_cvt >= 1,
    }
    v3 = all(v3_itens.values())

    v4_itens = {}
    for s in ("vksplat/shader/generated/fused_projection_backward_optimizer.spv",
              "vksplat/shader/generated/default_update_state.spv"):
        a3, a4 = rel[s]["D3"], rel[s]["D4"]
        nome = Path(s).stem
        v4_itens[f"{nome}: atomicos inalterados"] = a3["atomicos"] == a4["atomicos"]
        v4_itens[f"{nome}: OpConvertSToF aumentou"] = \
            a4["OpConvertSToF"] > a3["OpConvertSToF"]
    v4 = all(v4_itens.values())

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "proposito": "pre-registro §11.6 — verificacoes V2/V3/V4 de D4, antes do commit",
        "base": SHA_D3, "slangc": str(slangc), "slangc_versao": versao,
        "args_slangc": args_slangc,
        "compilados": compilados,
        "V2": {"ok": v2, "alterados": sorted(depois), "extra": v2_extra,
               "faltando": v2_falta},
        "V3": {"ok": v3, "itens": v3_itens,
               "deltas": {"round": d_round, "clamp": d_clamp, "minmax": d_minmax,
                          "OpConvertFToS": d_cvt}},
        "V4": {"ok": v4, "itens": v4_itens},
        "perfis": rel,
    }
    (out / "verificacao_d4.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False))

    print(f"slangc: {versao}")
    print(f"compilados: {len(compilados)} jobs, {len(falhas_comp)} falhas, "
          f"{len(avisos)} com saida (avisos)")
    for c in avisos:
        print(f"  AVISO em {c['job']}: {c['saida'][:300]}")
    print(f"\nV2 {'OK ' if v2 else 'FALHOU'}  conjunto alterado vs D3")
    for x in v2_extra:
        print(f"     a mais : {x}")
    for x in v2_falta:
        print(f"     faltando: {x}")
    print(f"V3 {'OK ' if v3 else 'FALHOU'}  rasterize_backward_1.spv")
    for k, ok in v3_itens.items():
        print(f"     [{'x' if ok else ' '}] {k}")
    print(f"     deltas vs D3: round={d_round} clamp={d_clamp} minmax={d_minmax} "
          f"ConvertFToS={d_cvt}   (esperado ~9 em cada, um por sitio)")
    print(f"V4 {'OK ' if v4 else 'FALHOU'}  consumidores")
    for k, ok in v4_itens.items():
        print(f"     [{'x' if ok else ' '}] {k}")
    tudo = v2 and v3 and v4 and not avisos
    print("\nVEREDITO:", "PRONTO PARA COMMIT DE D4" if tudo else
          "NAO commitar: ver itens acima" + (" (ha avisos do compilador)" if avisos else ""))
    print(f"relatorio: {out / 'verificacao_d4.json'}")
    return 0 if tudo else 2


if __name__ == "__main__":
    sys.exit(main())
