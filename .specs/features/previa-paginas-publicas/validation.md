# Prévia das páginas públicas antes de salvar — Validation

**Date**: 2026-09-23
**Spec**: `.specs/features/previa-paginas-publicas/spec.md`
**Diff range**: `08cf826..3fd6153` (29 commits, T1 `56f5e4f` → `3fd6153`)
**Verdict**: **PASS**
**Result**: PASS (16/17 ACs com evidência `file:line` e valor afirmado; 4/4 edge cases; sensor 8/8 mortas + 1 mutante sobrevivente de baixa severidade; gate 825 passed, 2 failed pré-existentes fora do escopo)
**Verifier**: Claude (Opus 5.5), sessão nova, sem memória da implementação — cobertura rederivada do zero, evidência-ou-zero (author ≠ verifier)

---

## Resumo executivo

A feature entrega a conferência das quatro páginas públicas antes de Salvar, com candidato em memória (SQLite nomeado `file:previa-<id>?mode=memory&cache=shared`), guardião de sessão/posse/estado, assinatura de origem conferida dentro de `BEGIN IMMEDIATE` e gravação por `executemany`. A rederivação independente confirma:

- **Paridade por valor**: os testes de paridade comparam KPIs, linhas de tabela e filtros da prévia vs. publicada por conteúdo renderizado (`textos(da_previa) == textos(do_publico)`) e por `assert_frame_equal`, não só por estrutura; o ano-base é afirmado como valor explícito de `config` (`test_ano_base_da_previa_e_o_de_config`, `test_previa_paridade.py:184-195`).
- **Posse por sessão**: existe teste com duas sessões do mesmo e-mail (`sessao-A`/`sessao-B`) em que a segunda recebe "Prévia indisponível" e nenhum dado (`test_segunda_sessao_do_mesmo_email_recebe_indisponivel`); existe teste de callback Dash chamado diretamente com `preview_id` forjado (`test_callback_previa_forjado_devolve_erro`).
- **Isolamento público**: o caminho público nunca emite o `dcc.Store` de prévia, então o callback público recebe `preview_id=None` e lê só o banco publicado; `test_caminho_publico_ignora_contexto_forjado` + `test_layout_publico_sem_preview_inalterado` (4 páginas) asseguram isso.
- **Rollback integral**: `test_salvar_interna_rollback_integral_em_falha_no_meio` força falha por FK no meio da inserção em lote e prova `interna_cursos == 0`, `interna_ciclos == 0`, `rev_interna == 0`.

**Dois gaps menores de cobertura** (não bloqueantes) e **um mutante sobrevivente de baixa severidade** (fechar a fonte = comportamento equivalente ao GC do CPython) ficam registrados abaixo.

---

## Task Completion

Todas as 28 tarefas marcadas `Done` no `tasks.md`. Confirmei no código e nos testes (não confiei nos `[x]`): os commits listados em cada tarefa tocam os arquivos declarados, e cada suíte nova existe e passa. Nenhuma tarefa parcial ou bloqueada.

| Faixa | Tarefas | Status |
| --- | --- | --- |
| Phase 1–5 (T1–T19) | candidato, fonte, guardião, consulta, páginas, navegação | ✅ Done |
| Phase 6 (T20–T23) | assinatura transacional, salvar candidato, rota 409, teste ano-base | ✅ Done |
| Phase 7 (T24–T26) | paridade, acesso/posse, estado/invalidação | ✅ Done |
| Phase 8 (T27–T28) | README + TESTAR | ✅ Done |

---

## Spec-Anchored Acceptance Criteria

