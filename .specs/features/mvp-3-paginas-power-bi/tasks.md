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

> Diretrizes: `.specs/PROJECT_RULES.md` (Princípio IV; interface gov.br DS, responsiva); `.specs/STATE.md` AD-001 a AD-006; `tests/test_style_css.py` (sem cor literal no CSS; só os pontos de quebra 576, 992, 1280 e 1600 px; alvo de toque de 24 px).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Componentes (`app/components/*.py`) | unit | Cada AC das histórias "Componentes" e "Coluna lateral": estrutura, textos, atributos, valores iniciais, cores | `tests/test_componentes_publicos.py`, `tests/test_lateral_painel.py` | `python -m pytest tests/test_componentes_publicos.py tests/test_lateral_painel.py -q -p no:cacheprovider` |
| Dados (`app/data/config_store.py`) | unit | `tem_logo_personalizado` nos dois casos | `tests/test_config_store.py` | `python -m pytest tests/test_config_store.py -q -p no:cacheprovider` |
| Shell (templates Jinja) | integration | Página pública sem `_menu.html`, com a classe no `<body>` e o botão com `data-toggle="menu-painel"`; telas administrativas como hoje | `tests/test_shell_parciais.py` | `python -m pytest tests/test_shell_parciais.py -q -p no:cacheprovider` |
| JavaScript (`menu.js`) | integration (node) | Abrir, fechar pelo botão, fechar pelo `data-dismiss`, fechar com `Esc`, `aria-expanded`, foco de volta | `tests/test_js_menu.py` | `python -m pytest tests/test_js_menu.py -q -p no:cacheprovider` |
| CSS (`app/assets/style.css`) | unit | Seletores novos presentes; regras de `tests/test_style_css.py` continuam valendo | `tests/test_style_css.py` | `python -m pytest tests/test_style_css.py -q -p no:cacheprovider` |
| Páginas (`app/pages/*.py`) | integration | Layout (lateral + conteúdo) na ordem do spec; cada filtro, cartão, gráfico e coluna com o texto do spec; callback com dados sintéticos devolve os números de `app/paineis/`; "Limpar Filtros"; sem dados → mensagem | `tests/test_paginas_publicas.py`, `tests/test_previa_callback_*.py` | `python -m pytest tests/test_paginas_publicas.py tests/test_previa_callback_matriculas.py tests/test_previa_callback_eficiencia.py tests/test_previa_callback_evasao.py tests/test_previa_callback_percentuais.py -q -p no:cacheprovider` |
| Documentação | unit (higiene) | Seções exigidas presentes | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Conferência humana | none | — | — | — |

Use os ajudantes de `tests/arvore_dash.py` (`componentes`, `classes`, `textos`) para procurar componentes e textos na árvore do Dash.

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Tarefas só de documentação | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Full | Toda tarefa com `.py`, `.html`, `.js` ou `.css` | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Regras desta feature (além do protocolo)

