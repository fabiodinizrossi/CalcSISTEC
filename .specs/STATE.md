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

- **Feature**: `.specs/features/correcoes-envio-pastas`
- **Phase / Task**: concluída e validada (T1–T7, as 2 fases).
- **Completed**: corrige os dois defeitos do primeiro uso real de `atualizacao-por-upload`. (1) UI: o `.br-upload` do gov.br DS escondia o `<input>` (`display:none`) sem widget próprio visível — trocado por marcação própria (`app/templates/atualizar.html:71-81`, `button` + input `hidden` + status anunciado) e lógica em `app/static/js/atualizar.js` (`CAMPOS_PASTA`, `contarSelecao`, `renderizarSelecao`), sem chamada de rede nem animação de "carregando" antes do envio real. (2) Leitura: `ler_planilha` (`app/sistec/colunas.py`) decodificava `cp1252` em modo estrito — qualquer byte fora do cp1252 em QUALQUER coluna (mesmo descartada) abortava o arquivo inteiro; corrigido com `encoding_errors="replace"`. Reproduzido e confirmado com um export real do Sistec (byte `0x81` em `NO_MAE_ALUNO`, coluna PII já descartada por `aplicar_permissao`). Commits `7717641`..`83b768b` (T1–T7) + `365470d` (spec/design) + `c838393` (teste que fecha o mutante sobrevivente do Verifier).
- **Verificação final**: `.specs/features/correcoes-envio-pastas/validation.md` — PASS. 683 testes passaram; sensor de discriminação com 3 mutações em worktree isolado — 2 mortas na 1ª rodada, 1 sobreviveu (`renderizarSelecao` nunca testada com 0 arquivos) e foi corrigida com um teste novo antes de fechar. Um gap de precisão de spec identificado e corrigido na própria implementação: a AC sobre "linha com campo a mais/a menos" não se sustenta no pandas 2.3.0 com `usecols` (tolera silenciosamente); substituída por defeito estrutural real (aspas desbalanceadas). Duas lições candidatas registradas em `.specs/lessons.json` (L-006, L-007).
- **Execução**: T1–T7 implementadas por DeepSeek via `handoff-ds` num único RUN_ID, revisadas e aceitas por mim sem necessidade de intervenção manual em nenhum commit (diferente da feature anterior — os commits saíram corretos de primeira). A infra do `handoff-cli` (chave de API, shim `script.exe`) documentada no handoff anterior segue funcionando.
- **Não fazer sem OK explícito**: `git push`, merge da branch e deploy. Nada foi enviado ao remoto.
- **Pendência fora do escopo**: as páginas do Dash não renderizam com query string (`/matriculas?x=1`); falta token CSRF nos POST administrativos (registrado em `CUTOVER.md`, pré-existente). `scripts/verificar_prontidao_cutover.py` segue em NO-GO nesta máquina só por `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH`/`CALCSISTEC_HTTPS` não configurados (ambiente local, não código). A funcionalidade de envio ainda não foi testada de ponta a ponta pela usuária no navegador real após esta correção — vale confirmar visualmente antes de considerar encerrado.
- **Working tree**: diretórios locais não rastreados `.agents/`, `.test-tmp*/` e `.verifier-scratch-t9/` (de uma feature anterior); não os incluir sem conferir a origem. `~/.local/bin/script.exe` é uma correção de ambiente da máquina, fora do repositório.
- **Branch**: migracao-dash-gov-br.
