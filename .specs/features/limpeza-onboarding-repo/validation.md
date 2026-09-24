# Limpeza de resíduos e onboarding do repositório — Validation

## Validation — `limpeza-onboarding-repo` (Rodada 2): PASS ✅

**Date**: 2026-09-24
**Spec**: `.specs/features/limpeza-onboarding-repo/spec.md`
**Diff range (rodada 2)**: `80bfc6f..3f8aa7b` (6 commits)
**Faixa original**: `b68118e..506c1b5` (17 tarefas, veredito FAIL ❌ em `80bfc6f`, arquivado no fim deste arquivo)
**Verifier**: sub-agente independente (author ≠ verifier)

**Veredito**: **PASS**. A rodada 1 deu FAIL por 4 mutantes sobreviventes (M9, M11, M12, M13) e 7 gaps de
teste (G1–G7) — o produto já estava correto, faltava teste onde a spec é precisa. O implementador fez
T18–T22 só em testes (`a0bb3cd..3f8aa7b`); re-derivei tudo nesta rodada: **nenhuma linha de produto
mudou** na faixa, **21 de 21 mutações morreram** (as 15 da rodada 1 + 6 novas), **29 de 29 critérios da
spec** têm evidência `file:line` e **4 de 4 edge cases** estão cobertos. Gate: **991 passed, 0 failed,
0 skipped**. G1–G7 e as três precisões do spec: fechados (só a precisão nº 3, o resíduo `(Tarefa 10)`,
segue como follow-up fora do escopo do AC).

---

## Escopo da rodada 2

Depois do FAIL da rodada 1, o orquestrador planejou a Phase 6 (`f8eabeb`) e o implementador fez
T18–T22 (`a0bb3cd..3f8aa7b`). Re-derivei tudo: nada de produto mudou.

`git diff --stat 80bfc6f..HEAD` (575 inserções, 13 deleções):

| Arquivo | +/− |
| --- | --- |
| `.specs/LESSONS.md` | +42 |
| `.specs/features/limpeza-onboarding-repo/tasks.md` | +146 |
| `.specs/lessons.json` | +128 |
| `tests/test_execucoes.py` | +37 |
| `tests/test_higiene_repositorio.py` | +72 |
| `tests/test_testar_ps1.py` | +163 −13 |

**Nenhum arquivo de produto** (`app/`, `run.py`, `scripts/`, `README.md`, `DEPLOY.md`, `AGENTS.md`,
`.env.example`, `requirements*.txt`) foi tocado na faixa. Nada de findings.

**Auditoria das 13 linhas removidas nos testes**: nenhum `def test_` e nenhum decorador foi apagado
(`git diff 80bfc6f..HEAD -- tests/ | grep -E "^-def test_|^-@pytest"` → vazio). As remoções são
substituições por asserções mais fortes: `assert "APAGAR" not in conteudo` → laço sobre a lista
completa de termos; `TERMOS_PROIBIDOS_EM_DOCS = TERMOS_PROIBIDOS + ["projetoFabio", "Tarefa "]` →
`projetoFabio` promovido para `TERMOS_PROIBIDOS` + `["Tarefa "]` (varredura maior); `assert str(porta)
in subida.stdout` → URL de login, e-mail e senha do `.env`; `rodar_script`/`derrubar` ganharam o
parâmetro `em` para rodar em cópia isolada.

---

## Gate Check (rodada 2)

- **Comando**: `python -m pytest -q -p no:cacheprovider`
- **Resultado**: **991 passed, 0 failed, 0 skipped** em 145,55 s (exit 0)
- **Antes da rodada 2**: 985; **depois**: 991 → **+6** (T18 +1, T19 +1, T20 +1, T21 +1, T22 +2), 0 testes
  deletados, 0 pulados — o teste do `-Simulado` (`tests/test_testar_ps1.py:281`) **rodou** nesta
  execução (a 8051 estava livre)
- **DEP-03**: não repetido — nenhum arquivo de produto nem dependência mudou na faixa
  (`requirements*.txt` fora do diff), então o resultado da rodada 1 (venv limpo 3.12.10 → 985 passed)
  continua valendo. O `+6` são só testes, sem dependência nova.

