**Veredito: PASS**

# Validation: govbr-design-system - PASS

**Data**: 2026-09-20
**Spec**: `.specs/features/govbr-design-system/spec.md` (DS-01 a DS-85)
**Intervalo de commits**: `42c5f43^..HEAD`, HEAD = `07439805ea1cc99e20b29267d83f66facebb9fdb` (branch `migracao-dash-gov-br`, iteração 5 do laço corrigir e reverificar; inclui `fix(ui): menu vira barra lateral fixa em telas largas`, além da iteração 4 com o Font Awesome)
**Verificador**: sub-agente independente (autor diferente do verificador); verificação do delta do commit `0743980` (DS-05 vira barra lateral fixa, AD-005) sobre o relatório da iteração 4, que seguia válido.

O código e os testes do working tree real não foram tocados. Único arquivo criado: este. O sensor rodou em `git worktree` descartável, já removido.

---

## Resumo

| Item | Resultado |
| ---- | --------- |
| Gate | `python -m compileall -q app` exit 0; `python -m pytest -q` = **548 passed, 0 failed, 0 skipped**, 2 warnings (FutureWarning de pandas em `app/data/fatores.py:199`, fora da feature) |
| ACs verificáveis | 84 de 85 com evidência `arquivo:linha` cujo valor asserido bate com a spec (DS-24 agora completo: DS local + Rawline + Font Awesome); PENDENTE só por passo humano: DS-42 |
| Sensor | 32 mutações no total, **32 mortas, 0 sobreviveram** (29 das iterações anteriores todas mortas; no delta DS-05, as 3 novas mortas — ver seção "Sensor do delta DS-05") |
| Defeito de produto | Nenhum achado. DS-05 (barra lateral fixa a partir de 992px, sem hambúrguer) está corrigido e coberto |
| Isolamento do sensor | `git status --porcelain` do repositório real idêntico antes e depois: só `.agents/`, `.cursor/`, `.windsurf/`, `.claude/skills/tlc-spec-driven/` (não rastreados, fora da feature) |
| `validate_state.py govbr-design-system` | exit 0 ("0 error(s)") |

### Integridade dos testes

- Linha de base antes da feature: 181 testes (`tasks.md`, matriz de cobertura). Agora: 548. Delta **+367** (o commit `0743980` trocou 2 testes por 2 — `tests/test_js_fiacao.py` e `tests/test_style_css.py` — sem mudar a contagem).
- `git diff 42c5f43^..HEAD -- tests`: 16 arquivos, **3157 inserções, 0 remoções** (os 16 são novos frente à linha de base). Nenhum teste foi removido nem pulado.
- Edições internas ao intervalo (commits `0b32445` e `0743980`), todas legítimas frente à spec:
  1. `tests/test_shell.py:187` e `tests/test_shell_parciais.py:211`: só renomeados (`core_min` para "o script do DS"); as asserções passam a exigir `core-init.min.js` uma vez, coerente com AD-004 e com DS-26 reescrito.
  2. `tests/test_style_css.py:101` e `tests/test_js_fiacao.py:71` (DS-05): no commit `0743980` (AD-005), o teste do menu a 992px deixou de exigir "botão presente que recolhe" e passou a exigir a barra lateral fixa — `test_a_partir_de_992px_o_menu_vira_barra_lateral_fixa_sem_botao` (`.br-menu{position:fixed;width:var(--menu-largura)}`, `.header-menu-trigger{display:none}`, `body{padding-left:var(--menu-largura)}`) e `test_o_menu_nao_tem_recolhimento_persistente_em_nenhuma_largura` (clique e teclas não marcam `menu-recolhido`).
  3. `tests/test_shell_parciais.py:216-220`: a lista proibida trocou `"core-init"` por `"core-init.js"` (o script minificado agora é o correto). Continua proibindo `dist/components/`, `core-base`, a versão não minificada `core-init.js` e `core.js` (DS-28).

---

## Tarefas

T1 a T56: concluídas (código + testes no gate). **T53** (Font Awesome 5 Free): agora concluída — `@fortawesome/fontawesome-free` 5.15.4 vendorizado em `app/static/vendor/fontawesome/` e linkado em `_head.html:22`. **T57**: roteiro e pendência de CSRF escritos em `CUTOVER.md:34-49`; o item de design fica desmarcado até Jaline informar dispositivo, largura e data (humano, ver PENDENTES). **Rework DS-05** (commit `0743980`, AD-005): concluído — o menu a 992px+ virou barra lateral fixa, `menu.js` perdeu o modo persistente/recolher e os dois testes trocados no delta passam no gate.

---

## Acceptance Criteria ancorados na spec

Siglas: `S`=`tests/test_shell.py`, `P`=`tests/test_shell_parciais.py`, `A`=`tests/test_shell_assets.py`, `C`=`tests/test_style_css.py`, `K`=`tests/test_contraste_tema.py`, `JT`=`tests/test_js_tema.py`, `JM`=`tests/test_js_menu.py`, `JC`=`tests/test_js_confirmar.py`, `JF`=`tests/test_js_fiacao.py`, `AP`=`tests/test_admin_paginas.py`, `AC`=`tests/test_admin_campi.py`, `CA`=`tests/test_campi.py`, `CP`=`tests/test_componentes_publicos.py`, `PP`=`tests/test_paginas_publicas.py`, `VV`=`verificacao-visual.md`. "Manual" = verificado manualmente pelo autor no Chrome e registrado em `VV` (eu não reabri o navegador).

