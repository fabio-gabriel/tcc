# Pré-registro do protocolo experimental

> **Status: ESTÁGIO 1 COMMITADO E VÁLIDO** para os degraus D0, D1, D2 e D3.
> **Estágio 2 (degrau D4) permanece rascunho** — ver §0.1.
>
> Este documento existe para que o histórico do git prove que o protocolo, os limiares e os critérios de refutação foram fixados **antes** de qualquer execução medida. Para os degraus cobertos pelo estágio 1, alterações só são legítimas como **desvio declarado** — entrada nova, datada, com justificativa, jamais edição silenciosa.
>
> Fundamentação em `PLANO.md` §2 (hipóteses) e §3.5 (plano estatístico). Em divergência, este documento prevalece quanto ao protocolo; o `PLANO.md` prevalece quanto ao enquadramento.

## 0. Pendências que bloqueiam a validação deste pré-registro

- [x] ~~**Auditoria da reordenação Morton**~~ **RESOLVIDA em 2026-09-02, e o resultado mudou a escada.** A reordenação **não é determinística**: a fase `ComputeStats` de `slang/morton_sort.slang:58-70` tem **6 sítios próprios de `InterlockedAddF32`**, calculando média e variância das posições por redução entre workgroups sem ordem imposta. Consequência direta: **a intervenção apenas no backward não pode produzir execuções bit-idênticas**, e H3a na formulação anterior nasceria refutada. Ver §3.1, agora com **cinco** degraus.
- [x] ~~**Decisão sobre referência ao fork**~~ **RESOLVIDA em 2026-09-02:** dois repositórios independentes, com a referência fixada pela tabela de SHAs de §3.1 e, redundantemente, pelo `env.json` de cada execução. Submódulo descartado por atrito desproporcional ao benefício, dado que a rastreabilidade já vem por duas vias.
- [x] ~~**Política de retenção**~~ **RESOLVIDA em 2026-09-02:** partição extensível a ~500 GB mais 5 TB em nuvem. Retenção integral, sem condicional. Ver §7.
- [ ] **SHAs dos commits D1, D2 e D3** — patches de 1 a 2 linhas, criáveis imediatamente. Transcrever em §3.1.
- [ ] **Toolchain Slang** (`slang-2026.2.1`), pré-requisito de D4: os `.spv` vêm pré-compilados no repositório, logo alterar `.slang` exige `compile_shaders.py` a partir da raiz do repo. Não está em apt. **Baixar antes da semana de D4, não durante.**
- [ ] **Parâmetros de D4** (bits fracionários, faixa dinâmica, saturação) em adendo datado, após a medição de magnitude típica dos gradientes e **antes** da execução de D4.
- [ ] Registrar o tamanho real do `splat.ply` de uma execução ADC, para o inventário de dados (não é mais restrição de espaço).

### 0.1 Pré-registro em estágios

Este documento é commitado **em estágios**, e cada estágio precede as execuções que governa:

| Estágio | Conteúdo | Pode ser commitado |
|---|---|---|
| **1** | Protocolo completo para **D0, D1, D2, D3** — configuração, grandezas, plano estatístico, critérios de refutação | **agora** |
| **2** | Adendo com os parâmetros de D4 e o SHA do commit E | antes da execução de D4 |

Nenhum estágio pode ser alterado depois de iniciadas as execuções que ele governa. Alterações posteriores entram como **desvio declarado** — entrada nova, datada, com justificativa. Este faseamento é legítimo porque cada degrau é uma série independente; não é licença para ajustar D0–D3 depois de vê-los.

## 1. Identificação

| Campo | Valor |
|---|---|
| Data de redação | 2026-09-02 |
| Trabalho | TCC — Reprodutibilidade em treino de 3D Gaussian Splatting |
| Repositório do TCC | `github.com/fabio-gabriel/tcc`, branch `main` (privado) |
| Fork do código experimental | **`github.com/fabio-gabriel/vksplatTCC`**, branch **`tcc-base`** |
| Upstream do fork | `github.com/harry7557558/vksplat`, base no commit `b3ad2b048918496616e0e9346e35c606d813ab55` |
| Licença do upstream | Apache-2.0 — modificação e redistribuição com atribuição são permitidas |
| **Commit que introduziu este protocolo** | **`f02183b`** — 2026-09-08T21:57:51-03:00 |
| Alcançou o remoto em | `2934c03` (merge), 2026-09-08T22:01:22-03:00 |

