# Correções da prévia após o uso real — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Cada task abaixo é para um modelo menos capaz executar sozinho, um de cada vez, em ordem. Não pule a leitura do arquivo indicado em "Where" antes de editar: os números de linha citados são os da leitura feita ao escrever esta tarefa (2026-09-23) e podem ter deslocado um pouco por edições de tasks anteriores da mesma fase — confira pelo texto citado, não só pelo número.

---

**Spec**: `.specs/features/correcoes-previa-uso-real/spec.md`
**Status**: In Progress

---

## Test Coverage Matrix

> Gerado do repositório e de `.specs/PROJECT_RULES.md`. Guidelines found: `.specs/PROJECT_RULES.md` (Princípio IV: "Mudança de comportamento em `app/domain/`, `app/data/` ou `app/sistec/` MUST incluir ou atualizar testes `pytest`"; "Correção de bug MUST começar por um teste que reproduz a falha"), `AGENTS.md`. Sem `CONTRIBUTING.md` nem config de cobertura; sem linter configurado (nenhum `ruff`/`flake8`/`.pre-commit-config` no repo) — gate é só `pytest`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------- | --------------------- | ------------------ | ------------- |
| `app/data/*.py` (ingest, campi, versoes, previa) | unit | Todo ramo novo/alterado; 1:1 com os ACs da spec; edge cases listados | `tests/test_previa_candidato.py`, `tests/test_campi.py`, `tests/test_versoes.py`, `tests/test_previa_fonte.py` | `python -m pytest tests/test_<arquivo>.py -q` |
| `app/sistec/*.py` (colunas, envio, execucoes) | unit | Todo ramo novo/alterado; 1:1 com os ACs da spec | `tests/test_colunas.py`, `tests/test_envio.py`, `tests/test_execucoes_previa.py` | `python -m pytest tests/test_<arquivo>.py -q` |
| `app/app.py` (rotas Flask) | integration | Toda rota tocada: caminho feliz + edge case + erro, via `server.test_client()` | `tests/test_admin_envio.py`, `tests/test_previa_acesso.py` | `python -m pytest tests/test_admin_envio.py tests/test_previa_acesso.py -q` |
| `app/pages/*.py` (layout Dash) | integration | Toda página tocada: layout público e de prévia, IDs de callback presentes | `tests/test_paginas_publicas.py`, `tests/test_previa_pagina.py`, novo `tests/test_previa_ids_callback.py` | `python -m pytest tests/test_paginas_publicas.py tests/test_previa_pagina.py -q` |
| Roteamento Dash Pages (`dash.register_page`) | integration | Requisição HTTP real via `_dash-update-component`, não só chamada direta de `layout()` | `tests/test_previa_pagina.py` | `python -m pytest tests/test_previa_pagina.py -q` |
| Documentação (`README.md`, `TESTAR.md`) | none | - (revisão humana) | - | build gate only |

*Nenhuma coluna pessoal nova: qualquer teste que toque `MUNICIPIO`/`NOME UNIDADE DE ENSINO` deve confirmar que elas não aparecem nas tabelas `cursos`/`ciclos` gravadas (Princípio III, RISK-008).*

## Gate Check Commands

| Gate Level | When to Use | Command |
| ---------- | ------------ | ------- |
| Quick | Nunca uso isolado nesta feature — as mudanças atravessam camadas (rota chama `ingest.py` chama `versoes.py`) e um gate parcial já escondeu uma regressão na feature anterior (ver `.specs/STATE.md`, "Lição de processo"). Mantido aqui só para referência. | `python -m pytest tests/test_<arquivo>.py -q` |
| Full | Depois de **toda** task desta feature, sem exceção | `python -m pytest tests/ -q` |
| Build | Não há lint/typecheck configurado neste repo | `python -m pytest tests/ -q` (mesmo comando do Full) |

**Toda task desta lista usa Gate: full** — rode `python -m pytest tests/ -q` antes de marcar a task como feita e antes do commit. O número de testes que passam deve ser ≥ ao da task anterior (825, ver `.specs/STATE.md`) mais os novos desta task; nenhuma falha nova é aceitável.

---

## Execution Plan

Fases em ordem; tasks dentro de cada fase em ordem.

### Phase 1: Roteamento da prévia (CPR-01)

```
T1
```

### Phase 2: Painel público volta a funcionar (CPR-02)

Execução em ordem T2, T3, T4, T5, T6 (fase sequencial); T2-T5 são independentes entre si (arquivos diferentes), só T6 depende de todos os quatro:

```
T2 -> T6
T3 -> T6
T4 -> T6
T5 -> T6
```

### Phase 3: Envio e Salvar com os CSVs reais (CPR-03, CPR-04)

```
T7 -> T8
T8 -> T9
```

### Phase 4: Unidades do envio — cidade e nome (CPR-05)

Execução em ordem T10, T11, T12, T13; T12 é independente de T10/T11 (arquivo `campi.py`, sem depender de `colunas.py`/`envio.py`), só roda depois deles por estar na mesma fase:

```
T10 -> T11
T11 -> T13
T12 -> T13
```

### Phase 5: Publicar leva os campi / prévia usa interna_campus (CPR-06)

T14 é independente (não depende de T7, nem T7 dele); T15 depende de T7 (Phase 3, mesmo arquivo `ingest.py`) e T16 depende de T15:

```
T7 -> T15
T15 -> T16
```

### Phase 6: Resumo e tabela da prévia com o conjunto PNP (CPR-07)

```
T17
```

### Phase 7: Documentação

T18 depende de T14 (Phase 5); T19 depende de T7 (Phase 3) e de T14 (Phase 5):

```
T14 -> T18
T7 -> T19
T14 -> T19
```

---

## Task Breakdown

### T1: Rota da prévia usa `path_template` e ganha teste de roteamento real

**What**: Trocar `path=` por `path_template=` no registro da página da prévia, para que `<execucao_id>` e `<pagina>` sejam lidos como variáveis de caminho (hoje o Dash trata a URL inteira como texto literal e toda visita vira "404 - Page not found"). Acrescentar um teste que bate na rota de verdade pelo mecanismo de roteamento do Dash, não só chamando `layout()` direto.

**Where**: `app/pages/previa.py`
**Depends on**: None
**Reuses**: `app/pages/matriculas.py:22` (`dash.register_page(__name__, path="/", ...)`) como referência de como as outras páginas registram — aqui é `path_template`, não `path`, porque há variáveis de caminho.
**Requirement**: CPR-01 (spec P1.1, AC1)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] `app/pages/previa.py:27` usa `dash.register_page(__name__, path_template="/admin/previa/<execucao_id>/<pagina>", title=...)` (troca só a palavra-chave `path` → `path_template`; o valor da string não muda).
- [x] Em `tests/test_previa_pagina.py`, novo teste que usa `app_module.server.test_client()` (padrão de `tests/test_previa_acesso.py:96`) autenticado (ver como `tests/test_admin_paginas.py` ou `tests/test_admin_envio.py` autenticam a sessão de teste antes do POST/GET) e faz um POST em `/_dash-update-component` com corpo JSON equivalente a:
  ```json
  {"output": "_pages_content.children", "inputs": [{"id": "_pages_location", "property": "pathname", "value": "/admin/previa/<id-de-uma-execucao-em-previa>/matriculas"}], "changedPropIds": ["_pages_location.pathname"]}
  ```
  (monte a execução em `previa` do mesmo jeito que `_envio_com_previa` faz em `tests/test_previa_pagina.py:78-105`).
