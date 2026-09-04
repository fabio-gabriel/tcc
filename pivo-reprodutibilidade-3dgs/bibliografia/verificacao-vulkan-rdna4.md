# Verificação de fatos Vulkan / RADV / RDNA 4

> **Nota de proveniência (2026-08-26).** Este arquivo foi levantado para a formulação *"MLP fundido em Vulkan compute com `VK_KHR_cooperative_matrix`"*, **abandonada no mesmo dia** (ver `PLANO.md` §6). É mantido porque (a) os fatos sobre RADV, wave size e atômicos continuam válidos e diretamente úteis ao tema atual — em especial §4 (wave size) e §9 (`VK_EXT_shader_atomic_float` em implementações reais); e (b) os achados categóricos de §2, §3 e §5 permanecem citáveis como observação sobre o ecossistema, independentemente do tema.
>
> **O que NÃO usar:** cooperative matrix como *objeto de estudo*. O objeto atual é reprodutibilidade de treino de 3DGS.
>
> **Fonte de verdade versionada** para os fatos técnicos verificados sobre o que a RDNA 4 (`gfx1201`) expõe, e o que uma API agnóstica de fornecedor alcança. Espelha a função de `../../bibliografia/verificacao-experimento-rdna4.md` no tema anterior.
>
> **Regra deste arquivo:** cada afirmação traz fonte e data de acesso. Afirmação não verificada é marcada `[NÃO VERIFICADO]` e não pode migrar para capítulo. Inferência própria é marcada `[INFERÊNCIA]` e distinguida de citação.
>
> Rodada 1: 2026-08-26.

---

## 1. A extensão

| Campo | Valor | Fonte |
|---|---|---|
| Nome | `VK_KHR_cooperative_matrix` | registry Khronos, acesso 2026-08-26 |
| Extension number | 507 | idem |
| Revision | 2 | idem; confirmação independente em `LWJGL/lwjgl3`, `KHRCooperativeMatrix.java` (`SPEC_VERSION = 2`) |
| Ratification status | **Ratified** | idem |
| Last Modified | **2023-05-03** | idem |
| Histórico | Rev. 1, 2019-02-05 (Jeff Bolz) — "NVIDIA vendor extension"; Rev. 2, 2023-05-03 (Kevin Petit) — "First KHR revision" | idem |
| Dependência SPIR-V | `SPV_KHR_cooperative_matrix`, capability `CooperativeMatrixKHR` | idem |
| Contribuidores | Bolz, Tavenrath, Koch (NVIDIA); Petit (Arm); **Zanin (AMD)** | idem |

URL: <https://registry.khronos.org/vulkan/specs/latest/man/html/VK_KHR_cooperative_matrix.html>

Descrição, citação literal: *"Cooperative matrix types are medium-sized matrices that are primarily supported in compute shaders, where the storage for the matrix is spread across all invocations in some scope (usually a subgroup) and those invocations cooperate to efficiently perform matrix multiplies."*

**`[NÃO VERIFICADO]`** A versão do Vulkan em que a extensão foi publicada. O valor `1.3.255` aparece apenas como comentário em código de terceiro (`mpv`, `video/out/vulkan/context.c`), não em fonte Khronos. Citar apenas a data de ratificação.

## 2. O que o RADV expõe em `gfx1201`

Fonte primária: código do **Mesa 25.2.8**, tarball oficial `archive.mesa3d.org/mesa-25.2.8.tar.xz`, acesso 2026-08-26. Esta é a versão instalada na máquina do experimento.

### 2.1 Condição de habilitação

`src/amd/vulkan/radv_physical_device.c:147-150`, citação literal:

```c
static bool radv_cooperative_matrix_enabled(const struct radv_physical_device *pdev)
{
   return pdev->info.gfx_level >= GFX11 && !pdev->use_llvm;
}
```

**Consequência operacional:** a extensão exige o backend **ACO**. Com `RADV_DEBUG=llvm` ela desaparece por completo. Registrar a variável de ambiente no pré-registro do protocolo.

`docs/features.txt:538`: `VK_KHR_cooperative_matrix    DONE (anv, radv/gfx11+)` — nenhum outro driver Mesa a implementa nesta versão.

### 2.2 Uma única forma

