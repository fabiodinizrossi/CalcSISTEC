# Design responsivo com o gov.br Design System Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/govbr-design-system/design.md`
**Spec**: `.specs/features/govbr-design-system/spec.md`
**Status**: Approved

---

## Notas de execução

- **Stage só caminhos explícitos** (`git add <caminho>`), nunca `git add -A` nem `git add .`: a pasta da feature tem 4 SVGs de cerca de 87 MB que não podem ser commitados, e `.agents/`, `.cursor/`, `.windsurf/` e `.claude/skills/tlc-spec-driven/` também estão fora de escopo. T1 trata disso.
- **Estado intermediário entre T2 e T16**: depois que o DS sai de `app/assets/`, o Dash não o carrega mais; as páginas públicas ficam sem o CSS do DS até o `PainelDash` entrar (T16). A suíte continua verde; é um estado de branch, sem deploy.
- **Fontes e ícones ficam na Phase 12** (T53 e T54), isoladas, porque exigem rede e autorização de Jaline e a licença da Rawline não está confirmada. Nada antes depende delas; botões de ícone levam `aria-label`, então o layout continua legível sem elas.
- **Ajustes ao design** encontrados ao montar as tasks (não mudam a spec):
  - Parcial novo `app/templates/shell/_scripts.html` (carrega `core.min.js` uma vez, `tema.js` e `confirmar.js`); o design lista só os outros parciais.
  - `validar_campos_campus(dados, inclusao=False)` no lugar de `exigir_nome_perfil`: na inclusão só Identificador e Nome do perfil são obrigatórios (DS-78, literal); na edição, os quatro campos.
  - Macro `mensagem`: `role="alert"` para `success` e `danger` (DS-22 é a spec); `role="status"` para `info` e `warning`.
  - Seletor "Exibir" da paginação (DS-83) é `<select>` nativo em formulário GET com botão "Aplicar", sem JavaScript próprio.
  - Testes de JS rodam com `node` (funções puras exportadas) e são pulados (`skipif`) se `node` não existir; nenhuma dependência nova no `requirements.txt`. O comportamento de DOM (foco preso, Esc, menu por teclado) é conferido na T55.

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `.specify/memory/constitution.md` (Princípio IV e Fluxo de Desenvolvimento), `TESTAR.md`; sem `AGENTS.md`, sem configuração de pytest, sem CI, sem linter. Linha de base: `python -m pytest -q` = **181 passed** (Python 3.12.10, pytest 9.1.1, Flask 3.1.3, Dash 4.4.1).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Shell Python (`app/shell.py`) | unit + integration | Todos os ramos; 1:1 com os ACs de menu, breadcrumb, identidade e `interpolate_index`; casos de borda (contato em branco, sem logotipo) | `tests/test_shell*.py` | `python -m pytest -q tests/test_shell.py` |
| Parciais Jinja e templates admin | integration (`server.test_client()`, `test_request_context`) | Cada parcial e cada página: caso feliz + estados de erro (campo `danger`, `br-message`) + variantes (sem menu, sem contato) | `tests/test_shell_parciais.py`, `tests/test_admin_paginas.py` | `python -m pytest -q tests/test_admin_paginas.py` |
| Rotas Flask do CRUD (`app/admin_campi.py`) | e2e (`test_client`, banco temporário) | Todas as rotas: caso feliz + cada caso de borda listado + erros (vazio, duplicado, inexistente, parâmetros inválidos) | `tests/test_admin_campi.py` | `python -m pytest -q tests/test_admin_campi.py` |
| Dados (`app/data/campi.py`) | unit | Todos os ramos; 1:1 com DS-66, DS-70 a DS-72; regressão dos testes existentes | `tests/test_campi.py`, `tests/test_campi_lista.py` | `python -m pytest -q tests/test_campi.py` |
| Componentes e páginas Dash | unit (árvore de componentes) | Classes `br-*` presentes, classes do Bootstrap ausentes, estado vazio, rótulo textual, nenhum componente do DS que dependa de JS (DS-27) | `tests/test_componentes_publicos.py`, `tests/test_paginas_publicas.py` | `python -m pytest -q tests/test_componentes_publicos.py` |
| CSS estático (`style.css`) | static (regex sobre o arquivo) | Sem hex/`rgb()`/`hsl()`, sem `--gov-*`, `@media` só nos pontos do DS, regras exigidas (1520px, 24px, 3px, tema escuro por `var()`); contraste dos pares de token (4,5:1 e 3:1) nos dois temas | `tests/test_style_css.py`, `tests/test_contraste_tema.py` | `python -m pytest -q tests/test_style_css.py` |
| JavaScript (`tema.js`, `confirmar.js`, script inline do tema) | unit via `node` (funções puras) + static | Tabela-verdade do tema (salvo x preferência x storage bloqueado); ciclo de foco e Esc do modal; ausência de `confirm()` nativo | `tests/test_js_*.py` | `python -m pytest -q tests/test_js_tema.py` |
| Domínio (`app/domain/`) | none (não tocado) | A suíte de paridade existente segue como guarda de regressão (Princípio I) | `tests/test_parity_dominio.py` | `python -m pytest -q` |
| Assets vendorizados, docs | none | - (gate de build; T53 acrescenta um teste de que todo asset local do HTML resolve) | - | build gate only |
| Navegador real (larguras, foco, teclado, tema) | manual | 11 páginas em 320, 576, 992, 1280 e 1600px; tema escuro; teclado; resultado registrado em arquivo (T55) | `.specs/features/govbr-design-system/verificacao-visual.md` | Chrome MCP |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Task com testes novos em um arquivo | `python -m pytest -q tests/<arquivo desta task>` |
| Full | Task que muda rota, template, shell ou componente compartilhado | `python -m pytest -q` (deve manter 181 + testes novos, nenhum removido) |
| Build | Fim de fase, task de config/asset/docs | `python -m compileall -q app` e `python -m pytest -q` (não há linter no repositório) |

`python scripts/verificar_prontidao_cutover.py` **não** é gate por task: hoje sai com NO-GO por causa do ambiente (autenticação, HTTPS e dataset publicado ausentes), não por causa de código. Roda na T55 só para registrar o estado.

---

## Execution Plan

Phases são ordenadas e sequenciais; dentro de cada uma, as tasks rodam na ordem numérica. Dependências entre fases apontam sempre para trás e ficam só no campo `Depends on`; o diagrama mostra as dependências dentro da fase.

### Phase 1: Entrega do DS

```
T1 → T2 → T3
```

### Phase 2: Parciais do shell

```
T4 → T5
T4 → T6
T4 → T7
T4 → T8
T4 → T9
T10   T11   T12
```

### Phase 3: Integração do shell (Flask e Dash)

```
T13 → T14
T13 → T15
T14 → T16
T15 → T16
```

### Phase 4: Páginas administrativas

```
T17 → T18 → T19 → T20 → T21
```

### Phase 5: Modal de confirmação

```
T22 → T23
```

### Phase 6: Dados e regras do CRUD de campi

```
T24   T25   T26   T27
```

### Phase 7: Telas do CRUD de campi

```
T28 → T29
T29 → T30
T30 → T31
T29 → T32
T29 → T33
T29 → T34
T34 → T35
```

### Phase 8: Configurações e limpeza do shell antigo

```
T36 → T37
T36 → T38
```

### Phase 9: Componentes públicos

```
T39 → T40
T39 → T41
T39 → T42
T39 → T43
```

### Phase 10: Páginas públicas

```
T44 → T45 → T46 → T47 → T48
```

### Phase 11: Estilo e tema

```
T49 → T50
T50 → T52
T51 → T52
```

### Phase 12: Fontes e ícones (requer autorização)

```
T53   T54
```

### Phase 13: Verificação e entrega

```
T55 → T56
T55 → T57
```

**Pacotes de execução (~7 tasks, fases inteiras):** 57 tasks passam de um lote; no Execute a skill oferece sub-agentes por lote antes de despachar qualquer um.

---

## Task Breakdown

### Phase 1: Entrega do DS

### T1: Versionar as specs sem os SVGs

**What**: Ignorar os SVGs de referência do Figma e versionar `STATE.md`, `spec.md`, `design.md` e `tasks.md`, para que cada task marque seu progresso no mesmo commit.
**Where**: `.gitignore`
**Depends on**: None
**Reuses**: Padrão de `.gitignore` existente
**Requirement**: - (infraestrutura da feature)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `.gitignore` ignora `.specs/features/**/*.svg`
- [x] `git status --porcelain` não lista nenhum SVG de `.specs/`
- [x] Commit inclui só `.gitignore`, `.specs/STATE.md` e `.specs/features/govbr-design-system/{spec,design,tasks}.md`
- [x] Gate build passa

**Tests**: none
**Gate**: build
**Commit**: `chore(specs): versiona specs da feature govbr-design-system sem os SVGs`

---

### T2: Servir o DS de `app/static/` por blueprint