---

## Spec-Anchored Acceptance Criteria (rodada 2)

Linhas das asserções re-derivadas no HEAD. As linhas do arquivo de higiene mudaram porque o arquivo
cresceu — todas recalculadas.

| Criterion (WHEN X THEN Y) | `file:line` + asserção | Result |
| --- | --- | --- |
| WDG-01 AC1 varredura antes do `app.run`, uma vez cada | `tests/test_run.py:43` — `assert len(espioes) == 2`; `:44` `espioes[0] == "varredura"`; `:45` `espioes[1][0] == "run"` | ✅ PASS |
| WDG-01 AC2 `--host`/`--port` repassados; padrão `0.0.0.0`/`8050` | `tests/test_run.py:51` — `{"host": "127.0.0.1", "port": 9999, "debug": False}`; `:57` — `{"host": "0.0.0.0", "port": 8050, "debug": False}` | ✅ PASS |
| WDG-01 edge `--port abc` sai com 2 sem varredura | `tests/test_run.py:64` — `assert excinfo.value.code == 2`; `:65` `assert espioes == []`; `:79-81` subprocesso | ✅ PASS |
| WDG-02 AC3 importar `app.app` não cria thread | `tests/test_run.py:98` — `assert resultado.stdout.strip() == "None"` (subprocesso, `:97` rc 0) | ✅ PASS |
| WDG-03 AC4 `testar.ps1` sobe por `run.py` | `tests/test_testar_ps1.py:40` — `"run.py --host 127.0.0.1 --port $Porta" in ler_script()`; contraprova `:44` — `"app.run(" not in ler_script()` | ✅ PASS |
| LIM-01 AC1 sem `app/data/validators.py` | `tests/test_higiene_repositorio.py:323` — `assert not os.path.exists(caminho("app","data","validators.py"))` | ✅ PASS |
| LIM-01 AC2 sem as 4 funções sem chamador (AST) | `tests/test_higiene_repositorio.py:337` — `assert nome not in definicoes(arquivo_relativo)` (parametrizado por `:324`) | ✅ PASS |
| LIM-01 AC3 `COLUNAS_PII` intacta | `tests/test_higiene_repositorio.py:358` — `assert COLUNAS_PII == COLUNAS_PII_ESPERADAS` | ✅ PASS |
| LIM-02 AC4 sem `nonascii.txt` nem `chromedriver/` | `tests/test_higiene_repositorio.py:364-365` — dois `assert not os.path.exists(...)` | ✅ PASS |
| LIM-02 AC5 `.gitignore` com `.agents/`, `.uv-cache/`, `.uv-python/` | `tests/test_higiene_repositorio.py:378` — `assert entrada in linhas` | ✅ PASS |
| DEP-01 AC1 `requirements.txt` com 9 versões fixas | `tests/test_higiene_repositorio.py:402` — `assert linhas_uteis("requirements.txt") == REQUIREMENTS_ESPERADOS` | ✅ PASS |
| DEP-01 AC2 `requirements-dev.txt` = `-r` + `pytest==9.1.1` | `tests/test_higiene_repositorio.py:407` — `assert linhas_uteis("requirements-dev.txt") == ["-r requirements.txt", "pytest==9.1.1"]` | ✅ PASS |
| DEP-02 AC3 `.python-version` = `3.12` | `tests/test_higiene_repositorio.py:415` — `assert linhas_uteis(".python-version") == ["3.12"]` | ✅ PASS |
| DEP-02 AC4 as 8 chaves do `.env.example` sem segredo real | `tests/test_higiene_repositorio.py:446` — `assert chave in valores`; `:463-464` vazios; `:467` — `valor == "" or valor == VALORES_DE_EXEMPLO.get(chave)`; `:470` — `not valor.startswith(("scrypt:", "pbkdf2:"))`; `:471` — `not PADRAO_HASH_HEX.fullmatch(valor)`. **Gap da rodada 1 fechado** (mutação X3 mata) | ✅ PASS |
| DEP-03 AC5 venv limpo instala e passa | rodada 1 (venv 3.12.10 → 985 passed); produto e dependências inalterados | ✅ PASS |
| DOC-01 AC1 sem termos proibidos, `projetoFabio` incluído | `tests/test_higiene_repositorio.py:53` — `"projetoFabio"` dentro de `TERMOS_PROIBIDOS` (`:46`); `:62` e `:77` — `pytest.fail(f"{arquivo} cita {termo}")` para `app/`, `scripts/`, `tests/`, `run.py`. **G6 fechado** (mutação X2 mata) | ✅ PASS |
| DOC-01 AC2 sem "Tarefa NN" em README/TESTAR/DEPLOY | `tests/test_higiene_repositorio.py:91` — `TERMOS_PROIBIDOS_EM_DOCS = TERMOS_PROIBIDOS + ["Tarefa "]`; `:101` — `pytest.fail(f"{documento} cita {termo}")` | ✅ PASS |
| DOC-01 AC3 sem `CUTOVER.md`/`PARITY_REPORT.md`, com `DEPLOY.md` | `tests/test_higiene_repositorio.py:129-131` | ✅ PASS |
| DOC-01 AC4 `DEPLOY.md` com os 7 marcadores | `tests/test_higiene_repositorio.py:150` — `assert marcador in conteudo` | ✅ PASS |
| DOC-01 AC5 seção fora do escopo aponta para `DEPLOY.md` | `tests/test_higiene_repositorio.py:317` — `assert "DEPLOY.md" in saida`; `:318` — `assert "CUTOVER.md" not in saida` | ✅ PASS |
| DOC-03 AC6 README lista cada subdiretório de `app/` + `scripts/`, `tests/`, `.specs/` | `tests/test_higiene_repositorio.py:171` — `assert f"app/{pasta}/" in conteudo`; `:173` — `f"`{pasta}`"` | ✅ PASS |
| DOC-03 AC7 "Começar" na ordem venv → dev.txt → `.env.example` → pytest → subir | `tests/test_higiene_repositorio.py:198` — `assert ordem == sorted(ordem)` | ✅ PASS |
| DOC-03 AC8 "Onde mexer" cobre os 5 temas | `tests/test_higiene_repositorio.py:208` — `assert tema in secao, f"Onde mexer não cita {tema}"` sobre `TEMAS_DE_ONDE_MEXER` (`:176-182`: regra de cálculo, página pública, coleta do Sistec, visual, rota administrativa). **G5 fechado** (mutação X1 mata) | ✅ PASS |
| DOC-01 AC1 README sem caminho inexistente | `tests/test_higiene_repositorio.py:225` — `assert os.path.exists(caminho(*citado.split("/")))` | ✅ PASS |
| DOC-04 AC9 `PROJECT_RULES.md` 1.2.0 e princípios intactos | `tests/test_higiene_repositorio.py:111` — `assert "**Version**: 1.2.0" in conteudo`; `:113` — nenhum termo proibido; Princípios I–VII byte a byte iguais a `b68118e` (conferido na rodada 1, arquivo fora do diff da rodada 2) | ✅ PASS |
| DOC-04 AC10 `.specs/README.md` sem Spec Kit nem termos proibidos | `tests/test_higiene_repositorio.py:122` — `assert "Spec Kit" not in conteudo`; `:124` — `assert termo not in conteudo` sobre a lista **completa**. **G6 fechado** | ✅ PASS |
| AMB-01 AC1 `-Destacado` com porta livre: 60 s, URL, e-mail, senha, PID, log, rc 0 | `tests/test_testar_ps1.py:221` — `assert f"http://localhost:{porta}/admin/login" in subida.stdout`; `:223` — `credenciais["ADMIN_EMAIL"] in subida.stdout`; `:224` — `credenciais["ADMIN_SENHA"] in subida.stdout`; `:225` — `assert "PID" in subida.stdout`; limite padrão em `:59` — `assert atribuicoes[0] == "60"`, `:60` — `[valor for valor in atribuicoes if valor.isdigit()] == ["60"]`, `:61` — `atribuicoes[1] == "$limitePedido"`. **G1 e G2 fechados** (mutações M9 e M12 mortas) | ✅ PASS |
| AMB-01 AC2 log no `%TEMP%`, nunca no repositório | `tests/test_testar_ps1.py:218` — caminho do log em `%TEMP%`; `:219` — `assert RAIZ not in linha_log`; `:249` — nenhum log quando a porta está ocupada | ✅ PASS |
| AMB-01 AC3 sem porta em 60 s: encerra, cita o log, sai 1 | `tests/test_testar_ps1.py:268-270` — rc 1, `f"calcsistec-{porta}.log" in saida.stdout`, `not escutando(porta)` | ✅ PASS |
| AMB-01 AC4 porta ocupada: PID de quem ocupa, rc 1, sem derrubar | `tests/test_testar_ps1.py:245-247` — `returncode == 1`, `str(os.getpid()) in saida.stdout`, `escutando(porta)` | ✅ PASS |
| AMB-01 AC5 `-Parar` derruba e sai 0; nada no ar avisa e sai 0 | `tests/test_testar_ps1.py:229-230`; `:316-317` — rc 0 e `"nada no ar" in saida.stdout.lower()` | ✅ PASS |
| AMB-01 AC6 `-Destacado -Simulado` sobe os dois; `-Parar -Simulado` derruba os dois | `tests/test_testar_ps1.py:295` — `assert escutando(8051)`; `:300-301` — `not escutando(porta)` e `not escutando(8051)`; `:303-304` — PID da 8050 inalterado; `skipif` em `:277-280`. **G3 fechado** (mutação M13 morta por este teste) | ✅ PASS |
| AMB-02 AC7 `/testar` com os switches e a ordem de não monitorar | `tests/test_higiene_repositorio.py:241-243` — switches; `:291` — `assert linha is not None`; `:292` — `assert "Não" in linha`. **Precisão nº 2 fechada** (mutação X4 mata) | ✅ PASS |
| AMB-02 AC8 `AGENTS.md` com a seção e a ordem de não monitorar | `tests/test_higiene_repositorio.py:265-267`; `:283` — `assert linha is not None`; `:284` — `assert "não" in linha`. **Precisão nº 2 fechada** (mutação X5 mata) | ✅ PASS |
| AMB-02 AC9 `CLAUDE.md` importa `@AGENTS.md` | `tests/test_higiene_repositorio.py:297` — `assert "@AGENTS.md" in texto("CLAUDE.md")` | ✅ PASS |
| EST-01 bloco "Estado atual" no topo do Handoff, ≤ 10 linhas | sem teste por desenho (`tasks.md`: "none — build gate only"); inspeção da rodada 1: `.specs/STATE.md:61-71`, 6 bullets antes do primeiro `###` (`:77`) | ✅ PASS (por inspeção) |