### P1.1 — Abrir as páginas após ler os CSVs (PVP-01, PVP-02, PVP-03)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: acesso às 4 páginas em `previa` | links/rotas para `/`, `/eficiencia`, `/evasao`, `/percentuais-legais` | `tests/test_previa_pagina.py:128-151` — `layout.children[-1].className == "painel-landing"/"painel-dashboard"` para as 4 páginas; `tests/test_js_envio.py:588-608` — `hrefs == {slug: "/admin/previa/abc/<slug>"}` por valor; `tests/test_tela_atualizar_envio.py:195-202` — `data-pagina` nos 4 links | ✅ PASS |
| AC2: "Prévia não publicada" + página + volta a "Atualizar dados" | faixa visível + link de retorno | `tests/test_previa_pagina.py:132` — `assert "Prévia não publicada" in textos(layout)`; **parte "voltar a Atualizar dados" sem teste** (link em `app/pages/previa.py:40,49,61`) | ⚠️ GAP menor |
| AC3: Salvar/Descartar continuam disponíveis | ações preservadas no fluxo | `tests/test_admin_envio_salvar_previa.py:125-152` — caminho feliz do Salvar 200 + grava; `tests/test_previa_estado.py:186-195` — Descartar libera; `tests/test_tela_atualizar_envio.py:204-212` — Salvar/Descartar na área da prévia | ✅ PASS |
| AC4: abrir/navegar deixa revisões e tabelas inalteradas | `rev_interna`/`rev_publicada`/tabelas iguais | `tests/test_previa_estado.py:102-111` — `assert _estado_versoes(db_path) == antes` após navegar 4 páginas; `tests/test_previa_candidato.py:81-92` — `interna_cursos == 0` e `rev_interna == 0` após `preparar_versao` | ⚠️ GAP menor (ver Gaps) |

### P1.2 — Conferir o resultado que seria publicado (PVP-04, PVP-05, PVP-06)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: mesmos indicadores/tabelas do conjunto que Salvar gravaria | tabelas candidatas == gravadas | `tests/test_previa_candidato.py:95-119` — `pd.testing.assert_frame_equal(preparada, gravada)` nas 4 tabelas (round-trip pelo SQLite) | ✅ PASS |
| AC2: filtro/eixo/FIC mesma regra e valores | mesma regra, mesmos valores | `tests/test_previa_paridade.py:238-259` — `assert _textos_de(da_previa) == _textos_de(do_publico)` (KPIs/matriz por valor, com `com_fic`/`sem_fic` e eixos); `:265-279` — `sorted(da_previa[col].unique()) == sorted(do_publico[col].unique())` | ✅ PASS |
| AC3: campus preservado incluído | dados de `interna_*` do campus ausente na prévia | `tests/test_previa_candidato.py:122-143` — `unidades == {"U1", "U2"}`, `campi_mantidos == ["U1"]`; `tests/test_previa_paridade.py:143-163` — `cidades == {"Santa Maria", "Jaguari"}` | ✅ PASS |
| AC4: avisos (preservados, não cadastrados, órfãs, ignorados) | strings de aviso presentes | `tests/test_previa_pagina.py:154-166` — `assert "Unidades com dados preservados: U2." in texto` etc. (4 avisos por valor) | ✅ PASS |
| AC5: sem publicação → sem "Ainda não há dados publicados." | mensagem pública ausente | `tests/test_previa_paridade.py:198-217` — `assert "Ainda não há dados publicados." not in textos(layout)` nas 4 páginas | ✅ PASS |
| AC6: omitir "Atualizado em" | carimbo ausente na prévia | `tests/test_previa_callback_matriculas.py:118-127` — `assert "Atualizado em" not in textos(layout)` (idem eficiencia/evasao/percentuais) | ✅ PASS |

