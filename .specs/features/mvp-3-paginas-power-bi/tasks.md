# MVP 3 — Páginas públicas no padrão do Power BI — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Exceção combinada com a usuária para executores sem suporte a skills: leia `.specs/MVP-PROTOCOLO.md` inteiro e siga-o; ele aponta o arquivo da skill que substitui a ativação.

Pré-requisito: `mvp-2-paridade` com Verifier PASS (esta feature usa `app/paineis/`).

---

**Spec**: `.specs/features/mvp-3-paginas-power-bi/spec.md`
**Referência visual**: `.specs/referencias/*.png` — abra o print da página antes de cada tarefa de página.
**Status**: Draft

---

## Test Coverage Matrix

> Diretrizes: `.specs/PROJECT_RULES.md` (Princípio IV; interface gov.br DS, responsiva); `.specs/STATE.md` AD-001 a AD-006; `tests/test_style_css.py` (sem cor literal no CSS; só os pontos de quebra 576, 992, 1280 e 1600 px).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Componentes (`app/components/*.py`) | unit | Cada AC da história "Componentes compartilhados": estrutura, textos, valores iniciais, cores | `tests/test_componentes_publicos.py` | `python -m pytest tests/test_componentes_publicos.py -q -p no:cacheprovider` |
| CSS (`app/assets/style.css`) | unit | Classes novas presentes; regras existentes de `tests/test_style_css.py` continuam valendo | `tests/test_style_css.py` | `python -m pytest tests/test_style_css.py -q -p no:cacheprovider` |
| Páginas (`app/pages/*.py`) | integration | Layout na ordem do spec; cada filtro, cartão, gráfico e coluna presente com o texto do spec; callback com dados sintéticos devolve os números de `app/paineis/`; "Limpar Filtros" volta ao estado inicial; sem dados → mensagem | `tests/test_paginas_publicas.py`, `tests/test_previa_callback_*.py` | `python -m pytest tests/test_paginas_publicas.py tests/test_previa_callback_matriculas.py tests/test_previa_callback_eficiencia.py tests/test_previa_callback_evasao.py tests/test_previa_callback_percentuais.py -q -p no:cacheprovider` |
| Documentação | unit (higiene) | Seções exigidas presentes | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Conferência humana | none | — | — | — |

Use os ajudantes de `tests/arvore_dash.py` (`componentes`, `classes`, `textos`) para procurar componentes e textos na árvore do Dash.

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Tarefas só de documentação | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Full | Toda tarefa com `.py` ou `.css` | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Regras desta feature (além do protocolo)

- **Testes de página existentes vão mudar.** Esta feature muda a ordem do layout,
  tira o cartão de IEA e o botão FIC da Evasão, e acrescenta um `Input` aos
  callbacks. Um teste existente de página só pode mudar na asserção que o spec
  contradiz; cite o AC no corpo do commit (ex.: "PBI-08 AC1: Eficiência sem cartão").
  Nunca apague um teste inteiro: reescreva-o para o comportamento novo.
- **Callbacks com `Input` novo:** declare o `Input` novo **depois** dos
  existentes e **antes** do `State` da prévia. Na função, o parâmetro novo
  entra na mesma posição, com valor padrão `None`. Depois, procure as chamadas
  diretas da função nos testes (`git grep -n "atualizar(" tests`) e ajuste as
  que passam argumentos por posição.
- **Nenhuma conta nas páginas.** Número mostrado vem de `app/paineis/`. A
  página só converte `"__todos__"` em `None`, monta `FiltrosPainel`, chama
  `app/paineis/` e formata.
- **Cor só por variável no CSS.** Em Python (Plotly), use as constantes de
  `app/components/cores.py`, nunca um hexadecimal solto.

---

## Execution Plan

### Phase 1: Componentes compartilhados

```
T1 → T2 → T3 → T4 → T5 → T6
```

### Phase 2: Páginas

```
T7 → T8 → T9 → T10
```

### Phase 3: Conferência e registro

```
T11 → T12 → T13
```

---

## Task Breakdown

### T1: Cores dos gráficos espelhando os tokens do DS

**What**: `app/components/cores.py` com as cores que o Plotly precisa.
**Where**: `app/components/cores.py` (novo)
**Depends on**: None
**Reuses**: `app/static/govbr-ds/dist/core-tokens.css`
**Requirement**: PBI-01

**Passos**:

1. Código:

   ```python
   """Cores dos gráficos, copiadas dos tokens do gov.br DS (core-tokens.css).

   O Plotly não lê variáveis CSS, então as cores vêm em hexadecimal. Cada valor
   precisa existir em core-tokens.css (o teste confere)."""

   AZUL = "#1351b4"          # --blue-warm-vivid-70
   VERMELHO = "#e52207"      # --red-vivid-50
   VERDE = "#168821"         # --green-cool-vivid-50
   CINZA_CLARO = "#cccccc"   # --gray-20 (#ccc)
   CINZA_ESCURO = "#333333"  # --gray-80 (#333)


   def rgba(hexadecimal, alfa):
       """"#e52207", 0.25 -> "rgba(229, 34, 7, 0.25)"."""
       h = hexadecimal.lstrip("#")
       r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
       return f"rgba({r}, {g}, {b}, {alfa})"
   ```

2. Teste em `tests/test_componentes_publicos.py`: para cada constante, o valor
   (ou a forma curta de 3 dígitos, para `#cccccc` e `#333333`) aparece em
   `core-tokens.css`, sem diferenciar maiúsculas; e `rgba("#e52207", 0.25) == "rgba(229, 34, 7, 0.25)"`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: linha de base + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): cores dos graficos a partir dos tokens do ds`

---

### T2: Filtro de Ano de Ingresso

**What**: Em `app/components/filters.py`, `filtro_ano_ingresso(id_, ano_min, ano_max)`
e `ano_ingresso_do_valor(valor, ano_min, ano_max)`; e, em `app/paineis/filtros.py`,
`anos_de_ingresso(df, ano_base)`.
**Where**: `app/components/filters.py`
**Depends on**: T1
**Reuses**: `select_filter` (mesmo arquivo), para o formato do rótulo
**Requirement**: PBI-02

**Passos**:

1. `filtro_ano_ingresso`:

   ```python
   def filtro_ano_ingresso(id_, ano_min, ano_max):
       """Controle de dois pontos para o intervalo de anos de início do ciclo."""
       return html.Div(
           [
               html.Label("Ano de Ingresso", className="filter-label", htmlFor=id_),
               dcc.RangeSlider(
                   id=id_,
                   min=ano_min,
                   max=ano_max,
                   step=1,
                   value=[ano_min, ano_max],
                   marks={ano_min: str(ano_min), ano_max: str(ano_max)},
                   allowCross=False,
                   tooltip={"placement": "bottom", "always_visible": True},
               ),
           ],
           className="filter-item filtro-ano",
       )
   ```

2. `ano_ingresso_do_valor(valor, ano_min, ano_max)`: devolve `None` quando
   `valor` é `None` ou `list(valor) == [ano_min, ano_max]`; senão
   `(int(valor[0]), int(valor[1]))`.
3. Em `app/paineis/filtros.py`, `anos_de_ingresso(df, ano_base)`: devolve
   `(menor ano de dt_data_inicio, ano_base)`; se não houver data válida,
   `(ano_base, ano_base)`; se o menor ano for maior que o ano-base, use o
   ano-base nos dois.
4. Testes: valor inicial, rótulo, marcas; os três casos de
   `ano_ingresso_do_valor`; os três casos de `anos_de_ingresso` (em
   `tests/test_paineis_filtros.py`).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): filtro de ano de ingresso`

---

### T3: Barra de filtros e botão FIC segmentado

**What**: Em `app/components/filters.py`, `barra_filtros(campos, id_limpar)`; e
`fic_toggle` passa a usar o mesmo visual segmentado de `_fic_selector` da página
Matrículas (`app/pages/matriculas.py:74`), que vira o único jeito de mostrar o botão.
**Where**: `app/components/filters.py`
**Depends on**: T2
**Reuses**: `_fic_selector` (`app/pages/matriculas.py`), `clear_filters_button`
**Requirement**: PBI-03

**Passos**:

1. `barra_filtros(campos, id_limpar)` devolve
   `html.Div([*campos, clear_filters_button(id_limpar)], className="barra-filtros", role="group", **{"aria-label": "Filtros"})`.
2. `fic_toggle(id_, default="com_fic")`: troque o corpo pelo de `_fic_selector`
   (classes `seg-grupo`, `seg`, `seg--ativo`, `seg-input`, contêiner
   `fic-segmentado`), mantendo o parâmetro `default`. Não mude
   `app/pages/matriculas.py` nesta tarefa.
