# Tarefa: paridade visual com o Figma na página inicial (Matrículas) em telas largas

**Feature**: `govbr-design-system`
**Escopo**: layout do shell (cabeçalho, menu lateral, rodapé) e da página `/` (Matrículas) a partir de 992px
**Referência de design**: Figma — arquivo `kuhtEfvHr1w0yQpPoIG7Va`, nó `15:2` ("09 - Página inicial (Matrículas)"), frame de 1280 x 1078px
**Branch atual**: `migracao-dash-gov-br`
**Situação**: a validação `validation.md` deu PASS nos critérios textuais (DS-01 a DS-85), mas o resultado renderizado em telas largas diverge do protótipo em vários pontos estruturais. Esta tarefa corrige essas divergências.

---

## 1. Como reproduzir o estado atual

O banco `app/data/sistec.db` já tem dados publicados. Suba o app e abra `/` com viewport de largura ≥ 992px:

```bash
python -c "from app.app import app; app.run(host='127.0.0.1', port=8051)"
# abrir http://127.0.0.1:8051/
```

Se o banco estiver vazio, rode antes `python scripts/seed_sintetico.py`.

Todas as medidas citadas abaixo como "medido" vieram de `getBoundingClientRect()` e `getComputedStyle()` nessa página, com o menu no modo barra lateral fixa (≥ 992px).

---

## 2. Restrições que a correção precisa respeitar

Estas regras já são cobertas por testes. Quebrá-las derruba a suíte:

1. **Nenhuma cor literal em `app/assets/style.css`** — `tests/test_style_css.py::test_nao_ha_cor_literal` proíbe `#rgb`, `#rrggbb`, `rgb()`, `rgba()`, `hsl()`, `hsla()`. Use apenas variáveis do DS.
2. **Nenhum ponto de quebra fora de 576, 992, 1280 e 1600px** — `test_todo_media_de_largura_usa_so_os_pontos_do_ds`.
3. **Nenhuma variável `--gov-*` própria** — `test_nao_ha_variavel_gov_propria`. Variáveis locais com outro prefixo (ex.: `--menu-largura`, já existente) são permitidas.
4. **Nenhum seletor do shell antigo** (`.app-header`, `.nav-menu`, `.admin-nav`, `.kpi-card`, `.nav-card`, `.hero`).
5. O comportamento **abaixo de 992px** (menu sobreposto com hambúrguer e scrim) e o fallback **`.ds-sem-js`** devem continuar funcionando. Não remova `app/assets/style.css:97-100`.
6. `tests/test_style_css.py:96-106` exige que o bloco `@media (min-width: 992px)` continue contendo `.br-menu { ... width: var(--menu-largura) ... }`. Se a correção mudar a estratégia de posicionamento (ver Defeito 1), **atualize esse teste junto**, mantendo uma asserção equivalente.
7. `tests/test_paginas_publicas.py:72` afirma `kpis.className == "kpis-figma"` no retorno do callback. O Defeito 5 muda isso — atualize o teste.

### Mapa de tokens (hex do Figma → variável do DS)

| Figma | Token do DS | Observação |
| --- | --- | --- |
| `#1351b4` | `--blue-warm-vivid-70` / `--color-primary-default` | azul institucional |
| `#0c326f` | `--blue-warm-vivid-80` | usado hoje indevidamente no item ativo do menu |
| `#071d41` | `--blue-warm-vivid-90` | usado hoje indevidamente no rodapé |
| `#ccc` | `--gray-20` (= `--border-color` no tema claro) | bordas dos cards |
| `#e6e6e6` | `--gray-10` | borda inferior das linhas da tabela |
| `#f8f8f8` | `--gray-2` | fundo da página e zebra da tabela |
| `#888` | `--gray-40` | travessão de valor ausente |
| `#666` | `--gray-60` (`#636363`, aproximação aceita e já em uso) | textos secundários |
| `#1e1e1e` | `--color` (tema claro) | texto principal |
| `#e52207` | `--danger` | coluna Evasões |
| `#f0f4fa` | sem token exato — use `--blue-warm-vivid-5` (`#edf5ff`) ou `color-mix(in srgb, var(--color-primary-default) 8%, var(--background))` | fundo do item ativo do menu e da linha Total |

### Valores de espaçamento e tipografia (conferidos no `core.min.css`)

