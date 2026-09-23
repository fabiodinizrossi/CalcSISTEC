# Atualização por Upload de Pastas Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/atualizacao-por-upload/design.md`
**Status**: Draft

---

## Test Coverage Matrix

> Gerada do código, das diretrizes do projeto e da spec — confirmar antes do Execute. Diretrizes encontradas: `.specs/PROJECT_RULES.md` (Princípio IV: mudança de comportamento em `app/domain/`, `app/data/` ou `app/sistec/` exige teste `pytest`; correção de bug começa pelo teste; integração com o Sistec testável sem o Sistec real), `AGENTS.md`, `TESTAR.md`. Não há `pytest.ini`, `pyproject.toml` nem configuração de linter no repositório.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Leitura e validação de planilha (`app/sistec/envio.py`, `app/sistec/colunas.py`) | unit | Todos os ramos; 1:1 com os AC da spec; todo Edge Case listado tem teste | `tests/test_*.py` | `python -m pytest tests/ -q` |
| Máquina de estados de execução (`app/sistec/execucoes.py`) | unit | Todos os ramos de transição e de recusa; 1:1 com os AC | `tests/test_execucoes.py` | `python -m pytest tests/test_execucoes.py -q` |
| Rotas administrativas (`app/app.py`) | integration | Toda rota no escopo: caminho feliz + todo Edge Case + caminhos de erro (`400`, `409`, `413`) | `tests/test_admin_*.py` | `python -m pytest tests/ -q` |
| Template e script da tela (`app/templates/`, `app/static/js/`) | unit | Marcação e comportamento afirmados por asserção de texto, no padrão já usado | `tests/test_js_*.py`, `tests/test_admin_paginas.py` | `python -m pytest tests/ -q` |
| Configuração e constantes (`app/data/historico.py` `TIPOS_VALIDOS`) | unit | Só o valor novo aceito e um inválido recusado | `tests/test_*.py` | `python -m pytest tests/ -q` |
| Documentação (`README.md`, `TESTAR.md`) | none | - (build gate apenas) | - | build gate apenas |

## Gate Check Commands

> Gerados do código — confirmar antes do Execute. `pytest` na raiz é inválido: ele coleta `APAGAR/` e `.test-tmp*/`, diretórios arquivados sem permissão de leitura (registrado em `.specs/STATE.md`). Todo comando aponta para `tests/`.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Depois de tarefa com testes unitários apenas | `python -m pytest tests/<arquivo_do_teste> -q` |
| Full | Depois de tarefa com testes de integração de rota ou de tela | `python -m pytest tests/ -q` |
| Build | No fim de cada fase e em tarefa só de documentação | `python -m pytest tests/ -q && python scripts/verificar_prontidao_cutover.py` |

---

## Execution Plan

As fases são ordenadas e rodam em sequência — cada fase termina antes da seguinte, e as tarefas dentro de uma fase executam em ordem.

### Phase 1: Leitura dos arquivos enviados

```
T1 → T2 → T3
```

### Phase 2: Execução de envio

```
T4 → T5
```

### Phase 3: Rotas administrativas

```
T6 → T7 → T8 → T9
```

### Phase 4: Tela e documentação

```
T10 → T11 → T12
```

---

## Task Breakdown

### T1: Extrair a leitura de CSV do Sistec para função compartilhada

**What**: mover a leitura `;` + `cp1252` + checagem de colunas obrigatórias de dentro de `receber_bytes` para uma função reutilizável, e fazer `receber_bytes` chamá-la, sem mudar o comportamento da baixa.
**Where**: `app/sistec/colunas.py`
**Depends on**: None
**Reuses**: `app/sistec/execucoes.py:202-236`, `COLUNAS_CICLO`, `COLUNAS_MATRICULA`, `aplicar_permissao`
**Requirement**: UPL-03

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `ler_planilha(conteudo_bytes, tipo) -> DataFrame` existe, levanta `ValueError("colunas_ausentes")` e `ValueError("leitura_csv")` com os mesmos códigos de hoje
- [x] `receber_bytes` delega a ela e não contém mais `pd.read_csv`
- [x] Os testes de baixa existentes passam sem edição, provando que a extração preservou o comportamento
- [x] Gate check passes: `python -m pytest tests/test_colunas.py tests/test_execucoes.py tests/test_downloads.py -q` (53 passed)
- [x] Test count: contagem anterior + 4 testes novos, sem exclusão silenciosa

