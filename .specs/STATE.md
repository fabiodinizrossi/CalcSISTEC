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

Estado revisado em 2026-09-23. As verificações usam `pytest` e `git`.

- **Feature**: `.specs/features/ajustes-feedback-envio`
- **Phase / Task**: concluída e validada (escopo Medium, sem `design.md`/`tasks.md` formais). `validate_state.py ajustes-feedback-envio` → 0 erros.
- **Completed**: 3 correções pós-uso-real da tela de envio, pedidas com capturas de tela pela usuária. AFE-01: tira a caixa amarela de confirmação de preservação — `atualizar.js` sempre manda `confirmar_preservacao: true` ao salvar, o portão do servidor (`ConfirmacaoNecessaria`) continua existindo mas nunca mais dispara dessa tela. AFE-02: o resultado por arquivo do envio sai de dentro do card "Enviar pastas" para um bloco de largura inteira abaixo dos dois cards (supera `CAD-03` de `cards-atualizar-dados`, anotado nos dois specs). AFE-03: unidade presente no CSV de ciclos mas fora do cadastro de campi é cadastrada automaticamente (`campi.incluir_campus`, `id_perfil=f"envio-{codigo}"`, `origem='manual'` gravado pela própria função — reusa a proteção contra ser apagada numa recaptura futura do Sistec), em vez de só avisada; colisão de cadastro (`CampusInvalido`) não derruba o envio, só pula aquela unidade. Commits `6e8f12c`/`55828c9`/`1be1957` (AFE-01/02/03) + `9212d3c` (checklist) + `2e5ab82`/`14bfc97`/`db74bea` (correções da rodada de verificação) + `2c074ba` (validação final).
- **Verificação final**: `.specs/features/ajustes-feedback-envio/validation.md` — PASS na 2ª rodada de Verifier. 1ª rodada (`05c3f40`) deu FAIL: AFE-03 AC3 (guarda de colisão) sem nenhum teste — sensor de mutação confirmou (mutante sobrevivente, 57 testes passando sem a guarda) — mais 3 gaps menores (AC2 de largura por proxy estrutural sem nota na spec, AC4 sem asserção de render em `/admin/campi`, e um Assumption da spec citando um parâmetro `origem` que `incluir_campus` não tem). Todos os 5 gaps fechados numa rodada de correção; 2ª verificação: 12/12 ACs com evidência, sensor 5/5 mutações mortas, `pytest tests/ -q`: 685 passed.
- **Execução**: implementação e as duas rodadas de Verifier/correção via `handoff-ds` (DeepSeek), 5 sessões no total — 1 implementador (`0923-ds-01`, resumido para a correção `0923-ds-03`) e 1 verificador (`0923-ds-02`, resumido para a reverificação `0923-ds-04`) mantidos como threads separadas (author ≠ verifier). O `handoff-cli` nesta máquina crasha ao *imprimir* o resultado final no terminal Windows cp1252 (não decodifica `→`/`≥`) em toda run — cosmético, o `.result.md` sempre é escrito antes do crash; não indica falha real da sessão.
- **Não fazer sem OK explícito**: `git push`, merge da branch e deploy. Nada foi enviado ao remoto.
- **Pendência fora do escopo**: as páginas do Dash não renderizam com query string (`/matriculas?x=1`); falta token CSRF nos POST administrativos (registrado em `CUTOVER.md`, pré-existente). `scripts/verificar_prontidao_cutover.py` segue em NO-GO nesta máquina só por `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH`/`CALCSISTEC_HTTPS` não configurados (ambiente local, não código). A conferência visual de que o resultado ocupa a largura inteira em ≥992px é passo humano (declarado na própria spec, AFE-02 AC2) — ainda não confirmada no navegador real.
- **Working tree**: diretórios locais não rastreados `.agents/` (prompts de handoff — sempre remova o `.prompt.md` de trabalho depois de `handoff new --write`, não deixe acumular), `.verifier-scratch-t9/` e o arquivo solto `nonascii.txt`; não os incluir sem conferir a origem. `app/data/sistec.db` (ignorado pelo git) ganhou 11 linhas `envio-*` de um uso real da tela pela usuária durante esta sessão — confirma AFE-03 funcionando fora dos testes também.
- **Branch**: migracao-dash-gov-br.
