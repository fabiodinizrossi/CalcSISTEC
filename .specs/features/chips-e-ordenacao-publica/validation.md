# Chips e ordenação das tabelas públicas — Validation

**Date**: 2026-09-22
**Spec**: `.specs/features/chips-e-ordenacao-publica/spec.md`
**Diff range**: `e8d9e29^..383a63e`
**Verifier**: independent sub-agent, com repetição local após o limite de uso do verificador.

## Task Completion

| Task | Status | Notes |
| --- | --- | --- |
| T1–T6 | ✅ Done | Implementação e testes presentes. |
| T7–T9 | ✅ Done | Observador e eventos delegados são discriminados. |

## Spec-Anchored Acceptance Criteria

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| CHIP-01.1: todo dashboard mostra seis chips, Campus inicial. | Checklist com seis eixos e valor `['campus']`. | `tests/test_componentes_publicos.py:156`–`tests/test_componentes_publicos.py:165` exige valores, `['campus']` e classes; layouts de Eficiência e Percentuais exigem `card-chips` em `tests/test_paginas_publicas.py:254`–`tests/test_paginas_publicas.py:256` e `tests/test_paginas_publicas.py:433`–`tests/test_paginas_publicas.py:436`. | ✅ PASS |
| CHIP-02.1: seleção e remoção preservam ordem de clique. | Eixo removido e reintroduzido vai ao fim. | `tests/test_componentes_publicos.py:176`–`tests/test_componentes_publicos.py:179` compara exatamente as três transições. | ✅ PASS |
| CHIP-02.2: eixos ativos formam hierarquia na mesma ordem. | Hierarquia Modalidade → Campus preserva pai-filho. | `tests/test_paginas_publicas.py:240`–`tests/test_paginas_publicas.py:246` exige cabeçalho e `data-parent-id`; Matrículas fixa ordem em `tests/test_paginas_publicas.py:108`–`tests/test_paginas_publicas.py:117`. | ✅ PASS |
| CHIP-01.2: Limpar mantém somente Campus. | Reset é `['campus']`, sem mudar KPI. | `tests/test_paginas_publicas.py:246` exige reset Eficiência; `tests/test_paginas_publicas.py:348`–`tests/test_paginas_publicas.py:353` e `tests/test_paginas_publicas.py:461`–`tests/test_paginas_publicas.py:466` exigem Evasão e Percentuais. | ✅ PASS |
| CHIP-02.3: sem eixo mostra Total geral sem erro nem KPI alterado. | Sem linhas de grupo, texto Total geral e total numérico. | `tests/test_paginas_publicas.py:145`–`tests/test_paginas_publicas.py:152`. | ✅ PASS |
| SORT-01.1: tabela inserida/substituída recebe foco, título e `aria-sort=none`. | Cabeçalho ordenável preparado após inserção dinâmica. | `tests/test_js_ordenacao_tabelas.py:146`–`tests/test_js_ordenacao_tabelas.py:164` instancia `MutationObserver`, chama `iniciar(documento)`, injeta a tabela e exige `tabindex`, `aria-sort` e título. | ✅ PASS |
| SORT-01.2: clique, Enter e Espaço alternam direção, `aria-sort` e linhas. | Os três eventos ordenam e atualizam ARIA. | `tests/test_js_ordenacao_tabelas.py:167`–`tests/test_js_ordenacao_tabelas.py:187` chama `iniciar(documento)`, despacha clique, Enter e Espaço e exige prevenção, direção e linhas. | ✅ PASS |
| SORT-02.1: Matrículas ordena blocos raiz sem separar descendentes. | Bloco pai segue com filhos nas duas direções. | `tests/test_js_ordenacao_tabelas.py:51`–`tests/test_js_ordenacao_tabelas.py:75` compara as duas sequências completas. | ✅ PASS |
| SORT-02.2: agrupadora ou `data-no-sort` não ordena. | Coluna Ano PNP permanece excluída. | `tests/test_paginas_publicas.py:174`–`tests/test_paginas_publicas.py:182` exige `data-sortable=true` e `data-no-sort=true`; `tests/test_js_ordenacao_tabelas.py:127`–`tests/test_js_ordenacao_tabelas.py:143` exige que o excluído não receba classe. | ✅ PASS |

**Status**: ✅ PASS. O recorte vazio segue com mensagem informativa em `tests/test_paginas_publicas.py:260`–`tests/test_paginas_publicas.py:269`. Valores vazios permanecem no fim nas duas direções em `tests/test_js_ordenacao_tabelas.py:31`–`tests/test_js_ordenacao_tabelas.py:48`.

## Discrimination Sensor

Sensor leve em worktree descartada. A árvore real ficou idêntica ao baseline após remoção da worktree.

| Mutation | File:line | Description | Killed? |
| --- | --- | --- | --- |
| M1 | `app/components/tabela.py:101` | `data-sortable` de `true` para `false`. | ✅ `tests/test_componentes_publicos.py:120`–`tests/test_componentes_publicos.py:131` falhou. |
| M2 | `app/pages/matriculas.py:249` | Remove `data-no-sort` de Ano PNP. | ✅ `tests/test_paginas_publicas.py:174`–`tests/test_paginas_publicas.py:182` falhou. |
| M3 | `app/static/js/ordenacao-tabelas.js:184` | Desabilita o `MutationObserver` que prepara tabelas inseridas pelo Dash. | ✅ MORTO: `tests/test_js_ordenacao_tabelas.py:146`–`tests/test_js_ordenacao_tabelas.py:164` falhou. |

**Sensor depth**: lightweight. **Result**: 3/3 killed. O teste T9 cobre adicionalmente os eventos delegados de clique, Enter e Espaço.

## Code Quality

| Principle | Status |
| --- | --- |
| Minimum code, mudanças cirúrgicas e padrões existentes | ✅ |
| Cálculos e filtros preservados | ✅ |
| Testes mapeiam aos critérios de chips e blocos | ✅ |
| Cobertura da reinicialização dinâmica exigida por SORT-01 | ✅ |
| Cobertura dos eventos reais exigidos por SORT-01 | ✅ |
| Guidelines followed: `.specs/PROJECT_RULES.md`, `.claude/skills/tlc-spec-driven/references/coding-principles.md` | ✅ |

## Gate Check

- **Gate command**: `uv run pytest -q`.
- **Result**: suíte completa executada após T9; subconjunto da feature: **82 passed, 0 failed**.
- **Test count before feature**: 574.
- **Test count after feature**: 577.
- **Delta**: +3 testes no total; não há teste removido sem justificativa no diff.

## Summary

**Overall**: ✅ PASS. Chips, hierarquia, total, exclusões, inserção dinâmica e os três eventos de ordenação estão cobertos.

**Verdict**: PASS
