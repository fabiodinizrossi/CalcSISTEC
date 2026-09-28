# Correções do Envio de Pastas — Validation

**Spec**: `.specs/features/correcoes-envio-pastas/spec.md`
**Design**: `.specs/features/correcoes-envio-pastas/design.md`
**Tasks**: `.specs/features/correcoes-envio-pastas/tasks.md`
**Verdict**: **PASS**
**Diff range**: `7717641..83b768b` (7 commits: T1–T7) + `c838393` (teste que fecha o mutante sobrevivente) + `365470d` (versionamento de spec/design)
**Author**: DeepSeek (via `handoff-ds`)
**Verifier**: Claude (Sonnet 5), sessão orquestradora — não escreveu o código de T1–T7, revisou todo diff antes de aceitar e executa este relatório de forma independente (author ≠ verifier)

---

## Spec-anchored outcome check

| Req | Evidência (`file:line`) | Checagem |
| --- | --- | --- |
| CEP-01 | `app/templates/atualizar.html:71-81` (input `hidden` + `button` + status); `app/static/js/atualizar.js:377-419` (`CAMPOS_PASTA`, wiring de clique) | Controle clicável real por pasta, sem depender de `.br-upload`/`initInstanceUpload()` (confirmado ausente na marcação: `tests/test_tela_atualizar_envio.py::test_o_bloco_de_envio_nao_usa_mais_a_classe_br_upload`). |
| CEP-02 | `app/static/js/atualizar.js:384-397` (`contarSelecao`/`renderizarSelecao`) | Nome da pasta (`webkitRelativePath`) + contagem de `.csv`/outros exibidos ao escolher; reescolha substitui (`test_reescolher_a_pasta_substitui_o_status_anterior`); troca de origem redesenha sem perder seleção (`test_trocar_para_envio_redesenha_o_status_das_pastas_ja_escolhidas`, `app/static/js/atualizar.js:429` via T7). |
| CEP-03 | `app/static/js/atualizar.js:362-421` (bloco inteiro do widget) | Nenhum `fetch`/`setTimeout`/classe de carregamento nesse trecho — conferido por leitura direta, não é uma asserção automatizável de "ausência", mas o sensor (mutante 2) confirma que a lógica de contagem é exercitada e correta sem rede. |
| CEP-04 | `app/sistec/colunas.py:89,102` (`encoding_errors="replace"` nos dois `pd.read_csv`) | Reproduzido de ponta a ponta nesta sessão com o arquivo real (`sistec_Campus Santa Rosa_sistec.csv`, byte `0x81` em `NO_MAE_ALUNO`): lê 17.626 linhas com sucesso, as 4 colunas mantidas inalteradas. Testes sintéticos equivalentes em `tests/test_colunas.py` (coluna descartada e coluna mantida). |
| CEP-05 | `app/sistec/colunas.py:92-95` (checagem de colunas obrigatórias, inalterada); `tests/test_colunas.py::test_ler_planilha_recusa_arquivo_estruturalmente_quebrado_apos_decodificacao_tolerante` | **Gap de precisão de spec, corrigido no próprio T2**: a AC original ("linha com número de campos diferente do cabeçalho") não se sustenta no pandas 2.3.0 com `usecols` (confirmado por reprodução independente nesta sessão — pandas tolera campo a mais/a menos silenciosamente, antes e depois de T2). Substituído por um defeito estrutural real (aspas desbalanceadas → `ParserError`) e por delimitador errado — ambos cobertos e recusados como hoje. |
| CEP-06 | `app/static/js/atualizar.js:429` (`escolherOrigem` chama `CAMPOS_PASTA.forEach(renderizarSelecao)`) | Status nunca fala "enviado" antes do clique real; distinto do texto de progresso do envio (`elStatusEnvio`, inalterado). |

**Gaps de precisão encontrados**: 1 (CEP-05, documentado acima — resolvido na própria implementação, com evidência e teste substituto, não uma promessa não cumprida).

---

## Discrimination sensor

Executado em worktree isolado (`git worktree add`/`remove`, `git status --porcelain` conferido idêntico ao estado pré-sensor). Três mutações comportamentais, uma por vez:

| # | Mutação | Local | Resultado |
| - | ------- | ----- | --------- |
| 1 | Desliga a decodificação tolerante na leitura de conteúdo: `encoding_errors="replace"` → `"strict"` | `app/sistec/colunas.py:102` | **Morto** — 3 falhas em `tests/test_colunas.py` |
| 2 | Inverte a checagem de extensão `.csv`: `if (/\.csv$/i.test(...))` → `if (!/\.csv$/i.test(...))` | `app/static/js/atualizar.js:387` | **Morto** — 5 falhas em `tests/test_js_envio.py` |
| 3 | Desativa o ramo "nenhum arquivo escolhido": `if (arquivos.length === 0)` → `if (false)` | `app/static/js/atualizar.js:395` | **Sobreviveu na 1ª rodada** — nenhum teste chamava `renderizarSelecao`/`escolherOrigem` com 0 arquivos. Corrigido: `tests/test_js_envio.py::test_trocar_para_envio_sem_nada_escolhido_mostra_o_texto_de_obrigatoriedade` (commit `c838393`), confirmado matando o mesmo mutante numa segunda rodada antes de fechar este relatório. |

3 de 3 mutantes mortos ao final (1 exigiu um teste novo). Loop de correção: 1 de 3 iterações permitidas.

---

## Gate final

- `python -m pytest tests/ -q` → **683 passed**, 2 warnings (pré-existentes, `FutureWarning` em `app/data/fatores.py`, fora do escopo desta feature).
- `python .claude/skills/tlc-spec-driven/scripts/validate_tasks.py correcoes-envio-pastas` → 0 erros, 3 avisos aceitos (T1/T3/T5 `Tests: none`, coerente com a matriz).
- Nenhum dado pessoal de estudante entrou no repositório: o arquivo real usado na reprodução (`sistec_Campus Santa Rosa_sistec.csv`) não foi versionado; os testes usam CSV sintético equivalente (`tests/test_colunas.py:_matricula_sintetica`).
- Working tree limpo após o sensor: `git status --porcelain` sem diferença de conteúdo além dos avisos de fim de linha do Git no Windows.

## Lições

Um gap de precisão de spec (CEP-05, AC baseada numa suposição sobre `pandas` que não se confirmou com `usecols`) e um mutante sobrevivente na 1ª rodada (cobertura de `renderizarSelecao` com seleção vazia) — ambos corrigidos nesta mesma rodada, dentro do escopo da própria implementação. Registrando como lição de projeto: ao escrever AC sobre comportamento de biblioteca externa (parsers, serializadores), verificar o comportamento real antes de travar a asserção, em vez de assumir o "modo estrito" documentado genericamente.