> **CORREÇÃO (2026-09-08) — leia antes de citar qualquer commit deste pré-registro.**
>
> Uma versão anterior desta seção afirmava que "o estágio 1 do pré-registro foi commitado como `879dc87`, em 2026-09-02". **As duas informações estavam erradas.** Verificado no histórico:
>
> | Commit | Data | Conteúdo real |
> |---|---|---|
> | `879dc87` | 2026-09-04T19:31 | **apenas `run_degree.sh`**, 18 linhas. **Não contém o pré-registro.** |
> | `f02183b` | 2026-09-08T21:57 | cria `pre-registro.md` com o protocolo completo e os quatro SHAs de §3.1; atualiza o caderno de campo; cria a versão vigente do `run_degree.sh` |
> | `2934c03` | 2026-09-08T22:01 | merge que integra os dois e leva `f02183b` ao remoto |
>
> Origem do erro: o SHA `879dc87` foi informado como sendo o do pré-registro e aceito sem inspecionar o commit. É o mesmo padrão do episódio da matriz do ROCm em 2026-08-25 — afirmação registrada sem verificação da fonte primária, sendo que `git show 879dc87 --stat` a desmentiria em segundos.
>
> **A prioridade do pré-registro está intacta, e isto é o que importa:** nenhuma execução medida ocorreu. As execuções de 2026-09-01 (bring-up) e a de 2026-09-08 (validação de encanamento) estão declaradas como tais no caderno de campo e **não** são dados do experimento. A primeira execução medida é a série D0, ainda não iniciada. Portanto o protocolo continua fixado *antes* dos dados, que é a única propriedade que o pré-registro precisa ter.
>
> **Referência vinculante:** o conteúdo protocolar é o de **`f02183b`**, verificável por `git show f02183b:pivo-reprodutibilidade-3dgs/pre-registro.md`. Alterações posteriores a ele são inspecionáveis por `git diff f02183b HEAD -- pivo-reprodutibilidade-3dgs/pre-registro.md` e, até 2026-09-08, consistem apenas desta correção. A validade vem do histórico do git, não de um campo dentro do arquivo — um arquivo não pode conter o hash do commit que o contém.

## 2. Ambiente, fixado

Descrito conforme a Rule 9 de Hoefler e Belli. Registrado por execução em `env.json`; o inventário completo está em `../experimentos/00-inventario/saidas/`.

| Item | Valor |
|---|---|
| Host | `fabio-desktop` |
| CPU | AMD Ryzen 7 5700X (8C/16T) |
| RAM | 15 GiB |
| GPU | AMD Radeon RX 9070 XT, RDNA 4, `gfx1201`, 16 GB |
| SO | Ubuntu 24.04.4 LTS |
| Kernel | `7.0.0-30-generic` (HWE) |
| Driver Vulkan | RADV, Mesa 25.2.8; loader de instância 1.3.275; device `apiVersion` 1.4.318 |
| Backend do compilador de shaders | **ACO** (padrão). `RADV_DEBUG=llvm` **não** deve estar definido |
| `subgroupSize` do dispositivo | 64; o VkSplat exige 32 via `VK_EXT_subgroup_size_control` (`SUBGROUP_SIZE 32` em `src/config.h:8`) |
| Atômicas em float | `shaderBufferFloat32AtomicAdd` **nativo**, confirmado; `USE_EMULATED_F32_ATOMIC` **não** acionado |
| Python | 3.12.3, em venv `~/code/tcc/.venv` |
| PyTorch | build de CPU (índice `download.pytorch.org/whl/cpu`) — usado só na avaliação |
| Dispositivo de treino | `TRAIN_DEVICE = 0`. **Nunca `-1`.** Execução com `deviceName` diferente de `AMD Radeon RX 9070 XT (RADV GFX1201)` é descartada |

**Não fixável, portanto declarado como não controlado:** carga de fundo da máquina, temperatura, e estados de energia da GPU. Consequência aceita: afeta as latências medidas e, por meio delas, o escalonador de kernels nos degraus D0 e D1 (ver §3).

## 3. Configuração experimental

| Parâmetro | Valor | Origem |
|---|---|---|
| Dataset | Mip-NeRF 360, `360_v2.zip`, SHA a registrar | `storage.googleapis.com/gresearch/refraw360/360_v2.zip` |
| Cena | **`garden`** | — |
| Resolução | **`images_4`** (JPEG, como distribuído) | — |
| Densificação | **`TrainerConfig`** — ADC original do Inria | `simple_trainer.py` |
| `train_steps` | **30000** | padrão |
| `eval_interval` | 8 → 161 treino / 24 validação | padrão |
| Demais hiperparâmetros | **padrão de `TrainerConfig`, sem alteração** | — |

**Justificativa da escolha de ADC sobre MCMC**, registrada antes da execução: na ADC as decisões de `dupli`/`split`/`prune` são comparações de limiar sobre gradientes (`grow_grad2d = 0.0002`, `prune_opa = 0.005`). Uma diferença numérica ínfima na acumulação atômica pode inverter uma comparação, mudando discretamente o número de primitivas — o que dá um **segundo canal de evidência, discreto e macroscópico**, além das métricas de imagem. A MCMC com `cap_max` suprime esse canal por construção, ao fixar a contagem final. Ver `../experimentos/caderno-de-campo.md`, entrada de 2026-09-01.

### 3.1 A escada de ablação — cinco degraus