**Status**: Done — commit `a44a55c`.

**Tests**: unit
**Gate**: quick

**Commit**: `refactor(sistec): extrai a leitura de planilha do Sistec para função reutilizável`

---

### T2: Criar o leitor das duas pastas enviadas

**What**: módulo novo que recebe as duas listas de arquivos enviados, ignora o que não é `.csv`, lê cada um pelo leitor de T1 e recusa o envio inteiro no primeiro arquivo reprovado.
**Where**: `app/sistec/envio.py`
**Depends on**: T1
**Reuses**: `ler_planilha` (T1), `aplicar_permissao`
**Requirement**: UPL-03, UPL-04, UPL-10, UPL-12

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `EnvioInvalido` carrega `arquivo` e `motivo` (`pasta_vazia` | `colunas_ausentes` | `leitura_csv`) e nunca conteúdo de célula
- [x] `nome_seguro` descarta componente de diretório do nome vindo do navegador
- [x] `ler_pastas` devolve `{"ciclo": [(nome, df)], "matricula": [(nome, df)], "ignorados": [nome]}`
- [x] Pasta sem nenhum `.csv` levanta `pasta_vazia` nomeando qual pasta, antes de ler qualquer arquivo
- [x] Pastas invertidas caem em `colunas_ausentes` nomeando o primeiro arquivo
- [x] Subpasta dentro da pasta escolhida tem os `.csv` processados sob as mesmas regras
- [x] Gate check passes: `python -m pytest tests/test_envio.py -q` (9 passed)
- [x] Test count: 9 testes novos, sem exclusão silenciosa

**Status**: Done — commit `fc72e7e`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(sistec): lê as pastas de ciclos e matrículas enviadas pelo administrador`

---

### T3: Calcular campi ausentes e não cadastrados

**What**: duas funções que comparam os `CO_UNIDADE` presentes nos ciclos consolidados com os campi cadastrados.
**Where**: `app/sistec/envio.py` (modificar)
**Depends on**: T2
**Reuses**: `app/data/campi.listar_campi`
**Requirement**: UPL-07, UPL-09

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `campi_ausentes(df_ciclos, campi_cadastrados)` devolve os `co_unidade` cadastrados e preenchidos sem nenhuma linha consolidada, em ordem estável
- [x] `campi_nao_cadastrados(df_ciclos, campi_cadastrados)` devolve o inverso
- [x] Campus cadastrado com `co_unidade` vazio não entra em nenhuma das duas listas
- [x] Ciclos vazios devolvem todos os cadastrados como ausentes
- [x] Campus cujas linhas foram todas filtradas por `EXCLUÍDO` aparece como ausente
- [x] Gate check passes: `python -m pytest tests/test_envio.py -q` (14 passed)
- [x] Test count: contagem de T2 + 5 testes novos

**Status**: Done — commit `eae9b0f`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(sistec): identifica campi ausentes e não cadastrados no envio`

---

### T4: Criar execução a partir de arquivos enviados

**What**: construtor alternativo de `Execucao` cuja fila tem um `Par` por arquivo enviado, com `origem="envio"`, mais o preenchimento dos `Par` a partir do resultado de `ler_pastas`.
**Where**: `app/sistec/execucoes.py` (modificar)
**Depends on**: None (abre a Phase 2; a Phase 1 já terminou)
**Reuses**: `Execucao`, `Par`, `criar_execucao`, `_LOCK`, `ESTADOS_TERMINAIS`
**Requirement**: UPL-05

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `criar_execucao_envio(...)` levanta `ExecucaoInvalida` quando o administrador já tem execução não terminal (RN-11)
- [x] A fila tem um `Par` por arquivo, com `nome_perfil` = nome do arquivo e `id_perfil` None
- [x] `Execucao.origem` vale `"baixa"` por padrão e `"envio"` nesse construtor
- [x] `registrar_leitura` preenche `df`, `linhas` e `status="baixado"` de cada `Par`
- [x] `_consolidar_ou_falhar` leva a execução a `previa` sem alteração no próprio `_consolidar_ou_falhar`
- [x] `ConsolidacaoInvalida` leva a `falhou_consolidacao` e nada é gravado
- [x] Gate check passes: `python -m pytest tests/test_execucoes.py tests/test_envio.py -q` (46 passed)
- [x] Test count: contagem anterior + 6 testes novos

