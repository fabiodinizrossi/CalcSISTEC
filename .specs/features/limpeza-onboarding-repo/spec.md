# Limpeza de resíduos e onboarding do repositório — Specification

## Problem Statement

Quem clona o repositório hoje não consegue começar sem ajuda. README, TESTAR, CUTOVER,
PARITY_REPORT, PROJECT_RULES e docstrings apontam para `_reversa_sdd/`, `_reversa_forward/`,
`cutover_plan.md` e `APAGAR/`, que não estão no repositório. README e TESTAR mandam usar um
comando `/testar` que não existe e um caminho (`projetoFabio\CalcSISTEC`) que não é o do clone.
`requirements.txt` não fixa versões e não lista `flask`, `werkzeug` e `pytest`; não há `.env.example`
nem versão de Python declarada.

Há também resíduos: um módulo inteiro sem uso (`app/data/validators.py`), funções sem nenhuma
chamada, e arquivos soltos na raiz (`nonascii.txt`, `chromedriver/`, que contraria o Princípio VI).

Um desses "resíduos" é um bug: `iniciar_varredura` (`app/sistec/execucoes.py:569`) é o watchdog
das execuções (encerra pausa com mais de 4 h e marca como falho o par de campus parado além do
limite, `execucoes.py:7-8`), mas ninguém a chama. Em produção, uma execução pausada ou travada
nunca expira sozinha.

## Goals

- [ ] Uma pessoa ou agente de LLM que clona o repositório instala, testa e sobe o app seguindo só
      README e AGENTS.md, sem referências a arquivos ausentes (verificado por teste automatizado).
- [ ] O watchdog de execuções roda sempre que o app sobe por `run.py` ou `scripts/testar.ps1`.
- [ ] Nenhum módulo ou função de `app/` fica sem referência (exceto as listadas em Out of Scope).
- [ ] `pip install -r requirements-dev.txt` num ambiente limpo com Python 3.12 instala versões fixas
      e o gate `python -m pytest -q` passa.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Dividir `app/app.py` (1034 linhas) em blueprints | Feature separada, com gate próprio; decisão da usuária em 2026-09-24. |