- **Testes existentes vão mudar.** Esta feature muda o layout das páginas, tira
  o menu Jinja das páginas públicas, tira o cartão de IEA e acrescenta `Input`s
  aos callbacks. Um teste existente só pode mudar na asserção que o spec
  contradiz; cite o AC no corpo do commit (ex.: "PBI-12 AC1: Eficiência sem
  cartão"). Nunca apague um teste inteiro: reescreva-o para o comportamento novo.
- **Callbacks com `Input` novo:** declare o `Input` novo **depois** dos
  existentes e **antes** do `State` da prévia. Na função, o parâmetro novo entra
  na mesma posição, com valor padrão `None`. Depois, procure as chamadas diretas
  da função nos testes (`git grep -n "atualizar(" tests`) e ajuste as que passam
  argumentos por posição.
- **Nenhuma conta nas páginas.** Número mostrado vem de `app/paineis/`. A página
  só converte `"__todos__"` em `None`, monta `FiltrosPainel`, chama
  `app/paineis/` e formata.
- **Cor só por variável no CSS.** Em Python (Plotly), use as constantes de
  `app/components/cores.py`, nunca um hexadecimal solto.
- **Layout comum das páginas públicas** (T11 a T14):

  ```python
  html.Div(
      [
          lateral_painel(CAMINHO, filtros_laterais([...], "<pagina>-limpar"),
                         preview=preview_id is not None, logo=logo_da_lateral()),
          html.Div([...conteúdo...], className="painel-conteudo"),
      ],
      className="painel-com-lateral",
  )
  ```

  `CAMINHO` é o `path` com que a página se registra (`"/"`, `"/eficiencia"`,
  `"/evasao"`, `"/percentuais-legais"`).

---

## Execution Plan

### Phase 1: Componentes do conteúdo

```
T1 → T2 → T3 → T4 → T5
```

### Phase 2: Coluna lateral e shell

```
T6 → T7 → T8 → T9 → T10
```

### Phase 3: Páginas

```
T11 → T12 → T13 → T14
```

### Phase 4: Conferência e registro

```
T15 → T16 → T17
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
   `core-tokens.css`, sem diferenciar maiúsculas; e
   `rgba("#e52207", 0.25) == "rgba(229, 34, 7, 0.25)"`.

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
e `ano_ingresso_do_valor(valor, ano_min, ano_max)`; em `app/paineis/filtros.py`,
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
3. `app/paineis/filtros.py`, `anos_de_ingresso(df, ano_base)`: devolve
   `(menor ano de dt_data_inicio, ano_base)`; sem data válida,
   `(ano_base, ano_base)`; se o menor ano for maior que o ano-base, o ano-base
   nos dois.
4. Testes: valor inicial, rótulo, marcas; os três casos de
   `ano_ingresso_do_valor`; os três de `anos_de_ingresso` (em
   `tests/test_paineis_filtros.py`).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): filtro de ano de ingresso`

---

### T3: Bloco de filtros da lateral e botão FIC segmentado

**What**: Em `app/components/filters.py`, `filtros_laterais(campos, id_limpar)`;
e `fic_toggle` passa a usar o visual segmentado de `_fic_selector` da página
Matrículas (`app/pages/matriculas.py`, perto da linha 74).
**Where**: `app/components/filters.py`
**Depends on**: T2
**Reuses**: `_fic_selector` (`app/pages/matriculas.py`), `clear_filters_button`
**Requirement**: PBI-03

**Passos**:

1. Código:

   ```python
   def filtros_laterais(campos, id_limpar):
       """Filtros da página, um embaixo do outro, com "Limpar Filtros" por último."""
       return html.Div(
           [
               html.H2("Filtros", className="lateral-titulo"),
               *campos,
               clear_filters_button(id_limpar),
           ],
           className="lateral-filtros",
           role="group",
           **{"aria-label": "Filtros"},
       )
   ```

2. `fic_toggle(id_, default="com_fic")`: troque o corpo pelo de `_fic_selector`
   (classes `seg-grupo`, `seg`, `seg--ativo`, `seg-input`, contêiner
   `fic-segmentado`), mantendo o parâmetro `default`. Não mude
   `app/pages/matriculas.py` nesta tarefa.
3. Testes: título "Filtros"; campos na ordem; botão por último; classe e
   `aria-label`; `fic_toggle(default="sem_fic")` começa em `sem_fic` com as
   classes do segmentado. Ajuste os testes existentes de `fic_toggle` que
   afirmavam a classe `br-radio` (cite PBI-03 no commit).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): bloco de filtros da lateral e botao fic segmentado`

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
   CONFIG = {"displayModeBar": False, "responsive": True}
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
   - `medidor("Técnico", 0.454, 0.5)`: no `dcc.Graph`, `figure.data[0].value == 45.4`,
     `gauge.bar.color == VERMELHO`, `gauge.threshold.value == 50`; texto com
     "Abaixo da meta" e "Meta: 50%"; `aria-label` com "45,4%";
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

**What**: `tabela_hierarquica_ds` (`app/components/tabela.py`) ganha o parâmetro
opcional `chave_ordem=None`.
**Where**: `app/components/tabela.py`
**Depends on**: T4
**Reuses**: função atual
**Requirement**: PBI-05

**Passos**:

1. Acrescente `chave_ordem=None` como último parâmetro.
2. Em `visitar`, quando `nivel == 0` e `chave_ordem` não é `None`, ordene os
   grupos por `chave_ordem(subgrupo)`, do maior para o menor, antes de montar as
   linhas. Nos outros níveis e sem `chave_ordem`, nada muda.
3. Testes: sem `chave_ordem`, a ordem de hoje (teste existente); com
   `chave_ordem=lambda g: len(g)`, o grupo maior primeiro; segundo nível na
   ordem de hoje.

**Done when**:

- [ ] Testes novos passam e os existentes continuam passando sem mudança
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): ordem inicial opcional na tabela hierarquica`

---

### T6: Saber se a instituição tem logotipo próprio

**What**: `tem_logo_personalizado()` em `app/data/config_store.py`.
**Where**: `app/data/config_store.py`
**Depends on**: None
**Reuses**: `get_logo_path`, `DEFAULT_LOGO_PATH` (mesmo arquivo)
**Requirement**: PBI-06

**Passos**:

1. Código:

   ```python
   def tem_logo_personalizado(db_path=DEFAULT_DB_PATH):
       """True quando a instituição enviou um logotipo (não o genérico)."""
       return get_logo_path(db_path) != DEFAULT_LOGO_PATH
   ```

