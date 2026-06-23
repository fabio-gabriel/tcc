# Plano do TCC — Renderização Neural em Hardware Heterogêneo

> Documento vivo: estado, cronograma, sprints, TODOs e decisões. Atualizar a cada sprint encerrado ou quando uma decisão importante for tomada. Para o papel de Claude e convenções estáveis do projeto, ver `CLAUDE.md`. Para fontes verificadas do experimento, ver memória persistente `reference_experimento_rdna4.md`.

## 1. Identidade

| Item | Valor |
|---|---|
| Aluno | Fabio Gabriel |
| Curso | Engenharia de Computação — UFC |
| Orientador | Prof. Gilvan |
| Tipo | Monografia bibliográfica + experimento próprio |
| Norma de formatação | ABNT (NBR 6023, 10520, 14724) |
| Formato de trabalho atual | Markdown (`.md`); migração futura para LaTeX (`abntex2`) |
| Início efetivo | 2026-06-23 |
| Defesa estimada | ~2026-11-23 (5 meses) |

## 2. Pergunta de pesquisa (a confirmar com Prof. Gilvan)

> Em que medida algoritmos modernos de renderização neural — Instant-NGP (NeRF acelerado) e 3D Gaussian Splatting — são portáveis e performantes em GPUs AMD RDNA 4 de consumo (RX 9070 XT) via ROCm/HIP, Vulkan e Taichi, em comparação com os baselines CUDA reportados na literatura?

