# Chips e ordenação das tabelas públicas — Tasks

**Design**: não necessário; a mudança reutiliza o padrão já existente em Matrículas.
**Status**: In Progress (T1 complete)

## Test Coverage Matrix

> Generated from `AGENTS.md`, `.specs/PROJECT_RULES.md`, `tests/`, `requirements.txt` and the specification. Correções começam por teste que reproduz a falha; a suíte completa é o gate antes de publicação.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Componentes Dash | unit | Cada estado de chips, ordem e renderização especificados | `tests/test_componentes_publicos.py` | `uv run pytest -q tests/test_componentes_publicos.py` |
| Páginas Dash | integration | Cada dashboard: eixos múltiplos, reset, total e cálculo preservado | `tests/test_paginas_publicas.py` | `uv run pytest -q tests/test_paginas_publicas.py` |
| JavaScript da tabela | unit | Todos os eventos, hierarquia e exclusões da spec | `tests/test_js_ordenacao_tabelas.py` | `uv run pytest -q tests/test_js_ordenacao_tabelas.py` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Após um componente ou página | `uv run pytest -q tests/test_componentes_publicos.py tests/test_paginas_publicas.py tests/test_js_ordenacao_tabelas.py` |
| Full | Após integração de página | `uv run pytest -q tests/test_paginas_publicas.py tests/test_componentes_publicos.py tests/test_js_ordenacao_tabelas.py` |
| Build | Após a última tarefa | `uv run pytest -q` |

## Execution Plan

### Phase 1: Contrato compartilhado

```
T1 → T2
```

### Phase 2: Adoção nas páginas

```
T2 → T3 → T4 → T5
```

### Phase 3: Ordenação resiliente

```
T5 → T6 → T7
```

## Task Breakdown

### T1: Compartilhar seletor e ordem de chips

**Status**: Complete

**What**: tornar o seletor de eixos um grupo de chips múltiplos e expor a regra de ordem de seleção.
**Where**: `app/components/filters.py`
**Depends on**: None
**Requirement**: CHIP-01, CHIP-02
**Tests**: unit (`tests/test_componentes_publicos.py`)
**Gate**: Quick
**Done when**:

- [x] Os seis eixos são chips com Campus como valor inicial.
- [x] Remover e selecionar novamente um eixo o coloca no fim da ordem ativa.

### T2: Renderizar matriz hierárquica reutilizável

**Status**: Complete

**What**: disponibilizar uma tabela pública que conserve grupos pai-filho e seus atributos de ordenação.
**Where**: `app/components/tabela.py`
**Depends on**: T1
**Requirement**: CHIP-02, SORT-02
**Tests**: unit (`tests/test_componentes_publicos.py`)
**Gate**: Quick
**Done when**:

- [x] A tabela recebe os eixos ativos na ordem escolhida e marca grupos para o script de ordenação.
- [x] Sem eixos, a tabela mostra apenas o total informado.

### T3: Aplicar chips à Eficiência Acadêmica

**Status**: Complete

**What**: substituir o seletor único pelo estado ordenado de chips e agrupar a matriz por todos os eixos ativos.
**Where**: `app/pages/eficiencia.py`
**Depends on**: T2
**Requirement**: CHIP-01, CHIP-02
**Tests**: integration (`tests/test_paginas_publicas.py`)
**Gate**: Full
**Done when**:

- [x] Chips, ordem de clique, hierarquia e reset Campus são observáveis na página.
- [x] O KPI de IEA mantém o cálculo existente.

### T4: Aplicar chips à Taxa de Evasão

**Status**: Complete

**What**: adicionar o seletor e estado ordenado de chips e agrupar a tabela de evasão pelos eixos ativos.
**Where**: `app/pages/evasao.py`
**Depends on**: T3
**Requirement**: CHIP-01, CHIP-02
**Tests**: integration (`tests/test_paginas_publicas.py`)
**Gate**: Full
**Done when**:

- [x] A página possui os mesmos seis chips e reset Campus.
- [x] Taxas e faixas de evasão continuam corretas em cada grupo.

### T5: Aplicar chips aos Percentuais Legais

**Status**: Complete

**What**: usar chips ordenados na tabela exploratória, preservando cartões e total geral.
**Where**: `app/pages/percentuais_legais.py`
**Depends on**: T4
**Requirement**: CHIP-01, CHIP-02
**Tests**: integration (`tests/test_paginas_publicas.py`)
**Gate**: Full
**Done when**:

- [x] A página agrupa por múltiplos eixos na ordem de seleção.
- [x] O reset seleciona somente Campus e os percentuais gerais não mudam.

### T6: Reativar ordenação de blocos em Matrículas

**Status**: Complete

**What**: remover a exclusão da tabela hierárquica e manter colunas agrupadoras não ordenáveis.
**Where**: `app/pages/matriculas.py`
**Depends on**: T5
**Requirement**: SORT-02
**Tests**: integration (`tests/test_paginas_publicas.py`)
**Gate**: Full
**Done when**:

- [x] A tabela hierárquica declara-se ordenável.
- [x] Colunas `data-no-sort` continuam excluídas.

### T7: Garantir reinicialização da ordenação após atualização do Dash

**What**: cobrir a preparação de cabeçalhos inseridos dinamicamente e a ordenação de blocos por clique e teclado.
**Where**: `app/static/js/ordenacao-tabelas.js`
**Depends on**: T6
**Requirement**: SORT-01, SORT-02
**Tests**: unit (`tests/test_js_ordenacao_tabelas.py`)
**Gate**: Build
**Done when**:

- [ ] Uma tabela adicionada depois da inicialização recebe foco, título e `aria-sort`.
- [ ] Clique e teclado alternam direção e nunca separam descendentes do pai.

## Cross-checks

| Dependency declared | Diagram edge | Match |
| --- | --- | --- |
| T2 depends on T1 | T1 → T2 | ✅ |
| T3 depends on T2 | T2 → T3 | ✅ |
| T4 depends on T3 | T3 → T4 | ✅ |
| T5 depends on T4 | T4 → T5 | ✅ |
| T6 depends on T5 | T5 → T6 | ✅ |
| T7 depends on T6 | T6 → T7 | ✅ |

| Task | Test co-located with deliverable | Match |
| --- | --- | --- |
| T1–T2 | Component tests | ✅ |
| T3–T6 | Public-page integration tests | ✅ |
| T7 | JavaScript unit tests | ✅ |