**Status**: Done — commit `85d61f4`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(sistec): aceita execução de atualização originada de arquivos enviados`

---

### T5: Exigir confirmação antes de salvar com campi preservados

**What**: registrar os campi ausentes como campi a preservar e bloquear `salvar` até a confirmação explícita, quando a origem é envio.
**Where**: `app/sistec/execucoes.py` (modificar)
**Depends on**: T4
**Reuses**: `salvar`, `campi_falhos`, `app/data/ingest.montar_versao_interna`
**Requirement**: UPL-06, UPL-08

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `definir_campi_preservados(execucao, codigos)` grava em `campi_falhos`
- [x] `ConfirmacaoNecessaria` é levantada por `salvar` quando `origem == "envio"`, há campi preservados e `confirmado` é falso
- [x] Com `confirmado=True`, `salvar` grava e as linhas dos campi preservados continuam idênticas na versão interna
- [x] Sem campi preservados, `salvar` grava sem exigir confirmação
- [x] Com `origem == "baixa"`, o comportamento de `salvar` não muda
- [x] Gate check passes: `python -m pytest tests/test_execucoes.py tests/test_consolidacao.py -q` (48 passed)
- [x] Test count: contagem de T4 + 5 testes novos

**Status**: Done — commit `993e331`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(sistec): exige confirmação para salvar envio que preserva campi`

---

### T6: Aceitar o tipo de histórico `envio`

**What**: acrescentar `"envio"` aos tipos válidos de histórico.
**Where**: `app/data/historico.py` (modificar)
**Depends on**: None (abre a Phase 3; a Phase 2 já terminou)
**Reuses**: `TIPOS_VALIDOS`, `iniciar`, `encerrar`
**Requirement**: UPL-14

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `iniciar("envio", ...)` cria a linha e devolve o `id`
- [x] Um tipo inválido continua levantando `ValueError`
- [x] Os desfechos `salva`, `descartada`, `cancelada`, `falhou` e `falhou_consolidacao` encerram uma linha de tipo `envio`
- [x] Gate check passes: `python -m pytest tests/ -q` (619 passed)
- [x] Test count: contagem anterior + 8 testes novos