Hipóteses subjacentes (a explicitar e testar):
- H1: É possível executar 3DGS em RDNA 4 com modificações localizadas no código (caminho de prova: PR #1297 do `graphdeco-inria/gaussian-splatting`).
- H2: Pipelines escritos em Taichi/Vulkan oferecem portabilidade suficiente para executar Instant-NGP em RDNA 4 sem reescrita do kernel principal.
- H3: A pilha PyTorch + ROCm 7.x apresenta penalidade de desempenho **e/ou regressões de correção** em RDNA 4 em comparação com PyTorch + CUDA em hardware NVIDIA equivalente.

## 3. Caminho experimental escolhido

| Pipeline | Rota concreta | Fonte verificada |
|---|---|---|
| **3D Gaussian Splatting** | Branch do PR `graphdeco-inria/gaussian-splatting#1297` (Port to HIP / AMDGPU) | github.com/graphdeco-inria/gaussian-splatting/pull/1297 |
| **NeRF / Instant-NGP** | `Linyou/taichi-ngp-renderer` via Taichi + backend Vulkan | github.com/Linyou/taichi-ngp-renderer |
| **Baseline de treino genérico** | PyTorch + ROCm 7.x estável, atento aos bugs ativos em gfx1201 | rocm.docs.amd.com + issues registradas |
| **Exploração lateral (opcional)** | `PhysicalAI-AIM/tiny-rocm-nn` adaptado para WMMA RDNA — pode virar trabalho futuro | github.com/PhysicalAI-AIM/tiny-rocm-nn |

Bugs ativos relevantes em PyTorch + ROCm gfx1201 (precisam entrar na seção de ameaças à validade):
- `pytorch/pytorch#177834` — LSTM/MIOpen incorreto em gfx1201
- `pytorch/pytorch#187343` — `expandable_segments:True` causa `hipErrorIllegalAddress`
- `pytorch/pytorch#181939` — falha CMake `gfx1036;gfx1201`
- `ROCm/ROCm#6116` — `torch.mm` produz NaN com >~500K linhas
- `ROCm/ROCm#6374` — page fault OpenCL/ROCr em RDNA 4 (XNACK off, host-VA)

## 4. Cronograma — fases e marcos

| Fase | Sem | Período aprox. | Saída | Status |
|---|---|---|---|---|
| **Sprint 0 — Viabilidade** | 1 | 23/jun → 30/jun/26 | Cada caminho roda ≥ 1 cena de teste; dump de versões/bugs; decisão go/no-go | Não iniciado |
| **1 — Proposta + Cap. 2** | 2-6 | jul → meados ago/26 | Proposta formal validada com Prof. Gilvan; sumário ABNT; Cap. 2 escrito | Não iniciado |
| **2 — Cap. 3 + datasets + métricas** | 7-8 | meados ago/26 | Cap. 3 (panorama de hardware) escrito; datasets selecionados; métricas definidas | Não iniciado |
| **3 — Experimento principal** | 9-12 | fim ago → meados out/26 | Benchmarks executados; tabelas brutas em CSV/JSON no repo | Não iniciado |
| **4 — Cap. 4 + Cap. 5** | 13-15 | meados out → início nov/26 | Metodologia e resultados/discussão escritos; revisão de Cap. 2-3 | Não iniciado |
| **5 — Fechamento** | 16-17 | início nov → 23/nov/26 | Cap. 1, Cap. 6, resumo, revisão integral, migração LaTeX, depósito, defesa | Não iniciado |

> Janela útil de escrita/experimento: ~17 semanas. Margem para banca/correções: ~3 semanas finais embutidas no Sprint 5.

## 5. Sprints e TODOs

### Sprint 0 — Viabilidade (semana 1: 23/jun → 30/jun/26)

Objetivo: validar antes de qualquer escrita que os três caminhos do experimento funcionam minimamente na 9070 XT.

- [ ] Decidir hospedagem do repositório git (GitHub privado / GitLab UFC / só local)
- [ ] Inicializar `git init` no repositório
- [ ] Configurar Tailscale entre Mac e máquina Linux (PAUSADO a pedido do usuário em 2026-06-23 — retomar antes do bring-up)
- [ ] Bring-up 3DGS via PR #1297 na 9070 XT — rodar treino mínimo
- [ ] Bring-up `Linyou/taichi-ngp-renderer` — rodar exemplo
- [ ] Bring-up PyTorch + ROCm 7.x — tutorial mínimo (treino MNIST ou similar)
- [ ] Reportar bugs/quirks encontrados em cada caminho (caderno de campo no repo)
- [ ] Decisão go/no-go por pipeline; ajustar escopo se necessário

### Sprint 1 — Proposta + Cap. 2 (semanas 2-6: jul → meados ago/26)

Objetivo: alinhar oficialmente com o orientador e produzir o capítulo de fundamentação teórica de renderização neural.

- [ ] Reunião formal com Prof. Gilvan: validar recorte temático e pergunta de pesquisa
- [ ] Fixar pergunta de pesquisa final + hipóteses
- [ ] Definir sumário ABNT da monografia (estrutura de capítulos)
- [ ] Ler papers seminais do Eixo A do fichamento (NeRF, 3DGS, métricas, surveys)
- [ ] Escrever Cap. 2 — Renderização Neural (representações implícitas, explícitas, volume rendering, splatting, métricas)
- [ ] Continuar leituras dos Eixos B e C em paralelo

### Sprint 2 — Cap. 3 + datasets + métricas (semanas 7-8: meados ago/26)

- [ ] Ler papers do Eixo C (Taichi, ROCm, HIP, Tensor Cores, WMMA, FSR/DLSS)
- [ ] Escrever Cap. 3 — Hardware Heterogêneo e Portabilidade (CUDA vs ROCm/HIP vs Vulkan vs Taichi)
- [ ] Selecionar datasets canônicos: Synthetic-NeRF, Mip-NeRF 360, Tanks and Temples (a confirmar com Prof. Gilvan)
- [ ] Definir conjunto final de métricas: PSNR, SSIM, LPIPS, tempo de treino, FPS de inferência, uso de VRAM, energia (se possível com `rocm-smi` / `nvidia-smi` por proxy bibliográfico)

### Sprint 3 — Experimento principal (semanas 9-12: fim ago → meados out/26)

- [ ] Executar 3DGS (PR #1297) em todos os datasets selecionados
- [ ] Executar Instant-NGP (taichi-ngp-renderer) em todos os datasets
- [ ] Executar baselines PyTorch + ROCm comparáveis
- [ ] Coletar métricas em formato versionável (CSV/JSON) no repo
- [ ] Comparar com baselines CUDA reportados na literatura (não há comparação direta no mesmo hardware — apontar como limitação)
- [ ] Documentar bugs/regressões de correção encontrados como achados empíricos

### Sprint 4 — Cap. 4 + Cap. 5 + revisão (semanas 13-15: meados out → início nov/26)

- [ ] Escrever Cap. 4 — Metodologia (setup, datasets, métricas, protocolo)
- [ ] Escrever Cap. 5 — Resultados e Discussão (tabelas, gráficos, análise crítica, limitações)
- [ ] Revisar Cap. 2 e Cap. 3 à luz dos resultados

### Sprint 5 — Fechamento (semanas 16-17: início nov → 23/nov/26)

- [ ] Escrever Cap. 1 — Introdução (motivação, objetivo, contribuições)
- [ ] Escrever Cap. 6 — Conclusão (síntese, trabalhos futuros)
- [ ] Escrever resumo + abstract (PT-BR e EN)
- [ ] Revisão integral
- [ ] Migrar `.md` → modelo LaTeX (`abntex2`); validar formatação ABNT
- [ ] Depósito + preparação da defesa

## 6. Decisões registradas

| Data | Decisão | Justificativa |
|---|---|---|
| 2026-06-23 | Tipo de TCC: monografia bibliográfica com experimento próprio | Hardware disponível (RX 9070 XT) e gap empírico real no estado da prática |
| 2026-06-23 | Norma: ABNT | Padrão UFC |
| 2026-06-23 | Formato: `.md` agora, LaTeX `abntex2` no fim | Iteração rápida agora; conformidade ABNT no fim |
| 2026-06-23 | Setup de execução: Tailscale + SSH + git | Iteração ágil com debug remoto; pausado para retomar antes do Sprint 0 |
| 2026-06-23 | Caminho experimental: 3DGS via PR #1297, Instant-NGP via taichi-ngp-renderer, baseline PyTorch+ROCm | Verificação de fontes primárias confirma viabilidade; tiny-cuda-nn AMD direto não é viável (CDNA-only) |

## 7. Decisões pendentes

- [ ] Hospedagem do repositório git: GitHub privado / GitLab UFC / só local
- [ ] Confirmação com Prof. Gilvan: pergunta de pesquisa, hipóteses, recorte
- [ ] Datasets finais: Synthetic-NeRF + Mip-NeRF 360 + Tanks and Temples? Outro?
- [ ] Comparativo NVIDIA: usaremos números da literatura ou tentaremos reproduzir num colega/laboratório com RTX equivalente?
- [ ] Energia: incluir medição (`rocm-smi --showpower`) como métrica complementar?

## 8. Riscos e ameaças à validade

| Risco | Impacto | Mitigação |
|---|---|---|
| Bugs ativos em PyTorch+ROCm RDNA 4 | Resultados podem incluir falhas de correção, não só de desempenho | Documentar como achado empírico; reportar issue upstream se inédito |
| PR #1297 do 3DGS é rascunho da comunidade | Pode regressar ou exigir patch local | Forkar e fixar commit; documentar versões usadas |
| Janela de 5 meses é apertada | Escopo pode estourar | Sprint 0 com decisão go/no-go por pipeline; permitir cortar tiny-rocm-nn sem perder o TCC |
| Falta de hardware NVIDIA equivalente | Comparativo direto inviável | Usar números da literatura como baseline; explicitar como limitação metodológica |
| Mudanças de versão ROCm/PyTorch durante o experimento | Resultados não-reprodutíveis | Fixar versões com `requirements.txt` / Dockerfile; registrar SHA |
| Bibliografia "estava na cabeça" e ainda precisa ser fichada | Atraso no Cap. 2 | Fichamento em curso (`bibliografia/fichamento.md`) |

## 9. Estado atual (atualizado em 2026-06-23)

- Repositório local existe; git ainda não inicializado
- Material de partida: 3 PDFs exploratórios na raiz (números a tratar com cautela)
- Domínios liberados no sandbox: `www.google.com`, `rocm.docs.amd.com`, `github.com`, `api.github.com`, `www.amd.com`, `arxiv.org`, `pytorch.org`, `docs.taichi-lang.org`, `raw.githubusercontent.com`, `phoronix.com`, `pypi.org`
- Verificação de viabilidade do experimento concluída — ver memória `reference_experimento_rdna4.md`
- Fichamento bibliográfico: em construção (`bibliografia/fichamento.md`)
- Tailscale: pausado a pedido do usuário; retomar antes do Sprint 0

## 10. Materiais e localização

- `CLAUDE.md` — papel do Claude, convenções, escopo confirmado
- `PLANO.md` — este arquivo
- `bibliografia/fichamento.md` — revisão bibliográfica do estado da arte (em construção)
- 3 PDFs iniciais na raiz (material exploratório, não usar como fonte direta sem validar)
- Memórias persistentes em `~/.claude/projects/-Users-fabiogomes-code-tcc/memory/`
