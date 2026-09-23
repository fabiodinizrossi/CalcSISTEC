# Prévia das páginas públicas antes de salvar Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/previa-paginas-publicas/design.md`
**Status**: Draft

---

## Test Coverage Matrix

> Gerada do código, das diretrizes do projeto e da spec — confirmar antes do Execute. Diretrizes encontradas: `.specs/PROJECT_RULES.md` (Princípio IV: teste `pytest` é gate de mudança em `app/domain/`, `app/data/` e `app/sistec/`), `AGENTS.md` (limpar temporários; nunca deixar `.test-*`/`.pytest_cache/`/`.verifier-scratch-*` no repositório) e `spec.md` §"Project Rules & References" (Princípio IV: paridade, acesso, ciclo de vida e falhas como gate). Não há `pytest.ini`, `pyproject.toml`, `tox.ini`, `Makefile`, `setup.cfg` nem configuração de linter/formatador no repositório — a matriz registra "nenhum configurado" em vez de inventar um comando.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Preparação de dados (`app/data/ingest.py`) | unit | Todos os ramos de `preparar_versao` e da assinatura de origem; 1:1 com PVP-03/PVP-04; campus preservado, `RISK-002` (vazio, NaN, data nula) e determinismo da assinatura | `tests/test_previa_candidato.py` | `python -m pytest tests/test_previa_candidato.py -q` |
| Fonte em memória (`app/data/previa.py`) | unit | Tabelas do candidato + `campus` publicado + ano-base de `config`; leitura recusa escrita; `abrir_leitura`/`fechar` idempotentes; sem arquivo em disco | `tests/test_previa_fonte.py` | `python -m pytest tests/test_previa_fonte.py -q` |
| Guardião de execução (`app/sistec/execucoes.py`) | unit | Todos os ramos de posse, origem e estado; trava por execução; liberação da fonte; bloqueio por falha de página | `tests/test_execucoes_previa.py` | `python -m pytest tests/test_execucoes_previa.py -q` |
| Consulta (`app/data/consulta.py`) | unit | Cada uma das 5 funções com conexão explícita e sem ela; sem conexão continua lendo o banco publicado | `tests/test_consulta.py` | `python -m pytest tests/test_consulta.py -q` |
| Transações de versão (`app/data/versoes.py`) | unit | Assinatura igual grava, diferente devolve conflito sem gravar; rollback integral em falha no meio da inserção; `publicar`/`desfazer` inalterados | `tests/test_versoes.py` | `python -m pytest tests/test_versoes.py -q` |
| Páginas Dash (`app/pages/*.py`) | integration | As 4 páginas em caminho público e em caminho de prévia: layout, KPIs, tabelas, filtros, estados vazios e contexto inválido | `tests/test_paginas_publicas.py`, `tests/test_previa_*.py` | `python -m pytest tests/ -q` |
| Rotas administrativas e guarda (`app/app.py`) | integration | Cada rota no escopo: caminho feliz + redirecionamento sem sessão + `404`/`409` + envio sem memória | `tests/test_admin_*.py` | `python -m pytest tests/ -q` |
| Template e script da tela (`app/templates/`, `app/static/js/`) | unit | Marcação e comportamento afirmados por asserção de texto, no padrão dos arquivos existentes | `tests/test_tela_atualizar_envio.py`, `tests/test_js_envio.py` | `python -m pytest tests/ -q` |
| Autorização, posse e ciclo de vida (atravessa `app/app.py` e `app/sistec/execucoes.py`) | integration | Sem login, sessão alheia, identificador forjado, URL antiga após Salvar/Descartar, execução perdida e ausência de PII | `tests/test_previa_acesso.py` | `python -m pytest tests/ -q` |
| Paridade e estados (atravessa dados, versões e páginas) | integration | As 4 páginas da prévia iguais às públicas depois de Salvar/Publicar em banco isolado, inclusive sem publicação inicial, com campus preservado e com `RISK-002`; revisões inalteradas por abrir/recarregar; assinatura alterada → `409` | `tests/test_previa_paridade.py`, `tests/test_previa_estado.py` | `python -m pytest tests/ -q` |
| Documentação (`README.md`, `TESTAR.md`) | none | - (build gate apenas) | - | build gate apenas |

## Gate Check Commands

> Gerados do código — confirmar antes do Execute. `pytest` na raiz é inválido: ele tenta coletar `APAGAR/` e diretórios arquivados sem permissão de leitura (registrado em `.specs/STATE.md` e em `atualizacao-por-upload/tasks.md`). Todo comando aponta para `tests/`. Linter/formatador: nenhum configurado no repositório.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Depois de tarefa com testes unitários apenas | `python -m pytest tests/<arquivo_do_teste> -q` |
| Full | Depois de tarefa com teste de integração de rota, de callback ou de tela | `python -m pytest tests/ -q` |
| Build | No fim de cada fase e em tarefa só de documentação | `python -m pytest tests/ -q` |

---

## Execution Plan

As fases são ordenadas e rodam em sequência — cada fase termina antes da seguinte, e as tarefas dentro de uma fase executam em ordem.

### Phase 1: Candidato preparado e fonte em memória (sem escrita)

```
T1 → T2
```

### Phase 2: Guardião de sessão, posse e estado

```
T3 → T4 → T5 → T6 → T7 → T8
```

### Phase 3: Consulta com conexão explícita

```
T9 → T10
```

### Phase 4: Páginas públicas compartilhadas

```
T11 → T12 → T13 → T14
```

### Phase 5: Página de prévia e navegação administrativa

```
T15

T16    (usa T7 e as quatro páginas: T11, T12, T13, T14)

T17 → T19

T18 → T19
```

### Phase 6: Salvar com conferência da origem

```
T20 → T21 → T22 → T23
```

### Phase 7: Testes transversais (paridade, acesso e estado)

```
T24

T25

T26
```

### Phase 8: Documentação do fluxo

```
T27 → T28
```

---

## Task Breakdown

### T1: Separar a preparação do candidato da gravação