Reformulada em 2026-09-02, após a auditoria da reordenação Morton. Cada degrau é uma configuração distinta, medida independentemente. Os patches são **cumulativos** e cada um vive em um commit próprio e identificável do fork.

| Degrau | Intervenção | Fonte de não-determinismo eliminada | Rebuild | SHA |
|---|---|---|---|---|
| **D0** | nenhuma ablação — código como distribuído, mais o harness | — (baseline; todas as fontes ativas) | não | **`3a5c0d97a6790e07ebd011a116d4d016c957ab9f`** |
| **D1** | descomentar `random.seed(step)` em `vksplat/simple_trainer.py`, no laço de embaralhamento | ordem de visitação das imagens de treino | não (Python) | **`4cb921a82f686c68578978bdeb215057935ae048`** |
| **D2** | `RASTERIZE_BACKWARD_USE_SCHEDULING 0` em `vksplat/src/config.h:24` | seleção de kernel de backward por latência medida — fixa `PerSplat` | **sim** (C++) | **`b395759efaeff12846aca49af1e8c9ca1aab02ac`** |
| **D3** | `#if 1` → `#if 0` em `vksplat/src/gs_trainer.cpp`, nas **duas** chamadas a `executeMortonSorting` | **reordenação Morton periódica** — remove os 6 sítios de `InterlockedAddF32` de `ComputeStats` e a variabilidade de permutação | **sim** (C++) | **`d222c47182f5917be0cc209f19d3257e1ebad17e`** |
| **D4** | acumulação em ponto fixo com atômicos inteiros nos **9 sítios** de `_ATOMIC_ADD` de `vksplat/slang/alphablend_shader_bwd_per_splat.slang:191-199` | acumulação `float32` não-associativa no backward de rasterização | **sim** (shader + C++) | *estágio 2* |

Todos na branch `tcc-base` do fork, em cadeia linear a partir de `b3ad2b0`. O commit de D0 contém **apenas** `vksplat/tcc_runner.py` e `run_series.sh` — harness e checagens de invalidação, nenhuma alteração de comportamento do treino. É por isso que ele é o estado de referência.

### 3.2 Procedimento de execução, e a armadilha do binário obsoleto

**O módulo compilado (`vksplat.cpython-*.so`) não está no git** — é coberto por `*.so` no `.gitignore`. Consequência crítica: **`git checkout` de outro degrau NÃO troca o binário.** Trocar de D1 para D2 sem recompilar executa o código C++ de D1 com o rótulo de D2, e **nada no `env.json` denunciaria isso**, porque o SHA registrado seria o de D2.

Esse é o modo de falha mais perigoso de todo o protocolo: silencioso, plausível, e invalidaria uma série inteira sem deixar rastro nos dados.

**Mitigação obrigatória:** a execução de cada degrau é orquestrada por script que faz `checkout`, **recompila incondicionalmente**, e só então roda a série. A recompilação é incondicional mesmo nos degraus que "não precisam" — o custo é de cerca de um minuto e elimina a classe de erro inteira.

```
git checkout <tag do degrau>
pip install -e . --no-build-isolation      # sempre, sem exceção
bash run_series.sh <degrau> <N>
```

O orquestrador vive no **repositório do TCC**, não no fork, porque é camada acima da escada e não pertence ao estado de código de nenhum degrau.

O orquestrador aborta a série se o log não contiver `Using device [0]`, se a GPU esperada não for enumerada como `VIABLE`, ou se aparecer qualquer menção a `USE_EMULATED` — implementando em código os critérios de §9.

> **Desvio declarado (2026-09-02, antes de qualquer execução medida).** O laço de repetição foi movido de `run_series.sh` — que está no fork, dentro do commit de D0 — para `run_degree.sh`, no repositório do TCC. Motivo: o redirecionamento interno do `run_series.sh` deixava o terminal sem saída durante os ~15 min de cada execução, tornando progresso indistinguível de travamento. O novo orquestrador usa `tee`, mostrando a saída ao vivo e gravando o log ao mesmo tempo.
>
> **O que mudou:** apenas quem executa o laço e como a saída é apresentada.
> **O que não mudou:** o `tcc_runner.py` — que fixa dispositivo e configuração e grava o `env.json` — é bit-idêntico e permanece no fork; e as **três checagens de invalidação são preservadas literalmente**. Nenhum estado de código de degrau foi alterado, e os SHAs de §3.1 seguem válidos.
> **Consequência a declarar:** o `run_series.sh` presente no commit de D0 passa a ser código não utilizado. Não foi removido, porque removê-lo alteraria o commit de D0.

