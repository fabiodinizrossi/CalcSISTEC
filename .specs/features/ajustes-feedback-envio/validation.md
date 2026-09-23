# Ajustes de Feedback do Envio — Validation

**Spec**: `.specs/features/ajustes-feedback-envio/spec.md`
**Verdict**: **FAIL**
**Diff range**: `f54572d..9212d3c` — 4 commits da feature (`6e8f12c` AFE-01, `55828c9` AFE-02, `1be1957` AFE-03, `9212d3c` docs); `938d5bb` (housekeeping `.gitignore`/`AGENTS.md`) fica fora do escopo
**Author**: DeepSeek (sessão separada, sem contexto desta)
**Verifier**: Claude (Sonnet 5) — não escreveu nenhum arquivo do diff; cobertura rederivada do zero, evidência-ou-zero (author ≠ verifier)

**Arquivos tocados pelo diff** (conferido com `git diff --stat`, não presumido): `app/app.py`, `app/static/js/atualizar.js`, `app/templates/atualizar.html`, `tests/test_admin_envio.py`, `tests/test_admin_envio_polling.py`, `tests/test_js_envio.py`, `tests/test_tela_atualizar_envio.py`, o próprio `spec.md`. **`app/data/campi.py` NÃO foi tocado** — correto, a premissa da feature é reusar o `origem='manual'` que já existe lá.

---

## Spec-anchored outcome check

### P1.1 — Salvar sem o clique extra (AFE-01)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: nenhuma caixa amarela/checkbox na tela | `#envio-preservacao`, `#envio-preservacao-texto` e `#envio-confirmar-preservacao` não existem na marcação | `tests/test_tela_atualizar_envio.py:143-144` — `assert id_removido not in html` para os 3 ids; `tests/test_js_envio.py:356` — `assert resultado["antes"]["preservacao"] is False` (`!!doc.porId["envio-preservacao"]` no DOM real servido ao `node`) | ✅ PASS |
| AC2: Salvar grava de primeira, sem clique extra | 1 requisição a `/salvar`, corpo `{"confirmar_preservacao": true}`, status de sucesso | `tests/test_js_envio.py:330-359` — `assert resultado["chamadas"] == 1` (`:357`), `assert resultado["corpos"] == ['{"confirmar_preservacao":true}']` (`:358`), `assert "Salvo na versão interna" in resultado["status"]` (`:359`); `assert resultado["antes"]["bloqueado"] is False` (`:355`, botão nunca desabilitado) | ✅ PASS |
| AC3: parágrafo do card mantém "preservados", sem prometer confirmação | texto com "nada dele é apagado" e sem "confirmação" | `tests/test_tela_atualizar_envio.py:146-151` — regex sobre o parágrafo real + `assert "nada dele é apagado" in paragrafo.group(0)` e `assert "confirmação" not in paragrafo.group(0)`; marcação em `app/templates/atualizar.html:54-56` | ✅ PASS |
| AC4: portão do servidor intacto (`ConfirmacaoNecessaria`, `POST .../salvar`), satisfeito na 1ª chamada | sem o campo → 409 `{"erro": "confirmacao_necessaria", ...}`; com `true` → 200 e grava | `tests/test_admin_envio_salvar.py:77-85` — `assert resposta.status_code == 409` + `assert resposta.get_json() == {"erro": "confirmacao_necessaria", "campi_preservados": ["U2"]}` + `assert GRAVACOES == []`; `:88-99` — `assert resposta.status_code == 200` e `assert execucao.estado == "salva"`. Código do servidor **fora do diff**: `app/app.py:504-518` e `app/sistec/execucoes.py:311` só foram tocados antes do range (`993e331`) | ✅ PASS |

### P1.2 — Resultado por arquivo em largura inteira (AFE-02)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: tabela por arquivo, linha de ignorados e avisos fora da coluna do card | `#envio-arquivos-area` e `#envio-avisos` são irmãos do container flex dos dois cards, não filhos de `#bloco-envio` | `tests/test_tela_atualizar_envio.py:104-125` — recorta `cards = html[inicio_cards:inicio_resultado]` e `largura_inteira = html[inicio_resultado:inicio_progresso]`; `assert 'id="envio-arquivos-area"' not in cards` (`:120`), `assert 'id="envio-avisos"' not in cards` (`:121`), `assert 'id="envio-arquivos-area"' in largura_inteira` (`:122`). Marcação: `app/templates/atualizar.html:79` fecha o flex de `:12` antes de `:81` | ✅ PASS |
| AC2: em viewport ≥ 992px o bloco continua ocupando a largura inteira abaixo dos dois cards | bloco fora do `flex-lg-row`, portanto sem restrição de coluna em nenhum breakpoint | `tests/test_tela_atualizar_envio.py:108-123` — **proxy estrutural**, não verificação de renderização: a asserção prova a causa (bloco fora do container `d-flex flex-column flex-lg-row`), não a largura medida | ⚠️ Spec-precision gap |
| AC3: os dois cards mantêm texto, botões e seletores de pasta | `#bloco-sistec`/`#bloco-envio` seguem com `#envio-ciclos`, `#envio-matriculas`, `#btn-enviar-pastas`, `#status-envio` | `tests/test_tela_atualizar_envio.py:114-117` — `assert 'id="envio-ciclos"' in cards and 'id="envio-matriculas"' in cards`, `assert 'id="btn-enviar-pastas"' in cards and 'id="status-envio"' in cards`; testes de CEP-01/CEP-02 (`:61-92`) seguem verdes na mesma marcação | ✅ PASS |

