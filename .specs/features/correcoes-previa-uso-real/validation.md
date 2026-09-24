# Correções da prévia após o uso real — Validação

**Veredito: PASS.** O gap único da verificação anterior (CPR-04 / P1.3 AC4 — cadastro de campus gravado antes de a prévia terminar de montar) foi corrigido no commit `1f645a4`. As duas escritas (`_cadastrar_unidades_do_envio`, `_completar_unidades_incompletas`) agora rodam dentro do mesmo `try` que chama `preparar_versao`/`execucoes.abrir_previa`, só depois de `abrir_previa` suceder. O teste novo `tests/test_admin_envio.py::test_falha_ao_montar_a_fonte_nao_deixa_cadastro_de_campus_gravado` compara o banco antes/depois de um erro injetado e falha se qualquer escrita persistir. O gate está verde (875 testes) e o sensor, repetido especificamente no gap corrigido, matou a mutação que reintroduz a ordem antiga.

**Data:** 2026-09-24
**Spec:** `.specs/features/correcoes-previa-uso-real/spec.md`
**Diff range:** `4d4bbb8..1f645a4` (feature completa); esta rodada de verificação cobre só o incremento `09ef700..1f645a4` (commit `1f645a4`), que fecha o único gap da verificação anterior
**Verifier:** subagente independente, distinto dos autores dos commits da feature (inclusive do commit de correção `1f645a4`)
**Result**: PASS

## Conclusão das tarefas

T1–T19 seguem com todos os itens `Done when` marcados em `tasks.md` (sem alteração desde a verificação anterior). O cabeçalho de `tasks.md` ainda diz `In Progress` e os requisitos em `spec.md` ainda dizem `Pending`; este relatório os atualiza para `Done`/`Verified` ao final, agora que o único gap foi fechado.

## Critérios de aceitação ancorados na spec

Linhas sem mudança desde a verificação anterior (`09ef700`, 2026-09-23) são revalidadas por reexecução do gate completo (875/875 verdes, nenhum teste removido ou enfraquecido) e por `git log 09ef700..1f645a4` mostrar que só `app/app.py` e `tests/test_admin_envio.py` mudaram — nenhum arquivo por trás das outras 20 evidências foi tocado. A linha de CPR-04 é revalidada do zero com evidência nova.