`--spacing-scale-half` 4px · `--spacing-scale-base` 8px · `--spacing-scale-baseh` 12px · `--spacing-scale-2x` 16px · `--spacing-scale-3x` 24px · `--spacing-scale-4x` 32px · `--spacing-scale-5x` 40px
`--font-size-scale-base` 14px · `--font-size-scale-up-03` 24.192px · `--font-size-scale-down-01` **11.662px**
`--surface-rounder-sm` 4px · `--surface-rounder-md` 8px · `--surface-rounder-pill` 999em

Atenção: `--font-size-scale-down-01` é 11,662px, **não** 12px. Onde o Figma pede 12px exatos (rótulos de KPI, `th` da tabela, rótulos dos filtros), o `style.css` de hoje já usa o literal `12px` — mantenha assim, literais de tamanho são permitidos (só cor é proibida).

---

## 3. Defeitos, causa-raiz e correção

### Defeito 1 — Cabeçalho e rodapé não ocupam a largura total; o menu cobre o cabeçalho

**Figma**: o `Header` (72px) ocupa os 1280px de largura no topo. Abaixo dele, `Corpo` é uma linha com `Menu lateral` (240px) à esquerda e `Main` à direita. O `Footer` (48px) ocupa os 1280px abaixo de tudo, inclusive abaixo do menu.

**Atual (medido)**: `body { padding-left: 240px }` empurra *todos* os filhos do `body`, inclusive `<header>` e `<footer>`. O `<header>` começa em `x=240`; o `<footer>` também. O `.br-menu` é `position: fixed; top: 0` com altura total da viewport, ficando **sobre** a faixa do cabeçalho — o item "Matrículas" aparece cortado atrás do cabeçalho azul.

**Causa-raiz**: `app/assets/style.css:87-95`.

**Correção recomendada** (só CSS; não altera `app/templates/_base.html`): trocar o `padding-left` do `body` por um grid no bloco `@media (min-width: 992px)`.

> **Este CSS foi testado no app rodando** (injetado via DevTools em `/`, viewport de 1895px). As medidas resultantes estão logo abaixo. Duas armadilhas foram encontradas e já estão resolvidas no trecho — leia as notas.

```css
@media (min-width: 992px){
  body{
    display: grid;
    grid-template-columns: var(--menu-largura) 1fr;
    grid-template-rows: auto 1fr auto;
    grid-template-areas:
      "cabecalho cabecalho"
      "menu      conteudo"
      "rodape    rodape";
    min-height: 100vh;
    padding-left: 0;        /* substitui o padding-left de hoje */
  }
  body > header.br-header{ grid-area: cabecalho; }
  body > .br-menu{ grid-area: menu; }
  body > footer.br-footer{ grid-area: rodape; }
  /* demais filhos do body (skiplink, scrim, main, modal, scripts) */
  body > *:not(header.br-header):not(.br-menu):not(footer.br-footer){ grid-column: 2; }

  .br-menu{
    position: static;       /* NÃO use sticky — ver nota 1 */
    top: auto;
    bottom: auto;
    left: auto;             /* zera os resíduos da regra atual (style.css:88) */
    align-self: stretch;
    width: auto;            /* a largura vem da coluna do grid */
    height: auto;
  }
  .br-menu .menu-container{ height: 100%; }   /* ver nota 2 */
}
```

**Nota 1 — não use `position: sticky` no `.br-menu`.** A regra de hoje (`app/assets/style.css:88`) define `top: 0; bottom: 0; left: 0` junto com `position: fixed`. Se você só trocar `fixed` por `sticky`, o `top: 0` continua valendo e o menu sobe para `y=0`, voltando a cobrir o cabeçalho — foi exatamente o que aconteceu no teste. Ou você zera `top/bottom/left` (como acima) e usa `static`, ou, se quiser o menu acompanhando a rolagem, aplique o `sticky` no `.menu-panel` (com `top` igual à altura do cabeçalho), nunca no `.br-menu` esticado.

**Nota 2 — `.menu-container { height: 100% }` é obrigatório.** Sem ele o painel do menu para na altura do conteúdo (medido: 257px em vez de 1271px) e a borda direita não desce até o rodapé.

**Atenção**: os filhos diretos do `body` renderizados são, nesta ordem (verificado no DOM): `div.br-skiplink`, `header.br-header`, `div.br-menu`, `main.container-fluid`, `div.br-scrim`, `footer.br-footer`, quatro `<script>` e um `div` do Dash. O seletor genérico acima cobre todos. O breadcrumb não aparece em `/` porque a trilha é vazia (`app/shell.py:44-47`), mas aparece nas demais páginas — confira que ele cai na coluna 2.