| AC | Resultado que a spec define | `arquivo:linha` + asserção | Status |
| -- | --------------------------- | -------------------------- | ------ |
| DS-01 | `<meta name="viewport" content="width=device-width, initial-scale=1">` em toda página | `P:30` `'<meta name="viewport" content="width=device-width, initial-scale=1">' in html`; o parcial é usado por `_base.html` (admin) e pelo Dash (`S:171`) | PASS |
| DS-02 | `@media` só em 576/992/1280/1600 | `C:27-33` `larguras <= PONTOS_DO_DS`; `C:22-24` sem `768px` nem `320px` | PASS |
| DS-03 | sem rolagem horizontal de 320 a 1920px | Manual: `VV:13-32` (14 telas x 5 larguras, `scrollWidth <= clientWidth`); complementos automáticos `C:138-140` (`overflow-wrap: anywhere`, `pre` com `overflow-x: auto`) e `C:143-147` (`.br-button` quebra rótulo) | PASS (manual) |
| DS-04 | < 992px: menu sobreposto, fechado por padrão, `aria-expanded` no botão | `JF:94` largura 576 `== {"inicial": "false", "recolhido": False}`; `JF:108` `aria-expanded` `"true"` ao abrir e `"false"` ao fechar; `P:80` `aria-expanded="false"` e `aria-controls="main-navigation"`; sobreposto no navegador: `VV:39` | PASS |
| DS-05 | >= 992px: menu persistente, aberto por padrão, como **barra lateral fixa à esquerda, sem botão hambúrguer** | `C:96-98` `test_menu_fica_persistente_e_aberto_a_partir_de_992px` (`.br-menu .menu-container, .br-menu.active .menu-container{display:block}` em `@media (min-width: 992px)`); `C:101-106` `test_a_partir_de_992px_o_menu_vira_barra_lateral_fixa_sem_botao` (`.br-menu{position:fixed;width:var(--menu-largura)}`, `.header-menu-trigger{display:none}`, `body{padding-left:var(--menu-largura)}`); `JF:71-84` `test_o_menu_nao_tem_recolhimento_persistente_em_nenhuma_largura` (a 1280px, clique/Enter/Espaço não marcam `menu-recolhido`); manual `VV:40` (Chrome a 992/1600px, AD-005) | PASS |
| DS-06 | < 576px: KPIs, medidores e filtros em coluna única | `PP:120` `"col-12" in coluna.className`, `PP:186`, `PP:304`, `PP:35` (`{"col-12","col-md-6","col-xl-3"}`), `CP:166` (filtros: cada coluna com `col-12`) | PASS |
| DS-07 | >= 1600px: conteúdo limitado a 1520px, centralizado | `C:77-80` `max-width: var(--grid-tv-maxwidth)` (= 1520px em `core-tokens.css:1201`) e `margin-inline: auto` no `@media (min-width: 1600px)`; manual `VV:37` (1520px medido nas 14 telas) | PASS |
| DS-08 | tabela larga rola só dentro do contêiner | `AC:166` `<div class="br-table"><div class="responsive"><table`; `CP:63-67` `raiz.className == "br-table"`, `children.className == "responsive"`; `AP:159` (histórico) | PASS |
| DS-09 | controle interativo com área mínima 24x24px | `C:83-87` `--alvo-toque-minimo: 24px`, `min-width` e `min-height: var(--alvo-toque-minimo)` na regra `button, input, select` | PASS |
| DS-10 | `br-header` com logotipo, título "Painel de Acompanhamento Sistec" e nome da instituição | `P:68-71` `"Painel de Acompanhamento Sistec" in html` e `"Instituto Teste" in html`; `P:57-61` logotipo com `alt`; `S:172` `'class="br-header"'` nas páginas do Dash | PASS |
| DS-11 | `br-menu` com Início, Matrículas, Eficiência Acadêmica, Taxa de Evasão Anual, Percentuais Legais, nesta ordem | `S:28-30` lista `PUBLICAS` igual (rótulo, href); `P:107-115` os 5 rótulos na ordem | PASS |
| DS-12 | item da página com `aria-current="page"` e estado ativo | `P:118-123` `com_aria == ["Matrículas"]` e `com_classe == ["Matrículas"]`; `S:33-36` só o item da página ativo; `S:174-175` e `S:224-225` no HTML do Dash | PASS |
| DS-13 | KPIs, medidores e cartões da capa em `br-card` | `CP:12-14` `"br-card" in classes(cartao)`; `PP:25-32` 4 cartões de navegação (href e texto); `PP:108-117` KPIs com os números; `PP:182-185`; `PP:280-301` medidor `f"{rotulo} {valor:.1%} {situacao} Meta: {meta:.0%}"` | PASS |
| DS-14 | tabelas em `br-table` | `CP:63-67`; `PP:127-131` (`matriz.className == "br-table"`, células `[["101","2"],["102","1"]]`), `PP:189-195`, `PP:256-258` | PASS |
| DS-15 | `br-radio` nos filtros exclusivos, `dcc.Dropdown` com variáveis do DS, "Limpar Filtros" em `br-button` | `CP:127-132` `"br-radio" in radio.className.split()`; `CP:147-163` Dropdown com `clearable is False`, `filtro-dropdown`; `C:114-118` `var(--background)`, `var(--color)`, `var(--border-color)`; `CP:138-144` `{"br-button","primary"}`, `n_clicks == 0` | PASS |
| DS-16 | `br-footer` com nome, site, e-mail e "Área administrativa" | `P:180-185` `href="https://it.edu.br"`, `mailto:pi@it.edu.br`, `href="/admin/login"` "Área administrativa"; `S:173` `'class="br-footer"'` | PASS |
| DS-17 | aviso "sem correção PNP" e aviso PROEJA em `br-message warning` | `CP:184-190` `{"br-message","warning"}`, `aviso.role == "status"`, `TEXTO_DO_AVISO in textos(aviso)`; `PP:314-317` `{"br-message","warning"}` com o texto do PROEJA | PASS |
| DS-18 | sem `dbc.themes.BOOTSTRAP` nas páginas públicas | `S:197-198` `"bootstrap" not in ... .lower()`; `S:223` `not re.search(r"<link[^>]*bootstrap", html)` | PASS |
| DS-19 | admin com os mesmos `br-header` e `br-footer` | `AP:29-30` (login), `AP:94-95` (recuperar); todas as páginas admin estendem `_base.html` (`grep -L 'extends "_base.html"'` só devolve a própria base) | PASS |
| DS-20 | campos, botões e tabelas admin em `br-input`/`br-password`/`br-select`, `br-button`, `br-table` | `P:294-298` rótulo acima do `<input required>`; `AP:105-113` `len(br-input) == len(ids)`; `AP:262-267`; `AP:159` `br-table` | PASS |
| DS-21 | campo inválido em `danger` com mensagem ligada por `aria-describedby` | `P:280-285` `class="br-input danger"` e o `id` citado em `aria-describedby` contém o texto; `AP:73-79`; `AP:123-129` | PASS |
| DS-22 | fim de ação: `br-message` `success`/`danger` com `role="alert"` | `P:301-305` `success` e `danger` => `alert`; `AP:82-86`; `AP:270-284`; `AC:183` `class="br-message success"[^>]*role="alert"` | PASS |
| DS-23 | < 576px: formulários em largura total, botões empilhados | `P:343-346` container de `botoes_formulario` contém `{"d-flex","flex-column","flex-sm-row","justify-content-sm-end"}` (as duas classes existem no `core.css:1761`, `@media (min-width: 576px)`); `AC:520-525` cada coluna dos 4 campos tem `{"col-12","col-md-6"}`; `AP:206-211` `flex-column` e `flex-sm-row` em `atualizar-acoes`; sensor M15, M16, M18 | PASS |
| DS-24 | DS 3.7.0 servido localmente, sem CDN | `A:20-24` `assets/govbr-ds` inexiste e `static/govbr-ds/dist/core.min.css` existe; `A:26-32` `resposta.data == arquivo`; `A:97-106` todo recurso do HTML de `/admin/login` e `/` resolve 200 e não começa com `http`; `P:35-38` sem URL externa; `A:109-117` 7 fontes Rawline resolvem; `A:120-129` os webfonts do Font Awesome (`fa-solid-900`/`fa-regular-400`/`fa-brands-400`) resolvem 200; `A:132-138` arquivos vendorizados presentes (`css/all.min.css`, `LICENSE.txt`, 15 webfonts); `_head.html:22` linka `/ds/vendor/fontawesome/css/all.min.css` antes de `core.min.css` | PASS |
| DS-25 | `core.min.css` exatamente uma vez | `P:31` `len(...core\.min\.css...) == 1`; `S:192`, `S:221`; `AP:27` | PASS |
| DS-26 | `core-init.min.js` exatamente uma vez | `P:213` `len(re.findall(...core-init.min.js...)) == 1`; `S:193`, `S:222`; `AP:28`; `A:120-129` (o `core-init.min.js` tem uma chamada `.initInstanceAll()` a mais que `core.min.js`, e `_scripts.html` cita `core-init.min.js`) | PASS |
| DS-27 | Dash só com componentes do DS que funcionam sem JS | `tests/arvore_dash.py:59-60` (`classes(raiz) & CLASSES_DO_DS_QUE_PRECISAM_DE_JS` vazio), usado em `CP:39-40`, `CP:99-100`, `CP:132`, `CP:161`, `PP:62`, `PP:140`, `PP:202`, `PP:261`, `PP:311`; o auxiliar é validado em `CP:43-47` | PASS |
| DS-28 | sem `dist/components/` e sem bundle não minificado | `P:216-220` `"dist/components/"`, `"core-base"`, `"core-init.js"` ausentes e `not re.search(r'src="[^"]*core\.js"')`; `A:20` | PASS |
| DS-29 | `style.css` sem hex e sem `@media` fora dos pontos do DS | `C:13-15` sem `#hex`, `rgb(`, `hsl(`; `C:27-33` só pontos do DS e `prefers-color-scheme` | PASS |
| DS-30 | sem `--gov-*` | `C:18-19` `"--gov-" not in CSS` | PASS |
| DS-31 | `lang="pt-BR"` em todas as páginas | `AP:26` `'<html lang="pt-BR"' in html`; `S:171` (Dash) | PASS |
| DS-32 | primeiro link "Ir para o conteúdo principal" leva a `#main-content` | `P:50-54` primeiro `<a>` do cabeçalho tem `href="#main-content"` e texto exato; alvo: `S:184` `<main id="main-content"...>` (o `_base.html` é comum; mutação M22 foi morta) | PASS |
| DS-33 | foco >= 3px em `--focus-color`, contraste >= 3:1 nos dois temas | `C:90-93` `outline: 3px solid var(--focus-color)`, `largura >= 3`; `K:50-53` `contraste(--focus-color, --background) >= 3` para claro e escuro | PASS |
| DS-34 | texto >= 4,5:1 nos dois temas | `K:43-47` `--color` e `--interactive` sobre `--background` >= 4.5; `K:67-70` `--color` sobre `--background-alternative` >= 4.5 (cartões e mensagens). Cobre os pares de token, não cada componente; legibilidade nas telas: manual `VV:66` | PASS (spec-precision: ver lacuna 2) |
| DS-35 | situação dos medidores e faixa de evasão com rótulo textual | `PP:247-253` `"Alta": ("50,0% (Alta)", "evasao-alta")`, `"Media": ("20,0% (Média)", ...)`, `"Baixa": ("0,0% (Baixa)", ...)`; `PP:301` "Acima da meta"/"Abaixo da meta" no texto do cartão | PASS |
| DS-36 | `alt` em toda imagem informativa, inclusive o logotipo | `P:57-61` `"Instituto Teste" in com_nome` e `sem_nome.strip() != ""` | PASS |
| DS-37 | Enter/Espaço no botão do menu abre e move o foco ao primeiro item | Comportamento do `core-init.min.js` do DS (`core.js:8656-8673`: `keydown` com `Enter`/`Space` chama `_openMenu` e `_focusOnFirstVisibleItem`); `A:120-129` garante que o script que instancia o menu é o carregado; manual `VV:46-52` (com `KeyboardEvent`, ver lacuna 3) | PASS (manual) |
| DS-38 | Esc com o menu aberto fecha e devolve o foco ao botão | `JF:214-225` ao remover `active` com o foco em um item: `foco: doc.activeElement === botao` `True`, `aposFechar == "false"`; `JF:228-238` o foco não é roubado se o usuário foi a outro controle; `JM:29-34` tabela-verdade de `deveDevolverFoco`; sensor M04; Esc do DS: manual `VV:48-51` | PASS |
| DS-39 | nome, sigla, site, e-mail e logotipo vêm da configuração | `S:95-100` `contexto["instituicao"]["nome"] == "Instituto Teste"`, `sigla`, `site`, `contato_email == "pi@it.edu.br"` (valores do `dados_instituicao` simulado); `P:180-185` o rodapé os mostra; `P:87-93` logotipo da rota `/branding/logo` | PASS |
| DS-40 | sem logotipo enviado: `padrao-generico.svg` | `P:87-93` `resposta.data == Path(DEFAULT_LOGO_PATH).read_bytes()` e `mimetype == "image/svg+xml"` | PASS |
| DS-41 | contato em branco omitido do rodapé, sem rótulo nem espaço vazio | `P:192-198` `"mailto:" not in html`, `len(<a>) == 1`, sem `<span/li/a/div/p>` vazio; `P:201-204`; `S:103-113` contato e site chegam vazios | PASS |
| DS-42 | `CUTOVER.md` com resultado em celular real e tela >= 1280px | Roteiro em `CUTOVER.md:34-49`; item de design `CUTOVER.md:19` desmarcado, "Resultado: dispositivo ______" em `CUTOVER.md:49` | PENDENTE (passo humano de Jaline) |
| DS-43 | grade de 4/8/12 colunas por faixa | `PP:35-41` `{"col-12","col-md-6","col-xl-3"}`; `AC:520-525`; o número de colunas é propriedade do `core.min.css` (verificado só por classes e visualmente: `VV:13-32`) | PASS (spec-precision: ver lacuna 2) |
| DS-44 | posiciona com `container-fluid`/`row`/`col-*`, sem grid próprio | `C:150-151` `not re.search(r"(?m)^\s*\.(?:row\|col...)\s*[,{]")`; `AP:31` `"container-fluid" in html`; `PP:36-38` `row` com colunas | PASS |
| DS-45 | sem escolha e sistema escuro => escuro | `JT:94-95` `tema_resultante(salvo=None, sistema="escuro") == "escuro"` (o script inline real do `_head.html`, executado em `node`) | PASS |
| DS-46 | sem escolha e sistema claro ou sem preferência => claro | `JT:98-99` `== "claro"`; `JT:102-103` sem `matchMedia` `== "claro"` | PASS |
| DS-47 | botão de tema no cabeçalho com rótulo e `aria-pressed` | `P:74-77` `aria-pressed="false"` e `"Usar tema escuro" in botao.group(1)`; `JT:135-136` `rotuloDoBotao`: `["Usar tema escuro","Usar tema claro"]` | PASS |
| DS-48 | acionar o botão aplica o tema sem recarregar | `JF:136-151` `botao.disparar("click")` muda `data-tema` para `escuro`, `aria-pressed` `"true"`, rótulo "Usar tema claro", e volta; sensores M07 e M08; manual `VV:65` (marca em `window` sobreviveu) | PASS |
| DS-49 | grava em `localStorage["calcsistec-tema"]` | `JF:150` `"salvo": "escuro"` após o clique e `JF:151` `"claro"` depois; `JT:139-144` `gravarTema("escuro", storage) == [True, {"calcsistec-tema": "escuro"}]` | PASS |
| DS-50 | escolha salva vence a preferência do sistema | `JT:106-107` `salvo="claro", sistema="escuro" == "claro"`; `JT:110-111` `"escuro"`; `JF:158-166` com `salvo="claro"`, mudar o sistema para escuro mantém `"claro"` | PASS |
| DS-51 | `localStorage` bloqueado: mantém a página e volta à preferência sem erro | `JT:114-116` com `getItem` lançando: `== "escuro"` e `== "claro"`; `JT:147-149` `gravarTema` com `setItem` lançando `is False` | PASS |
| DS-52 | tema aplicado antes da primeira pintura | `P:349-351` `html.index("<script>") < html.index('rel="stylesheet"')`; o script inline é o mesmo executado em `JT:79-91`; sensor M21 | PASS |
| DS-53 | tema escuro em cabeçalho, menu, cartões, tabelas, filtros, botões, mensagens, formulários, rodapé | `C:128-130` regra `:root[data-tema="escuro"] .<componente>` para `br-header`, `br-menu`, `br-footer`, `br-message`, `br-card`, `br-table`, `br-input`, `br-button`; `C:114-118` filtros (`dcc.Dropdown`); `K:56-60` `--background` e `--color` trocam pelos pares `-dark`; manual `VV:66` | PASS |
| DS-54 | cores do tema escuro só por tokens, sem hex | `C:121-125` todo valor do bloco `:root[data-tema="escuro"]` começa com `var(--`; `C:13-15` sem hex | PASS |
| DS-55 | logotipo sobre superfície clara nos dois temas | `P:64-65` `class="logo-superficie"` envolve o `<img>`; `C:133-135` `.logo-superficie{background: var(--pure-0)}` e nenhuma regra `data-tema="escuro"` altera `.logo-superficie` | PASS |
| DS-56 | breadcrumb em todas as admin, exceto login, recuperar e instalação | `S:76-80` `breadcrumb == [{"Início","/"},{rotulo,None}]`; `S:83-87` os três sem breadcrumb e sem menu; `AP:44-51`, `AP:89-97`, `AP:116-119`, `AP:174-179` | PASS |
| DS-57 | login: título "Acesso ao sistema", rótulo acima, apoio, "Esqueci minha senha" abaixo da senha, "Entrar" na largura | `AP:59-65` `<h1>Acesso ao sistema</h1>`, `"Mínimo de 8 caracteres."`, `html.index('id="senha"') < html.index("Esqueci minha senha")`; `AP:68-70` `class="br-button primary block"` | PASS |
| DS-58 | confirmação destrutiva em `br-modal`, ícone de alerta, pergunta, Cancelar `secondary` e confirmação `primary` | `P:246-266` `role="dialog"`, `aria-modal="true"`, `fa-exclamation-triangle`, `br-button secondary` "Cancelar", `br-button primary` confirmar; `JF:258-269` `confirmarAcao("Excluir o campus X?", {rotuloConfirmar:"Excluir"})` mostra `ativo True`, texto e rótulo; `AC:360-368` `data-confirm` e `data-confirm-rotulo="Excluir"` | PASS |
| DS-59 | sem `confirm()` nativo | `JC:51-53` e `JC:78-81` nenhuma chamada em `app/static/js/*.js`; `AP:116-120` `"confirm(" not in html`; `AP:242-259`; `JC:84-87` `atualizar.js` usa `confirmarAcao` nos 4 botões | PASS |
| DS-60 | modal: foco preso, Esc fecha, foco volta à origem | `JF:291-301` Tab/Shift+Tab ciclam `[True, True, True]`; `JF:272-288` Esc e Cancelar `resposta False`, Confirmar `True`, `fechado True`, `foco == origem`; `JF:258-269` foco inicial em Cancelar; `JC:28-46` `proximoFoco` e `teclaFecha`; sensores M10 a M14; manual `VV:56-62` | PASS |
| DS-61 | breadcrumb "Início > título" nas públicas não capa | `S:39-48` capa `== []`, demais `[{"Início","/"},{rotulo,None}]`; `S:226-231` `textos == ["Início", rotulo]` e capa sem `br-breadcrumb`; `P:158-163` | PASS |
| DS-62 | lista "Campi do Sistec" em `br-table`, 7 colunas | `AC:136-138` `colunas == ["Perfil","Identificador","Código da unidade","Cidade","Nome da unidade","Situação","Ações"]` e `<h1>Campi do Sistec</h1>` | PASS |
| DS-63 | situação em `br-tag` "Ativo" ou "Desativado" | `AC:146` e `AC:150` `<span class="br-tag">Ativo/Desativado</span>`; `P:316-320` | PASS |
| DS-64 | aviso "Identificador inválido: a atualização não roda assim" na linha do suspeito | `AC:156-161` `aviso not in linhas[0]`, `aviso in linhas[1]`, `aviso not in linhas[2]` | PASS |
| DS-65 | Editar, Desativar/Reativar, Excluir com nome acessível que cita o perfil | `AC:147-153` `aria-label="Editar campus Perfil Alegrete"`, `"Desativar campus ..."`, `"Excluir campus ..."`, `"Reativar campus Perfil Inativo"` e `"Desativar campus" not in inativo`; destinos: `AC:528-536` `href="/admin/campi/8278857/editar"` do Editar, `action=".../situacao"` com `name="ativo" value="0"` (Desativar) e `value="1"` (Reativar), `action=".../excluir"`; cards `AC:539-546`; `P:323-334` | PASS |
| DS-66 | Editar abre "Editar campus \| {perfil}" com breadcrumb Configurações > Campi > Editar | `AC:198` `<h1>Editar campus \| Perfil Alegrete</h1>`; `AC:200` `== ["Configurações","Campi","Editar"]`; `AC:531` o link Editar aponta ao `href` da tela; `S:51-60`; sensores M19 e M26 | PASS |
| DS-67 | campos Identificador, Código, Cidade, Nome da unidade em `br-input` com rótulo visível, em linhas da grade | `AC:201-203` `len(br-input) == 4` e `<label for="...">` dos 4; `AC:520-525` cada campo em coluna `{"col-12","col-md-6"}` dentro de `row`; `AC:267-273` inclusão com 5 rótulos na ordem | PASS |
| DS-68 | Cancelar `secondary` e Salvar `primary`, alinhados à direita a partir de 576px | `AC:204-205` `br-button secondary ... href="/admin/campi" ... Cancelar` e `br-button primary ... type="submit" ... Salvar`; `P:308-313` Cancelar antes de Salvar; `P:343-346` `justify-content-sm-end`; sensores M15 e M16 | PASS |
| DS-69 | salvar válido grava, volta à lista e mostra "Campus atualizado." | `AC:208-215` `status 302`, `Location` termina em `/admin/campi`, `obter_campus("8278857")["cidade"] == "Uruguaiana"`, mensagem `success` com `role="alert"` e o texto | PASS |
| DS-70 | campo obrigatório vazio: mantém a tela, campo `danger`, "Preencha o campo obrigatório" | `AC:225-238` `status 200`, `class="br-input danger"` no `co_unidade`, `id="co_unidade-erro"` com o texto, `value="Cidade digitada"` mantido; `CA:186-201` `validar_campos_campus(...) == {campo: "Preencha o campo obrigatório"}` | PASS |
| DS-71 | identificador ou código de outro campus: campo `danger` e mensagem da regra | `AC:241-254` `"esse identificador de perfil já está em outro campus"` no `id_perfil` e `"esse código da unidade já está em outro campus"` no `co_unidade`; `CA:118-155` `erro.value.campo == "id_perfil"/"co_unidade"` e `str(erro.value) == ...` | PASS |
| DS-72 | banner `danger` com `role="alert"` "Erro. Preencha abaixo os campos obrigatórios antes de enviar os dados." | `AC:233-237` `class="br-message danger"[^>]*role="alert".*Erro\. Preencha abaixo os campos obrigatórios antes de enviar os dados\.`; `AC:307` na inclusão | PASS |
| DS-73 | Excluir abre modal com a pergunta, o aviso do Sistec e os botões "Cancelar" e "Excluir" | `AC:360-369` `data-confirm="Tem certeza que deseja excluir o campus Perfil Alegrete?`, `"volta na próxima atualização" in botao`, `data-confirm-rotulo="Excluir"`, `<form class="confirm-form" action=".../excluir">`; abertura do modal com a pergunta: `JF:258-269`; botão "Cancelar": `P:264` | PASS |
| DS-74 | confirmar exclui e mostra "Perfil excluído da lista." | `AC:372-380` `302`, `obter_campus("8278857", banco) is None`, mensagem `success` com `role="alert"` e `"Perfil excluído da lista."`, o perfil some das linhas; `JF:280-288` confirmar `resposta True` e `JF:320-337` o formulário só é enviado depois de confirmar (`enviados == 1`, `marcado == "1"`) | PASS |
| DS-75 | Cancelar fecha o modal sem excluir | `JF:272-288` Cancelar `{"resposta": False, "fechado": True, "foco": True}`; `JF:320-337` cancelar: `enviados == 0` e `marcado is None`; manual `VV:61` (14 linhas antes e depois); sensores M10 e M13 | PASS |
| DS-76 | Desativar/Reativar sem confirmação e com `br-message success` | `AC:318-326` `ativo == 0`, "Campus desativado.", tag "Desativado"; `AC:329-335` `ativo == 1`, "Campus reativado."; `AC:338-342` `"data-confirm" not in botao`; `AC:354-357` valor inválido `400` e o campus não muda; destinos: `AC:532-535`; sensores M20 e M23 | PASS |
| DS-77 | "Incluir campus" com 5 campos no mesmo layout | `AC:271-273` `<h1>Incluir campus</h1>`, `re.findall(r'<label for="([^"]+)">') == ["id_perfil","nome_perfil","co_unidade","cidade","nome_unidade"]`, `len(br-input) == 5` | PASS |
| DS-78 | salvar a inclusão grava, volta e mostra "Campus incluído." | `AC:276-288` `302`, `campus["origem"] == "manual"`, `nome_perfil == "Perfil Novo"`, `co_unidade is None`, mensagem "Campus incluído."; `AC:291-295`; `CA:204-213` só identificador e nome são obrigatórios | PASS |
| DS-79 | sem campo de edição em célula de tabela | `AC:164-168` `"<input" not in celula` para toda `<td>`; `AP:221-232` idem em `/admin/config` e `"<table" not in html` | PASS |
| DS-80 | barra "Campi" com busca por texto acima da tabela | `AC:407-413` `<h2>Campi</h2>`, `<input ... name="q">`, `<button type="submit" aria-label="Buscar campus">`, `html.index('role="search"') < html.index("<table")` | PASS |
| DS-81 | busca por envio filtra por perfil, cidade ou unidade, sem diferenciar caixa | `AC:45-55` `["1","2","3"]` para `"santa"`, `"SANTA"`, `"  Santa  "`; `AC:416-421` `len(linhas) == 1` e `"1-1 de 1 itens"`; sensor M24 | PASS |
| DS-82 | sem resultado: `br-message info` "Nenhum campus encontrado." | `AC:424-427` `class="br-message info"[^>]*>.*Nenhum campus encontrado\.` e `"<table" not in html`; `AC:58-61` | PASS |
| DS-83 | paginação: seletor 10/25/50 (padrão 10), "1-10 de N itens", anterior e próxima | `AC:430-433` `"1-10 de 22 itens"`, `"1-22 de 22 itens"`, `"21-22 de 22 itens"`; `AC:436-441` `== ["10","25","50"]` e `<option value="25" selected>`; `AC:444-450` `disabled` na primeira e na última; `AC:453-464`; `AC:20-77` função pura | PASS |
| DS-84 | botão "Visualizar em Cards"/"Visualizar em Lista" com `aria-pressed` | `AC:471-475` `aria-pressed="false"`, "Visualizar em Cards", `visao=cards`; `AC:478-482` `aria-pressed="true"`, "Visualizar em Lista" | PASS |
| DS-85 | cada campus em `br-card` com dados, situação e as mesmas ações | `AC:485-499` 3 cards, `Perfil Alegrete`, `8278857`, `101`, tag, `aria-label` das 3 ações, aviso do suspeito, `"<table" not in html`; `AC:539-546` mesmos destinos da linha; `AC:509-517` busca e paginação valem nos cards | PASS |

