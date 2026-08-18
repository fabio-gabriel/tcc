# Verificação de Viabilidade do Experimento — RDNA 4 / RX 9070 XT

> Este arquivo é a **fonte de verdade versionada** para os fatos de viabilidade do experimento (suporte de stack, status de repositórios/PRs de terceiros, bugs upstream). Substitui a memória persistente `reference_experimento_rdna4.md`, perdida num reinstall do Claude Code em 2026-08-06. Ao contrário da memória do Claude, este arquivo sobrevive a qualquer reinstall porque está no git. A memória do Claude passa a guardar apenas um ponteiro curto para este arquivo — não os fatos em si.
>
> Cada item tem duas rodadas de verificação: a original (2026-06-23, registrada em PLANO.md/fichamento.md) e a reconfirmação em fontes primárias (2026-08-06). Quando o estado mudou entre as duas datas, isso está marcado explicitamente.

## 1. Suporte oficial ROCm a RDNA 4 / RX 9070 XT

- **Veredito:** confirmado, com versão atualizada.
- **Fonte:** rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html (acesso 2026-08-06)
- RX 9070 XT, RX 9070 GRE, RX 9070 (gfx1201) e RX 9060 XT LP, RX 9060 XT, RX 9060 (gfx1200) continuam listados como "✅ Supported", restritos a Ubuntu 24.04.4 / 22.04.5, RHEL 10.1 / 9.7.
- **Mudou:** produção avançou de ROCm 7.2.4 (jun/2026) para **ROCm 7.14.0** (ago/2026), com ROCm 7.13.0 como "technology preview" em paralelo — evolução rápida da linha de produção em ~1,5 mês.

## 2. PR `graphdeco-inria/gaussian-splatting#1297` (Port to HIP / AMDGPU)

- **Veredito:** confirmado aberto, porém estagnado.
- **Fonte:** api.github.com/repos/graphdeco-inria/gaussian-splatting/pulls/1297 (acesso 2026-08-06)
- `state: open`, `merged: false`. `created_at` e `updated_at` idênticos (2025-12-16T17:51:53Z) — nenhuma atividade desde a criação. 1 commit, 0 comentários.
- **Implicação para o TCC:** não tratar como PR "vivo"; é um rascunho parado há ~8 meses na data de acesso. Testar cedo no Sprint 0 para não descobrir problemas de compatibilidade tarde; considerar fork próprio fixando o commit.

## 3. VkSplat — paper (arXiv:2605.00219) e repositório `harry7557558/vksplat`

- **Veredito:** confirmado que paper e repositório são reais e acessíveis, mas com duas ressalvas importantes.
- **Fonte:** arxiv.org/abs/2605.00219 e github.com/harry7557558/vksplat (acesso 2026-08-06)
- Paper: "VkSplat: High-Performance 3DGS Training in Vulkan Compute", Jingxiang Chen, Mohamed Ibrahim, Yang Liu. Submissão v1 em 30/04/2026. Comentário oficial do arXiv: **"Submitted to Eurographics 2026 – Short Papers"** — ou seja, **submetido, não aceito**. Não afirmar aceitação no texto do TCC.
- Repositório: 129 stars, não arquivado, `pushed_at: 2026-07-22` (ativo). Claim de 3,3x speedup e 33% menos VRAM vs. gsplat (CUDA), testado pelos autores em NVIDIA RTX 3090/4080S/5070, **AMD Radeon RX 7800 XT (RDNA 3)** e Intel UHD.
- **Ressalva crítica:** **RX 9070 XT / RDNA 4 não está na lista de "Tested with" do README.** A força argumentativa de "referência mais alinhada possível ao experimento" cai de "baseline forte confirmado" para "baseline promissor, ainda sem confirmação de terceiros em RDNA 4" — o bring-up na 9070 XT no Sprint 0 passa a ser validação original, não replicação de resultado já demonstrado no mesmo hardware.

## 4. `Linyou/taichi-ngp-renderer`

- **Veredito:** confirmado existir, mas sem manutenção de código ativa.
- **Fonte:** api.github.com/repos/Linyou/taichi-ngp-renderer (acesso 2026-08-06)
- Repositório existe, não arquivado, 373 stars. `pushed_at: 2025-03-22T15:11:34Z` — **último push de código há ~1 ano e 4 meses** em relação a 2026-08-06. `updated_at` mais recente (2026-05-11) reflete só metadados (estrelas etc.), não código novo.
- **Implicação para o TCC:** funcional em tese, mas risco de incompatibilidade com versões atuais de Taichi/ROCm/Vulkan não testadas pelo autor original. Verificar compatibilidade cedo no Sprint 0.