**Medidas obtidas com esse CSS aplicado** (viewport de 1895px, já somando as correções dos Defeitos 2 e 4):

| Elemento | Antes | Depois |
| --- | --- | --- |
| `header.br-header` | `x=240 w=1655 h=104` | `x=0 w=1895 h=72` |
| `.br-menu` | `x=0 y=0 h=1271` (fixed, sobre o cabeçalho) | `x=0 y=72 w=240 h=1271` |
| `.br-menu .menu-panel` | `w=60 h=901` | `w=240 h=1271` |
| `main#main-content` | `y=104` | `y=72` |
| `footer.br-footer` | `x=240 w=1655` | `x=0 w=1895` |
| rolagem horizontal | não | não |

**Se mudar `width: var(--menu-largura)` para `width: auto`**, atualize `tests/test_style_css.py:101-106` para asseverar a nova regra (`grid-template-columns` contendo `var(--menu-largura)`), preservando a intenção do teste.

**Critérios de aceite**
- AC-1.1: em 1280px de viewport, `header.br-header` tem `x = 0` e largura igual à da viewport.
- AC-1.2: `footer.br-footer` tem `x = 0` e largura igual à da viewport.
- AC-1.3: o topo do `.br-menu` fica **abaixo** da borda inferior do cabeçalho; nenhum item do menu é encoberto.
- AC-1.4: abaixo de 992px nada muda — menu sobreposto, hambúrguer visível, scrim funcional.

---

### Defeito 2 — Menu lateral com 60px de largura útil: os rótulos quebram em até 4 linhas

**Figma**: painel do menu com 240px, fundo branco, borda direita 1px `#ccc`, `padding: 24px 0`, `gap: 4px` entre itens.

**Atual (medido)**: `.br-menu` = 240px, `.menu-container` = 240px, mas **`.menu-panel` = 60px** (`width: 25%; max-width: 25%`, herdado de uma media query do `core.min.css`). Resultado: "Taxa de Evasão Anual" quebra em quatro linhas ("Taxa / de / Evasão / Anual"), "Eficiência Acadêmica" em duas.

**Causa-raiz**: o override em `app/assets/style.css:87-95` neutraliza `position` e `display` do `.menu-container`, mas não a largura percentual que o DS aplica ao `.menu-panel`.

**Correção**: dentro do bloco `@media (min-width: 992px)`:

```css
.br-menu .menu-panel{
  width: 100%;
  max-width: none;
  height: auto;
  min-height: 100%;
  background: var(--background);
  border-right: 1px solid var(--border-color);
  padding: var(--spacing-scale-3x) 0;
  gap: var(--spacing-scale-half);
}
```

(`--spacing-scale-3x` = 24px, `--spacing-scale-half` = 4px — valores conferidos no `core.min.css`.)

**Testado**: com essa regra mais o `.menu-container { height: 100% }` da Nota 2 do Defeito 1, o painel passou de 60px para 240px de largura e de 257px para 1271px de altura, e os quatro rótulos couberam em uma linha cada.

**Critérios de aceite**
- AC-2.1: `.br-menu .menu-panel` tem largura computada de 240px em viewport de 1280px.
- AC-2.2: nenhum dos quatro rótulos (`Matrículas`, `Eficiência Acadêmica`, `Taxa de Evasão Anual`, `Percentuais Legais`) ocupa mais de uma linha.
- AC-2.3: o painel tem fundo `var(--background)` e borda direita de 1px em `var(--border-color)`.

---

### Defeito 3 — Item ativo do menu com o visual errado

**Figma**: item ativo com fundo `#f0f4fa`, barra vertical de 4 x 20px (`radius: 2px`) em `#1351b4` colada à esquerda, texto 14px **bold** `#1351b4`, altura 44px, `padding: 12px 16px 12px 12px`. Itens inativos: texto 14px regular `#1e1e1e`, `padding: 12px 16px 12px 24px`, altura 41px.

**Atual (medido)**: item ativo com `background: rgb(12, 50, 111)` (`--blue-warm-vivid-80`) e texto branco — é o estilo padrão do `.br-menu .menu-item.active` do DS. Não existe a barra marcadora. `padding: 16px`.

**Causa-raiz**: falta override em `app/assets/style.css`. O template `app/templates/shell/_menu.html:14-18` já emite `<a class="menu-item active">` com `<span class="content">`; a barra pode ser feita com `::before`, sem mexer no template.

**Correção**: no bloco `@media (min-width: 992px)`:

```css
.br-menu .menu-item{
  padding: var(--spacing-scale-baseh) var(--spacing-scale-2x) var(--spacing-scale-baseh) var(--spacing-scale-3x);
  font-size: var(--font-size-scale-base);   /* 14px */
  color: var(--color);
  background: transparent;
}
.br-menu .menu-item.active{
  background: var(--blue-warm-vivid-5);
  color: var(--color-primary-default);
  font-weight: var(--font-weight-bold);
  padding-left: var(--spacing-scale-baseh);
  gap: var(--spacing-scale-base);
}
.br-menu .menu-item.active::before{
  content: "";
  flex: 0 0 auto;
  width: 4px;
  height: 20px;
  border-radius: 2px;
  background: var(--color-primary-default);
}
```

(`--spacing-scale-baseh` = 12px, `--spacing-scale-2x` = 16px, `--spacing-scale-3x` = 24px, `--spacing-scale-base` = 8px.)

**Critérios de aceite**
- AC-3.1: o item ativo tem fundo claro azulado e texto em `var(--color-primary-default)`, **não** fundo azul escuro com texto branco.
- AC-3.2: existe uma barra de 4px de largura e 20px de altura à esquerda do rótulo ativo.
- AC-3.3: os itens inativos têm recuo à esquerda maior que o do item ativo (24px contra 12px), como no Figma.
- AC-3.4: o contraste texto/fundo do item ativo passa em AA (o par `--color-primary-default` sobre `--blue-warm-vivid-5` atende).

---

### Defeito 4 — Cabeçalho público com 104px em vez de 72px

**Figma**: `Header` com `height: 72px`, `padding: 16px 24px`, `gap: 16px`.

**Atual (medido)**: altura 104px. `.painel-publico .header-top` define `min-height: 72px` (`app/assets/style.css:240-245`), mas o **próprio `.br-header`** tem `padding: 16px 0` (confirmado por `getComputedStyle`), somando 32px.

**Correção** (testada):

```css
.painel-publico{ padding-top: 0; padding-bottom: 0; }
.painel-publico .header-top{
  min-height: 72px;
  padding: 0 var(--spacing-scale-3x);
}
```

**Duas armadilhas encontradas no teste:**

1. O padding **não** está no `.container-fluid`, está no `.br-header`. Zerar `.painel-publico .container-fluid` não muda nada — a altura continua 104px.
2. Não combine `min-height: 72px` com padding vertical no `.header-top`: o `min-height` se aplica à caixa de conteúdo, então `72 + 16 + 16` volta a dar 104px. Deixe o padding vertical em zero e use só as laterais de 24px; o DS já centraliza o conteúdo verticalmente.

Com as duas correções, o cabeçalho mediu exatamente **72px**.

**Critério de aceite**
- AC-4.1: `header.br-header.painel-publico` tem altura computada de 72px em viewport de 1280px.

---

### Defeito 5 — KPIs não se esticam: `div.kpis-figma` aninhado dentro de `div.kpis-figma`

**Figma**: cinco cards, cada um `flex: 1 0 0`, preenchendo os 992px do Main com `gap: 16px` (185,6px cada).

**Atual (medido)**: `#matriculas-kpis` tem 1440px; o `.kpis-figma` **filho** tem 651px; cada `.kpi-figma` tem 117px. Os cards ficam apertados e encostados à esquerda.

**Causa-raiz**: `app/pages/matriculas.py:116` cria o contêiner `html.Div(id="matriculas-kpis", className="kpis-figma")`, e o callback em `app/pages/matriculas.py:248-257` devolve **outro** `html.Div(..., className="kpis-figma")` como filho. O contêiner externo é `display: flex`, então o interno vira item flex e encolhe ao conteúdo.

**Correção**: remova a duplicação. A opção mais limpa é o callback devolver a **lista** de cards, e não um `Div`:

```python
# matriculas.py, no callback `atualizar`
kpis = [
    _kpi("Cursos", cursos_ativos),
    _kpi("Matrículas", total, formato="#,0"),
    _kpi("Matrículas equivalentes", equivalentes, formato="#,0.00", empty_state="dado incompleto"),
    _kpi("Matrículas concluídas", concluidas),
    _kpi("Ingressantes", ingressantes),
]
```

Mantendo `dcc.Loading(html.Div(id="matriculas-kpis", className="kpis-figma"))` no `layout()`.

