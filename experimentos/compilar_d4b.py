#!/usr/bin/env python3
"""
Compila os shaders de D4b e executa V2, V3, V4 e V5 do adendo §11.12
(pre-registro.md §11.12.5), ANTES de qualquer commit e de qualquer execucao
medida. Derivado de compilar_d4.py, que fez o mesmo para D4.

NAO COMMITA. Nao roda treino. Escreve apenas os `.spv` dos jobs afetados em
`vksplat/shader/generated/` do fork e um relatorio em --out.

PRE-REQUISITO
-------------
Fork em D4 (`tcc-base` = D4, 22560858...), com o patch de D4b aplicado na
arvore de trabalho:

    cd ~/code/vksplatTCC
    git checkout tcc-base            # deve estar em 22560858b0...
    git apply ~/code/tcc/experimentos/d4b/d4b.patch

O QUE FAZ
---------
1. Recusa rodar se o estado do fork nao for exatamente "D4 + fontes de D4b"
   (2 `.slang`: d4_fixed_point.slang e alphablend_shader_bwd_per_splat.slang).
2. Recompila os 16 jobs dos 3 grupos que incluem d4_fixed_point.slang, com o
   comando exato de compile_shaders.py (o de T0, §11.5, e de compilar_d4.py).
3. V2 — conjunto alterado contra D4 = EXATAMENTE os 2 `.slang` e 2 `.spv`
   (rasterize_backward_1, fused_projection_backward_optimizer). Previsto:
   default_update_state.spv BIT-IDENTICO a D4. Qualquer `.spv` a mais e defeito.
4. V3 — rasterize_backward_1.spv: OpAtomicIAdd x9, OpAtomicFAddEXT x0, sem
   SPV_EXT_shader_atomic_float_add; Round/RoundEven, FClamp/NClamp e
   OpConvertFToS com a MESMA contagem de D4 (a quantizacao muda de constantes,
   nao de estrutura).
5. V4 — fused_projection_backward_optimizer.spv: atomicos e OpConvertSToF com a
   mesma contagem de D4.
6. V5 — constantes float de 32 bits (OpConstant): o produtor contem 2^30 e
   +-262143.0 e NAO contem 2^18 nem 2^20; o otimizador contem 2^-30 e NAO
   contem 2^-18 nem 2^-20. Verificado em 2026-10-15 nos .spv versionados: essas
   constantes NAO existem em D3 e sao introduzidas por D4 (produtor: 2^18, 2^20;
   otimizador: 2^-18, 2^-20), logo o criterio e inequivoco. O relatorio registra
   tambem o multiconjunto de constantes de D4 e de D4b, para diagnostico.

USO (na Ubuntu)
---------------
    env -u LD_LIBRARY_PATH python3 experimentos/compilar_d4b.py \\
        --fork ~/code/vksplatTCC \\
        --slangc ~/opt/slang-2026.2.1/bin/slangc \\
        --out ~/tcc-runs/d4b-build

Saida: codigo 0 so se V2..V5 passarem e nao houver aviso do compilador.
Relatorio em <out>/verificacao_d4b.json, a copiar para
pivo-reprodutibilidade-3dgs/dados/toolchain/.
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

SHA_D4 = "22560858b0f23586176ea3bf03907c607d8c944f"   # pre-registro §11.11
VERSAO_SLANG = "2026.2.1"
GRUPOS = ["alphablend_shader.slang", "default.slang",
          "fused_projection_backward_optimizer.slang"]
FONTES_MODIFICADAS = {
    "vksplat/slang/d4_fixed_point.slang",
    "vksplat/slang/alphablend_shader_bwd_per_splat.slang",
}
PRODUTOR = "vksplat/shader/generated/rasterize_backward_1.spv"
OTIMIZADOR = "vksplat/shader/generated/fused_projection_backward_optimizer.spv"
UPDATE_STATE = "vksplat/shader/generated/default_update_state.spv"
SPV_ALTERADOS = {PRODUTOR, OTIMIZADOR}
ESPERADO_V2 = FONTES_MODIFICADAS | SPV_ALTERADOS

# V5 (§11.12.5)
V5_PRODUTOR_TEM = {"2^30": 2.0 ** 30}
V5_PRODUTOR_TEM_UM_DE = {"+262143.0": 262143.0, "-262143.0": -262143.0}
V5_PRODUTOR_NAO_TEM = {"2^18": 2.0 ** 18, "2^20": 2.0 ** 20}
V5_OTIMIZADOR_TEM = {"2^-30": 2.0 ** -30}
V5_OTIMIZADOR_NAO_TEM = {"2^-18": 2.0 ** -18, "2^-20": 2.0 ** -20}


def soma(c, nomes):
    return sum(c["glsl"].get(n, 0) for n in nomes)


def verificar_v3(d4, d4b):
    itens = {
        "OpAtomicIAdd == 9": d4b["atomicos"].get("OpAtomicIAdd", 0) == 9,
        "OpAtomicFAddEXT == 0": d4b["atomicos"].get("OpAtomicFAddEXT", 0) == 0,
        "sem SPV_EXT_shader_atomic_float_add":
            "SPV_EXT_shader_atomic_float_add" not in d4b["extensions"],
        "Round/RoundEven igual a D4":
            soma(d4b, ["Round", "RoundEven"]) == soma(d4, ["Round", "RoundEven"]),
        "FClamp/NClamp igual a D4":
            soma(d4b, ["FClamp", "NClamp"]) == soma(d4, ["FClamp", "NClamp"]),
        "OpConvertFToS igual a D4": d4b["OpConvertFToS"] == d4["OpConvertFToS"],
        "atomicos iguais a D4": d4b["atomicos"] == d4["atomicos"],
    }
    return all(itens.values()), itens


def verificar_v4(d4, d4b):
    itens = {"atomicos iguais a D4": d4b["atomicos"] == d4["atomicos"],
             "OpConvertSToF igual a D4": d4b["OpConvertSToF"] == d4["OpConvertSToF"]}
    return all(itens.values()), itens


def verificar_v5(const_prod, const_otim):
    itens = {}
    for k, v in V5_PRODUTOR_TEM.items():
        itens[f"produtor contem {k}"] = v in const_prod
    itens["produtor contem +-262143.0"] = any(v in const_prod for v in V5_PRODUTOR_TEM_UM_DE.values())
    for k, v in V5_PRODUTOR_NAO_TEM.items():
        itens[f"produtor NAO contem {k}"] = v not in const_prod
    for k, v in V5_OTIMIZADOR_TEM.items():
        itens[f"otimizador contem {k}"] = v in const_otim
    for k, v in V5_OTIMIZADOR_NAO_TEM.items():
        itens[f"otimizador NAO contem {k}"] = v not in const_otim
    return all(itens.values()), itens


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
    from inspecionar_spirv import (ler_palavras, strings_de, constantes_float32,  # type: ignore
                                   OPCODES, ATOMICOS)
    from compilar_d4 import perfil  # type: ignore  # mesma contagem usada em D4

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
    if git("rev-parse", "HEAD").strip() != SHA_D4:
        erros.append("HEAD nao e D4: aplique o patch sobre tcc-base = D4, sem commitar")
    antes = {ln[3:].strip().strip('"')
             for ln in git("status", "--porcelain", "--untracked-files=all").splitlines()}
    if antes != FONTES_MODIFICADAS:
        erros.append("arvore do fork nao e exatamente 'D4 + fontes de D4b' antes da "
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
        if fonte not in GRUPOS:
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

    # --- 3. V2 --------------------------------------------------------------
    depois = {ln[3:].strip().strip('"')
              for ln in git("status", "--porcelain", "--untracked-files=all").splitlines()}
    v2_extra, v2_falta = sorted(depois - ESPERADO_V2), sorted(ESPERADO_V2 - depois)
    update_state_identico = UPDATE_STATE not in depois
    v2 = not v2_extra and not v2_falta and not falhas_comp and update_state_identico

    # --- 4..6. V3, V4, V5: D4b (arvore) contra D4 (git show) ----------------
    def palavras(caminho_rel, de_d4):
        if de_d4:
            with tempfile.NamedTemporaryFile(suffix=".spv", delete=False) as fp:
                fp.write(subprocess.run(["git", "show", f"D4:{caminho_rel}"],
                                        cwd=fork, capture_output=True).stdout)
                tmp = fp.name
            try:
                return ler_palavras(tmp)[0]
            finally:
                os.unlink(tmp)
        return ler_palavras(str(fork / caminho_rel))[0]

    rel = {}
    for s in (PRODUTOR, OTIMIZADOR):
        p4, p4b = palavras(s, True), palavras(s, False)
        rel[s] = {"D4": perfil(p4, strings_de, OPCODES, ATOMICOS),
                  "D4b": perfil(p4b, strings_de, OPCODES, ATOMICOS),
                  "constantes_D4": {repr(k): n for k, n in sorted(constantes_float32(p4).items())},
                  "constantes_D4b": {repr(k): n for k, n in sorted(constantes_float32(p4b).items())},
                  "sha256_D4b": hashlib.sha256((fork / s).read_bytes()).hexdigest()}
    v3, v3_itens = verificar_v3(rel[PRODUTOR]["D4"], rel[PRODUTOR]["D4b"])
    v4, v4_itens = verificar_v4(rel[OTIMIZADOR]["D4"], rel[OTIMIZADOR]["D4b"])
    v5, v5_itens = verificar_v5(constantes_float32(palavras(PRODUTOR, False)),
                                constantes_float32(palavras(OTIMIZADOR, False)))

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "proposito": "pre-registro §11.12.5 — verificacoes V2..V5 de D4b, antes do commit",
        "base": SHA_D4, "slangc": str(slangc), "slangc_versao": versao,
        "args_slangc": args_slangc, "compilados": compilados,
        "V2": {"ok": v2, "alterados": sorted(depois), "extra": v2_extra, "faltando": v2_falta,
               "default_update_state_bit_identico_a_D4": update_state_identico},
        "V3": {"ok": v3, "itens": v3_itens},
        "V4": {"ok": v4, "itens": v4_itens},
        "V5": {"ok": v5, "itens": v5_itens},
        "perfis": rel,
    }
    (out / "verificacao_d4b.json").write_text(json.dumps(relatorio, indent=2, ensure_ascii=False))

    print(f"slangc: {versao}")
    print(f"compilados: {len(compilados)} jobs, {len(falhas_comp)} falhas, "
          f"{len(avisos)} com saida (avisos)")
    for c in avisos:
        print(f"  AVISO em {c['job']}: {c['saida'][:300]}")
    print(f"\nV2 {'OK ' if v2 else 'FALHOU'}  conjunto alterado vs D4 "
          f"(default_update_state bit-identico: {update_state_identico})")
    for x in v2_extra:
        print(f"     a mais : {x}")
    for x in v2_falta:
        print(f"     faltando: {x}")
    for nome, ok, itens in (("V3", v3, v3_itens), ("V4", v4, v4_itens), ("V5", v5, v5_itens)):
        print(f"{nome} {'OK ' if ok else 'FALHOU'}")
        for k, b in itens.items():
            print(f"     [{'x' if b else ' '}] {k}")
    tudo = v2 and v3 and v4 and v5 and not avisos
    print("\nVEREDITO:", "PRONTO PARA COMMIT DE D4b" if tudo else
          "NAO commitar: ver itens acima" + (" (ha avisos do compilador)" if avisos else ""))
    print(f"relatorio: {out / 'verificacao_d4b.json'}")
    return 0 if tudo else 2


if __name__ == "__main__":
    sys.exit(main())