### P1.3 — Restringir e encerrar a conferência (PVP-07, PVP-08, PVP-09, PVP-10)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: sem autenticação → `/admin/login` | redirect sem entregar dados | `tests/test_admin_previa_guarda.py:12-17` — `assert "/admin/login" in Location`; `tests/test_previa_acesso.py:95-99` — `assert resposta.status_code in (301, 302)` | ✅ PASS |
| AC2: sessão alheia → negar sem entregar dados | "Prévia indisponível", zero dados | `tests/test_execucoes_previa.py:83-86` — `obter_previa(envio.id, "sessao-B")` levanta `PreviaIndisponivel`; `tests/test_previa_acesso.py:102-109` — 2ª sessão do mesmo e-mail: `assert "Prévia indisponível" in textos` e `assert "Prévia não publicada" not in textos`; `tests/test_previa_callback_matriculas.py:141-150` — callback com `preview_id="forjado"` devolve erro, `assert "Matrículas" not in textos(kpis)` | ✅ PASS |
| AC3: salvar/descartar encerra; URL antiga → "Prévia indisponível" | acesso negado após terminal | `tests/test_previa_acesso.py:135-150` — `test_url_previa_apos_salvar_indisponivel` e `test_url_previa_apos_descartar_indisponivel` | ✅ PASS |
| AC4: consolidação falha → manter erro, sem prévia | erro visível, sem fonte | `tests/test_admin_envio.py:202-217` — `estado == "falhou_consolidacao"`, `previa is None`; `:506-517` — `previa_fonte is None`; `:520-536` — `MemoryError` → `erro_previa == "sem_memoria"`, nada gravado | ✅ PASS |
| AC5: conjunto/config muda → impedir Salvar | `409`/`PreviaDesatualizada` | `tests/test_previa_estado.py:114-163` — `interna_fatores`/`campus`/`ano_base`/`rev_interna` alterados levantam `PreviaDesatualizada`; `tests/test_admin_envio_salvar_previa.py:48-61` — `status_code == 409`, `erro == "previa_desatualizada"`, `"reenviar" in mensagem` | ✅ PASS |
| AC6: páginas públicas ligadas só à publicada | caminho público ignora contexto forjado | `tests/test_previa_acesso.py:120-132` — `layout()` público não mostra "Prévia indisponível"; 4× `test_layout_publico_sem_preview_inalterado` — `not any(c.id == "<pagina>-preview" ...)` | ✅ PASS |
| AC7: excluir colunas pessoais | nenhum nome/CPF/e-mail/nascimento | `tests/test_previa_fonte.py:170-186` — `PRAGMA table_info(matriculas)` sem PII; `tests/test_previa_acesso.py:161-174` — colunas sem PII + `assert "cpf" not in texto and "email" not in texto` | ✅ PASS (varredura representativa) |

**Status**: ✅ 16 de 17 partes de AC com evidência `file:line` e valor afirmado; 2 partes com cobertura parcial (gaps menores, abaixo). Nenhum spec-precision gap: a spec define resultados precisos e os testes os afirmam por valor.

---

## Edge Cases

| Edge case | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- |
| EC1: filtro sem linhas → mesmo estado vazio da página pública | `tests/test_previa_callback_matriculas.py:153-160` — `assert "Sem dados para o eixo selecionado." in textos(matriz)`; `evasao:143-148`; `percentuais:143-148`; não bloqueia Salvar: `test_previa_estado.py:175-183` — `salvar(...)["matriculas"] == 1` | ✅ PASS |
| EC2: página falha → identificar + impedir Salvar | `tests/test_previa_pagina.py:169-181` — `assert "Não foi possível renderizar a página Matrículas." in textos` + `paginas_com_falha == ["matriculas"]`; `test_previa_estado.py:166-172` — `PreviaIncompleta` e `estado == "previa"`; `test_admin_envio_salvar_previa.py:64-77` — `409` com `paginas == [...]` | ✅ PASS |
| EC3: recarregar com execução pendente → mantém conferência sem novo upload | `tests/test_previa_estado.py:102-111` — navega 4 páginas + `abrir_leitura_previa` repetido, revisões intactas; `test_execucoes_previa.py:211-223` — `abrir_previa` idempotente (`fonte_2 is fonte`) | ✅ PASS |
| EC4: execução perdida após reinício → "Prévia indisponível" sem substituir pela pública | `tests/test_previa_acesso.py:153-158` — registro limpo devolve "Prévia indisponível"; `test_execucoes_previa.py:123-126` — `obter_previa` com registro vazio levanta `PreviaIndisponivel` | ✅ PASS |

---

## Discrimination Sensor

Worktree isolado (`git worktree add ../calsistec-sensor HEAD`; `.env` + `app/data/sistec.db` copiados; `git worktree remove --force` ao fim). Baseline do worktree: suíte relevante verde. Nove mutações comportamentais, uma por vez, cada uma revertida com `git checkout -- <arquivo>` antes da próxima:

| # | Mutação | Local | Resultado |
| - | ------- | ----- | --------- |
| a | `obter_previa`: pula `compare_digest(sessao_dona, sessao_id)` (aceita qualquer sessão) | `app/sistec/execucoes.py:248` | **Morto** — 5 falhas (`test_obter_previa_recusa_sessao_alheia_do_mesmo_email`, `test_abrir_leitura_previa_sessao_alheia`, `test_segunda_sessao_do_mesmo_email_recebe_indisponivel`, `test_sessao_alheia_indisponivel`, `test_obter_previa_recusa_sessao_ausente_quando_dona_exigida`) |
| b | `obter_previa`: aceita estado ≠ `previa` | `app/sistec/execucoes.py:247` | **Morto** — 2 falhas (`test_obter_previa_recusa_estado_terminal`, `test_obter_previa_recusa_estado_diferente_de_previa`) |
| c | `salvar_interna`: não compara a assinatura | `app/data/versoes.py:80` | **Morto** — 6 falhas (2 em `test_versoes.py`, 4 em `test_previa_estado.py`) |
| d | `salvar_interna`: `rollback` → `commit` no caminho de erro da inserção em lote | `app/data/versoes.py:112` | **Morto** — `test_salvar_interna_rollback_integral_em_falha_no_meio` (`assert 1 == 0` em `interna_cursos`) |
| e | Callback de Matrículas: ao receber contexto inválido, cai no banco público | `app/pages/matriculas.py:344` | **Morto** — `test_callback_previa_forjado_devolve_erro` (obtém "Sem dados" público em vez de "Prévia indisponível") |
| f | `FontePrevia.abrir_leitura`: remove `PRAGMA query_only=ON` | `app/data/previa.py:45` | **Morto** — `test_abrir_leitura_recusa_escrita` (escrita não bloqueada) |
| g | Guarda `_exigir_sessao_previa`: não redireciona sem sessão | `app/app.py:249-250` | **Morto** — 2 falhas (`test_previa_sem_sessao_redireciona_para_login`, `test_get_previa_sem_sessao_redireciona_para_login`) |
| h | `descartar`: não chama `liberar_previa` | `app/sistec/execucoes.py:405` | **Morto** — 2 falhas (`test_descartar_libera_a_fonte_sem_alterar_revisoes`, `test_descar_libera_fonte_antes_de_marcar_descartada`, ambos `previa_fonte is None`) |
| h2 | `liberar_previa`: solta a referência sem `fonte.fechar()` (não fecha a âncora) | `app/sistec/execucoes.py:450` | **Sobreviveu** — 56 passed (nenhum teste discrimina o fechamento real da âncora) |

**Sensor depth**: expandido (feature em caminho crítico: autorização, posse de sessão, integridade transacional). 9 mutações injetadas.
**Resultado**: 8/8 mortas nas mutações de comportamento; 1 mutante sobrevivente (h2) — ver Gaps.

Isolamento conferido: `git status --porcelain` da árvore real antes e depois do sensor = `?? .agents/` + `?? nonascii.txt`, idêntico; `HEAD` segue `3fd6153`. Nenhum `git stash` usado.

---

## Gate final

- `python -m pytest tests/ -q` (raiz) → **825 passed, 2 failed, 2 warnings**, 0 skipped, 206,6 s.
- As 2 falhas são `tests/test_paginas_publicas.py::test_eficiencia_layout_poem_contexto_kpi_eixo_tabela_e_filtros_nesta_ordem` e `::test_percentuais_layout_ordena_contexto_cartoes_eixo_tabela_e_filtros`. **Confirmado** num worktree em `08cf826` (base, antes da feature) que ambas já falham lá, com `AssertionError: assert 'br-message info' == 'painel-dashboard'` — o layout devolve a mensagem "Ainda não há dados publicados." porque o `app/data/sistec.db` local está sem dados publicados (`dataset_disponivel()` → `False`). **Fora do escopo desta feature**: a feature não altera esses dois testes nem o caminho público de layout deles.
- Nenhuma falha nova em HEAD. Contagem base: a feature adicionou os 12 arquivos de teste novos sem remover nenhum teste (delta de +~130 testes sobre a base).