**Por que D3 vem antes de D4.** A auditoria de 2026-09-02 estabeleceu que `morton_sort.slang`, fase `ComputeStats`, acumula média e variância das posições com `InterlockedAddF32` entre workgroups, sem ordem imposta. O mecanismo de amplificação é uma **função degrau**: `pos_mean`/`pos_stdp` diferindo no último bit alteram a posição normalizada, e a quantização `uint32_t(pos.x * (float)(1 << 10) + 0.5f)` faz qualquer gaussiana próxima de fronteira de voxel cair em célula vizinha — chave Morton diferente, **permutação diferente do array inteiro**. Como a permutação remapeia os `splat_id` de destino das atômicas do backward, ela altera o padrão de colisão dessas atômicas. Logo é fonte **independente e a montante**, e intervir só no backward não produziria execuções bit-idênticas.

**Ordem de determinismo verificada, para o registro.** São determinísticos, dada a mesma entrada: o radix sort (ranking por ballot com desempate pelo índice anterior, atômicos apenas inteiros); a compactação de poda da ADC (prefix-sum inteiro, estável); o apêndice de dupli/split; a densificação MCMC (atômicos inteiros de contagem, índices por função pura de `seed` e `tid`); e o RNG de GPU, *counter-based*, semeado a partir de `rng.seed(42)` em `gs_trainer.cpp:127`.

**Inventário completo de atômicas em `float32` no shader tree** (varredura dos 18 arquivos de `slang/` no commit fixado): 9 sítios em `alphablend_shader_bwd_per_splat.slang`, 9 em `alphablend_shader_bwd_per_pixel.slang`, 9 em `alphablend_shader_bwd_tensor.slang`, e 6 em `morton_sort.slang`. **`ssim.slang` e `utils.slang` não têm nenhuma.**

**Dependência entre D2 e D4, a declarar.** Há três variantes de backward, cada uma com seus 9 sítios. Em AMD, o escalonador alterna entre `PerSplat` e `Tensor_0_8_8`. O patch de D4 cobre **apenas** a variante `PerSplat`, o que é suficiente **porque D2 é cumulativo e fixa essa variante**. Se D2 fosse removido, D4 estaria incompleto. Isto é propriedade do desenho cumulativo, não descuido.

**Observação sobre o alcance temporal do Morton.** A condição de execução (`step % config.refine_every == 0`) é mais frouxa que a da densificação: roda também antes de `refine_start_iter` e inclusive em `step == 0`. Na estratégia ADC há `return` antecipado em `step >= refine_stop_iter` que curto-circuita o Morton; na MCMC não há, e ele roda até o fim do treino. Coerente com a observação de que a densificação ADC cessa por volta do passo 15.000.

**Parâmetros de D4 a fixar antes de sua execução, em adendo datado:** número de bits fracionários, faixa dinâmica assumida para os gradientes, e comportamento em saturação. Esses valores **não** podem ser escolhidos após observar a dispersão de D0–D3.

**Configuração secundária, opcional:** D0 com `MCMCTrainerConfig` (`cap_max = 1000000`), mesmo N, para testar se fixar a contagem de gaussianas suprime ou apenas oculta a dispersão. Custo ≈ 3 h. Se executada, é reportada separadamente e **não** entra na análise principal. Nota: na MCMC o Morton roda até o fim do treino, ao contrário da ADC.

## 4. Grandezas medidas e registradas, por execução

Nenhuma métrica pode ser adicionada à análise após a coleta sem constar como desvio declarado.

**Primárias**

- PSNR, SSIM, LPIPS-VGG e LPIPS-Alex, em **precisão total do `eval.json`** (não os valores arredondados do stdout), média sobre as 24 imagens de validação.
- **Número final de gaussianas** (`num_splats`).

**Secundárias**

- Hash criptográfico do `splat.ply`, para teste de identidade bit a bit.
- Distribuição das diferenças por parâmetro entre pares de execuções: posição, escala, opacidade, rotação e coeficientes SH.
- `time_elapsed`; `breakdown` por estágio; `vram` e `peak_vram`.
- **Contagens de `_RasterizeBackwardScheduling_PerSplat` e `_Tensor_0_8_8`** — quantificam a contaminação do escalonador em D0 e D1.
- Sequência das 144 linhas de densificação (`N dupli, N split, N prune -> N splats`), para observar onde as trajetórias divergem.

**De ambiente**, em `env.json`: `deviceName`, índice do dispositivo, `subgroupSize` efetivo, SHA do fork, estado limpo/sujo da árvore, kernel, versões, variáveis de ambiente relevantes.

## 5. Plano estatístico, fixado

Conforme `PLANO.md` §3.5. **Não-paramétrico por decisão a priori**, porque Hoefler e Belli registram que N de 30–40 é insuficiente para invocar o Teorema Central do Limite e que normalidade é raramente observada em medição de computador.

