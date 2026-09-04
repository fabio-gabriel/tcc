# CLAUDE.md — pivô: reprodutibilidade em treino de 3DGS

Guia para o assistente ao trabalhar **nesta subpasta**. O TCC pivotou de tema em 2026-08-26. A pasta-raiz do repositório contém o material do tema anterior e **permanece intacta como registro** — não apagar, não reescrever retroativamente.

> A fonte de verdade do enquadramento é o `PLANO.md` desta pasta. O resumo abaixo orienta; em divergência, o `PLANO.md` prevalece.

## Papel esperado

Atuar como **professor orientador**. Questionar escopo, premissas e fontes antes de produzir texto; propor estrutura quando o pedido for vago; apontar lacunas de argumento; nunca inventar referências, dados ou citações. Idioma: **português (PT-BR)**, exceto ao citar literalmente fontes em inglês.

## Tema

**Título de trabalho (provisório, a validar com o Prof. Gilvan):**

> Reprodutibilidade em treino de 3D Gaussian Splatting: dispersão entre execuções, acumulação atômica não-associativa e a comparabilidade de resultados publicados

### Pergunta

Quão reprodutíveis são as métricas de qualidade no treino de 3D Gaussian Splatting, e o que a dispersão entre execuções idênticas implica para a comparabilidade dos resultados publicados na área?

### Mecanismo

O backward do 3DGS acumula gradientes por **atômicos de ponto flutuante**. Adição em ponto flutuante **não é associativa**, e a ordem de execução entre invocações de GPU não é determinística. Portanto duas execuções idênticas — mesma cena, mesma seed, mesmo commit, mesma máquina — não produzem o mesmo modelo. A questão empírica é o **tamanho** desse efeito nas métricas finais; a questão metodológica é se ele é da mesma ordem das diferenças que a literatura apresenta como ganho.

### Três eixos, deliberadamente independentes

| Eixo | Natureza | Risco |
|---|---|---|
| **1. Observacional** — dispersão de métricas e de parâmetros entre N execuções idênticas | Medição de erro e dispersão, não de velocidade | Baixo |
| **2. Interventivo** — variante determinística da acumulação (atômicos inteiros em ponto fixo, que são associativos) em um estágio do backward, com custo medido | Código autoral; transforma correlação em causa | Médio |
| **3. Replicação** — os valores publicados pelos autores do VkSplat se reproduzem em hardware que eles não testaram (RDNA 4)? | Replicação independente | Baixo |

**Nenhum eixo depende do sucesso dos outros.** Falha de bring-up é dado, não fracasso.

### O que este TCC não é

- **Não é benchmarking.** Não há comparação de tempo de parede entre fornecedores, plataformas ou implementações de terceiros. O eixo 2 mede o custo de uma intervenção própria, o que é justificativa de decisão de projeto.
- **Não é comparação com gsplat/CUDA.** Não há hardware NVIDIA. O eixo 3 compara os números obtidos com os **valores publicados pelos próprios autores do VkSplat**, e deve ser dito nesses termos.
- Não envolve implementar rasterizador nem MLP.

## Ambiente verificado (2026-08-26)

| Item | Estado |
|---|---|
| SO | Ubuntu 24.04.4 LTS, kernel `7.0.0-30-generic` (HWE) |
| GPU | AMD Radeon RX 9070 XT, RDNA 4, `gfx1201`, 16 GB |
| Driver Vulkan | RADV, Mesa 25.2.8; loader de instância 1.3.275; device `apiVersion` 1.4.318 |
| CPU / RAM | Ryzen 7 5700X · **15 GiB** (restrição real) |
| Toolchain | em instalação; `vulkan-tools` presente |
| ROCm | não instalado, e **fora do caminho crítico** |

Fontes: `../experimentos/00-inventario/saidas/` e `../experimentos/caderno-de-campo.md`.

## Armadilhas técnicas já identificadas — ler antes de rodar qualquer coisa

Detalhamento e fontes em `bibliografia/verificacao-vulkan-rdna4.md`.

