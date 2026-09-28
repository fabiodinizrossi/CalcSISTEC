# Correções do Painel Público Validation

**Date**: 2026-09-22
**Spec**: `.specs/features/correcoes-painel-publico/spec.md`
**Diff range**: `ddc8377..0f6149a`
**Verifier**: independent fresh-eyes pass (sub-agent dispatch is disabled by the workspace instruction)

## Task Completion

| Task | Status | Notes |
| --- | --- | --- |
| T1 | ✅ Done | Reset completo documentado por teste. |
| T2 | ✅ Done | Grid do shell corrige a ordem visual. |
| T3 | ✅ Done | Percentuais respeitam o ano-base ativo. |

## Spec-Anchored Acceptance Criteria

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- |
| PUBFIX-01, WHEN the user clicks Limpar Filtros | Todos os selects, FIC e eixo voltam aos padrões de cada página | `tests/test_paginas_publicas.py:66` - `assert pagina("matriculas").limpar_filtros(1) == (...)`; as quatro páginas são verificadas até a linha 75 | ✅ PASS |
| PUBFIX-02, WHILE desktop | Breadcrumb, conteúdo e rodapé usam áreas consecutivas e o rodapé vem depois | `tests/test_style_css.py:110` - `assert re.search(... "menu breadcrumb" ... "menu conteudo" ... "rodape rodape", bloco)`; áreas explícitas nas linhas 114-115 | ✅ PASS |
| PUBFIX-03, WHEN Percentuais Legais is updated | Registros fora do ano ativo não alteram cartões nem total | `tests/test_paginas_publicas.py:481` - `assert "Técnico 0,0%" in textos(cartoes)` e linha 482 - `assert "3,00" in textos(tabela)` | ✅ PASS |
| PUBFIX-04, IF no matrícula belongs to the active year | Mostra `Sem dados para os filtros selecionados.` e não indicadores | `tests/test_paginas_publicas.py:490` - `assert "Sem dados para os filtros selecionados." in textos(cartoes)` e linha 491 - `assert textos(tabela) == ""` | ✅ PASS |

**Status**: ✅ All ACs covered.

## Discrimination Sensor

| Mutation | File:line | Description | Killed? |
| --- | --- | --- | --- |
| 1 | `app/pages/percentuais_legais.py:112` | In a temporary git worktree, changed `== ano_base` to `!= ano_base` | ✅ Killed by `test_percentuais_ignora_matricula_de_outro_ano_base` |

**Sensor depth**: lightweight.
**Result**: 1/1 killed, PASS ✅. The real-tree porcelain before and after the sensor contained only pre-existing untracked local directories.

## Code Quality

| Principle | Status |
| --- | --- |
| Minimum code | ✅ |
| Surgical changes | ✅ |
| No scope creep | ✅ |
| Matches patterns | ✅ |
| Spec-anchored outcome check | ✅ |
| Tests map to requirements | ✅ |
| Project guidelines followed: `.specs/PROJECT_RULES.md` | ✅ |

## Gate Check

- **Targeted commands**: `pytest tests/test_paginas_publicas.py -q` and `pytest tests/test_style_css.py -q`
- **Result**: 34 + 44 passed, 0 failed.
- **Full-suite note**: `pytest` at the repository root is invalid because archived `APAGAR/` directories deny collection. The host did not return a terminal summary for the longer `pytest tests -q` run; the feature's complete test surface passed in the targeted gates above.

## Summary

**Overall**: ✅ Ready.

The public-panel resets are regression-tested, the desktop grid puts the footer after Dash content, and Percentuais Legais filters to the active year before calculating.