2. Testes em `tests/test_config_store.py`, com o banco temporário que o arquivo
   já usa: sem logotipo → `False`; depois de `set_logo("app/data/uploads/branding/logo.png", db)` → `True`;
   depois de `reset_logo(db)` → `False`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(config): saber se ha logotipo proprio da instituicao`

---

### T7: Componente da coluna lateral

**What**: `app/components/lateral.py` com `lateral_painel(caminho_atual, filtros, preview=False, logo=None)`
e `logo_da_lateral()`.
**Where**: `app/components/lateral.py` (novo)
**Depends on**: T6
**Reuses**: `app/templates/shell/_menu.html` (copie a estrutura e as classes); `PAGINAS_PUBLICAS` (`app/shell.py`); `tem_logo_personalizado`, `dados_instituicao` (`app/data/config_store.py`)
**Requirement**: PBI-07

**Passos**:

1. Leia `app/templates/shell/_menu.html` inteiro. O menu do Dash repete a mesma
   estrutura, trocando `data-dismiss="menu"` por `data-dismiss="menu-painel"`.
2. Código:

   ```python
   """Coluna lateral das páginas públicas: logotipo, menu e filtros."""

   from dash import html

   from app.data.config_store import dados_instituicao, tem_logo_personalizado
   from app.shell import PAGINAS_PUBLICAS


   def logo_da_lateral():
       """Dados do logotipo para a lateral, ou None sem logotipo próprio."""
       if not tem_logo_personalizado():
           return None
       nome = (dados_instituicao().get("nome") or "").strip()
       return {"src": "/branding/logo", "alt": f"Logotipo — {nome}" if nome else "Logotipo da instituição"}


   def _menu(caminho_atual):
       itens = []
       for rotulo, href in PAGINAS_PUBLICAS:
           ativo = href == caminho_atual
           extras = {"aria-current": "page"} if ativo else {}
           itens.append(html.A(
               html.Span(rotulo, className="content"),
               href=href,
               className="menu-item active" if ativo else "menu-item",
               **extras,
           ))
       return html.Div(
           html.Div(
               [
                   html.Div(
                       [
                           html.Div(
                               html.Div(
                                   html.Button(
                                       html.I(className="fas fa-times", **{"aria-hidden": "true"}),
                                       className="br-button circle",
                                       type="button",
                                       **{"aria-label": "Fechar o menu", "data-dismiss": "menu-painel"},
                                   ),
                                   className="menu-close",
                               ),
                               className="menu-header",
                           ),
                           html.Nav(itens, className="menu-body", **{"aria-label": "Navegação principal"}),
                       ],
                       className="menu-panel",
                   ),
                   html.Div(className="menu-scrim", tabIndex="0", **{"data-dismiss": "menu-painel"}),
               ],
               className="menu-container",
           ),
           className="br-menu",
           id="main-navigation",
       )


   def lateral_painel(caminho_atual, filtros, preview=False, logo=None):
       """De cima para baixo: logotipo (se houver), menu e filtros.
       Na prévia administrativa, só os filtros."""
       if preview:
           return html.Aside(filtros, className="painel-lateral painel-lateral--previa")
       partes = []
       if logo:
           partes.append(html.Div(html.Img(src=logo["src"], alt=logo["alt"]), className="lateral-logo"))
       partes.append(_menu(caminho_atual))
       partes.append(filtros)
       return html.Aside(partes, className="painel-lateral")
   ```

   Se `app.shell` importar algo que cause import circular ao ser importado por
   um componente, pare e avise.
3. `tests/test_lateral_painel.py`:
   - com `logo={"src": "/branding/logo", "alt": "Logotipo — IF Teste"}`: a
     ordem dos filhos do `Aside` é logotipo, menu, filtros; a `img` tem o `alt`;
   - com `logo=None`: não há `img`;
   - o menu tem `id="main-navigation"`, classe `br-menu`, 4 links com os rótulos
     e `href` de `PAGINAS_PUBLICAS`, na ordem;
   - para `caminho_atual="/evasao"`, só o link de `/evasao` tem `active` e
     `aria-current="page"`;
   - os dois elementos de fechar têm `data-dismiss="menu-painel"`;
   - `preview=True` devolve só os filtros (sem `br-menu`, sem `img`);
   - `logo_da_lateral()` com `tem_logo_personalizado` trocado por `monkeypatch`
     para `False` → `None`; para `True` e nome "IF Teste" → `alt` "Logotipo — IF Teste".
   - comparação com o Jinja: as classes usadas pelo menu do Dash (`br-menu`,
     `menu-container`, `menu-panel`, `menu-header`, `menu-close`, `menu-body`,
     `menu-item`, `menu-scrim`) aparecem todas no texto de `_menu.html`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(componentes): coluna lateral com logotipo, menu e filtros`

---

### T8: Shell sem o menu Jinja nas páginas públicas

**What**: Nas páginas públicas, o shell deixa de renderizar `_menu.html`, marca o
`<body>` com a classe `pagina-publica` e o botão de menu do cabeçalho público usa
`data-toggle="menu-painel"`. Telas administrativas: nada muda.
**Where**: `app/templates/shell/_menu.html`
**Depends on**: T7
**Reuses**: `shell.publico` (`app/shell.py`, `contexto_shell`)
**Requirement**: PBI-08