| Item | Valor fixado |
|---|---|
| Tendência central | mediana |
| Dispersão reportada | Q1, Q3, mínimo, máximo, amplitude (max − min), IQR |
| Intervalo de confiança | CI 95% não-paramétrico da mediana, pela fórmula de rank de Le Boudec citada por Hoefler e Belli |
| Nível de confiança | **α = 0,05** |
| Diagnóstico de normalidade | Shapiro-Wilk + Q-Q plot, em apêndice, apenas para documentar que a suposição foi checada |
| Outliers | **não remover.** Se inevitável: Tukey 1,5×IQR, com o número de removidos reportado por experimento |
| Comparação entre degraus | ~~CIs não sobrepostos; Kruskal-Wallis; tamanho de efeito~~ **CORRIGIDO — ver §5.2** |
| Agregação entre cenas | **não se aplica** — uma cena, e por decisão não se agrega PSNR em dB entre cenas |

### 5.2 Desvio declarado — teste de comparação entre degraus

**Data: 2026-09-09. Especificado ANTES de ser computado; a ordem é verificável no histórico do git.**

**O erro.** O plano estatístico original mandava comparar degraus por **intervalos de confiança da mediana não sobrepostos** e por **Kruskal-Wallis**. Ambos testam **localização** — se as medianas diferem. Mas H3.1 a H3.4 não afirmam nada sobre localização: afirmam que a **dispersão** diminui de um degrau para o seguinte. Os testes especificados são, em princípio, incapazes de estabelecer a afirmação que o trabalho faz, e nenhum aumento de N corrige isso. É erro de especificação, não de execução.

**Confirmação empírica de que a mediana não é o canal relevante:** em N=20, as medianas dos degraus D0, D1 e D2 ficam entre 27,3614 e 27,3849 dB — variação de 0,023 dB, dentro da própria dispersão intra-degrau — enquanto os IQRs vão de 0,0331 a 0,0507. As intervenções mexem em escala, não em posição.

**Substituição, fixada aqui antes de qualquer cálculo:**

| Item | Decisão |
|---|---|
| Teste de homogeneidade de escala | **Fligner-Killeen**, não-paramétrico e robusto a não-normalidade, sobre os quatro (ou cinco) degraus e também par a par |
| Estimativa de efeito | **IC 95% bootstrap percentílico sobre a razão de IQRs** entre degraus consecutivos, com 10.000 reamostragens |
| Estatística descritiva de dispersão | IQR como principal; amplitude e desvio absoluto mediano (MAD) como secundários |
| Nível | α = 0,05, inalterado |
| Critério de H3.x | a hipótese do degrau é **sustentada** se Fligner-Killeen rejeitar homogeneidade **e** o IC bootstrap da razão de IQRs excluir 1,0 na direção de redução; **refutada** caso contrário |

**Ressalva de ancoragem:** o *bootstrap* **não** pode ser justificado por Hoefler e Belli, que o exclui explicitamente do escopo (*"More advanced statistical techniques such as bootstrap are beyond the scope of our work"*). A justificativa metodológica vem de Efron e Tibshirani, e a referência precisa ser adicionada ao fichamento antes do Cap. 4.

**Honestidade sobre a força deste desvio.** Este teste é especificado após a coleta de D0–D3 em N=10 e de D0–D2 em N=20, e depois de eu ter observado as estatísticas descritivas de dispersão dessas séries. Não foi computado nenhum teste de escala antes desta especificação. Ainda assim, isto é **mais fraco** que um pré-registro limpo, e a monografia deve declarar exatamente isso — inclusive que a direção esperada do efeito já era conhecida quando o teste foi escolhido. Registrar a limitação é o que a torna tolerável; omiti-la seria o problema.

### 5.1 Regra de parada e N

- **`N_min` = 10** (Hoefler e Belli: n > 5 para CI não-paramétrico).
- **`k` = 10** — reavaliação do CI a cada 10 execuções.
- **`N_max` = 50** por degrau.
- **Largura-alvo:** CI 95% da mediana de PSNR com largura **≤ 0,02 dB**, isto é, um quinto do limiar de relevância de H2.
- **Parada:** ao atingir a largura-alvo em uma reavaliação, ou ao atingir `N_max`. Se `N_max` for atingido sem a largura-alvo, **isso é reportado como resultado**, não corrigido com execuções extra.

Custo previsto: **5 degraus** × até 50 execuções × ~15 min ≈ **até 62 h de máquina**.

> **Declaração exigida pela natureza sequencial do critério.** Parada adaptativa é decisão dependente dos dados, e só é legítima porque α, `k`, `N_min`, `N_max` e a largura-alvo estão fixados **aqui**, antes da primeira execução medida. Alterar qualquer um deles depois de observar resultados invalida o eixo 1.

## 6. Critérios de refutação, fixados

**H1 — existe não-determinismo detectável.**
Refutada se, em D0, as N execuções produzirem `splat.ply` de **hash idêntico** e PSNR idêntico na precisão do `eval.json`.

**H2 — a dispersão é metodologicamente relevante.**
Limiar de relevância: **0,10 dB de PSNR**, fixado a partir do levantamento de 2026-08-26 (`PLANO.md` §2.3), em que trabalhos de sistemas e eficiência sobre Mip-NeRF 360 reportam ganhos de 0,03 a 0,20 dB — gsplat declara paridade com +0,05 dB e apresenta features de +0,03, +0,11 e +0,18 dB; Mip-Splatting reporta +0,09 dB contra o próprio 3DGS retreinado.

