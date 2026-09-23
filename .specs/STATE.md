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

Estado revisado em 2026-09-22. As verificações usam `pytest` e `git`.

- **Feature**: `.specs/features/atualizacao-por-upload`
- **Phase / Task**: concluída e validada (T1–T12, todas as 4 fases).
- **Completed**: envio de pastas de ciclos/matrículas como segunda origem da mesma `Execucao` (`app/sistec/envio.py`), reusando a máquina de estados, prévia, Salvar/Descartar e publicação já existentes da baixa pelo Sistec. Rotas em `app/app.py` (`/admin/atualizar/envio`), tela em `app/templates/atualizar.html` + `app/static/js/atualizar.js`. Commits `a44a55c`..`1237cc0` (12 tarefas) + `9268f7d`/`ea76753` (versionamento do spec/design/tasks) + `2a211ef` inclui migração idempotente de schema para o tipo `envio` em `historico`.
- **Verificação final**: `.specs/features/atualizacao-por-upload/validation.md` — PASS. 661 testes passaram; sensor de discriminação com 3 mutações comportamentais em worktree isolado (portão de confirmação UPL-08, cálculo de campi ausentes UPL-07, checagem de colunas obrigatórias UPL-10), as 3 mortas pelos testes existentes. `pytest` na raiz continua inválido (coleta `APAGAR/`/`.test-tmp*/` sem permissão); usar `pytest tests/`.
- **Execução**: T1–T5 e T6–T12 implementadas por DeepSeek via `handoff-ds` (dois RUN_IDs), revisadas e commitadas por mim uma tarefa por vez (diff lido, gate rodado, commit feito). Foi preciso corrigir a integração local do `handoff-cli` no Windows: chave de API mal-formatada em `~/.handoff/config.yaml` e ausência do utilitário Unix `script` (o wrapper de PTY que o backend `type: claude` espera) — resolvido com um `script.exe` nativo compilado via `csc.exe` em `~/.local/bin/script.exe` (repassa o comando direto, sem PTY real; suficiente porque `claude --output-format stream-json` não depende de terminal). Sem esse shim, todo backend `type: claude` do handoff-cli falha nesta máquina.
- **Não fazer sem OK explícito**: `git push`, merge da branch e deploy. Nada foi enviado ao remoto.
- **Pendência fora do escopo**: as páginas do Dash não renderizam com query string (`/matriculas?x=1`); falta token CSRF nos POST administrativos (registrado em `CUTOVER.md`, pré-existente). `scripts/verificar_prontidao_cutover.py` segue em NO-GO nesta máquina só por `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH`/`CALCSISTEC_HTTPS` não configurados (ambiente local, não código).
- **Working tree**: diretórios locais não rastreados `.agents/`, `.test-tmp*/` e `.verifier-scratch-t9/` (este último de uma feature anterior); não os incluir sem conferir a origem. `~/.local/bin/script.exe` é uma correção de ambiente da máquina, fora do repositório.
- **Branch**: migracao-dash-gov-br.