| Remover IDs de spec (`UPL-02`, `CPR-05`, `T17`, `RISK-009`…) de docstrings e comentários | Mesma feature separada da refatoração. Aqui saem só os **caminhos** para arquivos ausentes. |
| Renomear identificadores em inglês (`filter_panel`, `kpi_card`, `correction.py`…) | Mesma feature separada; renomear mexe em muitos chamadores e testes. |
| Funções usadas só por testes (`filter_panel`, `agrupar_por_eixo`, `paginas_com_falha`, `deduplicar_por_campus`) | Têm testes com comportamento definido; decidir entre ligar ou apagar exige olhar o fluxo de cada uma. Registradas como follow-up em STATE.md. |
| `scripts/testar.sh` (Linux/macOS) | A usuária não pediu; o fluxo de teste segue só em Windows. DEPLOY.md cobre a subida em Linux com `run.py`. |
| Artefatos históricos em `.specs/features/*/` que citam `CUTOVER.md` ou `_reversa_*` | São registro do que foi feito na época; reescrevê-los falsificaria o histórico. |
| `app/static/govbr-ds/dist/core.min.js` | Não é servido, mas `tests/test_shell_assets.py:157` o lê para provar AD-004; fica. |
| CI (GitHub Actions), LICENSE, CONTRIBUTING | Não pedidos; decisão de licença é da instituição. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Fonte das regras de negócio após remover `_reversa_*` | `.specs/` (PROJECT_RULES, STATE, specs de feature) é a única fonte; PROJECT_RULES perde a cláusula que obriga citar `_reversa_*` | As pastas não existem no repositório nem na pasta-mãe | y |
| Versão da emenda em PROJECT_RULES | 1.1.0 → **1.2.0** (MINOR): remove a fonte externa obrigatória e troca `CUTOVER.md` por `DEPLOY.md` nos gates | Muda orientação de fluxo, sem remover princípio | y (aprovação da usuária = confirmação deste spec) |
| Onde o watchdog é iniciado | Numa função `main()` de `run.py`, antes de `app.run`; `testar.ps1` passa a subir o app por `python run.py --host 127.0.0.1 --port N` | Importar `app.app` (testes, Dash) não pode criar thread; o ponto de entrada de processo é o lugar certo | y (decisão técnica; a usuária escolheu "ligar no startup") |
| `t01_remover_pii` | Apagar a função; `COLUNAS_PII` fica | A PII é barrada pela lista de permissão de colunas (`app/sistec/colunas.py:21-68`, que falha se a lista contiver PII); `t01_remover_pii` não tem chamador | y (verificado no código) |
| `.agents/`, `.uv-cache/`, `.uv-python/` | Entram no `.gitignore`; não são apagados | São estado de ferramentas locais da usuária, não do projeto | y |
| CUTOVER.md e PARITY_REPORT.md | Apagados; os itens ainda válidos (teste em celular real DS-42, CSRF, HTTPS, worker único, `verificar_prontidao_cutover.py`) vão para um `DEPLOY.md` novo | Decisão da usuária | y |
| Mudança local em AGENTS.md (remove a linha sobre `APAGAR/`) | Incorporada: AGENTS.md vira o guia canônico para qualquer agente, e `CLAUDE.md` só importa `@AGENTS.md` | Decisão da usuária | y |
| Comportamento do `/testar` | Sobe o ambiente em segundo plano, espera a porta abrir (máximo de 60 s), imprime URL, credenciais, PID e caminho do log, e **termina**. Não monitora | Pedido explícito da usuária: "só sobe o ambiente, não fica gastando token monitorando" | y |
| Como o `/testar` fica disponível a "qualquer agente" | A lógica fica no próprio `testar.ps1` (`-Destacado` para subir e sair, `-Parar` para derrubar); `.claude/commands/testar.md` e AGENTS.md só mandam rodar esse comando | Qualquer agente que executa shell roda o mesmo comando; o slash command é só um atalho do Claude Code | y |
| Versões fixadas | As instaladas hoje, que passam no gate de 939 testes: dash 4.4.1, dash-bootstrap-components 2.0.4, pandas 2.3.0, openpyxl 3.1.5, plotly 6.8.0, defusedxml 0.7.1, Pillow 11.2.1, Flask 3.1.3, Werkzeug 3.1.8; pytest 9.1.1 em `requirements-dev.txt` | Decisão da usuária: pinar as versões atuais | y |
| Versão de Python | `.python-version` com `3.12` | PROJECT_RULES (Restrições Técnicas) já fixa Python 3.12; o ambiente atual é 3.12.10 | y |

**Open questions:** none — todas resolvidas ou registradas acima.

---

## User Stories

### P1: Watchdog de execuções roda em produção ⭐ MVP

**User Story**: Como administradora, quero que uma execução pausada há mais de 4 h ou travada
num campus expire sozinha, para não ter de reiniciar o servidor para destravar a atualização.

**Why P1**: É bug de comportamento em produção; o resto da feature é documentação e limpeza.

**Acceptance Criteria**:

1. WHEN o processo sobe por `run.py` THEN o sistema SHALL chamar `execucoes.iniciar_varredura()`
   exatamente uma vez, antes de `app.run(...)`.
2. WHEN `run.py` recebe `--host H --port P` THEN o sistema SHALL chamar `app.run(host=H, port=P, debug=False)`;
   sem argumentos, SHALL usar `host="0.0.0.0"` e `port=8050`.
3. The system SHALL NOT criar a thread de varredura ao importar `app.app` (após o import,
   `execucoes._VARREDURA_THREAD` SHALL ser `None`).
4. WHEN `scripts/testar.ps1` sobe o app THEN o sistema SHALL fazê-lo por `python run.py --host 127.0.0.1 --port <Porta>`,
   de modo que o watchdog também rode no ambiente de teste.

**Independent Test**: Chamar `run.main(["--host", "127.0.0.1", "--port", "9999"])` com
`iniciar_varredura` e `app.run` substituídos por espiões; ver a ordem das chamadas e os argumentos.

---

### P1: Código e arquivos sem uso removidos ⭐ MVP

**User Story**: Como pessoa que dá manutenção, quero que todo código em `app/` seja usado, para
não gastar tempo entendendo o que não roda.

**Why P1**: Código morto engana quem lê e quem mede cobertura.

**Acceptance Criteria**:

1. The system SHALL NOT conter `app/data/validators.py`.
2. The system SHALL NOT definir `kpi_colunas` (`app/components/kpi.py`), `data_ultimo_upload_valido`
   (`app/data/consulta.py`), `t01_remover_pii` (`app/data/transform.py`) nem `_rotulo_eixo`
   (`app/pages/percentuais_legais.py`).
3. The system SHALL manter `COLUNAS_PII` em `app/data/transform.py` com o mesmo conteúdo.
4. The repository SHALL NOT conter `nonascii.txt` nem o diretório `chromedriver/`.
5. The `.gitignore` SHALL listar `.agents/`, `.uv-cache/` e `.uv-python/`.
6. WHEN a limpeza termina THEN `python -m pytest -q` SHALL passar com 0 falhas.

**Independent Test**: Um teste de higiene lista os símbolos acima e falha se algum existir.

---

### P1: Instalação reproduzível ⭐ MVP

**User Story**: Como pessoa da equipe que clona o repositório, quero instalar exatamente as versões
que passam nos testes, para não depurar incompatibilidade de biblioteca.

**Why P1**: Sem versões fixas, um `pip install` de amanhã pode quebrar o gate.

**Acceptance Criteria**:

1. The `requirements.txt` SHALL listar, cada um com `==`, exatamente: `dash==4.4.1`,
   `dash-bootstrap-components==2.0.4`, `pandas==2.3.0`, `openpyxl==3.1.5`, `plotly==6.8.0`,
   `defusedxml==0.7.1`, `Pillow==11.2.1`, `Flask==3.1.3`, `Werkzeug==3.1.8`.
2. The `requirements-dev.txt` SHALL conter `-r requirements.txt` e `pytest==9.1.1`.
3. The repository SHALL conter `.python-version` com o conteúdo `3.12`.
4. The repository SHALL conter `.env.example` com as chaves `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`,
   `FLASK_SECRET_KEY`, `CALCSISTEC_HTTPS`, `CALCSISTEC_SISTEC_BASE_URL`,
   `CALCSISTEC_PASTA_DOWNLOADS`, `CALCSISTEC_PASTA_COLETA` e `ANO_BASE`, todas com valor vazio
   ou de exemplo (nenhum segredo real).
5. WHEN um ambiente virtual limpo com Python 3.12 instala `requirements-dev.txt` THEN
   `python -m pytest -q` SHALL passar com 0 falhas.

**Independent Test**: Criar venv temporário no diretório temporário do sistema, instalar, rodar o gate, apagar o venv.

---

### P1: Documentação sem referências quebradas ⭐ MVP

**User Story**: Como pessoa ou agente que chega ao projeto, quero que todo arquivo, pasta e comando
citado nos documentos exista no repositório, para seguir as instruções sem ajuda.

**Why P1**: É o problema principal apontado pela usuária.

**Acceptance Criteria**:

1. The system SHALL NOT citar `_reversa_sdd`, `_reversa_forward`, `cutover_plan.md`, `APAGAR/`,
   `projetoFabio`, `PARITY_REPORT.md` ou `CUTOVER.md` em: `README.md`, `TESTAR.md`, `DEPLOY.md`,
   `AGENTS.md`, `CLAUDE.md`, `.specs/README.md`, `.specs/PROJECT_RULES.md`, arquivos `.py` de
   `app/`, `scripts/`, `tests/` e `run.py` (o próprio teste de higiene é a única exceção, porque
   lista esses termos).
2. The system SHALL NOT citar "Tarefa NN" (numeração do plano de reconstrução antigo) em
   `README.md`, `TESTAR.md` e `DEPLOY.md`.
3. The repository SHALL NOT conter `CUTOVER.md` nem `PARITY_REPORT.md`.
4. The repository SHALL conter `DEPLOY.md` com, no mínimo: pré-requisitos (Python 3.12, variáveis
   de `.env.example`), subida com `python run.py`, `CALCSISTEC_HTTPS=1` com certificado fora de
   `localhost`, um único worker/processo, rodar `scripts/verificar_prontidao_cutover.py` com saída 0,
   a pendência de validação em celular real (DS-42) e a pendência de CSRF (`app/config.py`).
5. WHEN `scripts/verificar_prontidao_cutover.py` imprime a seção fora do escopo automatizável
   THEN o sistema SHALL apontar para `DEPLOY.md`.
