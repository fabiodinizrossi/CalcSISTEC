# Correções do Painel Público Specification

## Problem Statement

O botão de limpeza precisa restaurar todos os controles alteráveis do painel. Nas páginas com breadcrumb, o grid do shell posiciona o rodapé antes do conteúdo Dash. Percentuais Legais inclui registros de anos diferentes do ano-base publicado.

## Goals

- [ ] Restaurar todos os filtros e o eixo para os valores iniciais de cada página.
- [ ] Manter o rodapé após o conteúdo em Eficiência Acadêmica, Taxa de Evasão Anual e Percentuais Legais.
- [ ] Calcular Percentuais Legais exclusivamente com matrículas do ano-base ativo.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Alterar metas ou fórmulas legais | As regras BR-MIGRAR-009 a BR-MIGRAR-012 permanecem inalteradas. |
| Redesenhar o shell | Apenas o posicionamento do grid será corrigido. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Valores iniciais | Campus e demais selects em `__todos__`, eixo `campus` e FIC no padrão da página | Reproduz os valores definidos no layout existente. | y |
| Ano de Percentuais Legais | `ano_base_ativo()` | É o ano apresentado no cabeçalho e exigido pelo Princípio I. | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Restaurar a visão padrão

**User Story**: Como usuária do painel, quero limpar todos os controles alterados para retornar à visão padrão.

**Why P1**: Evita resultados residuais e torna o painel previsível.

**Acceptance Criteria**:

1. WHEN the user clicks `Limpar Filtros` THEN the system SHALL restore every select, FIC control and axis selector on the current public page to its documented initial value.

**Independent Test**: Chamar cada callback de limpeza e conferir a tupla completa de valores iniciais.

### P1: Exibir o rodapé após o conteúdo

**User Story**: Como usuária, quero ver o rodapé depois da página para que ele não interrompa a leitura do painel.

**Why P1**: O rodapé hoje aparece entre breadcrumb e conteúdo nas três páginas afetadas.

**Acceptance Criteria**:

1. WHILE the viewport is at least 992px wide THEN the system SHALL place breadcrumb, conteúdo principal and footer in consecutive grid areas, with the footer after the content.

**Independent Test**: Conferir a regra CSS do grid e a ausência da regra genérica que auto-posiciona elementos do shell.

### P1: Calcular percentuais no ano publicado

**User Story**: Como usuária, quero que Percentuais Legais use o ano-base do painel para comparar números coerentes com o cabeçalho.

**Why P1**: A mistura de anos viola a paridade de cálculo exigida pelo projeto.

**Acceptance Criteria**:

1. WHEN Percentuais Legais is updated THEN the system SHALL exclude every matrícula whose `ano_base` differs from the active year before calculating cards and table totals.

**Independent Test**: Incluir uma matrícula de outro ano que alteraria o percentual e conferir que ela não altera o cartão nem o total.

## Edge Cases

- IF no matrícula belongs to the active year THEN the system SHALL show the existing message `Sem dados para os filtros selecionados.` instead of zero-valued indicators.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| PUBFIX-01 | Restaurar a visão padrão | Execute | Verified |
| PUBFIX-02 | Exibir o rodapé após o conteúdo | Execute | Pending |
| PUBFIX-03 | Calcular percentuais no ano publicado | Execute | Pending |
| PUBFIX-04 | Ano-base sem registros | Execute | Pending |

**Coverage:** 4 total, 4 mapped to inline execution steps, 0 unmapped.

## Success Criteria

- [ ] Os testes de páginas públicas comprovam os resets e o recorte anual.
- [ ] O teste de CSS comprova a ordem de áreas do shell em desktop.
- [ ] A suíte `pytest` passa.