- [x] O teste confere que a resposta tem status 200 e que o corpo (`resposta.get_json()["response"]["_pages_content"]["children"]`) **não** contém o texto "404" nem "Page not found", e contém "Prévia não publicada" (texto da faixa).
- [x] Um segundo caso no mesmo teste (ou um teste irmão) confere que uma URL de prévia com slug de página inválido continua roteando (200) e devolve "Prévia indisponível" — não 404 do Dash.
- [x] Todos os testes que já chamavam `previa.layout(...)` direto continuam passando sem alteração (não são o alvo desta task, só não podem quebrar).

**Tests**: integration
**Gate**: full

---

### T2: `matriculas.py` sempre inclui o `dcc.Store` da prévia no layout

**What**: O `dcc.Store(id="matriculas-preview", ...)` só entra no layout quando `preview_id is not None`, mas o callback (`app/pages/matriculas.py:339`) sempre declara `State("matriculas-preview", "data")`. No painel público (sem `preview_id`), o navegador lança `ReferenceError: A nonexistent object was used in an State of a Dash callback` e KPIs/tabela ficam vazios. Corrigir incluindo o `Store` sempre, com `data=preview_id` (que vale `None` no caminho público).

**Where**: `app/pages/matriculas.py`
**Depends on**: None
**Reuses**: o próprio padrão do arquivo — só remove a condição em volta de uma linha já existente.
**Requirement**: CPR-02 (spec P1.2, AC1–2)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] Em `app/pages/matriculas.py:161-163`, a linha `filhos.append(dcc.Store(id="matriculas-preview", data=preview_id))` deixa de estar dentro do `if preview_id is not None:` e passa a rodar sempre (incondicional), como a penúltima linha antes do `return html.Div(filhos, ...)`.
- [x] O restante da função `layout` (o bloco que decide `df`/`ano_base`/`atualizado` a partir de `preview_id`, linhas 142-152) **não muda** — só a inclusão do `Store` deixa de ser condicional.
- [x] `app/pages/matriculas.py:339` (`State("matriculas-preview", "data")`) não muda.
- [x] Teste novo ou ajustado em `tests/test_paginas_publicas.py` (ou onde já existir teste de `pagina("matriculas").layout()` sem `preview_id`) que monta o layout público (`layout()`, sem argumento) e confere que a árvore de componentes contém um componente com `id="matriculas-preview"` (use o helper `componentes` de `tests/arvore_dash.py`, já importado em `test_paginas_publicas.py:8`).

**Tests**: integration
**Gate**: full

---

### T3: `eficiencia.py` sempre inclui o `dcc.Store` da prévia no layout

**What**: Mesma correção de T2, no arquivo da página Eficiência Acadêmica.

**Where**: `app/pages/eficiencia.py`
**Depends on**: None
**Reuses**: mesmo padrão de T2.
**Requirement**: CPR-02 (spec P1.2, AC1–2)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] Em `app/pages/eficiencia.py`, a linha `filhos.append(dcc.Store(id="eficiencia-preview", data=preview_id))` (hoje dentro de `if preview_id is not None:`, por volta da linha 89-90) passa a rodar sempre.
- [x] `State("eficiencia-preview", "data")` (por volta da linha 119) não muda.
- [x] Teste equivalente ao de T2, para `pagina("eficiencia").layout()` sem `preview_id`, confirmando `id="eficiencia-preview"` presente no layout público.

**Tests**: integration
**Gate**: full

---

### T4: `evasao.py` sempre inclui o `dcc.Store` da prévia no layout

**What**: Mesma correção de T2, no arquivo da página Taxa de Evasão Anual.

**Where**: `app/pages/evasao.py`
**Depends on**: None
**Reuses**: mesmo padrão de T2.
**Requirement**: CPR-02 (spec P1.2, AC1–2)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] Em `app/pages/evasao.py`, a linha `filhos.append(dcc.Store(id="evasao-preview", data=preview_id))` (hoje dentro de `if preview_id is not None:`, por volta da linha 80-81) passa a rodar sempre.
- [x] `State("evasao-preview", "data")` (por volta da linha 133) não muda.
- [x] Teste equivalente ao de T2, para `pagina("evasao").layout()` sem `preview_id`, confirmando `id="evasao-preview"` presente no layout público.

**Tests**: integration
**Gate**: full

---

### T5: `percentuais_legais.py` sempre inclui o `dcc.Store` da prévia no layout

**What**: Mesma correção de T2, no arquivo da página Percentuais Legais.

**Where**: `app/pages/percentuais_legais.py`
**Depends on**: None
**Reuses**: mesmo padrão de T2.
**Requirement**: CPR-02 (spec P1.2, AC1–2)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] Em `app/pages/percentuais_legais.py:108-109`, a linha `filhos.append(dcc.Store(id="percentuais-preview", data=preview_id))` passa a rodar sempre, fora do `if preview_id is not None:`.
- [x] `State("percentuais-preview", "data")` (por volta da linha 138, citada na spec) não muda.
- [x] Teste equivalente ao de T2, para `pagina("percentuais_legais").layout()` sem `preview_id`, confirmando `id="percentuais-preview"` presente no layout público.

**Tests**: integration
**Gate**: full

---

### T6: Teste de paridade — todo `Input`/`State` de callback existe no layout, público e de prévia

**What**: A causa raiz de CPR-02 (Store condicional) já não deve mais existir depois de T2-T5, mas nada impede que a mesma classe de bug volte (um novo componente com callback, esquecido de um dos dois layouts). Criar um teste dedicado, um por página, que reúne todo `id` citado em `Input`/`State` dos callbacks registrados pela página e confere que cada um aparece no layout público (`layout()`) **e** no layout de prévia (`layout(preview_id=...)`).

**Where**: `tests/test_previa_ids_callback.py` (novo arquivo)
**Depends on**: T2, T3, T4, T5
**Reuses**: `tests/arvore_dash.py` (helper `componentes`, já usado em `test_paginas_publicas.py:8`, para coletar os IDs presentes numa árvore de layout); `dash.callback_map` (Dash registra cada callback com as chaves `Input`/`State`/`Output` em `app.callback_map` depois que o módulo da página é importado — inspecione a estrutura antes de escrever o teste, ex. com um `print` num teste descartável, porque o formato exato do dicionário varia por versão do Dash).
**Requirement**: CPR-02 (spec P1.2, AC3)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] Para cada uma das quatro páginas (`matriculas`, `eficiencia`, `evasao`, `percentuais_legais`): o teste monta `layout()` (público) e `layout(preview_id="qualquer-string")` (prévia — sem precisar de banco real, já que o teste só olha a árvore de componentes, não dados; se `layout(preview_id=...)` exigir banco/sessão para não estourar, use os mesmos dublês/fixtures de `tests/test_previa_pagina.py`).
- [x] Para cada layout, coleta o conjunto de `id`s presentes (via `componentes(layout)` de `arvore_dash.py`, ou equivalente).
- [x] Para cada página, coleta do `dash.callback_map` (ou de `app._callback_list`/estrutura equivalente da versão de Dash instalada — confira em `requirements.txt`/`pip show dash`) todo `id` citado como `Input` ou `State` de um callback cujo módulo é o da página (filtre por prefixo do `id` ou pelo módulo de origem do callback, o que for mais simples de obter de forma confiável).
- [x] O teste falha (assert explícito, com a lista de IDs faltando na mensagem) se algum `id` de `Input`/`State` não estiver no conjunto de IDs do layout público OU do layout de prévia.
- [x] Rodar o teste ANTES de T2-T5 (ou num commit de verificação isolado) confirmando que ele pega a falha original (o `Store` de preview ausente no layout público) — isso prova que o teste é um teste de regressão de verdade, não um que passaria mesmo sem a correção. Depois de T2-T5 aplicadas, o teste passa.

