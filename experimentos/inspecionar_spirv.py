#!/usr/bin/env python3
"""
Inspeciona modulos SPIR-V binarios e reporta as instrucoes atomicas presentes.

MOTIVO DE EXISTIR
    O teste de §10.6 (`testar_slang_atomic.sh`) confirma que o `slangc` COMPILA
    `InterlockedAdd` inteiro sobre `RWByteAddressBuffer`. Mas compilar nao prova
    que a instrucao emitida e a pretendida: o compilador poderia, em principio,
    emitir uma emulacao por compare-and-swap (`OpAtomicCompareExchange` em laco)
    em vez de `OpAtomicIAdd` nativo. Essa distincao NAO e cosmetica para este
    trabalho — uma emulacao por CAS tem caracteristicas de contencao e de ordem
    diferentes, e o §10.6 pergunta especificamente pela instrucao.

    O caminho usual seria `spirv-dis`, do pacote `spirv-tools`. Este script evita
    essa dependencia de proposito: o ambiente da maquina de execucao foi
    congelado em 2026-09-21 (unattended-upgrades mascarado) e instalar pacote
    novo exigiria registrar alteracao de ambiente. SPIR-V e um formato de
    palavras de 32 bits com cabecalho fixo, e parsear os opcodes e trivial.

FORMATO, conforme a especificacao SPIR-V da Khronos (secao "Physical Layout")
    Cabecalho: 5 palavras de 32 bits
        [0] magic number 0x07230203
        [1] versao
        [2] generator magic
        [3] bound
        [4] schema
    Depois, instrucoes: a primeira palavra de cada uma codifica
        (wordCount << 16) | opcode
    de modo que o opcode sao os 16 bits baixos e o numero de palavras da
    instrucao (incluindo ela mesma) sao os 16 bits altos.

    O magic number tambem determina a ordem de bytes: se for lido invertido, o
    modulo esta em endianness oposta a do leitor.

Uso:
    python3 inspecionar_spirv.py arquivo.spv [outro.spv ...]
    python3 inspecionar_spirv.py ~/tcc-runs/slang-teste/*.spv
"""

import struct
import sys

MAGIC = 0x07230203

# Opcodes relevantes para este trabalho. Numeros da especificacao SPIR-V
# unificada. Os de atomico de ponto flutuante vem de SPV_EXT_shader_atomic_float.
OPCODES = {
    10:   "OpExtension",
    11:   "OpExtInstImport",
    17:   "OpCapability",
    227:  "OpAtomicLoad",
    228:  "OpAtomicStore",
    229:  "OpAtomicExchange",
    230:  "OpAtomicCompareExchange",
    231:  "OpAtomicCompareExchangeWeak",
    232:  "OpAtomicIIncrement",
    233:  "OpAtomicIDecrement",
    234:  "OpAtomicIAdd",
    235:  "OpAtomicISub",
    236:  "OpAtomicSMin",
    237:  "OpAtomicUMin",
    238:  "OpAtomicSMax",
    239:  "OpAtomicUMax",
    240:  "OpAtomicAnd",
    241:  "OpAtomicOr",
    242:  "OpAtomicXor",
    6035: "OpAtomicFAddEXT",
    6016: "OpAtomicFMinEXT",
    6017: "OpAtomicFMaxEXT",
}

ATOMICOS = {k for k in OPCODES if 227 <= k <= 242} | {6035, 6016, 6017}