**Estatística de teste, escolhida a priori: a fração de pares de execuções cuja diferença de PSNR é ≥ 0,10 dB.** Sobre as $\binom{N}{2}$ combinações de D0.
- **H2 sustentada** se essa fração for ≥ 5%.
- **H2 refutada** se for < 5%.

Razão de escolher a fração de pares em vez da amplitude: a **amplitude cresce com N** e não é estimador estável, logo não admite limiar fixo sob N variável. A fração de pares é robusta a N e traduz diretamente a afirmação de interesse — *"uma comparação de rodada única, no magnitude que a área publica, pode ser ruído"*. Amplitude e IQR seguem sendo reportados, como descritivos.

**H3 — atribuição das fontes de não-determinismo.** Desdobrada em quatro afirmações, uma por degrau, cada uma com refutação própria. Todas comparam a dispersão do degrau contra a do degrau anterior pelo critério de §5.

- **H3.1** — semear a ordem de visitação das imagens (D1) reduz a dispersão em relação a D0. *Refutada se* indistinguível de D0.
- **H3.2** — fixar o kernel de backward (D2) reduz a dispersão em relação a D1. *Refutada se* indistinguível de D1. Expectativa registrada: efeito pequeno, porque a contaminação medida é de ~1,8% dos passos.
- **H3.3** — desativar a reordenação Morton (D3) reduz a dispersão em relação a D2. *Refutada se* indistinguível de D2. **Esta é a hipótese nova, criada pela auditoria de 2026-09-02**, e nenhum trabalho localizado a considera.
- **H3.4** — tornar associativa a acumulação do backward (D4) elimina a dispersão: as N execuções produzem `splat.ply` de **hash idêntico**. *Refutada se* a dispersão persistir — o que indicaria fonte adicional não identificada e passaria a ser o achado.

**Ordem de magnitude não é pré-registrada para H3.1–H3.4.** O pré-registro fixa o *sinal* (redução) e o *critério de comparação*, não a magnitude — coerente com a regra do `PLANO.md` §2 de declarar mecanismo e falsificação em vez de magnitude.

**H3b — repetibilidade não implica estabilidade.**
Teste: a partir da configuração de D4, injetar alteração de **um bit** na representação de um parâmetro inicial, e repetir com o mesmo N.
Refutada se a divergência resultante for substancialmente menor que a dispersão medida em D0.

**Resultado nulo é resultado, declarado antes da medição.** Se a dispersão for pequena e H1 ou H2 forem refutadas, a conclusão *"o treino de 3DGS é reprodutível dentro de X dB nesta configuração"* é achado válido e publicável — responde a uma pergunta aberta desde 2023 que ninguém quantificou. Esta declaração existe para remover o incentivo de ajustar o limiar após ver os dados.

## 7. Retenção de dados

Partição extensível a ~500 GB, mais ~5 TB em nuvem. **Retenção integral, sem condicional.**

| Classe | Onde | Versionado no git? |
|---|---|---|
| `train.json`, `eval.json`, `config.json`, `env.json`, logs de stdout/stderr | repositório do TCC | **sim** — são o registro citável |
| Resumos estatísticos derivados e resultados de análise | repositório do TCC | **sim** |
| **Lista de hashes** dos `.ply` e das imagens renderizadas | repositório do TCC | **sim** |
| `splat.ply` de todas as execuções, imagens renderizadas | disco local e cópia em nuvem | não (volume) |

A regra que sustenta isso: **a lista de hashes fica no git, o volume fica onde couber.** Assim a integridade dos artefatos grandes é verificável a qualquer momento, e nenhuma afirmação da monografia depende da disponibilidade de um serviço de nuvem. Se um `.ply` for perdido, isso é detectável e declarável em vez de silencioso.

## 8. Limitações declaradas antes da execução

1. **Uma única cena.** `garden`. Não há alegação de generalidade entre cenas.
2. **JPEG contra PNG.** Os valores publicados pelos autores do VkSplat usam `images_4_png`, gerados pelo gsplat, conforme comentário no próprio código. Este experimento usa os JPEG distribuídos em `images_4`. **Comparação de valores absolutos com o artigo não é válida** sem essa ressalva. Afeta H4.
3. **Convenção de LPIPS.** No `eval()`, `lpips_vgg` usa `normalize=False` sobre imagens em `[0,1]`, quando o `torchmetrics` espera `[-1,1]` — defeito herdado do pipeline do 3DGS. Só `lpips_alex` está sob a convenção pretendida. As duas são reportadas com a convenção declarada.
4. **Contaminação do escalonador em D0 e D1.** Nesses degraus, ~1,8% dos passos usam um kernel de backward numericamente distinto, e a proporção varia entre execuções. Isso é parte do que D2 mede, não um defeito do protocolo.
5. **Ambiente térmico e carga não controlados**, por impossibilidade prática.
6. **O trabalho não descobre o fenômeno.** O não-determinismo foi reconhecido por Kerbl em 2023 (issue pública do `gaussian-splatting`) e atribuído a atômicas de ponto flutuante por um mantenedor do nerfstudio em 2024. A contribuição é **quantificação e atribuição**, não descoberta.
7. **A originalidade não está estabelecida em busca fechada.** Faltam consultas por frase exata e a bases fechadas. Nenhum texto pode alegar ineditismo antes disso.

