# Atualização por Upload de Pastas — Validation

**Spec**: `.specs/features/atualizacao-por-upload/spec.md`
**Design**: `.specs/features/atualizacao-por-upload/design.md`
**Tasks**: `.specs/features/atualizacao-por-upload/tasks.md`
**Verdict**: **PASS**
**Diff range**: `2cf5fc7..1237cc0` (12 commits: `a44a55c` T1 … `1237cc0` T12), fechamento em `ea76753` (hash de T12 registrado em tasks.md)
**Author**: DeepSeek (via `handoff-ds`), T1–T5 e T6–T12 em duas sessões
**Verifier**: Claude (Sonnet 5), sessão orquestradora — não escreveu nenhuma linha de código da feature, revisou todo diff antes de commitar e executa este relatório de forma independente (author ≠ verifier)

---

## Spec-anchored outcome check

Por requisito, o valor esperado é o que a spec define — não o que a implementação produz.

| Req | Evidência (`file:line`) | Checagem |
| --- | --- | --- |
| UPL-01 | `app/templates/atualizar.html:12-24` (radio de origem), `:59-112` (bloco de envio); `app/static/js/atualizar.js:81-96,469-472` (alternância) | Duas origens visíveis e alternáveis; `escolherOrigem` esconde/mostra os blocos corretos. |
| UPL-02 | `app/app.py:343` `@requer_autenticacao` na rota `/admin/atualizar/envio` | Rota exige sessão administrativa, mesmo decorator das demais rotas de `/admin/atualizar/*`. |
| UPL-03 | `app/sistec/colunas.py:80-104` `ler_planilha`; `app/sistec/envio.py:22-34` `_ler_pasta` chama `ler_planilha` | `;`/`cp1252`, lista de permissão via `aplicar_permissao` — mesma função usada pela baixa (`app/sistec/execucoes.py:216`). |
| UPL-04 | `app/sistec/envio.py:22-24` filtra por `.lower().endswith(".csv")`; `:23` `EnvioInvalido(nome_pasta, "pasta_vazia")` | Pasta vazia recusada antes de ler; não-`.csv` cai em `ignorados` (`envio.py:41`). |
| UPL-05 | `app/sistec/execucoes.py:148-174` `criar_execucao_envio`/`registrar_leitura`; `app/app.py:343-379` orquestra leitura → execução → consolidação | Um `Par` por arquivo; `_consolidar_ou_falhar` (reused, não alterado) leva a `previa`. |
| UPL-06 | `app/sistec/envio.py:44-47` `finally: arquivo.close()`; design.md documenta a decisão de processamento síncrono | Buffer do `FileStorage` fechado ao fim da leitura, dentro da própria requisição. |
| UPL-07 | `app/sistec/envio.py:79-83` `campi_ausentes` | Cadastrados sem `co_unidade` presente nos ciclos consolidados — sensor confirmou (mutante 2 abaixo). |
| UPL-08 | `app/sistec/execucoes.py:41-42` `ConfirmacaoNecessaria`; `:310-311` gate em `salvar`; `app/app.py:476-495` traduz para `409`; `atualizar.js:284-320` bloqueia o botão até checkbox marcado | Servidor recusa sem `confirmar_preservacao`; sensor confirmou (mutante 1 abaixo). |
| UPL-09 | `app/app.py:524,558-568` campos novos no polling; `app/sistec/envio.py:85-88` `campi_nao_cadastrados` | `origem`, `campi_preservados`, `campi_nao_cadastrados`, `arquivos_ignorados`, `matriculas_orfas` presentes; baixa devolve `origem="baixa"` e listas vazias. |
| UPL-10 | `app/sistec/colunas.py:91-93` checagem de colunas obrigatórias | Sensor confirmou (mutante 3 abaixo). |
| UPL-11 | `app/app.py:343-379` propaga `ConsolidacaoInvalida` → `falhou_consolidacao`, `historico_encerrar(..., detalhe={"erro": ...})` | Reusa `_consolidar_ou_falhar` sem alteração; mesmo desfecho da baixa. |
| UPL-12 | `app/sistec/envio.py:8-13` `EnvioInvalido` só carrega `arquivo`/`motivo`; `app/app.py:43` `MAX_CONTENT_LENGTH` global cobre `413` | Nenhuma mensagem cita conteúdo de célula (conferido nos testes `tests/test_envio.py`, `tests/test_admin_envio.py`). |
| UPL-13 | `app/app.py:278-284` (baixa checa execução existente, agnóstico de `origem`); rota de envio replica a mesma checagem (`:344-350`) | Baixa e envio compartilham `_REGISTRO`/`obter_do_admin`; um bloqueia o outro (RN-11). |
| UPL-14 | `app/data/historico.py:19` `"envio"` em `TIPOS_VALIDOS`; `app/data/schema.py` migração `_garantir_tipo_envio_historico` | Tipo novo aceito; bancos v2 existentes migrados sem perda de linha (`tests/test_historico_envio.py`). |

