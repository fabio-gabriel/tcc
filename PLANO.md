# Plano do TCC: Renderização Neural em Hardware Heterogêneo

> Documento vivo: estado, cronograma, sprints, TODOs e decisões. Atualizar a cada sprint encerrado ou quando uma decisão importante for tomada. Para o papel de Claude e convenções estáveis do projeto, ver `CLAUDE.md`. Para fontes verificadas do experimento, ver `bibliografia/verificacao-experimento-rdna4.md` (versionado no repositório; substitui a memória persistente `reference_experimento_rdna4.md`, perdida em reinstall do Claude em 2026-08-06).

## 1. Identidade

| Item | Valor |
|---|---|
| Aluno | Fabio Gabriel |
| Curso | Engenharia de Computação, UFC |
| Orientador | Prof. Gilvan |
| Tipo | Monografia bibliográfica + experimento próprio |
| Norma de formatação | ABNT (NBR 6023, 10520, 14724) |
| Formato de trabalho atual | Markdown (`.md`); migração futura para LaTeX (`abntex2`) |
| Início efetivo | 2026-06-23 |
| Defesa estimada | ~2026-11-23 (5 meses) |

### Hipóteses operacionais (a explicitar e testar)

- **H1, performance:** existe gap mensurável de performance (tempo de treinamento até PSNR-alvo e FPS de inferência) entre CUDA em hardware NVIDIA e ROCm/Vulkan/Taichi em hardware AMD comparável; o gap em renderização (FPS) é menor que o gap em treinamento (tempo até convergência).
- **H2, portabilidade:** linguagens agnósticas (Vulkan, Taichi) reduzem o esforço de instalação/bring-up mas com penalidade de performance contra CUDA nativo; trabalhos como VkSplat sugerem que a penalidade pode ser pequena (ou até negativa em alguns regimes).
- **H3, energia:** a métrica W/frame e J/treinamento favorece CUDA em hardware NVIDIA equivalente, devido aos Tensor Cores especializados; a lacuna em RDNA 4 (com WMMA exposto via rocWMMA) é menor que em gerações AMD anteriores sem instruções matriciais.
- **H4, gap funcional:** a defasagem temporal entre o lançamento de uma técnica em CUDA e seu equivalente acessível em ROCm/HIP é da ordem de meses a anos; certas ferramentas-chave (notadamente `tiny-cuda-nn` para RDNA) ainda não têm equivalente AMD em meados de 2026.

## 3. Caminho experimental escolhido

O experimento consiste em executar baselines existentes em ambos os lados (CUDA e não-CUDA) sob condições controladas e medir as 4 dimensões.

### Lado CUDA (RTX 5070 Ti alugada em vast.ai, CUDA 13.X)

| Pipeline | Implementação de referência |
|---|---|
| Instant-NGP | `NVlabs/instant-ngp` (oficial, CUDA + tiny-cuda-nn) |
| 3D Gaussian Splatting | `graphdeco-inria/gaussian-splatting` (oficial, CUDA) |
| 3DGS alternativo | `nerfstudio-project/gsplat` (CUDA mais modular) |

### Lado não-CUDA (RX 9070 XT, RDNA 4)

| Pipeline | Rota concreta | Tipo |
|---|---|---|
| 3DGS via HIP | Branch do PR `graphdeco-inria/gaussian-splatting#1297` | ROCm/HIP |
| 3DGS via Vulkan compute | `harry7557558/vksplat` (Chen, Ibrahim & Liu, 2026; validar em Sprint 0) | Vulkan |
| Instant-NGP via Taichi | `Linyou/taichi-ngp-renderer` com backend Vulkan | Taichi/Vulkan |
| Baseline genérico de treino | PyTorch + ROCm 7.x + Nerfstudio/Nerfacto | ROCm |
| Talvez? | `ZJLi2013/tiny-rocm-nn` (renomeado/transferido de `PhysicalAI-AIM/tiny-rocm-nn`, confirmado 2026-08-06; CDNA 3/MI300X → adaptar WMMA RDNA) | HIP/WMMA |

### Métricas, operacionalizadas em 4 dimensões

**Performance**
- Tempo de treinamento até atingir PSNR-alvo (ex.: PSNR ≥ 30 dB no dataset Synthetic-NeRF; PSNR ≥ 27 dB no Mip-NeRF 360)
- FPS de inferência (renderização) em resolução 800×800 e 1920×1080
- (Opcional) throughput de operações fundamentais: GEMM FP16, hash lookup
- Reportar média e desvio padrão sobre N rodadas (N ≥ 3)

