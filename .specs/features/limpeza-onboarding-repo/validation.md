# Limpeza de resíduos e onboarding do repositório — Validation

## Validation — `limpeza-onboarding-repo`: FAIL ❌

**Date**: 2026-09-24
**Spec**: `.specs/features/limpeza-onboarding-repo/spec.md`
**Diff range**: `b68118e..506c1b5` (17 commits, 17 tarefas)
**Verifier**: sub-agente independente (author ≠ verifier)

**Veredito**: **FAIL**. O produto está correto em tudo o que foi exercitado — 985 passed, 0 failed; os
quatro requisitos-chave (watchdog, limpeza, instalação fixa, documentação sem caminho quebrado) foram
reproduzidos com evidência. O FAIL vem do **sensor de discriminação**: 4 de 15 mutantes sobreviveram,
e três deles atingem ACs P1 (AMB-01 AC1 duas vezes, AMB-01 AC6 uma). Os testes não pinam o limite de
60 s, nem a impressão de e-mail/senha, nem metade automatizável do `-Simulado`. Nada disso é defeito do
código: é teste fraco onde a spec é precisa. Os gaps ranqueados estão no fim.

---

## Task Completion

Todas as 17 tarefas estão `[x]` em `tasks.md`. Verificado por commit: um commit por tarefa, na faixa
`b68118e..506c1b5`, com a marcação `[x]` no mesmo commit.

| Task | Status | Commit |
| ---- | ------ | ------ |
| T1 | ✅ Done | `492f086` |
| T2 | ✅ Done | `2fa2c65` |
| T3 | ✅ Done | `b26e7c6` |
| T4 | ✅ Done | `e4e0974` |
| T5 | ✅ Done | `01f732d` |
| T6 | ✅ Done | `8386596` |
| T7 | ✅ Done | `f28f685` |
| T8 | ✅ Done | `9b6eda0` |
| T9 | ✅ Done | `c39d604` |
| T10 | ✅ Done | `89c76f1` |
| T11 | ✅ Done | `942824d` |
| T12 | ✅ Done | `979a0e4` |
| T13 | ✅ Done | `3bff893` |
| T14 | ✅ Done | `eb67820` |
| T15 | ✅ Done | `dcb95cf` |
| T16 | ✅ Done | `a3829bf` |
| T17 | ✅ Done | `506c1b5` |

---

## Gate Check

- **Gate command**: `python -m pytest -q -p no:cacheprovider` (Build gate de `tasks.md`)
- **Result**: **985 passed, 0 failed, 0 skipped** em 138,52 s
- **Test count antes da feature**: 939 (`21941fd`)
- **Test count depois da feature**: 985
- **Delta**: **+46 testes**, **0 testes deletados** e nenhuma asserção enfraquecida
  (`git diff --diff-filter=D b68118e..506c1b5` só lista `CUTOVER.md`, `PARITY_REPORT.md` e
  `app/data/validators.py`; os arquivos de teste que já existiam só mudaram docstring —
  conferido por tokenização, sem comentários e sem docstrings)
- **Failures**: nenhuma

---