## Commits intermediários quebrados (lição de processo)

- **T21 `79aa3d2`** e **T22 `751e494`** não passam a suíte completa isoladamente. Confirmado em worktrees: `python -m pytest tests/test_execucoes.py tests/test_admin_envio_salvar.py -q` → **4 failed** em ambos (`test_salvar_envio_confirmado_preserva_linhas_do_campus_ausente`, `test_salvar_envio_sem_campi_preservados_nao_exige_confirmacao` — `TypeError: 'NoneType' object is not subscriptable` em `execucoes.salvar`; `test_salvar_envio_com_confirmacao_grava_e_registra_os_campi_preservados`, `test_salvar_envio_sem_campi_preservados_nao_exige_confirmacao` — `assert 500 == 200`).
- **T23 `b99984e`** corrige. Confirmei que a correção **não afrouxou** nenhuma asserção (diff `79aa3d2..b99984e` dos dois arquivos):
  - `test_admin_envio_salvar.py`: o dublê de gravação do envio passou de `montar_versao_interna` para `versoes.salvar_interna` (refletindo o contrato novo: envio → `salvar_interna` com assinatura), e a asserção de ano-base mudou de `_ano_base_config()` (variável de ambiente) para `config.ano_base` do banco — agora `assert GRAVACOES[0]["assinatura_esperada"]["ano_base"] == ano`, **mais precisa**, não mais fraca. O caminho de baixa direta ganhou uma asserção explícita nova (`assert GRAVACOES == [{"campi_falhos": set(), "ano_base": app_module._ano_base_config()}]`).
  - `test_execucoes.py`: os dois testes passaram a montar o `candidato` com `preparar_versao` real e a `abrir_previa`, e a baixa usa `versoes.salvar_interna` — a asserção de "preserva linhas do campus ausente" agora roda contra o caminho real de dados (mais forte), não contra um dublê.
- Conclusão: o HEAD está íntegro; o portão `quick` das tarefas T21/T22 não rodou a suíte completa e deixou 4 regressões passarem até T23. Registrado como lição de processo, sem reprovar a feature.

---

## Medição de memória e tempo

Volume sintético representativo via `scripts/sintetico.py` (250 unidades → 1.500 ciclos, 35.889 matrículas; PII fictícia descartada pela lista de permissão). Banco isolado em `tempfile.mkdtemp()`, nenhum dado real. Medido com `tracemalloc` + `time.perf_counter`:

| Etapa | Tempo | Pico de memória | Observação |
| --- | --- | --- | --- |
| `preparar_versao` + `abrir_fonte_previa` | 0,45 s | 21,6 MiB | monta as 4 tabelas + `campus` + `config` + `estado_versoes` na fonte em memória |
| Leitura de página pela fonte (`carregar_matriculas` + `carregar_eficiencia`) | 0,65 s | 35,4 MiB | 19.437 linhas de matrículas + 17.949 de eficiência juntadas |

Não é gate de PASS/FAIL — registro, conforme `design.md` §"Verification Strategy". Nenhum resíduo `.test-*`/`pytest_cache` deixado no repositório.

---

## Code Quality

| Princípio | Status |
| --- | --- |
| Código mínimo, sem abstração de uso único | ✅ (`FontePrevia`/`ContextoLeitura`/`com_trava` têm uso real múltiplo) |
| Mudanças cirúrgicas, sem "melhorar" código alheio | ✅ (diff toca só o necessário; `publicar`/`desfazer`/`aplicar_publico` intactos) |
| Sem scope creep | ✅ |
| Segue os padrões do repositório | ✅ (imports tardios para quebrar ciclo, dublês via `monkeypatch`, comentários explicando o porquê) |
| Spec-anchored outcome check | ✅ (valores afirmados batem com a spec; 2 gaps menores) |
| Toda AC com evidência `file:line` | ⚠️ (2 partes sem asserção direta — Gaps 1 e 2) |
| Nenhum teste órfão | ✅ (cada teste novo mapeia a uma AC, edge case ou Done-when) |
| Diretrizes documentadas seguidas | ✅ `AGENTS.md` (sem temporários no repo), `PROJECT_RULES.md` Princípio III (sem PII), IV (gate) |