**What**: extrair de `montar_versao_interna` uma função `preparar_versao(conjunto, campi_falhos, db_path=DEFAULT_DB_PATH, ano_base=None)` que devolve `{"tabelas", "resumo", "ano_base", "assinatura_origem"}` sem gravar nada, mais `calcular_assinatura_origem(db_path)`; `montar_versao_interna` passa a chamar as duas e segue sendo o caminho da baixa direta.
**Where**: `app/data/ingest.py`
**Depends on**: None
**Reuses**: `app/data/ingest.py:133-250` (`_ler_mantidos`, `_cursos_e_ciclos_do_conjunto`, `casar_fatores`, `salvar_interna`), `app/data/consulta.ano_base_ativo`
**Requirement**: PVP-03, PVP-04

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `preparar_versao` devolve as quatro tabelas (`cursos`, `ciclos`, `matriculas`, `matriculas_eficiencia`) já com os campi preservados concatenados e os fatores casados, sem abrir conexão de escrita
- [x] `ano_base=None` lê `config.ano_base` do banco (`consulta.ano_base_ativo`); com valor explícito, usa o valor recebido
- [x] `calcular_assinatura_origem` devolve `rev_interna`, `rev_publicada`, `ano_base` e um resumo determinístico de `interna_fatores` e do `campus` publicado, estável entre chamadas
- [x] `montar_versao_interna` mantém assinatura e retorno atuais e continua gravando por `salvar_interna`
- [x] Testes: `tests/test_previa_candidato.py` cobre tabelas iguais às gravadas para os mesmos CSVs, campus preservado, `RISK-002` (vazio, NaN, data nula) e determinismo da assinatura
- [x] Gate check passes: `python -m pytest tests/test_previa_candidato.py -q` e `python -m pytest tests/test_parity_dominio.py -q`
- [x] Test count: ≥ 6 testes novos; nenhum teste existente removido

**Status**: Done -- commit `72607a8`.

**Tests**: unit
**Gate**: quick

**Commit**: `refactor(dados): separa a preparação do candidato da gravação da versão interna`

---

### T2: Fonte candidata em SQLite nomeado em memória

**What**: criar `abrir_fonte_previa(candidato, campus_publico, db_path=DEFAULT_DB_PATH)` e a classe `FontePrevia` com `abrir_leitura()` e `fechar()`, sobre um banco `file:previa-<id>?mode=memory&cache=shared` mantido vivo por uma conexão âncora.
**Where**: `app/data/previa.py` (módulo novo)
**Depends on**: T1
**Reuses**: `app/data/schema.py` (`SCHEMA_PUBLICAS_SQL`, `SCHEMA_CONFIG_SQL`, `SCHEMA_ESTADO_VERSOES_SQL`), padrão de inserção em lotes de `app/data/versoes.py`
**Requirement**: PVP-03, PVP-04

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] O banco da fonte recebe as quatro tabelas do candidato, o `campus` publicado, a tabela `config` com o `ano_base` do candidato e `estado_versoes` com `publicada_em` vazio
- [x] A conexão âncora usa `sqlite3.connect(..., uri=True)` e permanece aberta enquanto a fonte existir (o banco nomeado em memória morre ao fechar a última conexão)
- [x] `abrir_leitura()` devolve conexão nova com `PRAGMA query_only=ON` e `PRAGMA temp_store=MEMORY`; escrita por essa conexão falha
- [x] `fechar()` é idempotente e não cria arquivo nenhum em disco
- [x] Nenhuma coluna pessoal entra na fonte (as tabelas vêm do candidato, já sem PII)
- [x] Testes: `tests/test_previa_fonte.py` cobre as quatro tabelas com contagens corretas, leitura somente, `fechar()` repetido e ausência de arquivo temporário
- [x] Gate check passes: `python -m pytest tests/test_previa_fonte.py -q`
- [x] Test count: ≥ 6 testes novos

**Status**: Done -- commit `3c7484a`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(dados): guarda o candidato da prévia em SQLite nomeado em memória`

---

### T3: Identificador de sessão no login administrativo

**What**: gravar um identificador opaco de sessão (`sessao_id`) no login e expor `sessao_id_atual()`, para vincular a execução à sessão que a iniciou.
**Where**: `app/auth.py`
**Depends on**: None
**Reuses**: `app/auth.py:61-77` (`autenticar_sessao`, `encerrar_sessao`), `secrets.token_urlsafe`
**Requirement**: PVP-07

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `autenticar_sessao` grava `flask.session["sessao_id"] = secrets.token_urlsafe(16)` a cada login bem-sucedido
- [x] `sessao_id_atual()` devolve o identificador da sessão atual e cria um quando ausente, sem nunca devolver vazio
- [x] `encerrar_sessao` remove o `sessao_id` junto com `admin_autenticado` e `admin_usuario`
- [x] Testes: cobrir login grava, logout remove, sessão nova não reaproveita o identificador anterior
- [x] Gate check passes: `python -m pytest tests/test_admin_paginas.py tests/test_admin_envio.py -q`
- [x] Test count: ≥ 3 testes novos

**Status**: Done -- commit `20c1e00`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(auth): identifica a sessão administrativa dona do envio`

---

### T4: Guardião de posse, origem e estado na execução

**What**: adicionar `Execucao.sessao_dona`, aceitar `sessao_id` em `criar_execucao_envio` e implementar `obter_previa(execucao_id, sessao_id)`, que recusa qualquer combinação fora de dono + `origem == "envio"` + `estado == "previa"` levantando `PreviaIndisponivel`.
**Where**: `app/sistec/execucoes.py`
**Depends on**: T3
**Reuses**: `app/sistec/execucoes.py:60-104` (`Execucao`), `:121-161` (`_REGISTRO`, `criar_execucao_envio`), `:181-191` (`obter_por_token`, `obter_do_admin`), `secrets.compare_digest`
**Requirement**: PVP-07

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `PreviaIndisponivel` é uma exceção própria do módulo, distinta de `ExecucaoInvalida`
- [x] `obter_previa` recusa: execução inexistente, `sessao_dona` diferente (inclusive outra sessão do mesmo e-mail), `origem != "envio"`, estado terminal ou estado diferente de `previa`
- [x] A recusa nunca devolve nem abre a fonte candidata nem cai no banco publicado
- [x] Registro limpo (reinício do processo) devolve `PreviaIndisponivel`
- [x] Testes: `tests/test_execucoes_previa.py` cobre cada motivo de recusa e o caminho autorizado
- [x] Gate check passes: `python -m pytest tests/test_execucoes_previa.py -q`
- [x] Test count: ≥ 6 testes novos

**Status**: Done -- commit `287d5cb`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(execucoes): valida dono, origem e estado da prévia`

---

### T5: Trava por execução entre leitura e transição de estado

**What**: dar a cada `Execucao` uma trava própria (`Execucao.lock`) e usá-la em toda leitura da fonte candidata e em `salvar`/`descartar`, para que Salvar ou Descartar não fechem a fonte no meio de um callback.
**Where**: `app/sistec/execucoes.py`
**Depends on**: T4
**Reuses**: `_LOCK` do registro (`app/sistec/execucoes.py:123`), `threading.Lock`
**Requirement**: PVP-07, PVP-08

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `Execucao` cria a trava na construção; `Execucao.lock` é reutilizável e não substituída por `criar_execucao_envio`
- [x] Existe um context manager (`com_trava(execucao)`) usado pela validação + leitura e pelas transições `salvar`/`salvar_candidato`/`descartar`
- [x] Nenhum caminho toma a trava do registro `_LOCK` e a trava da execução ao mesmo tempo em ordem invertida (evitar deadlock)
- [x] Testes: cobrir leitura concorrente com Descartar (thread de leitura termina antes do fechamento) e ausência de deadlock entre registro e execução
- [x] Gate check passes: `python -m pytest tests/test_execucoes_previa.py -q`
- [x] Test count: ≥ 3 testes novos

**Status**: Done -- commit `606b374`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(execucoes): serializa leitura e transição de estado da prévia`