## Spec-Anchored Acceptance Criteria

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| WDG-01 AC1 WHEN sobe por `run.py` THEN chama `iniciar_varredura()` uma vez, antes de `app.run` | exatamente 1 chamada de cada, varredura primeiro | `tests/test_run.py:40` — `assert len(espioes) == 2`; `espioes[0] == "varredura"`; `espioes[1][0] == "run"` (`:43-45`) | ✅ PASS |
| WDG-01 AC2 `--host H --port P` repassados; padrão `0.0.0.0`/`8050` | `app.run(host=H, port=P, debug=False)` | `tests/test_run.py:48` — `assert espioes[1] == ("run", {"host":"127.0.0.1","port":9999,"debug":False})`; padrão em `:54` — `{"host":"0.0.0.0","port":8050,"debug":False}` | ✅ PASS |
| WDG-01 edge `--port abc` sai com 2 sem iniciar varredura | `SystemExit` código 2, zero chamadas | `tests/test_run.py:60` — `assert excinfo.value.code == 2`; `:65` — `assert espioes == []`; subprocesso em `:68-81` (rc 2) | ✅ PASS |
| WDG-02 AC3 importar `app.app` não cria thread | `execucoes._VARREDURA_THREAD is None` | `tests/test_run.py:84` — subprocesso imprime o global; `:98` — `assert resultado.stdout.strip() == "None"` | ✅ PASS |
| WDG-03 AC4 `testar.ps1` sobe por `python run.py --host 127.0.0.1 --port <Porta>` | string exata no script | `tests/test_testar_ps1.py:37` — `assert "run.py --host 127.0.0.1 --port $Porta" in ler_script()`; `scripts/testar.ps1:245` | ✅ PASS |
| WDG-03 AC4 (contraprova: nenhum `app.run` avulso) | `app.run(` ausente | `tests/test_testar_ps1.py:41` — `assert "app.run(" not in ler_script()` | ✅ PASS |
| LIM-01 AC1 sem `app/data/validators.py` | arquivo inexistente | `tests/test_higiene_repositorio.py:274` — `assert not os.path.exists(caminho("app","data","validators.py"))` | ✅ PASS |
| LIM-01 AC2 sem `kpi_colunas`, `data_ultimo_upload_valido`, `t01_remover_pii`, `_rotulo_eixo` | nenhum dos 4 nomes definido no seu arquivo (AST) | `tests/test_higiene_repositorio.py:287` parametrizado por `:279-284` — `assert nome not in definicoes(arquivo_relativo)` | ✅ PASS |
| LIM-01 AC3 `COLUNAS_PII` mantida com o mesmo conteúdo | lista idêntica à de antes da feature | `tests/test_higiene_repositorio.py:307` — `assert COLUNAS_PII == COLUNAS_PII_ESPERADAS` (`:293-304`); comparei por AST com `b68118e`: 10 entradas, `iguais: True` | ✅ PASS |
| LIM-02 AC4 sem `nonascii.txt` nem `chromedriver/` | ambos ausentes | `tests/test_higiene_repositorio.py:314` — duas asserções de `os.path.exists` falso | ✅ PASS |
| LIM-02 AC5 `.gitignore` lista `.agents/`, `.uv-cache/`, `.uv-python/` | 3 entradas, e as pastas continuam no disco | `tests/test_higiene_repositorio.py:324` — `assert entrada in linhas`; `.gitignore:13-15`; as três pastas existem na raiz | ✅ PASS |
| DEP-01 AC1 `requirements.txt` com exatamente 9 pacotes `==` | lista exata das 9 versões | `tests/test_higiene_repositorio.py:353` — `assert linhas_uteis("requirements.txt") == REQUIREMENTS_ESPERADOS` (`:340-350`) | ✅ PASS |
| DEP-01 AC2 `requirements-dev.txt` = `-r requirements.txt` + `pytest==9.1.1` | duas linhas exatas | `tests/test_higiene_repositorio.py:358` — `assert linhas_uteis("requirements-dev.txt") == ["-r requirements.txt","pytest==9.1.1"]` | ✅ PASS |
| DEP-02 AC3 `.python-version` com `3.12` | conteúdo exato | `tests/test_higiene_repositorio.py:366` — `assert linhas_uteis(".python-version") == ["3.12"]` | ✅ PASS |
| DEP-02 AC4 `.env.example` com as 8 chaves, sem segredo real | as 8 chaves presentes; nenhum segredo | `tests/test_higiene_repositorio.py:394` — `assert chave in valores` (`:371-380`); `:402` — `FLASK_SECRET_KEY == ""` e `ADMIN_PASSWORD_HASH == ""` | ✅ PASS (asserção parcial — ver precisão nº 1) |
| DEP-03 AC5 venv limpo Python 3.12 instala e passa no gate | 0 falhas no gate | ver **DEP-03** abaixo | ✅ PASS |
| DOC-01 AC1 sem termos proibidos nos arquivos listados | nenhum dos 7 termos, nos 7 documentos e nos `.py` | `tests/test_higiene_repositorio.py:56` e `:66` (`.py` de `app/`, `scripts/`, `tests/`, `run.py`) e `:94` (docs, parametrizado por `:81-88`) — `pytest.fail(f"{arquivo} cita {termo}")`; grep independente: zero ocorrências | ✅ PASS (lista incompleta — ver gap G6) |
| DOC-01 AC2 sem "Tarefa NN" em README/TESTAR/DEPLOY | `"Tarefa "` ausente nos 3 | `tests/test_higiene_repositorio.py:90` (`TERMOS_PROIBIDOS_EM_DOCS`) aplicado pelo teste `:94`; grep independente: zero ocorrências | ✅ PASS |
| DOC-01 AC3 sem `CUTOVER.md` nem `PARITY_REPORT.md` | os dois ausentes, `DEPLOY.md` presente | `tests/test_higiene_repositorio.py:124-128` | ✅ PASS |
| DOC-01 AC4 `DEPLOY.md` com pré-requisitos, subida, HTTPS, worker único, prontidão, DS-42, CSRF | cada marcador presente | `tests/test_higiene_repositorio.py:141` com marcadores `:131-138`; leitura independente de `DEPLOY.md:7-19,21-37,39-49,51-59,75-106` | ✅ PASS |
| DOC-01 AC5 seção fora do escopo aponta para `DEPLOY.md` | saída com `DEPLOY.md`, sem `CUTOVER.md` | `tests/test_higiene_repositorio.py:263` — `assert "DEPLOY.md" in saida`; `:271` — `assert "CUTOVER.md" not in saida`; `scripts/verificar_prontidao_cutover.py:152` | ✅ PASS |
| DOC-03 AC6 README lista cada subdiretório de `app/` + `scripts/`, `tests/`, `.specs/` | lista montada do disco, com propósito | `tests/test_higiene_repositorio.py:155` — `assert f"app/{pasta}/" in conteudo` (subpastas lidas de `os.listdir`) e `:169-170` para as três pastas | ✅ PASS |
| DOC-03 AC7 "Começar" na ordem venv → `requirements-dev.txt` → `.env.example` → `pytest` → subir | ordem das três menções | `tests/test_higiene_repositorio.py:173` — `assert ordem == sorted(ordem)` (`:180-186`); `README.md:7-57` | ✅ PASS |
| DOC-03 AC8 "Onde mexer" cobre os 5 temas | seção presente e com os 5 destinos | `tests/test_higiene_repositorio.py:177` — `assert "## Onde mexer" in conteudo`; os 5 temas existem em `README.md:87-91`, mas **não** são asseverados (ver gap G5) | ⚠️ GAP |
| DOC-01 AC1 (README sem caminho inexistente) | todo caminho relativo citado existe | `tests/test_higiene_repositorio.py:192` — `assert os.path.exists(...)` por caminho entre crases | ✅ PASS |
| DOC-04 AC9 `PROJECT_RULES.md` 1.2.0, Sync Impact Report, sem fonte obrigatória `_reversa_*`, `DEPLOY.md` no lugar de `CUTOVER.md` | versão 1.2.0 + termos proibidos fora | `tests/test_higiene_repositorio.py:105` — `assert "**Version**: 1.2.0" in conteudo`; `:112` — nenhum termo proibido; conferi que os **Princípios I–VII são byte a byte iguais** a `b68118e` (4675 bytes, diff vazio) | ✅ PASS |
| DOC-04 AC10 `.specs/README.md` sem Spec Kit nem `APAGAR/` | dois termos ausentes | `tests/test_higiene_repositorio.py:115-121` | ✅ PASS (lista incompleta — ver gap G6) |
| AMB-01 AC1 `-Destacado` com porta livre: processo separado, espera ≤ 60 s, URL/e-mail/senha/PID/log, sai 0 | rc 0, porta aberta, 4 informações | `tests/test_testar_ps1.py:147` — `returncode == 0` (`:154`), `escutando(porta)` (`:155`), log em `%TEMP%` e fora do repositório (`:160-161`), `"PID" in stdout` (`:164`). **Não** asserta o limite de 60 s, o e-mail nem a senha | ⚠️ GAP |
| AMB-01 AC2 log do `-Destacado` no `%TEMP%`, nunca no repositório | caminho fora da raiz | `tests/test_testar_ps1.py:157` — `assert os.path.join(TEMPORARIO, f"calcsistec-{porta}.log") in subida.stdout`; `:161` — `assert RAIZ not in linha_log`; `:188` — nenhum log criado quando a porta está ocupada | ✅ PASS |
| AMB-01 AC3 sem porta em 60 s: encerra o processo, imprime o log, sai 1 | rc 1, log citado, porta livre | `tests/test_testar_ps1.py:191` — `returncode == 1` (`:207`), `f"calcsistec-{porta}.log" in stdout` (`:208`), `not escutando(porta)` (`:209`). O teste encurta a espera por `CALCSISTEC_TESTAR_TIMEOUT`; o padrão de 60 s é o que fica sem asserção (gap G1) | ✅ PASS |
| AMB-01 AC4 porta em uso: imprime o PID que a ocupa e sai 1, sem subir outro | rc 1, PID de quem ocupa, porta intacta | `tests/test_testar_ps1.py:175` — `assert saida.returncode == 1` (`:184`), `assert str(os.getpid()) in saida.stdout` (`:185`), `assert escutando(porta)` (`:186`), `scripts/testar.ps1:193-208` | ✅ PASS |
| AMB-01 AC5 `-Parar` encerra quem escuta e sai 0; nada no ar → avisa e sai 0 | rc 0 nos dois casos | `tests/test_testar_ps1.py:166` — `returncode == 0` + `not escutando(porta)` (`:169`); `:216` — `returncode == 0` (`:222`) e `assert "nada no ar" in saida.stdout.lower()` (`:223`) | ✅ PASS |
| AMB-01 AC6 `-Destacado -Simulado` sobe o simulado na 8051 destacado e `-Parar` derruba os dois | app + simulado no ar; `-Parar` encerra os dois | **nenhum teste automatizado**; reproduzido por mim à mão (ver **AMB-01 AC6** abaixo) | ⚠️ GAP |
| AMB-02 AC7 `.claude/commands/testar.md` com `-Destacado -SemNavegador` (+ `-Simulado`), repassar a saída e **não** monitorar | arquivo versionado, com os switches e a regra de não monitorar | `tests/test_higiene_repositorio.py:215` — `-Destacado`, `-SemNavegador`, `-Parar`; `:230` — `git check-ignore` falha e `ls-files` do `settings.local.json` falha; conteúdo em `.claude/commands/testar.md:1-27` (a regra "**Não** acompanhe o servidor" não é asseverada) | ✅ PASS (asserção parcial — precisão nº 2) |
| AMB-02 AC8 `AGENTS.md` com a seção "Subir o ambiente de teste", os comandos e a regra de não monitorar | seção + `-Destacado` + `-Parar` | `tests/test_higiene_repositorio.py:238` — `assert "## Subir o ambiente de teste" in conteudo` (`:243-245`); a regra de não monitorar não é asseverada | ✅ PASS (asserção parcial — precisão nº 2) |
| AMB-02 AC9 `CLAUDE.md` importa `@AGENTS.md` | string presente | `tests/test_higiene_repositorio.py:248` | ✅ PASS |
| EST-01 bloco "Estado atual" no topo do Handoff, ≤ 10 linhas, antes de qualquer `###` | ≤ 10 linhas, com branch, última feature, pendências e follow-ups | sem teste (a matriz de `tasks.md` diz "none — build gate only"); verificado por inspeção: `.specs/STATE.md:61-71` — 6 bullets, antes do primeiro `###` (`:77`), com branch, `correcao-matricula-atendida`, as 3 pendências humanas e os dois follow-ups (refatoração de `app.py`; funções usadas só por testes) | ✅ PASS (por inspeção) |