### P1.3 — Cadastro automático da unidade do envio (AFE-03)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: `co_unidade` ausente de `campi_sistec` vira linha nova via `incluir_campus`, antes de responder | linha em `campi_sistec`; resposta com `campi_cadastrados_automaticamente == ["U9"]` | `tests/test_admin_envio.py:335-356` — `assert corpo["campi_cadastrados_automaticamente"] == ["U9"]` (`:345`), `assert "U9" in cadastrados` (`:349`), `assert unidade["id_perfil"] == "envio-U9"` (`:351`), `assert unidade["nome_perfil"] == "Unidade U9 (cadastrada pelo envio de pastas)"` (`:352`), `assert unidade["origem"] == "manual"` (`:353`). Código: `app/app.py:426-430` (chamada antes de montar `resposta[...]` em `:433`) | ✅ PASS |
| AC2: resposta sem mensagem "fora do cadastro"/"não atualizada" | campo `campi_nao_cadastrados` inexistente na resposta; nenhum aviso com esse texto | `tests/test_admin_envio.py:346` — `assert "campi_nao_cadastrados" not in corpo`; `tests/test_js_envio.py:325-326` — `assert resultado["avisos"] == []` e `assert "fora do cadastro" not in resultado["texto"]`; linha neutra afirmada por valor em `:323` — `assert resultado["cadastrados"] == "1 unidade(s) nova(s) cadastrada(s) automaticamente: U9."` | ✅ PASS |
| AC3: se `incluir_campus` falhar (`CampusInvalido`), o envio segue para o resto | requisição não falha; só a unidade problemática fica de fora | **nenhum `file:line`** — não existe teste que force a colisão. `tests/test_admin_envio.py` não menciona `CampusInvalido` (grep em `tests/` só encontra ocorrências em `test_campi*.py` e `test_downloads.py`, todas da feature de campi). Mutante 5 do sensor confirma: removi o `try/except` de `app/app.py:353-364` e **os 57 testes das áreas afetadas continuaram passando** | ❌ GAP |
| AC4: unidade aparece em `/admin/campi` e conta nos totais de Configurações | linha servida por `listar_campi` | `tests/test_admin_envio.py:348-349` — `assert "U9" in cadastrados` sobre `dados_campi.listar_campi(banco_temporario)`. Fonte compartilhada conferida: `app/admin_campi.py:82` (`listar_campi(DB_PATH)`) e `app/templates/configuracoes.html:69` (`{{ campi|length }}`) usam a mesma função. **Nenhuma asserção no render das duas páginas**, e `admin_campi.DB_PATH` é constante própria — não exercitada pelo `monkeypatch` de `app_module.DEFAULT_DB_PATH` | ⚠️ Parcial (dado sim, tela não) |
| AC5: sobrevive a uma recaptura de perfis (`atualizar_lista`/`salvar_captura` não apaga `origem == "manual"`) | linha continua após `salvar_captura` | `tests/test_admin_envio.py:377-391` — cadastro pelo envio e depois `dados_campi.salvar_captura([{"id_perfil": "8278860", ...}], banco_temporario)`; `assert "U9" in {c["co_unidade"] for c in dados_campi.listar_campi(banco_temporario)}` (`:391`). Mecanismo: `app/data/campi.py:199-221` (`incluir_campus` grava `'manual'` no SQL de `:209`) e `app/data/campi.py:112-116` (só entra em `removidos` quem tem `origem != "manual"`). Mutantes 2 e 3 do sensor morrem exatamente aqui | ✅ PASS |

**Status**: ❌ Gaps presentes — 1 AC sem evidência (AFE-03 AC3), 2 coberturas parciais/spec-precision (AFE-02 AC2, AFE-03 AC4).

---

## Discrimination sensor

Worktree isolado (`git worktree add ../calsistec-sensor 9212d3c`; descartado com `git worktree remove --force`). Nenhuma mutação na árvore real. Nota de ambiente: o worktree nasce sem `.env` e sem `app/data/sistec.db` (ambos ignorados pelo Git), e sem eles a suíte afetada dá 18 falsas falhas (302 para `/admin/login` em `_exigir_instalacao`, `app/app.py:222-237`); com os dois arquivos copiados, a baseline do worktree ficou **57 passed** nos 5 arquivos da área, igual à árvore real.