**Tests**: integration
**Gate**: full

---

### T7: Descartar ciclos sem modalidade de ensino na preparação do candidato

**What**: Ciclos antigos (ex.: MULHERES MIL 2011-2013) chegam sem `MODALIDADE ENSINO`. A coluna é `NOT NULL` em `cursos`/`interna_cursos`, e a gravação da fonte da prévia (`app/data/previa.py:84`, `df.to_sql(...)`) quebra com `IntegrityError`, deixando a execução sem candidato. Filtrar esses ciclos (e as matrículas ligadas a eles) antes de montar `cursos`/`ciclos`/`matriculas`/`matriculas_eficiencia`, e expor a contagem do que foi descartado no resumo do candidato.

**Where**: `app/data/ingest.py`
**Depends on**: None
**Reuses**: `preparar_versao` já calcula `df_ciclo_novos` (linhas 219-225) antes de chamar `_cursos_e_ciclos_do_conjunto` (linha 227) e `montar_matriculas_e_eficiencia` (linha 228) — o filtro entra bem ali, e `montar_versao_interna` (linha 289-302) reaproveita `preparar_versao` inteira, então cobre a baixa direta automaticamente (CPR-03 AC5) sem tocar nesse segundo arquivo.
**Requirement**: CPR-03 (spec P1.3, AC1, AC2, AC5); Edge Case "todos os ciclos de uma unidade descartados por falta de modalidade" (parcialmente — a outra metade é T8).

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [x] Nova função pura `ciclos_com_modalidade(df_ciclo)` em `app/data/ingest.py`, exportável (sem `_` no nome — vai ser usada por `app/app.py` em T8), que devolve `df_ciclo` sem as linhas onde `MODALIDADE_ENSINO` é nulo, `NaN` ou string vazia/só espaço (confira o nome exato da coluna: em `app/sistec/colunas.py:31` o nome interno é `MODALIDADE_ENSINO`, maiúsculo, é o nome que chega em `df_ciclo` neste ponto do pipeline — não é o `modalidade_ensino` minúsculo, que só existe depois do rename em `_cursos_e_ciclos_do_conjunto`). Se `df_ciclo` estiver vazio ou não tiver a coluna, devolve `df_ciclo` sem alterar.
- [x] Em `preparar_versao` (linha ~219-227), logo depois de calcular `df_ciclo_novos` (linha 222-225) e antes de chamar `_cursos_e_ciclos_do_conjunto(df_ciclo_novos)` e `montar_matriculas_e_eficiencia(df_matricula, df_ciclo_novos, ano_base)`: chamar `df_ciclo_novos_filtrado = ciclos_com_modalidade(df_ciclo_novos)`, calcular `n_ciclos_descartados = len(df_ciclo_novos) - len(df_ciclo_novos_filtrado)`, calcular `codigos_descartados = set(df_ciclo_novos["CODIGO_CICLO_MATRICULA"]) - set(df_ciclo_novos_filtrado["CODIGO_CICLO_MATRICULA"])` e `n_matriculas_descartadas = int(df_matricula["CODIGO_CICLO_MATRICULA"].isin(codigos_descartados).sum())` (ajuste o nome da coluna de matrícula se for diferente — confira `app/sistec/colunas.py:44`, é `CODIGO_CICLO_MATRICULA` também). Usar `df_ciclo_novos_filtrado` (não o original) nas duas chamadas seguintes.
- [x] `matriculas_novos`/`eficiencia_novos` não precisam de filtro extra: `montar_matriculas_e_eficiencia` já faz `merge(..., how="inner")` (`app/sistec/consolidacao.py:133`) contra `df_ciclos`, então uma matrícula cujo ciclo foi descartado desaparece sozinha por não casar no merge.
- [x] O dicionário `resumo` devolvido por `preparar_versao` (linhas 272-280) ganha duas chaves novas: `"ciclos_sem_modalidade_descartados": n_ciclos_descartados` e `"matriculas_sem_modalidade_descartadas": n_matriculas_descartadas`.
- [x] Em `tests/test_previa_candidato.py`: novo teste com um CSV sintético de um ciclo com `MODALIDADE_ENSINO` vazio/nulo e duas matrículas ligadas a ele (junto de um ciclo normal, para garantir que só o certo é descartado); confere `preparar_versao(...)["resumo"]["ciclos_sem_modalidade_descartados"] == 1`, `["matriculas_sem_modalidade_descartadas"] == 2`, e que nenhuma linha do ciclo descartado aparece em `tabelas["cursos"]`/`tabelas["ciclos"]`/`tabelas["matriculas"]`.
- [x] Teste equivalente chamando `montar_versao_interna(...)` (já usado em `test_previa_candidato.py`) confirmando que a baixa direta também descarta (CPR-03 AC5) — pode ser o mesmo teste parametrizado ou um segundo teste curto.

**Tests**: unit
**Gate**: full

---

### T8: Envio informa ciclos/matrículas descartados e trata unidade sem modalidade como ausente

**What**: A rota `/admin/atualizar/envio` precisa (a) informar na resposta e no polling quantos ciclos/matrículas foram descartados por falta de modalidade (CPR-03 AC2) e (b) usar os ciclos já filtrados por modalidade ao decidir quais unidades estão "ausentes" ou "não cadastradas" — senão uma unidade cujos ciclos são TODOS sem modalidade parece presente (Edge Case da spec) quando na prática nenhum dado dela entra no candidato.

**Where**: `app/app.py`
**Depends on**: T7
**Reuses**: `execucao.matriculas_orfas`/`execucao.campi_cadastrados_automaticamente` (linhas 420-421, 448-449, 653-657) já são o padrão exato de "atributo solto na execução, espelhado na resposta imediata e no polling" — copiar esse padrão, não inventar um mecanismo novo.
**Requirement**: CPR-03 (spec P1.3, AC2); Edge Case "unidade toda descartada por falta de modalidade"

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Import no topo do arquivo: adicionar `ciclos_com_modalidade` ao `from app.data.ingest import preparar_versao` (linha 29), virando `from app.data.ingest import ciclos_com_modalidade, preparar_versao`.
- [ ] Logo depois de `campi_cadastrados = listar_campi()` (linha 439), antes das chamadas a `envio.campi_ausentes`/`envio.campi_nao_cadastrados` (linhas 440-444): `ciclos_validos = ciclos_com_modalidade(execucao.previa["ciclos"])`. Trocar `execucao.previa["ciclos"]` por `ciclos_validos` nas duas chamadas seguintes (linhas 440 e 443) — **não** mexer no resto de `execucao.previa` (a linha 445, `_matriculas_orfas_envio(execucao.previa)`, continua igual: matrícula órfã é um motivo diferente de matrícula descartada por modalidade, os dois não se misturam).
- [ ] Depois que `candidato = preparar_versao(...)` for bem-sucedido (dentro do bloco try, depois da linha ~461 atual): `execucao.ciclos_sem_modalidade_descartados = candidato["resumo"]["ciclos_sem_modalidade_descartados"]` e `execucao.matriculas_sem_modalidade_descartadas = candidato["resumo"]["matriculas_sem_modalidade_descartadas"]`; e em `resposta`: `resposta["ciclos_sem_modalidade_descartados"] = execucao.ciclos_sem_modalidade_descartados` e `resposta["matriculas_sem_modalidade_descartadas"] = execucao.matriculas_sem_modalidade_descartadas`.
- [ ] Em `admin_atualizar_estado` (por volta da linha 653-657), acrescentar ao JSON devolvido: `"ciclos_sem_modalidade_descartados": getattr(execucao, "ciclos_sem_modalidade_descartados", 0) or 0` e `"matriculas_sem_modalidade_descartadas": getattr(execucao, "matriculas_sem_modalidade_descartadas", 0) or 0`.
- [ ] Em `tests/test_admin_envio.py`: novo teste que envia um CSV com uma unidade cujo ÚNICO ciclo não tem `MODALIDADE ENSINO`, e confere que essa unidade **não** aparece em `corpo["campi_cadastrados_automaticamente"]` nem é tratada como presente (ela deve se comportar como se estivesse ausente do envio — dados atuais dela preservados, sem quebrar o envio). Outro teste (ou o mesmo, com um segundo ciclo válido) confere que `corpo["ciclos_sem_modalidade_descartados"]` e `corpo["matriculas_sem_modalidade_descartadas"]` batem com o esperado.