**Status**: ❌ Gaps presentes — 2 ACs com asserção parcial (DOC-03 AC8, AMB-01 AC1) e 1 AC P1 sem
teste (AMB-01 AC6).

---

## Edge Cases

| Edge case (spec) | Evidência | Result |
| --- | --- | --- |
| `--port` não inteiro → sai com 2 sem iniciar varredura | `tests/test_run.py:60-65` — `assert excinfo.value.code == 2` e `assert espioes == []`; subprocesso em `:68-81` | ✅ PASS |
| `iniciar_varredura` chamada duas vezes → uma única thread viva | **sem teste**; o mutante M11 (remover a guarda `app/sistec/execucoes.py:571-573`) sobreviveu — gap G4 | ❌ GAP |
| `.env` ausente + `-Destacado` → cria o `.env` antes de subir | **sem asserção**; o caminho existe em `scripts/testar.ps1:122-134` e é exercitado em qualquer runner sem `.env`, mas nenhum teste apaga o `.env` e afirma que ele foi criado — gap G7 | ❌ GAP |
| Termo proibido encontrado → mensagem cita arquivo e termo | `tests/test_higiene_repositorio.py:63`, `:78` e `:102` — `pytest.fail(f"{...} cita {termo}")`; a mensagem traz caminho relativo e termo. É o próprio teste, então não há teste de teste; conferido por inspeção | ✅ PASS (por inspeção) |