---

### T6: Abrir e liberar a fonte da prévia na execução

**What**: adicionar `abrir_previa(execucao, candidato, db_path=DEFAULT_DB_PATH)` (cria a fonte com o `campus` publicado e guarda `execucao.previa_fonte`/`execucao.candidato`) e `liberar_previa(execucao)`, e fazer `descartar` liberar a fonte.
**Where**: `app/sistec/execucoes.py`
**Depends on**: T5
**Reuses**: `app/data/previa.abrir_fonte_previa` (T2), `app/sistec/execucoes.py:320-323` (`descartar`)
**Requirement**: PVP-03, PVP-08

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `abrir_previa` lê `campus` do banco publicado e monta a fonte do candidato; chamadas repetidas para a mesma execução não criam uma segunda fonte
- [x] `liberar_previa` fecha a fonte, limpa `previa_fonte` e é idempotente
- [x] `descartar` libera a fonte antes de marcar `descartada` e continua recusando fora do estado `previa`
- [x] Depois de abrir a fonte, o envio libera os `DataFrame` por arquivo (`par.df = None`) e o dicionário consolidado pesado, conservando o resumo e a amostra usados pelo polling
- [x] Testes: cobrir fonte viva após abrir, memória liberada após descartar, descartar repetido e `campi_falhos`/resumo preservados
- [x] Gate check passes: `python -m pytest tests/test_execucoes_previa.py -q`
- [x] Test count: ≥ 5 testes novos

**Status**: Done -- commit `8eb0b8b`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(execucoes): abre e libera a fonte candidata da prévia`

---

### T7: Contexto de leitura da prévia para páginas e callbacks

**What**: implementar `abrir_leitura_previa(execucao_id, sessao_id)`, que valida o contexto pela mesma regra de `obter_previa` e devolve um `ContextoLeitura` com execução, conexão de leitura e ano-base, para uso por todo layout e callback privado.
**Where**: `app/sistec/execucoes.py`
**Depends on**: T6
**Reuses**: `obter_previa` (T4), `com_trava` (T5), `FontePrevia.abrir_leitura` (T2)
**Requirement**: PVP-04, PVP-07

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `ContextoLeitura` expõe `execucao`, `conn` e `ano_base` (o mesmo ano-base gravado no candidato)
- [x] A validação acontece sob a trava da execução e antes de qualquer consulta; contexto inválido levanta `PreviaIndisponivel` e não devolve conexão
- [x] Toda leitura feita por um callback passa por esta função — não existe atalho que leia a fonte sem validar
- [x] Nenhum contexto devolve a conexão do banco publicado
- [x] Testes: cobrir contexto válido, sessão alheia, estado terminal e fonte já fechada
- [x] Gate check passes: `python -m pytest tests/test_execucoes_previa.py -q`
- [x] Test count: ≥ 4 testes novos

**Status**: Done -- commit `ceb6c06`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(execucoes): entrega contexto de leitura validado para a prévia`

---

### T8: Registro de falha de página e bloqueio do Salvar

**What**: registrar as páginas da prévia que falharam ao calcular ou renderizar, com `registrar_falha_pagina`, `limpar_falha_pagina` e `paginas_com_falha`, e fazer a gravação de um envio recusar enquanto houver falha.
**Where**: `app/sistec/execucoes.py`
**Depends on**: T7
**Reuses**: `Execucao.previa`/`campi_falhos`, `ExecucaoInvalida`, `ConfirmacaoNecessaria`
**Requirement**: PVP-09

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `falhas_paginas` é um conjunto por execução, começando vazio
- [x] Uma renderização bem-sucedida da mesma página limpa a falha anterior
- [x] `salvar_candidato`/`salvar` de um envio levanta `PreviaIncompleta` (exceção própria, com a lista de páginas) enquanto houver falha; a baixa direta não é afetada
- [x] Descartar continua liberando a prévia mesmo com falha registrada
- [x] Testes: cobrir registrar, limpar ao renderizar de novo, bloqueio do Salvar com uma e com duas páginas falhas
- [x] Gate check passes: `python -m pytest tests/test_execucoes_previa.py -q`
- [x] Test count: ≥ 4 testes novos

**Status**: Done -- commit `47f2adb`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(execucoes): bloqueia o salvar enquanto houver página da prévia com falha`

---

### T9: Conexão explícita nas funções de estado e configuração da consulta

**What**: aceitar `conn` opcional em `dataset_disponivel`, `ano_base_ativo` e `data_ultima_publicacao`; sem conexão, cada uma segue abrindo o banco publicado como hoje.
**Where**: `app/data/consulta.py`
**Depends on**: None
**Reuses**: `app/data/consulta.py:19-59`, `app/data/schema.get_connection`
**Requirement**: PVP-04, PVP-05

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] As três funções aceitam `conn=None` como último parâmetro (os chamadores atuais, que não passam argumentos, continuam válidos)
- [x] Com `conn` explícita, a função não abre nem fecha conexão própria e não toca `DEFAULT_DB_PATH`
- [x] Sem `conn`, o comportamento e o fechamento de conexão permanecem os atuais
- [x] Testes: `tests/test_consulta.py` cobre cada função com e sem conexão explícita, inclusive `ano_base` lido de `config`
- [x] Gate check passes: `python -m pytest tests/test_consulta.py -q`
- [x] Test count: ≥ 5 testes novos

**Status**: Done -- commit `dbf2e1c`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(consulta): aceita conexão explícita nas leituras de estado`

---

### T10: Conexão explícita nas cargas de matrículas e eficiência

**What**: aceitar `conn` opcional em `carregar_matriculas` e `carregar_eficiencia`, para que a prévia rode exatamente o mesmo SQL contra a fonte candidata.
**Where**: `app/data/consulta.py`
**Depends on**: T9
**Reuses**: `app/data/consulta.py:62-111` (os dois `pd.read_sql_query`), padrão definido em T9
**Requirement**: PVP-04

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] As duas funções aceitam `conn=None` e, sem argumento, mantêm o comportamento atual
- [x] Com `conn` explícita, devolvem as mesmas colunas e os mesmos `parse_dates` do caminho público
- [x] Testes: `tests/test_consulta.py` compara o resultado das duas funções na fonte da prévia com o do banco publicado para os mesmos dados
- [x] Gate check passes: `python -m pytest tests/test_consulta.py -q`
- [x] Test count: ≥ 3 testes novos