**Status**: ✅ **29/29 critérios com o resultado da spec** — nenhum gap, nenhuma asserção parcial.

### Delta em relação à rodada 1

| Item da rodada 1 | Antes | Agora | Evidência nova |
| --- | --- | --- | --- |
| DOC-03 AC8 "Onde mexer" | ⚠️ GAP | ✅ PASS | `tests/test_higiene_repositorio.py:201-208`; mata X1 |
| AMB-01 AC1 (60 s) | ⚠️ GAP (G1) | ✅ PASS | `tests/test_testar_ps1.py:50-61`; mata M9 |
| AMB-01 AC1 (e-mail/senha) | ⚠️ GAP (G2) | ✅ PASS | `tests/test_testar_ps1.py:221-224`; mata M12 |
| AMB-01 AC6 `-Simulado` | ⚠️ GAP (G3) | ✅ PASS | `tests/test_testar_ps1.py:281-307`; mata M13 |
| DOC-01 AC1 (`projetoFabio`) | ⚠️ parcial (G6) | ✅ PASS | `tests/test_higiene_repositorio.py:46-53,62,77,124`; mata X2 |
| DEP-02 AC4 (8 chaves) | ⚠️ parcial (precisão 1) | ✅ PASS | `tests/test_higiene_repositorio.py:457-471`; mata X3 |
| AMB-02 AC7/AC8 (não monitorar) | ⚠️ parcial (precisão 2) | ✅ PASS | `tests/test_higiene_repositorio.py:274-292`; matam X4 e X5 |