**Portabilidade**
- Tempo até conseguir configurar o pipeline (horas até primeiro treino bem-sucedido)
- Inventário de bugs/issues encontrados (linkar issues upstream relevantes)
- Cobertura de operadores PyTorch+ROCm vs CUDA (script comparando outputs dos operadores comuns ao Nerfstudio)
- Tamanho de patch necessário (LOC modificadas) sobre upstream para fazer rodar em RDNA 4
- Taxa de sucesso de instalação (instala no primeiro try? quantas tentativas?)

**Eficiência energética**
- Potência instantânea durante treinamento e inferência via amostragem `rocm-smi --showpower` (AMD) e `nvidia-smi --query-gpu=power.draw` (NVIDIA), intervalo ≤ 1 s
- Energia total por treinamento (Wh) e energia por imagem renderizada (J/frame), por integração das amostras
- Reportar potência média, pico, desvio padrão; integrar para energia
- **Restrição metodológica (2026-08-06):** como o lado NVIDIA roda em host de nuvem não-controlado, H3 limita-se a **potência de placa** (telemetria interna da GPU), nunca a energia do sistema completo; registrar também temperatura da GPU, que afeta clocks e portanto potência
- Calibrar instrumentação no Sprint 0 (validar se `rocm-smi` reporta corretamente em RDNA 4; há issues conhecidas em gerações antigas; validar também `nvidia-smi` dentro do container da vast.ai)

**Gap funcional (não-experimental, predominantemente bibliográfico + GitHub mining)**
- Tabela cronológica: técnicas relevantes 2020-2026 (NeRF, Instant-NGP, 3DGS, Mip-NeRF 360, Zip-NeRF, Nerfacto, etc.) com datas de lançamento CUDA × datas de lançamento de equivalente não-CUDA acessível, e gap em meses
- Inventário de bibliotecas: cuBLAS↔rocBLAS, cuDNN↔MIOpen, NCCL↔RCCL, tiny-cuda-nn↔(nada para RDNA), CUTLASS↔Composable Kernel, NVTX↔ROCTracer
- Análise quantitativa: número de issues abertas em `pytorch/pytorch` e `ROCm/ROCm` específicas de gfx1201 vs número total de issues; tempo médio de resolução

### Bugs ativos relevantes em PyTorch + ROCm gfx1201 (verificados em 2026-06-23; status reconfirmado em 2026-08-06 — detalhe em `bibliografia/verificacao-experimento-rdna4.md`)
- `pytorch/pytorch#177834`: LSTM/MIOpen incorreto em gfx1201 — **ainda aberto**
- `pytorch/pytorch#187343`: `expandable_segments:True` causa `hipErrorIllegalAddress` — **fechado `not_planned`** (engenheiro AMD não conseguiu reproduzir em gfx1201; não é fix confirmado)
- `pytorch/pytorch#181939`: falha CMake `gfx1036;gfx1201` — **ainda aberto**
- `ROCm/ROCm#6116`: `torch.mm` produz NaN com >~500K linhas — **fechado `completed`, mas por inatividade**; o próprio autor relatou que o bug ainda reproduz no driver 26.2.2 e só "parece resolvido" no Adrenalin 26.3.1 — tratar como mitigação de driver não confirmada, não como fix do ROCm
- `ROCm/ROCm#6374`: page fault OpenCL/ROCr em RDNA 4 (XNACK off, host-VA) — **ainda aberto**

Esses bugs são parte do achado empírico do TCC (Cap. 5, discussão de portabilidade e maturidade do stack). Apenas 1 dos 5 tem indício de mitigação, e mesmo esse é ambíguo — reforça a tese de imaturidade do stack ROCm em RDNA 4 no curto prazo (jun→ago/2026).

## 4. Cronograma: fases e marcos

| Fase | Sem | Período aprox. | Saída | Status |
|---|---|---|---|---|
| **Sprint 0: Viabilidade** | 1 | 23/jun → 30/jun/26 | Cada caminho roda ≥ 1 cena de teste; dump de versões/bugs; decisão go/no-go | Não iniciado |
| **1: Proposta + Cap. 2** | 2-6 | jul → meados ago/26 | Proposta formal validada com Prof. Gilvan; sumário ABNT; Cap. 2 escrito | Não iniciado |
| **2: Cap. 3 + datasets + métricas** | 7-8 | meados ago/26 | Cap. 3 (panorama de hardware) escrito; datasets selecionados; métricas definidas | Não iniciado |
| **3: Experimento principal** | 9-12 | fim ago → meados out/26 | Benchmarks executados; tabelas brutas em CSV/JSON no repo | Não iniciado |
| **4: Cap. 4 + Cap. 5** | 13-15 | meados out → início nov/26 | Metodologia e resultados/discussão escritos; revisão de Cap. 2-3 | Não iniciado |
| **5: Fechamento** | 16-17 | início nov → 23/nov/26 | Cap. 1, Cap. 6, resumo, revisão integral, migração LaTeX, depósito, defesa | Não iniciado |

