# Correção da regra de matrícula atendida — Specification

## Problem Statement

O painel novo mostra menos matrículas que o painel legado para o mesmo export do Sistec
(14.022 vs 16.750, `Downloads/08agosto`, 11 campi). Investigação com dados reais isolou a causa
raiz: `t07_grao_matricula_atendida` (`app/data/transform.py:156-175`, a regra "matrícula
atendida", BR-MIGRAR-001) tenta parsear `MES_DE_OCORRENCIA` com `pd.to_datetime(..., errors=
"coerce")` (linha 167), mas o Sistec exporta esse campo como texto em português
(`"JUNHO 2026"`, `"DEZEMBRO 2025"`) — formato que `pandas`/`dateutil` não reconhece. O parse
falha silenciosamente para **100% das linhas** (`errors="coerce"` → `NaT`), então o termo
`mes_ocorrencia >= início do ano-base` nunca é verdadeiro. Toda matrícula que não está `EM_CURSO`
só é contada se o **ciclo** começou no ano-base — descartando ~2.700 matrículas concluídas/
evadidas cujo evento (conclusão, abandono etc.) aconteceu em 2026, mas cujo ciclo começou antes.

Confirmado com o export real (`Downloads/08agosto`, 121.332 matrículas brutas): corrigindo só o
parse de `MES_DE_OCORRENCIA` (nomes de mês em português → data), o total sobe de 14.022 para
**16.832** — a 82 de distância dos 16.750 do painel legado (0,5%), contra a regra descrita pela
usuária: "em curso sempre conta; qualquer outra situação conta se o mês de ocorrência cai no
ano-base, independente do ciclo".

Um segundo bug, já confirmado antes desta investigação mais funda: o KPI "Ingressantes"
(`app/pages/matriculas.py:355`) conta `status_corrigido == EM_CURSO` em vez de "matrícula
atendida cujo ciclo começou no ano-base (aproximação, pois a extração do Sistec não traz a data
da matrícula em si) OU matrícula EM_CURSO cujo mês de ocorrência cai no ano-base mesmo com ciclo
de outro ano".

## Goals

- [x] `t07_grao_matricula_atendida` interpreta `MES_DE_OCORRENCIA` em português corretamente —
      o total de matrículas atendidas reflete a regra real, não um parse quebrado.
- [x] "Ingressantes" conta a aproximação definida pela usuária (ciclo iniciado no ano-base OU
      em_curso com mês de ocorrência no ano-base), não mais `EM_CURSO`.
- [x] Teste de paridade (Princípio I) para as duas regras, cobrindo nominal + edge cases de
      `RISK-002` (vazio/NaN/mês em formato inesperado/data nula).

## Out of Scope

| Item | Motivo |
| --- | --- |
| KPI "Ingressantes" em outras páginas | Eficiência Acadêmica, Evasão Anual e Percentuais Legais não têm esse KPI. |
| Paridade exata (16.750 vs 16.832, diferença de 82) | **Causa do resíduo não identificada.** A hipótese original ("algum mês não-padrão") foi testada contra o export real e não se sustenta: as 330 linhas com formato irregular (`"FEVEREIRO/2011"`, 0,27% do total) contribuem **0** matrículas pela via do mês. Fica como follow-up, se a usuária quiser fechar os 0,5%. |
| Outros usos de `pd.to_datetime` no pipeline | `dt_data_inicio`/`dt_data_fim_previsto` (`app/data/transform.py:166,181`) usam formato ISO (`"2010-02-22 00:00:00"`) e parseiam corretamente — conferido nos dados reais; não precisam de mudança. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| `MES_DE_OCORRENCIA` com texto que não bate nenhum dos 12 meses em português, ou sem ano de 4 dígitos | Tratado como nulo (não conta pela via do mês) | Mesma tolerância de `errors="coerce"` que o código já tinha para outros formatos ruins — mantém RISK-002 (não quebra a ingestão) | n (assumido — baixo risco, comportamento defensivo padrão do resto do pipeline) |
| Matrícula cujo ciclo tem `dt_data_inicio` nulo, para efeito de Ingressantes | Não conta como ingressante por essa via (só pode entrar pela via `em_curso + mês no ano-base`) | Não dá pra confirmar que o ciclo começou no ano-base sem a data | y (implícito na regra que a usuária descreveu) |

**Open questions:** none — resolvido acima.

---

## User Stories

### P1: Matrícula atendida conta corretamente quem não está em curso ⭐ MVP

**User Story**: Como gestora que usa o painel para decisões institucionais, quero que o total de
matrículas reflita a regra real (em curso sempre conta; qualquer outra situação conta se o mês de
ocorrência é do ano-base), para o painel novo bater com o legado no mesmo dado de entrada.

**Why P1**: É a causa raiz confirmada da divergência de ~2.700 matrículas; Princípio I do projeto
(paridade de cálculo) é inegociável.

**Acceptance Criteria**:

1. WHEN `t07_grao_matricula_atendida` processa uma matrícula com `status_corrigido != "EM_CURSO"`
   THEN o sistema SHALL incluí-la se `MES_DE_OCORRENCIA` (nome do mês por extenso em português +
   ano) corresponde a um mês do ano-base ativo.
2. The system SHALL reconhecer os 12 nomes de mês em português (com e sem acento, maiúsculo,
   como o Sistec exporta: `JANEIRO`..`DEZEMBRO`).
3. WHEN `status_corrigido == "EM_CURSO"` THEN o sistema SHALL sempre incluir a matrícula,
   independente de `MES_DE_OCORRENCIA` ou do ciclo (comportamento já existente, não muda).
4. IF `MES_DE_OCORRENCIA` não corresponde a um mês/ano válido (texto inesperado, vazio ou nulo)
   THEN o sistema SHALL tratar como não-atendida por essa via (sem lançar exceção), mantendo as
   demais vias de inclusão (ciclo iniciado no ano-base, em_curso).

**Independent Test**: com um DataFrame sintético de matrículas com `MES_DE_OCORRENCIA` em
português (`"JUNHO 2026"`, `"DEZEMBRO 2025"`) e status variados, a nova função inclui as que têm
mês no ano-base e status != EM_CURSO, e exclui as de anos anteriores — provando que o parse
funciona (o bug atual falha em 100% dessas linhas).

---

### P2: Ingressantes usa a aproximação certa

**User Story**: Como gestora, quero que "Ingressantes" reflita quem realmente ingressou no
ano-base (não quem está em curso agora), usando a melhor aproximação disponível nos dados do
Sistec.

**Why P2**: Depende do fix de P1 (mesma função de parse de mês) para a segunda via de inclusão.

**Acceptance Criteria**:

1. WHEN a página Matrículas calcula "Ingressantes" THEN o sistema SHALL contar matrículas
   atendidas cujo ciclo tem `dt_data_inicio` no ano-base.
2. WHEN uma matrícula atendida tem `status_corrigido == "EM_CURSO"` E `MES_DE_OCORRENCIA` no
   ano-base, MESMO com o ciclo de outro ano, THEN o sistema SHALL também contá-la como
   ingressante.
3. The system SHALL NOT usar `status_corrigido == "EM_CURSO"` sozinho como critério de
   Ingressantes.
4. WHEN filtros de campus ou curso estão ativos THEN Ingressantes SHALL respeitar os mesmos
   filtros das demais contagens da página.

**Independent Test**: DataFrame sintético com (a) ciclo iniciado no ano-base e status concluído,
(b) EM_CURSO com ciclo de outro ano mas mês de ocorrência no ano-base, (c) EM_CURSO com ciclo E
mês de outro ano (não deve contar) — a nova função inclui (a) e (b), exclui (c).

---

## Edge Cases

- IF o DataFrame de entrada está vazio THEN ambas as funções SHALL devolver `0`/DataFrame vazio,
  sem erro.
- IF `MES_DE_OCORRENCIA` vem em maiúsculas sem acento (`"MARCO 2026"` em vez de `"MARÇO 2026"`)
  THEN o sistema SHALL ainda reconhecer o mês (exportações do Sistec variam em acentuação).
- WHEN todas as matrículas do lote são `EM_CURSO` THEN o total de atendida SHALL igualar o total
  de `EM_CURSO` (nenhuma via de mês/ciclo muda o resultado).
- WHEN uma matrícula concluída tem `dt_data_inicio` do ciclo nulo E `MES_DE_OCORRENCIA` no
  ano-base THEN o sistema SHALL contá-la como atendida (a via do mês não depende do ciclo).

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| MAT-01 | P1: Matrícula atendida conta corretamente quem não está em curso | Execute | Verified |
| MAT-02 | P2: Ingressantes usa a aproximação certa | Execute | Verified |

**Coverage:** 2 total, 2 mapped, 0 unmapped — MAT-01 em
`tests/test_shared_mes_ocorrencia.py` (33 casos de parse) + `tests/test_transform_matricula_atendida.py`
(17 casos de grão) + `tests/test_sintetico.py` (3 casos de corpus); MAT-02 em
`tests/test_parity_dominio.py` (7 casos `test_mat02_*`). Execute inline, sem `tasks.md` formal.

---

## Success Criteria

- [x] `python -m pytest tests/ -q` verde, com testes novos cobrindo P1 e P2 (nominal + edge
      cases de `RISK-002`) — 939 passed, 0 failed.
- [ ] Reenviando `Downloads/08agosto` pelo envio real, o total de matrículas fica próximo de
      16.750 (não mais 14.022) e "Ingressantes" deixa de ser igual ao total de Em Curso.
      **Substanciado no pipeline, não pela UI (G1).** O Verifier rodou o caminho real de
      código (`ler_planilha` → `consolidar` → `montar_matriculas_e_eficiencia`) sobre o
      export: regra antiga **14.022** (bate com a spec), implementação nova **16.832** (bate
      com a spec), `contar_ingressantes` **5.432** contra **13.328** de Em Curso — o KPI
      deixa de ser igual a Em Curso. O reenvio pela tela de envio continua com a usuária.