---

## Edge Cases (rodada 2)

| Edge case (spec) | Evidência | Result |
| --- | --- | --- |
| `--port` não inteiro → sai com 2 sem iniciar varredura | `tests/test_run.py:64-65` e subprocesso `:79-81` | ✅ PASS |
| `iniciar_varredura` duas vezes → uma única thread viva | `tests/test_execucoes.py:543-567` — `:552` `anterior is None`, `:559` segunda chamada, `:561` `assert execucoes._VARREDURA_THREAD is primeira`, `:562` `threads_do_laco() == [primeira]`; `finally` (`:563-567`) para a thread e restaura o global. M11 morto | ✅ PASS |
| `.env` ausente + `-Destacado` → cria o `.env` antes de subir | `tests/test_testar_ps1.py:337-370` — `:351` `git worktree add --detach` no `%TEMP%`, `:353` sem `.env`, `:360-362` `ADMIN_EMAIL`/`ADMIN_SENHA`/`FLASK_SECRET_KEY` preenchidos no `.env` criado, `:369-370` hash do `.env` da raiz e `git worktree list` inalterados. M16 (script deixa de criar o `.env`) morto | ✅ PASS |
| Termo proibido encontrado → mensagem cita arquivo e termo | `tests/test_higiene_repositorio.py:63`, `:78`, `:102` — `pytest.fail(f"{...} cita {termo}")` (caminho relativo + termo); é o próprio teste, conferido por inspeção | ✅ PASS (por inspeção) |