### Casos de borda da spec

| Caso de borda | Evidência | Status |
| ------------- | --------- | ------ |
| Sem dados publicados: "Ainda não há dados publicados." em `br-message info`, sem KPIs zerados | `PP:48-56` (`{"br-message","info"}`, `SEM_DADOS in textos(...)`, `not com_classe(layout, "br-card")`), `PP:143-149`, `PP:205-210`, `PP:264-269`, `PP:325-330`; `CP:19-32` (`None` vira travessão, `0` real não é escondido) | PASS |
| **Preferência do sistema muda com a página aberta e sem escolha salva: segue a nova preferência** | `JF:158-166` `consultas[0].mudar(true)` com `salvo=None` => `"escuro"`; com `salvo="claro"` => `"claro"` (a escolha vence); sensor M09 | PASS |
| Cor de estado mantém rótulo textual no tema escuro | `PP:247-253`, `PP:301`; `C:164-174` mensagens no escuro; manual `VV:66` | PASS |
| Nenhum campus cadastrado: `br-message info` | `AC:171-176` `class="br-message info"`, `"Importe a lista de perfis"`, `"inclua um campus"`, `"<table" not in html` | PASS |
| Editar campus excluído em outra aba: volta à lista com "Campus não encontrado." | `AC:257-264` (GET e POST: `302`, `Location` `/admin/campi`, `class="br-message danger"`, texto exato) | PASS |
| `core-init.min.js` não carrega: navegação continua visível | `P:224-235` o `onerror` põe `ds-sem-js` no `<html>` (executado em `node`); `C:110-111` `.ds-sem-js .br-menu .menu-container{display: block}` | PASS |
| Tabela de campi larga em 320px: rola só o contêiner | `AC:166`; manual `VV:29-30` | PASS |
| Zoom 200%, orientação, Rawline ausente, viewport < 320px | Sem teste automático; equivalem a largura menor (coberto por `VV:13-32`); fonte local `A:109-117` | PASS (manual) |