**Status**: Done -- commit `b9372d7`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(consulta): aceita conexão explícita nas cargas de matrículas e eficiência`

---

### T11: Página Matrículas lê a fonte da prévia

**What**: dar a `layout` o parâmetro `preview_id=None` e fazer cada callback resolver o contexto (`abrir_leitura_previa`) quando houver prévia, sem duplicar a página: o caminho público continua lendo o banco publicado e ignora qualquer identificador forjado.
**Where**: `app/pages/matriculas.py`
**Depends on**: None
**Reuses**: `app/data/consulta` (T9, T10), `app/sistec/execucoes.abrir_leitura_previa` (T7), `app/auth.sessao_id_atual` (T3), `app/components/mensagem.mensagem_ds`
**Requirement**: PVP-01, PVP-02, PVP-04, PVP-06

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `layout(preview_id=None)` sem `preview_id` produz exatamente a página pública atual (testes existentes de `tests/test_paginas_publicas.py` seguem passando)
- [x] Com `preview_id`, o layout e os callbacks leem pela conexão da fonte e usam o ano-base dela; o rótulo "Atualizado em" é omitido e a mensagem "Ainda não há dados publicados." não aparece
- [x] O `preview_id` chega aos callbacks por `State` (um `dcc.Store` por página), nunca por URL nem por dado vindo do cliente sem validação
- [x] `PreviaIndisponivel` no callback devolve estado vazio/erro e nunca dados públicos; filtro sem linhas mantém "Sem dados para o eixo selecionado."
- [x] Testes: cobrir layout público, layout de prévia, callback com prévia válida, callback com identificador forjado e filtro vazio nos dois caminhos
- [x] Gate check passes: `python -m pytest tests/test_paginas_publicas.py tests/test_previa_callback_matriculas.py -q`
- [x] Test count: ≥ 6 testes novos

**Status**: Done -- commit `2d51803`.

**Tests**: integration
**Gate**: full

**Commit**: `feat(paginas): matrículas lê a fonte da prévia mantendo o caminho público`

---

### T12: Página Eficiência Acadêmica lê a fonte da prévia

**What**: replicar em `layout` e nos callbacks da Eficiência Acadêmica o mesmo contrato de `preview_id`/`State` definido em T11, sem duplicar a página.
**Where**: `app/pages/eficiencia.py`
**Depends on**: T11
**Reuses**: `app/pages/matriculas.py` (T11 como referência), `app/components/painel_publico`, `app/domain/eficiencia.iea`
**Requirement**: PVP-01, PVP-02, PVP-04, PVP-06

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] Layout e callbacks públicos continuam idênticos (testes atuais passam sem alteração)
- [x] Com `preview_id`, KPIs e matriz saem da fonte candidata com o ano-base dela, sem carimbo de publicação
- [x] Identificador forjado ou estado terminal devolve erro/vazio, nunca dados públicos
- [x] Testes: cobrir os dois caminhos e a prévia sem publicação inicial
- [x] Gate check passes: `python -m pytest tests/ -q`
- [x] Test count: ≥ 4 testes novos

**Status**: Done -- commit `db92c34`.

**Tests**: integration
**Gate**: full

**Commit**: `feat(paginas): eficiência lê a fonte da prévia mantendo o caminho público`

---

### T13: Página Taxa de Evasão Anual lê a fonte da prévia

**What**: replicar o mesmo contrato de `preview_id`/`State` na Taxa de Evasão Anual.
**Where**: `app/pages/evasao.py`
**Depends on**: T12
**Reuses**: `app/pages/matriculas.py` (T11), `app/domain/matriculas.taxa_evasao`
**Requirement**: PVP-01, PVP-02, PVP-04, PVP-06

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Layout e callbacks públicos continuam idênticos
- [ ] Com `preview_id`, os indicadores e a matriz saem da fonte candidata com o ano-base dela
- [ ] Identificador forjado ou estado terminal devolve erro/vazio, nunca dados públicos
- [ ] Testes: cobrir os dois caminhos e filtro sem linhas
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 4 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `feat(paginas): evasão lê a fonte da prévia mantendo o caminho público`

---

### T14: Página Percentuais Legais lê a fonte da prévia

**What**: replicar o mesmo contrato de `preview_id`/`State` em Percentuais Legais.
**Where**: `app/pages/percentuais_legais.py`
**Depends on**: T13
**Reuses**: `app/pages/matriculas.py` (T11), `app/domain/percentuais_legais`
**Requirement**: PVP-01, PVP-02, PVP-04, PVP-06

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Layout e callbacks públicos continuam idênticos
- [ ] Com `preview_id`, medidores e tabelas saem da fonte candidata com o ano-base dela
- [ ] Identificador forjado ou estado terminal devolve erro/vazio, nunca dados públicos
- [ ] Testes: cobrir os dois caminhos e o caso de eixo sem linhas
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 4 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `feat(paginas): percentuais legais leem a fonte da prévia`

---

### T15: Guarda de autenticação para as rotas de prévia

**What**: barrar no servidor Flask toda requisição a `/admin/previa/...` sem sessão autenticada, redirecionando para `/admin/login` antes de o Dash montar qualquer layout.
**Where**: `app/app.py`
**Depends on**: None
**Reuses**: `app/app.py:225-237` (`_exigir_instalacao` como padrão de `before_request`), `app/auth.esta_autenticado`
**Requirement**: PVP-07

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] `before_request` redireciona `/admin/previa/<execucao_id>/<pagina>` sem sessão para `/admin/login`, sem corpo com dados da prévia
- [ ] Rotas públicas e as demais rotas administrativas mantêm o comportamento atual
- [ ] O guarda não substitui a validação de posse da T4/T7 — os dois valem, em camadas diferentes
- [ ] Testes: cobrir GET sem sessão (redireciona) e com sessão (não interfere)
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 2 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `feat(admin): exige sessão nas rotas de prévia`

---

### T16: Página Dash da prévia com aviso, navegação e conteúdo público

**What**: criar a página dinâmica de prévia que valida o contexto, mostra a faixa **Prévia não publicada**, os avisos do envio e a navegação entre as quatro páginas, e chama o layout público correspondente com `preview_id`.
**Where**: `app/pages/previa.py` (arquivo novo)
**Depends on**: T7, T11, T12, T13, T14
**Reuses**: `app/pages/{matriculas,eficiencia,evasao,percentuais_legais}.py` (T11–T14), `app/shell.contexto_shell` (migalhas e menu administrativos), `app/components/mensagem.mensagem_ds`, `Execucao.campi_falhos`/`campi_cadastrados_automaticamente`/`matriculas_orfas`/`arquivos_ignorados`
**Requirement**: PVP-01, PVP-02, PVP-05

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] `dash.register_page(__name__, path="/admin/previa/<execucao_id>/<pagina>")` e `layout(execucao_id=None, pagina=None)` recebem as variáveis de caminho do Dash Pages
- [ ] Slug desconhecido, execução perdida, sessão alheia ou estado terminal mostram **Prévia indisponível** com voltar para **Atualizar dados**; nunca a mensagem pública de ausência de dados nem dados publicados
- [ ] A faixa **Prévia não publicada** identifica os dados como não publicados e traz as quatro páginas de prévia mais o retorno a **Atualizar dados**
- [ ] Os avisos de campi preservados, unidades cadastradas pelo envio, matrículas órfãs e arquivos ignorados aparecem quando existirem
- [ ] Os controles **Salvar na versão interna** e **Descartar** continuam disponíveis no fluxo administrativo (nenhuma ação nova aqui)
- [ ] Uma falha ao calcular ou renderizar a página registra `registrar_falha_pagina` (T8) e mostra o nome da página com erro acionável
- [ ] Testes: cobrir as quatro páginas, slug inválido, contexto inválido, avisos e falha de renderização
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 8 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `feat(previa): renderiza as quatro páginas públicas com aviso de não publicada`

---

### T17: O envio prepara o candidato e abre a prévia

**What**: ao fim do envio de pastas, preparar o candidato sem gravar, abrir a fonte da prévia na execução e vincular a execução à sessão que a iniciou.
**Where**: `app/app.py`
**Depends on**: T3, T6
**Reuses**: `admin_atualizar_envio` (`app/app.py:367-439`), `app/data/ingest.preparar_versao` (T1), `execucoes.abrir_previa` (T6), `app/data/consulta.ano_base_ativo`
**Requirement**: PVP-01, PVP-03

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] `criar_execucao_envio` recebe `sessao_id=sessao_id_atual()`
- [ ] Depois de `definir_campi_preservados`, a rota prepara o candidato com `config.ano_base` e chama `abrir_previa`; a ordem preserva o cadastro automático de unidades e os avisos já existentes
- [ ] Falha ao montar a fonte (memória insuficiente) devolve erro próprio na resposta, mantém a execução pendente e deixa **Descartar** disponível; nada é gravado na versão interna ou pública
- [ ] O caminho de consolidação inválida continua sem oferecer prévia e mantém o erro visível
- [ ] O `DataFrame` por arquivo e o consolidado pesado são liberados depois de montar a fonte, preservando o resumo e a amostra do polling
- [ ] Testes: cobrir envio válido cria fonte, consolidação inválida não cria, e falha de memória simulada (`monkeypatch` que levanta `MemoryError`) devolve o erro sem gravar
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 4 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `feat(admin): prepara o candidato e abre a prévia ao fim do envio`

---

### T18: Bloco de prévia com as quatro páginas na tela Atualizar dados

**What**: acrescentar na área de prévia da tela administrativa a faixa **Prévia não publicada** e os quatro links para as páginas da prévia, mantendo **Salvar na versão interna** e **Descartar**.
**Where**: `app/templates/atualizar.html`
**Depends on**: None
**Reuses**: `app/templates/atualizar.html:112-128` (`#atualizar-previa`), classes `br-message`/`br-button` do gov.br DS (`AD-001` a `AD-005`), `app/templates/shell/` para o shell
**Requirement**: PVP-01, PVP-02

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Existe um contêiner com identificador próprio e quatro links (Matrículas, Eficiência Acadêmica, Taxa de Evasão Anual, Percentuais Legais), cada um com `data-pagina` para o script preencher o `href`
- [ ] A faixa de aviso diz que os dados são uma prévia não publicada e que nada foi salvo
- [ ] Salvar e Descartar continuam na mesma área, com os identificadores atuais
- [ ] A marcação usa o shell e os tokens do gov.br DS, sem cor hexadecimal literal (`AD-003`)
- [ ] Testes: `tests/test_tela_atualizar_envio.py` afirma a marcação e os identificadores lidos como HTML
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 3 testes novos