**What**: Mover o DS com `git mv` para `app/static/govbr-ds/`, criar `app/shell.py` com o blueprint `ds_static` (URL `/ds/`) e `init_shell(server, dash_app)`, chamar `init_shell` em `app/app.py` e apontar o link de `_base.html` para `/ds/govbr-ds/dist/core.min.css` (sem isso as páginas administrativas ficam sem CSS; por isso a mudança é uma só).
**Where**: `app/shell.py`
**Depends on**: T1
**Reuses**: Conteúdo já versionado de `app/assets/govbr-ds/`; padrão de `server.test_client()` de `tests/test_instalacao.py:131`
**Requirement**: DS-24, DS-28

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `app/assets/govbr-ds/` não existe mais; `app/static/govbr-ds/dist/core.min.css` e `core.min.js` existem (histórico preservado por `git mv`)
- [x] `GET /ds/govbr-ds/dist/core.min.css` e `GET /ds/govbr-ds/dist/core.min.js` respondem 200 pelo `test_client`
- [x] `GET /admin/login` referencia `/ds/govbr-ds/dist/core.min.css` e não referencia `/assets/govbr-ds/`
- [x] Novo `tests/test_shell_assets.py` cobre os três itens acima; gate full passa (≥ 181 + novos)

**Tests**: integration
**Gate**: full
**Commit**: `refactor(assets): serve o gov.br DS de app/static por blueprint`

---

### T3: Mover `atualizar.js` para `app/static/js/`

**What**: Tirar o script administrativo de `app/assets/` (o Dash o carregava em todas as páginas públicas) e referenciá-lo por `/ds/js/atualizar.js` em `atualizar.html`.
**Where**: `app/static/js/atualizar.js`
**Depends on**: T2
**Reuses**: `app/assets/js/atualizar.js` (conteúdo idêntico, só muda de pasta); referência em `app/templates/atualizar.html:74`
**Requirement**: DS-24

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `app/assets/js/` não existe; `GET /ds/js/atualizar.js` responde 200
- [x] `atualizar.html` referencia `/ds/js/atualizar.js` e não `/assets/js/`
- [x] `tests/test_shell_assets.py` ganha os testes dos dois itens; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `refactor(assets): move atualizar.js para app/static`

---

### Phase 2: Parciais do shell

### T4: Contexto do shell (menu, breadcrumb, identidade)

**What**: Em `app/shell.py`, criar `PAGINAS_PUBLICAS`, `PAGINAS_ADMIN` e `contexto_shell(caminho)`, que devolve itens de menu com `ativo`, breadcrumb, `com_menu`, dados da instituição e e-mail de contato.
**Where**: `app/shell.py`
**Depends on**: T2
**Reuses**: `PAGINAS` de `app/components/navigation.py` (rótulos e ordem); `dados_instituicao`, `get_contato_email` de `app/data/config_store.py`; `_contexto_base()` de `app/app.py:128`
**Requirement**: DS-11, DS-12, DS-19, DS-39, DS-41, DS-56, DS-61

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Menu público tem 5 itens na ordem Início, Matrículas, Eficiência Acadêmica, Taxa de Evasão Anual, Percentuais Legais; para cada um dos 5 caminhos, só esse item vem com `ativo=True`
- [x] Breadcrumb vazio em `/`; `["Início", "Matrículas"]` em `/matriculas` (último sem `href`); nas rotas de campi, `Configurações > Campi`, `Configurações > Campi > Editar` e `Configurações > Campi > Incluir`
- [x] `com_menu=False` em `/admin/login`, `/recuperar-acesso` e `/admin/instalacao`; breadcrumb vazio nessas três
- [x] Nome, sigla, site e e-mail vêm de `config_store` (teste com `monkeypatch`), nunca de literal; e-mail e site em branco chegam como vazios
- [x] Novo `tests/test_shell.py` cobre todos os itens; gate quick `python -m pytest -q tests/test_shell.py` passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(shell): contexto do shell com menu, breadcrumb e identidade`

---

### T5: Parcial `_head.html`

**What**: Criar o `<head>` do shell: viewport, `core.min.css` uma vez, `style.css`, título e o script inline que define `data-tema` em `<html>` antes da primeira pintura.
**Where**: `app/templates/shell/_head.html`
**Depends on**: T4
**Reuses**: Meta viewport e links de `app/templates/_base.html:5-8`
**Requirement**: DS-01, DS-25, DS-45, DS-46, DS-50, DS-51, DS-52

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] HTML renderizado tem `<meta name="viewport" content="width=device-width, initial-scale=1">` e exatamente 1 link para `core.min.css`
- [x] Nenhum URL externo (`http://` ou `https://`) no parcial
- [x] O script inline, executado em `node` com `document`, `localStorage` e `matchMedia` simulados, resulta em: sem escolha salva e sistema escuro → `escuro`; sem escolha e sistema claro ou sem preferência → `claro`; escolha `claro` salva e sistema escuro → `claro`; `localStorage` lançando exceção → preferência do sistema, sem erro
- [x] Novos `tests/test_shell_parciais.py` e `tests/test_js_tema.py` (este com `skipif` sem `node`); gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial head com viewport, DS único e tema sem flash`

---

### T6: Parcial `_header.html`

**What**: Criar o `br-header` com link de salto, logotipo, título "Painel de Acompanhamento Sistec", nome da instituição, botão de tema (`aria-pressed`, rótulo textual) e botão hambúrguer com `aria-expanded`.
**Where**: `app/templates/shell/_header.html`
**Depends on**: T4
**Reuses**: `<img src="/branding/logo">` e texto alternativo de `_base.html:16-17`; `GET /branding/logo` de `app/app.py:825`
**Requirement**: DS-04, DS-05, DS-10, DS-19, DS-32, DS-36, DS-39, DS-40, DS-47, DS-55

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O primeiro `<a>` do HTML renderizado é "Ir para o conteúdo principal" com `href="#main-content"`
- [x] `<img>` do logotipo tem `alt` não vazio com e sem nome de instituição configurado
- [x] Botão de tema tem texto "Usar tema escuro" e `aria-pressed="false"`; botão hambúrguer tem `aria-expanded="false"` e `aria-controls`; sem menu (`com_menu=False`) o hambúrguer não aparece
- [x] Logotipo fica dentro de um invólucro com classe própria para superfície clara nos dois temas
- [x] `GET /branding/logo` sem logotipo enviado responde com `padrao-generico.svg` (DS-40)
- [x] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial header br-header com botões de tema e menu`

---

### T7: Parcial `_menu.html`

**What**: Criar o `br-menu` com os itens do contexto, `aria-current="page"` e estado ativo no item da página atual.
**Where**: `app/templates/shell/_menu.html`
**Depends on**: T4
**Reuses**: Lista de itens de `contexto_shell` (T4); rótulos de `app/components/navigation.py`
**Requirement**: DS-04, DS-05, DS-11, DS-12

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Menu público renderiza 5 links na ordem da spec; só o da página atual tem `aria-current="page"` e a classe de estado ativo do DS
- [x] Menu administrativo renderiza os itens de `PAGINAS_ADMIN`
- [x] Com `com_menu=False` o parcial não renderiza nada
- [x] Todos os itens são `<a href>` (navegam sem JavaScript)
- [x] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial menu br-menu com item ativo`

---

### T8: Parcial `_breadcrumb.html`

**What**: Criar o `br-breadcrumb` a partir das migalhas do contexto, com a página atual sem link e com `aria-current="page"`.
**Where**: `app/templates/shell/_breadcrumb.html`
**Depends on**: T4
**Reuses**: Migalhas de `contexto_shell` (T4)
**Requirement**: DS-56, DS-61

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Sem migalhas (capa, login, recuperar acesso, instalação) o parcial não renderiza nada
- [x] Com `Início > Matrículas`: primeiro item é link para `/`; último é texto com `aria-current="page"`
- [x] Trilha `Configurações > Campi > Editar` renderiza os 3 itens na ordem
- [x] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial breadcrumb br-breadcrumb`

---

### T9: Parcial `_footer.html`

**What**: Criar o `br-footer` com nome, site e e-mail da instituição (omitindo o que estiver em branco) e o link "Área administrativa".
**Where**: `app/templates/shell/_footer.html`
**Depends on**: T4
**Reuses**: Rodapé de `_base.html:31-38`; destino do link atual em `app/components/footer.py`
**Requirement**: DS-16, DS-19, DS-39, DS-41

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Com tudo preenchido: nome, site (com `https://` quando faltar, `rel="noopener"`), e-mail em `mailto:` e "Área administrativa"
- [x] Com e-mail e site em branco: nenhum rótulo, link ou espaço vazio para eles; nome e "Área administrativa" permanecem
- [x] Sem nome de instituição: nenhum elemento vazio
- [x] Testes dos três casos em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial footer br-footer com contatos opcionais`

---

### T10: Parcial `_scripts.html`

**What**: Criar o parcial de scripts com `core.min.js` uma vez e `onerror` que põe `ds-sem-js` em `<html>`.
**Where**: `app/templates/shell/_scripts.html`
**Depends on**: T2
**Reuses**: `core.min.js` de `app/static/govbr-ds/dist/`
**Requirement**: DS-26, DS-27

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Exatamente 1 `<script>` para `core.min.js`, com `onerror` que adiciona `ds-sem-js` a `document.documentElement`
- [ ] Nenhuma referência a `dist/components/`, `core-init`, `core-base` nem a versão não minificada
- [ ] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial scripts com core.min.js único`

---

### T11: Parcial `_modal_confirmacao.html`