> Janela útil de escrita/experimento: ~17 semanas. Margem para banca/correções: ~3 semanas finais embutidas no Sprint 5.

## 5. Sprints e TODOs

### Sprint 0: Viabilidade (semana 1: 23/jun → 30/jun/26)

Objetivo: validar antes de qualquer escrita que (a) os baselines existentes em ambos os lados rodam, (b) a instrumentação de medição (potência, tempo, métricas de qualidade) funciona, (c) há clareza sobre o acesso a hardware NVIDIA.

- [ ] Decidir hospedagem do repositório git (GitHub privado / GitLab UFC / só local)
- [ ] Inicializar `git init` no repositório
- [ ] Configurar Tailscale entre Mac e máquina Linux (PAUSADO a pedido do usuário em 2026-06-23; retomar antes do bring-up)
- [ ] Validar pessoalmente o paper VkSplat (arXiv:2605.00219) e o repositório `harry7557558/vksplat`
- [x] Decisão sobre hardware NVIDIA: **RTX 5070 Ti alugada na vast.ai** (decidido 2026-08-06)
- [ ] Alugar instância vast.ai de teste (5070 Ti — disponibilidade já confirmada no catálogo em 2026-08-06): registrar especificações do host (CPU, RAM, lanes PCIe, disco), validar `nvidia-smi --query-gpu=power.draw` dentro do container
- [ ] Definir critérios de seleção de instância vast.ai (PCIe x16, CPU/RAM mínimos) e fixar imagem Docker por digest para reprodutibilidade
- [ ] Bring-up (lado AMD): rodar `Linyou/taichi-ngp-renderer` em uma cena
- [ ] Bring-up (lado AMD): rodar 3DGS via PR #1297 em uma cena
- [ ] Bring-up (lado AMD): rodar VkSplat em uma cena
- [ ] Bring-up (lado AMD): PyTorch + ROCm 7.x, tutorial mínimo (treino MNIST ou similar)
- [ ] Validar instrumentação de potência: amostragem `rocm-smi --showpower` em background durante uma execução; verificar se reporta valores plausíveis em RDNA 4
- [ ] Caderno de campo: registrar cada bug/quirk encontrado em arquivo versionado no repo
- [ ] Decisão go/no-go por pipeline; ajustar escopo se necessário

### Sprint 1: Proposta + Cap. 2 (semanas 2-6: jul → meados ago/26)

Objetivo: alinhar oficialmente com o orientador e produzir o capítulo de fundamentação teórica de renderização neural.

- [ ] Reunião formal com Prof. Gilvan: validar pergunta de pesquisa (4 dimensões), hipóteses H1-H4, e o desenho de execução pareada (RX 9070 XT local × RTX 5070 Ti em nuvem) com suas ameaças de validade
- [ ] Fixar pergunta de pesquisa final + hipóteses
- [ ] Definir sumário ABNT da monografia
- [ ] Ler papers prioritários do Eixo A do fichamento (NeRF, 3DGS, Instant-NGP, métricas, surveys)
- [ ] Escrever Cap. 2: Renderização Neural (representações implícitas, explícitas, volume rendering, splatting, métricas PSNR/SSIM/LPIPS)
- [ ] Continuar leituras dos Eixos B e C em paralelo

### Sprint 2: Cap. 3 + protocolo experimental (semanas 7-8: meados ago/26)

