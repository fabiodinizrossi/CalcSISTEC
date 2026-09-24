# Limpeza de resíduos e onboarding do repositório — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Regras do projeto que valem em toda tarefa (de `AGENTS.md`, `.specs/PROJECT_RULES.md` e `.specs/LESSONS.md`):

- Branch `migracao-dash-gov-br`. Commits locais apenas: **sem `git push`, merge, PR ou deploy**.
- Um commit por tarefa, em Conventional Commits, validado com `check_commit.py`. Marque a tarefa como `[x]` neste arquivo no mesmo commit.
- O gate é a suíte **completa** (`python -m pytest -q`) em toda tarefa que mexe em `.py`. Lição do projeto: o gate parcial deixou passar quebra em chamadores.
- Diretórios temporários só no diretório temporário do sistema; apague-os depois. Nunca deixe `.test-*`, `.pytest_cache/` ou `.verifier-scratch-*` no repositório.
- Não edite artefatos históricos em `.specs/features/*/` (exceto os desta feature).
- Não mexa em IDs de spec (`UPL-02`, `RISK-009`…) dentro de docstrings, só nos **caminhos** para arquivos ausentes (Out of Scope do spec).
- Linha de base: `python -m pytest -q` → **939 passed, 0 failed** (commit `21941fd`).

---

**Spec**: `.specs/features/limpeza-onboarding-repo/spec.md`
**Design**: não há `design.md`. A única decisão técnica (onde iniciar o watchdog) está registrada em Assumptions do spec.
**Status**: Approved (2026-09-24)

---

## Test Coverage Matrix

> Gerada a partir do código, das diretrizes e do spec; confirme antes do Execute. Diretrizes encontradas: `AGENTS.md`, `.specs/PROJECT_RULES.md` (Princípio IV: mudança de comportamento exige teste `pytest`, bug começa por teste que reproduz a falha). Não há `pytest.ini`, `conftest.py`, lint nem CI configurados.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Ponto de entrada (`run.py`) | unit | 1:1 com WDG-01/WDG-02 + edge case de porta inválida; espiões no lugar de `iniciar_varredura` e `app.run` | `tests/test_run.py` | `python -m pytest tests/test_run.py -q` |
| Script de teste (`scripts/testar.ps1`) | integration | AMB-01 AC1, AC3, AC4, AC5 com processo real em Windows (`skipif` fora de Windows); WDG-03 por leitura do script | `tests/test_testar_ps1.py` | `python -m pytest tests/test_testar_ps1.py -q` |
| Código de `app/` removido | unit (higiene) | Cada símbolo e arquivo removido tem uma asserção de ausência; `COLUNAS_PII` tem asserção de conteúdo preservado | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q` |
| Documentação e arquivos de configuração (`.md`, `requirements*.txt`, `.env.example`, `.python-version`, `.gitignore`) | unit (higiene) | Cada AC de DOC/DEP/AMB-02 vira uma asserção sobre o conteúdo do arquivo; termo proibido encontrado cita arquivo e termo | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q` |
| `.specs/STATE.md` | none | Build gate apenas | - | build gate only |

## Gate Check Commands

> Gerados a partir do código; confirme antes do Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Tarefas só de documentação (sem `.py` de `app/`, `scripts/` ou `run.py`) | `python -m pytest tests/test_higiene_repositorio.py -q` |
| Full | Toda tarefa que cria, altera ou apaga `.py` ou `testar.ps1` | `python -m pytest -q` |
| Build | Fim de cada fase | `python -m pytest -q` (não há lint nem build configurados) |

---

## Execution Plan

Fases em sequência; tarefas em ordem dentro de cada fase.

### Phase 1: Watchdog (correção de bug)

```
T1 → T2
```

### Phase 2: Limpeza de código e arquivos

```
T3 → T4 → T5
```

### Phase 3: Instalação reproduzível

```
T6 → T7
```

### Phase 4: Documentação sem referências quebradas

```
T8 → T9 → T10 → T11 → T12 → T13 → T14
```