def ler_palavras(caminho):
    """Le o modulo como lista de palavras de 32 bits, respeitando a endianness."""
    with open(caminho, "rb") as fp:
        dados = fp.read()
    if len(dados) < 20:
        raise ValueError(f"{caminho}: muito curto para ser SPIR-V ({len(dados)} bytes)")
    if len(dados) % 4 != 0:
        raise ValueError(f"{caminho}: tamanho {len(dados)} nao e multiplo de 4")

    primeira_le = struct.unpack("<I", dados[:4])[0]
    primeira_be = struct.unpack(">I", dados[:4])[0]
    if primeira_le == MAGIC:
        fmt = "<%dI" % (len(dados) // 4)
        ordem = "little"
    elif primeira_be == MAGIC:
        fmt = ">%dI" % (len(dados) // 4)
        ordem = "big"
    else:
        raise ValueError(
            f"{caminho}: magic number inesperado 0x{primeira_le:08x} — "
            "nao parece ser um modulo SPIR-V")
    return list(struct.unpack(fmt, dados)), ordem


def strings_de(palavras, inicio, fim):
    """Extrai a string terminada em NUL empacotada em palavras (OpExtension etc)."""
    bs = bytearray()
    for w in palavras[inicio:fim]:
        bs += struct.pack("<I", w)
    return bs.split(b"\x00")[0].decode("utf-8", "replace")


def inspecionar(caminho):
    palavras, ordem = ler_palavras(caminho)
    versao = palavras[1]
    maior, menor = (versao >> 16) & 0xFF, (versao >> 8) & 0xFF

    contagem = {}
    capabilities = []
    extensions = []

    i = 5  # pula o cabecalho
    total_instr = 0
    while i < len(palavras):
        palavra = palavras[i]
        word_count = palavra >> 16
        opcode = palavra & 0xFFFF
        if word_count == 0:
            # Instrucao malformada: sem isto o laco nao avancaria e travaria.
            raise ValueError(f"{caminho}: wordCount=0 na palavra {i}; modulo corrompido")
        nome = OPCODES.get(opcode, f"Op#{opcode}")
        if opcode in ATOMICOS:
            contagem[nome] = contagem.get(nome, 0) + 1
        elif opcode == 17 and word_count >= 2:
            capabilities.append(palavras[i + 1])
        elif opcode == 10:
            extensions.append(strings_de(palavras, i + 1, i + word_count))
        total_instr += 1
        i += word_count

    return {
        "arquivo": caminho,
        "ordem_bytes": ordem,
        "versao_spirv": f"{maior}.{menor}",
        "palavras": len(palavras),
        "instrucoes": total_instr,
        "atomicos": contagem,
        "capabilities_ids": capabilities,
        "extensions": extensions,
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 64

    resultados = []
    erros = 0
    for caminho in argv[1:]:
        try:
            resultados.append(inspecionar(caminho))
        except (OSError, ValueError) as e:
            print(f"ERRO: {e}", file=sys.stderr)
            erros += 1

    for r in resultados:
        print(f"--- {r['arquivo']} ---")
        print(f"  SPIR-V {r['versao_spirv']}  ordem={r['ordem_bytes']}  "
              f"{r['palavras']} palavras  {r['instrucoes']} instrucoes")
        if r["extensions"]:
            print(f"  OpExtension: {', '.join(r['extensions'])}")
        if r["atomicos"]:
            for nome, n in sorted(r["atomicos"].items()):
                print(f"  {nome}: {n}")
        else:
            print("  nenhuma instrucao atomica encontrada")
        print()

    # Veredito para o §10.6. A pergunta e binaria: OpAtomicIAdd nativo, ou
    # emulacao por compare-and-swap?
    print("=== veredito §10.6 ===")
    for r in resultados:
        nome = r["arquivo"].split("/")[-1]
        iadd = r["atomicos"].get("OpAtomicIAdd", 0)
        cas = (r["atomicos"].get("OpAtomicCompareExchange", 0)
               + r["atomicos"].get("OpAtomicCompareExchangeWeak", 0))
        fadd = r["atomicos"].get("OpAtomicFAddEXT", 0)
        if iadd and not cas:
            v = f"OpAtomicIAdd NATIVO x{iadd}"
        elif iadd and cas:
            v = f"OpAtomicIAdd x{iadd} MAIS compare-exchange x{cas} — investigar"
        elif cas:
            v = f"EMULADO por compare-exchange x{cas}, sem OpAtomicIAdd"
        elif fadd:
            v = f"atomico de PONTO FLUTUANTE x{fadd} (controle, esperado em v6)"
        else:
            v = "nenhum atomico — inesperado"
        print(f"  {nome:26s} {v}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
