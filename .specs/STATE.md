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

Estado revisado em 2026-09-24.

### Feature atual: `correcoes-previa-uso-real`

- **Estado**: **concluída e validada.** T1–T19 implementadas + fix CPR-04; Verifier independente em `validation.md` → **PASS**. `spec.md` (CPR-01..CPR-07 → `Verified`) e `tasks.md` (`Status: Done`) atualizados; `validate_state.py correcoes-previa-uso-real` → exit 0.
- **Fix do gap bloqueante (CPR-04 / P1.3 AC4)**: cadastro automático de campus e complemento de cidade/nome rodavam antes do `try` que prepara a fonte da prévia — erro na montagem devolvia JSON de falha, mas a escrita já tinha persistido. Corrigido no commit `1f645a4`: as duas escritas foram movidas para depois de `execucoes.abrir_previa(...)` suceder, dentro do mesmo `try` (`app/app.py`). Teste novo: `tests/test_admin_envio.py::test_falha_ao_montar_a_fonte_nao_deixa_cadastro_de_campus_gravado`.
- **Reverificação**: gate `pytest tests/ -q` → 875 passed, 0 failed (874 + 1 novo). Sensor de discriminação repetido em `git worktree` descartável — reverter a ordem das escritas no snapshot reproduziu o bug e o teste novo matou a mutação.
- **UAT ainda pendente**: conferir os CSVs reais de 11 campi, as quatro páginas no navegador e o console. Os testes automatizados usam dados sintéticos.
- **Árvore de trabalho**: commit `1f645a4` já feito (só `app/app.py` + `tests/test_admin_envio.py`). `validation.md`/`spec.md`/`tasks.md` desta reverificação ainda locais, não commitados. `.agents/` e `nonascii.txt` seguem não rastreados (pré-existentes).
- **Branch**: `migracao-dash-gov-br`. Sem push, merge ou deploy.

### Handoff anterior: `previa-paginas-publicas`

- **Feature**: `.specs/features/previa-paginas-publicas` (Large) — **concluída e validada** (T1–T28, `tasks.md` `Done`, `validate_state.py` → 0 erros).
- **Execução**: 3 lotes via `handoff-ds` (DeepSeek `--pro`, mesma thread `0923-ds-08`): T1–T8 (`56f5e4f`..`8ad885c`), T9–T19 (`ce75f44`..`b78bd6d`), T20–T28 (`f5b1704`..`3715bed`) + `3fd6153` (fechamento). 140 testes novos.
- **Verificação**: `validation.md` — **PASS** (`7937d3e`), Verifier em sessão DeepSeek separada (`0923-ds-12`, author ≠ verifier). 16/17 partes de AC + 4/4 edge cases com evidência; sensor expandido 9 mutações, 8 mortas. Medição com dados sintéticos (1.500 ciclos, 35.889 matrículas): preparar+abrir 0,45 s / 21,6 MiB; leitura de página 0,65 s / 35,4 MiB.
- **Gaps não bloqueantes (candidatos a follow-up)**: (1) link "Voltar para Atualizar dados" de `app/pages/previa.py` sem teste de texto/href; (2) "tabelas inalteradas" (P1.1 AC4) afirmado só por `rev_interna`/`rev_publicada`, não por conteúdo — não-escrita garantida estruturalmente por `query_only=ON`; (3) mutante sobrevivente em `fonte.fechar()` (efeito só de memória).
- **Lição de processo**: T21 `79aa3d2` e T22 `751e494` quebram 4 testes existentes isoladamente (o gate *quick* da tarefa não cobria esses arquivos); corrigidos em T23 `b99984e` sem afrouxar asserção. Em tarefas que mudam contrato de função já usada, o gate deve incluir os testes dos chamadores.
- **Gate final**: `pytest tests/ -q` → 825 passed, 2 failed **pré-existentes** (`test_eficiencia_layout_...`, `test_percentuais_layout_...`; reproduzidas no `08cf826`, `sistec.db` local vazio). Nenhuma falha nova.
- **Pendente humano**: conferência visual da faixa **Prévia não publicada** em ≥992px e em tela pequena; teste real com envio de pastas no navegador.
- **Não fazer sem OK explícito**: `git push`, merge da branch e deploy. Nada enviado ao remoto.
- **Working tree à época**: só `?? .agents/` e `?? nonascii.txt` (pré-existentes, não rastreados). `app/data/sistec.db` (ignorado) vazio de publicadas.
- **Branch**: migracao-dash-gov-br.