**Edge cases: 4/4 com evidência** (3 automatizadas + 1 por inspeção).

---

## Discrimination Sensor (rodada 2)

Cópia isolada por `git worktree add --detach` no diretório temporário do sistema
(`%TEMP%\calcsistec-sensor-r2*`), **cada mutação commitada dentro da cópia** (o teste de T20 cria o
próprio `worktree` a partir do `HEAD` da cópia — mutação não commitada seria invisível para ele), e
`git reset --hard` + `git clean -fdx` entre as mutações, conferindo `git status --porcelain` vazio a
cada passo. Nunca usei `git stash` nem editei a árvore real. As 15 mutações da rodada 1 foram
reaplicadas + 6 novas (5 do "Done when" de T22 e 1 para o edge case do `.env`).

**Resultado: 21 mutações, 21 mortas, 0 sobreviventes.**

| # | Mutação | Arquivo | Alvo | Resultado |
| --- | --- | --- | --- | --- |
| M1 | tirar `iniciar_varredura()` de `run.main` | `run.py:28` | `tests/test_run.py` | ✅ MORTO (3 failed) |
| M2 | `iniciar_varredura()` depois de `app.run` | `run.py:28-29` | `tests/test_run.py` | ✅ MORTO (3 failed) |
| M3 | recriar `t01_remover_pii` | `app/data/transform.py` | higiene | ✅ MORTO (1 failed) |
| M4 | `requirements.txt` sem versão fixa | `requirements.txt` | higiene | ✅ MORTO (1 failed) |
| M5 | `CUTOVER.md` de volta no `README.md` | `README.md` | higiene | ✅ MORTO (1 failed) |
| M6 | recriar `CUTOVER.md` na raiz | `CUTOVER.md` | higiene | ✅ MORTO (1 failed) |
| M7 | tirar `-Destacado` (switch + bloco) | `scripts/testar.ps1:53,233-276` | `tests/test_testar_ps1.py` | ✅ MORTO (6 failed) |
| M8 | `iniciar_varredura` no import de `app.app` | `app/app.py` (fim do módulo) | `tests/test_run.py` | ✅ MORTO (1 failed) |
| M9 | limite do `-Destacado` 60 s → 30 s | `scripts/testar.ps1:236` | `tests/test_testar_ps1.py` | ✅ **MORTO agora** — `test_limite_padrao_do_destacado_e_60_segundos` (era sobrevivente) |
| M10 | `-Parar` sem nada no ar sai 1 | `scripts/testar.ps1:88` | `tests/test_testar_ps1.py -k parar` | ✅ MORTO (3 failed) |
| M11 | remover a guarda de idempotência | `app/sistec/execucoes.py:571-573` | `tests/test_execucoes.py` + `tests/test_run.py` | ✅ **MORTO agora** — `test_iniciar_varredura_e_idempotente` (era sobrevivente) |
| M12 | `-Destacado` não imprime a senha | `scripts/testar.ps1:215` | `tests/test_testar_ps1.py -k destacado` | ✅ **MORTO agora** — `test_destacado_sobe_o_app_e_parar_derruba` (era sobrevivente) |
| M13 | `-Parar` não encerra o simulado da 8051 | `scripts/testar.ps1:82` | `tests/test_testar_ps1.py -k "simulado or parar"` | ✅ **MORTO agora** — `test_destacado_com_simulado_sobe_e_parar_derruba_os_dois` (era sobrevivente) |
| M14 | porta padrão do `run.py` 8050 → 8051 | `run.py:18` | `tests/test_run.py` | ✅ MORTO (1 failed) |
| M15 | prontidão volta a citar `CUTOVER.md` | `scripts/verificar_prontidao_cutover.py:152` | higiene | ✅ MORTO (2 failed) |
| X1 | apagar "coleta do Sistec" do "Onde mexer" | `README.md:89` | higiene | ✅ MORTO — `test_onde_mexer_cobre_os_cinco_temas` |
| X2 | `# legado do projetoFabio` em `run.py` | `run.py` | higiene | ✅ MORTO — `test_scripts_tests_e_run_nao_citam_documentos_ausentes` |
| X3 | `ADMIN_PASSWORD_HASH=scrypt:...` no `.env.example` | `.env.example` | higiene | ✅ MORTO — `test_env_exemplo_nao_traz_segredo_nenhum` |
| X4 | `/testar` manda **acompanhar** o servidor | `.claude/commands/testar.md:21` | higiene | ✅ MORTO — `test_instrucao_de_nao_monitorar_o_servidor_depois_de_subir` |
| X5 | `AGENTS.md` manda **monitorar** o servidor | `AGENTS.md:24` | higiene | ✅ MORTO — `test_instrucao_de_nao_monitorar_o_servidor_depois_de_subir` |
| M16 | `testar.ps1` deixa de criar o `.env` | `scripts/testar.ps1:123-134` | `tests/test_testar_ps1.py -k env_e_criado` | ✅ MORTO — `test_env_e_criado_antes_de_subir_o_app` |