**Tests**: integration
**Gate**: full

---

### T9: Falha ao montar a fonte da prévia responde JSON de erro, nunca 500

**What**: Hoje só `MemoryError` é tratado ao montar a fonte da prévia (`preparar_versao` + `execucoes.abrir_previa`); qualquer outro erro (como o `IntegrityError` de modalidade nula, antes de T7 existir, ou qualquer falha futura) sobe como 500 sem corpo JSON. Ampliar para responder erro estruturado em qualquer falha, mantendo a execução em `previa`/descartável e sem gravar nada.

**Where**: `app/app.py`
**Depends on**: T8
**Reuses**: o próprio bloco `try/except MemoryError` já existente (linhas ~458-468) — só acrescenta um segundo `except`, não reescreve a lógica.
**Requirement**: CPR-04 (spec P1.3, AC4)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] O bloco try (que chama `preparar_versao(...)` e `execucoes.abrir_previa(...)`) ganha um `except Exception:` **depois** do `except MemoryError:` já existente (ordem importa: `MemoryError` é mais específico e precisa vir primeiro, senão o `except Exception` genérico o captura primeiro e a mensagem "sem_memoria" nunca aparece).
- [ ] O novo `except Exception:` faz exatamente o que o `except MemoryError:` já faz, trocando só o valor: `resposta["previa"] = None`, `resposta["erro_previa"] = "falha_previa"` (em vez de `"sem_memoria"`), `return flask.jsonify(resposta)`.
- [ ] Nenhuma escrita acontece nesse caminho de erro: confirme que `execucoes.abrir_previa` só atribui `execucao.previa_fonte`/`execucao.candidato` DEPOIS de `abrir_fonte_previa` retornar com sucesso (veja `app/sistec/execucoes.py:435-436`) — se a leitura estiver certa, nada precisa mudar lá, só confirmar no teste.
- [ ] `execucao.estado` continua `"previa"` depois da falha (já era `"previa"` antes de `preparar_versao` ser chamado — confirme lendo `app/sistec/execucoes.py` em volta de onde `estado = "previa"` é setado na consolidação, não mexer nisso).
- [ ] Em `tests/test_admin_envio.py`: novo teste que usa `monkeypatch` para fazer `preparar_versao` (ou `execucoes.abrir_previa`) levantar uma exceção genérica (ex. `ValueError("boom")`) e confere: `resposta.status_code == 200` (nunca 500), `corpo["erro_previa"] == "falha_previa"`, `corpo["previa"] is None`, e que a execução (via `execucoes.obter_do_admin(ADMIN)` ou equivalente) continua em estado `"previa"` e pode ser descartada (`execucoes.descartar(...)` não levanta erro).
- [ ] O teste já existente `test_falha_de_memoria_devolve_erro_sem_gravar` (linha 520 de `tests/test_admin_envio.py`) continua passando sem alteração.

**Tests**: integration
**Gate**: full

---

### T10: Lista de permissão de colunas passa a ler `MUNICIPIO` e `NOME UNIDADE DE ENSINO`

**What**: O CSV de ciclos traz `MUNICIPIO` e `NOME UNIDADE DE ENSINO`, mas `app/sistec/colunas.py` não os lê, então o cadastro automático de campus nunca teve como saber a cidade/nome da unidade. Adicionar as duas colunas à lista de permissão do tipo `"ciclo"`, com nomes internos que não colidam com nada existente e não sejam confundidos com dado pessoal.

**Where**: `app/sistec/colunas.py`
**Depends on**: None
**Reuses**: o próprio dicionário `COLUNAS_CICLO` (linhas 24-39) — só acrescenta duas entradas, no mesmo formato `{"NOME NO SISTEC": "NOME_INTERNO"}` das demais.
**Requirement**: CPR-05 (spec P1.4, AC1, AC6)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] `COLUNAS_CICLO` (linha 24) ganha duas entradas: `"MUNICIPIO": "MUNICIPIO_UNIDADE"` e `"NOME UNIDADE DE ENSINO": "NOME_UNIDADE_ENSINO"`. Confirme o texto exato do cabeçalho do CSV real antes de fechar a task — a spec cita os nomes sem acento e em maiúsculas (`MUNICIPIO`, não `MUNICÍPIO`); se os CSVs de `Downloads/01janeiro` (verificação local da usuária) tiverem grafia diferente, ajuste a chave para bater com o arquivo real, não com a spec.
- [ ] A checagem de defesa em profundidade no fim do arquivo (linhas 58-63, o `for _tipo, _mapa in ...`) continua passando na importação do módulo — `MUNICIPIO_UNIDADE` e `NOME_UNIDADE_ENSINO` não podem estar em `COLUNAS_PII` (não estão: são dado institucional, não pessoal — Princípio III do `.specs/PROJECT_RULES.md`).
- [ ] `aplicar_permissao(df, "ciclo")` (linha 66) continua funcionando sem mudança de código — ela já itera `mapa` genericamente.
- [ ] Confirme (não precisa alterar código, só ler) que `app/data/ingest.py` (`_COLUNAS_CURSOS_SCHEMA`, `_COLUNAS_CICLOS_SCHEMA`, linhas 31-54) **não** lista `MUNICIPIO_UNIDADE`/`NOME_UNIDADE_ENSINO` — são colunas de leitura, nunca devem ser gravadas em `cursos`/`ciclos`/`interna_cursos`/`interna_ciclos` (CPR-05 AC6). Essa é a garantia estrutural do requisito, sem precisar de filtro extra.
- [ ] Em `tests/test_colunas.py`: novo teste que monta um DataFrame com as colunas externas (incluindo `"MUNICIPIO"` e `"NOME UNIDADE DE ENSINO"`) e confere que `aplicar_permissao(df, "ciclo")` devolve as colunas renomeadas `MUNICIPIO_UNIDADE`/`NOME_UNIDADE_ENSINO` presentes no resultado. Outro teste confere que a lista de permissão de `"matricula"` continua sem essas colunas (elas só existem na planilha de ciclo).

**Tests**: unit
**Gate**: full

---

### T11: Função pura que resolve cidade/nome de cada unidade a partir do envio

**What**: Dado o DataFrame de ciclos do envio (já com `MUNICIPIO_UNIDADE`/`NOME_UNIDADE_ENSINO`, depois de T10), extrair para cada `CO_UNIDADE` o primeiro valor não vazio de cidade e nome, na ordem em que as linhas aparecem (que é a ordem dos arquivos, porque `consolidar` concatena os arquivos nessa ordem — confirme lendo `app/sistec/consolidacao.py` se tiver dúvida).