## 5. PyTorch estável × versão ROCm suportada nos wheels oficiais

- **Veredito:** mudou — defasagem reduzida, não eliminada.
- **Fonte:** pytorch.org/get-started/locally/ (acesso 2026-08-06)
- PyTorch estável: **2.13.0** (era 2.7.0 em jun/2026). Wheels ROCm oficiais estáveis agora apontam para **ROCm 7.2** (era ROCm 6.3 em jun/2026).
- **Gap residual:** a doc oficial de produção ROCm já está em 7.14.0 (item 1), então persiste descompasso PyTorch↔ROCm (7.2 vs 7.14), só que menor que antes (era 6.3 vs 7.2.4/7.13.0). Continua válido como achado próprio do TCC — atualizar apenas os números.

## 6. Bugs ativos em PyTorch + ROCm gfx1201

- **Veredito:** parcialmente mudou — status individual por item. Fonte: `api.github.com/repos/.../issues/<n>`, acesso 2026-08-06.

| Issue | Status em 2026-06-23 | Status em 2026-08-06 |
|---|---|---|
| `pytorch/pytorch#177834` (LSTM/MIOpen incorreto gfx1201) | aberto | **ainda aberto** (atualizado 2026-07-31, 12 comentários) |
| `pytorch/pytorch#187343` (`expandable_segments:True` → `hipErrorIllegalAddress`) | aberto | **fechado `not_planned`** em 2026-07-16 — engenheiro AMD (`naromero77amd`) obteve acesso a gfx1201 e **não conseguiu reproduzir**; não é um fix confirmado, é falta de reprodutibilidade do ambiente do reporter |
| `pytorch/pytorch#181939` (falha CMake `gfx1036;gfx1201`) | aberto | **ainda aberto** (atualizado 2026-07-23, 9 comentários) |
| `ROCm/ROCm#6116` (`torch.mm` → NaN com >~500K linhas) | aberto | **fechado `completed`** em 2026-06-25, **mas ambíguo**: o próprio autor comentou no fechamento que o bug ainda reproduz deterministicamente no driver 26.2.2 (gfx1201) e só "parece resolvido" no driver Adrenalin 26.3.1 — fechamento por inatividade do mantenedor, não por fix confirmado do ROCm em si |
| `ROCm/ROCm#6374` (page fault OpenCL/ROCr RDNA 4, XNACK off/host-VA) | aberto | **ainda aberto** (atualizado 2026-07-18, 3 comentários) |

- **Leitura para o TCC:** de 5 bugs, apenas 1 (`#6116`) tem indício de mitigação, e mesmo esse é atribuído a driver, não a patch do ROCm, e não confirmado oficialmente. Isso reforça — em vez de enfraquecer — a tese de imaturidade do stack ROCm em RDNA 4 no curto prazo (jun→ago/2026, ~1,5 mês).

## 7. `tiny-rocm-nn` (adaptação de tiny-cuda-nn para HIP/WMMA)

- **Veredito:** mudou — repositório foi transferido/renomeado.
- **Fonte:** api.github.com/repos/PhysicalAI-AIM/tiny-rocm-nn (acesso 2026-08-06) → HTTP 301 apontando para repository id 863925079
- Esse ID resolve hoje para **`ZJLi2013/tiny-rocm-nn`** (github.com/ZJLi2013/tiny-rocm-nn), mesma descrição de propósito, 4 stars, não arquivado, `pushed_at: 2026-04-02`.
- README confirma: port de tiny-cuda-nn para HIP/hipBLAS/rocWMMA, mas **benchmarkado em MI300X (CDNA 3)**, não em RDNA 4/RX 9070 XT — condizente com a nota já registrada no PLANO.md ("CDNA → adaptar WMMA RDNA").
- **Implicação prática:** a URL antiga (`PhysicalAI-AIM/tiny-rocm-nn`) quebra; usar `github.com/ZJLi2013/tiny-rocm-nn` em qualquer referência futura.

---

## Nota metodológica sobre esta reconfirmação

Verificação feita via chamadas diretas a `api.github.com`, `arxiv.org` e `rocm.docs.amd.com` (não via ferramenta de fetch de página, que falhou de forma consistente nesta sessão). Todas as datas de acesso: **2026-08-06**. Dois itens seguem precisando de reconfirmação manual antes do depósito final do TCC:

- **VkSplat/Eurographics 2026:** confirmar se o paper foi de fato aceito (hoje é "submitted") antes de citar como aceito.
- **`ROCm/ROCm#6116`:** não descrever como "corrigido" — descrever como "fechado por inatividade, com indício não confirmado de mitigação via driver mais novo".