**Passos**:

1. `app/templates/shell/_menu.html`: troque a primeira linha por
   `{% if shell.com_menu and not shell.publico %}`.
2. `app/templates/_base.html`: `<body>` vira
   `<body{% if shell.publico %} class="pagina-publica"{% endif %}>`.
3. `app/templates/shell/_header.html`, ramo `{% if shell.publico %}`: no botão
   `botao-menu`, troque `data-toggle="menu"` por `data-toggle="menu-painel"`.
   Mantenha `data-target="#main-navigation"`, `aria-controls` e `aria-expanded`.
4. Testes em `tests/test_shell_parciais.py`:
   - página pública (`/eficiencia`): o HTML **não** tem `class="br-menu"`; tem
     `<body class="pagina-publica">`; o botão tem `data-toggle="menu-painel"`;
   - tela administrativa (`/admin/atualizar`, com login): o HTML tem o menu
     Jinja e o `<body>` sem a classe.
   Reescreva os testes que afirmavam o menu Jinja nas páginas públicas
   (`test_menu_publico_renderiza_4_links_na_ordem_da_spec`,
   `test_so_o_link_da_pagina_atual_tem_aria_current_e_classe_ativa` e
   `test_botao_hamburguer_declara_estado_e_alvo_e_some_sem_menu`, se for o
   caso) para o comportamento novo; os 4 links e o item ativo passam a ser
   provados em `tests/test_lateral_painel.py` (T7). Cite PBI-08 AC5 no commit.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed (testes reescritos contam uma vez)

**Tests**: integration
**Gate**: full

**Commit**: `feat(shell): paginas publicas sem o menu jinja`

---

### T9: `menu.js` abre e fecha o menu do Dash

**What**: `app/static/js/menu.js` trata, por delegação de eventos no `document`,
os atributos `data-toggle="menu-painel"` e `data-dismiss="menu-painel"` e a tecla
`Esc`. O comportamento atual para o menu Jinja continua.
**Where**: `app/static/js/menu.js`
**Depends on**: T8
**Reuses**: `valorAriaExpanded`, `deveDevolverFoco` (mesmo arquivo); padrão de teste de `tests/test_js_menu.py`
**Requirement**: PBI-09

**Passos**:

1. Leia `menu.js` e `tests/test_js_menu.py` inteiros.
2. Acrescente duas funções puras, exportadas em `module.exports` junto das atuais:

   ```javascript
   function alternarMenu(menu, botao) {
     var abrir = !menu.classList.contains("active");
     if (abrir) { menu.classList.add("active"); } else { menu.classList.remove("active"); }
     botao.setAttribute("aria-expanded", valorAriaExpanded(abrir));
     return abrir;
   }

   function fecharMenu(menu, botao) {
     if (!menu.classList.contains("active")) { return false; }
     menu.classList.remove("active");
     botao.setAttribute("aria-expanded", "false");
     if (typeof botao.focus === "function") { botao.focus(); }
     return true;
   }
   ```

3. Dentro do `if (typeof document !== "undefined")`, sem mexer no bloco atual:

   ```javascript
   var SELETOR_BOTAO = '[data-toggle="menu-painel"]';
   document.addEventListener("click", function (evento) {
     var alvo = evento.target;
     if (!alvo || typeof alvo.closest !== "function") { return; }
     var botaoPainel = alvo.closest(SELETOR_BOTAO);
     if (botaoPainel) {
       var menuAlvo = document.querySelector(botaoPainel.getAttribute("data-target"));
       if (menuAlvo) { alternarMenu(menuAlvo, botaoPainel); }
       return;
     }
     var fechar = alvo.closest('[data-dismiss="menu-painel"]');
     if (fechar) {
       var menuAberto = fechar.closest(".br-menu");
       var botao = document.querySelector(SELETOR_BOTAO);
       if (menuAberto && botao) { fecharMenu(menuAberto, botao); }
     }
   });
   document.addEventListener("keydown", function (evento) {
     if (evento.key !== "Escape") { return; }
     var botao = document.querySelector(SELETOR_BOTAO);
     var menuAlvo = botao && document.querySelector(botao.getAttribute("data-target"));
     if (menuAlvo) { fecharMenu(menuAlvo, botao); }
   });
   ```

4. Testes em `tests/test_js_menu.py`, no mesmo estilo dos existentes (objetos
   falsos com `classList` e `setAttribute`): `alternarMenu` abre e depois fecha,
   e o `aria-expanded` acompanha; `fecharMenu` num menu aberto fecha, põe
   `aria-expanded="false"` e chama `focus`; num menu fechado devolve `false` e
   não chama `focus`.

**Done when**:

- [ ] Testes novos passam (precisam do `node` no PATH, como os outros `test_js_*`)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(menu): abrir e fechar o menu da coluna lateral do painel`

---

### T10: CSS da coluna lateral, dos filtros e dos gráficos

**What**: Regras em `app/assets/style.css` para a grade das páginas públicas,
`.painel-com-lateral`, `.painel-lateral`, `.lateral-logo`, `.lateral-filtros`,
`.lateral-titulo`, `.painel-conteudo`, `.filtro-ano`, `.medidores`, `.medidor`,
`.card-grafico`, `.grafico-titulo`, `.texto-leitor-tela` e o texto dos gráficos
no tema escuro.
**Where**: `app/assets/style.css`
**Depends on**: T9
**Reuses**: regras do menu lateral de hoje (`style.css`, bloco "Menu: barra lateral fixa à esquerda a partir de 992px", perto da linha 86); variáveis do DS já usadas no arquivo
**Requirement**: PBI-10

**Passos**:

1. Leia `app/assets/style.css` inteiro e `tests/test_style_css.py`. Regras: sem
   cor literal, só os pontos de quebra 576, 992, 1280 e 1600 px, alvo de toque
   de pelo menos 24 px.
2. A partir de 992 px:
   - `body.pagina-publica`: as áreas da grade passam a ser
     `"cabecalho cabecalho" "breadcrumb breadcrumb" "conteudo conteudo" "rodape rodape"`
     (o menu agora mora dentro de `main`);
   - `body.pagina-publica > main#main-content`: sem recuo à esquerda
     (`padding-left: 0`), para a lateral encostar na borda;
   - `.painel-com-lateral`: `display: grid; grid-template-columns: var(--menu-largura) minmax(0, 1fr); gap` da escala do DS;
   - `.painel-lateral`: mesmo fundo do menu lateral de hoje (use as mesmas
     variáveis do bloco do menu), `align-self: start`, `position: sticky; top: 0`;
   - o `.br-menu` dentro de `.painel-lateral` já fica aberto e estático pelas
     regras atuais de `.br-menu` a partir de 992 px; confira que nenhuma delas
     depende de `body > .br-menu` para isso. Se depender, acrescente o mesmo
     seletor para `.painel-lateral .br-menu`.
3. Abaixo de 992 px:
   - `.painel-com-lateral` e `.painel-lateral`: `display: contents`, para o menu
     seguir sobreposto (regras atuais do DS) e o bloco de filtros cair no fluxo;
   - `.lateral-filtros`: cartão no topo do conteúdo (mesmo visual do cartão de
     filtros de hoje, `.card-filtros`).
4. `.lateral-filtros`: campos em coluna (`display: flex; flex-direction: column; gap`),
   largura total da lateral; `.lateral-titulo` com o tamanho de título pequeno
   já usado no arquivo; `.lateral-logo img`: largura máxima de 100% e altura
   máxima de uns 6rem, centralizado, sobre superfície clara no tema escuro (veja
   como `.logo-superficie` do cabeçalho administrativo resolve isso e reaproveite).
5. `.medidores`: grade de 3 colunas a partir de 992 px, 1 coluna abaixo.
   `.card-grafico`: mesmo visual de cartão; `.grafico-titulo` com o tamanho de
   título de cartão já usado.
6. `.texto-leitor-tela`: `position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;`.
7. Texto do Plotly no tema escuro (o Plotly grava a cor no atributo `style` do
   SVG, por isso o `!important`):

   ```css
   .grafico-medidor text,
   .grafico-evasoes text {
     fill: var(--color) !important;
   }
   ```

8. Testes em `tests/test_style_css.py`: cada seletor novo aparece no arquivo; a
   regra de `display: contents` existe fora do bloco de 992 px; a regra de
   `fill: var(--color)` existe para os dois gráficos.

**Done when**:

- [ ] Testes novos passam e `tests/test_style_css.py` inteiro continua verde
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `style(publico): coluna lateral com filtros, medidores e graficos`

---

### T11: Página Matrículas como no Power BI

**What**: `app/pages/matriculas.py` com o "Layout comum das páginas públicas";
filtros na lateral (Ano de Ingresso, Campus, Tipo de Curso, Tipo de Programa,
FIC, Limpar); cartões na ordem Cursos, Matrículas, Matrículas equivalentes,
Matrículas concluídas, Ingressantes; números de `app/paineis/matriculas.py`.
**Where**: `app/pages/matriculas.py`
**Depends on**: None
**Reuses**: `lateral_painel`, `logo_da_lateral` (T7); `filtros_laterais`, `filtro_ano_ingresso`, `ano_ingresso_do_valor`, `fic_toggle`, `select_filter`; `FiltrosPainel`, `aplicar_filtros`, `anos_de_ingresso`; `resumo_matriculas`, `metricas_matriculas`; print `.specs/referencias/matriculas-por-campus.png`
**Requirement**: PBI-11