### Phase 5: Ambiente de teste para qualquer agente

```
T15 → T16 → T17
```

---

## Task Breakdown

### T1: `run.py` inicia o watchdog antes de subir o app

**What**: Criar `main(argv=None)` em `run.py` com `argparse` (`--host`, padrão `0.0.0.0`; `--port`, `int`, padrão `8050`), que chama `execucoes.iniciar_varredura()` e depois `app.run(host=..., port=..., debug=False)`; o bloco `if __name__ == "__main__"` chama `main()`. Escreva os testes **antes** e veja-os falhar (Princípio IV: bug começa por teste que reproduz a falha).
**Where**: `run.py`
**Depends on**: None
**Reuses**: `app/sistec/execucoes.py:569` (`iniciar_varredura`, já idempotente)
**Requirement**: WDG-01, WDG-02

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `tests/test_run.py` cobre: ordem `iniciar_varredura` → `app.run` com uma chamada de cada (WDG-01 AC1); `--host 127.0.0.1 --port 9999` repassados (AC2); padrão `0.0.0.0`/`8050` sem argumentos (AC2); `--port abc` sai com `SystemExit` código 2 sem chamar `iniciar_varredura` (edge case)
- [x] Teste em **subprocesso** (`sys.executable -c "import app.app; from app.sistec import execucoes; print(execucoes._VARREDURA_THREAD)"`) afirma a saída `None` (WDG-02); subprocesso evita contaminar o estado global dos outros testes
- [x] Os testes de WDG-01 falham antes da mudança em `run.py` (registre no commit)
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: 939 + novos, 0 failed (sem deleções)

**Tests**: unit
**Gate**: full

**Commit**: `fix(execucoes): iniciar a varredura de execucoes ao subir o app`

---

### T2: `testar.ps1` sobe o app por `run.py`

**What**: Trocar a linha `python -c "from app.app import app; app.run(host='127.0.0.1', port=$Porta, debug=False)"` (`scripts/testar.ps1:174`) por `python run.py --host 127.0.0.1 --port $Porta`, para o watchdog também rodar no ambiente de teste.
**Where**: `scripts/testar.ps1`
**Depends on**: T1
**Reuses**: `run.py` de T1
**Requirement**: WDG-03

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `tests/test_testar_ps1.py` (arquivo novo) afirma que o script contém `run.py --host 127.0.0.1 --port $Porta` e **não** contém `app.run(`
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total de T1 + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `fix(testar): subir o ambiente de teste por run.py com o watchdog`

---

### T3: Apagar `app/data/validators.py` e criar o teste de higiene

**What**: Criar `tests/test_higiene_repositorio.py` com a primeira asserção (o arquivo `app/data/validators.py` não existe), apagar o módulo e tirar a menção a `validators.py` da docstring de `app/data/consulta.py:5`.
**Where**: `app/data/validators.py` (apagar)
**Depends on**: None
**Reuses**: nenhum
**Requirement**: LIM-01 (AC1)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `git grep -n "validators"` em `app/`, `scripts/`, `tests/` e `run.py` não encontra import nem menção ao módulo (exceto o próprio teste de higiene)
- [x] O teste de higiene usa a raiz do repositório calculada a partir de `__file__`, não o diretório corrente
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `refactor(data): remover validators.py, que nenhum modulo usa`

---

### T4: Apagar as quatro funções sem chamador