| # | Mutação | Local | Resultado |
| - | ------- | ----- | --------- |
| 1 | `confirmar_preservacao: true` → `false` no corpo do Salvar (AFE-01) | `app/static/js/atualizar.js:296` | **Morto** — 2 falhas: `test_envio_com_campi_preservados_salva_de_primeira_sem_clique_extra`, `test_numa_baixa_o_salvar_tambem_manda_a_confirmacao` |
| 2 | Remove o efeito obrigatório: `campi.incluir_campus(...)` → `pass` (AFE-03 AC1) | `app/app.py:354-360` | **Morto** — 2 falhas: `test_unidade_fora_do_cadastro_e_cadastrada_automaticamente`, `test_unidade_cadastrada_pelo_envio_sobrevive_a_uma_leitura_do_sistec` |
| 3 | `origem` gravado deixa de ser `'manual'`: `'manual'` → `'envio'` no INSERT | `app/data/campi.py:209` | **Morto** — 5 falhas, incluindo `test_unidade_fora_do_cadastro_e_cadastrada_automaticamente` (`assert 'envio' == 'manual'`) e a de sobrevivência à recaptura |
| 4 | Reintroduz a caixa amarela na marcação (`<div id="envio-preservacao" class="br-message warning" hidden>`) | `app/templates/atualizar.html` antes de `#status-envio` | **Morto** — 1 falha: `test_card_de_envio_nao_pede_confirmacao_de_preservacao` |
| 5 | Remove a guarda de `CampusInvalido` (chamada nua, sem `try/except`) — AFE-03 AC3 | `app/app.py:354-362` | **Sobreviveu** — 57 passed, 0 falhas. Confirma o GAP do AC3: a suíte não distingue a guarda presente da ausente |

4 de 5 mutações mortas. **Resultado do sensor: ❌ FAIL pelo mutante 5 sobrevivente.**

Isolamento conferido: `git status --porcelain` da árvore real antes e depois do sensor = `?? .agents/` + `?? nonascii.txt`, idêntico; `HEAD` segue `9212d3c`.

---

## Edge cases da spec

- [x] Mesmo `co_unidade` em dois envios não recadastra — `tests/test_admin_envio.py:359-374` (`assert resultado... == []` e `assert dados_campi.listar_campi(banco_temporario) == []`). Ressalva: o segundo envio é simulado por `monkeypatch` de `listar_campi` (`:364-368`) em vez de um segundo POST real sobre o banco temporário — cobre o ramo, não o ciclo completo.
- [x] Envio sem preservados e sem não cadastrados não renderiza nada — comportamento inalterado coberto por `tests/test_admin_envio.py:135-150` (CAMPI = U1..U3, envio de U1..U3) e `tests/test_admin_envio_polling.py:67` (`assert corpo["campi_cadastrados_automaticamente"] == []`).
- [x] `falhou_consolidacao` não roda resultado/avisos/cadastro — `app/app.py:417-423` retorna antes do bloco de cadastro; `tests/test_admin_envio.py:201-216` (`assert corpo["estado"] == "falhou_consolidacao"`, `assert HISTORICO[0]["desfecho"] == "falhou_consolidacao"`).

---

## Gate final

- `python -m pytest tests/ -q` (a partir da raiz) → **683 passed**, 2 warnings (`FutureWarning` pré-existente em `app/data/fatores.py:198-199`, fora do escopo), 0 failed, 0 skipped.
- Baseline pré-feature (`f54572d`, worktree isolado, `--collect-only`) → **680 tests collected**. Delta **+3** (7 removidos, 10 adicionados). As 5 remoções são a caixa de confirmação e seus testes de comportamento superado (3 em `test_js_envio.py`, 2 em `test_tela_atualizar_envio.py`), justificadas pelo Assumption de AFE-01 — nenhuma asserção foi enfraquecida sem substituição; as novas asserções são mais específicas que as antigas (valor do corpo JSON, `origem`, `id_perfil`, sobrevivência à recaptura).

---

## Code quality

| Princípio | Status |
| --- | --- |
| Código mínimo, sem abstração de uso único | ✅ (`_cadastrar_unidades_do_envio` tem um chamador só e função única) |
| Mudanças cirúrgicas, sem "melhorar" código alheio | ✅ (nenhum refactor fora dos 3 pedidos; `campi.py` intocado) |
| Sem scope creep | ✅ (o servidor de confirmação continua existindo, como decidido) |
| Segue os padrões do repositório | ✅ (comentários em PT explicando o porquê, nomes dos campos no padrão do projeto) |
| Spec-anchored outcome check | ❌ 1 AC sem asserção (AFE-03 AC3) |
| Toda AC com evidência `file:line` | ❌ 11 de 12 (AFE-02 AC2 e AFE-03 AC4 são proxies) |
| Nenhum teste órfão | ✅ (os testes novos mapeiam para AFE-01/02/03 ou para o edge case de recadastro) |
| Diretrizes documentadas seguidas | ✅ `AGENTS.md` (sem teste que dependa do Sistec real; dublês para banco/histórico) |