**Where**: `app/sistec/envio.py`
**Depends on**: T10
**Reuses**: `_codigos_ciclo` (linhas 58-65) como referência de como esse arquivo já lida com `CO_UNIDADE`/`SITUACAO_CICLO`, mas a função nova é separada (esta precisa de cidade/nome, não só do código).
**Requirement**: CPR-05 (spec P1.4, AC1); Edge Case "valores diferentes de MUNICIPIO para a mesma unidade → primeiro valor não vazio na ordem dos arquivos"

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Nova função `dados_unidades_do_envio(df_ciclos)` em `app/sistec/envio.py`, que devolve `dict[str, dict]` no formato `{"U1": {"cidade": "Santa Maria", "nome_unidade": "Campus SM"}, ...}` — uma entrada por `CO_UNIDADE` distinto presente em `df_ciclos`.
- [ ] Para cada `CO_UNIDADE`, `cidade` é o primeiro valor de `MUNICIPIO_UNIDADE` não nulo/não vazio (depois de `str().strip()`) entre as linhas daquele código, na ordem em que aparecem no DataFrame; mesma regra para `nome_unidade`/`NOME_UNIDADE_ENSINO`. Se nenhuma linha tiver valor não vazio, o campo correspondente fica `None` (não a string vazia).
- [ ] `df_ciclos` vazio, ou sem as colunas `CO_UNIDADE`/`MUNICIPIO_UNIDADE`/`NOME_UNIDADE_ENSINO`, devolve `{}` sem erro (mesma tolerância de `_codigos_ciclo`, linha 60).
- [ ] Em `tests/test_envio.py`: teste com duas linhas do mesmo `CO_UNIDADE`, a primeira com `MUNICIPIO` vazio e a segunda preenchida, confirmando que o valor da segunda linha é usado (primeiro não vazio, não necessariamente a primeira linha). Outro teste com uma unidade sem nenhum valor preenchido, confirmando `None`. Outro teste com duas unidades diferentes, confirmando que cada uma recebe seu próprio valor.

**Tests**: unit
**Gate**: full

---

### T12: `app/data/campi.py` ganha função para completar cidade/nome sem sobrescrever

**What**: Uma unidade já cadastrada (por leitura anterior do Sistec ou envio anterior) pode estar sem `cidade`/`nome_unidade`. Precisa de uma função que preencha só o que está vazio, nunca sobrescrevendo um valor já existente — o mesmo padrão que `preencher_unidade` (linha 234-268) já usa com `COALESCE`, mas disparado por código de unidade, não por `id_perfil`.

**Where**: `app/data/campi.py`
**Depends on**: None
**Reuses**: `preencher_unidade` (linhas 234-268) como modelo direto de "`UPDATE ... SET cidade = COALESCE(cidade, ?), nome_unidade = COALESCE(nome_unidade, ?) ... ; _regravar_interna_campus(conn); conn.commit()`" dentro de uma transação `BEGIN IMMEDIATE`/`try`/`except`/`finally`.
**Requirement**: CPR-05 (spec P1.4, AC2)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Nova função `completar_cidade_nome(co_unidade, cidade, nome_unidade, db_path=DEFAULT_DB_PATH)` em `app/data/campi.py`, seguindo o mesmo esqueleto transacional das funções vizinhas (`BEGIN IMMEDIATE`, `try`/`except Exception: rollback; raise`/`finally: close`).
- [ ] O `UPDATE` afeta **todas** as linhas de `campi_sistec` com aquele `co_unidade` (pode haver mais de uma, se houver duplicidade histórica — mas normalmente uma só) usando `cidade = COALESCE(cidade, ?), nome_unidade = COALESCE(nome_unidade, ?) WHERE co_unidade = ?`. Se `cidade`/`nome_unidade` recebidos forem `None`, o `COALESCE` não muda nada (comportamento correto: nada para preencher).
- [ ] Chama `_regravar_interna_campus(conn)` (linha 289) antes do commit, do mesmo jeito que as outras funções de escrita deste arquivo.
- [ ] `co_unidade` que não existe em `campi_sistec`: a função não faz nada (0 linhas afetadas) e não levanta erro — quem cadastra unidades novas é `incluir_campus`, não esta função.
- [ ] Em `tests/test_campi.py`: teste que cadastra um campus sem cidade/nome (via `incluir_campus`, sem passar esses argumentos), chama `completar_cidade_nome` com valores, e confere que `cidade`/`nome_unidade` foram gravados E que `interna_campus` foi regravada (mesmo padrão de asserção que os outros testes deste arquivo usam para `_regravar_interna_campus`). Outro teste confirma que, se o campus já tinha `cidade` preenchida, chamar `completar_cidade_nome` com um valor diferente **não** sobrescreve o valor existente.

**Tests**: unit
**Gate**: full

---

### T13: Envio cadastra unidade nova com cidade/nome e completa unidades incompletas

**What**: Ligar T10-T12: ao cadastrar automaticamente uma unidade nova (AFE-03), gravar `cidade`/`nome_unidade` a partir do CSV; e para unidades já cadastradas mas incompletas que aparecem no envio, completar os campos vazios.

**Where**: `app/app.py`
**Depends on**: T11, T12
**Reuses**: `_cadastrar_unidades_do_envio` (linhas 355-378) já existe e já chama `campi.incluir_campus` — só precisa passar `cidade`/`nome_unidade`, que a assinatura de `incluir_campus` já aceita (`app/data/campi.py:199`, parâmetros `cidade=None, nome_unidade=None` já existem).
**Requirement**: CPR-05 (spec P1.4, AC1, AC2)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] `_cadastrar_unidades_do_envio(codigos, ...)` (linha 355) ganha um parâmetro novo, `dados_unidades` (o `dict` devolvido por `envio.dados_unidades_do_envio`). Dentro do loop `for codigo in codigos:` (linha 367), a chamada a `campi.incluir_campus(...)` (linhas 369-374) ganha `cidade=dados_unidades.get(codigo, {}).get("cidade")` e `nome_unidade=dados_unidades.get(codigo, {}).get("nome_unidade")`.
- [ ] No corpo da rota `/admin/atualizar/envio` (por volta da linha 439-444), antes de chamar `_cadastrar_unidades_do_envio`: `dados_unidades = envio.dados_unidades_do_envio(ciclos_validos)` (reaproveita o `ciclos_validos` já filtrado por modalidade que T8 introduziu — **não** o `execucao.previa["ciclos"]` bruto, para ficar consistente com o que realmente vai para o candidato) e passar `dados_unidades` na chamada existente: `_cadastrar_unidades_do_envio(envio.campi_nao_cadastrados(ciclos_validos, campi_cadastrados), dados_unidades)`.
- [ ] Nova etapa logo depois: para cada campus em `campi_cadastrados` (a lista já lida na linha 439) cujo `co_unidade` está em `dados_unidades` e que tem `cidade` ou `nome_unidade` vazios, chamar `campi.completar_cidade_nome(campus["co_unidade"], dados_unidades[campus["co_unidade"]]["cidade"], dados_unidades[campus["co_unidade"]]["nome_unidade"], db_path=DEFAULT_DB_PATH)`. Pode ser um laço simples direto na rota ou uma função auxiliar `_completar_unidades_incompletas(campi_cadastrados, dados_unidades)` — escolha o que ficar mais legível, mas mantenha no mesmo arquivo.
- [ ] Em `tests/test_admin_envio.py`: estenda `test_unidade_fora_do_cadastro_e_cadastrada_automaticamente` (linha 345) — ou crie um teste irmão — passando `"MUNICIPIO"`/`"NOME UNIDADE DE ENSINO"` na linha de ciclo da unidade nova (`_linha_ciclo`, linha 39, precisa ganhar esses campos como parâmetro opcional) e conferindo que o campus cadastrado (`dados_campi.listar_campi(...)`) tem `cidade`/`nome_unidade` preenchidos com os valores do CSV.
- [ ] Novo teste: uma unidade já cadastrada sem cidade/nome (via `incluir_campus` direto no fixture, sem esses campos) aparece num envio cujo CSV traz `MUNICIPIO`/`NOME UNIDADE DE ENSINO` preenchidos para ela; depois do POST, `dados_campi.listar_campi(...)` mostra `cidade`/`nome_unidade` completados. Outro teste confirma que, se a unidade já tinha `cidade` preenchida com outro valor, o envio não sobrescreve.