**Status**: Done — commit `2a211ef`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(data): registra atualizações por envio no histórico`

---

### T7: Criar a rota de envio

**What**: endpoint que recebe o multipart das duas pastas, orquestra leitura, consolidação, campi preservados e histórico, e devolve o desfecho por arquivo.
**Where**: `app/app.py` (modificar)
**Depends on**: T6
**Reuses**: `envio.ler_pastas`, `criar_execucao_envio`, `registrar_leitura`, `definir_campi_preservados`, `_execucao_da_sessao`, `historico_iniciar`/`historico_encerrar`, `listar_campi`
**Requirement**: UPL-02, UPL-05, UPL-06, UPL-10, UPL-11, UPL-12, UPL-13

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `POST /admin/atualizar/envio` sem sessão administrativa é recusado
- [x] Envio válido chega a `previa` e a resposta lista o desfecho de cada arquivo e os ignorados
- [x] `EnvioInvalido` devolve `400` com `{arquivo, motivo}` e a versão interna fica inalterada
- [x] `ConsolidacaoInvalida` leva a `falhou_consolidacao` com `erro_consolidacao` exposto e nada gravado
- [x] Baixa em andamento devolve `409` `execucao_em_andamento`; prévia pendente devolve `409` `previa_pendente`
- [x] Um envio em andamento faz a baixa (`POST /admin/atualizar/sistec`) devolver `409`
- [x] Payload acima de `MAX_CONTENT_LENGTH` devolve `413`
- [x] O histórico abre com tipo `envio` e encerra com o desfecho correspondente, sem conteúdo de planilha em `detalhe`
- [x] Nenhum arquivo temporário do envio permanece legível após a resposta
- [x] Nenhuma mensagem de erro contém conteúdo de célula
- [x] Gate check passes: `python -m pytest tests/ -q` (636 passed)
- [x] Test count: 17 testes novos, um por item acima

**Status**: Done — commit `affd272`.

**Tests**: integration
**Gate**: full

**Commit**: `feat(admin): adiciona a rota de atualização por envio de pastas`

---

### T8: Aceitar a confirmação de preservação em Salvar

**What**: a rota de salvar passa a ler `confirmar_preservacao` do corpo e a traduzir `ConfirmacaoNecessaria` em `409`.
**Where**: `app/app.py` (modificar)
**Depends on**: T7
**Reuses**: `admin_atualizar_salvar`, `execucoes.salvar`
**Requirement**: UPL-08

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] Salvar um envio com campi preservados sem o campo devolve `409` `confirmacao_necessaria` e não grava
- [x] Com `{"confirmar_preservacao": true}`, grava e o histórico registra os campi preservados
- [x] Salvar uma execução de baixa continua funcionando sem o campo
- [x] Gate check passes: `python -m pytest tests/ -q` (641 passed)
- [x] Test count: contagem de T7 + 5 testes novos

**Status**: Done — commit `28a5306`.

**Tests**: integration
**Gate**: full

**Commit**: `feat(admin): exige confirmação explícita ao salvar envio com campi preservados`

---

### T9: Expor o estado do envio no polling

**What**: a rota de estado passa a devolver os campos que a tela precisa para o envio.
**Where**: `app/app.py` (modificar)
**Depends on**: T8
**Reuses**: `admin_atualizar_estado`
**Requirement**: UPL-09

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `GET /admin/atualizar/execucao` devolve `origem`, `campi_preservados`, `campi_nao_cadastrados`, `arquivos_ignorados` e `matriculas_orfas`
- [x] Numa execução de baixa, `origem` vale `"baixa"` e os campos novos vêm vazios, sem quebrar a resposta atual
- [x] Nenhum campo novo carrega dado pessoal nem conteúdo de célula
- [x] Gate check passes: `python -m pytest tests/ -q` (645 passed)
- [x] Test count: contagem de T8 (641) + 4 testes novos

**Status**: Done — commit `4a8b1ad`.

**Tests**: integration
**Gate**: full

**Commit**: `feat(admin): expõe o estado do envio no polling da tela de atualização`

---

### T10: Oferecer as duas origens na tela

**What**: acrescentar a escolha de origem e os dois campos de pasta ao template da tela Atualizar dados.
**Where**: `app/templates/atualizar.html` (modificar)
**Depends on**: None (abre a Phase 4; a Phase 3 já terminou)
**Reuses**: componentes do gov.br DS já carregados pelo shell (AD-001, AD-002), marcação existente da tela
**Requirement**: UPL-01

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] A página traz a escolha entre "Atualizar do Sistec" e "Enviar pastas"
- [x] O bloco de envio tem um campo de pasta para ciclos e um para matrículas, ambos com seleção de diretório
- [x] Existe área para o resultado por arquivo e para a confirmação de preservação
- [x] A marcação segue o gov.br DS e o layout não quebra abaixo de 992px (AD-005)
- [x] Gate check passes: `python -m pytest tests/ -q` (650 passed)
- [x] Test count: contagem de T9 (645) + 5 testes novos

**Status**: Done — commit `566d348`.

**Tests**: integration
**Gate**: full

**Commit**: `feat(ui): oferece baixa do Sistec e envio de pastas na tela de atualização`

---

### T11: Conduzir o envio no script da tela

**What**: alternar entre as origens, enviar as duas pastas por multipart, mostrar o resultado por arquivo e conduzir a confirmação de preservação antes de Salvar.
**Where**: `app/static/js/atualizar.js` (modificar)
**Depends on**: T10
**Reuses**: `poll`, `renderizarPrevia`, `confirmarAcao` de `app/static/js/confirmar.js`
**Requirement**: UPL-01, UPL-08

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] Escolher uma origem ativa só os controles dela
- [x] Enviar sem uma das pastas avisa que as duas são obrigatórias, sem chamar o servidor
- [x] Durante o envio a tela informa quantos arquivos foram enviados e bloqueia o botão
- [x] Resposta `400` mostra o arquivo e o motivo em português; `409` e `413` têm mensagem própria
- [x] Havendo campi preservados, Salvar só é chamado depois da confirmação
- [x] Gate check passes: `python -m pytest tests/test_js_envio.py -q` (11 passed)
- [x] Test count: 11 testes novos no padrão de `tests/test_js_*.py`

**Status**: Done — commit `860ce51`.

**Tests**: unit
**Gate**: quick

**Commit**: `feat(ui): conduz o envio de pastas e a confirmação de preservação`

---

### T12: Documentar as duas formas de atualizar

**What**: descrever a escolha de origem, o formato esperado das pastas e a regra de campus ausente na documentação de uso.
**Where**: `README.md`, `TESTAR.md`
**Depends on**: T11
**Reuses**: texto existente da seção de atualização
**Requirement**: UPL-01

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `README.md` descreve as duas origens e o que cada pasta deve conter
- [x] `TESTAR.md` explica como testar o envio sem o Sistec real
- [x] Ambos citam que um campus ausente tem os dados preservados e exige confirmação
- [x] Gate check passes: `python -m pytest tests/ -q` (661 passed) e `python scripts/verificar_prontidao_cutover.py` (roda; segue em NO-GO por duas condições de ambiente, não de código: `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` e `CALCSISTEC_HTTPS=1` ausentes)
- [x] Test count: contagem de T11 mantida (661), sem exclusão silenciosa

**Status**: Done — commit `PENDING`.

**Tests**: none
**Gate**: build

**Commit**: `docs: descreve a atualização por envio de pastas`

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1 ------→ T2 ------→ T3
Phase 2:  T4 ------→ T5
Phase 3:  T6 ------→ T7 ------→ T8 ------→ T9
Phase 4:  T10 -----→ T11 -----→ T12
```