**What**: Apagar `kpi_colunas` (`app/components/kpi.py:39`), `data_ultimo_upload_valido` (`app/data/consulta.py:33`), `t01_remover_pii` (`app/data/transform.py:69`) e `_rotulo_eixo` (`app/pages/percentuais_legais.py:40`), mais imports que ficarem órfãos por causa delas. **Não** apague `COLUNAS_PII`: ela é usada por `app/sistec/colunas.py:21`. Quatro arquivos numa tarefa por coesão: é a mesma operação (apagar função sem chamador), com uma asserção de higiene para cada.
**Where**: `app/components/kpi.py`, `app/data/consulta.py`, `app/data/transform.py`, `app/pages/percentuais_legais.py`
**Depends on**: T3
**Reuses**: `tests/test_higiene_repositorio.py`
**Requirement**: LIM-01 (AC2, AC3)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene afirma, por AST, que nenhum dos quatro nomes é definido no seu arquivo
- [x] O teste de higiene afirma que `COLUNAS_PII` contém exatamente as mesmas entradas de antes (copie a lista atual para o teste)
- [x] Antes de apagar cada função, `git grep -nw <nome>` confirma zero chamadores (se aparecer chamador, PARE e reporte)
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `refactor(app): remover funcoes sem chamador`

---

### T5: Tirar arquivos soltos e ignorar pastas de ferramenta

**What**: Apagar `nonascii.txt` e o diretório `chromedriver/` da raiz (ambos fora do Git; o `chromedriver` contraria o Princípio VI) e acrescentar `.agents/`, `.uv-cache/` e `.uv-python/` ao `.gitignore`. **Não** apague `.agents/`, `.uv-cache/` nem `.uv-python/`.
**Where**: `.gitignore`
**Depends on**: T4
**Reuses**: `tests/test_higiene_repositorio.py`
**Requirement**: LIM-02

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene afirma a ausência de `nonascii.txt` e `chromedriver/` e a presença das três entradas no `.gitignore`
- [x] `git status --short` não mostra `.agents/` como não rastreado
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `chore(repo): remover arquivos soltos e ignorar caches de ferramenta`

---

### T6: Fixar versões em `requirements.txt` e criar `requirements-dev.txt`

**What**: Reescrever `requirements.txt` com exatamente `dash==4.4.1`, `dash-bootstrap-components==2.0.4`, `pandas==2.3.0`, `openpyxl==3.1.5`, `plotly==6.8.0`, `defusedxml==0.7.1`, `Pillow==11.2.1`, `Flask==3.1.3`, `Werkzeug==3.1.8`; criar `requirements-dev.txt` com `-r requirements.txt` e `pytest==9.1.1`. Os dois arquivos juntos porque o segundo inclui o primeiro.
**Where**: `requirements.txt`, `requirements-dev.txt` (novo)
**Depends on**: None
**Reuses**: `tests/test_higiene_repositorio.py`
**Requirement**: DEP-01

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene compara as linhas não vazias de cada arquivo com a lista exata do spec (DEP AC1, AC2)
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `build(deps): fixar versoes testadas e separar dependencias de desenvolvimento`

---

### T7: Criar `.python-version` e `.env.example`

**What**: Criar `.python-version` com `3.12` e `.env.example` com as chaves `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`, `FLASK_SECRET_KEY`, `CALCSISTEC_HTTPS`, `CALCSISTEC_SISTEC_BASE_URL`, `CALCSISTEC_PASTA_DOWNLOADS`, `CALCSISTEC_PASTA_COLETA`, `ANO_BASE`, cada uma com comentário de uma linha dizendo para que serve e valor vazio ou de exemplo. Explique no comentário de `ADMIN_PASSWORD_HASH` como gerar o hash (`python -c "from werkzeug.security import generate_password_hash as g; print(g('SUA_SENHA'))"`). Leia `app/config.py`, `app/auth.py` e `app/sistec/*.py` para descrever cada chave pelo uso real, não por suposição.
**Where**: `.env.example` (novo), `.python-version` (novo)
**Depends on**: T6
**Reuses**: `tests/test_higiene_repositorio.py`
**Requirement**: DEP-02

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene afirma o conteúdo `3.12` de `.python-version` e a presença de cada uma das oito chaves em `.env.example`
- [x] O teste de higiene afirma que `.env.example` não tem valor com cara de segredo: `FLASK_SECRET_KEY` e `ADMIN_PASSWORD_HASH` estão vazios
- [x] `.env.example` **não** é ignorado pelo `.gitignore` (`git check-ignore .env.example` não imprime nada)
- [x] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `chore(config): documentar variaveis de ambiente e versao de python`

