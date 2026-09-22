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
- **Decision**: A partir de 992px o menu principal ocupa a coluna lateral esquerda de 240px, sempre aberto e sem botão hambúrguer; cabeçalho e rodapé continuam na largura total. Abaixo de 992px ele é sobreposto e fechado por padrão.
- **Reason**: A primeira versão (barra horizontal com botão hambúrguer para recolher) ficou ruim em telas largas. O layout atual usa grid no `<body>` e posicionamento estático do menu, evitando que a lateral cubra ou desloque cabeçalho e rodapé.
- **Trade-off**: O menu deixa de ser recolhível em telas largas (não há como escondê-lo); abaixo de 992px continua sobreposto e fechado por padrão, aberto pelo hambúrguer.
- **Scope**: Todas as páginas públicas e administrativas com menu (DS-05; antes era "barra horizontal com hambúrguer").
- **Date**: 2026-09-20
- **Status**: active

## Handoff

Estado revisado em 2026-09-22. As verificações usam `uv`, `pytest`, `node` e `git`.

- **Feature**: `.specs/features/govbr-design-system`
- **Phase / Task**: T58 a T65 concluídas e verificadas independentemente.
- **Completed**: extensão pública T58–T65 nos commits `9816bff`, `0bff60a`, `d059945`, `9f014cd`, `ba5756d`, `6338d8d`, `6b71457` e `5d3f3c8`; relatório independente em `validation.md` (PASS).
- **In-progress**: nenhuma tarefa de código.
- **Blocker humano**: DS-42 exige teste de Jaline em celular real, com dispositivo, largura e data registrados em `CUTOVER.md`; não é falha técnica da extensão.
- **Verificação final**: compilação e 574 testes passaram; o sensor do verificador matou 2 de 2 mutações. `verificar_prontidao_cutover.py` permanece NO-GO apenas por credenciais administrativas e HTTPS ausentes no ambiente local.
- **Não fazer sem OK explícito**: `git push`, merge da branch e deploy. Nada foi enviado ao remoto.
- **Pendência fora do escopo**: as páginas do Dash não renderizam com query string (`/matriculas?x=1`), porque o Dash chama `layout(x="1")` e os cinco `layout()` não aceitam parâmetros (anterior a esta feature). Falta também token CSRF nos POST administrativos (registrado em `CUTOVER.md`).
- **Ambiente**: `app/data/sistec.db` foi restaurado ao hash original após a inspeção com dados sintéticos; nenhum servidor ficou rodando.
- **Working tree**: diretórios locais não rastreados `.agents/` e `.test-tmp*/`; não os incluir sem conferir a origem.
- **Branch**: migracao-dash-gov-br.