**Passos**:

1. Conteúdo (`painel-conteudo`), nesta ordem: `_cabecalho`, cartões
   (`matriculas-kpis`), chips, `Store` dos eixos, matriz, `Store` da prévia.
   Filtros na lateral, nesta ordem: `filtro_ano_ingresso("matriculas-filtro-ano", ...)`,
   Campus, Tipo de Curso, Tipo de Programa, `fic_toggle("matriculas-fic")`.
   Apague `_filtros(df)` e `_fic_selector`.
2. `anos_de_ingresso(df, ano_base)` dá o intervalo; guarde-o em
   `dcc.Store(id="matriculas-anos", data=[ano_min, ano_max])` dentro do conteúdo.
3. Callback `atualizar`: `Input("matriculas-filtro-ano", "value")` depois dos
   outros `Input`; `State("matriculas-anos", "data")` antes do `State` da prévia
   (siga as "Regras desta feature"). Monte
   `FiltrosPainel(campus=..., tipo_curso=..., programa=..., incluir_fic=(fic == "com_fic"), ano_ingresso=ano_ingresso_do_valor(valor_ano, *anos))`
   convertendo `"__todos__"` em `None`. Cartões por `resumo_matriculas`; matriz
   sobre `aplicar_filtros(df, filtros)` com `metricas_matriculas` no lugar de
   `_metricas` (apague `_metricas` e `_filtrar`).
4. `limpar_filtros`: acrescente `Output("matriculas-filtro-ano", "value")` e
   `State("matriculas-anos", "data")`, devolvendo o intervalo completo.
5. Testes em `tests/test_paginas_publicas.py`:
   - o layout é `painel-com-lateral` com a lateral e o conteúdo; no conteúdo, a
     ordem título, cartões, chips, matriz;
   - a lateral tem, nesta ordem, os rótulos "Ano de Ingresso", "Campus",
     "Tipo de Curso", "Tipo de Programa", o botão FIC e "Limpar Filtros";
   - cartões com os rótulos na ordem do spec e números iguais a
     `resumo_matriculas` sobre os dados do teste;
   - ano de ingresso reduzido baixa os números para os do intervalo;
   - "Limpar Filtros" devolve o intervalo completo.
   Ajuste os testes existentes que afirmavam a ordem antiga (cite PBI-11).

**Done when**:

- [ ] Testes novos passam; os de prévia (`tests/test_previa_callback_matriculas.py`) continuam verdes
- [ ] Nenhuma conta de indicador sobrou em `app/pages/matriculas.py`
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(matriculas): lateral com filtros e cartoes do power bi`

---

### T12: Página Eficiência como no Power BI

**What**: `app/pages/eficiencia.py` com o layout comum; sem cartão; filtros
Campus, Tipo de Curso, Modalidade, Programa, FIC (padrão Sem FIC); tabela com IEA
em percentual, Concluídos, Evadidos e Retidos por Ciclo; números de
`metricas_eficiencia`.
**Where**: `app/pages/eficiencia.py`
**Depends on**: T11
**Reuses**: igual a T11; `metricas_eficiencia`; print `.specs/referencias/eficiencia-por-campus-sem-fic.png`
**Requirement**: PBI-12

**Passos**:

1. Conteúdo: cabeçalho, chips, `Store`, matriz, `Store` da prévia. Tire o `Div`
   `eficiencia-kpi` e o `Output` dele.
2. Filtros novos: `eficiencia-filtro-tipo-curso` (`tipo_curso_pnp`) e
   `eficiencia-filtro-programa` (`tipo_programa_curso`); as colunas existem desde
   a feature 2 (T1).
3. Colunas: `["Índice de Eficiência Acadêmica", "Concluídos por Ciclo", "Evadidos por Ciclo", "Retidos por Ciclo"]`.
   IEA com `f"{v * 100:.2f}".replace(".", ",") + "%"`; contagens com
   `formatar_valor(v, "#,0")` (`app/components/kpi.py`). Total por
   `metricas_eficiencia` do df filtrado inteiro.
4. `limpar_filtros` devolve também os dois filtros novos.
5. Testes: layout com lateral e sem cartão; rótulos dos filtros na ordem; as 4
   colunas; Total com IEA em percentual (ex.: `41,44%` para 1.849/2.613/502);
   filtro de tipo de curso muda os números. Reescreva os testes existentes do
   cartão de IEA (cite PBI-12 AC1).

**Done when**:

- [ ] Testes novos passam; os de prévia continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(eficiencia): lateral com filtros e colunas do power bi`

---

### T13: Página Evasão como no Power BI