---

## Discrimination Sensor

Cópia isolada em `git worktree add --detach` no diretório temporário do sistema (`/tmp/calcsistec-sensor-wt`,
fora do repositório), descartada no fim. Nunca usei `git stash` nem editei a árvore real.
**Sensor depth**: expandido (15 mutações, acima do mínimo de 7 pedido em `tasks.md`).
**Resultado**: **15 mutações, 11 mortas, 4 sobreviventes**.

| # | Mutação | Arquivo | Alvo dos testes | Resultado |
| --- | --- | --- | --- | --- |
| M1 | tirar `iniciar_varredura()` de `run.main` | `run.py:28` | `tests/test_run.py` | ✅ MORTO (3 failed) |
| M2 | chamar `iniciar_varredura()` **depois** de `app.run` | `run.py:28-29` | `tests/test_run.py` | ✅ MORTO (3 failed) |
| M3 | recriar `t01_remover_pii` em `app/data/transform.py` | `app/data/transform.py` | `tests/test_higiene_repositorio.py` | ✅ MORTO (1 failed) |
| M4 | `requirements.txt` sem versão fixa | `requirements.txt` | `tests/test_higiene_repositorio.py` | ✅ MORTO (1 failed) |
| M5 | reintroduzir a string `CUTOVER.md` em `README.md` | `README.md` | `tests/test_higiene_repositorio.py` | ✅ MORTO (1 failed) |
| M6 | recriar o arquivo `CUTOVER.md` na raiz | `CUTOVER.md` | `tests/test_higiene_repositorio.py` | ✅ MORTO (1 failed) |
| M7 | tirar o tratamento de `-Destacado` do `testar.ps1` (switch + bloco) | `scripts/testar.ps1:53,233-276` | `tests/test_testar_ps1.py` | ✅ MORTO (3 failed) |
| M8 | `iniciar_varredura` no import de `app.app` (WDG-02) | `app/app.py` (fim do módulo) | `tests/test_run.py` | ✅ MORTO (1 failed) |
| M9 | timeout padrão do `-Destacado`: 60 s → 30 s | `scripts/testar.ps1:236` | `tests/test_testar_ps1.py` | ❌ **SOBREVIVEU** (0 failed) → gap G1 |
| M10 | `-Parar` sem nada no ar sai com 1 | `scripts/testar.ps1:88` | `tests/test_testar_ps1.py -k parar_sem_nada` | ✅ MORTO (1 failed) |
| M11 | remover a guarda de idempotência de `iniciar_varredura` | `app/sistec/execucoes.py:571-573` | `tests/test_execucoes.py tests/test_run.py` | ❌ **SOBREVIVEU** → gap G4 |
| M12 | `-Destacado` deixa de imprimir a senha | `scripts/testar.ps1:215` | `tests/test_testar_ps1.py -k destacado` | ❌ **SOBREVIVEU** → gap G2 |
| M13 | `-Parar` deixa de encerrar o simulado da 8051 | `scripts/testar.ps1:82` | `tests/test_testar_ps1.py -k "parar_sem_nada or sobe_o_app_por_run_py"` | ❌ **SOBREVIVEU** → gap G3 |
| M14 | porta padrão do `run.py`: 8050 → 8051 | `run.py:18` | `tests/test_run.py` | ✅ MORTO (1 failed) |
| M15 | mensagem da prontidão volta a citar `CUTOVER.md` | `scripts/verificar_prontidao_cutover.py:152` | `tests/test_higiene_repositorio.py` | ✅ MORTO (2 failed) |