**Tests**: integration
**Gate**: full

---

### T14: Publicar e Desfazer passam a levar `campus`

**What**: Hoje `campus` só muda por **Aplicar ao público** em Configurações (RN-33); uma instalação que nunca clicou nesse botão publica dados e o painel público continua com `campus` vazio. Por decisão da usuária (spec, `Assumptions`), **Publicar** passa a copiar `interna_campus → campus` na mesma transação, guardando o `campus` anterior em `anterior_campus`; **Desfazer** restaura junto.

**Where**: `app/data/versoes.py`
**Depends on**: None
**Reuses**: o mecanismo já genérico de `_ORDEM_DELETE_PUBLICACAO`/`_ORDEM_INSERT_PUBLICACAO` (linhas 26-27), que `publicar` (linha 118) e `desfazer` (linha 153) já percorrem sem código específico por tabela — `campus`/`interna_campus`/`anterior_campus` já existem no schema (mesmo DDL gerado por `_ddl_conjunto` para os três prefixos, `app/data/schema.py:40-48`), então basta incluir `"campus"` nessas duas tuplas.
**Requirement**: CPR-06 (spec P1.4, AC3, AC4); Edge Case "`interna_campus` vazio no Publicar"

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] `_ORDEM_DELETE_PUBLICACAO` (linha 26) passa de `_ORDEM_DELETE_BAIXA + ("fatores",)` para `_ORDEM_DELETE_BAIXA + ("fatores", "campus")`.
- [ ] `_ORDEM_INSERT_PUBLICACAO` (linha 27) passa de `("fatores",) + _ORDEM_INSERT_BAIXA` para `("fatores", "campus") + _ORDEM_INSERT_BAIXA`.
- [ ] Não precisa mexer em `publicar` (linha 118), `desfazer` (linha 153) nem `aplicar_publico` (linha 182) — os três já iteram essas tuplas genericamente com `INSERT INTO {tabela} SELECT * FROM interna_{tabela}`/`anterior_{tabela}`. `aplicar_publico` continua existindo e continua fazendo sua própria cópia de `campus` (linhas 198-199) — isso fica redundante depois desta task quando o fluxo passa por `publicar`, mas não é um bug: **Aplicar ao público** continua sendo um caminho válido e independente (spec: "Aplicar ao público continua existindo").
- [ ] `interna_campus` vazio: `publicar` funciona normalmente (o `INSERT ... SELECT *` de uma tabela vazia não falha, só não insere linhas) — sem código extra para este edge case, só confirme no teste.
- [ ] Em `tests/test_versoes.py`: estenda `test_publicar_move_interna_para_publicada_e_atualiza_estado` (linha 113) — ou crie um teste irmão — inserindo uma linha em `interna_campus` antes de publicar, e conferindo que ela aparece em `campus` depois. Estenda `test_publicar_pela_segunda_vez_guarda_a_publicada_anterior` (linha 132) conferindo que a segunda publicação move o `campus` antigo para `anterior_campus`. Estenda `test_desfazer_restaura_a_publicada_anterior` (linha 155) conferindo que `campus` volta ao valor anterior depois de `desfazer()`. Novo teste curto confirmando que publicar com `interna_campus` vazio não levanta erro e deixa `campus` vazio.

**Tests**: unit
**Gate**: full

---

### T15: Assinatura de origem passa a resumir `interna_campus`

**What**: `calcular_assinatura_origem` hoje resume o `campus` publicado; com a mudança de T14 (Publicar levando `campus`), a prévia precisa comparar contra `interna_campus` — o que vai ao ar —, não contra o `campus` já publicado (que pode estar desatualizado até o próximo Publicar). Isso também faz o `409` de "conferência desatualizada" (`ConflitoDeConferencia`, já existente) reagir a mudanças em `interna_campus`, como pede o edge case da spec sobre o Salvar.

**Where**: `app/data/ingest.py`
**Depends on**: T7 (mesmo arquivo — aplique depois, para não conflitar com a edição de T7 na mesma região do arquivo)
**Reuses**: a própria função `calcular_assinatura_origem` (linhas 176-204) — troca só a tabela lida na consulta SQL, a estrutura do dict devolvido não muda.
**Requirement**: CPR-06 (spec P1.4, AC5); Edge Case "Salvar recebe prévia cujo `interna_campus` mudou depois da montagem → 409 já existente"

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Em `calcular_assinatura_origem` (linha 192-194), a consulta `"SELECT co_unidade, cidade, nome_unidade FROM campus ORDER BY co_unidade"` passa a ler `FROM interna_campus` em vez de `FROM campus`.
- [ ] O docstring da função (linhas 177-182, "...e um resumo determinístico... de `interna_fatores` e do `campus` publicado") é atualizado para dizer `interna_campus` em vez de "`campus` publicado".
- [ ] A chave do dict devolvido continua se chamando `"campus"` (linha 203) — só a fonte dos dados muda, não o formato do retorno (isso evita quebrar `tests/test_versoes.py:268`, que monta um dict `assinatura_falsa` com a chave `"campus"`).
- [ ] Em `tests/test_previa_candidato.py`: novo teste que grava uma linha em `interna_campus` (não em `campus`) e confere que `calcular_assinatura_origem(db_path)["campus"]` reflete essa linha, mesmo com `campus` publicado vazio ou diferente.
- [ ] Rode `python -m pytest tests/test_versoes.py -q` sozinho antes do gate completo — este arquivo tem `assinatura_falsa`/`assinatura_esperada` comparados contra `calcular_assinatura_origem` de verdade em vários testes de `ConflitoDeConferencia` (linhas 255-342); é exatamente o tipo de "quebra em quem chama a função" que a lição registrada em `.specs/STATE.md` (Handoff) pede para cobrir.

**Tests**: unit
**Gate**: full

---

### T16: Fonte da prévia lê `campus` de `interna_campus`

**What**: `abrir_fonte_previa` monta a tabela `campus` da fonte em memória da prévia a partir do `campus` publicado (`app/data/previa.py:64-71`) quando não recebe `campus_publico` explícito — e `execucoes.abrir_previa` sempre chama com `campus_publico=None` (`app/sistec/execucoes.py:435`). Trocar essa leitura para `interna_campus`, para a prévia mostrar exatamente o que o Publicar vai levar ao ar (consistente com T14/T15).