---

## Sensor de discriminação

**Profundidade**: expandida (caminho crítico de interface e regras de campi), 26 mutações de comportamento, cada uma aplicada em `git worktree --detach` do HEAD, rodando a suíte inteira com `-x`, restaurada com `git checkout -- <arquivo>` e conferida com `git status --porcelain --untracked-files=no` vazio entre uma e outra. Linha de base no scratch: 545 passed.

| # | Arquivo | Mutação | Teste que matou | Status |
| - | ------- | ------- | --------------- | ------ |
| M01 | `app/static/js/menu.js` | remove o recolhimento por clique (`addEventListener("click", ...)`) | `JF:182` `test_a_partir_de_992px_o_menu_comeca_expandido_e_o_botao_o_recolhe_por_clique_e_por_teclado` | MORTO |
| M02 | `app/static/js/menu.js` | remove o recolhimento por Enter/Espaço (`code === "Enter" \|\| "Space"` vira `false`) | `JF:182` (mesmo teste) | MORTO |
| M03 | `app/static/js/menu.js` | `menuExpandido` invertido (`? !recolhido` vira `? recolhido`) | `JF:182` | MORTO |
| M04 | `app/static/js/menu.js` | não devolve o foco ao botão (`botao.focus()` removido) | `JF:214` `test_abaixo_de_992px_aria_expanded_acompanha_o_menu_e_o_foco_volta_ao_botao_ao_fechar` | MORTO |
| M05 | `app/assets/style.css` | esconde `.header-menu-trigger` de novo em `@media (min-width: 992px)` | `C:101` `test_a_partir_de_992px_o_botao_do_cabecalho_continua_visivel_e_recolhe_o_menu` | MORTO |
| M06 | `app/assets/style.css` | remove a regra `.menu-recolhido` | `C:101` (mesmo teste; `_regra` levanta `sem regra para .br-menu.menu-recolhido`) | MORTO |
| M07 | `app/static/js/tema.js` | clique não grava a escolha (remove `gravarTema`) | `JF:136` `test_clique_no_botao_de_tema_troca_o_tema_o_aria_pressed_o_rotulo_e_grava_a_escolha` | MORTO |
| M08 | `app/static/js/tema.js` | `aria-pressed` fixo em `"false"` | `JF:136` | MORTO |
| M09 | `app/static/js/tema.js` | ignora a mudança da preferência do sistema | `JF:158` `test_mudanca_da_preferencia_do_sistema_so_vale_sem_escolha_salva[None-escuro]` | MORTO |
| M10 | `app/static/js/confirmar.js` | Cancelar confirma (`fechar(true)`) | `JF:272` `..._todos_devolvem_o_foco_a_origem[cancelar...-False]` | MORTO |
| M11 | `app/static/js/confirmar.js` | Esc não fecha (`if (false)`) | `JF:272` `[doc.disparar("keydown", { key: "Escape" })...-False]` | MORTO |
| M12 | `app/static/js/confirmar.js` | não devolve o foco à origem | `JF:272` `[doc.disparar("keydown"...` | MORTO |
| M13 | `app/static/js/confirmar.js` | formulário enviado mesmo após Cancelar (remove `if (!ok) return`) | `JF:320` `test_formulario_confirm_form_so_e_enviado_depois_de_confirmar_no_modal[cancelar-False]` | MORTO |
| M14 | `app/static/js/confirmar.js` | submit não interceptado (remove `preventDefault`) | `JF:320` `[confirmar-True]` (`evitado is True`) | MORTO |
| M15 | `app/templates/shell/_macros.html` | `botoes_formulario` sem `flex-column` | `P:343` `test_botoes_do_formulario_empilham_abaixo_de_576px_e_alinham_a_direita_depois` | MORTO |
| M16 | `app/templates/shell/_macros.html` | `botoes_formulario` sem `justify-content-sm-end` | `P:343` | MORTO |
| M17 | `app/templates/shell/_macros.html` | `role` da `mensagem` `success` vira `status` | `AC:179` `test_mensagem_flash_aparece_como_br_message_da_categoria` (e `P:301`) | MORTO |
| M18 | `app/templates/campi_form.html` | campos sem `col-12` | `AC:520` `test_campos_do_formulario_de_campus_ocupam_a_linha_toda_no_celular_...` | MORTO |
| M19 | `app/templates/campi_lista.html` | link Editar sem `/editar` | `AC:528` `test_cada_linha_liga_editar_ao_href_certo_...` | MORTO |
| M20 | `app/templates/campi_lista.html` | `action` da situação aponta para `/excluir` | `AC:528` | MORTO |
| M21 | `app/templates/shell/_head.html` | script de tema depois das folhas de estilo | `P:349` `test_head_define_o_tema_antes_de_qualquer_folha_de_estilo_para_nao_piscar` | MORTO |
| M22 | `app/templates/_base.html` | `<main>` sem `id="main-content"` (alvo do link de salto, DS-32) | `S:178` `test_pagina_dash_mantem_entrada_config_scripts_e_renderer_com_a_entrada_no_main` | MORTO |
| M23 | `app/admin_campi.py` | `situacao` deixa de responder 400 para valor inválido | `AC:353` `test_situacao_com_valor_invalido_responde_400_...[None]` | MORTO |
| M24 | `app/admin_campi.py` | busca deixa de olhar a cidade | `AC:45` `test_busca_acha_perfil_cidade_ou_nome_da_unidade_...` | MORTO |
| M25 | `app/shell.py` | item ativo do menu nunca marcado | `AP:182` `test_atualizar_mostra_breadcrumb_e_menu_administrativo` | MORTO |
| M26 | `app/shell.py` | breadcrumb de Editar com "Campi" sem link | `S:51` `test_breadcrumb_das_rotas_de_campi` | MORTO |