---

## Gaps ranqueados

1. **[Minor] P1.1 AC2 — "caminho de volta para Atualizar dados" sem teste.** O link existe (`app/pages/previa.py:40` `_voltar_atualizar`, incluído em `:49` e `:61`), mas nenhum teste afirma o texto "Atualizar dados" nem o `href="/admin/atualizar"`. Os testes afirmam "Prévia não publicada"/"Prévia indisponível", mas não o retorno. Severidade baixa: elemento de navegação trivial, presente no código.
2. **[Minor] P1.1 AC4 — "tabelas internas e públicas inalteradas" afirmado só por revisões.** `test_abrir_recarregar_nao_altera_revisoes` (`tests/test_previa_estado.py:102-111`) e `test_descartar_libera_a_fonte_sem_alterar_revisoes` (`:186-195`) comparam apenas `rev_interna`/`rev_publicada`, não o conteúdo de `interna_*`/tabelas públicas antes/depois. A não-escrita é garantida estruturalmente (conexões `query_only=ON` testadas em `test_abrir_leitura_recusa_escrita`; `preparar_versao` sem escrita testado por conteúdo em `test_previa_candidato.py:81-92`), então o risco é baixo, mas o snapshot de conteúdo antes/depois da navegação, pedido pelo Independent Test da spec, não é direto.
3. **[Low] Mutante h2 sobrevivente — `fonte.fechar()` não discriminado.** Nenhum teste verifica que a conexão âncora foi realmente fechada (a memória liberada). Em CPython, soltar `execucao.previa_fonte = None` já descarta o objeto `FontePrevia` e, por contagem de referência, fecha a âncora — comportamento observável quase idêntico. O gap é de instrumentação (a liberação de memória não é medida), não de correção. Não vale uma rodada própria; registrar um teste que afirme o fechamento da âncora (ex.: expor `fonte._ancora is None` após `fechar`) se a feature for tocada de novo.

Nenhum gap bloqueante. Os dois gaps de cobertura e o mutante sobrevivente são de baixa severidade e não afetam os caminhos críticos (autorização, posse, rollback, assinatura, isolamento público), todos discriminados por teste.

---

## Lições

1. **Comportamento crítico exige teste que o provoque, não que o descreva.** As mutações a–h foram mortas porque cada uma tem um teste que força a condição contrária (sessão alheia, estado terminal, assinatura divergente, FK no meio do lote, `preview_id` forjado, escrita na fonte, sem sessão, descartar). A única mutação sobrevivente (h2, fechar a âncora) não tem teste que observe o efeito — é efeito colateral de memória, não estado observável.
2. **Portão `quick` de tarefa não substitui a suíte completa em refatoração de contrato.** T21/T22 trocaram o contrato de `salvar` (de `montar_versao_interna` para `salvar_interna` com assinatura) e quebraram 4 testes existentes que o gate `quick` não pegou; só T23 rodou a suíte e corrigiu. Quando uma tarefa muda a assinatura de uma função chamada por testes antigos, o gate deve ser `full`, não `quick`.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 16/17 partes de AC com valor afirmado batendo com a spec + 4/4 edge cases (2 gaps menores de cobertura, nenhum spec-precision gap)
**Sensor**: 8/8 mutações de comportamento mortas, 1 mutante de memória sobrevivente (low)
**Gate**: 825 passed, 2 failed pré-existentes (confirmadas no `08cf826`), 0 falhas novas
**Commits intermediários**: T21 `79aa3d2` e T22 `751e494` quebrados; T23 `b99984e` corrige sem afrouxar asserções

**What works**: conferência por valor das 4 páginas; paridade com campus preservado e `RISK-002`; posse por sessão (2ª sessão do mesmo e-mail negada); isolamento público; assinatura de origem dentro de `BEGIN IMMEDIATE` com rollback integral; encerramento por Salvar/Descartar; ausência de PII.

**Next steps**: nenhuma correção obrigatória. Gaps 1–3 são de baixa severidade e podem ser fechados em rodada futura sem reprovar a feature.