**Tests**: unit
**Gate**: full

**Commit**: `feat(ui): oferece as quatro páginas da prévia na tela Atualizar dados`

---

### T19: Script preenche e mostra os links da prévia

**What**: preencher o `href` dos quatro links a partir do `execucao_id` do polling e mostrar o bloco só quando o envio estiver em `previa`.
**Where**: `app/static/js/atualizar.js`
**Depends on**: T17, T18
**Reuses**: `renderizarPrevia` (`app/static/js/atualizar.js:181-217`), o estado do polling `GET /admin/atualizar/execucao`
**Requirement**: PVP-01, PVP-02

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Os quatro `href` seguem o formato `/admin/previa/<execucao_id>/<slug>`, com o `execucao_id` recebido do polling
- [ ] O bloco fica oculto fora do estado `previa` e no envio de origem `baixa`
- [ ] Nenhum dado da prévia é buscado pelo script além do que o polling já devolve
- [ ] Testes: `tests/test_js_envio.py` cobre href montado, bloco oculto fora de `previa` e ausência de nova chamada de rede
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 3 testes novos

**Tests**: unit
**Gate**: full

**Commit**: `feat(ui): liga os links da prévia ao estado do envio`

---

### T20: Assinatura de origem transacional e gravação em lotes

**What**: estender `salvar_interna` com `assinatura_esperada` opcional, conferida dentro do `BEGIN IMMEDIATE` antes de apagar ou inserir qualquer linha, e trocar `DataFrame.to_sql` por `sqlite3.executemany` em lotes com colunas explícitas e nulos normalizados; `publicar`, `desfazer` e `aplicar_publico` ficam inalterados.
**Where**: `app/data/versoes.py`
**Depends on**: None
**Reuses**: `app/data/versoes.py:32-55` (`salvar_interna`, `_ORDEM_DELETE_BAIXA`/`_ORDEM_INSERT_BAIXA`), `app/data/ingest.calcular_assinatura_origem` (T1)
**Requirement**: PVP-03, PVP-10

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Assinatura igual grava como hoje e incrementa `rev_interna` uma única vez
- [ ] Assinatura diferente (revisões, ano-base, `interna_fatores` ou `campus` publicado) faz `rollback` e levanta uma exceção própria `ConflitoDeConferencia`, sem trocar nenhuma tabela
- [ ] A comparação roda depois de `BEGIN IMMEDIATE` e antes do primeiro `DELETE`
- [ ] Gravação por `executemany` em lotes limitados, com colunas explícitas e `None` para NaN/NaT; falha no meio de um lote faz rollback integral e deixa `rev_interna` inalterada
- [ ] `assinatura_esperada=None` mantém o comportamento usado pela baixa direta
- [ ] `publicar`/`desfazer`/`aplicar_publico` sem alteração de código nem de teste
- [ ] Testes: `tests/test_versoes.py` cobre assinatura igual, assinatura divergente, rollback em falha intermediária (dublê que levanta no meio) e `NaN`/data nula gravados como `NULL`
- [ ] Gate check passes: `python -m pytest tests/test_versoes.py tests/test_schema_v2.py -q`
- [ ] Test count: ≥ 6 testes novos