---

### T8: Tirar caminhos para arquivos ausentes do código de `app/`

**What**: Em todo `.py` de `app/`, remover ou reescrever as menções a `_reversa_sdd`, `_reversa_forward`, `cutover_plan.md`, `PARITY_REPORT.md`, `CUTOVER.md` e `APAGAR` (hoje em cerca de 20 arquivos: `git grep -n "_reversa_sdd\|_reversa_forward\|cutover_plan\|PARITY_REPORT\|CUTOVER.md\|APAGAR" -- app`). Onde a menção explica uma regra, mantenha a explicação e troque a referência para o spec de `.specs/features/` ou para `DEPLOY.md` (criado em T10). **Não** mexa em IDs como `RISK-009` ou `BR-MIGRAR-001`. Só docstrings e comentários mudam; nenhuma linha de código executável.
**Where**: `app/`
**Depends on**: None
**Reuses**: `tests/test_higiene_repositorio.py`
**Requirement**: DOC-01 (AC1, parte `app/`)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene percorre todo `.py` de `app/` e falha citando arquivo e termo se achar um termo proibido
- [x] `git diff --stat` só mostra arquivos `.py` de `app/`, e `git diff` só altera linhas de docstring e comentário
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(app): trocar referencias a documentos ausentes por specs do repositorio`

---

### T9: Tirar caminhos para arquivos ausentes de `scripts/`, `tests/` e `run.py`

**What**: Mesmo trabalho de T8 em `scripts/*.py`, `tests/*.py` (exceto `tests/test_higiene_repositorio.py`) e `run.py`. Em `scripts/verificar_prontidao_cutover.py:153`, a mensagem passa a dizer `ver DEPLOY.md`.
**Where**: `scripts/verificar_prontidao_cutover.py`
**Depends on**: T8
**Reuses**: `tests/test_higiene_repositorio.py`
**Requirement**: DOC-01 (AC1, parte `scripts/`/`tests/`), DOC-02 (AC5)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene cobre também `scripts/*.py`, `tests/*.py` (excluindo a si mesmo) e `run.py`
- [x] Um teste roda `scripts/verificar_prontidao_cutover.py` (ou importa a função que imprime a seção) e afirma que a saída contém `DEPLOY.md` e não contém `CUTOVER.md`
- [x] Gate check passes: `python -m pytest -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(scripts): apontar a verificacao de prontidao para DEPLOY.md`

---

### T10: Trocar `CUTOVER.md` e `PARITY_REPORT.md` por `DEPLOY.md`

**What**: Criar `DEPLOY.md` com as seções do DOC AC4: pré-requisitos (Python 3.12, `requirements.txt`, variáveis de `.env.example`); subida com `python run.py` (e `--host`/`--port`); `CALCSISTEC_HTTPS=1` e certificado válido fora de `localhost`; **um único** worker/processo, porque o registro de execuções é em memória; checklist antes de publicar (`python -m pytest -q` verde, `python scripts/verificar_prontidao_cutover.py` com saída 0); pendências abertas: validação em celular real (DS-42: celular de 320 a 430 px e tela de 1280 px ou mais, registrando dispositivo, largura e data nesse arquivo) e CSRF (rotas administrativas com POST sem token; só `SameSite=Lax` protege, `app/config.py`). Leia `CUTOVER.md` antes de apagá-lo e leve para `DEPLOY.md` tudo o que ainda vale hoje, sem a numeração "Tarefa NN". Depois apague `CUTOVER.md` e `PARITY_REPORT.md`.
**Where**: `DEPLOY.md` (novo)
**Depends on**: T9
**Reuses**: conteúdo vigente de `CUTOVER.md`
**Requirement**: DOC-02 (AC3, AC4)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene afirma a ausência de `CUTOVER.md` e `PARITY_REPORT.md`, a presença de `DEPLOY.md` e, em `DEPLOY.md`, os marcadores `run.py`, `CALCSISTEC_HTTPS=1`, `verificar_prontidao_cutover.py`, `DS-42`, `CSRF` e a palavra `worker`
- [x] `DEPLOY.md` entra na lista de arquivos verificados contra termos proibidos (DOC AC1, AC2)
- [x] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(deploy): substituir CUTOVER e PARITY_REPORT por DEPLOY.md`

---

### T11: Reescrever o README para quem clona

**What**: Reescrever `README.md` com: (1) uma frase sobre o que é o CalcSISTEC; (2) "Começar": clonar, `python -m venv .venv` com Python 3.12, ativar, `pip install -r requirements-dev.txt`, copiar `.env.example` para `.env`, `python -m pytest -q`, subir com `scripts/testar.ps1` (teste) ou `python run.py` (produção); (3) "Estrutura": cada subdiretório direto de `app/` (`assets`, `components`, `data`, `domain`, `pages`, `sistec`, `static`, `templates`) e os arquivos-chave (`app.py`, `shell.py`, `admin_campi.py`, `auth.py`, `config.py`), mais `scripts/`, `tests/`, `.specs/`, `extensao-sistec/`, cada um com uma linha de propósito; (4) "Onde mexer" (DOC AC8); (5) as seções atuais que continuam válidas (painel público, atualização de dados, instalar em outra instituição, observação sobre métricas), revisadas; (6) links para `TESTAR.md`, `DEPLOY.md`, `AGENTS.md` e `.specs/README.md`. Tire "Tarefa NN", `_reversa_*` e `projetoFabio`. Confira cada caminho citado no repositório antes de escrevê-lo.
**Where**: `README.md`
**Depends on**: T10
**Reuses**: README atual e `.specs/STATE.md` (decisões AD-001 a AD-005 para o "Onde mexer" de visual e shell)
**Requirement**: DOC-03, DOC-01 (README)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene afirma que o README cita cada subdiretório existente de `app/` (listado dinamicamente, então um diretório novo sem documentação faz o teste falhar), mais `scripts/`, `tests/` e `.specs/`
- [x] O teste de higiene afirma a presença das seções "Começar" e "Onde mexer" e, dentro de "Começar", a ordem `requirements-dev.txt` → `.env.example` → `pytest`
- [x] O teste de higiene afirma que todo caminho relativo citado entre crases no README que comece com `app/`, `scripts/`, `tests/` ou `.specs/` existe no repositório
- [x] `README.md` entra na verificação de termos proibidos
- [x] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(readme): reescrever o guia de entrada para quem clona o repositorio`

---

### T12: Atualizar `TESTAR.md`

**What**: Corrigir o caminho (`cd` para a raiz do clone, sem `projetoFabio`), descrever `/testar` como atalho de `scripts/testar.ps1 -Destacado -SemNavegador` e documentar `-Destacado` e `-Parar` (a implementação vem em T15; escreva o comportamento do spec, AMB-01), trocar `CUTOVER.md` por `DEPLOY.md` e tirar da seção "Onde ler mais" os caminhos `_reversa_*`. A seção "Testes automatizados" passa a citar `pip install -r requirements-dev.txt`.
**Where**: `TESTAR.md`
**Depends on**: T11
**Reuses**: `TESTAR.md` atual
**Requirement**: DOC-01 (TESTAR)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `TESTAR.md` entra na verificação de termos proibidos e "Tarefa NN"
- [x] O teste de higiene afirma que `TESTAR.md` cita `-Destacado`, `-Parar` e `requirements-dev.txt`
- [x] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(testar): alinhar o roteiro de teste ao repositorio clonado`

---

### T13: Emendar `PROJECT_RULES.md` para 1.2.0

**What**: Emenda MINOR, aprovada pela usuária com este spec. (1) Sync Impact Report no topo: 1.1.0 → 1.2.0, data 2026-09-24, o que mudou. (2) Remover o item de "Fluxo de Desenvolvimento" que torna `_reversa_sdd/` e `_reversa_forward/` fonte obrigatória; `.specs/` passa a ser a fonte, e os IDs herdados (`BR-*`, `RISK-*`, `D-*`, `P-*`) continuam válidos onde já aparecem. (3) Trocar `CUTOVER.md` por `DEPLOY.md` nas linhas de gate, de documentação acompanhada e de Governance. (4) Rodapé: `**Version**: 1.2.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-24`. Commit dedicado, só com este arquivo, este `tasks.md` e o teste de higiene (Governance).
**Where**: `.specs/PROJECT_RULES.md`
**Depends on**: T12
**Reuses**: formato do Sync Impact Report atual
**Requirement**: DOC-04 (AC9)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O teste de higiene afirma `**Version**: 1.2.0` no arquivo e a ausência dos termos proibidos
- [x] Os Princípios I–VII ficam com o texto inalterado (`git diff` só toca o cabeçalho, a seção "Fluxo de Desenvolvimento e Gates de Qualidade", Governance e o rodapé)
- [x] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [x] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(rules): emendar PROJECT_RULES para 1.2.0 sem fonte externa`

---

### T14: Atualizar `.specs/README.md`

**What**: Tirar o parágrafo sobre o Spec Kit e `APAGAR/`, e acrescentar uma linha dizendo que `.specs/features/<feature>/` guarda o histórico de cada feature (spec, tasks, validation), com as mais antigas podendo citar documentos que não existem mais.
**Where**: `.specs/README.md`
**Depends on**: T13
**Reuses**: nenhum
**Requirement**: DOC-04 (AC10)

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O teste de higiene afirma a ausência de `Spec Kit` e `APAGAR` em `.specs/README.md`
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(specs): tirar do indice a referencia ao Spec Kit arquivado`

---

### T15: `testar.ps1 -Destacado` e `-Parar`

**What**: Acrescentar dois switches a `scripts/testar.ps1`. `-Destacado`: depois dos passos 1–5 atuais, inicia `python run.py --host 127.0.0.1 --port $Porta` com `Start-Process -WindowStyle Hidden -PassThru`, com stdout e stderr redirecionados para arquivos em `$env:TEMP` (por exemplo, `calcsistec-<porta>.log` e `calcsistec-<porta>.err.log`). Espera até 60 s por `Get-NetTCPConnection -LocalPort $Porta -State Listen`, imprime URL, e-mail, senha, PID e os caminhos dos logs e sai com 0. No timeout, encerra o processo, imprime o caminho do log e sai com 1. Com `-Simulado`, sobe também `scripts/sistec_simulado.py` destacado (em vez de `Start-Job`). `-Parar`: encerra quem escuta em `$Porta` (e em 8051, se houver) e sai com 0; sem nada no ar, avisa e sai com 0. O modo atual (sem os switches) continua igual. As variáveis de ambiente que o script já define (hash da senha, `FLASK_SECRET_KEY`) precisam chegar ao processo filho, e a senha continua sem aparecer na linha de comando.
**Where**: `scripts/testar.ps1`
**Depends on**: None
**Reuses**: passos 1–5 atuais do script; `run.py` de T1
**Requirement**: AMB-01

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `tests/test_testar_ps1.py` ganha testes de integração marcados `skipif(sys.platform != "win32")` que usam uma porta livre (via `socket.bind(("127.0.0.1", 0))`) e `-SemNavegador`: `-Destacado` sai com 0 em menos de 60 s e a porta fica escutando (AC1); a saída cita um caminho de log dentro do diretório temporário e fora do repositório (AC2); segunda chamada com a porta ocupada sai com 1 e cita o PID (AC4); `-Parar` sai com 0 e libera a porta (AC5); `-Parar` sem nada no ar sai com 0 (AC5)
- [ ] O teste encerra o processo em `finally`, mesmo se uma asserção falhar, e não deixa arquivo novo no repositório (`git status --porcelain` igual antes e depois, ignorando `.env`)
- [ ] AC3 (timeout) coberto por teste que força a falha (por exemplo, uma variável de ambiente que o script lê para reduzir o timeout, combinada com uma porta que o app não vai abrir) **ou**, se isso exigir mudar o comportamento do produto, registrado como verificação manual no `validation.md` com o motivo
- [ ] Gate check passes: `python -m pytest -q`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(testar): subir o ambiente de teste destacado e derrubar com -Parar`

---

### T16: `/testar`, AGENTS.md e CLAUDE.md

**What**: (1) Criar `.claude/commands/testar.md`: frontmatter com `description` e `argument-hint: [simulado]`; corpo manda rodar `powershell -ExecutionPolicy Bypass -File scripts/testar.ps1 -Destacado -SemNavegador` (mais `-Simulado` quando `$ARGUMENTS` for `simulado`), repassar a saída à usuária e **não** acompanhar, consultar nem esperar o servidor depois; para derrubar, `-Parar`. (2) Em `AGENTS.md` (incorporando a mudança local que já tira a linha do Spec Kit/`APAGAR/`), acrescentar as seções "Começar" (ordem de leitura: `README.md` → `.specs/PROJECT_RULES.md` → `.specs/STATE.md`; gate `python -m pytest -q`) e "Subir o ambiente de teste" (os mesmos comandos e a regra de não monitorar), e a regra de não fazer `git push`, merge, PR nem deploy sem pedido explícito. (3) Criar `CLAUDE.md` com uma linha de contexto e `@AGENTS.md`.
**Where**: `AGENTS.md`, `.claude/commands/testar.md` (novo), `CLAUDE.md` (novo)
**Depends on**: T15
**Reuses**: `AGENTS.md` atual (com a mudança local)
**Requirement**: AMB-02

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O teste de higiene afirma: `.claude/commands/testar.md` contém `-Destacado` e `-SemNavegador`; `AGENTS.md` contém `-Destacado`, `-Parar` e a seção "Subir o ambiente de teste"; `CLAUDE.md` contém `@AGENTS.md`
- [ ] `AGENTS.md` e `CLAUDE.md` entram na verificação de termos proibidos
- [ ] `.claude/commands/testar.md` não é ignorado pelo Git (`.claude/settings.local.json` continua ignorado)
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(agentes): documentar o /testar e o guia comum para qualquer agente`

---

### T17: Bloco "Estado atual" no topo do Handoff de `STATE.md`

**What**: No início da seção `## Handoff` de `.specs/STATE.md`, um bloco "Estado atual" de no máximo 10 linhas: branch; última feature concluída; pendências humanas abertas (conferência dos KPIs de `correcao-matricula-atendida` no navegador; DS-42 em celular real; CSRF); follow-ups registrados (feature de refatoração de `app.py` em blueprints + IDs de spec nas docstrings + nomes em inglês; funções usadas só por testes: `filter_panel`, `agrupar_por_eixo`, `paginas_com_falha`, `deduplicar_por_campus`). Acrescente também o handoff desta feature.
**Where**: `.specs/STATE.md`
**Depends on**: T16
**Reuses**: Handoff atual
**Requirement**: EST-01

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O bloco tem no máximo 10 linhas e aparece antes de qualquer subseção `###` do Handoff
- [ ] `python -m pytest -q` passa (build gate de fim de fase)
- [ ] Test count: total anterior, 0 failed

**Tests**: none
**Gate**: build

**Commit**: `docs(state): resumir o estado atual no topo do handoff`

---

## Verificação (automática, depois de T17)

Verifier **independente**, em sessão separada da que implementou (author ≠ verifier), como nas features anteriores. Além do fluxo da skill:

- DEP-03: criar um venv no diretório temporário do sistema com Python 3.12, `pip install -r requirements-dev.txt`, rodar `python -m pytest -q` com esse venv e apagar o venv depois.
- Sensor de discriminação: pelo menos estas mutações precisam ser mortas: tirar `iniciar_varredura()` de `run.main`; chamá-la depois de `app.run`; recriar `t01_remover_pii`; voltar `requirements.txt` sem versão; reintroduzir `CUTOVER.md` em `README.md`; recriar `CUTOVER.md`; tirar `-Destacado` do `testar.ps1`.
- `validation.md` com PASS/FAIL, evidência `file:line` por AC e a faixa de commits.
- `validate_state.py limpeza-onboarding-repo` com saída 0.

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

Phase 1:  T1 → T2
Phase 2:  T3 → T4 → T5
Phase 3:  T6 → T7
Phase 4:  T8 → T9 → T10 → T11 → T12 → T13 → T14
Phase 5:  T15 → T16 → T17
```

Lotes para execução delegada (fases inteiras, cerca de 7 tarefas): **lote A** = fases 1–3 (T1–T7), **lote B** = fase 4 (T8–T14), **lote C** = fase 5 (T15–T17), depois o Verifier.

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | 1 função (`run.main`) | ✅ |
| T2 | 1 linha de 1 script | ✅ |
| T3 | 1 arquivo apagado + 1 menção em docstring | ✅ |
| T4 | 4 funções em 4 arquivos, mesma operação | ⚠️ coeso: só apagar código sem chamador, uma asserção por função |
| T5 | `.gitignore` + 2 itens não rastreados | ✅ |
| T6 | 2 arquivos de dependências | ⚠️ coeso: o `-dev` inclui o principal |
| T7 | 2 arquivos de configuração pequenos | ⚠️ coeso: ambiente de execução |
| T8 | docstrings de `app/` | ⚠️ mecânico, uma regra, um diretório |
| T9 | docstrings de `scripts/`/`tests/` + 1 mensagem | ✅ |
| T10 | 1 arquivo novo + 2 apagados | ✅ substituição |
| T11 | 1 arquivo | ✅ |
| T12 | 1 arquivo | ✅ |
| T13 | 1 arquivo | ✅ |
| T14 | 1 arquivo | ✅ |
| T15 | 1 script (2 switches) | ✅ |
| T16 | 3 arquivos de instrução para agentes | ⚠️ coeso: um aponta para o outro |
| T17 | 1 arquivo | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | None | início da fase 2 | ✅ |
| T4 | T3 | T3 → T4 | ✅ |
| T5 | T4 | T4 → T5 | ✅ |
| T6 | None | início da fase 3 | ✅ |
| T7 | T6 | T6 → T7 | ✅ |
| T8 | None | início da fase 4 | ✅ |
| T9 | T8 | T8 → T9 | ✅ |
| T10 | T9 | T9 → T10 | ✅ |
| T11 | T10 | T10 → T11 | ✅ |
| T12 | T11 | T11 → T12 | ✅ |
| T13 | T12 | T12 → T13 | ✅ |
| T14 | T13 | T13 → T14 | ✅ |
| T15 | None | início da fase 5 | ✅ |
| T16 | T15 | T15 → T16 | ✅ |
| T17 | T16 | T16 → T17 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | ponto de entrada | unit | unit | ✅ |
| T2 | script de teste (linha de subida) | integration/unit | unit (leitura do script; integração real em T15) | ✅ |
| T3 | código de `app/` removido | unit (higiene) | unit | ✅ |
| T4 | código de `app/` removido | unit (higiene) | unit | ✅ |
| T5 | configuração | unit (higiene) | unit | ✅ |
| T6 | configuração | unit (higiene) | unit | ✅ |
| T7 | configuração | unit (higiene) | unit | ✅ |
| T8 | docstrings de `app/` | unit (higiene) | unit | ✅ |
| T9 | docstrings + mensagem de script | unit (higiene) | unit | ✅ |
| T10 | documentação | unit (higiene) | unit | ✅ |
| T11 | documentação | unit (higiene) | unit | ✅ |
| T12 | documentação | unit (higiene) | unit | ✅ |
| T13 | documentação | unit (higiene) | unit | ✅ |
| T14 | documentação | unit (higiene) | unit | ✅ |
| T15 | script de teste | integration | integration | ✅ |
| T16 | documentação | unit (higiene) | unit | ✅ |
| T17 | `.specs/STATE.md` | none | none | ✅ |
