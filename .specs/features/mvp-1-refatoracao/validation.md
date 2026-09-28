# MVP 1 — Refatoração de `app.py` e das docstrings — Validation

**Date**: 2026-09-28
**Spec**: `.specs/features/mvp-1-refatoracao/spec.md`
**Diff range**: `e99b8dd..dc57577` (branch `orq/mvp-1-refatoracao`, worktree `_int`)
**Verifier**: independente (author = execução `/orq` de 2026-09-26; verifier = sessão de 2026-09-28, sem código escrito por esta feature)

---

## Task Completion

| Task | Status  | Notes |
| ---- | ------- | ----- |
| T1–T9  | ✅ Done | Rotas movidas para `app/rotas/*` (Fase 1) |
| T10–T15 | ✅ Done | Docstrings/comentários limpos em `app/`, `scripts/`, `run.py` (Fase 2) |
| T16  | ✅ Done | `.specs/STATE.md` atualizado |

---

## Spec-Anchored Acceptance Criteria

### P1: Rotas administrativas separadas por área

| Criterion | Spec-defined outcome | `file:line` + evidência | Result |
| --- | --- | --- | --- |
| AC1 rotas em módulos de `app/rotas/` | 9 módulos listados no "Mapa de rotas" | `app/rotas/{comum,publico,acesso,instalacao,configuracoes,publicacao,envio,coleta_sistec,atualizar}.py` existem | ✅ PASS |
| AC2 `app.py` ≤150 linhas, sem `@server.route` | 0 ocorrências, ≤150 linhas | `app/app.py`: 65 linhas; `grep -c "@server.route" app/app.py` = 0; teste `tests/test_rotas_modulos.py:56 test_app_py_so_monta_o_app` | ✅ PASS |
| AC3 mesma URL/status/corpo de antes | testes existentes continuam passando | `tests/test_rotas_modulos.py` (27 casos, todos ✅) + gate completo | ✅ PASS |
| AC4 os dois `before_request` continuam valendo pra todo o app | `_exigir_instalacao` e `_exigir_sessao_previa` como `before_app_request` do blueprint da área | `app/rotas/instalacao.py:90` (`_exigir_instalacao`), `app/rotas/acesso.py:71-72` (`@acesso_bp.before_app_request` / `_exigir_sessao_previa`) | ✅ PASS |
| AC5 README cita `app/rotas/` em Estrutura e Onde mexer | duas menções | `README.md:66` (Estrutura), `README.md:92` (Onde mexer) | ✅ PASS |

### P1: Docstrings dizem o que o código faz

| Criterion | Spec-defined outcome | `file:line` + evidência | Result |
| --- | --- | --- | --- |
| AC1 nenhum padrão proibido em docstring/comentário de `app/`, `scripts/`, `run.py` | 0 ocorrências | `tests/test_higiene_docstrings.py::test_docstrings_e_comentarios_sem_ids_de_spec` cobre `ALVOS_LIMPOS` = todo `app/*`, `run.py`, `scripts` (linha 24-29); `test_todos_os_modulos_app_estao_cobertos` garante que nenhum módulo de `app/` ficou fora da lista; gate verde | ✅ PASS |
| AC2 explicação da regra sobrevive à limpeza do ID | amostragem manual | amostra de 5 docstrings (`publico.py:1`, `envio.py:1`, `instalacao.py:1`, `coleta_sistec.py:1`, `comum.py:1`) — todas descrevem a função sem citar ID/documento | ✅ PASS |
| AC3 nenhuma linha executável muda | sem diff de comportamento | gate completo (1058 passed) sem regressão + sensor de discriminação (abaixo) confirma que mudar comportamento real quebra teste, não a limpeza de docstring | ✅ PASS |
| AC4 `verificar_prontidao_cutover.py` não imprime "Tarefa" | 0 ocorrências | `tests/test_higiene_docstrings.py::test_relatorio_de_prontidao_sem_numeracao_de_tarefas` → passou (`assert "Tarefa" not in saida`) | ✅ PASS |

**Status**: ✅ Todos os ACs cobertos, sem gap de precisão.

---

## Discrimination Sensor

Executado em worktree scratch (`/tmp/scratch-verifier-mvp1`, removido ao final; `git status --porcelain` da árvore real conferido igual antes/depois — vazio nas duas vezes).