**Where**: `app/data/previa.py`
**Depends on**: T15
**Reuses**: a própria função `abrir_fonte_previa` (linhas 56-103) — troca só a tabela lida no fallback, linhas 64-71.
**Requirement**: CPR-06 (spec P1.4, AC5)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Em `abrir_fonte_previa` (linhas 64-71), a consulta `"SELECT co_unidade, cidade, nome_unidade FROM campus"` passa a ler `FROM interna_campus`.
- [ ] O docstring da função (linha 58-59, "`campus_publico`: DataFrame do `campus` publicado... se None, é lido de `db_path`") é atualizado para dizer que o fallback lê `interna_campus`, não o `campus` publicado.
- [ ] O parâmetro `campus_publico` da função **não muda de nome nem de posição** (quem já passa um DataFrame explícito continua funcionando igual — só o fallback interno muda de tabela).
- [ ] Em `tests/test_previa_fonte.py`: novo teste (ou ajuste de um existente que já testava o fallback lendo `campus`) que grava uma linha em `interna_campus` e nenhuma (ou uma diferente) em `campus`, chama `abrir_fonte_previa(candidato, campus_publico=None, db_path=...)`, e confere pela conexão de leitura da fonte (`fonte.abrir_leitura()`) que a tabela `campus` da fonte tem os dados de `interna_campus`.

**Tests**: unit
**Gate**: full

---

### T17: Resumo e amostra da prévia vêm do candidato, não do consolidado bruto

**What**: O polling mostra `2600 ciclos e 116011 matrículas` (consolidado bruto de todos os arquivos) quando o que o Salvar realmente grava é o candidato já filtrado pela regra PNP (ex.: 11.071 matrículas). `_resumo_amostra` (`app/sistec/execucoes.py:409-421`) e `abrir_previa` (linha 424-439) usam `execucao.previa` (bruto) — trocar para usar `candidato`, que já está disponível no momento em que `abrir_previa` roda.

**Where**: `app/sistec/execucoes.py`
**Depends on**: None
**Reuses**: `candidato["resumo"]` (já devolvido por `preparar_versao`, `app/data/ingest.py:272-280`) já tem as contagens de `cursos`/`ciclos`/`matriculas`/`matriculas_eficiencia` prontas — não precisa recalcular nada, só usar.
**Requirement**: CPR-07 (spec P2, AC1-AC4)

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Nova função `_amostra_candidato(candidato)` em `app/sistec/execucoes.py`, que monta até 20 linhas juntando `candidato["tabelas"]["matriculas"]` com `candidato["tabelas"]["ciclos"]` (por `codigo_ciclo_matricula`) e `candidato["tabelas"]["cursos"]` (por `codigo_portfolio`, via os ciclos), uma linha por matrícula, com as colunas: `co_matricula`, `status_corrigido`, `mes_ocorrencia_corrigido`, `ano_base` (de `matriculas`), `codigo_ciclo_matricula` (de `ciclos`), `nome_curso_ajustado`, `tipo_curso_pnp`, `modalidade_ensino` (de `cursos`), `co_unidade` (de `ciclos` ou `cursos`, o que tiver — confira qual das duas tabelas retém essa coluna em `_COLUNAS_CICLOS_SCHEMA`/`_COLUNAS_CURSOS_SCHEMA`, `app/data/ingest.py:31-54`). Sem nenhuma coluna de `_COLUNAS_MATRICULAS_SCHEMA`/`_COLUNAS_EFICIENCIA_SCHEMA`/`_COLUNAS_CURSOS_SCHEMA` que não esteja nessa lista — em especial, nada de nome/CPF/e-mail/nascimento (já não existem no candidato, mas confirme).
- [ ] `_resumo_amostra` (linha 409) é substituída (ou ganha uma variante) para receber `candidato` em vez de `previa`: `"cursos"`, `"ciclos"`, `"matriculas"`, `"matriculas_eficiencia"` vêm de `candidato["resumo"]`; `"amostra"` vem de `_amostra_candidato(candidato)` (convertida com `.astype(object).replace([inf, -inf], None).where(notna(), None).to_dict(orient="records")`, mesmo tratamento de NaN/inf que já existe na linha 415-416).
- [ ] `abrir_previa` (linha 424-439) chama a nova versão de `_resumo_amostra` com `candidato` (já é um parâmetro da função, linha 424) em vez de `execucao.previa` — mova a chamada (linha 438) para antes ou depois de `execucao.previa = None` (linha 439), não importa, já que agora ela não depende mais de `execucao.previa`.
- [ ] O fluxo de baixa direta (a rota/branch que NÃO passa por `abrir_previa` — o `elif execucao.previa is not None:` em `admin_atualizar_estado`, `app/app.py:629-637`) **não muda** — CPR-07 AC4 pede explicitamente para preservar o resumo/amostra atual desse fluxo.
- [ ] Em `tests/test_execucoes_previa.py` (ou `tests/test_previa_estado.py`, o que já tiver cobertura de `abrir_previa`/polling — confira os dois antes de decidir): novo teste com um envio sintético onde só parte das matrículas passa na regra PNP (algumas ciclos/cursos "rejeitados" ou fora do candidato), confirmando que `execucao.previa_resumo["ciclos"]`/`["matriculas"]` batem com `candidato["resumo"]`, não com a contagem bruta do CSV; e que a amostra tem `co_matricula` e o nome do curso na mesma linha (CPR-07 AC2, teste independente da spec).

**Tests**: unit
**Gate**: full

---

### T18: `README.md` cita que Publicar leva os campi

**What**: Documentar a mudança de comportamento de T14 (Publicar agora leva `campus`, além dos dados de baixa) para quem opera o painel.

**Where**: `README.md`
**Depends on**: T14
**Reuses**: a seção existente do README que já descreve o fluxo Publicar/Desfazer/Aplicar ao público (leia antes de editar para manter o tom e a estrutura).
**Requirement**: spec, "Project Rules & References" ("`README.md` e `TESTAR.md` devem citar que Publicar leva os campi e que ciclos sem modalidade são descartados")

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] A seção do README que descreve **Publicar** passa a citar que a lista de campi (`interna_campus`) também é levada ao público na mesma operação, com a versão anterior preservada para Desfazer — mesma linguagem/nível de detalhe do restante do documento, em português.
- [ ] Nenhuma outra seção do README é reescrita além do necessário para essa frase.

**Tests**: none
**Gate**: full

---

### T19: `TESTAR.md` cita Publicar levando campi e descarte de ciclos sem modalidade

**What**: Mesma atualização de T18, no guia de teste manual, e mais a menção ao descarte de ciclos sem modalidade (T7).

**Where**: `TESTAR.md`
**Depends on**: T7, T14
**Reuses**: a própria estrutura de passo a passo do documento (leia a seção de Publicar/Atualizar antes de editar).
**Requirement**: spec, "Project Rules & References"

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] O passo a passo de **Publicar** em `TESTAR.md` passa a citar que os campi vão junto.
- [ ] O passo a passo de **Atualizar dados** (envio) passa a citar que ciclos sem `MODALIDADE ENSINO` são descartados automaticamente, com a contagem aparecendo na tela/polling.
- [ ] Nenhuma outra seção do documento é reescrita além do necessário.

**Tests**: none
**Gate**: full

---

## Phase Execution Map

Fases executam nesta ordem: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7. Dentro de cada fase, as tasks rodam na ordem em que aparecem em "Task Breakdown" (T1, T2, T3, ...), mesmo quando não há seta abaixo — a ausência de seta só significa "sem dependência de dado", não "pode rodar em paralelo" (não há paralelismo dentro de uma fase).

