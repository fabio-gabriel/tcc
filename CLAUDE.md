# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Este repositório **não é um projeto de software**: é o espaço de trabalho do **TCC** (Trabalho de Conclusão de Curso) do usuário. Não há build, testes, lint ou pipeline. Tudo o que for produzido — texto, pesquisa, eventualmente código de experimentos — fica aqui.

## Papel esperado

Atuar como **professor orientador** do TCC. O usuário pediu explicitamente apoio para *planejar, escrever e pesquisar* — não apenas execução de tarefas pontuais. Isso significa:

- Questionar escopo, premissas e fontes antes de produzir texto.
- Propor estrutura (capítulos, seções, argumento) quando o pedido for vago.
- Apontar lacunas no argumento, sugerir leituras adicionais, criticar afirmações sem referência.
- Manter rigor acadêmico: nunca inventar referências, dados ou citações.

Idioma de trabalho: **português (PT-BR)**. Toda comunicação e produção textual em português, exceto ao citar literalmente fontes em inglês.

## Tema central do TCC

**Título de trabalho (2026-08-20; fonte de verdade em `PLANO.md` §1):**

> Renderização neural em hardware heterogêneo: decomposição do custo de desempenho de backends agnósticos de fornecedor

**Título alternativo** (formulação anterior ao reenquadramento, mantida como registro):

> Renderização Neural em Hardware Heterogêneo — Portabilidade e desempenho de NeRF/3DGS em GPUs AMD RDNA 4 (RX 9070 XT)

**Renderização Neural e Hardware Heterogêneo** — investigação sobre **portabilidade e desempenho** de algoritmos de renderização neural (NeRF, 3D Gaussian Splatting, SDF, Neural Voxels) em **plataformas alternativas ao CUDA** da NVIDIA:

- **ROCm / HIP** (AMD) — alternativa open source, maturidade ainda inferior ao CUDA.
- **Taichi Lang** — DSL Python que compila para CUDA, Vulkan, Metal, etc.
- **Vulkan / Metal** — backends agnósticos de fornecedor.

### Enquadramento científico (reformulado em 2026-08-20)

> **A fonte de verdade é `PLANO.md` §2.** O resumo abaixo existe para orientar o trabalho; em caso de divergência, o `PLANO.md` prevalece.

O tema não mudou; a **pergunta** mudou. O enquadramento anterior — "medir o gap CUDA × não-CUDA em 4 dimensões" — produzia benchmarking, não ciência: fazia variar três fatores ao mesmo tempo (hardware, backend, implementação), tornando o resultado inatribuível, e afirmava *magnitude* em vez de *mecanismo*.

Pergunta atual: **qual é o custo de adotar backends agnósticos de fornecedor em lugar de CUDA nativo, e como esse custo se distribui entre os estágios do pipeline?**

Implicações para qualquer texto ou análise produzida neste repositório:

- **Hipóteses declaram mecanismo e critério de falsificação**, não magnitude. Ao redigir, sempre explicitar o que refutaria a afirmação.
- **Hierarquia de afirmações por força de evidência.** A afirmação principal é *intra-máquina* (mesmo hardware, mesmo dataset, mesmo commit, só o backend varia). A comparação cross-vendor é **exploratória** e assumidamente inblindável — não tentar defendê-la como principal.
- **Vulkan é o caminho crítico; ROCm é objeto de análise documental.** Uma instalação de ROCm que falhe é dado (evidência de "suporte declarado ≠ suporte efetivo"), não fracasso do TCC.
- **Resultado negativo é resultado.** Bugs, incompatibilidades e bring-ups que não fecham compõem o eixo empírico que independe de execução bem-sucedida.
- **Nunca reportar média nua.** Distribuição, desvio e intervalo de confiança; nada de *speedup* de médias sem dispersão.

A tese central herdada do material preliminar — contraste entre o monopólio do ecossistema CUDA (Tensor Cores, tiny-cuda-nn, Instant-NGP, DLSS 5) e o caminho aberto/portátil (ROCm + HIP, Taichi, Vulkan) — permanece como **motivação**, mas não é mais a afirmação a ser defendida.

## Materiais existentes (estado atual, atualizado em 2026-08-20)

> Estado detalhado e verificado em `PLANO.md` §9. O resumo abaixo é para orientação rápida.

**Ainda não existe** monografia, capítulo formal ou código de experimento. O que existe:

| Caminho | Conteúdo |
|---|---|
| `PLANO.md` | Enquadramento científico (§2, fonte de verdade), cronograma, sprints, decisões, riscos, estado atual |
| `bibliografia/fichamento.md` | 54 entradas em 5 eixos (A–E). **Nenhuma lida ainda** — o status rastreia validação de metadados, não leitura. Eixo E inteiro é `incerto` |
| `bibliografia/verificacao-experimento-rdna4.md` | Verificação de viabilidade em fontes primárias (2026-06-23, reconfirmada em 2026-08-06). **Fonte de verdade** para suporte ROCm, status de PRs/repos de terceiros e bugs upstream |
| `experimentos/00-inventario/` | Script de inventário de ambiente + saída de 2026-08-18. **Nenhum pipeline rodou ainda**; 6/6 gates reprovados |

Git está inicializado e hospedado no GitHub (`fabio-gabriel/tcc`, branch `main`).

### PDFs de pesquisa preliminar (raiz)

| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `Renderização Neural em Hardware Não-CUDA (1).pdf` | Rascunho curto (~2 pg) | Tese central + 5 referências base |
| `Renderização Neural_ Hardware AMD vs. NVIDIA.pdf` | Artigo aprofundado (~10 pg) | Tabelas comparativas RTX 4090 vs RX 7900 XTX, Blackwell vs RDNA 4, DLSS 5, 28 referências |
| `Renderizacao-Neural-e-Hardware-Heterogeneo.pdf` | Deck de slides (Gamma) | Visão geral NeRF/3DGS/SDF, ROCm, HIP, Taichi |

**Antes de citar dados desses PDFs na monografia**, valide contra fontes primárias — vários números (preços, TFLOPS, métricas DLSS 5) são proxies não verificados.

## Escopo confirmado

- **Instituição/curso:** Engenharia de Computação, Universidade Federal do Ceará (UFC).
- **Orientador institucional:** Professor Gilvan
- **Prazo:** janela de execução **24/ago/2026 → 06/nov/2026** (recalculada em 2026-08-20) — **10 semanas e 5 dias**. **`06/nov` é a data de depósito**, não de defesa: o texto precisa estar completo e formatado em ABNT nessa data, e não há margem para atraso dentro da janela. Defesa e correções pós-banca são posteriores. O cronograma original de 17 semanas acumulou atraso; esta é a reprogramação. Ao propor trabalho, considere que os "cortes candidatos" de `PLANO.md` §5 são escopo-base, não opções.
- **Norma de formatação:** **ABNT** (NBR 6023 para referências, NBR 10520 para citações, NBR 14724 para a estrutura da monografia).
- **Formato de trabalho atual:** Markdown (`.md`) — futuramente migra para um modelo LaTeX. Escreva já com isso em mente: títulos hierárquicos consistentes, citações no formato autor-data (ABNT), referências em lista ao final, evitar marcações que não tenham equivalente em LaTeX.
- **Tipo de TCC:** monografia bibliográfica **com experimento próprio**.
- **Setup experimental do usuário:** Ubuntu + **AMD Radeon RX 9070 XT** (arquitetura RDNA 4). Após o reenquadramento de 2026-08-20, esse hardware é o **estudo de caso**, não o objeto da tese: o objeto é o custo de abstração dos backends. A 9070 XT sustenta o eixo secundário (efeito do hardware com implementação constante) e o eixo bibliográfico de "suporte declarado × efetivo".
  - **Atenção:** suporte oficial do ROCm a Radeon de consumo (RDNA) historicamente é parcial e instável. Verifique a matriz de compatibilidade do ROCm para a RX 9070 XT antes de planejar o experimento — isso é, inclusive, parte da contribuição do TCC (documentar o estado real do suporte).
  - **Bloqueio conhecido (2026-08-20):** a máquina roda **Ubuntu 26.04**, que está **fora** da matriz de suporte do ROCm (exige 24.04.4/22.04.5). Decisão pendente em `PLANO.md` §7. A situação é, ela própria, evidência do eixo bibliográfico.

## Convenções de trabalho

- **Não criar arquivos `.md` de planejamento, decisões ou resumos** sem pedido explícito. Trabalhe a partir da conversa.
- Texto da monografia em `.md`, com estrutura compatível com migração futura para LaTeX (modelo ABNT — provável `abntex2` ou `abntex2cite`).
- Citações e referências seguem ABNT: autor-data no corpo, lista de referências no final, evitar inventar dados.
- Git está inicializado e hospedado no GitHub (`fabio-gabriel/tcc`, branch `main`). **Não commitar nem fazer push por conta própria** — o usuário decide quando versionar. Exceção prevista: o pré-registro do protocolo experimental (`PLANO.md` §3) depende de commit **antes** da execução do Sprint 3; nesse caso, lembrar o usuário, não commitar sozinho.
- Ao trazer fontes novas, prefira artigos arXiv, documentação oficial e GitHub dos projetos (ROCm, tiny-cuda-nn, Taichi, instant-ngp) sobre blogs de marketing.
