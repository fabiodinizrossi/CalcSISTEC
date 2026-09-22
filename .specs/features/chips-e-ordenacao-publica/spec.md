# Chips e ordenação das tabelas públicas — Specification

## Problem Statement

A tabela hierárquica de Matrículas foi marcada como não ordenável, apesar de o
script compartilhado suportar ordenar blocos hierárquicos. Ao mesmo tempo,
Eficiência, Evasão e Percentuais Legais usam controles de eixo diferentes dos
chips de Matrículas. Isso torna a interação inconsistente e permite que uma
atualização dinâmica do Dash faça a ordenação parecer indisponível.

## Goals

- [ ] Os quatro dashboards públicos usam o mesmo seletor de chips para “Ver tabela por”.
- [ ] A ordenação por cabeçalho funciona nas tabelas públicas, inclusive na hierarquia de Matrículas, após toda atualização do Dash.
- [ ] Os cálculos, filtros e estados sem dados existentes permanecem inalterados.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Alterar fórmulas ou metas dos indicadores | A mudança é somente de interação e apresentação. |
| Ordenar grupos internos separadamente dos seus pais | Ordenar o bloco do grupo preserva a hierarquia legível. |
| Persistir eixos ou ordenação entre recargas | Não foi solicitado; o estado continua por sessão Dash. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| “Mesmo comportamento” | Todos os dashboards aceitam múltiplos chips, e a ordem de seleção define a hierarquia. | Jaline confirmou explicitamente que quer chips como os de Matrículas. | y |
| Nenhum chip selecionado | A tabela mostra somente o Total geral, sem erro. | É o comportamento já suportado por Matrículas e mantém um estado coerente. | y |
| Clique em cabeçalho de tabela hierárquica | Ordena somente blocos de nível raiz, mantendo filhos junto ao pai. | O algoritmo compartilhado já implementa essa regra e evita separar a hierarquia. | y |

**Open questions:** none - all resolved or logged above.

## User Stories

### P1: Eixos públicos consistentes ⭐ MVP

**User Story**: Como visitante, quero usar os mesmos chips em todos os dashboards públicos para escolher os recortes da tabela sem reaprender controles.

**Why P1**: A navegação de recortes precisa ter uma linguagem única nas quatro páginas públicas.

**Acceptance Criteria**:

1. WHEN qualquer dashboard público é exibido THEN the system SHALL renderizar “Ver tabela por” com os seis chips compartilhados e Campus selecionado inicialmente. <!-- event-driven -->
2. WHEN o visitante seleciona ou remove chips THEN the system SHALL agrupar a tabela pelos eixos ativos na ordem em que foram selecionados. <!-- event-driven -->
3. WHEN o visitante aciona Limpar Filtros THEN the system SHALL restaurar somente o chip Campus em cada dashboard público. <!-- event-driven -->
4. IF nenhum chip estiver selecionado THEN the system SHALL mostrar o Total geral da tabela sem erro nem KPI alterado. <!-- unwanted-behavior -->

**Independent Test**: Renderizar cada página com fixture, escolher dois eixos em ordens diferentes e conferir a hierarquia, o total e o reset.

---

### P1: Ordenação resiliente ⭐ MVP

**User Story**: Como visitante, quero ordenar as tabelas públicas por cabeçalho mesmo depois que filtros ou eixos atualizam a tabela para comparar os grupos.

**Why P1**: A ordenação desapareceu quando Matrículas foi marcada como não ordenável, quebrando uma interação já entregue.

**Acceptance Criteria**:

1. WHEN uma tabela pública é inserida ou substituída pelo Dash THEN the system SHALL preparar novamente os seus cabeçalhos ordenáveis com foco, título e `aria-sort="none"`. <!-- event-driven -->
2. WHEN o visitante clica ou pressiona Enter/Espaço em um cabeçalho ordenável THEN the system SHALL alternar a direção, atualizar `aria-sort` e reordenar as linhas. <!-- event-driven -->
3. WHEN a tabela de Matrículas tem grupos hierárquicos THEN the system SHALL ordenar os blocos de raiz sem separar seus descendentes. <!-- state-driven -->
4. IF uma coluna for agrupadora ou estiver marcada com `data-no-sort` THEN the system SHALL mantê-la não ordenável. <!-- unwanted-behavior -->

**Independent Test**: Simular a inserção de uma tabela após a inicialização, ordenar um grupo hierárquico por clique e por teclado e conferir blocos, `aria-sort` e cabeçalhos excluídos.

## Edge Cases

- IF o recorte não tiver linhas THEN the system SHALL manter a mensagem informativa existente sem criar cabeçalho ordenável vazio.
- WHEN o mesmo eixo for removido e selecionado novamente THEN the system SHALL colocá-lo no fim da hierarquia ativa.
- WHEN valores vazios forem ordenados THEN the system SHALL mantê-los depois dos valores preenchidos nas duas direções.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| CHIP-01 | P1: Eixos públicos consistentes | Implementing | Pending |
| CHIP-02 | P1: Eixos públicos consistentes | Implementing | Pending |
| SORT-01 | P1: Ordenação resiliente | Implementing | Pending |
| SORT-02 | P1: Ordenação resiliente | Implementing | Pending |

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 4 total, 4 mapped to implementation, 0 unmapped.

## Success Criteria

- [ ] Os quatro dashboards usam chips com os mesmos seis eixos, estado inicial Campus e reset previsível.
- [ ] Matrículas e as três tabelas públicas voltam a ordenar por clique e teclado após recortes e atualizações do Dash.
- [ ] A suíte completa passa sem mudança nos cálculos dos indicadores.
