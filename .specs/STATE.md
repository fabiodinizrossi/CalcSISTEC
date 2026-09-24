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

Estado revisado em 2026-09-24 (segunda revisão no mesmo dia, após o UAT ao vivo).

### Feature atual: `correcoes-previa-uso-real`

- **Estado**: **concluída e validada**, em duas rodadas de verificação. T1–T19 + fix CPR-04 + T20/T21 (fix tasks do UAT ao vivo); Verifier independente em `validation.md` → **PASS** nas duas rodadas. `spec.md` (CPR-01..CPR-07 → `Verified`) e `tasks.md` (`Status: Done`) atualizados; `validate_state.py correcoes-previa-uso-real` → exit 0. Árvore de trabalho limpa, tudo commitado (`1f645a4`, `4c4d7cf`, `1e64a3c`, `1c2d59a`, `f49580b`, `ad474c9`). Branch `migracao-dash-gov-br`, sem push/merge/deploy.
- **Correções do UAT ao vivo (2026-09-24, dois bugs reais do fluxo envio → Salvar/Descartar)**:
  - **T20 / `f49580b` (CPR-03 AC3)**: a assinatura de origem era capturada por `preparar_versao` **antes** das escritas de campus do envio (o próprio commit `1f645a4` do CPR-04 moveu as escritas para depois de `abrir_previa`). Resultado: `interna_campus` mudava dentro da mesma requisição e o Salvar do mesmo envio respondia **409 `previa_desatualizada`** sempre. Fix em `app/app.py`: `candidato["assinatura_origem"] = calcular_assinatura_origem(db_path=DEFAULT_DB_PATH)` depois de `_cadastrar_unidades_do_envio`/`_completar_unidades_incompletas` e antes do retorno de sucesso — a garantia do CPR-04 (nada grava antes da prévia montar) continua, e o 409 de mudança **externa** continua valendo.
  - **T21 / `ad474c9` (CPR-04 / P1.3 AC4)**: a âncora da fonte da prévia (`app/data/previa.py`) usava o default `check_same_thread=True`; o Flask atende cada requisição numa thread, então o Descartar (e o Salvar bem-sucedido) quebrava em `FontePrevia.fechar()` com `sqlite3.ProgrammingError` e a rota devolvia **500 sem corpo JSON**, deixando a execução presa em `previa`. Fix: `sqlite3.connect(nome, uri=True, check_same_thread=False)` — seguro porque todo acesso já é serializado por `execucoes.com_trava`.
  - Testes novos (4): `tests/test_admin_envio.py::test_salvar_envio_que_cadastra_unidade_nova_nao_acusa_previa_desatualizada`, `::test_salvar_recusa_previa_quando_interna_campus_muda_depois_do_envio`; `tests/test_previa_fonte.py::test_fechar_em_thread_diferente_da_que_abriu`, `::test_liberar_previa_de_outra_thread_fecha_a_fonte`. Gate: **879 passed** (875 + 4), 0 failed. Sensor: 2/2 mutações matadas.
  - **Lições**: `L-009` (`spec_precision_gap`) — o edge case de `spec.md` ("`interna_campus` mudou depois da montagem → 409") não distinguia a escrita do próprio envio da mudança de outra origem; o edge case foi reescrito para explicitar "por outra origem". (A lição de processo anterior, do gate parcial, continua valendo: gate é full.)
  - **Pendências**: (1) reiniciar o processo do servidor local para os fixes valerem — o processo da porta 8050 ainda roda o código antigo e a execução `96upk3yF8YG4GzI7MwBKNg` continua presa em `previa`; (2) reenvio real dos 11 campi e conferência visual ficam com a usuária; (3) a "Publicação" feita nesta sessão gravou dados vazios de ciclos/matrículas (o Salvar real nunca teve sucesso) — estado local de teste, a ser refeito no reenvio.
  - **Gap não bloqueante (candidato a follow-up)**: os dois testes de T21 cobrem a operação de base (`FontePrevia.fechar` / `execucoes.liberar_previa` atravessando threads), não a rota `POST /admin/atualizar/execucoes/<id>/descartar` end-to-end (o sintoma de 500).
- **Fix do gap bloqueante (CPR-04 / P1.3 AC4)**: cadastro automático de campus e complemento de cidade/nome rodavam antes do `try` que prepara a fonte da prévia — erro na montagem devolvia JSON de falha, mas a escrita já tinha persistido. Corrigido no commit `1f645a4`: as duas escritas foram movidas para depois de `execucoes.abrir_previa(...)` suceder, dentro do mesmo `try` (`app/app.py`). Teste novo: `tests/test_admin_envio.py::test_falha_ao_montar_a_fonte_nao_deixa_cadastro_de_campus_gravado`.
- **UAT com CSVs reais dos 11 campi (2026-09-24, servidor local em execução, `.\scripts\testar.ps1 -SemNavegador`, login `teste@iffar.edu.br`/`teste123`)**: envio de `Downloads/01janeiro/{ciclos,matriculas}` (11 campi reais) via `/admin/atualizar/envio` — sucesso, sem 500. Bruto: 2600 ciclos, 116011 matrículas; 11 ciclos e 982 matrículas descartados por falta de modalidade (CPR-03 real); candidato final (regra PNP): **2589 ciclos, 11071 matrículas** — bate com a medição sintética anterior (`.specs/STATE.md`, handoff `previa-paginas-publicas`: "11.071 matrículas"). CPR-05 confirmado ao vivo: os 11 campi (cadastrados numa rodada anterior sem cidade/nome) tiveram `cidade`/`nome_unidade` completados a partir do CSV real, sem sobrescrever. As quatro rotas de prévia (`/admin/previa/<id>/{matriculas,eficiencia,evasao,percentuais-legais}`) responderam 200 com o conteúdo real (faixa "Prévia não publicada", navegação, filtros), sem "Prévia indisponível" nem erro de render, verificado replicando a chamada AJAX do Dash (`_dash-update-component`) via `requests` autenticado. Nenhum ERROR novo no log do servidor.
- **UAT ainda pendente (não coberto nesta rodada)**: conferência visual real no navegador (KPIs renderizados pelo callback client-side `matriculas.atualizar`/equivalentes, que depende de disparo de callback no browser) e checagem do console JS — a extensão Claude-in-Chrome não estava conectada nesta sessão em background. A execução `96upk3yF8YG4GzI7MwBKNg` ficou em estado `previa` (nada Salvo/Publicado) no servidor local ainda de pé; abra `http://localhost:8050/admin/previa/96upk3yF8YG4GzI7MwBKNg/matriculas` no navegador para concluir a conferência visual e do console, depois **Salvar na versão interna** (e **Publicar**, se aprovar) a critério da usuária.
- **Árvore de trabalho**: limpa (só `.agents/` e `nonascii.txt`, pré-existentes, não rastreados). `app/data/sistec.db` local (fora do git) agora tem os 11 campi com cidade/nome preenchidos e uma execução `previa` pendente em memória do processo do servidor de teste.

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