**Resultado do sensor**: 26/26 mortos, 0 sobreviveram. Os 14 mutantes que sobreviviam na verificação anterior (`botoes_formulario` sem `flex-column`/`justify-content-sm-end`, `col-12`, `href` de Editar, `action` de situação, script de tema depois das folhas, mudança da preferência do sistema, e a fiação de DOM de `tema.js`, `menu.js` e `confirmar.js`) estão todos cobertos por teste que falha com a mutação.

> M01, M02, M03, M05 e M06 miravam o DS-05 antigo (barra horizontal com botão para recolher). O commit `0743980` (AD-005) substituiu esse código; as mutações equivalentes para a nova barra lateral estão em M30-M32.

### Sensor do delta T53 (Font Awesome) — leve, 3 mutações

Rodei em `git worktree --detach` do HEAD (`7daec61`), com os alvos em scratch, restaurando cada arquivo antes da próxima mutação e removendo o worktree ao final; `git status --porcelain` idêntico antes e depois.

| # | Arquivo | Mutação | Teste que matou (ou ausência) | Status |
| - | ------- | ------- | ----------------------------- | ------ |
| M27 | `app/static/vendor/fontawesome/webfonts/fa-solid-900.woff2` | arquivo apagado | `A:120` `test_os_webfonts_do_font_awesome_resolvem_para_200` (o `url(...)` vira 404) e `A:132` `test_font_awesome_e_vendorizado_localmente` (arquivo ausente) | MORTO |
| M28 | `app/static/vendor/fontawesome/css/all.min.css` | `fa-solid-900.woff2` trocado por `fa-solid-900-X.woff2` no `url(...)` | `A:120` (a URL não resolve 200) | MORTO |
| M29 | `app/templates/shell/_head.html` | `<link .../fontawesome/css/all.min.css>` removido (linha 22) | `P:37` `test_head_linka_o_font_awesome_local_antes_do_ds` | MORTO |