**Isolamento**: `git status --porcelain` da árvore real ficou vazio **antes de cada mutação** (asserção
no próprio driver) e no fim; `git worktree list` mostra só o repositório principal; nenhum
`.pytest_cache/`, `.test-*` ou `.verifier-scratch-*` no repositório.

**Ressalva do sensor (não é gap)**: sob M13 o próprio `derrubar(porta, simulado=True)` do teste também
não encerra a 8051, então a execução do mutante **deixa um `sistec_simulado.py` órfão** no ar. Matei os
três que apareceram (PIDs 42024, 5488 e 25808, todos com `scripts/sistec_simulado.py` na linha de
comando e log em `%TEMP%\calcsistec-simulado-8051*.log`) e removi os logs. Consequência prática: com a
8051 ocupada, o `skipif` de `tests/test_testar_ps1.py:277` **pula** o único teste que mata M13 — por
isso o sensor de M13 foi rodado com a 8051 livre e conferido caso a caso.

---

## Gaps da rodada 1 — reavaliação

| Gap | Fechado? | Evidência |
| --- | --- | --- |
| **G1** 60 s sem asserção | ✅ FECHADO | `tests/test_testar_ps1.py:50-61`; M9 morto |
| **G2** e-mail/senha não asseverados | ✅ FECHADO | `tests/test_testar_ps1.py:221-224` (`http://localhost:<porta>/admin/login`, `ADMIN_EMAIL`, `ADMIN_SENHA` lidos do `.env`); M12 morto |
| **G3** `-Simulado` sem teste automatizado | ✅ FECHADO | `tests/test_testar_ps1.py:281-307`; M13 morto |
| **G4** idempotência de `iniciar_varredura` | ✅ FECHADO | `tests/test_execucoes.py:543-567`; M11 morto |
| **G5** "Onde mexer" só tinha a seção | ✅ FECHADO | `tests/test_higiene_repositorio.py:176-208`; X1 morto |
| **G6** lista de termos mais estreita que o AC | ✅ FECHADO | `tests/test_higiene_repositorio.py:46-53` + `:91` + `:124`; X2 morto |
| **G7** edge case do `.env` ausente | ✅ FECHADO | `tests/test_testar_ps1.py:337-370` (worktree `--detach` no `%TEMP%`, hash da raiz e `worktree list` conferidos); M16 morto |
| **Precisão 1** DEP-02 AC4 (8 chaves) | ✅ FECHADO | `tests/test_higiene_repositorio.py:457-471`; X3 morto |
| **Precisão 2** AMB-02 AC7/AC8 (não monitorar) | ✅ FECHADO | `tests/test_higiene_repositorio.py:274-292`; X4 e X5 mortos |
| **Precisão 3** resíduo `(Tarefa 10)` em `scripts/verificar_prontidao_cutover.py:143` | ⏳ follow-up (não é gap) | O AC2 de DOC-01 cobre apenas README/TESTAR/DEPLOY; o resíduo segue registrado como pendência de limpeza de numeração, fora do escopo desta feature |