**Efeito nos testes**: `tests/test_paginas_publicas.py:72` (`assert kpis.className == "kpis-figma"`) passa a falhar. Substitua por uma asserção sobre a lista devolvida (ex.: `assert len(kpis) == 5` e que cada item tem `className == "kpi-figma"`). O teste vizinho que compara os textos dos cinco cards precisa do mesmo ajuste na forma de navegar a árvore.

**Critérios de aceite**
- AC-5.1: não existe `.kpis-figma` dentro de `.kpis-figma` no DOM renderizado.
- AC-5.2: em viewport de 1280px, os cinco `.kpi-figma` somados mais os 4 gaps de 16px preenchem a largura do Main; cada card tem a mesma largura (±1px).

---

### Defeito 6 — Chips "Ver tabela por" empilhados na vertical

**Figma**: rótulo "Ver tabela por:" e os seis chips na mesma linha, com quebra por `flex-wrap`, `gap: 8px 12px`.

**Atual**: os seis chips aparecem um embaixo do outro, e o card cresce para 244px de altura.

**Causa-raiz** (a mesma do Defeito 7): o projeto **não carrega Bootstrap**. Os `<link>` da página são apenas `rawline.css`, `fontawesome`, `govbr-ds/dist/core.min.css` e `assets/style.css`. O `dbc.RadioItems` emite `<div class="form-check form-check-inline">` por opção, dentro de um `<div id="matriculas-eixo">`; sem o CSS do Bootstrap, `.form-check-inline` não tem `display: inline-block` e cada opção vira bloco. `app/assets/style.css:351` só zera padding e margin do `.form-check`, sem tratar o `display`, e o wrapper intermediário (`#matriculas-eixo`) não é item flex do `.card-chips`.

**Correção**: dar uma classe ao wrapper do `RadioItems` (o `dbc.RadioItems` aceita `className` no contêiner) e estilizá-la, em vez de depender do Bootstrap.

```python
# matriculas.py, em _chip_selector
dbc.RadioItems(
    id=id_,
    options=EIXOS,
    value="campus",
    inline=True,
    className="chips-grupo",
    labelClassName="chip",
    labelCheckedClassName="chip--ativo",   # ver nota abaixo
    inputClassName="chip-input",
)
```

```css
.card-chips .chips-grupo{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-scale-base) var(--spacing-scale-baseh);   /* 8px 12px */
}
.card-chips .chips-grupo .form-check{ display: inline-flex; padding: 0; margin: 0; }
```

**Nota sobre `labelCheckedClassName`**: hoje `app/pages/matriculas.py:52` passa `"chip chip--ativo"`, e o `dbc` concatena com `labelClassName`, produzindo `class="form-check-label chip chip chip--ativo"` (o `chip` duplicado). Passe só `"chip--ativo"`. O mesmo vale para `_fic_selector` em `app/pages/matriculas.py:72`.

**O card "Ver tabela por" não tem borda no Figma** — é só fundo branco com `radius: 12px` e `padding: 16px`. Hoje `app/assets/style.css:336-345` aplica `border: 1px solid var(--border-color)`. Remova a borda desse card (mantenha-a nos cards de KPI, tabela e filtros).

**Critérios de aceite**
- AC-6.1: em viewport de 1280px, o rótulo e os seis chips ficam na mesma linha; o `.card-chips` tem altura ≤ 66px.
- AC-6.2: o chip ativo tem fundo `var(--color-primary-default)` e texto `var(--pure-0)`; os inativos têm fundo do card, borda e texto em `var(--color-primary-default)`.
- AC-6.3: o `.card-chips` não tem borda.

---

### Defeito 7 — Controle segmentado "Com FIC / Sem FIC" empilhado na vertical

**Figma**: os dois botões lado a lado, dentro de um grupo com borda única de 1px `#1351b4` e `radius: 4px`; cada opção com 40px de altura e `padding: 0 16px`; a ativa preenchida de azul com texto branco bold.

**Atual**: "Com FIC" em cima e "Sem FIC" embaixo — mesma causa-raiz do Defeito 6.

**Correção**: analogamente, `className="seg-grupo"` no `dbc.RadioItems` de `_fic_selector` (`app/pages/matriculas.py:67-74`) e:

```css
.card-filtros .fic-segmentado .seg-grupo{ display: flex; }
.card-filtros .fic-segmentado .form-check{ display: inline-flex; padding: 0; margin: 0; }
.card-filtros .fic-segmentado label.seg{
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 var(--spacing-scale-2x);
}
```

As regras de arredondamento de primeira/última opção já existem em `app/assets/style.css:449-455` e continuam válidas.