**Isolamento**: `git status --porcelain` da árvore real medido antes do sensor (vazio) e depois da
limpeza (vazio) — igual. O worktree foi removido (`git worktree list` só mostra o repositório principal).

---

## DEP-03 (venv limpo)

| Passo | Comando | Resultado |
| --- | --- | --- |
| venv no diretório temporário do sistema | `python -m venv %TEMP%\calcsistec-dep03-venv` | ok — `Python 3.12.10` |
| instalação | `<venv>\Scripts\python.exe -m pip install -r requirements-dev.txt` | ok; `pip freeze` mostra `dash==4.4.1`, `dash-bootstrap-components==2.0.4`, `pandas==2.3.0`, `openpyxl==3.1.5`, `plotly==6.8.0`, `defusedxml==0.7.1`, `pillow==11.2.1`, `Flask==3.1.3`, `Werkzeug==3.1.8`, `pytest==9.1.1` |
| gate | `<venv>\Scripts\python.exe -m pytest -q -p no:cacheprovider` | **985 passed, 0 failed** em 124,77 s (exit 0) |
| limpeza | `rm -rf` do venv | ok — nada deixado no repositório |

O venv foi criado e apagado dentro do diretório temporário do sistema; o repositório continuou limpo
(`git status --porcelain` vazio antes e depois).