| AC | Resultado definido na spec | Evidência de teste (`file:line` + asserção) | Estado |
| --- | --- | --- | --- |
| P1.1 AC1 | URL da prévia roteia pelo Dash, mostra faixa e conteúdo, sem 404 | `tests/test_previa_pagina.py:221-224` — status 200, ausência de `404`/`Page not found`, presença de `Prévia não publicada`; slug inválido em `:233-236` | PASS (revalidado — arquivo inalterado) |
| P1.1 AC2 | KPIs/tabela vêm da fonte candidata, sem erro de callback | `tests/test_previa_callback_matriculas.py:141-142` — `Matrículas 1` e tabela sem `Sem dados`; `tests/test_previa_ids_callback.py:92-96` — nenhum ID de `Input`/`State` faltando nos layouts | PASS automatizado; console real pendente de UAT |
| P1.1 AC3 | Unidades do envio aparecem com indicadores não zero | `tests/test_previa_callback_matriculas.py:141` — `Matrículas 1`; `tests/test_previa_paridade.py:166` — cidades `{Santa Maria, Jaguari}` | PASS em dados sintéticos |
| P1.2 AC1 | Quatro layouts públicos incluem todos os componentes de callback | `tests/test_previa_ids_callback.py:92-96` — conjuntos de IDs sem faltantes; `tests/test_paginas_publicas.py:218`, `:323`, `:386`, `:537` — cada Store presente | PASS |
| P1.2 AC2 | Callback público sem prévia lê a versão publicada | `tests/test_previa_paridade.py:262` — saídas da prévia e da publicação iguais após publicação dos mesmos dados; `tests/test_previa_callback_matriculas.py:118-119` — Store público único com `data is None` | PASS |
| P1.2 AC3 | Teste cruza IDs de `Input`/`State` com ambos os layouts nas quatro páginas | `tests/test_previa_ids_callback.py:79-96` — parametrização das quatro páginas, callbacks não vazios e diferença de conjuntos vazia | PASS |
| P1.3 AC1 | Ciclos sem modalidade e respectivas matrículas saem do candidato; envio chega a prévia | `tests/test_previa_candidato.py:252-260` — 1 ciclo e 2 matrículas descartados, só C1/M1 restantes; `tests/test_admin_envio.py:390-397` — 200, estado `previa`, fonte presente | PASS |
| P1.3 AC2 | Resposta e polling informam as duas contagens de descarte | `tests/test_admin_envio.py:392-393` — contagens `1`/`1` na resposta; `tests/test_admin_envio_polling.py:71-72` — `11`/`42` no polling | PASS |
| P1.3 AC3 | Salvar prévia grava versão interna e responde sucesso | `tests/test_admin_envio_salvar_previa.py:145-152` — HTTP 200, estado `salva`, 1 registro interno; `tests/test_execucoes_previa.py:410-421` — candidato salvo | PASS em dados sintéticos |
| **P1.3 AC4 / CPR-04** | Erro de fonte retorna JSON, execução descartável e **nenhuma gravação** | `tests/test_admin_envio.py:672-714` — `test_falha_ao_montar_a_fonte_nao_deixa_cadastro_de_campus_gravado`: monkeypatcha `preparar_versao` para lançar `ValueError`, captura `campi_sistec`/`interna_campus` antes e depois (`:692-700`), afirma `resposta.status_code == 200` (`:705`), `corpo["erro_previa"] == "falha_previa"` (`:706`), `campi_depois == campi_antes` e `interna_depois == interna_antes` (`:710-711`), e explicitamente `"U9" not in campi_depois` / `campi_depois["U2"]["cidade"] is None` (`:712-714`) — a unidade nova não foi cadastrada e a unidade incompleta não foi completada. Código: `app/app.py:483-517` — as escritas (`:494-497`) agora ficam dentro do `try` (`:486`), depois de `execucoes.abrir_previa` suceder (`:490`); qualquer exceção antes disso cai em `except MemoryError`/`except Exception` (`:505-517`), que só setam `resposta["erro_previa"]` e retornam — nenhuma chamada de escrita acontece nesses ramos. | **PASS** |
| P1.3 AC5 | Baixa direta usa o mesmo descarte | `tests/test_previa_candidato.py:270-283` — contagens `1`/`2`; só C1/P1/M1 nas tabelas internas | PASS |
| P1.4 AC1 | Cadastro automático recebe cidade e nome do CSV | `tests/test_admin_envio.py:362-376` — U9 cadastrada com `Cidade Teste` e `Campus U9` | PASS |
| P1.4 AC2 | Campos vazios de unidade existente são preenchidos sem sobrescrever os demais | `tests/test_campi.py:245`, `:260-262`; `tests/test_admin_envio.py:550-551`, `:569-570` — valores exatos preservados/completados | PASS |
| P1.4 AC3 | Publicar copia `interna_campus` e salva anterior na mesma transação | `tests/test_versoes.py:157`, `:184-185` — campus público novo e `anterior_campus` antigo; transação em `app/data/versoes.py:118-143` | PASS |
| P1.4 AC4 | Desfazer restaura o campus anterior | `tests/test_versoes.py:215-216` — campus anterior restaurado e snapshot consumido | PASS |
| P1.4 AC5 | Prévia e assinatura usam `interna_campus` | `tests/test_previa_fonte.py:230` — fonte lê campus interno; `tests/test_previa_candidato.py:302`, `:327` — assinatura acompanha interna e ignora público | PASS |
| P1.4 AC6 | Município e nome da unidade não entram nas tabelas de cursos/ciclos | `tests/test_colunas.py:94-95` — campos ausentes dos schemas graváveis; `:129-131` — PII também descartada | PASS |
| P2 AC1 | Resumo usa contagens do candidato | `tests/test_execucoes_previa.py:511-515` — cursos/ciclos/matrículas/eficiência iguais ao resumo candidato | PASS |
| P2 AC2 | Amostra tem até 20 matrículas com campos da matrícula e do ciclo/curso | `tests/test_execucoes_previa.py:518-532` — valores e conjunto exato de nove colunas; `:546-548` — 20 primeiras de 21 matrículas | PASS |
| P2 AC3 | Amostra exclui colunas pessoais | `tests/test_execucoes_previa.py:558-560` — colunas disjuntas de `COLUNAS_PII`; conjunto exato em `:524-528` | PASS |
| P2 AC4 | Baixa direta conserva resumo/amostra anteriores | `tests/test_admin_envio_polling.py:113-119` — resumo e amostra do ramo de baixa preservados | PASS |

