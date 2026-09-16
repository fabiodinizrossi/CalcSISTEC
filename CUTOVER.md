# Checklist de Cutover — Painel de Acompanhamento Sistec

> Operacionaliza `_reversa_sdd/migration/cutover_plan.md` para este repositório.
> Estratégia confirmada: **Big Bang, sem gate de Parallel Run** — a validação
> automatizada de paridade (Tarefa 11) é a única defesa antes do corte.

## Pré-requisitos (checklist)

- [x] Setup do projeto novo sobre `projetoFabio/CalcSISTEC` (Tarefa 01)
- [x] Schema do banco alvo, sem coluna de PII (Tarefa 02)
- [x] Pipeline de ingestão T-01 a T-08 implementado (Tarefa 05)
- [x] Núcleo de Matrículas — funções puras de domínio (Tarefa 06)
- [x] Indicadores Regulatórios — percentuais legais e IEA (Tarefa 07)
- [x] Autenticação da rota administrativa de upload (Tarefa 08, `RISK-009`)
- [x] As 5 páginas com identidade gov.br (Tarefa 09) — **tokens ainda 🟡, não confirmados contra a documentação oficial**
- [ ] Todas as 28 regras `BR-MIGRAR-*` com teste unitário próprio (parcial — ver nota abaixo)
- [ ] `parity_specs.md`/`parity_tests/` executados contra os dados do mês corrente, batendo 100% (Tarefa 11 — **não iniciada**)
- [ ] Checklist de ausência de PII verificado com dados reais de upload (verificável com `scripts/verificar_prontidao_cutover.py`, mas só definitivo após um upload real)
- [ ] Design gov.br validado em pelo menos um dispositivo móvel real (passo humano)
- [x] `AMB-003` (integração do repositório `projetoFabio/CalcSISTEC`) resolvido na Tarefa 01 (`AD-05`)

### `002-baixador-planilhas-sistec` (baixador de planilhas do Sistec)

- [x] Schema v2 (versionamento interna/publicada/anterior, `fatores`, `campi_sistec`, `estado_versoes`, `historico`) — T004-T012
- [x] `/admin/upload` removido; `/admin/atualizar` é a nova porta de entrada de dados (D-14)
- [x] Extensão MV3 `extensao-sistec/` (baixa com a sessão da PI, sem senha, sem Downloads) — T013, T045, T046, T061
- [x] Rotas `/api/sistec/*` com token por execução (D-16) e bloqueio de HTTP fora de `localhost` (D-19)
- [ ] **Processo único (P-09)**: o registro em memória de execuções (`app/sistec/execucoes.py`) só funciona com **um único worker/processo**. Configurar o servidor de produção (`gunicorn`/`waitress`/etc.) com `--workers 1` (ou equivalente) antes do cutover — múltiplos workers quebram silenciosamente a fila e o limite de uma execução por administrador (RN-11)
- [ ] **`CALCSISTEC_HTTPS=1`** configurado no ambiente de produção, com certificado válido — D-19 recusa `/api/sistec/*` sem isso fora de `localhost`
- [ ] Extensão instalada na máquina da Pesquisa Institucional (política institucional ou modo desenvolvedor, P-10)
- [ ] Roteiro de `_reversa_forward/002-baixador-planilhas-sistec/onboarding.md` executado (Sistec simulado + 1 baixa real de pelo menos 1 campus)
- [ ] W001 a W008 (`_reversa_forward/002-baixador-planilhas-sistec/regression-watch.md`) conferidas sem regressão nas telas novas e alteradas

**Nota sobre "28 regras com teste unitário"**: as Tarefas 05-07 testaram cada
regra com dados sintéticos ad-hoc (não uma suíte de testes formal versionada,
ex. `pytest`). Antes do cutover, migrar esses testes ad-hoc para uma suíte
real é recomendável, mas não bloqueia a Tarefa 11 (que cobre paridade via
`parity_tests/*.feature`).

## Como rodar a verificação automatizada

```bash
python scripts/verificar_prontidao_cutover.py
```

Cobre: ausência de PII no schema (`RISK-008`), autenticação admin configurada
(`RISK-009`), schema v2 aplicado (`002-baixador-planilhas-sistec`, substitui
`RISK-004`/`uploads_log`), tabela de fatores carregada, `CALCSISTEC_HTTPS=1`
configurado (D-19), dataset publicado presente e ano-base configurado. **Não
cobre** paridade numérica (Tarefa 11), o processo único (P-09, checklist
acima) nem os passos humanos abaixo — o script termina com `NO-GO` até que
uma baixa real de teste seja publicada e a Tarefa 11 esteja completa, mesmo
que os critérios técnicos automatizáveis estejam OK.

## Passos do cutover (`cutover_plan.md` §"Passos do cutover")

| # | Passo | Owner | Reversível? |
|---|---|---|---|
| 1 | Rodar `parity_specs.md`/`parity_tests/` completos contra os dados reais do mês corrente | agente de codificação (Tarefa 11) | sim |
| 2 | Corrigir divergências e repetir o passo 1 até paridade 100% | agente de codificação | sim |
| 3 | Rodar `scripts/verificar_prontidao_cutover.py` e validar checklist de PII/autenticação | agente de codificação + Jaline | sim |
| 4 | Validar design gov.br responsivo em pelo menos um dispositivo móvel real | Jaline | sim |
| 5 | Comunicar a data de transição aos stakeholders | Jaline | sim |
| 6 | Publicar o sistema novo como canal oficial | Jaline | **não** (ver rollback) |
| 7 | Monitorar o primeiro ciclo de upload real pós-cutover | Jaline | não (rollback disponível) |

## Critérios de go / no-go

**Go** — todos verdadeiros:
- Paridade de cálculo 100% em `parity_tests/` para as 28 regras `BR-MIGRAR-*` e os edge cases de `RISK-002` (BLANK/NaN/data nula).
- `scripts/verificar_prontidao_cutover.py` retorna código de saída 0.
- Design gov.br responsivo validado em dispositivo móvel real.

**No-go** — qualquer um verdadeiro:
- Divergência de cálculo não explicada/corrigida nos testes de paridade.
- PII detectada em qualquer etapa do pipeline.
- Autenticação da rota administrativa não configurada (`RISK-009`) — nesse caso, considerar cutover parcial (painel público liberado, upload mantido restrito/manual).

## Plano de rollback

1. Republicar/manter acessível o link do Power BI Service como fonte oficial temporária.
2. Comunicar aos stakeholders o retorno temporário ao sistema anterior.
3. Corrigir o problema no sistema novo; repetir os passos 1-4 antes de tentar o cutover novamente.

**Tempo máximo até rollback**: 1 dia útil a partir da detecção do problema.
**Owner do rollback**: Jaline.
**Importante**: o Power BI legado não deve ser desativado antes do período de
observação pós-cutover (ver abaixo) — não há gate de Parallel Run prévio,
então este é o primeiro contato do sistema com dados reais de produção.

## Pós-cutover

- [ ] Monitorar 1 ciclo de upload completo após o corte, com Jaline validando o resultado.
- [ ] Repetir a validação de paridade (`parity_specs.md`) no primeiro ciclo pós-cutover.
- [ ] Decommission do Power BI Service somente após o ciclo de monitoramento ser aprovado por Jaline — nunca simultâneo ao passo 6.