**Gaps de precisão encontrados**: nenhum. As únicas divergências entre spec e implementação são desvios já documentados e justificados nos commits (migração de schema em T6, fechamento de `FileStorage` em T7) — nenhuma delas afrouxa um AC; ambas o cumprem com mais rigor do que o texto exigia.

---

## Discrimination sensor

Executado em worktree isolado (`git worktree add`, removido ao final; `git worktree list` e `git status --porcelain` na árvore real conferidos idênticos ao estado pré-sensor). Três mutações comportamentais, uma por vez, cada uma testada e revertida antes da próxima:

| # | Mutação | Local | Resultado |
| - | ------- | ----- | --------- |
| 1 | Inverte o portão de confirmação: `not confirmado` → `confirmado` | `app/sistec/execucoes.py:310` | **Morto** — `tests/test_execucoes.py`: 2 falhas (`test_salvar_envio_com_campi_preservados_exige_confirmacao`, `test_salvar_envio_confirmado_preserva_linhas_do_campus_ausente`) |
| 2 | Inverte a comparação de campi ausentes: `not in presentes` → `in presentes` | `app/sistec/envio.py:82` | **Morto** — `tests/test_envio.py`: 4 falhas |
| 3 | Enfraquece a checagem de colunas obrigatórias: `any(...)` → `all(...)` | `app/sistec/colunas.py:92` | **Morto** — `tests/test_colunas.py`: 1 falha (`test_ler_planilha_recusa_coluna_obrigatoria_ausente`) |

3 de 3 mutantes mortos. Nenhum sobrevivente — nenhuma tarefa de correção gerada.

---

## Gate final

- `python -m pytest tests/ -q` → **661 passed**, 2 warnings (pré-existentes, não relacionados à feature — `FutureWarning` de `.fillna` em `app/data/fatores.py`, fora do escopo desta feature).
- `python .claude/skills/tlc-spec-driven/scripts/validate_tasks.py atualizacao-por-upload` → 0 erros, 2 avisos aceitos (T12: `Tests: none` coerente com a matriz; `Where` com dois arquivos da mesma seção de documentação).
- `python scripts/verificar_prontidao_cutover.py` → NO-GO por duas condições de ambiente pré-existentes e não relacionadas à feature (`ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` e `CALCSISTEC_HTTPS=1` ausentes nesta máquina de desenvolvimento) — nenhuma checagem de PII, schema ou dado publicado falhou.
- Working tree limpo após o sensor: `git status --porcelain` sem diferença de conteúdo além dos avisos de fim de linha do Git no Windows.

## Lições

Nenhuma falha fundamentada (mutante sobrevivente, gap de precisão de spec, AC falho, ou desvio não registrado) surgiu nesta rodada — nada a distilar em `.specs/LESSONS.md`.

Um ponto de processo, não de código: os artefatos de spec/design/tasks desta feature ficaram fora do git até o commit `9268f7d` (metade da execução). Passam a ser versionados desde o início nas próximas features.