Isolamento: `git worktree remove --force` + `git worktree prune`; `git worktree list` mostra só o repositório real; `git status --porcelain` idêntico ao de antes (4 linhas não rastreadas: `.agents/`, `.claude/skills/tlc-spec-driven/`, `.cursor/`, `.windsurf/`).

### Sensor do delta DS-05 (barra lateral fixa) — leve, 3 mutações

Rodei em `git worktree --detach` do HEAD (`0743980`), com os alvos em scratch, restaurando cada arquivo antes da próxima mutação e removendo o worktree ao final; `git status --porcelain` idêntico antes e depois.

| # | Arquivo | Mutação | Teste que matou (ou ausência) | Status |
| - | ------- | ------- | ----------------------------- | ------ |
| M30 | `app/assets/style.css` | `position: fixed` removido do `.br-menu` no bloco 992px | `C:103` `test_a_partir_de_992px_o_menu_vira_barra_lateral_fixa_sem_botao` | MORTO |
| M31 | `app/assets/style.css` | `display: none` removido do `.header-menu-trigger` | `C:105` (mesmo teste) | MORTO |
| M32 | `app/static/js/menu.js` | reintroduz `menu.classList.toggle("menu-recolhido")` no clique | `JF:81` `test_o_menu_nao_tem_recolhimento_persistente_em_nenhuma_largura` (e `JF:94` `test_abaixo_de_992px_o_menu_comeca_fechado_e_o_botao_nao_recolhe_nada`) | MORTO |