`radv_physical_device.c:2998-3078`. **Todas** as entradas têm `MSize = NSize = KSize = 16` e `scope = VK_SCOPE_SUBGROUP_KHR`. Não há 8×8×16 nem dimensões flexíveis.

`radv_physical_device.c:1978`: `cooperativeMatrixSupportedStages = VK_SHADER_STAGE_COMPUTE_BIT` — **somente compute**.

### 2.3 Combinações de tipo

| Bloco | A / B | C / Result | Condição | Nº |
|---|---|---|---|---|
| FP8 | E4M3 ou E5M2 | FP32 | **`gfx_level >= GFX12`** | 4 |
| FP16/BF16 | FP16 | FP16 ou FP32 | todas as gerações | 2 |
| | BF16 | BF16 ou FP32 | **GFX12 apenas** | 2 |
| INT8 | SINT8/UINT8 | SINT32/UINT32, ±saturação | exceto C unsigned + saturate | 12 |

**`[INFERÊNCIA]`** Total esperado em `gfx1201`: **20 entradas**; em `gfx11`: 14. É predição falsificável em um comando — conferir com `vulkaninfo` antes de citar.

Duas citações literais do código do driver, ambas material direto para o eixo "declarado × efetivo":

- `/* BF16 isn't working precisely on GFX11. */` — o driver **recusa** BF16 em RDNA 3 por imprecisão de hardware, e o habilita em RDNA 4.
- `/* The HW only supports signed acc. */` — justifica a exclusão de acumulador unsigned com saturação.

### 2.4 Tipos ausentes

Não expostos: FP64, **INT4**, FP6/FP4/MXINT8. Relevante porque o silício **tem** `v_wmma_i32_16x16x32_iu4` — não há `VkComponentTypeKHR` para INT4, logo é inalcançável pela extensão.

## 3. O achado categórico principal: esparsidade inalcançável

Tabela de opcodes do ACO, `src/amd/compiler/aco_opcodes.py:1227-1248` (Mesa 25.2.8):

- **WMMA denso**, novidades de gfx12: `v_wmma_f32_16x16x16_fp8_fp8`, `_fp8_bf8`, `_bf8_fp8`, `_bf8_bf8` (0x46–0x49) e `v_wmma_i32_16x16x32_iu4` (0x4a).
- **SWMMAC**, família inteira exclusiva de gfx12 (0x50–0x5a): `v_swmmac_f32_16x16x32_f16`, `_bf16`, `v_swmmac_f16_16x16x32_f16`, `v_swmmac_bf16_16x16x32_bf16`, `v_swmmac_i32_16x16x32_iu8`, `_iu4`, `v_swmmac_i32_16x16x64_iu4`, `v_swmmac_f32_16x16x32_fp8_fp8`, `_fp8_bf8`, `_bf8_fp8`, `_bf8_bf8`.

`src/amd/compiler/instruction_selection/aco_select_nir_intrinsics.cpp:3836-3905` (`visit_cmat_muladd`) emite **apenas** variantes `v_wmma_*`. Nunca SWMMAC. Consistente com a spec: `VK_KHR_cooperative_matrix` não tem conceito de matriz esparsa.

> **A esparsidade estruturada da RDNA 4 existe no silício e é inalcançável por API agnóstica de fornecedor ratificada.**

**`[INFERÊNCIA]`** O K dobrado nos nomes (`16x16x32` em SWMMAC contra `16x16x16` em WMMA; `16x16x64` para INT4) é assinatura de esparsidade estruturada 2:4. O nome do opcode só mostra o K dobrado — confirmar no ISA guide antes de afirmar "2:4".

## 4. Layout de dados e o problema do wave size

`src/amd/vulkan/nir/radv_nir_lower_cooperative_matrix.c`, cabeçalho, citação literal:

> "On GFX11, the A&B matrices needs to be replicated, lanes 0..15 are replicated to 16..31 and for wave64 also into lanes 32..47 and 48..63. A&B matrices are always vectors of 16 elements.
> On GFX12, there is no data replication (...)
> Note that the GFX12 ISA doc describes other layouts for A/B, but they are identical to the C layout with the exception of the order of the rows (columns for A). And as long as these are swapped in the same way for both A and B, the muladd result will be the same. So we use the C layout for all uses."