**What**: Criar o markup único do `br-scrim` + `br-modal` de confirmação, fechado por padrão, com ícone de alerta, área da pergunta e botões "Cancelar" (`secondary`) e de confirmação (`primary`).
**Where**: `app/templates/shell/_modal_confirmacao.html`
**Depends on**: None
**Reuses**: Classes `br-scrim` e `br-modal` de `app/static/govbr-ds/dist/core.css`
**Requirement**: DS-58, DS-60, DS-73

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Markup tem `role="dialog"`, `aria-modal="true"`, `aria-labelledby` apontando para um id existente, ícone de alerta com `aria-hidden="true"`
- [ ] Botão "Cancelar" é `br-button secondary`; botão de confirmação é `br-button primary`, com ids fixos que `confirmar.js` (T22) vai usar
- [ ] Renderizado sem a classe `active` do scrim (fechado)
- [ ] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): parcial do modal de confirmação br-modal`

---

### T12: Macros `campo`, `mensagem` e `botoes_formulario`

**What**: Criar `_macros.html` com os macros de formulário: `campo` (`br-input` com rótulo acima, ajuda e erro `danger` ligado por `aria-describedby`), `mensagem` (`br-message`) e `botoes_formulario` (Cancelar `secondary`, Salvar `primary`).
**Where**: `app/templates/shell/_macros.html`
**Depends on**: None
**Reuses**: Marcação de `br-input` e `br-button` de `app/templates/login.html` e `configuracoes.html`
**Requirement**: DS-20, DS-21, DS-22

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `campo` com `erro` marca o estado `danger`, mostra o texto abaixo do campo e liga o campo ao texto por `aria-describedby` com id existente; sem erro não há `aria-describedby` vazio
- [ ] `campo` renderiza `<label for>` visível acima do input; `obrigatorio` marca o campo como obrigatório
- [ ] `mensagem("success"|"danger", ...)` tem `role="alert"`; `info` e `warning` têm `role="status"`; tipo vira classe `br-message <tipo>`
- [ ] `botoes_formulario` renderiza "Cancelar" (link, `secondary`) antes de "Salvar" (`primary`)
- [ ] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): macros de formulário e mensagem do DS`

---

### Phase 3: Integração do shell (Flask e Dash)

### T13: `init_shell` injeta o contexto do shell nos templates

**What**: Em `init_shell`, registrar um context processor que injeta `shell = contexto_shell(request.path)` (mais `instituicao` e `contato_email` quando a rota não os passar) em todo template Flask.
**Where**: `app/shell.py`
**Depends on**: T4
**Reuses**: `contexto_shell` (T4); `_contexto_base()` de `app/app.py:128`
**Requirement**: DS-19, DS-39

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Dentro de `server.test_request_context("/admin/historico")`, `render_template_string("{{ shell.menu|length }}")` devolve o número de itens administrativos
- [ ] Rota que já passa `instituicao` e `contato_email` mantém os valores dela
- [ ] Testes em `tests/test_shell.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): context processor com o contexto do shell`

---

### T14: `_base.html` compõe os parciais do shell

**What**: Reescrever `_base.html` para compor head, cabeçalho, menu, breadcrumb, `<main id="main-content">` em `container-fluid`, modal, rodapé e scripts, com `lang="pt-BR"`.
**Where**: `app/templates/_base.html`
**Depends on**: T13, T5, T6, T7, T8, T9, T10, T11, T12
**Reuses**: Blocos `title` e `content` do `_base.html` atual
**Requirement**: DS-01, DS-03, DS-19, DS-25, DS-26, DS-31, DS-32, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET /admin/login` responde 200 com `<html lang="pt-BR">`, 1 `core.min.css`, 1 `core.min.js`, `br-header`, `br-footer`, `container-fluid`, e sem `app-header`, `app-footer` nem `admin-nav`
- [ ] Com sessão autenticada e instalação concluída (`monkeypatch`), `GET /admin/historico` mostra `br-menu` e `br-breadcrumb`; `/admin/login` não mostra nenhum dos dois
- [ ] Nenhuma folha do Bootstrap no HTML
- [ ] Novo `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `refactor(ui): base Jinja compõe o shell do DS`

---

### T15: `PainelDash` monta o shell ao redor do Dash

**What**: Criar a classe `PainelDash(dash.Dash)` com `interpolate_index(metas, title, css, config, scripts, app_entry, favicon, renderer)`, que devolve o HTML completo do shell com `app_entry` dentro de `<main id="main-content">`, item de menu e breadcrumb pelo caminho da requisição.
**Where**: `app/shell.py`
**Depends on**: T13, T5, T6, T7, T8, T9, T10, T11
**Reuses**: Parciais do shell; assinatura de `interpolate_index` verificada no Design
**Requirement**: DS-10, DS-16, DS-25, DS-26, DS-27, DS-31, DS-32, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Chamado em `server.test_request_context("/matriculas")`, o HTML tem `lang="pt-BR"`, `br-header`, item "Matrículas" com `aria-current="page"`, `br-footer`, e `app_entry`, `config`, `scripts` e `renderer` presentes; `app_entry` dentro de `<main id="main-content">`
- [ ] 1 `core.min.css` e 1 `core.min.js`; `style.css` aparece 1 vez mesmo quando o argumento `css` também o traz
- [ ] Sem folha do Bootstrap
- [ ] Testes em `tests/test_shell.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(shell): PainelDash injeta o shell no HTML do Dash`

---

### T16: Ligar `PainelDash` em `app.py`

**What**: Trocar `dash.Dash` por `PainelDash` sem `external_stylesheets` (sem `dbc.themes.BOOTSTRAP`), remover o `index_string` fixo, reduzir `serve_layout` ao aviso "sem correção PNP" mais `dash.page_container`, e chamar `init_shell(server, app)`.
**Where**: `app/app.py`
**Depends on**: T14, T15, T2
**Reuses**: `make_aviso_sem_pnp`, `dash.page_container`
**Requirement**: DS-18, DS-25, DS-26, DS-61

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET /`, `/matriculas`, `/eficiencia`, `/evasao` e `/percentuais-legais` respondem 200 com `br-header`, `br-menu`, `br-footer`, 1 `core.min.css`, 1 `core.min.js` e nenhuma folha do Bootstrap
- [ ] Em cada uma, só o item de menu da própria página tem `aria-current="page"`; as 4 diferentes da capa mostram breadcrumb `Início > título`; a capa não mostra
- [ ] `app.layout()` não contém mais cabeçalho, menu nem rodapé do Dash
- [ ] Testes em `tests/test_shell.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `refactor(ui): páginas públicas passam a usar o shell do DS`

---

### Phase 4: Páginas administrativas

### T17: Login administrativo

**What**: Reescrever `login.html` com título "Acesso ao sistema", campos com rótulo acima e texto de apoio (`br-input`, `br-password`), link "Esqueci minha senha" abaixo do campo de senha e botão "Entrar" na largura do formulário; erros pelo macro `mensagem` e estado `danger`.
**Where**: `app/templates/login.html`
**Depends on**: T14, T12
**Reuses**: Nomes de campos e lógica de `admin_login` em `app/app.py:132`; macros `campo` e `mensagem`
**Requirement**: DS-20, DS-21, DS-23, DS-57

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET /admin/login` mostra "Acesso ao sistema", 2 campos com `<label>` visível, texto de apoio, e "Esqueci minha senha" depois do campo de senha na ordem do HTML
- [ ] Botão "Entrar" tem `br-button primary` com classe de largura total
- [ ] POST com campo inválido devolve 200 com o campo em `danger` e `aria-describedby` apontando para um id presente
- [ ] POST com credenciais recusadas mostra `br-message danger` com `role="alert"`
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `feat(ui): login administrativo no padrão do DS`

---

### T18: Recuperar acesso

**What**: Reescrever `recuperar_acesso.html` com o layout do shell e botão de retorno em `br-button`.
**Where**: `app/templates/recuperar_acesso.html`
**Depends on**: T17
**Reuses**: Texto atual da página
**Requirement**: DS-19, DS-23

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET /recuperar-acesso` responde 200 com `<h1>`, `br-header`, `br-footer`, sem menu e sem breadcrumb
- [ ] O botão de voltar é `br-button` e leva a `/admin/login`
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `feat(ui): recuperar acesso no padrão do DS`

---

### T19: Assistente de instalação

**What**: Reescrever `instalacao.html` com `campo`, `br-button`, `br-table` e `mensagem` do DS, em largura total abaixo de 576px, sem `confirm()` nativo.
**Where**: `app/templates/instalacao.html`
**Depends on**: T18
**Reuses**: Campos e ações de `admin_instalacao` em `app/app.py:179`
**Requirement**: DS-20, DS-21, DS-23

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Com sessão autenticada, `GET /admin/instalacao` responde 200; todo `<input>` de texto tem `<label for>` e está em `br-input`
- [ ] Sem menu nem breadcrumb (DS-56); nenhum `confirm(` no arquivo
- [ ] POST com nome da instituição vazio devolve o campo em `danger` com mensagem ligada por `aria-describedby`
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `feat(ui): assistente de instalação no padrão do DS`

---

### T20: Histórico de atualizações

**What**: Reescrever `historico.html` com `br-table` dentro de contêiner rolável e `br-message info` quando não houver registros.
**Where**: `app/templates/historico.html`
**Depends on**: T19
**Reuses**: `historico_listar` e a rota `admin_historico` de `app/app.py:510`
**Requirement**: DS-08, DS-20, DS-56

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Com registros (`monkeypatch` de `historico_listar`), a tabela é `br-table` dentro de contêiner com rolagem contida; sem `table-scroll-wrapper` antigo
- [ ] Sem registros, `br-message info` no lugar da tabela
- [ ] Breadcrumb `Início > Histórico de atualizações` presente
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `feat(ui): histórico no padrão do DS`