**Tests**: unit
**Gate**: quick

**Commit**: `feat(versoes): confere a assinatura de origem na transação e grava em lotes`

---

### T21: Salvar aproveita o candidato conferido e encerra a prévia

**What**: fazer o caminho de envio de `salvar` persistir as tabelas já preparadas e conferidas, com o ano-base e a assinatura do candidato, encerrando a prévia e liberando a fonte no sucesso.
**Where**: `app/sistec/execucoes.py`
**Depends on**: T20
**Reuses**: `app/sistec/execucoes.py:305-317` (`salvar`), `app/data/versoes.salvar_interna` (T20), `liberar_previa` (T6)
**Requirement**: PVP-04, PVP-08, PVP-10

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] O envio grava exatamente `execucao.candidato.tabelas` com `assinatura_esperada=candidato.assinatura_origem` e `ano_base=candidato.ano_base`; a baixa direta continua por `montar_versao_interna`
- [ ] `ConflitoDeConferencia` vira `PreviaDesatualizada` (exceção própria) e a execução continua em `previa`, com as ações disponíveis
- [ ] `PreviaIncompleta` (T8) continua sendo levantada antes de qualquer gravação
- [ ] No sucesso, o estado vira `salva` e a fonte é liberada; no conflito, a fonte continua viva para nova conferência
- [ ] O dublê de gravação é possível por `monkeypatch.setattr(versoes, "salvar_interna", ...)` — importar `app.data.versoes` no topo do módulo
- [ ] Testes: cobrir salvar de envio com sucesso, conflito (assinatura divergente) e baixa direta inalterada
- [ ] Gate check passes: `python -m pytest tests/test_execucoes_previa.py -q`
- [ ] Test count: ≥ 4 testes novos

**Tests**: unit
**Gate**: quick

**Commit**: `feat(execucoes): salva o candidato conferido e encerra a prévia`

---

### T22: Rota de Salvar responde conflito e usa o ano-base da prévia

**What**: ajustar a rota de Salvar para o envio usar o ano-base da configuração pública (o mesmo que as páginas consultam), responder `409` com orientação quando a conferência estiver desatualizada e `409` quando houver página com falha.
**Where**: `app/app.py`
**Depends on**: T21
**Reuses**: `admin_atualizar_salvar` (`app/app.py:502-532`), `_ano_base_config` (`app/app.py:251-252`), `app/data/consulta.ano_base_ativo`
**Requirement**: PVP-04, PVP-09, PVP-10

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Envio passa `ano_base` de `config` (via `ano_base_ativo`); baixa direta continua com `_ano_base_config()`
- [ ] `PreviaDesatualizada` responde `409` com erro próprio e texto orientando descartar e reenviar as pastas; nada é gravado
- [ ] `PreviaIncompleta` responde `409` com a lista de páginas com falha
- [ ] `404` para execução inexistente e o portão `confirmacao_necessaria` continuam como estão
- [ ] Testes: cobrir os três `409`, o `404` e o caminho feliz do envio
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: ≥ 5 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `feat(admin): responde conflito de conferência e usa o ano-base configurado`

---

### T23: Atualizar o teste antigo do ano-base no salvar do envio

**What**: trocar a expectativa antiga de `app_module._ano_base_config()` pela fonte usada pelo painel, mantendo a verificação explícita do valor, e apontar o dublê de gravação para o caminho novo do envio.
**Where**: `tests/test_admin_envio_salvar.py`
**Depends on**: T22
**Reuses**: `tests/test_admin_envio_salvar.py:40-99` (`ambiente`, `_execucao_de_envio_com_previa`)
**Requirement**: PVP-04

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] A gravação do envio é dublada em `versoes.salvar_interna` e o teste continua afirmando o ano-base recebido, agora igual ao de `config.ano_base` do banco usado no teste
- [ ] O teste de baixa direta continua cobrindo `_ano_base_config()`
- [ ] Os testes do portão de confirmação e de ausência de PII no histórico seguem passando sem afrouxamento
- [ ] Gate check passes: `python -m pytest tests/test_admin_envio_salvar.py -q`
- [ ] Test count: mesmo número de testes do arquivo, com a expectativa corrigida (sem exclusão silenciosa)

**Tests**: integration
**Gate**: quick

**Commit**: `test(envio): atualiza o ano-base esperado no salvar do envio`

---

### T24: Suíte de paridade das quatro páginas

**What**: comparar, para os mesmos CSVs sintéticos, os indicadores, tabelas e filtros das quatro páginas na prévia com o resultado das mesmas páginas depois de Salvar e Publicar em banco isolado.
**Where**: `tests/test_previa_paridade.py` (arquivo novo)
**Depends on**: None
**Reuses**: dublês e CSVs sintéticos de `tests/test_admin_envio.py`, `tests/test_envio.py` e `tests/test_parity_dominio.py`, banco isolado por `tempfile.mkdtemp()` + `init_db`, `app/arvore_dash`/`app/domain`
**Requirement**: PVP-04, PVP-05, PVP-06

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] As quatro páginas são comparadas (KPIs, linhas de tabela e filtros) entre prévia e versão publicada, sem diferença
- [ ] O caso de campus preservado entra: dados de `interna_*` do campus ausente aparecem na prévia iguais aos da versão interna após Salvar
- [ ] O caso sem publicação inicial renderiza as quatro páginas sem a mensagem "Ainda não há dados publicados."
- [ ] `RISK-002` coberto: vazio, `NaN` e data nula não divergem entre prévia e publicação
- [ ] O ano-base usado na prévia é o de `config` — o teste afirma o valor, não só a igualdade entre lados
- [ ] Nada de `.test-*`/`pytest_cache` deixado no repositório (`AGENTS.md`)
- [ ] Gate check passes: `python -m pytest tests/test_previa_paridade.py -q`
- [ ] Test count: ≥ 8 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `test(previa): compara as quatro páginas da prévia com a versão publicada`

---

### T25: Suíte de acesso, posse e ciclo de vida