**Critérios de aceite**
- AC-7.1: as duas opções ficam lado a lado, com 40px de altura cada.
- AC-7.2: a base do grupo FIC alinha com a base dos três `dcc.Dropdown` e com a do botão "Limpar Filtros" (o `.card-filtros` já usa `align-items: flex-end`).

---

### Defeito 8 — Acessibilidade: o foco do teclado some nos chips e no segmentado FIC

**Atual**: `app/assets/style.css:352` e `:438` escondem o `<input type="radio">` com `position: absolute; opacity: 0; width: 0; height: 0`. Como o `<label>` não recebe estilo de foco, navegar por Tab/setas não mostra indicação visual nenhuma.

**Correção**:

```css
.card-chips .chip-input:focus-visible + label.chip,
.card-filtros .seg-input:focus-visible + label.seg{
  outline: 3px solid var(--focus-color);
  outline-offset: var(--spacing-scale-half);
}
```

**Critério de aceite**
- AC-8.1: com o teclado, cada chip e cada opção FIC mostram anel de foco visível nos dois temas.

---

### Defeito 9 — Tabela sem o card: falta borda, cantos arredondados e larguras de coluna

**Figma**: a tabela vive dentro de um card com `background: #fff`, `border: 1px solid #ccc`, `border-radius: 12px` e recorte do conteúdo. Cabeçalho azul de 64px em duas faixas de 32px. Larguras: **Campus** flexível (360px no mock), **Ano PNP / Total de Matrículas** 160px, **Concluídas** 110px, **Integralizadas** 130px, **Em Curso** 120px, **Evasões** 110px. Cabeçalhos numéricos alinhados à direita; "Campus" e "Concluintes" centralizados. Linhas de 36px com borda inferior 1px `#e6e6e6`; zebra: ímpares brancas, pares `#f8f8f8`. Células `padding: 0 12px`, 13px; Campus à esquerda, numéricas à direita.

**Atual (medido)**: `.matriz-figma` sem borda e sem `border-radius`; `.tabela-landing` com `border-radius: 0px`. Sem `colgroup`, as larguras são distribuídas pelo conteúdo — as colunas numéricas ficam largas demais e os valores não alinham com os títulos. `app/assets/style.css:374-381` não define `text-align` nos `th`, então todos herdam o `center` padrão.

**Correção**:

1. Em `app/pages/matriculas.py:214-217`, envolver a tabela num card e emitir um `<colgroup>`:

```python
colgroup = html.Colgroup([
    html.Col(className="col-eixo"),
    html.Col(className="col-total"),
    html.Col(className="col-concluidas"),
    html.Col(className="col-integralizadas"),
    html.Col(className="col-em-curso"),
    html.Col(className="col-evasoes"),
])
return html.Div(
    html.Table([colgroup, cabecalho, html.Tbody(corpo), html.Tfoot(rodape)], className="tabela-landing"),
    className="matriz-figma",
)
```

2. No CSS:

```css
.matriz-figma{
  background: var(--background);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}
.tabela-landing{ table-layout: fixed; }
.tabela-landing .col-total{ width: 160px; }
.tabela-landing .col-concluidas{ width: 110px; }
.tabela-landing .col-integralizadas{ width: 130px; }
.tabela-landing .col-em-curso{ width: 120px; }
.tabela-landing .col-evasoes{ width: 110px; }
.tabela-landing thead th{ text-align: right; }
.tabela-landing thead th[rowspan="2"]:first-child,
.tabela-landing thead th[colspan]{ text-align: center; }
.tabela-landing tbody td, .tabela-landing tfoot td{ height: 36px; }
.tabela-landing tbody tr:nth-child(even) td{ background: var(--gray-2); }
```

**Atenção ao tema escuro**: `app/assets/style.css:391-393` usa hoje `var(--background-alternative)` na zebra, que no escuro vira `--blue-warm-vivid-80`. Se trocar por `--gray-2`, adicione o par escuro em `:root[data-tema="escuro"]` para a zebra não sumir.

**Critérios de aceite**
- AC-9.1: `.matriz-figma` tem borda de 1px e `border-radius` de 12px, e o cabeçalho azul respeita os cantos arredondados de cima.
- AC-9.2: cada coluna numérica tem a largura da tabela de referência acima; os valores das células alinham à direita, sob os respectivos títulos.
- AC-9.3: "Campus" e "Concluintes" ficam centralizados; os demais `th` à direita.
- AC-9.4: a zebra alterna corretamente nos dois temas.

---

### Defeito 10 — Zeros onde o Figma mostra travessão