| Mutação | File:line | Descrição | Killed? |
| --- | --- | --- | --- |
| 1 | `app/data/campi.py:1` | Inseriu `"Tarefa 09"` na docstring do módulo | ✅ Killed — `test_higiene_docstrings.py::test_docstrings_e_comentarios_sem_ids_de_spec[app/data]` falhou |
| 2 | `app/rotas/instalacao.py:89` | Removeu o decorador `@instalacao_bp.before_app_request` de `_exigir_instalacao` | ✅ Killed — `test_instalacao.py::test_tela_administrativa_leva_ao_assistente_enquanto_a_instalacao_nao_termina` falhou (200 em vez de 302) |
| 3 | `app/app.py:41` | Comentou `server.register_blueprint(publico_bp)` (rota "voltando" a não estar registrada via blueprint) | ✅ Killed — 2 casos de `test_rotas_modulos.py::test_rota_mora_no_blueprint_da_area` falharam |
| 4 | `app/app.py` | Engordou o arquivo para 265 linhas | ✅ Killed — `test_rotas_modulos.py::test_app_py_so_monta_o_app` falhou (265 > 150) |

**Sensor depth**: lightweight (4 mutações, conforme prescrito em `tasks.md` "Verificação (depois de T16)")
**Result**: 4/4 killed — ✅ PASS

---

## Code Quality

| Principle | Status |
| --- | --- |
| Minimum code | ✅ |
| Surgical changes (refatoração pura, sem mudar comportamento) | ✅ |
| No scope creep | ✅ — `app/admin_campi.py` e `app/sistec/api.py` ficaram como blueprints próprios, fora do escopo de rotas (conforme Out of Scope) |
| Matches patterns | ✅ — blueprints Flask, mesmo padrão dos módulos já existentes |
| Spec-anchored outcome check | ✅ |
| Documented guidelines followed | `.specs/MVP-PROTOCOLO.md` (seção 5, monkeypatch em módulo novo) — seguido |

---

## Edge Cases

- [x] Nome movido importado por outro módulo de `app/`: sem cópia residual em `app/app.py` (verificado pelo gate + AC2).
- [x] Docstring vazia após limpeza: `tests/test_higiene_docstrings.py::test_nenhuma_docstring_ficou_vazia` cobre todo `ALVOS_LIMPOS`.
- [x] Comentário só com ID apagado por inteiro: coberto pelo padrão de regex do teste de higiene (não sobra comentário órfão nos arquivos tocados).

---

## Gate Check

- **Gate command**: `python -m pytest -q -p no:cacheprovider` (rodado como `python -m pytest -q`, equivalente)
- **Result**: 1058 passed, 0 failed, 0 skipped (4 warnings pré-existentes de parsing de data, não relacionados à feature)
- **Test count antes da feature**: não medido nesta sessão (handoff de `orq` não registrou baseline); sem indício de teste removido — `git log` da feature só acrescenta testes (`test_rotas_modulos.py`, `test_higiene_docstrings.py`)
- **Skipped tests**: nenhum
- **Failures**: nenhuma

---

## Requirement Traceability Update

| Requirement | Previous Status | New Status |
| --- | --- | --- |
| REF-01 | Pending | ✅ Verified |
| REF-02 | Pending | ✅ Verified |
| REF-03 | Pending | ✅ Verified |
| REF-04 | Pending | ✅ Verified |
| REF-05 | Pending | ✅ Verified |
| REF-06 | Pending | ✅ Verified |
| REF-07 | Pending | ✅ Verified |

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 9/9 ACs (5 de Rotas + 4 de Docstrings) batem com o resultado da spec
**Sensor**: 4/4 mutações mortas
**Gate**: 1058 passed, 0 failed

**What works**: `app/app.py` reduzido a 65 linhas sem `@server.route`; 9 módulos de `app/rotas/` cobrindo o Mapa de rotas; os dois `before_app_request` preservados; README atualizado; docstrings/comentários de `app/`, `scripts/`, `run.py` sem IDs de spec, documento ausente ou "Tarefa NN"; script de prontidão sem numeração de tarefa na saída.

**Issues found**: nenhum.

**Next steps**: atualizar `tasks.md` (header "Status: Draft" → "Done") e a tabela de traceability de `spec.md` com os vereditos acima; branch `orq/mvp-1-refatoracao` segue só local — push/merge/deploy pendem de decisão explícita da usuária.