6. The `README.md` SHALL ter uma seção de estrutura que lista cada subdiretório direto de `app/`
   existente no repositório, mais `scripts/`, `tests/` e `.specs/`, cada um com uma linha de propósito.
7. The `README.md` SHALL ter uma seção "Começar" com a sequência: clonar, criar venv com
   Python 3.12, `pip install -r requirements-dev.txt`, copiar `.env.example` para `.env`,
   `python -m pytest -q`, subir o app.
8. The `README.md` SHALL ter uma seção "Onde mexer" que indica o arquivo ou diretório para, no
   mínimo: mudar uma regra de cálculo, adicionar uma página pública, mudar a coleta do Sistec,
   mudar o visual (DS/tema) e mudar uma rota administrativa.
9. The `.specs/PROJECT_RULES.md` SHALL estar na versão 1.2.0, com Sync Impact Report da emenda,
   sem a cláusula que torna `_reversa_*` fonte obrigatória e com `DEPLOY.md` no lugar de `CUTOVER.md`.
10. The `.specs/README.md` SHALL NOT mencionar o Spec Kit nem `APAGAR/`.

**Independent Test**: O teste de higiene percorre os arquivos listados e falha em qualquer termo proibido ou arquivo ausente.

---

### P1: Ambiente de teste acionável por qualquer agente ⭐ MVP

**User Story**: Como usuária que trabalha com agentes diferentes (Claude Code, Codex, DeepSeek),
quero um comando que suba o ambiente de teste e devolva o controle, para que o agente não gaste
tokens monitorando o servidor.

**Why P1**: Pedido explícito da usuária; README e TESTAR já prometem `/testar`.

**Acceptance Criteria**:

1. WHEN `scripts/testar.ps1 -Destacado` roda com a porta livre THEN o sistema SHALL iniciar o app
   em um processo separado, esperar a porta aceitar conexão por no máximo 60 s, imprimir URL de
   login, e-mail, senha, PID e caminho do arquivo de log, e sair com código 0.
2. WHILE o app sobe em modo `-Destacado`, o sistema SHALL gravar stdout e stderr em um arquivo de
   log no diretório temporário do sistema (`$env:TEMP`), nunca no repositório.
3. IF a porta não aceita conexão em 60 s THEN o sistema SHALL encerrar o processo iniciado,
   imprimir o caminho do log e sair com código 1.
4. IF a porta já está em uso THEN o sistema SHALL imprimir o PID que a ocupa e sair com código 1,
   sem iniciar outro processo (comportamento atual, mantido também em `-Destacado`).
5. WHEN `scripts/testar.ps1 -Parar` roda THEN o sistema SHALL encerrar o processo que escuta na
   porta (padrão 8050) e sair com código 0; IF nada escuta na porta THEN SHALL imprimir que não
   havia nada no ar e sair com código 0.
6. WHERE `-Simulado` é combinado com `-Destacado`, o sistema SHALL também subir o Sistec simulado
   destacado na porta 8051 e `-Parar` SHALL encerrar os dois.
7. The repository SHALL conter `.claude/commands/testar.md`, que manda rodar
   `scripts/testar.ps1 -Destacado -SemNavegador` (mais `-Simulado` quando o argumento for
   `simulado`), repassar a saída à usuária e **não** acompanhar o servidor depois.
8. The `AGENTS.md` SHALL conter uma seção "Subir o ambiente de teste" com os mesmos comandos
   (`-Destacado`, `-Parar`) e a instrução de não monitorar o processo depois de subir.
9. The repository SHALL conter `CLAUDE.md` cujo conteúdo importa `@AGENTS.md`.

**Independent Test**: Em Windows, rodar `testar.ps1 -Destacado -SemNavegador -Porta <livre>`, ver
código 0 e a porta aberta, rodar `-Parar -Porta <mesma>`, ver a porta livre.

---

### P2: Estado atual legível em STATE.md

**User Story**: Como pessoa que retoma o projeto, quero ler em poucas linhas onde o projeto está,
antes do histórico detalhado de handoffs.

**Why P2**: Ajuda o onboarding, mas não bloqueia instalar nem testar.

**Acceptance Criteria**:

1. The `.specs/STATE.md` SHALL começar a seção Handoff com um bloco "Estado atual" de no máximo 10
   linhas: branch, última feature concluída, pendências humanas abertas e follow-ups registrados
   (incluindo as funções usadas só por testes e a feature de refatoração de `app.py`).

**Independent Test**: Ler o topo do Handoff e responder "o que falta?" sem descer mais.

---

## Edge Cases

- IF `run.py` recebe uma porta que não é número inteiro THEN o sistema SHALL sair com código 2
  (erro padrão do `argparse`) sem iniciar a varredura.
- IF `iniciar_varredura` é chamada duas vezes no mesmo processo THEN o sistema SHALL manter uma
  única thread viva (idempotência já existente, `execucoes.py:571-573`).
- WHEN o `.env` não existe e `testar.ps1 -Destacado` roda THEN o sistema SHALL criá-lo como hoje,
  antes de subir o processo.
- IF o teste de higiene encontra um termo proibido THEN a mensagem de falha SHALL citar o arquivo
  e o termo encontrados.

---

## Implicit-requirement dimensions

| Dimensão | Resolução |
| --- | --- |
| Input validation & bounds | `run.py` valida `--port` como inteiro (argparse); edge case acima. |
| Failure / partial-failure | Timeout de 60 s em `-Destacado` encerra o processo e sai com 1 (Ambiente AC3). |
| Idempotency / retry | `iniciar_varredura` idempotente (edge case); `-Parar` sem nada no ar sai com 0 (Ambiente AC5). |
| Auth boundaries | O app de teste continua preso a `127.0.0.1`; a senha continua saindo do `.env`, nunca da linha de comando (Watchdog AC4). |
| Concurrency / ordering | Varredura inicia antes de `app.run` (Watchdog AC1); produção segue com um único worker (DEPLOY.md). |
| Data lifecycle | Log do modo destacado fica em `$env:TEMP`, fora do repositório (Ambiente AC2). |
| Observability | Modo destacado imprime PID e caminho do log (Ambiente AC1). |
| External-dependency failure | N/A porque a feature não muda chamadas ao Sistec. |
| State-transition integrity | N/A porque a lógica de `varrer` não muda; só passa a ser chamada. Os testes de `varrer` já existem (`tests/test_execucoes.py:159-198`). |

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| WDG-01 | P1: Watchdog — AC1, AC2, edge case de porta inválida | Tasks | Pending |
| WDG-02 | P1: Watchdog — AC3 (import sem thread) | Tasks | Pending |
| WDG-03 | P1: Watchdog — AC4 (testar.ps1 usa run.py) | Tasks | Pending |
| LIM-01 | P1: Código sem uso — AC1, AC2, AC3 | Tasks | Pending |
| LIM-02 | P1: Código sem uso — AC4, AC5 | Tasks | Pending |
| DEP-01 | P1: Instalação — AC1, AC2 | Tasks | Pending |
| DEP-02 | P1: Instalação — AC3, AC4 | Tasks | Pending |
| DEP-03 | P1: Instalação — AC5 (venv limpo) | Validate | Pending |
| DOC-01 | P1: Documentação — AC1, AC2, AC3 (teste de higiene) | Tasks | Pending |
| DOC-02 | P1: Documentação — AC4, AC5 (DEPLOY.md) | Tasks | Pending |
| DOC-03 | P1: Documentação — AC6, AC7, AC8 (README) | Tasks | Pending |
| DOC-04 | P1: Documentação — AC9, AC10 (PROJECT_RULES, .specs/README) | Tasks | Pending |
| AMB-01 | P1: Ambiente — AC1..AC6 (testar.ps1 -Destacado/-Parar) | Tasks | Pending |
| AMB-02 | P1: Ambiente — AC7, AC8, AC9 (/testar, AGENTS.md, CLAUDE.md) | Tasks | Pending |
| EST-01 | P2: STATE.md — AC1 | Tasks | Pending |

**Coverage:** 15 total, 15 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `python -m pytest -q` passa com 0 falhas, incluindo o teste de higiene novo.
- [ ] Um venv limpo instala `requirements-dev.txt` e passa no gate.
- [ ] `testar.ps1 -Destacado -SemNavegador` devolve o controle em menos de 60 s, com o app no ar;
      `testar.ps1 -Parar` derruba o app.
- [ ] Nenhum termo proibido (DOC-01) aparece nos arquivos listados.