**What**: cobrir a matriz de recusa da prévia — sem sessão, sessão alheia, identificador forjado, URL antiga após Salvar/Descartar, execução perdida e ausência de dado pessoal nas respostas.
**Where**: `tests/test_previa_acesso.py` (arquivo novo)
**Depends on**: None
**Reuses**: `test_client` e fixtures de sessão de `tests/test_admin_envio_salvar.py` e `tests/test_admin_envio_polling.py`, `app/auth` (T3), `app/sistec/execucoes` (T4–T8)
**Requirement**: PVP-07, PVP-08, PVP-10

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] GET de prévia sem login redireciona para `/admin/login` sem entregar dados do envio
- [ ] Segunda sessão do mesmo e-mail (outro `sessao_id`) recebe **Prévia indisponível** e nenhuma linha, indicador ou tabela do envio
- [ ] `preview_id` forjado no `dcc.Store` não vira acesso: o callback recusa
- [ ] Caminho público com contexto forjado continua devolvendo só a versão publicada
- [ ] URL de prévia depois de Salvar ou Descartar mostra **Prévia indisponível**, e registro limpo (execução perdida) faz o mesmo, sem substituir por dados públicos
- [ ] Nenhuma resposta da prévia tem coluna pessoal (nome, CPF, e-mail, data de nascimento)
- [ ] Gate check passes: `python -m pytest tests/test_previa_acesso.py -q`
- [ ] Test count: ≥ 8 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `test(previa): cobre acesso, posse e encerramento da conferência`

---

### T26: Suíte de estado, invalidação e falhas

**What**: cobrir que abrir e recarregar a prévia não altera revisões nem tabelas, que mudança de configuração antes do Salvar devolve `409`, que falha conhecida de página bloqueia o Salvar e que filtro vazio não bloqueia.
**Where**: `tests/test_previa_estado.py` (arquivo novo)
**Depends on**: None
**Reuses**: `tests/test_versoes.py` (banco isolado), fotos de `estado_versoes`/tabelas, `app/sistec/execucoes` (T8), `app/app.py` (T22)
**Requirement**: PVP-03, PVP-06, PVP-09, PVP-10

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Abrir, recarregar e navegar pelas quatro páginas deixa `rev_interna`, `rev_publicada`, `interna_*` e as tabelas públicas iguais ao estado anterior
- [ ] Alterar `interna_fatores`, `campus` publicado, ano-base ou `rev_interna` depois da prévia faz Salvar devolver `409` e não grava nada; Descartar continua funcionando
- [ ] Página com falha registrada bloqueia Salvar com `409` e o Descartar libera a prévia
- [ ] Filtro sem linhas não bloqueia Salvar
- [ ] Descartar libera a fonte candidata (memória) e não altera nenhuma revisão
- [ ] Gate check passes: `python -m pytest tests/test_previa_estado.py -q`
- [ ] Test count: ≥ 7 testes novos

**Tests**: integration
**Gate**: full

**Commit**: `test(previa): cobre estados, invalidação da conferência e falhas`

---

### T27: Documentar a etapa de prévia no README

**What**: descrever no fluxo de uso que, após ler os CSVs, as quatro páginas públicas podem ser conferidas antes de Salvar, e que a prévia é privada, não publicada e dura enquanto o envio estiver pendente.
**Where**: `README.md`
**Depends on**: None
**Reuses**: seção de atualização por envio de pastas já existente
**Requirement**: PVP-01, PVP-02

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] O README cita os quatro links de prévia e o aviso **Prévia não publicada**
- [ ] Fica dito que conferir não grava a versão interna nem a publicada, e que Salvar/Descartar encerram a prévia
- [ ] O texto não promete prévia para a baixa direta do Sistec
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: contagem da T26 mantida (sem exclusão silenciosa)

**Tests**: none
**Gate**: build

**Commit**: `docs: descreve a prévia das páginas antes de salvar`

---

### T28: Documentar o teste da prévia no TESTAR

**What**: acrescentar ao guia de teste o roteiro de conferência das quatro páginas antes de Salvar e o que verificar quando o Salvar recusa.
**Where**: `TESTAR.md`
**Depends on**: T27
**Reuses**: roteiro de teste do envio por pastas já existente
**Requirement**: PVP-01, PVP-05

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] O TESTAR descreve como abrir as quatro páginas da prévia depois de enviar as pastas
- [ ] Explica as duas recusas do Salvar: conferência desatualizada e página com falha (descartar e reenviar)
- [ ] Cita que uma URL antiga de prévia deixa de funcionar após Salvar ou Descartar
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: contagem da T26 mantida (sem exclusão silenciosa)

**Tests**: none
**Gate**: build

**Commit**: `docs: ensina a testar a prévia das páginas públicas`

---

## Phase Execution Map

Relações de dependência entre fases (a execução é sequencial, fase a fase):

```
Phase 1:  T1 → T2
Phase 2:  T3 → T4 → T5 → T6 → T7 → T8
Phase 3:  T9 → T10
Phase 4:  T11 → T12 → T13 → T14
Phase 5:  T15
Phase 5:  T16
Phase 5:  T17 → T19
Phase 5:  T18 → T19
Phase 6:  T20 → T21 → T22 → T23
Phase 7:  T24
Phase 7:  T25
Phase 7:  T26
Phase 8:  T27 → T28
```

Dependências que atravessam fases (o destino abre depois, na ordem das fases):

```
T7  → T16
T11 → T16
T12 → T16
T13 → T16
T14 → T16
T3  → T17
T6  → T17
```

