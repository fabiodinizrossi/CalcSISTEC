# STATE

## Decisions

### AD-001
- **Decision**: Cabeçalho, menu, breadcrumb, modal de confirmação e rodapé existem uma vez, em parciais Jinja (`app/templates/shell/`), usados pelas páginas Flask e injetados no HTML do Dash por `interpolate_index`; o Dash renderiza só o conteúdo de `<main>`.
- **Reason**: Uma só marcação para as 11 telas, e o JS do DS inicializa no DOM real da carga (o `core.min.js` não observa DOM criado depois).
- **Trade-off**: Navegar entre páginas públicas passa a recarregar a página inteira.
- **Scope**: Toda tela nova, pública ou administrativa.
- **Date**: 2026-09-19
- **Status**: active

### AD-002
- **Decision**: O gov.br DS, o Font Awesome 5 e a fonte Rawline são servidos localmente de `app/static/` (URL `/ds/`), fora de `app/assets/`, com `core.min.css` e `core.min.js` carregados uma vez pelo shell.
- **Reason**: O Dash carrega recursivamente tudo de `app/assets/` (162 arquivos do DS, mais os scripts administrativos); fora dele, o shell decide o que carrega. O pacote 3.7.0 não traz fonte nem ícones.
- **Trade-off**: Os arquivos do DS deixam de ser um diretório de assets do Dash; atualizar o DS exige trocar a pasta e conferir as dependências de fonte e ícone.
- **Scope**: Toda entrega de CSS, JS, fonte e ícone da interface.
- **Date**: 2026-09-19
- **Status**: active

### AD-003
- **Decision**: O tema claro e o escuro são escolhidos por `data-tema` em `<html>`, e o escuro remapeia só as variáveis semânticas do DS (`--background`, `--color`, `--interactive`…) para as variantes `-dark`; nenhuma cor hexadecimal literal em `style.css`.
- **Reason**: O DS 3.7.0 não tem tema global, mas os tokens já trazem pares claro e escuro; trocar variáveis mantém uma só fonte de cor.
- **Trade-off**: Componentes sem suporte a tokens `-dark` exigem regra extra em `style.css`, sempre com variáveis do DS.
- **Scope**: Todo CSS novo do painel.
- **Date**: 2026-09-19
- **Status**: active

### AD-004
- **Decision**: O shell carrega `core-init.min.js` (um único script do DS), não `core.min.js`; `menu.js` complementa o menu do DS com `aria-expanded` e o foco de volta ao botão.
- **Reason**: `core.min.js` só registra os comportamentos e não instancia `br-menu`, `br-header` e os demais (verificado no Chrome: o botão do menu não abria). `core-init.min.js` faz isso na carga do DOM real; o DS não devolve o foco ao botão ao fechar com Esc.
- **Trade-off**: Substitui a premissa de AD-001 e AD-002 de que `core.min.js` inicializa os componentes; atualizar o DS exige conferir que o `core-init.min.js` continua chamando `initInstanceAll`.
- **Scope**: Toda página que carrega o shell (`shell/_scripts.html`).
- **Date**: 2026-09-19
- **Status**: active

### AD-005
- **Decision**: A partir de 992px o menu principal é uma barra lateral fixa à esquerda (largura `--menu-largura: 240px`), sempre aberta, sem botão hambúrguer; o conteúdo (cabeçalho, breadcrumb, `<main>`, rodapé) desloca para a direita por `padding-left` no `<body>`.
- **Reason**: A primeira versão (barra horizontal com botão hambúrguer para recolher) ficou ruim em telas largas, relatado por Jaline após o teste em celular e tela grande. O `br-menu` 3.7.0 só tem o modo push/sobreposto; a barra lateral é construída em `style.css` (`position: fixed` + `width` + `padding-left`).
- **Trade-off**: O menu deixa de ser recolhível em telas largas (não há como escondê-lo); abaixo de 992px continua sobreposto e fechado por padrão, aberto pelo hambúrguer.
- **Scope**: Todas as páginas públicas e administrativas com menu (DS-05; antes era "barra horizontal com hambúrguer").
- **Date**: 2026-09-20
- **Status**: active

## Handoff

Pausa em 2026-09-20. Quem retomar pode ser outro agente (opencode), sem as ferramentas do Claude: nada abaixo depende delas, só de `python`, `node` e `git`.

- **Feature**: `.specs/features/govbr-design-system`
- **Phase / Task**: Execute concluído; Verifier em PASS na 2ª iteração (`validation.md`, `validate_state.py` exit 0)
- **Completed**: T1 a T52, T54, T55, T56 e T57 (menos o passo humano). 60 commits na branch, último `8f18f3b`; 545 testes passam (`python -m pytest -q`; os de `tests/test_js_*.py` precisam do `node`)
- **In-progress** (file:line): none
- **Next step**: (1) T53: com autorização de Jaline para baixar da rede, vendorizar `@fortawesome/fontawesome-free` 5.x (CSS, `webfonts/fa-solid-900`, `fa-regular-400`, `fa-brands-400` e a licença) em `app/static/vendor/fontawesome/`, linkar o CSS em `app/templates/shell/_head.html` antes de `core.min.css`, e estender `tests/test_shell_assets.py` (todo recurso local do HTML resolve para 200, sem URL externo; já há o padrão para a Rawline). Commit: `feat(assets): Font Awesome 5 Free local para os ícones do DS`, com versão e origem no corpo. Sem isso os botões de ícone (editar, excluir, menu, busca) aparecem sem glifo, mas têm `aria-label`. (2) T57: Jaline testa em celular real (roteiro em `CUTOVER.md`, seção "Design gov.br responsivo") e informa dispositivo, largura e data; só então marcar o item de design de `CUTOVER.md` (DS-42). (3) Depois disso, rodar o Verifier de novo (`.claude/skills/tlc-spec-driven/references/validate.md`) para fechar DS-24
- **Blockers**: T53 exige autorização de rede de Jaline (só a Rawline foi liberada; ela veio de `Downloads/rawline-cdnfonts`, sem arquivo de licença junto). DS-42 exige o teste de Jaline
- **Não fazer sem OK explícito**: `git push`, merge da branch e deploy. Nada foi enviado ao remoto
- **Pendência fora do escopo**: as páginas do Dash não renderizam com query string (`/matriculas?x=1`), porque o Dash chama `layout(x="1")` e os cinco `layout()` não aceitam parâmetros (anterior a esta feature). Falta também token CSRF nos POST administrativos (registrado em `CUTOVER.md`)
- **Ambiente**: `app/data/sistec.db` está no estado original (vazio, restaurado após a verificação visual); nenhum servidor ficou rodando
- **Uncommitted files**: none da feature (fora de escopo e sem stage: `.agents/`, `.cursor/`, `.windsurf/`, `.claude/skills/tlc-spec-driven/`)
- **Branch**: migracao-dash-gov-br