---

## Gaps ranqueados

1. **[Major] AFE-03 AC3 sem nenhuma cobertura.** `app/app.py:361` engole `CampusInvalido` para não derrubar o envio, mas nenhum teste força a colisão. Mutante 5 (guarda removida) sobreviveu a 57 testes. Correção sugerida: teste que pré-cadastre um campus com `id_perfil="envio-U9"` e `co_unidade` diferente (ou `co_unidade` já ocupado por outra linha) e afirme que o POST de envio responde 200/`previa`, que o restante das unidades é processado e que `campi_cadastrados_automaticamente` exclui `"U9"`.
2. **[Major] AFE-02 AC2 verificado só por proxy estrutural.** `tests/test_tela_atualizar_envio.py:108-123` prova que o bloco está fora do container flex, não que ele ocupa a largura inteira em ≥ 992px. Não há CSS/@media em `app/static/css` nem teste de viewport. Correção sugerida: anotar na spec que a garantia é estrutural (container do DS é full-width) e que a confirmação visual fica na UAT, ou cobrir com teste de largura.
3. **[Minor] AFE-03 AC4 sem asserção no render de `/admin/campi` e de Configurações.** A evidência é `listar_campi` direto no banco temporário (`tests/test_admin_envio.py:348`), e `app/admin_campi.py:82` lê `DB_PATH` próprio — uma divergência entre `DEFAULT_DB_PATH` e `DB_PATH` não seria pega. Correção sugerida: um GET em `/admin/campi` no mesmo teste, afirmando `U9` na lista e no contador de Configurações.
4. **[Minor] Divergência spec × implementação no `origem`.** O Assumption de AFE-03 (`spec.md:30`) diz que a chamada passa `origem="manual"`; `campi.incluir_campus` não tem esse parâmetro (`app/data/campi.py:199`) e grava `'manual'` no próprio SQL (`:209`), então `app/app.py:355-360` passa só `id_perfil`/`nome_perfil`/`co_unidade`/`db_path`. O comportamento exigido pelo AC5 está correto e comprovado (mutante 3 morto); o texto da spec é que descreve uma chamada que não existe. Ajustar a redação do Assumption.
5. **[Minor] Edge case "mesmo `co_unidade` em dois envios" cobre o ramo, não o ciclo.** `tests/test_admin_envio.py:359-374` injeta a unidade já cadastrada via `monkeypatch` de `listar_campi`, em vez de um segundo POST real contra o banco temporário.

---

## Inconsistência documental (não bloqueia o código, bloqueia o fechamento)

`spec.md:125` — o último item de **Success Criteria** (`pytest tests/ -q` verde) já está marcado `[x]` desde `9212d3c`, junto com os outros quatro. Como esta verificação é FAIL, o checklist está à frente da evidência; ele não foi alterado aqui (o Verifier não corrige nem marca Success Criteria em FAIL).

---

## Lições

Dois sinais reais nesta rodada: (a) um `try/except` de resiliência entrou sem teste que force a exceção — o mutante 5 sobreviveu intacto, porque o caminho de erro foi escrito mas nunca exercitado; (b) o Assumption da spec descreve uma assinatura de chamada (`origem="manual"`) que a função real não tem, e a divergência passou pelas três rodadas de implementação sem ser notada porque o valor final batia. Registrando como lição de projeto: AC sobre caminho de erro (colisão, exceção, timeout) precisa de um teste que **provoque** o erro, não de um `try/except` visível na leitura; e assinatura de chamada citada em spec deve ser conferida contra o `def` real antes de virar Assumption.

---

## Veredito

**FAIL.** O comportamento entregue bate com o que a spec pede nos três requisitos — o gate fecha em 683 passed e 4 das 5 mutações morrem, incluindo as duas que provariam a preservação dos campi e o cadastro automático. O que reprova é cobertura: o AC de resiliência do cadastro automático (AFE-03 AC3) não tem teste nenhum, e um mutante que apaga a guarda sobrevive a toda a suíte. Dois critérios (AFE-02 AC2, AFE-03 AC4) estão cobertos por proxy, não pelo resultado que a spec descreve.

**Next step**: um teste que force `CampusInvalido` no cadastro automático (gap 1) e, se quiser fechar os proxies, uma asserção no render de `/admin/campi` (gap 3); a re-verificação roda depois disso.