**What**: `app/pages/evasao.py` com o layout comum; filtros Ano de Ingresso,
Campus, Tipo de Curso, Modalidade, FIC (padrão **Com FIC**); 4 cartões; gráfico
mensal; tabela com "Evasões em {ano}" e "Taxa de Evasão Anual" ordenada pela
taxa; números de `app/paineis/evasao.py`.
**Where**: `app/pages/evasao.py`
**Depends on**: T12
**Reuses**: igual a T11; `grafico_evasoes_mes`, `chave_ordem`; `resumo_evasao`, `evasoes_por_mes`, `metricas_evasao`; print `.specs/referencias/evasao-por-campus.png`
**Requirement**: PBI-13

**Passos**:

1. Conteúdo: cabeçalho, linha com os 4 cartões (`cartao_indicador` de
   `app/components/painel_publico.py`; rótulos "Abandonos",
   "Transferências externas", "Desligamentos", "Transferências internas") e, ao
   lado, o gráfico mensal (`id="evasao-grafico"`), chips, `Store`, tabela,
   `Store` da prévia.
2. Filtros: `filtro_ano_ingresso("evasao-filtro-ano", ...)`, Campus, Tipo de
   Curso, Modalidade (`evasao-filtro-modalidade`, coluna `modalidade_ensino`) e
   `fic_toggle("evasao-fic", default="com_fic")` (hoje o padrão é `sem_fic`:
   passa a `com_fic`, cite PBI-13 AC1).
3. Tabela: colunas `[f"Evasões em {ano_base}", "Taxa de Evasão Anual"]`;
   `metricas` devolve
   `[formatar_valor(evasoes, "#,0"), {"valor": [taxa_formatada, html.Span(f" ({faixa})", className="texto-leitor-tela")], "classe": classe}]`,
   com `classe` de `_classe_evasao` e `faixa` de `_LABEL_EVASAO` (já existem no
   arquivo). Taxa com 1 casa: `f"{taxa * 100:.1f}".replace(".", ",") + "%"`.
   `chave_ordem=lambda g: metricas_evasao(g, ano_base)["taxa"]`.
4. `limpar_filtros` com o ano de ingresso (como em T11), a modalidade e o FIC
   voltando a `com_fic`.
5. Testes: layout; 4 cartões com os números de `resumo_evasao`; gráfico com os
   12 valores de `evasoes_por_mes`; FIC começa em `com_fic`; primeira linha da
   tabela é o campus de maior taxa; célula de taxa com a classe da faixa e o
   texto oculto. Reescreva os testes existentes do cartão único de taxa (cite
   PBI-13 AC1).

**Done when**:

- [ ] Testes novos passam; os de prévia continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(evasao): lateral, cartoes, grafico mensal e tabela do power bi`

---

### T14: Página Percentuais como no Power BI

**What**: `app/pages/percentuais_legais.py` com o layout comum; filtros Campus,
Tipo de Curso, Modalidade, Programa Associado; aviso de PROEJA no conteúdo;
cartão Matrículas equivalentes e 3 medidores; tabela com as 6 colunas; números
de `app/paineis/percentuais.py`.
**Where**: `app/pages/percentuais_legais.py`
**Depends on**: T13
**Reuses**: igual a T11; `medidor`; `resumo_percentuais`, `metricas_percentuais`; `META_*`; print `.specs/referencias/percentuais-por-campus.png`
**Requirement**: PBI-14

**Passos**:

1. Conteúdo: cabeçalho, o `Div` do aviso de PROEJA (`percentuais-aviso-proeja`),
   linha com o cartão "Matrículas equivalentes" e
   `html.Div(className="medidores")` com os 3 medidores, chips, `Store`, tabela,
   `Store` da prévia. Apague a função interna `gauge` do callback.
2. Colunas: `["Técnicos (MatEq)", "Formação de Professores (MatEq)", "Proeja (MatEq)", "% Técnico", "% Formação de Professores", "% Proeja"]`;
   MatEq com `_formatar_equivalentes` (já existe) e percentuais com 2 casas.
3. Filtros novos: `percentuais-filtro-tipo-curso` e `percentuais-filtro-modalidade`;
   `limpar_filtros` devolve os dois.
4. Testes: layout; 3 medidores com os valores de `resumo_percentuais` (procure
   `dcc.Graph` com `className="grafico-medidor"`); as 6 colunas; aviso de PROEJA
   aparece com filtro de programa e some sem ele. Reescreva os testes existentes
   dos cartões de percentual (cite PBI-14 AC1).

**Done when**:

- [ ] Testes novos passam; os de prévia continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(percentuais): lateral, medidores e colunas do power bi`

---

### T15: Roteiro de conferência visual no `TESTAR.md`

**What**: Na seção de conferência do design do `TESTAR.md`, um roteiro por
página: abrir o print de `.specs/referencias/`, abrir a página no navegador e
conferir item a item a seção "O que cada página mostra" do spec (inclusive a
coluna lateral: logotipo, menu e filtros), nos temas claro e escuro, com a
largura entre 320 e 430 px (menu pelo botão, filtros no topo) e com 1280 px ou
mais (lateral fixa). Atualize a seção "Painel público" do `README.md`.
**Where**: `TESTAR.md`
**Depends on**: None
**Reuses**: spec desta feature
**Requirement**: PBI-15