Componentes por invocação em GFX12: `assert(desc.cols == 16 && desc.rows == 16); return 256 / params->wave_size;` → **8 componentes/lane em wave32, 4 em wave64**.

Alinhamento de load/store: `align_mul = MIN2(16, bits*rows/8)` e, **em GFX12, `align_mul /= wave_size/16`** — o alinhamento exigido depende do wave size.

### 4.1 Wave64 é o padrão silencioso

`src/amd/vulkan/radv_shader_info.c:928-941`:

```c
const bool require_full_subgroups =
   stage_key->subgroup_require_full || nir->info.cs.has_cooperative_matrix || (...);
const unsigned required_subgroup_size = stage_key->subgroup_required_size * 32;
if (required_subgroup_size)        info->wave_size = required_subgroup_size;
else if (require_full_subgroups)   info->wave_size = RADV_SUBGROUP_SIZE;   // = 64
```

com `#define RADV_SUBGROUP_SIZE 64` em `radv_constants.h:84`.

> **Qualquer compute shader que use cooperative matrix é compilado em wave64 por padrão no RADV.** Para obter wave32 é preciso exigir explicitamente via `VkPipelineShaderStageRequiredSubgroupSizeCreateInfo` (ou `SubgroupSize` no SPIR-V).

Isso tem duas consequências, e as duas são centrais para este TCC:

1. **Ameaça à validade.** Sem fixar o subgroup size, muda o layout de dados, muda o alinhamento exigido, e mede-se duas coisas acreditando medir uma.
2. **Oportunidade.** É uma variável experimental **intra-máquina perfeita** — mesmo shader, mesmo hardware, mesmo driver, mesmo dataset, só o subgroup size varia. É a forma mais forte de afirmação disponível.

## 5. O que a spec tem e o driver não tem