1. **`llvmpipe` é enumerado como segundo dispositivo Vulkan.** É rasterizador em CPU. Sem fixar a seleção de dispositivo, uma execução pode cair silenciosamente nele e produzir números absurdos. **Registrar `deviceName` em toda saída de medição.**
2. **O RADV força wave64** em compute shaders sob certas condições, e o wave size altera layout de dados e alinhamento exigido. Se for variável relevante, fixar explicitamente e reportar qual foi usado.
3. **VkSplat exige `VK_EXT_shader_atomic_float`** — é literalmente o mecanismo sob investigação. Confirmar que `shaderBufferFloat32AtomicAdd` está ativa; se o caminho cair em emulação, o objeto de estudo muda.
4. **VkSplat só lê COLMAP.** Não há leitor de `transforms.json`, logo Synthetic-NeRF não entra sem conversão. Dataset primário: **Mip-NeRF 360, cena `garden`, `images_4`**.
5. **`image_cache_device` é `'cpu'` por padrão** — cache do dataset na RAM do host. Com 15 GiB, é o candidato mais provável a OOM. Existe a opção `'gpu'`.
6. **Pode ser necessário recompilar shaders** se o dispositivo exigir `USE_EMULATED_INT64` / `USE_EMULATED_F32_ATOMIC`. Requer a toolchain **Slang** (`slang-2026.2.1`), ausente do apt. **Se cair no caminho `USE_EMULATED_F32_ATOMIC`, isso é diretamente relevante ao tema** — a emulação muda o comportamento numérico da acumulação.

## Disciplina de método — não negociável

Vem de erros cometidos neste projeto entre 2026-08-20 e 2026-08-26, documentados em `../bibliografia/verificacao-experimento-rdna4.md` §1.1 e `../experimentos/caderno-de-campo.md`.

1. **Verificar se a fonte foi superseded antes de citá-la.** Uma reinstalação de SO desnecessária resultou de citar página marcada com *"This page has moved!"*.
2. **Não converter inconveniência de ambiente em evidência.** Dificuldade de instalação foi registrada como "evidência de imaturidade do stack" antes de qualquer verificação. Era falsa.
3. **Exigir a saída literal antes de afirmar causa.** Três diagnósticos sucessivos de um erro de `apt` foram emitidos com confiança acima da evidência; a causa era um espaço escapado por `\`.
4. **Separar erro do operador de defeito da plataforma.**
5. **Escrutínio maior para achados que favorecem a tese**, não menor.
6. **Nunca reportar média nua.** Neste TCC isso deixa de ser boa prática e passa a ser **o objeto de estudo** — a tese é que médias nuas escondem dispersão relevante. Reportar média nua aqui seria autocontraditório.
7. **Pré-registrar o protocolo em commit antes da primeira execução medida.** N, seed, cena, resolução, critério de parada e limiares de dispersão definidos **antes** de ver os dados. Sem isso o eixo 1 é indefensável, porque a tentação de ajustar N ou o limiar depois de ver a dispersão é direta.

## Convenções de trabalho

- **Não criar arquivos `.md` de planejamento, decisões ou resumos** sem pedido explícito.
- Texto da monografia em `.md`, estruturado para migração futura a LaTeX (`abntex2`).
- **ABNT:** NBR 6023 (referências), NBR 10520 (citações), NBR 14724 (estrutura).
- **Não commitar nem dar push por conta própria.** Exceção prevista, a lembrar ao aluno: o pré-registro do protocolo depende de commit **antes** da primeira execução medida.
- Métricas (CSV/JSON), logs e inventários **são dados de pesquisa e devem ser versionados**. Datasets, checkpoints e `.ply` não.
- Fontes: preferir spec Khronos, ISA de fornecedor, arXiv e repositórios oficiais a blogs e material de marketing.

## Escopo institucional

- **Instituição/curso:** Engenharia de Computação, Universidade Federal do Ceará (UFC)
- **Orientador institucional:** Professor Gilvan — **o pivô ainda não foi levado a ele.** Foram três reenquadramentos em uma semana; a conversa é obrigatória e o `PLANO.md` serve de base
- **Depósito:** 06/nov/2026, data institucional
- **Tipo:** monografia com experimento próprio e intervenção de código de escopo limitado