## 9. O que invalidaria o experimento

- Execução com `deviceName` diferente do esperado, ou com `TRAIN_DEVICE = -1`.
- Acionamento de `USE_EMULATED_F32_ATOMIC` ou `USE_EMULATED_INT64` sem declaração.
- **Execução de uma série sem recompilar após `git checkout` do degrau** — ver §3.2. O binário não é versionado, logo o SHA registrado no `env.json` pode não corresponder ao código C++ efetivamente executado. Este é o modo de falha silencioso do protocolo, e a razão pela qual a recompilação é incondicional.
- Alteração de qualquer parâmetro de §3 no meio de uma série.
- Alteração de α, `k`, `N_min`, `N_max` ou da largura-alvo após observação de resultados.
- Descarte de execuções por qualquer motivo que não os acima — descartes precisam ser contados e justificados.
- Árvore de trabalho suja (`vksplat_dirty` não vazio no `env.json`) durante uma série medida.

---

## 10. Adendo do estágio 2 — plano de implementação de D4 (RASCUNHO, ainda não vinculante)

> **Estado: rascunho.** Torna-se vinculante quando os parâmetros de escala forem fixados a partir da medição de §10.3 e este adendo for commitado. Base: auditoria de código de 2026-09-21 no commit `b3ad2b0`.

### 10.1 O achado que redefine o escopo de D4

Ponto fixo nos 9 sítios de `_ATOMIC_ADD`, isoladamente, **não** entrega bit-identidade — por duas razões, ambas verificadas no código:

1. **O escalonador sorteia entre implementações.** Em AMD, entre `PerSplat` e `Tensor_0_8_8`. As duas agrupam os termos de forma diferente **antes** do atômico, e essas reduções parciais são **em ponto flutuante**. Tornar a soma final associativa não faz as somas parciais coincidirem entre implementações.
2. **Dentro de cada implementação há pré-redução em float antes do atômico.** No `per_pixel` via `WaveActiveSum`; no `tensor` via `reduce_splats` em memória compartilhada. **A exceção é o `per_splat`:** ali a pré-redução é acumulação sequencial em registrador, com ordem fixada pelo laço, e portanto determinística.

**Consequência, e ela valida o desenho cumulativo da escada:** como **D2 já fixa a implementação em `PerSplat`**, e D4 é cumulativo sobre D2, converter **apenas** o `per_splat` é suficiente para fechar a bit-identidade. Isso não é atalho — é controle experimental. Comparar "atômico float" contra "ponto fixo" enquanto o escalonador sorteia pipelines misturaria duas fontes de variação.

**A dependência D2 → D4 deve ser declarada explicitamente no texto:** o patch de D4 cobre uma única das três variantes de backward, e isso só é válido porque D2 é cumulativo. Removido D2, D4 fica incompleto.

### 10.2 Conjunto de mudanças — 4 arquivos Slang, **zero C++**

| # | Arquivo | Mudança |
|---|---|---|
| 1 | `slang/config.slang` | constantes de escala **por componente**; macro `_ATOMIC_ADD_FIXED` sobre `buffer.InterlockedAdd(byteAddress, uint)`; helper de desescala |
| 2 | `slang/alphablend_shader_bwd_per_splat.slang` | os 9 sítios, em bloco único |
| 3 | `slang/fused_projection_backward_optimizer.slang` | 3 bindings (5/6/7) e 3 leituras; o helper `read_t3_float3` precisa de variante inteira ou de desenrolar a leitura |
| 4 | `slang/default.slang`, fase `UpdateState` | 1 binding e 1 leitura de `v_xy_vs` |

**Por que zero C++:**

- Os três buffers são `RWByteAddressBuffer` nos produtores e `Buffer<float>` no C++. Como `sizeof(float) == sizeof(int32_t)`, os **mesmos bytes** podem ser acumulados como inteiro **sem realocar nada**.
- O zeramento por passo é `vkCmdFillBuffer(..., 0)`: **zero bytes é simultaneamente `0.0f` e `int32_t(0)`.** Não muda valor, tamanho nem barreira. É o ponto mais barato do plano.
- O readback Python continua funcionando com `.view(np.int32)`.

### 10.3 A medição que precede tudo — e **não exige código nenhum**