---

## Conferências extras

| Conferência | Resultado | Evidência |
| --- | --- | --- |
| `.py` de `9b6eda0` e `c39d604`: só docstring/comentário mudou | ✅ | AST sem docstrings **idêntica** em todos os 16 `.py` de `app/` de `9b6eda0` e nos 3 de `test_*` de `c39d604`; a comparação por token (sem comentários, sem docstrings) só acusa `scripts/verificar_prontidao_cutover.py` (a mensagem, exceção esperada) e `tests/test_higiene_repositorio.py` (testes novos que o próprio T8/T9 exigia) |
| Princípios I–VII de `PROJECT_RULES.md` iguais a `b68118e` | ✅ | bloco `## Core Principles` → `## Restrições Técnicas`: **byte a byte iguais** (4675 bytes cada, diff vazio) |
| README não cita caminho inexistente | ✅ | `tests/test_higiene_repositorio.py:192-203` passa; leitura independente do `README.md` não achou caminho entre crases sem arquivo |
| `testar.ps1` não põe a senha na linha de comando do filho | ✅ | a senha vai por `$env:SENHA_TEMP` (`scripts/testar.ps1:148-152`); com o app no ar, `Get-CimInstance Win32_Process` mostrou a linha de comando do filho `"...python.exe" run.py --host 127.0.0.1 --port 59370` e **nenhum** processo com a senha na linha de comando |
| Faixa de diff | ✅ | `b68118e..506c1b5` = 17 commits; `git diff --diff-filter=D` só lista `CUTOVER.md`, `PARITY_REPORT.md`, `app/data/validators.py` |
| 8050 intacta | ✅ | PID 5644 escutando antes e depois de todos os testes (o da usuária; nunca chamado sem `-Porta` livre) |

### AMB-01 AC6 — verificação manual reproduzida pelo Verifier

O implementador registrou o AC6 como verificação manual (evidência em `.specs/STATE.md:71`: app na
64006, simulado na 8051, `-Parar` encerrou os PIDs 4032 e 25568, 8050 intacta). Como a **8051 estava
livre** nesta sessão, repeti o teste em porta livre:

1. `powershell -File scripts/testar.ps1 -Destacado -SemNavegador -Simulado -Porta 61019` → exit 0;
   `Get-NetTCPConnection` mostrou **61019 = PID 15984** (app) e **8051 = PID 37008** (simulado), com a
   8050 intacta (PID 5644).
2. `powershell -File scripts/testar.ps1 -Parar -Simulado -Porta 61019` → exit 0, com a saída
   `Encerrado o processo 15984 (porta 61019).` e `Encerrado o processo 37008 (porta 8051).`; depois
   disso só a 8050 continuava escutando.

Ou seja: o comportamento do AC6 está correto (depende de passar `-Simulado` no `-Parar`, como o
`.claude/commands/testar.md` documenta). O que falta é o teste automatizado — gap G3.

---

## Code Quality

| Princípio | Status |
| --- | --- |
| Código mínimo / sem abstração para uso único | ✅ |
| Mudanças cirúrgicas (só o arquivo da tarefa) | ✅ |
| Sem scope creep | ✅ |
| Segue os padrões do repositório | ✅ |
| Cada teste mapeia para um AC, edge case ou "Done when" | ✅ |
| Asserted values conferem com o resultado da spec | ⚠️ AMB-01 AC1 (60 s/e-mail/senha) e DOC-03 AC8 |
| Guidelines documentadas seguidas (`AGENTS.md`, `.specs/PROJECT_RULES.md` Princípio IV) | ✅ — um commit por tarefa, gate completo em toda tarefa de `.py` |