**Resultado do sensor do delta DS-05**: 3/3 mortos, 0 sobreviveram. O teste da barra lateral prende `position: fixed`, `width: var(--menu-largura)`, `.header-menu-trigger{display:none}` e `body{padding-left:var(--menu-largura)}`; o teste de fiação prende a ausência do recolhimento persistente.

---

## Regra de payload e conjunção

Os campos nomeados alvejam valor ou estado, não apenas a chamada: `AC:212` (`["cidade"] == "Uruguaiana"`), `AC:283-285` (`origem == "manual"`, `nome_perfil`, `co_unidade is None`), `AC:322` e `AC:332` (`ativo == 0` e `== 1`), `AC:376` (`obter_campus(...) is None`), `AC:357` (o campus não muda com `400`), `CA:167-172` (cada coluna de `obter_campus`), `CA:189` e `CA:194` (mapa exato campo -> mensagem), `JF:149-151` (`tema`, `pressed`, `rotulo`, `salvo` juntos), `JF:81-84` (`expanded` e `recolhido` juntos), `JF:337` (`enviados` e `marcado`), `PP:249-253` (valor e classe de cor por campus). Nenhuma asserção só de "a chamada ocorreu" foi achada nos ACs desta iteração.

---

## Qualidade de código

| Princípio | Status |
| --------- | ------ |
| Sem funcionalidade além do pedido | OK: só o que a spec pede; sem dependência nova (testes de JS em `node`, com `skipif`) |
| Mudanças cirúrgicas | OK: o intervalo toca os arquivos da feature; remoções (`header.py`, `footer.py`, `navigation.py`, `nav-toggle.js`, `_admin_nav.html`) estão em DS-19/T38 |
| Segue os padrões existentes | OK: `server.test_client()`, `session_transaction`, banco temporário |
| Testes mapeiam ACs, sem teste órfão | OK; helpers `arvore_dash.py` e `dom_falso.py` são apoio dos ACs |
| Diretrizes documentadas | `.specify/memory/constitution.md` (Princípios IV e fluxo) e `TESTAR.md`; sem linter no repositório |
| Escopo (`git diff 42c5f43^..HEAD --name-status`) | OK: nenhum arquivo fora de app, tests, docs e `.specs` |

---

## Lacunas ranqueadas (não derrubam o PASS)

1. **Menor, DS-37/DS-38 em navegador real**: o comportamento de `menu.js` com o `core-init.min.js` (manter `aria-expanded` e devolver o foco ao botão ao fechar) só é exercido em navegador pelo autor (`VV:46-52`, com `KeyboardEvent` sintético porque as teclas reais não chegaram ao `iframe`). Abaixo de 992px o DS abre/fecha o menu sobreposto e `menu.js` só sincroniza `aria-expanded` e o foco. Nenhum teste automático prende a interação das teclas do DS; risco baixo, e a regra AD-004 pede conferir o `core-init.min.js` ao atualizar o DS.
2. **Menor, spec-precision em DS-34 e DS-43**: DS-34 é provado só para os pares de token (`--color`, `--interactive`, `--focus-color` sobre `--background` e `--background-alternative`, `K:43-70`), não para cada componente; DS-43 (4/8/12 colunas) é propriedade do `core.min.css` e o teste afirma as classes `col-*`, não a contagem de colunas por faixa. Complemento: `VV:13-32`, `VV:66`. Não há resultado impreciso na spec que o teste contradiga.
3. **Cosmética**: o nome do teste `AC:520` diz "metade a partir de 768px", mas `col-md-6` é 992px no DS (`core.css:2518`); a asserção `{"col-12","col-md-6"}` está correta, só o nome é antigo. Sugestão: renomear.
4. **Fora do escopo desta feature, herdada** (`VV:78`): `/matriculas?x=1` não renderiza porque os cinco `layout()` do Dash não aceitam parâmetros; anotado no relatório visual.
5. **Cosmética, fora do que posso editar**: `verificacao-visual.md:41` ainda descreve o DS-05 antigo ("Botão do cabeçalho presente a partir de 992px ... `menu.js` recolhe e mostra"), contradizendo o AD-005; a linha `VV:40` já tem a nota de atualização. O implementador deve corrigir `VV:41` (esta verificação só escreve `validation.md`).

---

## PENDENTES (humano ou externo; nenhum é falha de código)

| Item | Motivo | Efeito enquanto pendente | Quem resolve |
| ---- | ------ | ------------------------ | ------------ |
| **DS-42** (celular real, 320-430px, e tela de 1280px ou mais; 5 páginas públicas e `/admin/atualizar`) | Passo humano de Jaline (T57): roteiro pronto em `CUTOVER.md:34-49`; o item de design (`CUTOVER.md:19`) só é marcado com dispositivo, largura e data | `CUTOVER.md` continua com o item desmarcado; DS-42 não passa a "Verified" | Jaline |

---

## Rastreabilidade (atualizar `spec.md`, tabela de requisitos)

DS-01 a DS-41 e DS-43 a DS-85: **Verified**. DS-24: **Verified** por completo (DS local, Rawline e Font Awesome). DS-42: pendente de passo humano. (Esta verificação não alterou `spec.md`; a atualização de status DS-24 já foi feita pelo implementador no commit do Font Awesome.)

---

## Lições reaproveitáveis (não gravadas; `lessons.py` não foi rodado)

- Teste de comportamento de DOM em `node` com DOM simulado (`tests/dom_falso.py`) mata mutantes de fiação (clique, tecla, observador) que testes só de função pura deixam viver; vale como padrão para qualquer script estático.
- Ao trocar um AC da spec (DS-05), reescrever o teste que afirmava o comportamento antigo (`C:96`) em vez de apenas acrescentar outro: o teste antigo exigia o botão oculto e teria travado a correção.
- Depois de corrigir um mutante por asserção de classe CSS (`flex-column`), conferir que a classe existe no CSS do DS e na faixa certa (`core.css:1761`, 576px): a asserção sem essa conferência prova a string, não o efeito.
- Nome de teste com valor de breakpoint antigo (768px) envelhece; nomear pela regra ("metade em telas médias").
- Ao vendorizar um asset, testar também o `<link>`/`<script>` que o inclui no template (presença), não só os arquivos no disco e a resolução das URLs: o mutante que apaga o link do Font Awesome em `_head.html` sobreviveu, pois os testes só cobriam arquivo e URL.

---

# Rodada paridade Figma — página inicial (Matrículas) em telas largas — PASS