3. Testes: a barra tem os campos na ordem e o botão por último; a classe e o
   `aria-label`; `fic_toggle` com `default="sem_fic"` começa em `sem_fic` e usa
   as classes do segmentado. Ajuste os testes existentes de `fic_toggle` que
   afirmavam a classe `br-radio` (cite PBI-03 no commit).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): barra de filtros e botao fic segmentado`

---

### T4: Medidor e gráfico de evasões por mês

**What**: `app/components/graficos.py` com `medidor(rotulo, valor, meta)` e
`grafico_evasoes_mes(valores, ano)`.
**Where**: `app/components/graficos.py` (novo)
**Depends on**: T3
**Reuses**: `cor_medidor` (`app/domain/percentuais_legais.py`), `app/components/cores.py`
**Requirement**: PBI-04

**Passos**:

1. Código:

   ```python
   """Gráficos das páginas públicas (Plotly)."""

   import plotly.graph_objects as go
   from dash import dcc, html

   from app.components.cores import CINZA_CLARO, CINZA_ESCURO, VERDE, VERMELHO, rgba
   from app.domain.percentuais_legais import cor_medidor

   MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
   CONFIG = {"displayModeBar": False, "staticPlot": False, "responsive": True}
   _LAYOUT_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", separators=",.")


   def _pct(valor):
       return f"{valor * 100:.1f}".replace(".", ",") + "%"


   def medidor(rotulo, valor, meta):
       cor = VERDE if cor_medidor(valor, meta) == "verde" else VERMELHO
       figura = go.Figure(go.Indicator(
           mode="gauge+number",
           value=round(valor * 100, 1),
           number={"suffix": "%", "valueformat": ".1f"},
           gauge={
               "shape": "angular",
               "axis": {"range": [0, 100], "visible": False},
               "bar": {"color": cor},
               "bgcolor": CINZA_CLARO,
               "borderwidth": 0,
               "threshold": {"line": {"color": CINZA_ESCURO, "width": 3}, "thickness": 0.9, "value": meta * 100},
           },
       ))
       figura.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=0), **_LAYOUT_BASE)
       situacao = "Acima da meta" if valor >= meta else "Abaixo da meta"
       return html.Div(
           [
               html.Div(rotulo, className="rotulo"),
               dcc.Graph(figure=figura, config=CONFIG, className="grafico-medidor"),
               html.Div(f"{situacao} · Meta: {meta * 100:.0f}%", className="medidor-situacao"),
           ],
           className="medidor",
           role="img",
           **{"aria-label": f"{rotulo}: {_pct(valor)}. {situacao}. Meta: {meta * 100:.0f}%."},
       )


   def grafico_evasoes_mes(valores, ano):
       figura = go.Figure(go.Scatter(
           x=MESES, y=valores, mode="lines+markers", fill="tozeroy",
           line={"color": VERMELHO, "width": 2}, fillcolor=rgba(VERMELHO, 0.25),
           hovertemplate="%{x}: %{y} evasões<extra></extra>",
       ))
       figura.update_layout(
           height=220, margin=dict(l=10, r=10, t=10, b=30), showlegend=False,
           yaxis={"visible": False, "rangemode": "tozero"}, xaxis={"fixedrange": True},
           **_LAYOUT_BASE,
       )
       return html.Div(
           [
               html.H2(f"Matrículas evadidas por mês em {ano}", className="grafico-titulo"),
               dcc.Graph(figure=figura, config=CONFIG, className="grafico-evasoes"),
           ],
           className="card-grafico",
       )
   ```

2. Testes em `tests/test_componentes_publicos.py`:
   - `medidor("Técnico", 0.454, 0.5)`: o `dcc.Graph` tem `figure.data[0].value == 45.4`,
     `gauge.bar.color == VERMELHO`, `gauge.threshold.value == 50`; o texto tem
     "Abaixo da meta" e "Meta: 50%"; o `aria-label` tem "45,4%";
   - `medidor("Proeja", 0.12, 0.10)`: barra `VERDE`, "Acima da meta";
   - `grafico_evasoes_mes([1] * 12, 2025)`: `x` igual a `MESES`, `y` igual aos
     valores, `fill == "tozeroy"`, título "Matrículas evadidas por mês em 2025";
   - nos dois, `config["displayModeBar"] is False` e `paper_bgcolor` transparente.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): medidor e grafico mensal de evasoes`