A execução é estritamente sequencial — não há paralelismo dentro de uma fase.

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Extrair leitura de CSV | 1 função + 1 chamada | ✅ Granular |
| T2: Leitor das pastas | 1 módulo novo, 3 funções coesas | ✅ Granular |
| T3: Campi ausentes | 2 funções no mesmo módulo | ✅ Granular |
| T4: Execução de envio | 2 funções no mesmo módulo | ✅ Granular |
| T5: Confirmação em salvar | 1 função + 1 portão | ✅ Granular |
| T6: Tipo de histórico | 1 constante | ✅ Granular |
| T7: Rota de envio | 1 endpoint | ✅ Granular |
| T8: Confirmação em Salvar | 1 endpoint | ✅ Granular |
| T9: Estado no polling | 1 endpoint | ✅ Granular |
| T10: Tela | 1 template | ✅ Granular |
| T11: Script | 1 arquivo | ✅ Granular |
| T12: Documentação | 2 arquivos coesos, mesma seção | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | (início da Phase 1) | ✅ Match |
| T2 | T1 | T1 → T2 | ✅ Match |
| T3 | T2 | T2 → T3 | ✅ Match |
| T4 | None (abre a Phase 2) | (início da Phase 2) | ✅ Match |
| T5 | T4 | T4 → T5 | ✅ Match |
| T6 | None (abre a Phase 3) | (início da Phase 3) | ✅ Match |
| T7 | T6 | T6 → T7 | ✅ Match |
| T8 | T7 | T7 → T8 | ✅ Match |
| T9 | T8 | T8 → T9 | ✅ Match |
| T10 | None (abre a Phase 4) | (início da Phase 4) | ✅ Match |
| T11 | T10 | T10 → T11 | ✅ Match |
| T12 | T11 | T11 → T12 | ✅ Match |

Nenhuma dependência aponta para fase posterior.

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | Leitura e validação de planilha | unit | unit | ✅ OK |
| T2 | Leitura e validação de planilha | unit | unit | ✅ OK |
| T3 | Leitura e validação de planilha | unit | unit | ✅ OK |
| T4 | Máquina de estados de execução | unit | unit | ✅ OK |
| T5 | Máquina de estados de execução | unit | unit | ✅ OK |
| T6 | Configuração e constantes | unit | unit | ✅ OK |
| T7 | Rotas administrativas | integration | integration | ✅ OK |
| T8 | Rotas administrativas | integration | integration | ✅ OK |
| T9 | Rotas administrativas | integration | integration | ✅ OK |
| T10 | Template da tela | unit (asserção de marcação) | integration | ✅ OK — nível acima do exigido, o teste sobe o app Flask |
| T11 | Script da tela | unit | unit | ✅ OK |
| T12 | Documentação | none | none | ✅ OK |

---

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| UPL-01 | T10, T11, T12 |
| UPL-02 | T7 |
| UPL-03 | T1, T2 |
| UPL-04 | T2 |
| UPL-05 | T4, T7 |
| UPL-06 | T5, T7 |
| UPL-07 | T3 |
| UPL-08 | T5, T8, T11 |
| UPL-09 | T3, T9 |
| UPL-10 | T2, T7 |
| UPL-11 | T7 |
| UPL-12 | T2, T7 |
| UPL-13 | T7 |
| UPL-14 | T6, T7 |

14 requisitos, 14 mapeados, 0 sem tarefa.