Nenhuma linha de código executável mudou em `9b6eda0`/`c39d604` (só docstring e comentário), o que
respeita o Out of Scope de "IDs de spec" e a instrução de não renomear identificadores.

---

## Gaps (ranqueados)

### G1 — AMB-01 AC1: o limite de 60 s não está pinado em teste algum (Major)

`tests/test_testar_ps1.py:147-172` asserta `returncode == 0`, a porta aberta, `"PID" in stdout` e o
caminho do log; o mutante M9 (`$limite = 60` → `$limite = 30`, `scripts/testar.ps1:236`) **passou na
suíte inteira**. A spec é precisa ("esperar a porta aceitar conexão por no máximo 60 s") e o teste não
alcança o valor.

**Correção sugerida**: asserção de unidade no `tests/test_testar_ps1.py` de que o script mantém o
padrão de 60 s (por exemplo, `assert "$limite = 60" in ler_script()` e ausência de outro valor
atribuído a `$limite`), mantendo o escape `CALCSISTEC_TESTAR_TIMEOUT` só para encurtar o teste.

### G2 — AMB-01 AC1: e-mail e senha não são asseverados na saída do `-Destacado` (Major)

O AC1 exige imprimir "URL de login, e-mail, senha, PID e caminho do arquivo de log". O mutante M12
(apagar `scripts/testar.ps1:215`, a linha `Senha:`) **sobreviveu** à suíte. `str(porta) in stdout`
também é asserção fraca para "URL de login" — a porta aparece em várias linhas.

**Correção sugerida**: assertar que a saída contém `http://localhost:<porta>/admin/login`, o
`ADMIN_EMAIL` e o `ADMIN_SENHA` lidos do `.env` do próprio runner.

### G3 — AMB-01 AC6: nenhum teste automatizado para `-Simulado` (Major)

Não existe teste que combine `-Simulado` com `-Destacado`, nem que verifique o `-Parar -Simulado`
encerrando a 8051 (`scripts/testar.ps1:82`). O mutante M13 **sobreviveu**. O comportamento foi
verificado à mão nesta sessão e funciona (ver acima), mas a metade automatizável do AC não está pinada.

**Correção sugerida**: teste de integração em porta livre com `-Simulado`, pulando (`skipif`) quando a
8051 já estiver ocupada, e `-Parar -Simulado` no `finally`.

### G4 — Edge case de idempotência de `iniciar_varredura` sem teste (Minor)

O spec lista "chamada duas vezes → uma única thread viva" (`app/sistec/execucoes.py:571-573`) e o
mutante M11 (remover a guarda) **sobreviveu**. É código pré-existente, fora da superfície nova da
feature, mas o edge case está declarado no spec.

**Correção sugerida**: teste unitário que chama `iniciar_varredura()` duas vezes com `INTERVALO` curto
e afirma uma única thread viva (e um único `_loop`).

### G5 — DOC-03 AC8: o teste só verifica que a seção existe (Minor)

`tests/test_higiene_repositorio.py:177` asserta `"## Onde mexer" in conteudo`; os cinco temas exigidos
(regra de cálculo, página pública, coleta do Sistec, visual, rota administrativa) não são asseverados.
O README os cobre (`README.md:87-91`), então é fragilidade de teste, não defeito.

**Correção sugerida**: assertar os cinco destinos exigidos pelo AC.

### G6 — DOC-01 AC1: lista de termos do teste mais estreita que o AC (Minor)

O AC manda barrar `projetoFabio` nos `.py` de `app/`, `scripts/`, `tests/` e `run.py`, mas
`TERMOS_PROIBIDOS` (`tests/test_higiene_repositorio.py:46-53`) não inclui esse termo; e
`.specs/README.md` é coberto só por "Spec Kit"/`APAGAR` (`:115-121`), não pela lista completa do AC1.
Hoje não há violação (grep independente: zero ocorrências), então o gap é latente.

**Correção sugerida**: incluir `projetoFabio` na varredura de `.py` e aplicar a lista completa a
`.specs/README.md`.

### G7 — Edge case do `.env` ausente sem asserção (Minor)

`scripts/testar.ps1:122-134` cria o `.env` antes de subir o processo, mas nenhum teste apaga o `.env`
e afirma a criação. É a menor das lacunas: os testes de integração só passam porque o arquivo existe
(ou é criado por eles), o que dá alguma cobertura indireta.