---

### T21: Tela de atualização

**What**: Reescrever `atualizar.html` com `br-button`, `br-message` para o estado da execução e formulários em largura total abaixo de 576px, mantendo os 4 `data-confirm` e o script `/ds/js/atualizar.js`.
**Where**: `app/templates/atualizar.html`
**Depends on**: T20, T3
**Reuses**: Ids que `atualizar.js` consulta (`btn-cancelar`, `btn-descartar`, `btn-publicar`, `btn-desfazer`)
**Requirement**: DS-08, DS-20, DS-22, DS-23

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Com sessão autenticada e instalação concluída, `GET /admin/atualizar` responde 200 com breadcrumb e `br-menu` administrativo
- [ ] Os 4 ids de botão e os 4 atributos `data-confirm` continuam presentes com os mesmos textos
- [ ] Botões empilhados abaixo de 576px pelas classes do DS (sem `@media` próprio)
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `feat(ui): tela de atualização no padrão do DS`

---

### Phase 5: Modal de confirmação

### T22: `confirmar.js` abre o `br-modal` no lugar de `confirm()`

**What**: Criar `confirmar.js` com `window.confirmarAcao(mensagem, {rotuloConfirmar}) -> Promise<boolean>` (abre o modal, prende o foco, fecha com Esc, devolve o foco ao controle de origem) e a interceptação de `.confirm-form` e `button[data-confirm]`; incluir o script em `_scripts.html`.
**Where**: `app/static/js/confirmar.js`
**Depends on**: T10, T11
**Reuses**: Textos de `data-confirm` existentes; ids do modal de T11
**Requirement**: DS-58, DS-59, DS-60

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Funções puras exportadas (`proximoFoco(indice, total, shift)`, `teclaFecha(tecla)`) rodam em `node`: Tab no último elemento volta ao primeiro, Shift+Tab no primeiro vai ao último, Esc fecha, outras teclas não
- [ ] O arquivo não contém chamada ao `confirm()` nativo; usa os ids do modal de T11 (teste de contrato entre os dois arquivos)
- [ ] `_scripts.html` carrega `confirmar.js` uma vez, depois de `core.min.js`
- [ ] Novo `tests/test_js_confirmar.py` (com `skipif` sem `node`); gate quick passa. O comportamento no DOM é conferido na T55

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): confirmação em br-modal com foco preso e Esc`

---

### T23: `atualizar.js` usa `confirmarAcao`

**What**: Trocar as 4 chamadas ao `confirm()` de `atualizar.js` (cancelar, descartar, publicar e desfazer) por `await confirmarAcao(...)`.
**Where**: `app/static/js/atualizar.js`
**Depends on**: T22, T3
**Reuses**: `confirmarAcao` (T22)
**Requirement**: DS-59

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Nenhum `confirm(` nativo em `app/static/js/*.js` (regex com fronteira de palavra, ignorando `confirmarAcao(`)
- [ ] `atualizar.js` chama `confirmarAcao` 4 vezes, com os textos de `data-confirm` dos 4 botões
- [ ] Testes em `tests/test_js_confirmar.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `refactor(ui): atualizar.js confirma pelo modal do DS`

---

### Phase 6: Dados e regras do CRUD de campi

### T24: `CampusInvalido` informa o campo

**What**: Dar a `CampusInvalido` o atributo `campo` (`id_perfil` ou `co_unidade`, padrão `None`) e preenchê-lo em `salvar_campus_manual` e `incluir_campus`, com as mensagens "esse identificador de perfil já está em outro campus" e "esse código da unidade já está em outro campus".
**Where**: `app/data/campi.py`
**Depends on**: None
**Reuses**: `sqlite3.IntegrityError` já tratado em `salvar_campus_manual` e `incluir_campus`
**Requirement**: DS-71

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Identificador duplicado levanta `CampusInvalido` com `campo == "id_perfil"` e a mensagem do identificador; código duplicado, `campo == "co_unidade"` e a mensagem do código (nos dois caminhos: edição e inclusão)
- [ ] Chamadores existentes de `CampusInvalido(mensagem)` continuam válidos (`campo` padrão `None`); testes antigos passam sem alteração
- [ ] Testes novos em `tests/test_campi.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(campi): CampusInvalido informa o campo em conflito`

---

### T25: `obter_campus`

**What**: Criar `obter_campus(id_perfil, db_path)`, que devolve o campus como dict ou `None`.
**Where**: `app/data/campi.py`
**Depends on**: None
**Reuses**: `_ler` e `COLUNAS` de `app/data/campi.py`
**Requirement**: DS-66

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Devolve o dict com as colunas de `campi_sistec` para um id existente e `None` para inexistente ou vazio
- [ ] Testes em `tests/test_campi.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(campi): obter_campus por identificador`

---

### T26: `validar_campos_campus`

**What**: Criar `validar_campos_campus(dados, inclusao=False)`, função pura que devolve o mapa campo → "Preencha o campo obrigatório": na edição, os 4 campos; na inclusão, só `id_perfil` e `nome_perfil`.
**Where**: `app/data/campi.py`
**Depends on**: None
**Reuses**: Nomes de campo de `salvar_campus_manual` e `incluir_campus`
**Requirement**: DS-70, DS-72

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Edição com cada campo vazio, um por vez, devolve só esse campo; todos vazios devolve os 4; todos preenchidos devolve `{}`
- [ ] Valor só com espaços conta como vazio; a função não faz I/O
- [ ] Inclusão exige `id_perfil` e `nome_perfil`; `co_unidade`, `cidade` e `nome_unidade` vazios não geram erro
- [ ] Testes em `tests/test_campi.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(campi): validação dos campos obrigatórios do campus`

---

### T27: `filtrar_e_paginar`

**What**: Criar o módulo `app/admin_campi.py` com a função pura `filtrar_e_paginar(campi, q, pagina, por_pagina) -> PaginaCampi` (busca por perfil, cidade ou nome da unidade sem diferenciar maiúsculas; `por_pagina` 10, 25 ou 50).
**Where**: `app/admin_campi.py`
**Depends on**: None
**Reuses**: Modelo `PaginaCampi` do Design
**Requirement**: DS-81, DS-82, DS-83

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Com 22 campi: `por_pagina=10, pagina=3` → 2 itens, `inicio=21`, `fim=22`, `total=22`; `por_pagina=25` → 1 página com 22 itens
- [ ] Busca "santa" acha perfil, cidade ou nome da unidade com "Santa", sem diferenciar caixa; texto sem resultado → `total=0`, `itens=[]`, `inicio=0`, `fim=0`
- [ ] `por_pagina` inválido (7, "x", 0) vira 10; `pagina` inválida (0, negativa, texto ou além do fim) vira 1
- [ ] Novo `tests/test_admin_campi.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(campi): busca e paginação da lista de campi`

---

### Phase 7: Telas do CRUD de campi

### T28: Macros `tag_situacao` e `botao_icone`

**What**: Acrescentar a `_macros.html` os macros `tag_situacao(ativo)` (`br-tag` com texto "Ativo" ou "Desativado") e `botao_icone(icone, rotulo, ...)` (botão só de ícone, com `aria-label`).
**Where**: `app/templates/shell/_macros.html`
**Depends on**: T12
**Reuses**: Macros de T12
**Requirement**: DS-63, DS-65

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `tag_situacao(True)` mostra o texto "Ativo" e `tag_situacao(False)` mostra "Desativado", ambos em `br-tag` (a situação não depende só da cor)
- [ ] `botao_icone` renderiza `<button>` com `aria-label` igual ao rótulo, ícone com `aria-hidden="true"` e área mínima definida por classe do DS
- [ ] Testes em `tests/test_shell_parciais.py`; gate quick passa

**Tests**: integration
**Gate**: quick
**Commit**: `feat(shell): macros de tag de situação e botão de ícone`

---

### T29: Lista de campi (`GET /admin/campi`)

**What**: Criar o blueprint `campi_bp` com a rota `GET /admin/campi` (autenticada) e `campi_lista.html`: título "Campi do Sistec", `br-table` com as 7 colunas, tags de situação, aviso de identificador suspeito, botões de ícone por linha, botão "Incluir campus", mensagens `flash` e estado vazio; registrar o blueprint em `app/app.py`.
**Where**: `app/admin_campi.py`
**Depends on**: T28, T27, T14, T16
**Reuses**: `listar_campi`, `id_suspeito` de `app/data/campi.py`; `requer_autenticacao`; `flask.flash`; padrão de teste de `tests/test_instalacao.py:131`
**Requirement**: DS-22, DS-56, DS-62, DS-63, DS-64, DS-65, DS-79

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Sem sessão autenticada, redireciona ao login; com sessão e banco temporário (`monkeypatch` de `DB_PATH` do módulo), responde 200 com as colunas Perfil, Identificador, Código da unidade, Cidade, Nome da unidade, Situação e Ações
- [ ] Cada linha tem `br-tag` "Ativo" ou "Desativado" e botões com nomes acessíveis "Editar campus {perfil}", "Desativar campus {perfil}" (ou "Reativar") e "Excluir campus {perfil}"
- [ ] Identificador suspeito mostra "Identificador inválido: a atualização não roda assim" na linha; identificador válido não
- [ ] Nenhum `<input>` dentro de `<td>` (DS-79); tabela em contêiner com rolagem própria
- [ ] Sem campus cadastrado, `br-message info` convida a importar a lista ou incluir um campus; mensagem `flash` aparece como `br-message`
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): lista de campi em br-table`

---

### T30: Editar campus

**What**: Criar `GET|POST /admin/campi/<id_perfil>/editar` e `campi_form.html`: título "Editar campus | {perfil}", 4 campos com rótulo visível em linhas da grade, botões Cancelar e Salvar alinhados à direita a partir de 576px, erros por campo e banner no topo.
**Where**: `app/admin_campi.py`
**Depends on**: T29, T24, T25, T26, T12
**Reuses**: `salvar_campus_manual`, `obter_campus`, `validar_campos_campus`, `CampusInvalido.campo`; macros `campo`, `mensagem`, `botoes_formulario`
**Requirement**: DS-66, DS-67, DS-68, DS-69, DS-70, DS-71, DS-72, DS-79

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET` mostra "Editar campus | {perfil}", breadcrumb "Configurações > Campi > Editar", 4 `br-input` com `<label for>` visível e Cancelar (`secondary`) e Salvar (`primary`)
- [ ] `POST` válido grava, redireciona para `/admin/campi` e a lista mostra `br-message success` "Campus atualizado."; identificador com menos de 5 dígitos também salva
- [ ] `POST` com código vazio devolve 200 na mesma tela, campo em `danger` com "Preencha o campo obrigatório" e banner `danger` `role="alert"` "Erro. Preencha abaixo os campos obrigatórios antes de enviar os dados."; os valores digitados permanecem
- [ ] Identificador ou código de outro campus: campo em `danger` com "esse identificador de perfil já está em outro campus" ou "esse código da unidade já está em outro campus"
- [ ] Id inexistente redireciona à lista com `br-message danger` "Campus não encontrado."
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): tela de edição de campus`

---

### T31: Incluir campus

**What**: Criar `GET|POST /admin/campi/novo` com o mesmo layout da edição e o campo extra "Nome do perfil".
**Where**: `app/admin_campi.py`
**Depends on**: T30
**Reuses**: `incluir_campus`; `campi_form.html` (T30)
**Requirement**: DS-77, DS-78

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET` mostra "Incluir campus" e 5 campos: Identificador do perfil, Nome do perfil, Código da unidade, Cidade, Nome da unidade
- [ ] `POST` com identificador e nome do perfil preenchidos grava (`origem = 'manual'`), redireciona e a lista mostra `br-message success` "Campus incluído."
- [ ] `POST` sem identificador ou sem nome do perfil devolve 200 com campo `danger`, "Preencha o campo obrigatório" e o banner de erro
- [ ] Identificador repetido mostra a mensagem da regra no campo
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): tela de inclusão de campus`

---

### T32: Desativar e reativar campus

**What**: Criar `POST /admin/campi/<id_perfil>/situacao` (campo `ativo=0|1`), sem confirmação, com `flash` de sucesso e redirecionamento à lista.
**Where**: `app/admin_campi.py`
**Depends on**: T29
**Reuses**: `definir_ativo`, `obter_campus`
**Requirement**: DS-76

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `ativo=0` desativa, `ativo=1` reativa, cada um com `br-message success` na lista seguinte; a linha passa a mostrar a tag "Desativado" ou "Ativo"
- [ ] Os botões Desativar e Reativar da lista não levam `data-confirm`
- [ ] Id inexistente redireciona com `br-message danger` "Campus não encontrado."
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): desativar e reativar campus`

---

### T33: Excluir campus com confirmação em modal

**What**: Criar `POST /admin/campi/<id_perfil>/excluir` e ligar o botão Excluir da lista ao modal por `.confirm-form` e `data-confirm`, com a pergunta "Tem certeza que deseja excluir o campus {perfil}?", o aviso do Sistec e o rótulo "Excluir".
**Where**: `app/admin_campi.py`
**Depends on**: T29, T22
**Reuses**: `excluir_campus`; `data-confirm` e `confirmar.js`; texto de aviso de `configuracoes.html:124`
**Requirement**: DS-73, DS-74, DS-75

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O formulário de exclusão de cada linha é `.confirm-form` com `data-confirm` contendo "Tem certeza que deseja excluir o campus {perfil}?" e o aviso de que o perfil volta na próxima atualização se ainda existir no Sistec, e com o rótulo de confirmação "Excluir"
- [ ] `POST` remove o campus e a lista seguinte mostra `br-message success` "Perfil excluído da lista."
- [ ] Sem o `POST` (Cancelar no modal não envia nada), o campus continua na lista
- [ ] Id inexistente redireciona com `br-message danger` "Campus não encontrado."
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa. O modal em si é conferido na T55

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): exclusão de campus com confirmação em modal`

---

### T34: Busca e paginação na lista

**What**: Ligar `filtrar_e_paginar` à lista por parâmetros GET `q`, `pagina` e `por_pagina`: barra com título "Campi" e busca por envio, e rodapé com "Exibir" (10, 25, 50; botão "Aplicar"), "1-10 de N itens" e botões de página anterior e próxima.
**Where**: `app/admin_campi.py`
**Depends on**: T29, T27
**Reuses**: `filtrar_e_paginar` (T27); `br-message info`
**Requirement**: DS-80, DS-81, DS-82, DS-83

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET /admin/campi` mostra a barra "Campi" com campo de busca (`<form method="get">` com botão de lupa de nome acessível) acima da tabela
- [ ] `?q=<parte de uma cidade>` lista só as linhas que a contêm; `?q=zzz` mostra `br-message info` "Nenhum campus encontrado."
- [ ] Com 22 campi: padrão mostra "1-10 de 22 itens"; `?por_pagina=25` mostra "1-22 de 22 itens"; `?pagina=3` mostra "21-22 de 22 itens"; anterior desabilitado na página 1 e próxima na última
- [ ] `pagina` e `por_pagina` inválidos na URL viram 1 e 10, sem erro; a busca e o tamanho de página se mantêm nos links de página
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): busca e paginação na lista`

---

### T35: Visão em cards

**What**: Acrescentar o parâmetro `visao=lista|cards`, o botão "Visualizar em Cards" / "Visualizar em Lista" com `aria-pressed` e a visão em `br-card` com as mesmas ações da linha.
**Where**: `app/admin_campi.py`
**Depends on**: T34
**Reuses**: Macros `tag_situacao` e `botao_icone`; formulários de situação e exclusão de T32 e T33
**Requirement**: DS-84, DS-85

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O botão de visão aparece acima da lista com `aria-pressed` coerente com a visão atual e rótulo "Visualizar em Cards" (visão lista) ou "Visualizar em Lista" (visão cards)
- [ ] Com `?visao=cards`, cada campus vira um `br-card` com perfil, identificador, código, cidade, nome da unidade, tag de situação e as ações Editar, Desativar (ou Reativar) e Excluir com os mesmos nomes acessíveis e `data-confirm`
- [ ] `visao` inválida cai em lista; busca e paginação continuam valendo nos cards
- [ ] Testes em `tests/test_admin_campi.py`; gate full passa

**Tests**: e2e
**Gate**: full
**Commit**: `feat(campi): visão em cards da lista`

---

### Phase 8: Configurações e limpeza do shell antigo

### T36: `configuracoes.html` no padrão do DS

**What**: Reescrever `configuracoes.html`: a seção "Campi do Sistec" vira resumo (total, ativos, aviso de suspeitos) com o link "Gerenciar campi"; e-mail, logotipo, fatores, `qtdPerfis` e importação de perfis passam a usar `campo`, `br-button` e `mensagem`; sai o script inline com `confirm()`.
**Where**: `app/templates/configuracoes.html`
**Depends on**: T29, T12, T22
**Reuses**: Formulários e ações que continuam em `admin_config` (`app/app.py:522`); `data-confirm` existentes
**Requirement**: DS-20, DS-21, DS-22, DS-23, DS-59, DS-62, DS-79

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `GET /admin/config` responde 200 com link "Gerenciar campi" para `/admin/campi`, sem `<input name="novo_id_perfil">` e sem nenhum campo de campus em célula de tabela
- [ ] Nenhuma ocorrência de `confirm(` nativo no arquivo; os 6 `data-confirm` restantes (e-mail, logotipo, 2 de fatores, resetar, aplicar) continuam com o mesmo texto
- [ ] Campos com `<label>` visível; mensagens de e-mail, logotipo e fatores em `br-message`
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `refactor(ui): configurações no padrão do DS com resumo de campi`

---

### T37: Remover de `admin_config` as ações de campus

**What**: Remover de `admin_config` as ações `salvar_campus`, `incluir_campus`, `excluir_campus`, `ativar_campus` e `desativar_campus`, sem outra refatoração da rota.
**Where**: `app/app.py`
**Depends on**: T36
**Reuses**: Restante de `admin_config`, intocado
**Requirement**: DS-79

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `POST /admin/config` com `acao=salvar_campus`, `incluir_campus`, `excluir_campus`, `ativar_campus` ou `desativar_campus` não altera nenhum campus no banco temporário
- [ ] Ações restantes seguem funcionando: `salvar_qtd_perfis` grava o valor e `importar_perfis` importa uma linha válida
- [ ] Testes em `tests/test_admin_paginas.py`; gate full passa (suíte existente de fatores e e-mail sem alteração)

**Tests**: integration
**Gate**: full
**Commit**: `refactor(campi): remove ações de campus de /admin/config`

---

### T38: Remover o shell antigo

**What**: Apagar `header.py`, `footer.py` e `navigation.py` de `app/components/`, mais `app/assets/nav-toggle.js` e `app/templates/_admin_nav.html`, que o shell novo substituiu.
**Where**: `app/components/`
**Depends on**: T36, T16
**Reuses**: Nada; é remoção
**Requirement**: DS-16, DS-19

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Os cinco arquivos não existem; nenhum `import` de `app.components.header`, `footer` ou `navigation` em `app/`; nenhuma referência a `_admin_nav` nem a `nav-toggle` em `app/templates/` ou `app/assets/`
- [ ] Teste estático em `tests/test_shell_assets.py` cobre as duas ausências; gate build passa

**Tests**: integration
**Gate**: build
**Commit**: `chore(ui): remove cabeçalho, rodapé e menu antigos`

---

### Phase 9: Componentes públicos

### T39: `kpi_card` em `br-card`

**What**: Trocar `dbc.Card` por `div.br-card` em `kpi_card`, mantendo a assinatura e `formatar_valor`, e criar o helper de teste que percorre a árvore de componentes Dash.
**Where**: `app/components/kpi.py`
**Depends on**: None
**Reuses**: `formatar_valor`; padrão de teste de `tests/test_parity_dominio.py` para importar `app`
**Requirement**: DS-13, DS-27

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `kpi_card("Matrículas", 1234, "0")` tem classe `br-card` e o texto "1.234"; valor `None` mostra "—"; `empty_state` substitui o valor `None` sem virar "0"
- [ ] Nenhuma classe `card`, `card-body` ou `kpi-card` do Bootstrap na árvore
- [ ] O helper de teste falha se a árvore tiver classe de componente do DS que depende de JS (`br-select`, `br-tab`, `br-modal`, `br-tooltip`, `br-accordion`, `br-dropdown`, `br-carousel`, `br-upload`)
- [ ] Novo `tests/test_componentes_publicos.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): KPI em br-card`

---

### T40: `tabela_ds`

**What**: Criar `tabela_ds(colunas, linhas, legenda)` que devolve `div.br-table` com contêiner de rolagem própria e `<table>` com `<caption>`, `th scope="col"` e células com classe opcional.
**Where**: `app/components/tabela.py`
**Depends on**: T39
**Reuses**: Helper de teste de T39
**Requirement**: DS-08, DS-14, DS-27

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] A árvore tem `br-table` > contêiner de rolagem > `table`; cabeçalhos com `scope="col"`; legenda em `<caption>`
- [ ] Valores das células chegam iguais aos passados; classe por célula (usada pela evasão) é aplicada
- [ ] Nenhuma classe `table`, `table-striped` nem `dbc.Table` do Bootstrap
- [ ] Testes em `tests/test_componentes_publicos.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): tabela_ds em br-table com rolagem contida`

---

### T41: Filtros de opção exclusiva em `br-radio`

**What**: Fazer `fic_toggle` e `axis_selector` usarem `dbc.RadioItems(className="br-radio")`, mantendo ids, opções e valores padrão.
**Where**: `app/components/filters.py`
**Depends on**: T39
**Reuses**: `EIXOS`; ids usados pelos callbacks das páginas
**Requirement**: DS-15, DS-27

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `fic_toggle("x")` tem 2 opções ("Com FIC", "Sem FIC") com padrão `com_fic`; `axis_selector("y")` tem os 6 eixos com padrão `campus`; ids preservados
- [ ] `className` contém `br-radio`; nenhuma classe `btn` do Bootstrap
- [ ] Testes em `tests/test_componentes_publicos.py`; gate quick passa. O visual de `input` + `label` irmãos é conferido na T55

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): filtros de opção exclusiva em br-radio`

---

### T42: Dropdown, botão "Limpar Filtros" e painel de filtros

**What**: Fazer `select_filter` usar `dcc.Dropdown` com classe própria estilizável pelas variáveis do DS, `clear_filters_button` usar `html.Button` com `br-button primary`, e `filter_panel` usar a grade do DS (`row` com colunas `col-12` a partir do menor tamanho).
**Where**: `app/components/filters.py`
**Depends on**: T39
**Reuses**: `TODOS`; ids de callback existentes
**Requirement**: DS-06, DS-09, DS-15, DS-27, DS-43

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `clear_filters_button("id")` tem `id="id"`, `n_clicks` e classes `br-button primary`, sem `dbc.Button`
- [ ] `select_filter` mantém `value=TODOS`, `clearable=False` e a opção "Todos"; nenhum `br-select`
- [ ] `filter_panel` devolve `div.row` com cada campo em coluna que começa em `col-12`
- [ ] Testes em `tests/test_componentes_publicos.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): dropdown, botão e painel de filtros no padrão do DS`

---

### T43: Aviso "sem correção PNP" em `br-message`

**What**: Fazer `make_aviso_sem_pnp` devolver `div.br-message warning` com o mesmo texto, mantendo `None` quando `CORRECAO_PNP_ATIVA` for verdadeira.
**Where**: `app/components/aviso_sem_pnp.py`
**Depends on**: T39
**Reuses**: `_MENSAGEM` e `CORRECAO_PNP_ATIVA`
**Requirement**: DS-17

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Com `CORRECAO_PNP_ATIVA=False`: classes `br-message warning`, `role="status"`, texto original mantido
- [ ] Com `True` (`monkeypatch`): devolve `None`
- [ ] Testes em `tests/test_componentes_publicos.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): aviso sem correção PNP em br-message`

---

### Phase 10: Páginas públicas

### T44: Página Início

**What**: Reescrever `home.py` com `<h1>`, cartões de navegação em `br-card` na grade do DS e estado vazio em `br-message info`.
**Where**: `app/pages/home.py`
**Depends on**: T39, T43
**Reuses**: `NAV_CARDS`; `data_ultimo_upload_valido`, `dataset_disponivel`
**Requirement**: DS-06, DS-13, DS-17, DS-43, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Com dados (`monkeypatch` de `dataset_disponivel`), `layout()` tem 4 `br-card` de navegação com os hrefs `/matriculas`, `/eficiencia`, `/evasao`, `/percentuais-legais` e rótulos atuais, dentro de `row` com colunas `col-12 col-md-6 col-xl-3` (ou equivalentes do DS)
- [ ] Sem dados: `br-message info` "Ainda não há dados publicados.", sem nenhum cartão de KPI
- [ ] Nenhuma classe `nav-card` nem `hero` própria; nenhum componente do DS que dependa de JS
- [ ] Novo `tests/test_paginas_publicas.py`; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): página Início com br-card e grade do DS`

---

### T45: Página Matrículas

**What**: Reescrever `matriculas.py` com `tabela_ds`, KPIs em `br-card` na grade (`row` e `col-*`), filtros novos e estado vazio em `br-message info`, sem mudar nenhum cálculo.
**Where**: `app/pages/matriculas.py`
**Depends on**: T44, T39, T40, T41, T42
**Reuses**: `kpi_card`, `tabela_ds`, `axis_selector`, `fic_toggle`, `select_filter`, `clear_filters_button`; callbacks e domínio sem alteração
**Requirement**: DS-06, DS-13, DS-14, DS-43, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Callback com um `DataFrame` pequeno (`monkeypatch` de `carregar_matriculas`) devolve `br-card` para os KPIs e `br-table` para a matriz, com os mesmos números de antes
- [ ] KPIs em colunas que começam em `col-12`; nenhuma classe `kpi-row`, `table` ou `card` do Bootstrap; sem `dbc.Table`
- [ ] Sem dados: `br-message info` "Ainda não há dados publicados."
- [ ] Testes em `tests/test_paginas_publicas.py`; gate full passa (paridade de domínio intacta)

**Tests**: unit
**Gate**: full
**Commit**: `feat(ui): página Matrículas com componentes do DS`

---

### T46: Página Eficiência Acadêmica

**What**: Reescrever `eficiencia.py` com `tabela_ds`, KPI em `br-card`, filtros novos e estado vazio em `br-message info`, sem mudar cálculo.
**Where**: `app/pages/eficiencia.py`
**Depends on**: T45
**Reuses**: Mesmos componentes de T45
**Requirement**: DS-14, DS-43, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Callback com dados simulados devolve `br-table` e `br-card` com os mesmos números de antes; sem `dbc.Table.from_dataframe`
- [ ] Sem dados: `br-message info` "Ainda não há dados publicados."
- [ ] Testes em `tests/test_paginas_publicas.py`; gate full passa

**Tests**: unit
**Gate**: full
**Commit**: `feat(ui): página Eficiência com componentes do DS`

---

### T47: Página Taxa de Evasão Anual

**What**: Reescrever `evasao.py` com `tabela_ds` e a faixa de evasão (baixa, média, alta) com rótulo textual além da cor.
**Where**: `app/pages/evasao.py`
**Depends on**: T46
**Reuses**: `tabela_ds` com classe por célula; classes `evasao-baixa`, `evasao-media`, `evasao-alta`
**Requirement**: DS-14, DS-35, DS-43, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Cada célula de taxa mostra o percentual e o texto "Baixa", "Média" ou "Alta" (ex.: "12,3% (Média)"), com a classe de cor correspondente; a taxa em si é a mesma de antes
- [ ] Tabela é `br-table`; sem `dbc.Table` nem `table-scroll-wrapper`
- [ ] Sem dados: `br-message info` "Ainda não há dados publicados."
- [ ] Testes em `tests/test_paginas_publicas.py`; gate full passa

**Tests**: unit
**Gate**: full
**Commit**: `feat(ui): página Evasão com rótulo textual de faixa`

---

### T48: Página Percentuais Legais

**What**: Reescrever `percentuais_legais.py` com medidores em `br-card` (situação "Acima da meta" ou "Abaixo da meta" em texto), aviso de filtro PROEJA em `br-message warning` e estado vazio em `br-message info`.
**Where**: `app/pages/percentuais_legais.py`
**Depends on**: T47, T43
**Reuses**: Função interna `gauge` e `cor_medidor`; `kpi_card`; componentes de filtro
**Requirement**: DS-06, DS-13, DS-17, DS-35, DS-43, DS-44

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Os 3 medidores (Técnico, Formação de Professores, PROEJA) são `br-card` com valor, "Meta: N%" e a situação em texto; sem `dbc.Card`
- [ ] Com programa filtrado, o aviso "Atenção: o filtro de Programa Associado pode distorcer o percentual PROEJA." aparece em `br-message warning`; sem filtro, não aparece
- [ ] Sem dados: `br-message info` "Ainda não há dados publicados."; medidores em colunas que começam em `col-12`
- [ ] Testes em `tests/test_paginas_publicas.py`; gate full passa

**Tests**: unit
**Gate**: full
**Commit**: `feat(ui): página Percentuais Legais com componentes do DS`

---

### Phase 11: Estilo e tema

### T49: Enxugar `style.css`

**What**: Remover de `style.css` tudo que o DS cobre (cabeçalho, menu, cartões, navegação administrativa, variáveis `--gov-*`, `@media` de 768px e 320px) e migrar as regras que sobram (faixas de evasão, medidores, estado vazio) para variáveis do DS, sem cor literal.
**Where**: `app/assets/style.css`
**Depends on**: T38, T48
**Reuses**: Variáveis semânticas de `app/static/govbr-ds/dist/core-tokens.css`
**Requirement**: DS-02, DS-29, DS-30, DS-54

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Sem cor hexadecimal, `rgb()` ou `hsl()` literal; sem `--gov-`; sem `768px` nem `320px`; todo `@media` de largura usa só 576, 992, 1280 ou 1600px (`prefers-color-scheme` permitido)
- [ ] Nenhum seletor `.app-header`, `.nav-menu`, `.admin-nav`, `.kpi-card`, `.nav-card`, `.hero`
- [ ] Novo `tests/test_style_css.py`; gate full passa
- [ ] Faixas `.evasao-*` e medidores continuam definidos, agora por `var(--...)`

**Tests**: unit
**Gate**: full
**Commit**: `refactor(ui): enxuga style.css para só o que o DS não cobre`

---

### T50: Regras de layout, toque e foco

**What**: Acrescentar a `style.css`: conteúdo limitado a `--grid-tv-maxwidth` (1520px) e centralizado a partir de 1600px, área mínima de toque de 24×24px, contorno de foco de 3px, estilo do `dcc.Dropdown` por variáveis do DS e o fallback `.ds-sem-js` do menu.
**Where**: `app/assets/style.css`
**Depends on**: T49
**Reuses**: Tokens `--grid-tv-maxwidth`, `--focus-color`; seletores do `dcc.Dropdown` do Dash 4.4.1 (conferir no DOM instalado)
**Requirement**: DS-03, DS-07, DS-08, DS-09, DS-15, DS-33

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `@media (min-width: 1600px)` limita o contêiner a `var(--grid-tv-maxwidth)` com `margin-inline: auto`
- [ ] Há regra de `min-width` e `min-height` de `24px` para controles interativos e `outline` de largura ≥ 3px em `:focus-visible`, ambos por `var()` onde o token existir
- [ ] Há regras `.ds-sem-js` que mantêm os links do menu visíveis
- [ ] `tests/test_style_css.py` continua verde (sem hex, sem `--gov-*`, `@media` só nos pontos do DS) e cobre os itens novos; gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): regras de contêiner, toque e foco sobre o DS`

---

### T51: `tema.js` (botão de tema)

**What**: Criar `tema.js` com o clique do botão de tema (alterna `data-tema` em `<html>`, atualiza `aria-pressed` e o rótulo, salva em `localStorage` `calcsistec-tema`) e o acompanhamento de `prefers-color-scheme` sem escolha salva; incluir em `_scripts.html`.
**Where**: `app/static/js/tema.js`
**Depends on**: T6, T10, T5
**Reuses**: Botão de tema de `_header.html`; script inline de `_head.html`
**Requirement**: DS-45, DS-46, DS-47, DS-48, DS-49, DS-51

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Funções puras exportadas rodam em `node`: alternar `claro` ↔ `escuro`; rótulo "Usar tema escuro" quando claro e "Usar tema claro" quando escuro; gravar em `localStorage` que lança exceção não propaga erro e devolve `false`
- [ ] Gravar usa a chave `calcsistec-tema` com `claro` ou `escuro`
- [ ] `resolverTema` de `tema.js` e o script inline de `_head.html` dão o mesmo resultado nos mesmos 4 casos da tabela-verdade de T5
- [ ] `_scripts.html` carrega `tema.js` uma vez, depois de `core.min.js`
- [ ] Testes em `tests/test_js_tema.py` (com `skipif` sem `node`); gate quick passa

**Tests**: unit
**Gate**: quick
**Commit**: `feat(ui): botão de tema claro e escuro com persistência`

---

### T52: Tema escuro em `style.css`

**What**: Acrescentar `:root[data-tema="escuro"]` remapeando as variáveis semânticas do DS para as variantes `-dark`, mais regras (só com variáveis do DS) para header, menu, footer e message, que não têm `.dark-mode` no DS 3.7.0, e o logotipo sobre superfície clara. Começa por conferir os tokens no navegador a 1280px em `/` e `/admin/login` e listar as lacunas.
**Where**: `app/assets/style.css`
**Depends on**: T50, T51
**Reuses**: Pares `-light` e `-dark` de `core-tokens.css:936-1000`; Chrome MCP para a conferência inicial
**Requirement**: DS-33, DS-34, DS-35, DS-53, DS-54, DS-55

**Tools**:

- MCP: `claude-in-chrome` (conferência visual das lacunas)
- Skill: NONE

**Done when**:

- [ ] O bloco escuro existe, todo valor de cor dentro dele é `var(--...)`, e há regras para `br-header`, `br-menu`, `br-footer`, `br-message`, `br-card`, `br-table` e `br-input`
- [ ] O invólucro do logotipo mantém superfície clara nos dois temas
- [ ] Novo `tests/test_contraste_tema.py` calcula o contraste dos pares `--color`/`--background`, `--interactive`/`--background` e `--focus-color`/`--background` resolvidos em `core-tokens.css`, nos dois temas: texto ≥ 4,5:1 e foco ≥ 3:1
- [ ] As lacunas achadas na conferência visual estão listadas no corpo do commit e cobertas por regra; `tests/test_style_css.py` continua verde; gate full passa

**Tests**: unit
**Gate**: full
**Commit**: `feat(ui): tema escuro por tokens do DS`

---

### Phase 12: Fontes e ícones (requer autorização)

### T53: Vendorizar o Font Awesome 5 Free

**What**: Com autorização de Jaline para baixar da rede, trazer `@fortawesome/fontawesome-free` 5.x (CSS e webfonts `fa-solid-900`, `fa-regular-400`, `fa-brands-400`, mais a licença) para `app/static/vendor/fontawesome/` e linkar o CSS em `_head.html`.
**Where**: `app/static/vendor/fontawesome/`
**Depends on**: T5
**Reuses**: Família "Font Awesome 5 Free" exigida em `core.css:29845`
**Requirement**: DS-24

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Jaline autorizou o download antes de rodar; versão baixada e origem anotadas no corpo do commit
- [ ] Arquivos de licença do Font Awesome Free ficam junto dos fontes
- [ ] Teste em `tests/test_shell_assets.py`: todo `href` e `src` local do HTML de `/admin/login` e do shell do Dash resolve para 200, e não há URL externo
- [ ] Gate full passa

**Tests**: integration
**Gate**: full
**Commit**: `feat(assets): Font Awesome 5 Free local para os ícones do DS`

---

### T54: Rawline (condicional à licença)

**What**: Se Jaline confirmar que a licença permite redistribuir a Rawline, trazer os arquivos e o `@font-face` para `app/static/vendor/rawline/` e linkar em `_head.html`; se não, registrar em `STATE.md` (AD-004) que a fonte cai em Raleway e depois em sans-serif, e encerrar sem arquivos.
**Where**: `app/static/vendor/rawline/`
**Depends on**: T5
**Reuses**: `--font-family-base` de `core-tokens.css:970`
**Requirement**: DS-24

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Ramo com licença confirmada: arquivos e `@font-face` locais, sem URL externo, e o teste de assets de T53 continua verde
- [ ] Ramo sem licença: `STATE.md` ganha AD-004 com a decisão, a razão e o trade-off, e nenhuma referência a fonte inexistente fica no HTML
- [ ] Gate build passa

**Tests**: none
**Gate**: build
**Commit**: `feat(assets): fonte Rawline local (ou registra a decisão de não vendorizar)`

---

### Phase 13: Verificação e entrega

### T55: Verificação visual e de teclado

**What**: Rodar o app com dados publicados (Sistec simulado) e conferir no Chrome, nas 11 páginas, em 320, 576, 992, 1280 e 1600px: rolagem horizontal, menu, coluna única, contêiner de 1520px, tema escuro, foco por teclado, menu por Enter, Espaço e Esc, e o modal de confirmação; registrar o resultado.
**Where**: `.specs/features/govbr-design-system/verificacao-visual.md`
**Depends on**: T52, T53, T54, T48, T35
**Reuses**: `scripts/testar.ps1 -Simulado` (TESTAR.md); `javascript_tool` para medir `scrollWidth`
**Requirement**: DS-03, DS-04, DS-05, DS-06, DS-07, DS-09, DS-37, DS-38, DS-43, DS-44, DS-48, DS-53

**Tools**:

- MCP: `claude-in-chrome`
- Skill: NONE

**Done when**:

- [ ] Tabela página × largura com PASS ou FAIL e a medida de `scrollWidth ≤ innerWidth` para as 11 páginas nas 5 larguras
- [ ] Registrado o resultado do menu persistente a partir de 992px; se falhar, decisão de cair para menu sobreposto em todas as larguras (ajuste de DS-04 e DS-05) e o ajuste feito
- [ ] Registrado: Enter e Espaço abrem o menu e levam o foco ao primeiro item, Esc fecha e devolve o foco ao botão (DS-37, DS-38); se o JS do DS não cumprir, a lacuna vira task nova neste arquivo
- [ ] Registrado: modal de exclusão prende o foco, fecha com Esc, devolve o foco e o botão "Cancelar" não exclui (DS-60, DS-75); botão de tema troca sem recarregar; `br-radio` e `dcc.Dropdown` legíveis nos dois temas
- [ ] `python scripts/verificar_prontidao_cutover.py` rodado e o estado (NO-GO por ambiente) anotado; toda lacuna vira task nova ou correção com teste, antes de seguir

**Tests**: none
**Gate**: build
**Commit**: `docs(ui): registra a verificação visual do design responsivo`

---

### T56: README e TESTAR

**What**: Atualizar `README.md` (estrutura com `app/static/`, DS fora de `app/assets/`, tema, shell único) e `TESTAR.md` (gestão de campi em `/admin/campi`, botão de tema, testes novos) conforme a constituição exige para mudança de fluxo de uso.
**Where**: `README.md`
**Depends on**: T55
**Reuses**: Seção "Antes da primeira atualização" de `TESTAR.md`; estrutura do README (`README.md:11`)
**Requirement**: - (Constituição, Fluxo de Desenvolvimento)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `README.md` descreve `app/static/` e `app/templates/shell/` e não cita mais `app/assets/govbr-ds/`
- [ ] `TESTAR.md` troca "Configurações → Campi do Sistec" por `/admin/campi` onde ensina a editar identificadores
- [ ] Gate build passa

**Tests**: none
**Gate**: build
**Commit**: `docs: atualiza README e TESTAR para o design gov.br`

---

### T57: CUTOVER e teste em celular real (passo humano)

**What**: Atualizar `CUTOVER.md`: roteiro do teste em celular real (5 páginas públicas e `/admin/atualizar`, 320px a 430px, mais uma tela de 1280px ou mais), registro da pendência de CSRF nos POSTs administrativos, e marcar o item de design só quando Jaline informar o resultado.
**Where**: `CUTOVER.md`
**Depends on**: T55
**Reuses**: Item "Design gov.br validado em pelo menos um dispositivo móvel real" de `CUTOVER.md:19`
**Requirement**: DS-42

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `CUTOVER.md` traz o roteiro e a pendência de CSRF (`app/config.py:18`, só `SameSite=Lax` protege)
- [ ] **Humano:** Jaline testou e informou dispositivo, largura e data; o item de design fica marcado com esses três dados. Sem isso o requisito DS-42 fica bloqueado, e o Verifier o registra como pendente de passo humano, não como falha de código
- [ ] Gate build passa

**Tests**: none
**Gate**: build
**Commit**: `docs(cutover): roteiro de validação em celular real e pendência de CSRF`

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
Phase 7 → Phase 8 → Phase 9 → Phase 10 → Phase 11 → Phase 12 → Phase 13
```

Execução estritamente sequencial: um agente (ou um worker de lote) faz uma task por vez, na ordem.

---

## Validação pré-aprovação

### Check 1: granularidade

Cada task entrega um arquivo ou um conceito coeso. Três tasks mexem em mais de um arquivo por necessidade, e cada uma diz por quê: T2 (mover o DS exige o blueprint e o link novo no mesmo commit, senão o admin fica sem CSS), T22 (`confirmar.js` mais a linha em `_scripts.html`) e T38 (remoção de cinco arquivos mortos, sem lógica nova).

### Check 2: diagrama × `Depends on`

Rodado por `validate_tasks.py` (ver resultado abaixo). Dependências entre fases ficam só no campo `Depends on` e todas apontam para trás.

### Check 3: co-localização de testes

| Task | Camada criada ou alterada | Matriz exige | Task diz | Status |
| ---- | ------------------------- | ------------ | -------- | ------ |
| T4, T13, T15 | Shell Python | unit + integration | unit / integration | ✅ OK |
| T5 a T12, T28 | Parciais Jinja | integration | integration | ✅ OK |
| T14, T17 a T21, T36 | Templates admin | integration | integration | ✅ OK |
| T16, T37 | `app/app.py` (rotas) | integration | integration | ✅ OK |
| T24 a T27 | Dados e função pura | unit | unit | ✅ OK |
| T29 a T35 | Rotas do CRUD | e2e | e2e | ✅ OK |
| T39 a T48 | Componentes e páginas Dash | unit | unit | ✅ OK |
| T49, T50, T52 | CSS | static | unit (estático) | ✅ OK |
| T22, T23, T51 | JavaScript | unit via node | unit | ✅ OK |
| T1, T54, T55, T56, T57 | Config, docs, assets, manual | none | none | ✅ OK (matriz diz none; T55 é manual) |
| T2, T3, T38, T53 | Assets, remoção | integration (estático) | integration | ✅ OK |

Nenhum teste foi adiado para outra task. T33 e T22 cobrem o servidor e a função pura; o comportamento de DOM do modal fica na T55, dito nas duas tasks.

---

## Cobertura dos requisitos

| Requisito | Tasks |
| --------- | ----- |
| DS-01 | T5, T14 |
| DS-02 | T49 |
| DS-03 | T14, T50, T55 |
| DS-04, DS-05 | T6, T7, T55 |
| DS-06 | T42, T44, T45, T48, T55 |
| DS-07 | T50, T55 |
| DS-08 | T20, T21, T40, T50 |
| DS-09 | T42, T50, T55 |
| DS-10 | T6, T15 |
| DS-11, DS-12 | T4, T7 |
| DS-13 | T39, T44, T45, T48 |
| DS-14 | T40, T45, T46, T47 |
| DS-15 | T41, T42, T50 |
| DS-16 | T9, T15, T38 |
| DS-17 | T43, T44, T48 |
| DS-18 | T16 |
| DS-19 | T4, T6, T9, T13, T14, T18, T38 |
| DS-20 | T12, T17, T19, T20, T21, T36 |
| DS-21 | T12, T17, T19, T36 |
| DS-22 | T12, T21, T29, T36 |
| DS-23 | T17, T18, T19, T21, T36 |
| DS-24 | T2, T3, T53, T54 |
| DS-25, DS-26 | T5, T10, T14, T15, T16 |
| DS-27 | T10, T15, T39, T40, T41, T42 |
| DS-28 | T2 |
| DS-29, DS-30 | T49 |
| DS-31 | T14, T15 |
| DS-32 | T6, T14, T15 |
| DS-33 | T50, T52 |
| DS-34 | T52 |
| DS-35 | T47, T48, T52 |
| DS-36 | T6 |
| DS-37, DS-38 | T7, T55 |
| DS-39 | T4, T6, T9, T13 |
| DS-40 | T6 |
| DS-41 | T4, T9 |
| DS-42 | T57 |
| DS-43, DS-44 | T14, T15, T42, T44 a T48, T55 |
| DS-45, DS-46 | T5, T51 |
| DS-47 | T6, T51 |
| DS-48 | T51, T55 |
| DS-49 | T51 |
| DS-50 | T5 |
| DS-51 | T5, T51 |
| DS-52 | T5 |
| DS-53 | T52, T55 |
| DS-54 | T49, T52 |
| DS-55 | T6, T52 |
| DS-56 | T4, T8, T20, T29 |
| DS-57 | T17 |
| DS-58 | T11, T22 |
| DS-59 | T22, T23, T36 |
| DS-60 | T11, T22 |
| DS-61 | T4, T8, T16 |
| DS-62 | T29, T36 |
| DS-63 | T28, T29 |
| DS-64 | T29 |
| DS-65 | T28, T29 |
| DS-66 | T25, T30 |
| DS-67, DS-68, DS-69 | T30 |
| DS-70 | T26, T30 |
| DS-71 | T24, T30 |
| DS-72 | T26, T30 |
| DS-73 | T11, T33 |
| DS-74, DS-75 | T33 |
| DS-76 | T32 |
| DS-77, DS-78 | T31 |
| DS-79 | T29, T30, T36, T37 |
| DS-80 | T34 |
| DS-81, DS-82, DS-83 | T27, T34 |
| DS-84, DS-85 | T35 |

**Cobertura:** 85 de 85 requisitos mapeados a ao menos uma task.