- [ ] Ler papers do Eixo C (Taichi, ROCm, HIP, Tensor Cores, WMMA, Davis et al. 2024 sobre performance portability)
- [ ] Escrever Cap. 3: Hardware Heterogêneo e Portabilidade (CUDA vs ROCm/HIP vs Vulkan vs Taichi; Tensor Cores vs WMMA; ecossistemas de bibliotecas)
- [ ] Selecionar datasets canônicos: Synthetic-NeRF + Mip-NeRF 360 + Tanks and Temples (a confirmar com Prof. Gilvan)
- [ ] Fechar protocolo experimental: número de rodadas, hardware, versões fixadas (`requirements.txt` / Dockerfile / SHAs), critérios de PSNR-alvo, intervalo de amostragem de potência, scripts de coleta
- [ ] Construir tabela cronológica de "gap funcional" (CUDA-release → equivalente acessível); esta tabela é entregável próprio do Cap. 3 ou Cap. 5
- [ ] Construir inventário de paridade de bibliotecas CUDA ↔ ROCm

### Sprint 3: Experimento principal (semanas 9-12: fim ago → meados out/26)

- [ ] **Lado AMD (todos):** executar 3DGS (PR #1297, VkSplat) e Instant-NGP (taichi-ngp-renderer) nos datasets selecionados, com rodadas para média/desvio
- [ ] **Lado AMD:** executar baseline PyTorch + ROCm em 1-2 tarefas comparáveis para complementar
- [ ] **Lado NVIDIA (RTX 5070 Ti, vast.ai):** executar Instant-NGP oficial e 3DGS oficial nos mesmos datasets, mesma instrumentação, mesmos critérios; registrar especificações do host e digest da imagem para cada sessão de aluguel
- [ ] **Lado NVIDIA:** rodar as N rodadas de um mesmo experimento **na mesma instância** (evita confundir variância de host com variância de execução); repetir um subconjunto em uma segunda instância para estimar a variância entre hosts
- [ ] Complementar com números publicados na literatura onde a execução pareada não cobrir (explicitar no texto quais comparações são pareadas e quais são indiretas)
- [ ] Coletar métricas em formato versionável (CSV/JSON) no repo: tempo, FPS, PSNR, SSIM, LPIPS, potência amostrada, energia integrada
- [ ] Documentar cada bug/regressão de correção encontrado como achado empírico do Cap. 5

### Sprint 4: Cap. 4 + Cap. 5 + revisão (semanas 13-15: meados out → início nov/26)

- [ ] Escrever Cap. 4: Metodologia (protocolo, datasets, métricas, instrumentação, limitações)
- [ ] Escrever Cap. 5: Resultados e Discussão, estruturada nas 4 dimensões (performance, portabilidade, energia, gap funcional)
- [ ] Revisar Cap. 2 e Cap. 3 à luz dos resultados

### Sprint 5: Fechamento (semanas 16-17: início nov → 23/nov/26)

- [ ] Escrever Cap. 1: Introdução (motivação, objetivo, contribuições)
- [ ] Escrever Cap. 6: Conclusão (síntese, trabalhos futuros)
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
| 2026-06-23 | Caminho experimental: 3DGS via PR #1297 + VkSplat (Vulkan), Instant-NGP via taichi-ngp-renderer, baseline PyTorch+ROCm | Verificação de fontes primárias confirma viabilidade; tiny-cuda-nn AMD direto não é viável (CDNA-only) |
| 2026-06-23 | **Reformulação do escopo: TCC é análise comparativa CUDA × não-CUDA, não trabalho de portabilidade própria** | VkSplat e Linyou/taichi-ngp-renderer já fornecem implementações não-CUDA, então o foco move-se para medição e comparação nas 4 dimensões (performance, portabilidade, energia, gap funcional) |
| 2026-08-06 | Re-verificação de fontes primárias (após perda da memória `reference_experimento_rdna4.md` em reinstall) confirma viabilidade geral, mas rebaixa a confiança no VkSplat e no PR #1297 como baselines "prontos" | PR #1297 está parado há ~8 meses sem atividade; VkSplat ainda não foi testado pelos autores em RDNA 4 (só até RDNA 3) e o paper está "submitted", não aceito em Eurographics 2026 — ver `bibliografia/verificacao-experimento-rdna4.md` |
| 2026-08-06 | **Lado CUDA será executado em RTX 5070 Ti alugada na vast.ai** (resolve o bloqueante de hardware NVIDIA) | Custo baixo viabiliza execução pareada CUDA × não-CUDA nos mesmos datasets e protocolo, em vez de comparação indireta com números de papers; RTX 5070 Ti é a concorrente direta de mercado da RX 9070 XT (mesma geração, mesma faixa de preço/TDP), o que fortalece a comparabilidade. Introduz ameaças de validade próprias do ambiente de nuvem — ver §8 |

## 7. Decisões pendentes

- [x] ~~**BLOQUEANTE: acesso a hardware NVIDIA contemporâneo**~~ **RESOLVIDO em 2026-08-06:** RTX 5070 Ti alugada na vast.ai; disponibilidade no catálogo confirmada pelo aluno em 2026-08-06. Pendências derivadas (ver §8): (a) validar que `nvidia-smi --query-gpu=power.draw` funciona no container alugado; (b) definir critérios de seleção de instância (PCIe x16, CPU/RAM adequados) para não confundir H1; (c) decidir como tratar a métrica "tempo até bring-up" dada a imagem Docker pré-construída
- [ ] Hospedagem do repositório git: GitHub privado / GitLab UFC / só local
- [ ] Confirmação com Prof. Gilvan: pergunta de pesquisa reformulada (4 dimensões) e hipóteses H1-H4
- [ ] Datasets finais: Synthetic-NeRF + Mip-NeRF 360 + Tanks and Temples? Outro?
- [ ] Energia: confirmar instrumentação no Sprint 0. O `rocm-smi --showpower` reporta corretamente em RDNA 4? Caso contrário, plano B (medidor externo de tomada para potência total da workstation, ou outro método)
- [x] Validação bibliográfica do paper/repo VkSplat (arXiv:2605.00219) — confirmado real e ativo em 2026-08-06 (ver `bibliografia/verificacao-experimento-rdna4.md`); **pendente:** bring-up prático na RX 9070 XT, já que os autores só testaram até RDNA 3 (RX 7800 XT) e o paper ainda está "submitted" (não aceito) em Eurographics 2026

## 8. Riscos e ameaças à validade

| Risco | Impacto | Mitigação |
|---|---|---|
| ~~**Sem hardware NVIDIA**~~ **RESOLVIDO (2026-08-06):** lado CUDA em RTX 5070 Ti alugada na vast.ai | — | Execução pareada agora é possível; riscos residuais nas 4 linhas seguintes |
| **Energia (H3) em ambiente de nuvem não-controlado:** o lado AMD roda na sua bancada (temperatura, gabinete, refrigeração conhecidos), o lado NVIDIA num host desconhecido | Comparação de energia system-level fica indefensável; até a potência de placa sofre efeito indireto de temperatura ambiente sobre clocks/ventoinha | Restringir H3 explicitamente a **potência de placa** (telemetria interna da GPU via `nvidia-smi`/`rocm-smi`), nunca energia do sistema; registrar temperatura da GPU junto da potência; declarar a limitação no Cap. 4 |
| **Variância de host da vast.ai confunde H1:** instâncias variam em CPU, RAM, lanes PCIe (rigs de mineração com riser x1/x4 são comuns) e disco — e treino de NeRF/3DGS tem componente real de CPU/IO | Um host fraco faz o lado NVIDIA parecer artificialmente lento, invalidando a comparação de performance | Filtrar instâncias por PCIe x16 + CPU/RAM adequados; registrar especificações do host de cada sessão; rodar as N repetições na mesma instância; repetir subconjunto em segundo host para medir variância entre hosts |
| **"Tempo até bring-up" deixa de ser comparável:** a vast.ai entrega imagem Docker com CUDA+PyTorch pré-construídos (setup ≈ 0 por construção), contra instalação ROCm do zero no Ubuntu | A dimensão de portabilidade favoreceria CUDA por artefato do provedor, não por mérito técnico | Escolher uma das opções e declarar: (a) medir bring-up a partir de imagem base limpa nos dois lados, (b) abandonar tempo-de-bring-up e manter tamanho de patch + contagem de bugs como proxies de portabilidade, ou (c) reportar com ressalva explícita |
| **Instância da vast.ai é efêmera:** desaparece ao ser liberada | Resultados não reproduzíveis se o ambiente não for capturado | Snapshot obrigatório por sessão: versão de driver, CUDA, digest da imagem Docker, CPU/RAM/PCIe do host, `nvidia-smi -q` completo |
| Bugs ativos em PyTorch+ROCm RDNA 4 | Resultados podem incluir falhas de correção, não só de desempenho | Documentar como achado empírico; reportar issue upstream se inédito |
| PR #1297 do 3DGS é rascunho da comunidade, **parado há ~8 meses sem atividade** (confirmado 2026-08-06) | Pode regressar, exigir patch local, ou já estar desatualizado contra o `main` upstream | Forkar e fixar commit; documentar versões usadas; testar cedo no Sprint 0 para não descobrir problemas tarde |
| VkSplat confirmado real (paper+repo existem e estão ativos), mas **não testado em RDNA 4 pelos autores** (só até RDNA 3) e paper ainda "submitted", não aceito em Eurographics 2026 | Baseline-chave do lado Vulkan pode não funcionar de primeira em RDNA 4; bring-up na 9070 XT passa a ser validação original, não replicação de resultado já demonstrado no mesmo hardware | Bring-up continua sendo a primeira tarefa prática do Sprint 0; não citar como "aceito" em Eurographics até confirmação |
| `rocm-smi --showpower` pode não reportar corretamente em RDNA 4 | H3 (energia) fica comprometida | Validar no Sprint 0; plano B com medidor externo de tomada |
| Janela de 5 meses é apertada | Escopo pode estourar | Sprint 0 com decisão go/no-go por pipeline; permitir cortar tiny-rocm-nn sem perder o TCC |
| Mudanças de versão ROCm/PyTorch durante o experimento | Resultados não-reprodutíveis | Fixar versões com `requirements.txt` / Dockerfile; registrar SHA |
| Bibliografia "estava na cabeça" e ainda precisa ser fichada | Atraso no Cap. 2 | Fichamento em `bibliografia/fichamento.md` (~50 entradas). O aluno deve ler os papers prioritários listados ao final do fichamento |
| Comparativos cross-paper entre CUDA e ROCm são frágeis | Conclusões da H1 ficam fracas se não houver execução pareada | **Mitigado em 2026-08-06:** o aluguel da 5070 Ti na vast.ai permite execução pareada (mesmos datasets, protocolo e instrumentação nos dois lados). Onde ainda houver comparação indireta com literatura, marcar explicitamente como tal |

### Ressalvas diferidas para o momento da execução (registrado em 2026-08-06)

As duas ressalvas metodológicas abaixo são **decisões diferidas**, não pendências bloqueantes. Ficam registradas aqui para serem retomadas quando o experimento for de fato executado (Sprint 2 para o protocolo, Sprint 3 para a execução). Postura definida pelo aluno: **se não houver alternativa viável, a ressalva pode ser abandonada — declarando a limitação honestamente no texto — em vez de descartar a dimensão de medição.**

1. **Energia (H3) em host de nuvem não-controlado.** Plano atual: restringir a potência de placa e registrar temperatura. Se a instrumentação na vast.ai não permitir nem isso de forma confiável, a alternativa é reduzir H3 a uma análise qualitativa/bibliográfica, ou removê-la das hipóteses testadas — decidir com o Prof. Gilvan, não silenciosamente.
2. **Métrica "tempo até bring-up" viciada pela imagem Docker pré-construída.** Três saídas registradas na tabela acima. Se nenhuma for praticável, a métrica sai da dimensão de portabilidade e o peso migra para tamanho de patch + contagem de bugs upstream, com a exclusão justificada no Cap. 4.



- Repositório local existe; git ainda não inicializado
- Material de partida: 3 PDFs exploratórios na raiz (números a tratar com cautela)
- Domínios liberados no sandbox: `www.google.com`, `rocm.docs.amd.com`, `github.com`, `api.github.com`, `www.amd.com`, `arxiv.org`, `pytorch.org`, `docs.taichi-lang.org`, `raw.githubusercontent.com`, `phoronix.com`, `pypi.org`
- Verificação de viabilidade do experimento concluída (2026-06-23) e reconfirmada em fontes primárias (2026-08-06); ver `bibliografia/verificacao-experimento-rdna4.md` (a memória `reference_experimento_rdna4.md` foi perdida em reinstall do Claude — este arquivo no repositório é agora a fonte de verdade, versionada em git)
- Fichamento bibliográfico: em construção (`bibliografia/fichamento.md`)
- Tailscale: pausado a pedido do usuário; retomar antes do Sprint 0

## 10. Materiais e localização

- `CLAUDE.md`: papel do Claude, convenções, escopo confirmado
- `PLANO.md`: este arquivo
- `bibliografia/fichamento.md`: revisão bibliográfica do estado da arte (em construção)
- `bibliografia/verificacao-experimento-rdna4.md`: log de verificação de viabilidade do experimento (fonte de verdade, versionado — substitui a memória `reference_experimento_rdna4.md`, perdida em reinstall)
- 3 PDFs iniciais na raiz (material exploratório, não usar como fonte direta sem validar)
- Memórias persistentes em `~/.claude/projects/-Users-fabiogomes-code-tcc/memory/` (agora contêm apenas ponteiros/resumos curtos, não fatos brutos — os fatos vivem no repositório)