`VK_EXT_cooperative_matrix_maintenance1` (extension #660, **ratificada**, EXT multi-vendor com NVIDIA, Qualcomm, Intel e Arm) acrescenta as capabilities SPIR-V `CooperativeMatrixReductionsEXT`, `CooperativeMatrixConversionsEXT`, `CooperativeMatrixPerElementOperationsEXT`, `CooperativeMatrixGetCoordinateEXT`.

**Não existe no Mesa 25.2.8** — verificado por ausência em `docs/features.txt` e em `src/amd/vulkan/`. O `mesamatrix.net` registra o commit *"docs: add missing VK_EXT_cooperative_matrix_maintenance1 for radv, lvp"* datado de **2026-08-20**, posterior à versão instalada.

**`[NÃO VERIFICADO]` e importante:** se o Mesa 26.0.3 — que estava instalado na máquina antes da reinstalação de 2026-08-25 — já continha `maintenance1`. Se contiver, a reinstalação desnecessária custou acesso a essa funcionalidade. Verificar antes de afirmar qualquer coisa.

`VK_NV_cooperative_matrix2` no RADV: habilitada só via driconf `cooperative_matrix2_nv` (**desligada por padrão**), expõe apenas `cooperativeMatrixConversions`, e `...FlexibleDimensionsPropertiesNV` retorna `*pPropertyCount = 0`.

Consequência de projeto: a não-linearidade do MLP terá de ser aplicada por acesso a elemento (`m[i]`), e as conversões de tipo à mão.

## 6. Restrição de armazenamento — com uma ressalva que importa

`GLSL_KHR_cooperative_matrix.txt` (Khronos, Last Modified **2023-07-21**, Revision 1), citação literal:

> "Cooperative matrix types can be used as global variables, local variables, function parameters, and function return values. **They must not be used in uniform, buffer, or shared memory, or in input/output storage classes.**"

**Ressalva de leitura, e ela muda o projeto:** a restrição é sobre **declarar variáveis do tipo `coopmat`** nessas classes de armazenamento — **não** sobre carregar/armazenar dados de/para `shared`. O `coopMatLoad`/`coopMatStore` operam sobre arrays, inclusive em `shared`, e a própria spec diz que o tipo do componente pode diferir do tipo do array de origem, *"this makes it easier to efficiently load matrix data into shared memory"*. Evidência de uso real: o shader `linear_qw_coopmat.glsl` do ExecuTorch aplica escala de peso *"during the B-tile store to shared"*.

Portanto: staging de ativações por `shared` é viável; o que não é viável é manter um objeto `coopmat` residente em `shared` entre camadas. A fusão entre camadas se dá em registrador ou com round-trip explícito por `shared`.

## 7. Linguagens de shading

| Caminho | Estado | Fonte |
|---|---|---|
| **GLSL `GL_KHR_cooperative_matrix`** | ✅ **Verificado e é o caminho batido.** `coopmat<T, scope, rows, cols, use>`, `coopMatLoad/Store/MulAdd`. Status "Complete", Rev. 1, 2023-07-21. Usado por llama.cpp/ggml, ncnn, ExecuTorch | repo `KhronosGroup/GLSL`, `extensions/khr/GLSL_KHR_cooperative_matrix.txt` |
| **Slang `CoopMat<>` + `coopMatMulAdd<T,bool>`** | ⚠️ Existe no `master` (emissores para CUDA, Metal, HLSL confirmados), mas **ausente do user guide oficial** e **o caminho de emissão SPIR-V não foi confirmado** | `shader-slang/slang`, `tools/slang-unit-test/unit-test-cooperative-type-metadata.cpp:353-362` |
| HLSL | Exige shader model 6.10; sem variante com saturação | comentário no repo do Slang — `[NÃO VERIFICADO]` na doc da Microsoft |
| WGSL `subgroupMatrixMultiplyAccumulate` | Em uso real no ONNX Runtime, com tiling `8x16x16` | `microsoft/onnxruntime`, templates WGSL — spec normativa `[NÃO VERIFICADO]` |

**Decisão derivada:** GLSL é o caminho padrão do projeto. Slang só depois de um teste de 5 minutos — `slangc -target spirv` de um shader mínimo, seguido de `spirv-dis`, para confirmar que emite `SPV_KHR_cooperative_matrix`.

Constantes GLSL úteis: `gl_MatrixUseA/B/Accumulator = 0/1/2`; `gl_CooperativeMatrixLayoutRowMajor/ColumnMajor = 0/1`; `gl_MatrixOperandsSaturatingAccumulation = 0x10`. Os parâmetros scope/rows/cols podem ser **constantes de especialização** — permite um único SPIR-V parametrizado por dispositivo.

## 8. Literatura: o vácuo

Consultas à API oficial do arXiv (`export.arxiv.org/api/query`), acesso 2026-08-26:

| Consulta | `totalResults` |
|---|---|
| `all:"cooperative matrix" AND all:Vulkan` | **0** |
| `all:"Vulkan" AND all:"matrix cores"` | **0** |
| `all:"Vulkan" AND all:"Tensor Cores"` | **0** |
| `abs:"cooperative matrix"` | 4 — **nenhum sobre GPU** (EDPs, teoria dos jogos, e um typo de "copper matrix") |

**Afirmação segura:** nenhum trabalho encontrado no arXiv sobre uso de cooperative matrix em Vulkan.
**Afirmação NÃO autorizada:** "não existe literatura". Falta consultar ACM DL, IEEE Xplore, Eurographics DL (HPG/EGSR) e Scopus — nenhuma foi consultada.

## 9. Implementações abertas que usam a extensão

| Projeto | Uso | Referência de código |
|---|---|---|
| **llama.cpp / ggml / whisper.cpp** | Três caminhos paralelos: scalar, `coopmat` (KHR), `coopmat2` (NV). Detecção **em tempo de compilação contra o `glslc`**, com shaders sentinela | `ggml/src/ggml-vulkan/CMakeLists.txt:72-85`; `vulkan-shaders/feature-tests/coopmat.comp` |
| **ncnn** (Tencent) | GEMM com tiling `coopmat_M/N/K`; padding condicional anti-conflito-de-banco em função do caminho de API | `src/layer/vulkan/gemm_vulkan.cpp:1010, 1189, 1642` |
| **PyTorch ExecuTorch** | Shaders `linear_qw_coopmat.glsl`, `linear_dq8ca_qw_coopmat.glsl`; FP16→FP32 MMA | `backends/vulkan/runtime/graph/ops/glsl/` |
| **vkpeak** (nihui) | Mede teto de throughput com `REPEAT_16(c = coopMatMulAdd(a,b,c))`, com um e dois acumuladores | `vkpeak.cpp:736-806` |
| **MLIR / LLVM** | `gpu::MMAMatrixType` → `spirv::CooperativeMatrixType`, escopo fixo em Subgroup | `mlir/lib/Conversion/GPUToSPIRV/WmmaOpsToSPIRV.cpp:36-45` |
| IREE | Consulta as propriedades; **`[NÃO VERIFICADO]`** se gera cooperative matrix no codegen | `runtime/src/iree/hal/drivers/vulkan/physical_device.h:120-129` |

**Nenhum deles é um MLP fundido.** São GEMMs e camadas lineares dentro de frameworks de inferência.

### 9.1 Bug de driver documentado por terceiro

Comentário nos shaders do ExecuTorch, citação literal: *"crashes (null deref in `vkCreateComputePipelines`) when a loop containing `coopMatMulAdd` has a UBO-derived trip count."*

**`[NÃO VERIFICADO]`** O comentário **não identifica o driver**. Não atribuir ao RADV sem reproduzir. Se reproduzir em RADV/gfx1201, é achado próprio e reportável upstream.

## 10. Material aplicado da AMD

A página oficial <https://gpuopen.com/amd-gpu-architecture-programming-documentation/> (acesso 2026-08-26) hospeda o ISA guide de RDNA 4 e uma série de três artigos, transcrição literal dos resumos:

- **"WMMA guide for AMD RDNA 4 architecture GPUs — part 1"**: *"Practical guide to fusing GEMMs on AMD RDNA™ 4 architecture, covering WMMA layout, a transpose-by-swapping A/B technique, HIP sample code, and hipBLAS-verified results used in Llama.cpp."*
- **part 2**: *"Achieve peak AMD RDNA™ 4 architecture memory bandwidth for low-precision GEMM by fusing WMMA to double the K dimension, enabling 128-bit loads for FP8/INT8, and matching hipBLAS results bit-for-bit."*
- **part 3**: *"...fast in-register matrix transpose ... with a WMMA-based identity trick..."*

Duas observações. A técnica *transpose-by-swapping A/B* que a AMD descreve é exatamente a que o RADV documenta no comentário citado em §4. E a série é sobre **HIP**, não Vulkan — é a via nativa de fornecedor, logo serve como linha de base de projeto e como contraste.

**`[NÃO VERIFICADO]`** O conteúdo do ISA guide de RDNA 4. Um PDF intitulado "RDNA4 Instruction Set Architecture", datado 2025-04-07, 697 páginas, aparece em `docs.amd.com/api/khub/documents/uQpkEvk3pv~kfAb2x~j4uw/content`, mas a referência vem de snippet de busca e o documento não foi aberto. **Tudo o que este arquivo afirma sobre WMMA/SWMMAC vem da tabela de opcodes do ACO, não da AMD.** Baixar pelo link do GPUOpen e conferir folha de rosto antes de citar.

## 11. Pendências de verificação, por prioridade

1. **Executar `vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR` na máquina** e conferir contra a predição de 20 entradas (§2.3). Primeiro experimento do projeto, custo de minutos.
2. **Abrir o ISA guide de RDNA 4** e conferir WMMA/SWMMAC, formas, e a interpretação de esparsidade 2:4.
3. **Testar se o Slang emite `SPV_KHR_cooperative_matrix`** (`slangc -target spirv` + `spirv-dis`).
4. **`git log` de `radv_nir_lower_cooperative_matrix.c`** para datar a estreia no RADV. O `gitlab.freedesktop.org` está atrás de proof-of-work anti-scraping; resolve-se em clone local.
5. **Verificar se o Mesa 26.0.3 tem `maintenance1`** — determina se a reinstalação de 2026-08-25 custou funcionalidade.
6. **Buscar literatura fora do arXiv** (ACM DL, IEEE Xplore, Eurographics DL, Scopus).
7. **Capturar as URLs** dos três artigos WMMA do GPUOpen.
8. **Reproduzir o crash do ExecuTorch** em RADV/gfx1201, ou confirmar que não ocorre.