**Resultado:** 21 de 21 ACs cobertos com resultado esperado, nenhuma falha funcional. A ausência de erro no console do navegador e o fluxo com os CSVs reais de 11 campi ainda dependem de UAT, conforme `spec.md` Success Criteria — isso não bloqueia o veredito de código/testes, mas continua registrado como pendência de UAT. A paridade automatizada usa dados sintéticos; não equivale à conferência real da usuária.

## Edge cases

Sem mudança desde a verificação anterior (nenhum arquivo relacionado foi tocado pelo commit `1f645a4`); revalidado por reexecução do gate completo.

| Caso | Evidência | Estado |
| --- | --- | --- |
| Todos os ciclos da unidade sem modalidade: unidade ausente, dados preservados | `tests/test_admin_envio.py:415-416`, `:431-433` | PASS |
| Município divergente: primeiro valor não vazio na ordem dos arquivos | `tests/test_envio.py:130-137` | PASS |
| Publicar com `interna_campus` vazio | `tests/test_versoes.py:219-227` | PASS |
| Mudança em `interna_campus` após abrir prévia: Salvar recusado | `tests/test_previa_estado.py:127-139`, `tests/test_admin_envio_salvar_previa.py:58-61` — HTTP 409 | PASS |

## Gate e integridade dos testes

Gate definido em `tasks.md`: `python -m pytest tests/ -q`. Neste shell, `python` está no PATH (ambiente diferente do usado na verificação anterior, que precisou de `uv run`); rodei o comando direto, sem flags extras.

- **Comando:** `python -m pytest tests/ -q`
- **Resultado:** 875 passed, 0 failed, 0 skipped, 0 errors, 79,18 s.
- **Antes desta rodada de correção:** 874 passed (verificação anterior, `09ef700`). **Delta:** +1 (`test_falha_ao_montar_a_fonte_nao_deixa_cadastro_de_campus_gravado`), nenhum teste removido.
- **Antes da feature inteira:** 825 passed + 2 failed pré-existentes = 827 (`.specs/STATE.md`). **Delta acumulado da feature:** +48 casos.
- Nenhum resíduo temporário: o teste novo usa `tmp_path` (fixture `banco_temporario`), sem diretório criado no repositório.

## Sensor de discriminação

**Escopo desta rodada:** focado no gap corrigido (CPR-04). Não repeti as 5 mutações genéricas da verificação anterior (roteamento, ingest, versões, fonte, amostra) porque nenhum arquivo por trás delas mudou entre `09ef700` e `1f645a4` — `git log 09ef700..1f645a4 --stat` mostra só `app/app.py` e `tests/test_admin_envio.py`.

