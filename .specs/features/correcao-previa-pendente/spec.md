# Corrigir prévia pendente sem saída

## Problem Statement

O polling de uma execução em `previa` pode receber uma amostra com `NaN` e falhar no `response.json()`. A tela deixa Salvar e Descartar ocultos, enquanto as rotas de nova atualização respondem `409 previa_pendente`.

## Goals

- [x] A resposta de estado da prévia deve ser JSON válido para o navegador mesmo com valores ausentes ou não finitos na amostra.
- [x] O estado `previa` deve manter uma ação de descarte visível mesmo se o resumo da amostra estiver ausente.

## Out of Scope

- Implementar as páginas públicas de prévia descritas em `previa-paginas-publicas`.
- Alterar a regra de consolidação, cálculo ou publicação.

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Dados ausentes na amostra | Serializar como `null` | Preserva o significado da ausência e permite `response.json()` no navegador. | y |
| Resumo ausente com estado `previa` | Mostrar Descartar e orientar nova atualização após o descarte | A ação encerra a execução pendente pela rota existente. | y |

**Open questions:** none.

## User Stories

### P1: Resolver uma prévia pendente

**User Story**: Como administradora, quero ver as ações da prévia pendente para salvar ou descartar e poder iniciar outra atualização.

**Acceptance Criteria**:

1. WHEN a amostra da prévia contiver valores ausentes ou não finitos THEN the system SHALL devolver JSON válido com esses valores como `null`, mantendo `estado`, `execucao_id` e as contagens da prévia.
2. WHEN o polling receber uma execução em `previa` com resumo válido THEN the system SHALL exibir Salvar na versão interna e Descartar.
3. IF o polling receber `estado=previa` sem resumo THEN the system SHALL manter Descartar visível e acionável para encerrar a execução pendente.
4. WHEN a administradora descartar a prévia pendente THEN the system SHALL liberar uma nova atualização.

**Independent Test**: Criar uma execução em prévia com valores ausentes e não finitos, conferir o JSON com parser estrito, renderizar o estado no JS e descartar antes de uma nova tentativa.

## Edge Cases

- IF a amostra estiver vazia THEN the system SHALL manter Salvar e Descartar disponíveis para a execução válida.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| CPP-01 | P1: Resolver uma prévia pendente | Execute | Implemented |
| CPP-02 | P1: Resolver uma prévia pendente | Execute | Implemented |
| CPP-03 | P1: Resolver uma prévia pendente | Execute | Implemented |
| CPP-04 | P1: Resolver uma prévia pendente | Execute | Implemented |

**Detalhamento:** CPP-01 = JSON válido; CPP-02 = ações com resumo; CPP-03 = descarte sem resumo; CPP-04 = novo envio após descarte.

**Coverage:** 4 requisitos cobertos por testes de rota e interface.

## Project Rules & References

- Princípios III e VII: a amostra não passa a persistir dados pessoais e o ciclo prévia → salvar/descartar continua versionado.
- Princípio IV: o teste de regressão reproduz a falha antes da correção.

## Success Criteria

- [x] O teste de regressão do JSON inválido falha antes da correção e passa depois.
- [x] Os testes do polling, da interface JS e do fluxo administrativo passam.
