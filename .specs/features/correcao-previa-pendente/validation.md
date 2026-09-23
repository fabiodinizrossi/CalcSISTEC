# Correção de prévia pendente sem saída — validação

**Data:** 2026-09-23  
**Spec:** `.specs/features/correcao-previa-pendente/spec.md`  
**Diff:** alterações locais de `app/app.py`, `app/static/js/atualizar.js`, `tests/test_admin_envio_polling.py`, `tests/test_js_envio.py` e `tests/test_admin_envio.py` contra `HEAD`  
**Verifier:** agente independente do implementador

## Veredito

**PASS no escopo da correção:** 4/4 critérios de aceitação e o caso de amostra vazia têm evidência. Os 44 testes afetados passaram. O sensor de discriminação matou a mutação da condição que originalmente escondia as ações. A suíte completa informada pelo implementador ficou em **686 passed, 2 failed** por `dataset_disponivel()` falso em testes isolados de layout público, fora do fluxo alterado; portanto, o gate global do projeto ainda não está verde.

## Critérios de aceitação

| Critério | Resultado esperado | Evidência | Resultado |
| --- | --- | --- | --- |
| CPP-01: amostra com ausentes ou não finitos | JSON estrito válido, valores `null`, estado, ID e contagens preservados | `app/app.py:576-582` converte `NaN`, `inf`, `-inf` e `pd.NA` antes de `jsonify`; `tests/test_admin_envio_polling.py:92-104` usa `json.loads(..., parse_constant=...)` e compara `estado`, `execucao_id`, contagens e amostra com `None`. | PASS |
| CPP-02: prévia com resumo | Salvar e Descartar visíveis | `app/static/js/atualizar.js:182-188` mostra a área da prévia e Salvar quando há resumo; `app/templates/atualizar.html:112-129` contém Descartar na mesma área; `tests/test_js_envio.py:279-288` afirma os três estados visíveis para um resumo válido. | PASS |
| CPP-03: prévia sem resumo | Descartar visível e acionável | `app/static/js/atualizar.js:186-192` mantém a área visível, oculta apenas Salvar e mostra orientação; `tests/test_js_envio.py:252-276` afirma visibilidade, mensagem e chamada de `/descartar` após clique. | PASS |
| CPP-04: descartar e reenviar | Descarte encerra pendência e nova atualização entra em prévia | `app/app.py:537-548` chama `execucoes.descartar`; `tests/test_admin_envio.py:240-257` comprova bloqueio 409 anterior, descarte 204 e novo envio 200 em `previa`. | PASS |
| Borda: amostra vazia | Salvar e Descartar disponíveis | `app/static/js/atualizar.js:200-204` só interrompe a montagem da tabela; `tests/test_js_envio.py:279-288` usa `amostra: []` e afirma ambos os botões visíveis. | PASS |

Os testes comparam os resultados prescritos pela spec. A rota de polling é coberta com parser JSON estrito, necessário para distinguir `NaN` do `null` exigido. O teste de interface executa o script real em DOM simulado, e o de descarte usa as rotas reais.

## Sensor de discriminação

| Mutação em cópia temporária fora do repositório | Teste | Resultado |
| --- | --- | --- |
| `app/static/js/atualizar.js:182`: restaurar `if (!previa || estado !== "previa")`, escondendo toda a prévia quando o resumo é nulo | `test_previa_pendente_sem_resumo_ainda_permite_descartar` | **Morta:** falha em `tests/test_js_envio.py:273`, `previaVisivel` é `false` quando deveria ser `true`. |

Sensor leve: 1 mutação, 1 morta. A execução ocorreu em `TemporaryDirectory` com cópias de JS, teste e `dom_falso.py`; o diretório foi removido. `git status --porcelain -uno` permaneceu idêntico antes e depois.

## Gate e qualidade

- Gate independente: `.uv-python/cpython-3.12.14-windows-x86_64-none/python.exe -m pytest tests/test_admin_envio_polling.py tests/test_js_envio.py tests/test_admin_envio.py -q -p no:cacheprovider --basetemp <diretório temporário> --tb=short` → **44 passed**.
- Três testes foram adicionados e um teste de rota foi ampliado. Nenhuma asserção existente foi enfraquecida no diff.
- As alterações de produção ficam na serialização da amostra e na renderização da prévia; não mudam consolidação nem publicação. Ações administrativas continuam autenticadas e o descarte usa a rota já existente.
- Regras conferidas: `.specs/PROJECT_RULES.md` (Princípios III, IV e VII). A verificação visual em navegador real não foi executada; o fluxo de interface foi exercitado pelo teste Node com DOM simulado.

**Pendência externa ao escopo:** investigar as duas falhas de layout público antes de considerar satisfeito o gate de suíte completa exigido pelo projeto. Não há gap identificado nesta correção.

## Nota de fechamento (Claude, Sonnet 5, revisão independente do commit)

Confirmado com `git stash` (árvore sem este diff) que as 2 falhas de
`tests/test_paginas_publicas.py` (`test_eficiencia_layout_...`,
`test_percentuais_layout_...`, ambas `assert layout.className ==
"painel-dashboard"` recebendo `"br-message info"`) já existem no `HEAD`
anterior a esta correção — não são causadas por este diff. `pytest tests/ -q`
completo, de novo com o diff aplicado: 686 passed, 2 failed (os mesmos
dois). Gate do escopo desta correção (`test_admin_envio_polling.py`,
`test_js_envio.py`, `test_admin_envio.py`) confirmado independente: 44
passed. Commit liberado; as 2 falhas pré-existentes ficam para investigação
separada, fora desta feature.