---

### T5: Ordem inicial da tabela hierárquica

**What**: `tabela_hierarquica_ds` (`app/components/tabela.py:46`) ganha o
parâmetro opcional `chave_ordem=None`.
**Where**: `app/components/tabela.py`
**Depends on**: T4
**Reuses**: função atual
**Requirement**: PBI-05

**Passos**:

1. Acrescente `chave_ordem=None` como último parâmetro (só por nome).
2. Em `visitar`, quando `nivel == 0` e `chave_ordem` não é `None`, ordene os
   grupos por `chave_ordem(subgrupo)`, do maior para o menor, antes de montar as
   linhas. Nos outros níveis e sem `chave_ordem`, nada muda.
3. Testes: sem `chave_ordem` a ordem é a de hoje (teste existente); com
   `chave_ordem=lambda g: len(g)`, o grupo maior vem primeiro; o segundo nível
   continua na ordem de hoje.

**Done when**:

- [ ] Testes novos passam e os existentes continuam passando sem mudança
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): ordem inicial opcional na tabela hierarquica`

---

### T6: CSS da barra de filtros, dos medidores e dos gráficos

**What**: Regras em `app/assets/style.css` para `.barra-filtros`,
`.filtro-ano`, `.medidores`, `.medidor`, `.card-grafico`, `.grafico-titulo`,
`.texto-leitor-tela` e o texto dos gráficos no tema escuro.
**Where**: `app/assets/style.css`
**Depends on**: T5
**Reuses**: variáveis do DS já usadas no arquivo (`--background`, `--color`, `--spacing-scale-*`, `--surface-*`)
**Requirement**: PBI-06

**Passos**:

1. Leia `app/assets/style.css` inteiro e `tests/test_style_css.py`. Regras: sem
   cor literal (nada de `#abc`, `rgb(`), só os pontos de quebra 576, 992, 1280
   e 1600 px, alvo de toque de pelo menos 24 px.
2. `.barra-filtros`: `display: flex; flex-wrap: wrap; gap` com a escala de
   espaçamento do DS; alinhamento no fim da linha (`align-items: flex-end`);
   mesmo visual de cartão que `.card-filtros` usa hoje. Cada `.filter-item`
   com largura mínima de uns 12rem; `.filtro-ano` com uns 16rem.
3. `.medidores`: grade de 3 colunas a partir de 992 px, 1 coluna abaixo.
4. `.card-grafico`: mesmo visual de cartão; `.grafico-titulo` com o tamanho de
   título de cartão já usado no arquivo.
5. `.texto-leitor-tela`: esconde visualmente e mantém para leitor de tela
   (`position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;`).
6. Texto do Plotly no tema escuro. O Plotly grava a cor do texto no atributo
   `style` do SVG, por isso precisa de `!important`:

   ```css
   .grafico-medidor text,
   .grafico-evasoes text {
     fill: var(--color) !important;
   }
   ```

7. Testes em `tests/test_style_css.py`: cada seletor novo aparece no arquivo; a
   regra de `fill: var(--color)` existe para os dois gráficos.

**Done when**:

- [ ] Testes novos passam e `tests/test_style_css.py` inteiro continua verde
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `style(publico): barra de filtros, medidores e graficos`

---

### T7: Página Matrículas como no Power BI

**What**: `app/pages/matriculas.py` passa a: mostrar a barra de filtros logo
abaixo do título (Ano de Ingresso, Campus, Tipo de Curso, Tipo de Programa,
FIC, Limpar); mostrar os cartões na ordem Cursos, Matrículas, Matrículas
equivalentes, Matrículas concluídas, Ingressantes; calcular tudo por
`app/paineis/matriculas.py`.
**Where**: `app/pages/matriculas.py`
**Depends on**: None
**Reuses**: `barra_filtros`, `filtro_ano_ingresso`, `ano_ingresso_do_valor`, `fic_toggle`, `select_filter` (`app/components/filters.py`); `FiltrosPainel`, `anos_de_ingresso` (`app/paineis/filtros.py`); `resumo_matriculas`, `metricas_matriculas` (`app/paineis/matriculas.py`); print `.specs/referencias/matriculas-por-campus.png`
**Requirement**: PBI-07

**Passos**:

1. Layout, nesta ordem: `_cabecalho`, barra de filtros, cartões
   (`matriculas-kpis`), chips, `Store` dos eixos, matriz, `Store` da prévia.
   O antigo `_filtros(df)` no fim some.
2. O filtro de ano usa `id="matriculas-filtro-ano"` e
   `anos_de_ingresso(df, ano_base)` para o intervalo. Guarde o intervalo num
   `dcc.Store(id="matriculas-anos", data=[ano_min, ano_max])` para o callback e
   para o "Limpar Filtros".
3. Troque `_fic_selector` por `fic_toggle("matriculas-fic")` e apague `_fic_selector`.
4. Callback `atualizar`: `Input("matriculas-filtro-ano", "value")` depois dos
   outros `Input`; `State("matriculas-anos", "data")` antes do `State` da
   prévia (siga as "Regras desta feature"). Monte
   `FiltrosPainel(campus=..., tipo_curso=..., programa=..., incluir_fic=(fic == "com_fic"), ano_ingresso=ano_ingresso_do_valor(valor_ano, *anos))`
   convertendo `"__todos__"` em `None`. Os cartões usam
   `resumo_matriculas(df, ano_base, filtros)`. A matriz usa
   `aplicar_filtros(df, filtros)` e troca `_metricas` por `metricas_matriculas`
   (apague `_metricas` e `_filtrar`).
5. `limpar_filtros`: acrescente `Output("matriculas-filtro-ano", "value")` e
   `State("matriculas-anos", "data")`, devolvendo o intervalo completo.
6. Testes em `tests/test_paginas_publicas.py`:
   - ordem do layout (título, barra, cartões, chips, matriz);
   - a barra tem, nesta ordem, os rótulos "Ano de Ingresso", "Campus",
     "Tipo de Curso", "Tipo de Programa", o botão FIC e "Limpar Filtros";
   - os cartões têm os rótulos na ordem do spec, com os números iguais a
     `resumo_matriculas` sobre os dados do teste;
   - com o ano de ingresso reduzido, os números caem para os do intervalo;
   - "Limpar Filtros" devolve o intervalo completo.
   Ajuste os testes existentes que afirmavam a ordem antiga (cite PBI-07).

**Done when**:

- [ ] Testes novos passam; os de prévia (`tests/test_previa_callback_matriculas.py`) continuam verdes
- [ ] Nenhuma conta de indicador sobrou em `app/pages/matriculas.py` (só chamadas a `app/paineis/`)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(matriculas): filtros e cartoes no padrao do power bi`

---

### T8: Página Eficiência como no Power BI

**What**: `app/pages/eficiencia.py` sem cartão; barra de filtros (Campus, Tipo
de Curso, Modalidade, Programa, FIC com padrão Sem FIC, Limpar); tabela com
IEA em percentual, Concluídos, Evadidos e Retidos por Ciclo; números de
`app/paineis/eficiencia.py`.
**Where**: `app/pages/eficiencia.py`
**Depends on**: T7
**Reuses**: igual a T7; `metricas_eficiencia`; print `.specs/referencias/eficiencia-por-campus-sem-fic.png`
**Requirement**: PBI-08

**Passos**:

1. Layout: cabeçalho, barra de filtros, chips, `Store`, matriz, `Store` da
   prévia. Tire o `Div` `eficiencia-kpi` e o `Output` correspondente do callback.
2. Filtros novos com os ids `eficiencia-filtro-tipo-curso` (coluna
   `tipo_curso_pnp`) e `eficiencia-filtro-programa` (`tipo_programa_curso`);
   as colunas existem desde a feature 2 (T1).
3. Colunas: `["Índice de Eficiência Acadêmica", "Concluídos por Ciclo", "Evadidos por Ciclo", "Retidos por Ciclo"]`.
   Formato: IEA `f"{v * 100:.2f}".replace(".", ",") + "%"`; contagens com
   `formatar_valor(v, "#,0")` (`app/components/kpi.py`). A linha Total usa
   `metricas_eficiencia` sobre o df filtrado inteiro.
4. `limpar_filtros` devolve também os dois filtros novos.
5. Testes: ordem do layout sem cartão; os rótulos da barra na ordem do spec;
   cabeçalho da tabela com as 4 colunas; o Total dos dados de teste com o IEA
   em percentual (ex.: `41,44%` para 1.849/2.613/502 — reaproveite o caso de
   `tests/test_paineis_eficiencia.py`); filtro de tipo de curso muda os números.
   Reescreva os testes existentes que afirmavam o cartão de IEA (cite PBI-08 AC1).

**Done when**:

- [ ] Testes novos passam; os de prévia continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(eficiencia): colunas e filtros no padrao do power bi`