**Correção sugerida**: teste de integração que roda em cópia isolada ou respalda/restaura o `.env` e
afirma que ele passou a existir antes da subida.

### Precisão do spec (não são gaps de código, mas o AC ficou aquém do texto)

1. **DEP-02 AC4** — o spec pede as 8 chaves "todas com valor vazio ou de exemplo (nenhum segredo
   real)"; o teste (`tests/test_higiene_repositorio.py:402-406`) só afirma que `FLASK_SECRET_KEY` e
   `ADMIN_PASSWORD_HASH` estão vazios. É a substância (as outras seis trazem valores de exemplo
   declaradamente públicos), mas o AC literal não é 1:1 com a asserção.
2. **AMB-02 AC7/AC8** — os testes afirmam os switches e a existência das seções, não a instrução de
   "não acompanhar o servidor depois". O texto existe nos dois arquivos.
3. **DOC-01 AC2 / resíduo de numeração** — `scripts/verificar_prontidao_cutover.py:143` ainda imprime
   `(Tarefa 10)` no cabeçalho do relatório. O AC2 limita-se a README/TESTAR/DEPLOY, então não é
   violação; fica registrado como resíduo da numeração antiga.

---

## Requirement Traceability Update

O veredito é FAIL, então **nenhum** requisito foi movido para `Verified` (decisão do fluxo do
Verifier: gaps viram tarefas de correção, e o `spec.md`/`tasks.md` não são tocados neste commit).

| Requirement | Status anterior | Status proposto |
| --- | --- | --- |
| WDG-01, WDG-02, WDG-03 | Pending | Pending (aguardando os fixes de G1–G3) |
| LIM-01, LIM-02 | Pending | Pending |
| DEP-01, DEP-02, DEP-03 | Pending | Pending |
| DOC-01..DOC-04 | Pending | Pending |
| AMB-01 | Pending | Pending (G1, G2, G3) |
| AMB-02 | Pending | Pending |
| EST-01 | Pending | Pending |

---

## Summary

**Overall**: ❌ Not Ready (gaps de teste em ACs P1)

**Spec-anchored check**: 29 critérios avaliados — 26 com o resultado da spec comprovado por
`file:line`, 2 com asserção parcial (DOC-03 AC8, AMB-01 AC1) e 1 sem teste automatizado (AMB-01 AC6).
Edge cases: 2/4 com evidência automatizada, 1 por inspeção, 1 sem evidência.

**Sensor**: 15 mutações injetadas, 11 mortas, 4 sobreviventes (M9, M11, M12, M13).

**Gate**: 985 passed, 0 failed (baseline 939; +46 testes, 0 deletados).

**DEP-03**: venv limpo com Python 3.12.10, `pip install -r requirements-dev.txt` e gate → 985 passed,
0 failed; venv removido.

**O que funciona** (reproduzido por mim): o watchdog sobe por `run.py` uma única vez antes do
`app.run` e não no import; a porta/padrão do `run.py` são os da spec; `testar.ps1 -Destacado` devolve
o controle com a porta no ar, log no `%TEMP%`, PID e credenciais (verificado ao vivo em 59360/61019);
`-Parar` derruba e sai 0; `-Destacado -Simulado` sobe a 8051 e `-Parar -Simulado` derruba os dois; a
senha não vai para linha de comando de processo nenhum; `app/data/validators.py`, as quatro funções
sem chamador, `nonascii.txt` e `chromedriver/` saíram; `COLUNAS_PII` está intacta; as nove versões
estão fixas; `.python-version`, `.env.example` e `.gitignore` estão como o spec pede; nenhum termo
proibido sobrou nos arquivos listados; `PROJECT_RULES.md` é 1.2.0 com os Princípios I–VII byte a byte
iguais; `DEPLOY.md` cobre os pontos exigidos.

**Issues encontrados**: G1 e G2 (AMB-01 AC1 — limite de 60 s e impressão de e-mail/senha sem
asserção), G3 (AMB-01 AC6 sem teste automatizado) são os que bloqueiam o PASS; G4–G7 são menores.

**Próximos passos**: o orquestrador decide sobre as tarefas de correção (G1–G3 no mínimo); depois,
re-verificação.