```
T2 -> T6
T3 -> T6
T4 -> T6
T5 -> T6
T7 -> T8
T8 -> T9
T10 -> T11
T11 -> T13
T12 -> T13
T7 -> T15
T15 -> T16
T14 -> T18
T7 -> T19
T14 -> T19
```

Execução é estritamente sequencial — sem paralelismo dentro de uma fase. Um agente (ou worker de lote) trabalha uma task de cada vez, em ordem.

**Como a execução em lotes funciona:** 19 tasks ao todo, empacotadas em fases inteiras (nunca corta uma fase no meio), buscando ~7 tasks por lote:

- **Lote 1**: Phase 1 + Phase 2 = T1-T6 (6 tasks)
- **Lote 2**: Phase 3 + Phase 4 = T7-T13 (7 tasks)
- **Lote 3**: Phase 5 + Phase 6 + Phase 7 = T14-T19 (6 tasks)

Isso é > 8 tasks no total, então a oferta de sub-agentes por lote se aplica (ver seção "Sub-Agent Delegation" da skill `tlc-spec-driven`) — mas só depois de aprovação explícita da usuária para usá-los; sem aprovação, execução inline, lote por lote, na mesma ordem.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1: `path_template` + teste de roteamento | 1 arquivo de página + 1 arquivo de teste (co-localizado) | ✅ Granular |
| T2-T5: `dcc.Store` sempre no layout | 1 arquivo cada, mesma mudança de 1 linha | ✅ Granular |
| T6: teste de paridade de IDs | 1 arquivo de teste novo | ✅ Granular |
| T7: descarte de ciclos sem modalidade | 1 arquivo (`ingest.py`), 1 função nova + 1 função alterada | ✅ Granular |
| T8: edge case + contagens no envio | 1 arquivo (`app.py`) | ✅ Granular |
| T9: erro JSON da montagem da prévia | 1 arquivo (`app.py`), 1 bloco `except` novo | ✅ Granular |
| T10: permissão de colunas | 1 arquivo (`colunas.py`), 2 entradas de dict | ✅ Granular |
| T11: `dados_unidades_do_envio` | 1 arquivo (`envio.py`), 1 função nova | ✅ Granular |
| T12: `completar_cidade_nome` | 1 arquivo (`campi.py`), 1 função nova | ✅ Granular |
| T13: cadastro automático com cidade/nome | 1 arquivo (`app.py`) | ✅ Granular |
| T14: Publicar/Desfazer levam `campus` | 1 arquivo (`versoes.py`), 2 tuplas | ✅ Granular |
| T15: assinatura de origem usa `interna_campus` | 1 arquivo (`ingest.py`), 1 função alterada | ✅ Granular |
| T16: fonte da prévia usa `interna_campus` | 1 arquivo (`previa.py`), 1 função alterada | ✅ Granular |
| T17: resumo/amostra do candidato | 1 arquivo (`execucoes.py`), 1 função nova + 1 alterada | ✅ Granular |
| T18: README | 1 arquivo | ✅ Granular |
| T19: TESTAR.md | 1 arquivo | ✅ Granular |

Nenhuma task toca mais de um arquivo de produção; quando cita um arquivo de teste, é o "Done when" (co-localização exigida pela skill), não um segundo "Where".

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| ---- | ------------------------ | --------------- | ------ |
| T1 | None | (sem seta) | ✅ Match |
| T2 | None | (sem seta) | ✅ Match |
| T3 | None | (sem seta) | ✅ Match |
| T4 | None | (sem seta) | ✅ Match |
| T5 | None | (sem seta) | ✅ Match |
| T6 | T2, T3, T4, T5 | `T2→T6`, `T3→T6`, `T4→T6`, `T5→T6` | ✅ Match |
| T7 | None | (sem seta) | ✅ Match |
| T8 | T7 | `T7→T8` | ✅ Match |
| T9 | T8 | `T8→T9` | ✅ Match |
| T10 | None | (sem seta) | ✅ Match |
| T11 | T10 | `T10→T11` | ✅ Match |
| T12 | None | (sem seta) | ✅ Match |
| T13 | T11, T12 | `T11→T13`, `T12→T13` | ✅ Match |
| T14 | None | (sem seta) | ✅ Match |
| T15 | T7 | `T7→T15` | ✅ Match |
| T16 | T15 | `T15→T16` | ✅ Match |
| T17 | None | (sem seta) | ✅ Match |
| T18 | T14 | `T14→T18` | ✅ Match |
| T19 | T7, T14 | `T7→T19`, `T14→T19` | ✅ Match |

Confirmado por `python3 .claude/skills/tlc-spec-driven/scripts/validate_tasks.py .specs/features/correcoes-previa-uso-real/tasks.md` → `0 error(s)`. T3-T5 e T12 não têm seta de entrada porque não dependem de dado de nenhuma outra task (arquivos diferentes); dentro da fase elas ainda rodam em sequência (T2 antes de T3 antes de T4...), só não é uma dependência de verdade — ver "Tips" no fim do arquivo.

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | ------------------------------ | ------------------ | ----------- | -------- |
| T1 | Roteamento Dash Pages (`app/pages/previa.py`) | integration | integration | ✅ OK |
| T2 | `app/pages/*.py` layout | integration | integration | ✅ OK |
| T3 | `app/pages/*.py` layout | integration | integration | ✅ OK |
| T4 | `app/pages/*.py` layout | integration | integration | ✅ OK |
| T5 | `app/pages/*.py` layout | integration | integration | ✅ OK |
| T6 | `app/pages/*.py` layout (teste cruzado) | integration | integration | ✅ OK |
| T7 | `app/data/*.py` | unit | unit | ✅ OK |
| T8 | `app/app.py` rota | integration | integration | ✅ OK |
| T9 | `app/app.py` rota | integration | integration | ✅ OK |
| T10 | `app/sistec/*.py` | unit | unit | ✅ OK |
| T11 | `app/sistec/*.py` | unit | unit | ✅ OK |
| T12 | `app/data/*.py` | unit | unit | ✅ OK |
| T13 | `app/app.py` rota | integration | integration | ✅ OK |
| T14 | `app/data/*.py` | unit | unit | ✅ OK |
| T15 | `app/data/*.py` | unit | unit | ✅ OK |
| T16 | `app/data/*.py` | unit | unit | ✅ OK |
| T17 | `app/sistec/*.py` | unit | unit | ✅ OK |
| T18 | Documentação | none | none | ✅ OK |
| T19 | Documentação | none | none | ✅ OK |

Nenhuma violação — nenhuma task usa "Tests: none" para uma camada que a matriz exige teste, e nenhuma task empurra teste para uma task futura (toda task que cria/altera código de produção já inclui, no próprio "Done when", os testes daquela mudança).

---

## Tips

- **Fases são ordenadas** — cada fase termina antes da próxima começar; tasks rodam em ordem dentro da fase.
- **Reuses = economia de leitura** — sempre referencia código já existente em vez de reinventar.
- **Uma task = um commit** — mensagem sugerida por task, no padrão Conventional Commits já usado no histórico do repo (`fix(previa): ...`, `feat(campi): ...`, `docs: ...`); rode `python3 .claude/skills/tlc-spec-driven/scripts/check_commit.py --message "<msg>"` antes de cada commit.
- **Done when = testável** — se não dá para verificar, a redação da task está errada, não o código.
- **Gate = full em toda task** — a feature atravessa camadas; um gate parcial já escondeu uma regressão na feature anterior (`.specs/STATE.md`, "Lição de processo").