**Isolamento:** `git worktree add --detach <scratch> HEAD` (`%TEMP%\cpr04-sensor-1436`) — desta vez a criação teve sucesso (a verificação anterior tinha batido em `Permission denied`). Baseline de `git status --porcelain` da árvore real capturado antes de qualquer ação no scratch.

**Achado de ambiente (não é falha da feature):** rodar `tests/test_admin_envio.py` isolado no worktree devolvia 30/33 falhas por `302` em vez do código esperado — não por causa da mutação, mas porque o worktree não tem o `app/data/sistec.db` local (não versionado) com a instalação já concluída; `_exigir_instalacao` (`app/app.py:227-239`) redireciona qualquer rota `/admin/*` para `/admin/instalacao` enquanto `app.data.instalacao.concluida()` (que lê `app/data/schema.DEFAULT_DB_PATH`, não o `DEFAULT_DB_PATH` de `app_module` que os testes trocam por `banco_temporario`) não achar a instalação concluída nesse banco. Corrigido criando um banco descartável só no scratch (`init_db` + `instalacao.concluir`, nenhum dado real copiado) antes de rodar os testes — isso não altera nenhuma asserção nem o comportamento avaliado, só destrava o gate de instalação que é lido de um caminho fixo do módulo, fora do que os testes desta rota trocam.

| Mutação no snapshot | Teste alvo e resultado | Estado |
| --- | --- | --- |
| `app/app.py`: mover `_cadastrar_unidades_do_envio(...)` e `_completar_unidades_incompletas(...)` de volta para antes do `try`/`preparar_versao` (reproduz exatamente o bug pré-`1f645a4`) | `tests/test_admin_envio.py` completo: 32 passed, **1 failed** — `test_falha_ao_montar_a_fonte_nao_deixa_cadastro_de_campus_gravado` falha em `assert campi_depois == campi_antes` (linha 710), com `U9` presente em `campi_depois` e `dict` completo divergente; as outras 32 (inclusive `test_falha_ao_montar_a_fonte_devolve_erro_json_nunca_500`) continuam verdes | **morta** |

**Resultado:** 1/1 mutação matada pelo teste que a verificação anterior pediu como fix task; nenhuma sobreviveu.

**Verificação de isolamento:** `git worktree remove --force <scratch>`; `git status --porcelain` da árvore real após a remoção é byte-idêntico ao baseline capturado antes do sensor (mesmas 7 linhas de modificação + 3 untracked já presentes no início da sessão). Nenhuma mutação vazou para a árvore real.

## Interactive UAT Results

Não realizado nesta rodada — escopo era fechar o gap de código/testes apontado pela verificação anterior. UAT com os CSVs reais de 11 campi continua pendente, como já registrado antes.

## Qualidade, rastreabilidade e UAT

- O commit `1f645a4` só move duas chamadas já existentes para dentro do `try` já existente e adiciona comentários explicativos (`app/app.py:491-493`, `:512-514`); nenhuma abstração nova, nenhum arquivo fora do escopo do gap tocado.
- O teste novo segue o padrão dos demais testes de rota do arquivo (fixtures `sessao`/`banco_temporario`/`monkeypatch` já existentes), mede estado do banco antes/depois em vez de só a resposta HTTP — mais forte que os testes anteriores de erro da mesma rota.
- Nenhuma nova dependência. `app/domain/` não foi alterado.
- `README.md`/`TESTAR.md` não precisaram de atualização para este incremento (o comportamento documentado — "erro na montagem não grava nada" — já estava correto na descrição; só o código não cumpria).
- `spec.md` e `tasks.md` são atualizados por este relatório: requisitos `CPR-01`..`CPR-07` de `Pending` para `Verified`/`Done`, cabeçalho de `tasks.md` de `In Progress` para `Done`.
- `validate_state.py correcoes-previa-uso-real` deve ser executado depois destas atualizações e terminar com exit 0.

**Resumo:** gate 875/875; sensor 1/1 mutação matada (foco no gap); critérios 21/21; **PASS**.