**Nenhum gap aberto. 1 follow-up documentado.**

---

## Follow-ups (não bloqueiam o PASS)

1. `scripts/verificar_prontidao_cutover.py:143` ainda imprime `(Tarefa 10)` no relatório de prontidão —
   resíduo da numeração antiga, fora do escopo do DOC-01 AC2.
2. `tests/test_testar_ps1.py:277-280` usa `skipif` avaliado na coleta: com a 8051 ocupada o teste do
   `-Simulado` é pulado (correto para não derrubar ambiente manual, mas é o único que mata M13). Vale
   registrar em `.specs/LESSONS.md` na próxima passagem se isso voltar a esconder mutante.
3. EST-01 continua sem teste automatizado por decisão de `tasks.md` (build gate only) — inspeção manual.

---

## Code Quality (rodada 2)

| Princípio | Status |
| --- | --- |
| Código mínimo / sem abstração para uso único | ✅ (rodada 2 só toca testes e `.specs/`) |
| Mudanças cirúrgicas (só os arquivos das tarefas) | ✅ `tests/test_testar_ps1.py`, `tests/test_execucoes.py`, `tests/test_higiene_repositorio.py`, `tasks.md` |
| Sem scope creep | ✅ nenhum arquivo de produto no diff |
| Sem asserção enfraquecida | ✅ nenhum `def test_`/decorador removido; as 13 linhas trocadas foram substituídas por versões mais fortes |
| Cada teste mapeia para um AC, edge case ou "Done when" | ✅ T18→G1/G2, T19→G3, T20→G7, T21→G4, T22→G5/G6/precisões 1–2 |
| Guidelines seguidas (`AGENTS.md`, `.specs/PROJECT_RULES.md` IV) | ✅ um commit por tarefa, gate completo por tarefa |

---

## Requirement Traceability Update (rodada 2)

| Requirement | Status anterior | Status novo |
| --- | --- | --- |
| WDG-01, WDG-02, WDG-03 | Pending | **Verified** |
| LIM-01, LIM-02 | Pending | **Verified** |
| DEP-01, DEP-02, DEP-03 | Pending | **Verified** |
| DOC-01, DOC-02, DOC-03, DOC-04 | Pending | **Verified** |
| AMB-01, AMB-02 | Pending | **Verified** |
| EST-01 | Pending | **Verified** (por inspeção, como o `tasks.md` prevê) |