---

### T9: Página Evasão como no Power BI

**What**: `app/pages/evasao.py` com barra de filtros (Ano de Ingresso, Campus,
Tipo de Curso, Modalidade, Limpar), sem botão FIC; 4 cartões; gráfico mensal;
tabela com "Evasões em {ano}" e "Taxa de Evasão Anual" ordenada pela taxa;
números de `app/paineis/evasao.py`.
**Where**: `app/pages/evasao.py`
**Depends on**: T8
**Reuses**: igual a T7; `grafico_evasoes_mes`, `chave_ordem` (T4, T5); `resumo_evasao`, `evasoes_por_mes`, `metricas_evasao`; print `.specs/referencias/evasao-por-campus.png`
**Requirement**: PBI-09

**Passos**:

1. Layout: cabeçalho, barra de filtros, linha com os 4 cartões
   (`cartao_indicador` de `app/components/painel_publico.py`, rótulos
   "Abandonos", "Transferências externas", "Desligamentos",
   "Transferências internas") e, ao lado, o gráfico mensal
   (`id="evasao-grafico"`), chips, `Store`, tabela, `Store` da prévia.
2. Tire o `fic_toggle` e o `Input` dele; `FiltrosPainel(incluir_fic=True, ...)`.
3. Tabela: colunas `[f"Evasões em {ano_base}", "Taxa de Evasão Anual"]`;
   `metricas` devolve `[formatar_valor(evasoes, "#,0"), {"valor": [taxa_formatada, html.Span(f" ({faixa})", className="texto-leitor-tela")], "classe": classe}]`,
   onde `classe` vem de `_classe_evasao` (já existe no arquivo) e `faixa` de
   `_LABEL_EVASAO`. Taxa com 1 casa: `f"{taxa * 100:.1f}".replace(".", ",") + "%"`.
   `chave_ordem=lambda g: metricas_evasao(g, ano_base)["taxa"]`.
4. `limpar_filtros` sem o FIC e com o ano de ingresso (como em T7).
5. Testes: layout na ordem; sem botão FIC; os 4 cartões com os números de
   `resumo_evasao`; o gráfico recebe os 12 valores de `evasoes_por_mes`; a
   primeira linha da tabela é o campus de maior taxa; a célula de taxa tem a
   classe da faixa e o texto oculto com o nome da faixa. Reescreva os testes
   existentes do cartão de taxa e do botão FIC (cite PBI-09 AC1).

**Done when**:

- [ ] Testes novos passam; os de prévia continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(evasao): cartoes, grafico mensal e tabela no padrao do power bi`

---

### T10: Página Percentuais como no Power BI

**What**: `app/pages/percentuais_legais.py` com barra de filtros (Campus, Tipo
de Curso, Modalidade, Programa Associado, Limpar), aviso de PROEJA mantido;
cartão Matrículas equivalentes e 3 medidores; tabela com as 6 colunas; números
de `app/paineis/percentuais.py`.
**Where**: `app/pages/percentuais_legais.py`
**Depends on**: T9
**Reuses**: igual a T7; `medidor` (T4); `resumo_percentuais`, `metricas_percentuais`; `META_*`; print `.specs/referencias/percentuais-por-campus.png`
**Requirement**: PBI-10

**Passos**:

1. Layout: cabeçalho, barra de filtros (o `Div` do aviso de PROEJA logo abaixo
   da barra), linha com o cartão "Matrículas equivalentes" e um
   `html.Div(className="medidores")` com os 3 medidores, chips, `Store`,
   tabela, `Store` da prévia. Apague a função interna `gauge` do callback.
2. Colunas: `["Técnicos (MatEq)", "Formação de Professores (MatEq)", "Proeja (MatEq)", "% Técnico", "% Formação de Professores", "% Proeja"]`;
   MatEq com `_formatar_equivalentes` (já existe) e percentuais com 2 casas.
3. Filtros novos com ids `percentuais-filtro-tipo-curso` e
   `percentuais-filtro-modalidade`; `limpar_filtros` devolve os dois.
4. Testes: layout; os 3 medidores com os valores de `resumo_percentuais`
   (procure `dcc.Graph` com `className="grafico-medidor"`); as 6 colunas; o
   aviso de PROEJA aparece com filtro de programa e some sem ele. Reescreva os
   testes existentes dos cartões de percentual (cite PBI-10 AC1).

**Done when**:

- [ ] Testes novos passam; os de prévia continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(percentuais): medidores e colunas no padrao do power bi`