**Figma**: em "Integralizadas", quando não há valor, a célula mostra `—` em `#888` — não `0`.

**Atual**: `app/pages/matriculas.py:169` aplica a classe `"num zero"` quando o valor é zero, mas **nenhuma regra usa `.zero`**, e `formatar_valor(0, "#,0")` devolve `"0"`.

**Correção**: decidir e aplicar de forma consistente. Recomendado seguir o Figma: quando `integralizadas == 0`, renderizar `"—"` com a classe `num vazio`, e no CSS `.tabela-landing td.vazio{ color: var(--gray-40); }`. Manter `0` nas demais colunas (o Figma mostra números reais nelas). Confirme com a dona do produto se o travessão vale também para "Concluídas" quando zero — o mock não tem esse caso.

**Critérios de aceite**
- AC-10.1: célula de "Integralizadas" com valor zero mostra `—` em cinza.
- AC-10.2: a linha "Total" segue a mesma regra.
- AC-10.3: a classe `zero`, que hoje não tem efeito, deixa de existir (ou passa a ter regra).

---

### Defeito 11 — Ordem dos chips diverge do Figma

**Figma** (nós `15:51` a `15:61`): Campus, Tipo de Curso, **Oferta (Técnico)**, Nome do Curso, Modalidade, Ciclo.

**Atual**: `app/components/filters.py:20-27` define Campus, Tipo de Curso, Nome do Curso, Modalidade, **Oferta (Técnico)**, Ciclo.

**Correção**: reordenar a constante `EIXOS` para a ordem do Figma. `EIXOS` é usada também por `axis_selector` e pelo mapa de rótulos em `app/pages/matriculas.py:140`; a mudança é só de ordem, sem efeito sobre os `value`. Verifique se algum teste de paridade fixa a ordem antes de mudar.

**Critério de aceite**
- AC-11.1: a ordem renderizada dos seis chips é a do Figma.

---

### Defeito 12 — Rodapé azul-escuro, 66px de altura

**Figma**: `Footer` com `height: 48px`, fundo `#1351b4`, `padding: 16px 24px`, três itens com `gap: 16px`, texto 13px branco.

**Atual (medido)**: `background: rgb(7, 29, 65)` (`--blue-warm-vivid-90`, padrão do `.br-footer`), altura 66px.

**Correção**: adicionar uma variante `painel-publico` ao rodapé, espelhando o que já foi feito no cabeçalho. O template `app/templates/shell/_footer.html:1` precisa receber a classe condicional (`{% if shell.publico %}`), e o CSS:

```css
.br-footer.painel-publico{
  background: var(--color-primary-default);
  color: var(--pure-0);
  min-height: 48px;
}
.br-footer.painel-publico .container-fluid{ padding: var(--spacing-scale-2x) var(--spacing-scale-3x); }
.br-footer.painel-publico a{ color: var(--pure-0); }
```

**Diferença intencional, manter**: o rodapé real tem um quarto link, "Área administrativa", que não está no Figma. Ele é necessário para o acesso administrativo — **não remova**.

**Critérios de aceite**
- AC-12.1: nas páginas públicas o rodapé tem fundo `var(--color-primary-default)` e altura de 48px (podendo crescer se o conteúdo quebrar).
- AC-12.2: nas páginas administrativas o rodapé mantém o visual atual do DS.
- AC-12.3: o contraste dos links brancos sobre o azul passa em AA.

---

### Defeito 13 — Fundo da página: o Main deveria ser branco sobre fundo cinza

**Figma**: o frame tem fundo `#f8f8f8`; o `Main` tem fundo branco, `padding: 32px 24px 40px`, `gap: 24px` entre os blocos.

**Atual (medido)**: `body` branco, `main` transparente — tudo branco, sem a distinção de superfícies. `main` começa em `x=308` enquanto o cabeçalho começa em `x=240`: 68px de desalinhamento entre o título do cabeçalho e o conteúdo.

**Correção**: introduzir uma variável local de superfície (não use o prefixo `--gov-`), remapeada no tema escuro:

```css
:root{ --superficie-pagina: var(--gray-2); }
:root[data-tema="escuro"]{ --superficie-pagina: var(--background-dark); }
body{ background: var(--superficie-pagina); color: var(--color); }
main#main-content{ background: var(--background); }
@media (min-width: 992px){
  main#main-content{
    padding: var(--spacing-scale-4x) var(--spacing-scale-3x) var(--spacing-scale-5x);
  }
}
```