---

## Summary (rodada 2)

**Overall**: ✅ **Ready** — 29/29 critérios com evidência, 4/4 edge cases, 21/21 mutantes mortos,
gate 991 passed / 0 failed / 0 skipped, nenhuma linha de produto alterada na faixa `80bfc6f..3f8aa7b`.

**Faixa**: `80bfc6f..3f8aa7b` (6 commits: lições `ebd46be`, planejamento `f8eabeb`, T18 `a0bb3cd`,
T19 `70438d7`, T20 `c8fb091`, T21 `c24e709`, T22 `3f8aa7b`).

**O que mudou desde o FAIL**: 6 testes novos em 3 arquivos de teste fecharam os 7 gaps e as 3 precisões
do spec. O produto já estava correto na rodada 1 — o FAIL era de cobertura de teste, e o sensor de
discriminação agora mata as quatro mutações que escapavam (M9, M11, M12, M13).

**Porta 8050**: intacta (PID 5644) durante toda a rodada; todo teste usou porta livre via
`socket.bind(("127.0.0.1", 0))` com `-Porta` explícito, inclusive no `-Parar`.

---

## Rodada 1 — arquivo histórico (2026-09-24, veredito FAIL ❌)

_Conteúdo original preservado (commit `80bfc6f`); só o título da rodada 1 mudou de nível._

### Veredito da rodada 1: FAIL ❌

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

### Task Completion

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

### Gate Check

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

### Spec-Anchored Acceptance Criteria

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

### Edge Cases

| Edge case (spec) | Evidência | Result |
| --- | --- | --- |
| `--port` não inteiro → sai com 2 sem iniciar varredura | `tests/test_run.py:60-65` — `assert excinfo.value.code == 2` e `assert espioes == []`; subprocesso em `:68-81` | ✅ PASS |
| `iniciar_varredura` chamada duas vezes → uma única thread viva | **sem teste**; o mutante M11 (remover a guarda `app/sistec/execucoes.py:571-573`) sobreviveu — gap G4 | ❌ GAP |
| `.env` ausente + `-Destacado` → cria o `.env` antes de subir | **sem asserção**; o caminho existe em `scripts/testar.ps1:122-134` e é exercitado em qualquer runner sem `.env`, mas nenhum teste apaga o `.env` e afirma que ele foi criado — gap G7 | ❌ GAP |
| Termo proibido encontrado → mensagem cita arquivo e termo | `tests/test_higiene_repositorio.py:63`, `:78` e `:102` — `pytest.fail(f"{...} cita {termo}")`; a mensagem traz caminho relativo e termo. É o próprio teste, então não há teste de teste; conferido por inspeção | ✅ PASS (por inspeção) |

---

### Discrimination Sensor

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

### DEP-03 (venv limpo)

| Passo | Comando | Resultado |
| --- | --- | --- |
| venv no diretório temporário do sistema | `python -m venv %TEMP%\calcsistec-dep03-venv` | ok — `Python 3.12.10` |
| instalação | `<venv>\Scripts\python.exe -m pip install -r requirements-dev.txt` | ok; `pip freeze` mostra `dash==4.4.1`, `dash-bootstrap-components==2.0.4`, `pandas==2.3.0`, `openpyxl==3.1.5`, `plotly==6.8.0`, `defusedxml==0.7.1`, `pillow==11.2.1`, `Flask==3.1.3`, `Werkzeug==3.1.8`, `pytest==9.1.1` |
| gate | `<venv>\Scripts\python.exe -m pytest -q -p no:cacheprovider` | **985 passed, 0 failed** em 124,77 s (exit 0) |
| limpeza | `rm -rf` do venv | ok — nada deixado no repositório |

O venv foi criado e apagado dentro do diretório temporário do sistema; o repositório continuou limpo
(`git status --porcelain` vazio antes e depois).

---

### Conferências extras

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

### Code Quality

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

### Gaps (ranqueados)

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

### Requirement Traceability Update

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

### Summary

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