**Data**: 2026-09-21
**Fonte**: `.specs/features/govbr-design-system/tarefa-paridade-figma-telas-largas.md` (13 defeitos, AC-1.1 a AC-13.3)
**Intervalo de commits**: `63569ae` (baseline da migração) a `45b5c72` (10 commits de defeito + 1 correção de follow-up), branch `migracao-dash-gov-br`
**Método**: correção por defeito, um commit atômico por defeito (ordem da seção 5); medição no DOM via Playwright (Chromium) nas larguras 1280/1600/900px e no tema escuro a 1280px.

## Gate

- `python -m compileall -q app` → exit 0.
- `python -m pytest -q` → **541 passed, 0 failed, 0 skipped** (2 FutureWarnings de pandas em `app/data/fatores.py`, fora da feature).

## Testes atualizados junto com o código (não ignorados)

| Teste | Motivo |
| ----- | ------ |
| `tests/test_style_css.py:101-106` | Defeito 1 trocou `position:fixed`/`padding-left` do `body` por grid; agora assevera `grid-template-columns: var(--menu-largura)`, `position: static` e `.header-menu-trigger{display:none}` |
| `tests/test_paginas_publicas.py:72` | Defeito 5: o callback devolve lista de 5 `kpi-figma`, não um `Div.kpis-figma` aninhado |
| `tests/test_paginas_publicas.py:76-84` | Defeito 10: "Integralizadas" zero vira "—" |
| `tests/test_componentes_publicos.py:122` | Defeito 11: ordem dos `EIXOS` |
| `tests/test_shell.py:172` | Defeito 12: rodapé público `br-footer painel-publico` |
| `tests/test_js_fiacao.py:19,38-40` | rótulo do tema encurtou para "Tema escuro"/"Tema claro" (baseline) |

## Critérios de aceite — evidência no DOM (1280px, tema claro, salvo indicação)

| AC | Medição (`getBoundingClientRect`/`getComputedStyle`) | Status |
| -- | ----------------------------------------------------- | ------ |
| AC-1.1 | `header.br-header` x=0 w=1280 | PASS |
| AC-1.2 | `footer.br-footer` x=0 w=1280 | PASS |
| AC-1.3 | `.br-menu` topo y=72, logo abaixo do cabeçalho (h=72); item ativo visível, não encoberto | PASS |
| AC-1.4 | 900px: `.br-menu` recolhido (h=0), cabeçalho com o botão, `main` largura total | PASS |
| AC-2.1 | `.br-menu .menu-panel` w=240 | PASS |
| AC-2.2 | os 4 rótulos com altura de uma linha (labelLines=20) | PASS |
| AC-2.3 | painel `background: rgb(255,255,255)` (`--background`) + `border-right: 1px solid var(--border-color)` | PASS |
| AC-3.1 | item ativo bg `color(srgb 0.925961 0.945412 0.976471)` (~#ECF1F9, claro) + texto `rgb(19,81,180)`; **não** azul-escuro/branco | PASS |
| AC-3.2 | `::before` do ativo: 4px x 20px, bg `rgb(19,81,180)` | PASS |
| AC-3.3 | ativo `padding-left: 12px`, inativos `24px` | PASS |
| AC-3.4 | `--color-primary-default` sobre o fundo claro ≈ 5,5:1 (AA) | PASS |
| AC-4.1 | `header.br-header.painel-publico` h=72 | PASS |
| AC-5.1 | `nestedKpis == 0` (sem `.kpis-figma` dentro de `.kpis-figma`) | PASS |
| AC-5.2 | 5 `.kpi-figma` com w=186 cada (iguais), somando a largura do Main (992) | PASS |
| AC-6.1 | 6 chips na mesma linha (y=423); `.card-chips` h=67 (teto 66; +1px de arredondamento) | PASS |
| AC-6.2 | chip ativo bg `rgb(19,81,180)` + texto branco; inativos borda e texto `--interactive` | PASS |
| AC-6.3 | `.card-chips` `border: 0px none` | PASS |
| AC-7.1 | duas opções FIC lado a lado, `min-height: 40px` | PASS |
| AC-7.2 | base do grupo FIC `bottom` == base dos Dropdowns (1125 == 1125) | PASS |
| AC-8.1 | foco no input de chip/seg desenha `outline: 3px solid var(--focus-color)` no label irmão (ambos os temas) | PASS |
| AC-9.1 | `.matriz-figma` `border: 1px solid`, `border-radius: 12px`, `overflow: hidden` | PASS |
| AC-9.2 | colWidths `[359,160,110,130,120,110]` (Campus flexível; 1600px → Campus 679) | PASS |
| AC-9.3 | "Campus"/"Concluintes" `center`; demais `th` `right` | PASS |
| AC-9.4 | zebra claro `rgb(248,248,248)` (`--gray-2`); escuro `rgb(12,50,111)` (`--background-alternative`) | PASS |
| AC-10.1/10.2 | célula "Integralizadas" zero (corpo e Total) mostra "—" em `td.vazio` (`--gray-40`) | PASS |
| AC-10.3 | classe `zero` removida de `matriculas.py` | PASS |
| AC-11.1 | ordem renderizada: Campus, Tipo de Curso, Oferta (Técnico), Nome do Curso, Modalidade, Ciclo | PASS |
| AC-12.1 | rodapé público `bg rgb(19,81,180)`, `min-height: 48px` (h=49 com o conteúdo), sem borda superior | PASS |
| AC-12.2 | rodapé administrativo mantém o DS (`class="br-footer"`, sem `painel-publico`) | PASS |
| AC-12.3 | links brancos sobre o azul institucional passam AA | PASS |
| AC-13.1 | `body` bg `rgb(248,248,248)` (cinza claro); `main` bg branco | PASS |
| AC-13.2 | conteúdo do `main` em x=264 (240 + 24px), mesmo recuo do título do cabeçalho | PASS |
| AC-13.3 | tema escuro: `body` e `main` em `rgb(7,29,65)`; sem branco-sobre-branco nem cinza-sobre-cinza | PASS |

## Desvios registrados (não reabrir)

1. **Correção de follow-up** (`45b5c72`): o seletor `a.menu-item.active` (especificidade 0,4,1) era necessário para vencer o `.br-menu a.menu-item:not(:disabled).active` do DS; o fundo ativo usa `color-mix(in srgb, var(--color-primary-default) 8%, var(--background))` (adaptável ao escuro) em vez de `--blue-warm-vivid-5` fixo, com par escuro próprio.
2. Rodapé h=49px (o conteúdo de 4 links o estica 1px além dos 48; o AC permite crescer).
3. `.card-chips` h=67px (teto de 66; 1px de arredondamento do chip).
4. Tema escuro: `--superficie-pagina` = `--background-dark` e `main` = `--background` (= `--background-dark`), então a distinção de superfície colapsa no escuro — comportamento da própria regra do Defeito 13, sem branco/cinza indevidos.
5. Fonte Rawline (não Inter), banner do Sistec, link "Área administrativa", skiplink e breadcrumb mantidos (seção 4 da tarefa).

## Verificação visual

Playwright (Chromium) em 1280x1078, 1600x900, 900x900 (claro) e 1280x1078 (escuro). Todos os ACs acima medidos no DOM. Abaixo de 992px o menu fica sobreposto e fechado por padrão (AC-1.4), sem regressão.