Confira os valores reais de `--spacing-scale-4x` / `--spacing-scale-5x` no `core.min.css` antes de usar; o alvo é `32px` no topo, `24px` nas laterais e `40px` embaixo.

**Critérios de aceite**
- AC-13.1: o fundo fora do `main` é cinza claro no tema claro; o `main` é branco.
- AC-13.2: a margem esquerda do conteúdo do `main` coincide com a do título do cabeçalho (ambas 24px a partir da borda da sua coluna).
- AC-13.3: no tema escuro nenhum bloco fica branco sobre branco nem cinza sobre cinza.

---

## 4. Diferenças que **não** devem ser "corrigidas"

Registre-as para o verificador não reabri-las:

1. **Fonte**: o Figma usa Inter; o projeto usa **Rawline**, a fonte do gov.br DS, já vendorizada. Manter Rawline.
2. **Aviso "Os dados exibidos vêm direto do Sistec..."**: banner real acima do título, ausente do mock. Manter.
3. **Link "Área administrativa" no rodapé**: ausente do mock, necessário. Manter.
4. **Skiplink e breadcrumb**: exigências de acessibilidade do DS, ausentes do mock. Manter.
5. **Dados**: o mock traz 203 cursos / 16.750 matrículas; o banco local é sintético. Compare **layout**, nunca números.
6. **"Atualizado em 08/09/26"**: o mock abrevia o ano; `_data_curta` (`app/pages/matriculas.py:27-31`) devolve `dd/mm/aaaa`. Diferença cosmética — só mude se a dona do produto pedir.

---

## 5. Ordem sugerida de execução e commits

Um commit atômico por defeito, no padrão Conventional Commits já usado no branch:

1. `fix(ui): cabeçalho e rodapé voltam à largura total em telas largas` — Defeito 1
2. `fix(ui): barra lateral usa os 240px e não quebra os rótulos` — Defeitos 2 e 3
3. `fix(ui): cabeçalho público volta aos 72px do protótipo` — Defeito 4
4. `fix(ui): KPIs deixam de ser aninhados e preenchem a linha` — Defeito 5
5. `fix(ui): chips e segmentado FIC voltam a ficar em linha` — Defeitos 6 e 7
6. `fix(a11y): foco visível nos chips e no segmentado FIC` — Defeito 8
7. `fix(ui): tabela ganha o card e as larguras de coluna do protótipo` — Defeitos 9 e 10
8. `fix(ui): ordem dos chips segue o protótipo` — Defeito 11
9. `fix(ui): rodapé público adota o azul institucional` — Defeito 12
10. `fix(ui): separa a superfície da página da do conteúdo` — Defeito 13

---

## 6. O que já foi verificado e o que não foi

**Verificado com o app rodando** (medição no DOM, viewport de 1895px, tema claro):
- Todas as medidas "atual" citadas nos 13 defeitos.
- A causa-raiz de cada defeito (incluindo a ausência do Bootstrap, confirmada pela lista de `<link>` servida em `/`).
- O CSS proposto para os Defeitos 1, 2 e 4, aplicado em conjunto — resultado na tabela do Defeito 1.
- Os nomes e valores de todos os tokens do DS citados neste documento.

**Não verificado — confirme durante a implementação**:
- O CSS proposto para os Defeitos 3, 5 a 13 (é derivação direta do Figma, mas não foi executado).
- O comportamento abaixo de 992px. Por construção, todas as regras novas ficam dentro do bloco `@media (min-width: 992px)`, então nada abaixo desse ponto deveria mudar — mas a verificação visual continua obrigatória (seção 7, item 3). O ambiente de teste não permitiu reduzir o viewport CSS abaixo de 992px.
- O tema escuro com as regras novas.

---

## 7. Verificação obrigatória antes de declarar pronto

1. `python -m compileall -q app` → exit 0.
2. `python -m pytest -q` → 0 falhas. Os testes citados na seção 2 (itens 6 e 7) precisam ser **atualizados junto com o código**, não ignorados nem marcados como skip.
3. Inspeção visual com o app rodando, em **três larguras**: 1280px (paridade com o frame do Figma), 1600px (regra do contêiner máximo) e 900px (menu sobreposto, comportamento preservado).
4. Repetir a inspeção de 1280px no **tema escuro**, confirmando que nenhuma das novas regras fixa cor clara.
5. Reconferir cada critério de aceite (AC-1.1 a AC-13.3) com medição no DOM, não a olho.
6. Atualizar `.specs/features/govbr-design-system/validation.md` com o resultado desta rodada.