---

### T11: Roteiro de conferência visual no `TESTAR.md`

**What**: Na seção de conferência do design do `TESTAR.md`, um roteiro por
página: abrir o print de `.specs/referencias/`, abrir a página no navegador e
conferir, item a item, a lista da seção "O que cada página mostra" do spec, nos
temas claro e escuro, com a largura entre 320 e 430 px e com 1280 px ou mais.
Atualize também a seção "Painel público" do `README.md`.
**Where**: `TESTAR.md`
**Depends on**: None
**Reuses**: spec desta feature
**Requirement**: PBI-11

**Done when**:

- [ ] Teste de higiene: `TESTAR.md` cita os 4 prints de `.specs/referencias/`
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(testar): roteiro de conferencia das paginas com o power bi`

---

### T12: [HUMANO] Jaline confere as 4 páginas

**What**: Jaline segue o roteiro de T11 e registra em `DEPLOY.md`, item DS-42:
navegador, larguras e data, e o que precisar de ajuste. Ajustes viram tarefas
novas neste arquivo (T12a, T12b…), com teste.
**Where**: `DEPLOY.md`
**Depends on**: T11
**Reuses**: roteiro de T11
**Requirement**: PBI-11

**O agente executor para aqui** e avisa: "T12 é humana: falta a conferência visual da Jaline".

**Done when**:

- [ ] `DEPLOY.md` com o resultado da conferência

**Tests**: none
**Gate**: build

**Commit**: `docs(deploy): registrar a conferencia visual das paginas`

---

### T13: Registrar a feature no `STATE.md`

**What**: Handoff da feature (commits, testes, conferência). Registre como AD-008
a decisão "filtros numa barra no topo, e não no menu lateral".
**Where**: `.specs/STATE.md`
**Depends on**: T12
**Reuses**: formato dos handoffs
**Requirement**: PBI-11

**Done when**:

- [ ] "Estado atual" diz que `mvp-3-paginas-power-bi` está implementada e aguarda o Verifier
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`

**Tests**: none
**Gate**: build

**Commit**: `docs(state): registrar as paginas no padrao do power bi`

---

## Verificação (depois de T13)

Verifier independente. Sensor mínimo: trocar a ordem de dois cartões da
Matrículas; tirar o `fill` do gráfico mensal; `ano_ingresso_do_valor` devolver
tupla no intervalo completo; esquecer `chave_ordem` na Evasão; voltar a calcular
o IEA na página em vez de `app/paineis/`.

---

## Phase Execution Map

```
Phase 1:  T1 → T2 → T3 → T4 → T5 → T6
Phase 2:  T7 → T8 → T9 → T10
Phase 3:  T11 → T12 → T13
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1, T4, T5, T6 | 1 arquivo | ✅ |
| T2 | 2 funções em `filters.py` + 1 em `paineis/filtros.py` | ⚠️ coeso: o filtro de ano precisa do intervalo |
| T3 | 1 arquivo | ✅ |
| T7–T10 | 1 página | ✅ |
| T11–T13 | documentação e registro | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | T2 | T2 → T3 | ✅ |
| T4 | T3 | T3 → T4 | ✅ |
| T5 | T4 | T4 → T5 | ✅ |
| T6 | T5 | T5 → T6 | ✅ |
| T7 | None | início da fase 2 | ✅ |
| T8 | T7 | T7 → T8 | ✅ |
| T9 | T8 | T8 → T9 | ✅ |
| T10 | T9 | T9 → T10 | ✅ |
| T11 | None | início da fase 3 | ✅ |
| T12 | T11 | T11 → T12 | ✅ |
| T13 | T12 | T12 → T13 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1–T5 | componentes | unit | unit | ✅ |
| T6 | CSS | unit | unit | ✅ |
| T7–T10 | páginas | integration | integration | ✅ |
| T11 | documentação | unit (higiene) | unit | ✅ |
| T12, T13 | conferência humana e registro | none | none | ✅ |