O binding Python **já expõe** os três buffers de gradiente como numpy: `module.v_xy_vs` `(N,2)`, `module.v_inv_cov_vs_opacity` `(N,4)`, `module.v_rgb` `(N,3)`. Também `module.tiles_touched` e `module.radii`. Portanto **a magnitude dos gradientes e a distribuição de K são mensuráveis hoje, sem tocar em C++ nem em Slang, e sem depender da toolchain Slang.**

Colher, e registrar no adendo antes de implementar:

- Histograma **por componente separadamente** — 2 de `xy`, 3 de cônica, 1 de opacidade, 3 de cor. As unidades diferem e quase certamente exigem escalas diferentes.
- **Mínimo não-nulo e máximo absoluto**, não só média — são eles que fixam bits fracionários e risco de estouro.
- Evolução **ao longo do treino**: a distribuição muda com `step`, com `active_sh` crescendo de 0 a 3, e com a densificação.
- Distribuição de **K** (tiles por gaussiana), para o orçamento de estouro.

Ponto de leitura: após `rasterize_backward()`. Note que `copyFromDevice` sincroniza o pipeline — irrelevante para instrumentação.

### 10.4 Orçamento de estouro — e a ausência de atômico de 64 bits

**Não existe atômico inteiro de 64 bits em nenhum lugar do repositório.** A macro `USE_EMULATED_INT64` **não tem relação com atômicos** — é emulação de armazenamento e aritmética — e nunca é acionada pelo build. Logo não há infraestrutura reaproveitável para acumulador maior que 32 bits: as alternativas seriam duas somas de 32 bits com propagação de carry, sem precedente no repositório, ou atômico 64 nativo, exigindo estender a detecção de features em C++. **Dimensionar a escala para caber em `int32` com margem.**

Termos somados por acumulador: `K × A`, com `A = 1` no `per_splat` — mas `A ∈ {8, 16, 32}` nas outras variantes, o que é outro argumento para fixar `per_splat`. E **não há limite dedicado de tiles por gaussiana**: `K ≤ grid_width × grid_height`, com *clamp* apenas contra o grid. Uma gaussiana grande e opaca pode cobrir a tela toda.

Ponto de partida analítico para a escala: o gradiente que entra no backward já vem dividido por `3·W·H` (`executeComputeSSIMGradient` fixa `(1 - ssim_lambda)/(3·w·h)`), o que é da ordem de 1e-7 por pixel-canal em imagem de ~1 MP.

### 10.5 A consequência que mais importa cientificamente

**Adam é invariante a fator de escala global no gradiente** — numerador e denominador escalam juntos, até `eps = 1e-15` deixar de ser desprezível. Isso é favorável: erro de escala uniforme é absorvido pelo consumidor principal.

**Mas `default.slang` não é invariante.** A fase `UpdateState` calcula `grad = 0.5 * length(v_xy_vs[gid] * float2(width, height))`, e esse valor alimenta um **teste de limiar** em `ComputeGrowMask`: `is_grad_high = grad > uniforms.grow_grad2d`, com `grow_grad2d = 0.0002`. Não há normalização que absorva a escala.

Ou seja: **o erro de quantização do ponto fixo propaga diretamente para a decisão de duplicar ou dividir gaussianas.** Se o quantum for grosso demais, D4 muda o número de primitivas — e o número de gaussianas é um dos observáveis do trabalho. Isto precisa ser medido e declarado, e é o candidato mais provável a fazer D4 trocar determinismo por qualidade.

### 10.6 Risco técnico não mitigado

**Não existe, em nenhum `.slang` do repositório, uma chamada `InterlockedAdd` inteira sobre `RWByteAddressBuffer`.** A intervenção estreia essa API, e nenhum `.spv` versionado contém precedente. Se o `slangc` não emitir SPIR-V válido para ela, D4 exige outro desenho. **É o principal risco técnico em aberto, e é verificável em minutos assim que a toolchain estiver em disco** — compilar um shader mínimo e inspecionar com `spirv-dis`.

### 10.7 Ordem de execução

1. Medir magnitude e distribuição de K via Python — **gratuito, sem código, independente da Slang**.
2. Verificar que `slangc` emite SPIR-V válido para `InterlockedAdd` inteiro em `RWByteAddressBuffer`.
3. Fixar as escalas por componente e commitar este adendo como vinculante.
4. Implementar, compilar shaders, commitar como degrau D4 com SHA registrado em §3.1.
5. Rodar a série e verificar **bit-identidade** por hash.

### 10.8 Itens a fixar também no adendo

- **`-denorm-mode-fp32`**: o `slangc` tem essa opção com default `any`, documentado como *"implementation defined"*, e o `compile_shaders.py` **não a fixa**. Num trabalho sobre reprodutibilidade numérica isso é fonte de divergência não controlada. Fixar explicitamente, ou declarar como limitação do artefato tal como distribuído.
- **SHA-256 do asset da Slang** (`assets[].digest` no endpoint da release), para o ambiente ser reproduzível.
- Comportamento em **saturação**: contar e reportar, em vez de saturar silenciosamente.