A execução é estritamente sequencial — não há paralelismo dentro de uma fase.

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Preparação do candidato | 1 arquivo, 2 funções coesas de dados | ✅ Granular |
| T2: Fonte em memória | 1 módulo, 3 funções coesas | ✅ Granular |
| T3: `sessao_id` | 1 arquivo, 3 funções pequenas | ✅ Granular |
| T4: Guardião da prévia | 1 função + 1 exceção | ✅ Granular |
| T5: Trava por execução | 1 atributo + 1 context manager | ✅ Granular |
| T6: Abrir/liberar fonte | 2 funções | ✅ Granular |
| T7: Contexto de leitura | 1 função + 1 estrutura | ✅ Granular |
| T8: Falhas de página | 3 funções pequenas + 1 exceção | ✅ Granular |
| T9: Consulta de estado | 3 funções no mesmo arquivo, mesmo padrão | ✅ Granular |
| T10: Consulta de carga | 2 funções no mesmo arquivo, mesmo padrão | ✅ Granular |
| T11: Página Matrículas | 1 arquivo (layout + 3 callbacks) | ✅ Granular |
| T12: Página Eficiência | 1 arquivo | ✅ Granular |
| T13: Página Evasão | 1 arquivo | ✅ Granular |
| T14: Página Percentuais Legais | 1 arquivo | ✅ Granular |
| T15: Guarda de sessão | 1 `before_request` | ✅ Granular |
| T16: Página da prévia | 1 arquivo (layout + navegação) | ✅ Granular |
| T17: Rota de envio | 1 endpoint | ✅ Granular |
| T18: Template da tela | 1 template | ✅ Granular |
| T19: Script da tela | 1 arquivo | ✅ Granular |
| T20: `salvar_interna` | 1 função | ✅ Granular |
| T21: Salvar do candidato | 1 função | ✅ Granular |
| T22: Rota de Salvar | 1 endpoint | ✅ Granular |
| T23: Teste do ano-base | 1 arquivo de teste | ✅ Granular |
| T24: Suíte de paridade | 1 arquivo de teste | ✅ Granular |
| T25: Suíte de acesso | 1 arquivo de teste | ✅ Granular |
| T26: Suíte de estado | 1 arquivo de teste | ✅ Granular |
| T27: README | 1 arquivo | ✅ Granular |
| T28: TESTAR | 1 arquivo | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | (início da Phase 1) | ✅ Match |
| T2 | T1 | T1 → T2 | ✅ Match |
| T3 | None | (início da Phase 2) | ✅ Match |
| T4 | T3 | T3 → T4 | ✅ Match |
| T5 | T4 | T4 → T5 | ✅ Match |
| T6 | T5 | T5 → T6 | ✅ Match |
| T7 | T6 | T6 → T7 | ✅ Match |
| T8 | T7 | T7 → T8 | ✅ Match |
| T9 | None | (início da Phase 3) | ✅ Match |
| T10 | T9 | T9 → T10 | ✅ Match |
| T11 | None | (início da Phase 4) | ✅ Match |
| T12 | T11 | T11 → T12 | ✅ Match |
| T13 | T12 | T12 → T13 | ✅ Match |
| T14 | T13 | T13 → T14 | ✅ Match |
| T15 | None | (início da Phase 5) | ✅ Match |
| T16 | T7, T11, T12, T13, T14 | T7 → T16, T11 → T16, T12 → T16, T13 → T16, T14 → T16 | ✅ Match |
| T17 | T3, T6 | T3 → T17, T6 → T17 | ✅ Match |
| T18 | None | (sem dependência na fase) | ✅ Match |
| T19 | T17, T18 | T17 → T19, T18 → T19 | ✅ Match |
| T20 | None | (início da Phase 6) | ✅ Match |
| T21 | T20 | T20 → T21 | ✅ Match |
| T22 | T21 | T21 → T22 | ✅ Match |
| T23 | T22 | T22 → T23 | ✅ Match |
| T24 | None | (sem dependência na fase) | ✅ Match |
| T25 | None | (sem dependência na fase) | ✅ Match |
| T26 | None | (sem dependência na fase) | ✅ Match |
| T27 | None | (início da Phase 8) | ✅ Match |
| T28 | T27 | T27 → T28 | ✅ Match |

Nenhuma dependência aponta para fase posterior.

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | Preparação de dados | unit | unit | ✅ OK |
| T2 | Fonte em memória | unit | unit | ✅ OK |
| T3 | Guardião (sessão) | unit | unit | ✅ OK |
| T4 | Guardião de execução | unit | unit | ✅ OK |
| T5 | Guardião de execução | unit | unit | ✅ OK |
| T6 | Guardião de execução | unit | unit | ✅ OK |
| T7 | Guardião de execução | unit | unit | ✅ OK |
| T8 | Guardião de execução | unit | unit | ✅ OK |
| T9 | Consulta | unit | unit | ✅ OK |
| T10 | Consulta | unit | unit | ✅ OK |
| T11 | Páginas Dash | integration | integration | ✅ OK |
| T12 | Páginas Dash | integration | integration | ✅ OK |
| T13 | Páginas Dash | integration | integration | ✅ OK |
| T14 | Páginas Dash | integration | integration | ✅ OK |
| T15 | Rotas administrativas e guarda | integration | integration | ✅ OK |
| T16 | Páginas Dash | integration | integration | ✅ OK |
| T17 | Rotas administrativas e guarda | integration | integration | ✅ OK |
| T18 | Template e script da tela | unit | unit | ✅ OK |
| T19 | Template e script da tela | unit | unit | ✅ OK |
| T20 | Transações de versão | unit | unit | ✅ OK |
| T21 | Guardião de execução | unit | unit | ✅ OK |
| T22 | Rotas administrativas e guarda | integration | integration | ✅ OK |
| T23 | Rotas administrativas e guarda (teste de rota) | integration | integration | ✅ OK |
| T24 | Paridade e estados | integration | integration | ✅ OK |
| T25 | Autorização, posse e ciclo de vida | integration | integration | ✅ OK |
| T26 | Paridade e estados | integration | integration | ✅ OK |
| T27 | Documentação | none | none | ✅ OK |
| T28 | Documentação | none | none | ✅ OK |

As suítes transversais (T24, T25, T26) não substituem teste de tarefa alguma: cada tarefa de código entrega o próprio teste co-localizado, e as três fecham o que atravessa várias fases (paridade ponta a ponta, matriz de autorização e ciclo de vida da conferência).

---

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| PVP-01 | T16, T17, T18, T19, T27, T28 |
| PVP-02 | T11, T12, T13, T14, T16, T18, T19, T27 |
| PVP-03 | T1, T2, T6, T17, T20, T26 |
| PVP-04 | T1, T2, T7, T9, T10, T11, T12, T13, T14, T21, T22, T23, T24 |
| PVP-05 | T9, T16, T24, T28 |
| PVP-06 | T11, T12, T13, T14, T24, T26 |
| PVP-07 | T3, T4, T5, T7, T15, T25 |
| PVP-08 | T5, T6, T21, T25 |
| PVP-09 | T8, T22, T26 |
| PVP-10 | T20, T21, T22, T25, T26 |

10 requisitos, 10 mapeados, 0 sem tarefa.

---

## Verification Notes

- Medir pico de memória e tempo de montagem/leitura da fonte com volume de CSV representativo antes de fechar a implementação (`design.md` §"Verification Strategy"). Passo humano/Verifier, não vira tarefa.
- A conferência visual da faixa **Prévia não publicada** em ≥992px e em tela pequena é passo humano, dentro das decisões `AD-001` a `AD-005`.
- O `README.md` e o `TESTAR.md` são as duas últimas tarefas (Phase 8) porque a spec diz que o fluxo de uso "precisará refletir a nova etapa quando a feature for implementada" — a implementação acontece no Execute, então a documentação fecha a feature; não fica fora de escopo.