**Done when**:

- [ ] Teste de higiene: `TESTAR.md` cita os 5 prints de `.specs/referencias/`
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(testar): roteiro de conferencia das paginas com o power bi`

---

### T16: [HUMANO] Jaline confere as 4 páginas

**What**: Jaline segue o roteiro de T15 e registra em `DEPLOY.md`, item DS-42:
navegador, larguras, data e o que precisar de ajuste. Ajustes viram tarefas
novas neste arquivo (T16a, T16b…), com teste.
**Where**: `DEPLOY.md`
**Depends on**: T15
**Reuses**: roteiro de T15
**Requirement**: PBI-15

**O agente executor para aqui** e avisa: "T16 é humana: falta a conferência visual da Jaline".

**Done when**:

- [ ] `DEPLOY.md` com o resultado da conferência

**Tests**: none
**Gate**: build

**Commit**: `docs(deploy): registrar a conferencia visual das paginas`

---

### T17: Registrar a feature no `STATE.md`

**What**: Handoff da feature (commits, testes, conferência). Registre AD-008:
"Nas páginas públicas, a coluna lateral (logotipo, menu e filtros) é montada
pelo Dash (`app/components/lateral.py`); o parcial `_menu.html` só aparece nas
telas administrativas. O botão do cabeçalho público usa
`data-toggle="menu-painel"`, tratado por `menu.js`." Reason: filtros ao lado do
menu, como no Power BI; o Dash só renderiza dentro da própria raiz. Trade-off: a
marcação do menu existe em dois lugares (Jinja e Dash), e o teste de T7 garante
as mesmas classes. Scope: páginas públicas. Status: active; e marque AD-001 com
"substituída por AD-008 nas páginas públicas".
**Where**: `.specs/STATE.md`
**Depends on**: T16
**Reuses**: formato dos handoffs e das decisões
**Requirement**: PBI-15

**Done when**:

- [ ] "Estado atual" diz que `mvp-3-paginas-power-bi` está implementada e aguarda o Verifier
- [ ] AD-008 registrada e AD-001 anotada
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`

**Tests**: none
**Gate**: build

**Commit**: `docs(state): registrar as paginas no padrao do power bi`

---

## Verificação (depois de T17)

Verifier independente. Sensor mínimo: trocar a ordem de dois cartões da
Matrículas; tirar o `fill` do gráfico mensal; `ano_ingresso_do_valor` devolver
tupla no intervalo completo; esquecer `chave_ordem` na Evasão; voltar a calcular
o IEA na página; `lateral_painel` pôr os filtros acima do menu; `_menu.html`
voltar a aparecer nas páginas públicas; `menu.js` não devolver o foco ao fechar.

---

## Phase Execution Map

```
Phase 1:  T1 → T2 → T3 → T4 → T5
Phase 2:  T6 → T7 → T8 → T9 → T10
Phase 3:  T11 → T12 → T13 → T14
Phase 4:  T15 → T16 → T17
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1, T4, T5, T6, T7, T9, T10 | 1 arquivo | ✅ |
| T2 | 2 funções em `filters.py` + 1 em `paineis/filtros.py` | ⚠️ coeso: o filtro de ano precisa do intervalo |
| T3 | 1 arquivo | ✅ |
| T8 | 3 templates do shell | ⚠️ coeso: uma mudança de comportamento do shell |
| T11–T14 | 1 página | ✅ |
| T15–T17 | documentação e registro | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | T2 | T2 → T3 | ✅ |
| T4 | T3 | T3 → T4 | ✅ |
| T5 | T4 | T4 → T5 | ✅ |
| T6 | None | início da fase 2 | ✅ |
| T7 | T6 | T6 → T7 | ✅ |
| T8 | T7 | T7 → T8 | ✅ |
| T9 | T8 | T8 → T9 | ✅ |
| T10 | T9 | T9 → T10 | ✅ |
| T11 | None | início da fase 3 | ✅ |
| T12 | T11 | T11 → T12 | ✅ |
| T13 | T12 | T12 → T13 | ✅ |
| T14 | T13 | T13 → T14 | ✅ |
| T15 | None | início da fase 4 | ✅ |
| T16 | T15 | T15 → T16 | ✅ |
| T17 | T16 | T16 → T17 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1–T5, T7 | componentes | unit | unit | ✅ |
| T6 | dados | unit | unit | ✅ |
| T8 | shell (templates) | integration | integration | ✅ |
| T9 | JavaScript | integration | integration | ✅ |
| T10 | CSS | unit | unit | ✅ |
| T11–T14 | páginas | integration | integration | ✅ |
| T15 | documentação | unit (higiene) | unit | ✅ |
| T16, T17 | conferência humana e registro | none | none | ✅ |
