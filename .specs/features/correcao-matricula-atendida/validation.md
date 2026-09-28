# correcao-matricula-atendida Validation

**Date**: 2026-09-24
**Spec**: `.specs/features/correcao-matricula-atendida/spec.md`
**Diff range**: `6b59990..182375b` (commits `9411302`, `8df7552`, `59b6444`, `182375b`)
**Verifier**: independent sub-agent (author ≠ verifier)

**Note on HEAD movement**: partway through this verification an **external** commit
`98a2efd` ("docs(specs): fechar correcao-matricula-atendida com o gate verde", author
Jaline, 03:16:43) moved HEAD from `182375b` to `98a2efd`. `git diff --stat
182375b..98a2efd -- app/ tests/ scripts/` is **empty** — that commit touched only
`.specs/STATE.md` and the feature's `spec.md`. No code under verification changed; this
report covers the code as it stands at `98a2efd` (identical to `182375b`). All `file:line`
citations below are valid at both commits.

---

## Task Completion

Execute was inline (no formal `tasks.md`, per spec's Requirement Traceability note).

| Task (derived from spec Goals) | Status | Notes |
| --- | --- | --- |
| G1 — `t07_grao_matricula_atendida` parses `MES_DE_OCORRENCIA` in Portuguese | ✅ Done | `app/domain/shared.py:128-150`, wired at `app/data/transform.py:180` |
| G2 — "Ingressantes" uses the ciclo/month approximation instead of `EM_CURSO` | ✅ Done | `app/domain/matriculas.py:62-75`, wired at `app/pages/matriculas.py:355` |
| G3 — parity test for both rules, nominal + `RISK-002` edge cases | ✅ Done | 60 new test cases (33 + 17 + 3 + 7) |

---

## Spec-Anchored Acceptance Criteria

### P1 / MAT-01 — matrícula atendida (`app/data/transform.py:158-187`)

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: status != EM_CURSO + `MES_DE_OCORRENCIA` in ano-base → include | included (count 1); previous-year month → excluded (count 0) | `tests/test_transform_matricula_atendida.py:43`→`:50` `assert len(resultado) == 1` (ciclo 2024-03-10, CONCLUÍDA, "JUNHO 2026", ano_base 2026); negative `:53`→`:59` `assert len(resultado) == 0` ("DEZEMBRO 2025"); cross-check `tests/test_parity_dominio.py:245`→`:251` `assert t07_grao_matricula_atendida(df, 2026).shape[0] == 1` | ✅ PASS |
| AC2: recognise the 12 Portuguese month names (upper case, with and without accent) | each name → day 1 of that month; `MARCO` == `MARÇO` == 3 | `tests/test_shared_mes_ocorrencia.py:40-47` (parametrized ×12) `assert resultado.iloc[0] == pd.Timestamp(year=2026, month=numero, day=1)`; `:50-54` and `:57-60` `assert resultado.iloc[0] == pd.Timestamp(year=2026, month=3, day=1)`; `:137-141` `assert sorted(set(MESES_PT.values())) == list(range(1, 13))` and `assert MESES_PT["MARÇO"] == MESES_PT["MARCO"] == 3` | ✅ PASS |
| AC3: `status_corrigido == "EM_CURSO"` → always include, regardless of month/ciclo | all 3 EM_CURSO rows included | `tests/test_transform_matricula_atendida.py:62`→`:72` `assert len(resultado) == 3` (ciclo 2019, months "DEZEMBRO 2025" / `None` / "LIXO") | ✅ PASS |
| AC4: invalid/empty/null `MES_DE_OCORRENCIA` → not included by that route, no exception, other routes preserved | count 0 for the month route; `NaT` per value; other routes still include | `tests/test_transform_matricula_atendida.py:121-129` (parametrized ×7: `None`, `pd.NA`, `""`, `"LIXO"`, `"2026"`, `"JUNHO"`, `"06/2026"`) `assert len(resultado) == 0`; `tests/test_shared_mes_ocorrencia.py:89-112` (parametrized ×13) `assert resultado.iloc[0] is pd.NaT`; "other routes preserved" at `tests/test_transform_matricula_atendida.py:75`→`:84` `assert len(resultado) == 2` (ABANDONO with 2026 ciclo + null month) | ✅ PASS |

### P2 / MAT-02 — Ingressantes (`app/domain/matriculas.py:62-75`)

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: count atendidas whose ciclo `dt_data_inicio` is in ano-base | count 1 for a CONCLUÍDA with ciclo 2026-02-01 and month "DEZEMBRO 2025"; page KPI = 3 for the 3-row fixture (all ciclo 2026-02-01) | `tests/test_parity_dominio.py:224`→`:228` `assert contar_ingressantes(df, FiltrosAtivos(ano_base=2026)) == 1`; page level `tests/test_paginas_publicas.py:84-90` (`"Ingressantes 3"`, fixture `dt_data_inicio = pd.to_datetime(["2026-02-01"] * 3)` at `:36`, `ano_base` 2026 at `:32`) | ✅ PASS |
| AC2: atendida with `EM_CURSO` **and** month in ano-base, even with ciclo of another year → also counted | count 1 | `tests/test_parity_dominio.py:231`→`:235` `assert contar_ingressantes(df, FiltrosAtivos(ano_base=2026)) == 1` (ciclo 2024-03-10, EM_CURSO, "JUNHO 2026") | ✅ PASS |
| AC3: SHALL NOT use `EM_CURSO` alone | count 0 | `tests/test_parity_dominio.py:238`→`:242` `assert contar_ingressantes(df, FiltrosAtivos(ano_base=2026)) == 0` (ciclo 2024-03-10, EM_CURSO, "DEZEMBRO 2025"); second route fixed at `:245`→`:252` `assert t07_grao_matricula_atendida(df, 2026).shape[0] == 1` **and** `assert contar_ingressantes(...) == 0` (same row: atendida but not ingressante) | ✅ PASS |
| AC4: campus/curso filters respected | 0 when filtering a different campus, 1 when filtering the row's campus | `tests/test_parity_dominio.py:255`→`:259-260` `assert contar_ingressantes(df, FiltrosAtivos(ano_base=2026, campus="U1")) == 0` / `... campus="U9")) == 1`; integration: `app/pages/matriculas.py:350` builds the single `FiltrosAtivos` used by `:355` | ✅ PASS (see G3) |

**Status**: ✅ All 8 ACs covered with the spec-defined outcome.

---

## Edge Cases

| Edge case (spec.md) | Evidence | Result |
| --- | --- | --- |
| Empty input DataFrame → `0` / empty DataFrame, no error | `tests/test_transform_matricula_atendida.py:144-153` `assert len(resultado) == 0` + columns preserved; `tests/test_shared_mes_ocorrencia.py:115-120` `assert len(resultado) == 0` and `assert resultado.dtype.kind == "M"`; `tests/test_parity_dominio.py:263-269` `assert contar_ingressantes(...) == 0` | ✅ Handled |
| `"MARCO 2026"` without cedilla recognised | `tests/test_shared_mes_ocorrencia.py:50-54` `assert resultado.iloc[0] == pd.Timestamp(year=2026, month=3, day=1)`; end-to-end through `t07`: `tests/test_transform_matricula_atendida.py:87`→`:96` `assert len(resultado) == 2` (MARÇO 2026 + MARCO 2026 both included) | ✅ Handled |
| All rows `EM_CURSO` → atendida total equals EM_CURSO total | `tests/test_transform_matricula_atendida.py:108`→`:118` `assert len(resultado) == 3` on 3 EM_CURSO rows (ciclo 2019 / ciclo 2024 / null ciclo, all months outside or null); `contar_por_status(df, filtros, "EM_CURSO")` is 3 for the same fixture, so the asserted value is the spec outcome | ✅ Handled (assertion is a literal 3; see G3) |
| CONCLUÍDA with null ciclo `dt_data_inicio` **and** month in ano-base → counted | `tests/test_transform_matricula_atendida.py:99`→`:105` `assert len(resultado) == 1` (`(None, "CONCLUÍDA", "JANEIRO 2026")`) | ✅ Handled |
| `RISK-002` extra: null month must not become "year 0" | `tests/test_transform_matricula_atendida.py:156`→`:163` `assert list(resultado["mes_ocorrencia_corrigido"]) == ["JUNHO 2026"]` | ✅ Handled |
| Index contract of the parse (masks are combined with `&`/`\|`) | `tests/test_shared_mes_ocorrencia.py:79-86` `assert list(resultado.index) == [42, 7]` | ✅ Handled |
| Synthetic corpus must exercise the month route | `tests/test_sintetico.py:45-54` (`isna().sum() == 0`, ano-base present), `:57-64` (literal `"<MÊS> <AAAA>"`), `:67-89` (`assert int(so_pelo_mes.sum()) > 0`, `assert esperadas <= set(atendidas["CO_MATRICULA"])`) | ✅ Handled |

---

## Discrimination Sensor

Isolated `git worktree` scratch at `HEAD` (temp dir outside the repo). The real worktree
was never mutated; `git status --porcelain` matched the pre-sensor baseline after cleanup.
Control run in the scratch copy: **160 passed, 0 failed** over the feature-scoped test files
(the same scratch runs 48 unrelated `test_admin_envio*` failures because the untracked
`chromedriver` binary is absent from a worktree; none of those files are on this feature's
surface).

| # | Mutation | File:line | Description | Killed? |
| --- | --- | --- | --- | --- |
| M1 | `"MARCO": 3` → `4` | `app/domain/shared.py:46` | month map swapped for the accent-less variant | ✅ Killed (`test_shared_mes_ocorrencia.py:50`, `:137`) |
| M2 | `r"^([A-ZÇ]+)\s+(\d{4})$"` → anchor `$` removed | `app/domain/shared.py:140` | parse accepts any trailing garbage | ✅ Killed (`test_shared_mes_ocorrencia.py:107` case `"JUNHO 2026 DEZEMBRO"`) |
| M3 | `mes_ocorrencia.dt.year == ano_base` → `>= ano_base` | `app/data/transform.py:184` | back to "from the ano-base onwards" | ✅ Killed (`test_transform_matricula_atendida.py:132`, `assert 2 == 1`) |
| M4 | dropped the `ocorreu_no_ano_base` term | `app/data/transform.py:186` | month route removed from the OR | ✅ Killed (7 failures in `test_transform_matricula_atendida.py`) |
| M5 | `parsear_mes_ocorrencia(...)` → `pd.to_datetime(..., errors="coerce")` | `app/data/transform.py:180` | regression to the root-cause parse | ✅ Killed (9 failures) |
| M6 | `(iniciou_no_ano_base \| (em_curso & ocorreu_no_ano_base))` → `(iniciou_no_ano_base \| em_curso)` | `app/domain/matriculas.py:75` | old `EM_CURSO`-only rule | ✅ Killed (`test_parity_dominio.py:238`, `:272`; `assert 1 == 0`, `assert 3 == 1`) |
| M7 | removed `m.mes_ocorrencia_corrigido` from the `conn is not None` query | `app/data/consulta.py:86` | prévia read path loses the column | ✅ Killed (`test_previa_callback_matriculas.py:134` → `KeyError: 'mes_ocorrencia_corrigido'`) |
| M8 | removed `m.mes_ocorrencia_corrigido` from the public query | `app/data/consulta.py:106` | public read path loses the column | ✅ Killed (`test_consulta.py:132`, `test_previa_paridade.py:114` — column lists diverge) |
| M9 | `contar_ingressantes(df, filtros)` → `contar_por_status(df, filtros, STATUS_EM_CURSO)` | `app/pages/matriculas.py:355` | page reverted to the old KPI rule | ✅ Killed (`test_paginas_publicas.py:81` → got `"Ingressantes 2"`, expected `"Ingressantes 3"`) |

**Sensor depth**: P0-full (data-integrity counting rule), 9 manual behavior-level mutations.
**Result**: **9/9 killed — PASS**. No surviving mutant.

---

## Independent checks beyond the authored tests (adversarial)

1. **Real Sistec export, format claim (MAT-01 AC1/AC2).** Read-only scan of
   `Downloads/08agosto/matriculas/*.csv` (11 files, cp1252): 121.332 rows, 225 distinct
   `MES_DE_OCORRENCIA` values, all `<MÊS POR EXTENSO> <AAAA>`; `MARÇO` appears 13.089 times
   as `MARÇO` and **0** times as `MARCO` (the accent-less edge case is defensive, not observed).
   The spec's premise ("`pd.to_datetime` fails for 100% of rows") is confirmed: 121.002 / 121.332
   rows (99,73%) match the new parse; the remaining 330 rows use `"MÊS/AAAA"` with a slash.
2. **Real pipeline totals (Success Criteria #2).** Ran the real code path
   (`ler_planilha` → `consolidar` → `montar_matriculas_e_eficiencia`) over the same export,
   `ano_base=2026`:
   - old rule (`pd.to_datetime` + `>= inicio do ano-base`): **14.022** (matches the spec's
     reported legacy divergence exactly);
   - new implementation: **16.832** (matches the spec's claimed post-fix total exactly);
   - `==` vs `>=` on the parsed month are identical on this data (16.832 both ways);
   - `contar_ingressantes` on the same data: **5.432**, vs `EM_CURSO` count **13.328** —
     "Ingressantes" is no longer equal to Em Curso.
   The criterion is therefore substantiated by direct execution, **not** by an upload through
   the UI/envio (see G1).
3. **SQLite `DATE` column holding Portuguese text.** Reproduced a `matriculas` row written
   by the real ingestion with `mes_ocorrencia_corrigido = "JUNHO 2026"`, then read it back
   with `carregar_matriculas` (pandas 2.3.0 / Python 3.12): the value round-trips as text and
   `contar_ingressantes` / `t07` work (no `KeyError`, no `date` converter crash). This closes
   the "would the public page break in production" question for the reader path.
4. **Both `carregar_matriculas` queries updated.** `app/data/consulta.py:86` (branch
   `conn is not None`) and `:106` (own connection) — the two blocks are byte-identical, so
   the change had to be applied twice; both carry `m.mes_ocorrencia_corrigido`. Covered by
   pre-existing parity tests (`test_consulta.py:132-148`, `test_previa_paridade.py:114-127`)
   plus M7/M8 above.
5. **The `2 → 3` fixture change in `test_paginas_publicas.py` is not a weakening.** The
   fixture (3 rows, all `dt_data_inicio = 2026-02-01`, `ano_base = 2026`) yields exactly 3 by
   MAT-02 AC1; the previous value 2 was the `EM_CURSO` count, i.e. the bug. M9 proves the
   assertion is discriminating: restoring the old rule makes it fail with `"Ingressantes 2"`.

---

## Code Quality

| Principle | Status |
| --- | --- |
| No features beyond what was asked | ✅ |
| No abstractions for single-use code | ✅ — `parsear_mes_ocorrencia` is the one new abstraction, used by two call sites (`transform.py:180`, `matriculas.py:73`) |
| No unnecessary "flexibility" | ✅ — `MESES_PT` has exactly one extra key (`MARCO`), required by the spec's edge case |
| Only touched files required for task | ✅ — `git diff --name-only 6b59990..98a2efd` = the 12 files listed in the task + the 2 `.specs/` docs from the external commit |
| Didn't "improve" unrelated code | ✅ — `t08_grao_eficiencia_academica`, `app/data/versoes.py`, `app/app.py` untouched |
| Matches existing patterns/style | ✅ — pure functions in `app/domain/`, `pd.to_datetime(..., errors="coerce")` idiom preserved |
| Principle II (domain pure) | ✅ — `app/domain/shared.py` imports only `pandas` + `app.domain.contrato`; no I/O, no `app/data/*`, no env |
| Would a senior engineer approve? | ✅ |
| Tests map to ACs and are non-shallow | ✅ — each assertion targets a count, a `Timestamp`, or a `NaT`; no `assert x is not None` padding |
| Spec-anchored outcome check (asserted values match spec) | ✅ |
| Per-layer Coverage Expectation (domain 1:1 ACs) | ✅ — MAT-01 AC1-4 and MAT-02 AC1-4 each have a dedicated domain test |
| Every test maps to a spec AC / edge case / goal (no unclaimed tests) | ✅ — 33 + 17 + 3 + 7 cases all trace to MAT-01/MAT-02, the 4 edge cases, `RISK-002`, or the spec's synthetic-corpus goal |
| Documented guidelines followed | ✅ — `AGENTS.md` (temp cleanup, no `.specify/` artifacts), `.specs/PROJECT_RULES.md` I (parity tests added), II, IV (bug fix starts from a reproducing test) |

Minor observations (non-blocking):

- `scripts/sintetico.py:28-42` duplicates `MESES_PT` instead of importing
  `app.domain.shared.MESES_PT`. Justified: `scripts/sintetico.py` keeps a stdlib-only import
  list so it can be imported as a bare module (`scripts/seed_sintetico.py:22` does
  `import sintetico`). A single source would be better; the duplication is a drift risk, and
  `tests/test_sintetico.py:59-64` would not catch a divergence between the two maps.
- `app/data/transform.py:23` is the **first** `app/data/*` → `app/domain/*` import in the
  codebase. Principle II forbids only the reverse direction, and `app/domain/` is pure, so
  this is legal — but it is a new architectural edge worth recording in `PROJECT_RULES.md` /
  the reversa docs at the next amendment.
- `.pytest_cache/` is present in the repository root (created by the gate run; gitignored by
  `.gitignore:9`). `AGENTS.md` asks for it not to be left behind; not removed here because
  this verification is read-only over the real tree and other agents were concurrently active.

---

## Gate Check

- **Gate command**: `python -m pytest tests/ -q`
- **Result**: **939 passed, 0 failed, 0 skipped** (exit code 0, 90,03 s)
- **Test count before feature**: **879** — independently reproduced by collecting at
  `6b59990` in a throwaway worktree (`879 tests collected`)
- **Test count after feature**: **939** (`939 tests collected`)
- **Delta**: **+60**, exactly `33` (`test_shared_mes_ocorrencia.py`) +
  `17` (`test_transform_matricula_atendida.py`) + `3` (`test_sintetico.py`) +
  `7` (`test_mat02_*` in `test_parity_dominio.py`) — each file count confirmed with
  `--collect-only`
- **Skipped tests**: none (`grep -n "skip\|xfail"` over all six feature test files: no hits)
- **Failures**: none
- **Assertions weakened or removed**: none. The only modified assertion in the whole feature
  is `tests/test_paginas_publicas.py:87` (`"Ingressantes 2"` → `"Ingressantes 3"`), which the
  new rule requires and which M9 proves is discriminating. The other two pre-existing test
  edits are fixture additions (`tests/test_paginas_publicas.py:33`,
  `tests/test_previa_callback_matriculas.py:174`).

---

## Fix Plans

None blocking.

**G1 — Success Criteria #2 not exercised through the real envio (open item).**
The second Success Criterion is still `[ ]` unchecked in `spec.md`. It asks for a real
re-upload of `Downloads/08agosto`. This verification substantiated its substance by running
the same pipeline code directly (16.832 vs 14.022; Ingressantes 5.432 vs Em Curso 13.328),
but did not drive the UI/envio path. **Action**: either accept the pipeline-level evidence and
tick the box with that caveat, or run the real envio as UAT. Priority: Minor.

**G2 — Spec-precision gap: the "residual 82" explanation is unsupported.**
`spec.md` Out of Scope attributes the 16.750 vs 16.832 residual to "ruído de
amostragem/edge case menor (ex.: algum mês não-padrão)". The non-standard format does exist
in the real data (`"FEVEREIRO/2011"` style, 330 rows = 0,27%), but forcing a parse on those
330 rows adds **0** rows through the month route on this export, so that hypothesis does not
explain the residual. **Action**: correct the Out of Scope wording to "causa do resíduo não
identificada", or open a follow-up to investigate. The code itself is correct against the
spec's stated format (AC1/AC2 and Assumptions row 1 both define non-matching text as null).
Priority: Minor.

**G3 — Thin evidence at two assertion sites (not gaps in coverage).**
(a) MAT-02 AC4 has domain-level coverage only; no page-level test asserts the "Ingressantes"
number under an active campus/curso filter. (b) The "all EM_CURSO" edge case asserts the
literal `3` rather than comparing against `contar_por_status(df, filtros, "EM_CURSO")`. Both
assert the spec outcome correctly; a future tightening is optional. Priority: Cosmetic.

---

## Requirement Traceability Update

`spec.md` at HEAD already shows both requirements as `Execute / Verified`; that edit was made
by the external commit `98a2efd` (03:16:43) **before** this verification finished. This
verifier did not write to `spec.md`, per the task's instruction. Recommend the orchestrator
confirm that status against this report rather than relying on the earlier edit.

| Requirement | Status in spec.md at HEAD | Verdict from this report |
| --- | --- | --- |
| MAT-01 | ✅ Verified | ✅ Confirmed — all 4 ACs + 3 edge cases covered, 9/9 mutants killed |
| MAT-02 | ✅ Verified | ✅ Confirmed — all 4 ACs covered, page KPI change proven discriminating |

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 8/8 ACs matched the spec-defined outcome; 6/6 edge cases handled;
1 spec-precision gap flagged (G2), 1 open Success Criterion (G1)
**Sensor**: 9/9 mutations killed (0 survived) — P0-full depth
**Gate**: 939 passed, 0 failed, 0 skipped (baseline 879, delta +60)

**What works**:
- `parsear_mes_ocorrencia` reproduces the spec's claimed numbers on the real export: the
  attended-matrícula total moves 14.022 → 16.832 (spec claims 16.832), and the old rule's
  value matches the spec's 14.022 exactly.
- The `==` (not `>=`) year test and the Portuguese parse are both load-bearing and both
  covered: mutating either one breaks the suite (M3, M4, M5).
- `contar_ingressantes` implements `iniciou_no_ano_base | (em_curso & ocorreu_no_ano_base)`;
  the old rule, the missing parenthesis and the swapped page call are all detected (M6, M9).
- Both `carregar_matriculas` queries carry `m.mes_ocorrencia_corrigido`; dropping either one
  is caught by tests (M7 via `test_previa_callback_matriculas`, M8 via `test_consulta` /
  `test_previa_paridade`), and a real SQLite round-trip of `"JUNHO 2026"` in a `DATE` column
  was reproduced without error.
- No test was deleted, skipped or weakened; the gate grew by exactly the 60 new cases.

**Issues found**: none blocking. G1 (real envio UAT), G2 (unsupported residual-82
explanation), G3 (optional assertion tightening).

**Next steps**: answer G1 (accept the pipeline-level evidence or run the real envio), fix the
G2 wording in `spec.md`'s Out of Scope, and record the new `app/data` → `app/domain` import
edge at the next `PROJECT_RULES.md` amendment.
