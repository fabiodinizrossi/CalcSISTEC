# Ajustes de Feedback do Envio — Validation (rodada 2)

**Spec**: `.specs/features/ajustes-feedback-envio/spec.md`
**Verdict**: **PASS**
**Result**: PASS (12/12 ACs com evidência, 5/5 mutações mortas, 685 passed)
**Rodada anterior**: FAIL, commit `05c3f40` (5 gaps ranqueados, 1 mutante sobrevivente). A rodada de correção (`2e5ab82`, `14bfc97`, `db74bea`) fechou os 5 — tabela de fechamento abaixo. Este relatório substitui o anterior; o histórico fica no `git log` desta feature.
**Diff desta rodada**: `05c3f40..db74bea` (3 commits, só `tests/test_admin_envio.py` e `spec.md` — nenhum arquivo de aplicação mudou)
**Diff total da feature**: `f54572d..db74bea` (`6e8f12c`, `55828c9`, `1be1957`, `9212d3c`, `05c3f40`, `2e5ab82`, `14bfc97`, `db74bea`); `938d5bb` (housekeeping) fora do escopo
**Author**: DeepSeek (implementação + rodada de correção)
**Verifier**: Claude (Sonnet 5), sessão nova, sem memória da rodada 1 — cobertura rederivada do zero, evidência-ou-zero (author ≠ verifier, incluindo contra a correção)

---

## Fechamento dos 5 gaps da rodada 1

| # | Gap (rodada 1) | Fechado? | Evidência |
| - | -------------- | -------- | --------- |
| 1 | **[Major]** AFE-03 AC3 sem teste: guarda de `CampusInvalido` sobrevivia à suíte | ✅ | `tests/test_admin_envio.py:360-385` — pré-cadastra `envio-U9` (`:367`), envia U9 **e** U8, e afirma por valor: `assert resposta.status_code == 200` (`:377`), `assert corpo["estado"] == "previa"` (`:378`), `assert corpo["campi_cadastrados_automaticamente"] == ["U8"]` (`:379`), `assert cadastrados["U8"]["id_perfil"] == "envio-U8"` (`:382`), `assert cadastrados["U7"]["id_perfil"] == "envio-U9"` (`:384`, linha colidida intacta), `assert "U9" not in cadastrados` (`:385`). Mutante 5 do sensor (guarda removida) **agora morre**: `assert 500 == 200` |
| 2 | **[Major]** AFE-02 AC2 verificada só por proxy, sem dizer isso | ✅ | `spec.md:67` — nota "Como esta AC é garantida — e como ela é verificada" declara a garantia **estrutural** (nenhum container de coluna envolve o bloco; o teste é o recorte estrutural; largura renderizada é conferência visual, fora do alcance do `test_client`). Confirmei a substância contra `app/assets/style.css`: as ocorrências de `max-width` no arquivo são `.container-fluid` em `@media (min-width:1600px)` (`:68-71`), `.br-menu .menu-panel{max-width:none}` (`:121-123`), `pre` (`:298-299`) e `.br-button` (`:302-303`) — nenhuma limita o bloco de resultado. **Nenhum teste de viewport/CSS computado foi inventado**: o diff desta rodada toca só `tests/test_admin_envio.py` e `spec.md`, e `tests/test_tela_atualizar_envio.py:104-125` segue sendo o recorte estrutural de antes |
| 3 | **[Minor]** AFE-03 AC4 sem asserção no render das páginas | ✅ | `tests/test_admin_envio.py:388-414` — aponta `admin_campi.DB_PATH` e o `listar_campi` do `app.py` para o banco temporário (`:400-401`), faz o envio de U9 (`:406`) e bate nas duas páginas: `assert "Unidade U9 (cadastrada pelo envio de pastas)" in pagina_campi` (`:409`), `assert re.search(r"<td>\s*U9\s*</td>", pagina_campi)` (`:410`), `assert "1 campi cadastrados, 1 ativos." in config` (`:413`), `assert "1 campus com identificador inválido" in config` (`:414`). As strings de Configurações vêm de `app/templates/configuracoes.html:69` e `:71` |
| 4 | **[Minor]** Assumption citava `origem="manual"`, parâmetro que `incluir_campus` não tem | ✅ | `spec.md:30` agora diz `incluir_campus(id_perfil=..., nome_perfil=..., co_unidade=..., db_path=...)` e explica que **não tem parâmetro `origem`** — grava `'manual'` no próprio INSERT (`app/data/campi.py:209`). Confere com a assinatura real (`app/data/campi.py:199`) e com a chamada (`app/app.py:355-360`) |
| 5 | **[Minor]** Edge case de recadastro testado por `monkeypatch` de retorno fixo | ✅ | `tests/test_admin_envio.py:417-440` — dois POSTs reais contra o mesmo banco temporário, com `descartar` entre eles (`:436`) para liberar a prévia pendente; `assert primeiro["campi_cadastrados_automaticamente"] == ["U9"]` (`:434`), `assert segundo["campi_cadastrados_automaticamente"] == []` (`:439`), `assert [c["co_unidade"] for c in dados_campi.listar_campi(banco_temporario)] == ["U9"]` (`:440`, sem duplicata). O `listar_campi` continua monkeypatched (`:423`), mas agora delegando ao banco real — não é mais uma lista fixa |

**Nenhum gap novo de cobertura.** Uma imprecisão documental menor foi encontrada na nota nova da AC2 e está registrada abaixo, sem bloquear.

---

## Spec-anchored outcome check

### P1.1 — Salvar sem o clique extra (AFE-01)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: nenhuma caixa amarela/checkbox na tela | os 3 ids não existem na marcação | `tests/test_tela_atualizar_envio.py:143-144` — `assert id_removido not in html` para `envio-preservacao`, `envio-preservacao-texto`, `envio-confirmar-preservacao`; `tests/test_js_envio.py:356` — `assert resultado["antes"]["preservacao"] is False` (checado no DOM real servido ao `node`) | ✅ PASS |
| AC2: Salvar grava de primeira, sem clique extra | 1 requisição, corpo `{"confirmar_preservacao": true}`, status de sucesso | `tests/test_js_envio.py:330-360` — `assert resultado["antes"]["bloqueado"] is False` (`:355`), `assert resultado["chamadas"] == 1` (`:357`), `assert resultado["corpos"] == ['{"confirmar_preservacao":true}']` (`:358`), `assert resultado["cabecalhos"]["Content-Type"] == "application/json"` (`:359`), `assert "Salvo na versão interna" in resultado["status"]` (`:360`); mesmo campo na baixa (`:384-387`) | ✅ PASS |
| AC3: parágrafo mantém "preservados", sem prometer confirmação | texto com "nada dele é apagado" e sem "confirmação" | `tests/test_tela_atualizar_envio.py:146-151` — regex sobre o HTML real + `assert "nada dele é apagado" in paragrafo.group(0)` (`:150`) e `assert "confirmação" not in paragrafo.group(0)` (`:151`); marcação em `app/templates/atualizar.html:54-56` | ✅ PASS |
| AC4: portão do servidor intacto e satisfeito na 1ª chamada | sem o campo → 409 `confirmacao_necessaria`; com `true` → 200 e grava | `tests/test_admin_envio_salvar.py:82-84` — `assert resposta.status_code == 409`, `assert resposta.get_json() == {"erro": "confirmacao_necessaria", "campi_preservados": ["U2"]}`, `assert GRAVACOES == []`; `:95-96` — `assert resposta.status_code == 200` + `assert GRAVACOES == [...]`. Servidor fora do diff da feature: `app/app.py:504-518`, `app/sistec/execucoes.py:311`, último toque em `993e331` | ✅ PASS |

### P1.2 — Resultado por arquivo em largura inteira (AFE-02)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: tabela, ignorados e avisos fora da coluna do card | bloco irmão do container dos dois cards, não filho de `#bloco-envio` | `tests/test_tela_atualizar_envio.py:104-125` — `assert 'id="envio-arquivos-area"' not in cards` (`:120`), `assert 'id="envio-avisos"' not in cards` (`:121`), `assert 'id="envio-arquivos-area"' in largura_inteira` (`:122`), `assert 'id="envio-avisos"' in largura_inteira` (`:123`); marcação: `app/templates/atualizar.html:79` fecha o flex aberto em `:12`, e `:81`/`:96` ficam fora | ✅ PASS |
| AC2: em ≥992px o bloco segue em largura inteira abaixo dos dois cards | garantia estrutural (declarada), verificada pelo recorte do DOM | `spec.md:67` (nota) + `tests/test_tela_atualizar_envio.py:108-123`. Confirmei por leitura do CSS que nenhuma regra de `app/assets/style.css` limita a largura do bloco (ver Gap 2 acima) — a verificação por pixel é conferência visual, como a spec agora diz | ✅ PASS |
| AC3: os dois cards mantêm texto, botões e seletores | `#bloco-sistec`/`#bloco-envio` seguem com os controles | `tests/test_tela_atualizar_envio.py:114-117` — `assert 'id="envio-ciclos"' in cards and 'id="envio-matriculas"' in cards`, `assert 'id="btn-enviar-pastas"' in cards and 'id="status-envio"' in cards`; testes de CEP-01/CEP-02 (`:61-92`) verdes na mesma marcação | ✅ PASS |

### P1.3 — Cadastro automático da unidade do envio (AFE-03)

| AC | Resultado definido pela spec | Evidência (`file:line` + asserção) | Resultado |
| --- | --- | --- | --- |
| AC1: `co_unidade` ausente vira linha nova via `incluir_campus`, antes de responder | linha em `campi_sistec` + `campi_cadastrados_automaticamente == ["U9"]` | `tests/test_admin_envio.py:336-357` — `assert corpo["campi_cadastrados_automaticamente"] == ["U9"]` (`:346`), `assert "U9" in cadastrados` (`:349`), `assert unidade["id_perfil"] == "envio-U9"` (`:351`), `assert unidade["nome_perfil"] == "Unidade U9 (cadastrada pelo envio de pastas)"` (`:352`), `assert unidade["origem"] == "manual"` (`:353`), `assert dados_campi.id_suspeito(unidade["id_perfil"]) is True` (`:357`). Código: `app/app.py:426-428` roda antes da resposta montada em `:432-433` | ✅ PASS |
| AC2: sem mensagem "fora do cadastro"/"não atualizada" | campo ausente na resposta, nenhum aviso com esse texto | `tests/test_admin_envio.py:346` — `assert "campi_nao_cadastrados" not in corpo`; `tests/test_js_envio.py:323` — `assert resultado["cadastrados"] == "1 unidade(s) nova(s) cadastrada(s) automaticamente: U9."` (linha neutra por valor), `:325` — `assert resultado["avisos"] == []`, `:326` — `assert "fora do cadastro" not in resultado["texto"]` | ✅ PASS |
| AC3: se `incluir_campus` falhar, o envio segue | requisição não falha; só a unidade colidida fica de fora | `tests/test_admin_envio.py:360-385` (ver Gap 1 acima). Mutante 5 do sensor morre aqui — era o gap da rodada 1 | ✅ PASS |
| AC4: unidade aparece em `/admin/campi` e conta nos totais de Configurações | nome na lista renderizada, contadores refletindo a linha nova | `tests/test_admin_envio.py:388-414` (ver Gap 3 acima); páginas: `app/admin_campi.py:82`, `app/templates/configuracoes.html:69,71` | ✅ PASS |
| AC5: sobrevive a uma recaptura de perfis | linha continua depois de `salvar_captura` | `tests/test_admin_envio.py:443-457` — `assert "U9" in {c["co_unidade"] for c in dados_campi.listar_campi(banco_temporario)}` (`:457`) depois de `dados_campi.salvar_captura([...], banco_temporario)` (`:452-455`). Mecanismo: `app/data/campi.py:199-221` (INSERT grava `'manual'` em `:209`) e `app/data/campi.py:112-116` (só entra em `removidos` quem tem `origem != "manual"`) | ✅ PASS |

**Status**: ✅ 12 de 12 ACs com evidência `file:line` e valor afirmado batendo com o resultado definido na spec. Nenhum spec-precision gap bloqueante; 1 imprecisão documental menor em `spec.md:67` (abaixo).

---

## Discrimination sensor

Worktree isolado (`git worktree add ../calsistec-sensor2 db74bea`; `git worktree remove --force` ao fim). `.env` e `app/data/sistec.db` (ambos ignorados pelo Git) copiados para o worktree — sem eles a suíte dá falsas falhas em 302 para `/admin/login` (`_exigir_instalacao`, `app/app.py:222-237`). Baseline do worktree nos 5 arquivos da área: **59 passed**. Cinco mutações comportamentais, uma por vez:

| # | Mutação | Local | Resultado |
| - | ------- | ----- | --------- |
| 1 | `confirmar_preservacao: true` → `false` no corpo do Salvar (AFE-01) | `app/static/js/atualizar.js:296` | **Morto** — 2 falhas: `test_envio_com_campi_preservados_salva_de_primeira_sem_clique_extra`, `test_numa_baixa_o_salvar_tambem_manda_a_confirmacao` |
| 2 | Remove o efeito obrigatório: `campi.incluir_campus(...)` → `pass` (AFE-03 AC1) | `app/app.py:354-360` | **Morto** — 5 falhas, incluindo `assert ['U9', 'U8'] == ['U8']` no teste de colisão e a ausência do nome na página `/admin/campi` |
| 3 | `origem` gravado deixa de ser `'manual'`: `'manual'` → `'envio'` no INSERT (AFE-03 AC5) | `app/data/campi.py:209` | **Morto** — 5 falhas (2 em `test_admin_envio.py`, 3 em `test_campi*.py`), incluindo `test_unidade_cadastrada_pelo_envio_sobrevive_a_uma_leitura_do_sistec` |
| 4 | Reintroduz a caixa amarela (`<div id="envio-preservacao" class="br-message warning" hidden>`) | `app/templates/atualizar.html` antes de `#status-envio` | **Morto** — 1 falha: `test_card_de_envio_nao_pede_confirmacao_de_preservacao` (`tests/test_tela_atualizar_envio.py:144`) |
| 5 | Remove a guarda de `CampusInvalido` (chamada nua, sem `try/except`) — AFE-03 AC3 | `app/app.py:354-362` | **Morto** — 1 falha: `test_colisao_no_cadastro_automatico_nao_derruba_o_envio` (`assert 500 == 200`). **Sobrevivia na rodada 1**; o teste novo fecha o gap |

**Sensor depth**: lightweight (5 mutações, uma por AC de risco).
**Resultado**: 5/5 mortas — **PASS ✅** (rodada 1: 4/5).

Isolamento conferido: `git status --porcelain` da árvore real antes e depois do sensor = `?? .agents/` + `?? .specs/features/previa-paginas-publicas/` + `?? nonascii.txt`, idêntico; `HEAD` segue `db74bea`. Nenhum `git stash` usado.

---

## Edge cases da spec

- [x] Mesmo `co_unidade` em dois envios não recadastra — `tests/test_admin_envio.py:417-440`, dois POSTs reais e `assert ... == []` no segundo (`:439`), sem duplicata no banco (`:440`).
- [x] Envio sem preservados e sem não cadastrados não renderiza nada — `tests/test_admin_envio.py:136-150` (CAMPI = U1..U3, envio de U1..U3) e `tests/test_admin_envio_polling.py:67` (`assert corpo["campi_cadastrados_automaticamente"] == []`).
- [x] `falhou_consolidacao` não roda resultado/avisos/cadastro — `app/app.py:417-423` retorna antes do bloco de cadastro; `tests/test_admin_envio.py:202-218` (`assert corpo["estado"] == "falhou_consolidacao"`, `assert HISTORICO[0]["desfecho"] == "falhou_consolidacao"`, nada gravado).

---

## Gate final

- `python -m pytest tests/ -q` (a partir da raiz) → **685 passed**, 2 warnings (`FutureWarning` pré-existente em `app/data/fatores.py:198-199`, fora do escopo), 0 failed, 0 skipped.
- Baseline pré-feature (`f54572d`): **680 collected**. Rodada 1: 683 passed. Delta desta rodada: **+2** (`test_colisao_no_cadastro_automatico_nao_derruba_o_envio`, `test_unidade_cadastrada_pelo_envio_aparece_nas_paginas_de_cadastro`; `test_unidade_ja_cadastrada_nao_e_cadastrada_de_novo` foi reescrito no lugar, sem mudar a contagem).
- Testes removidos na feature (5, nas rodadas anteriores): todos da caixa de confirmação superada por AFE-01, com asserções substitutas mais específicas — nenhuma asserção enfraquecida, nenhum teste deletado nesta rodada.

---

## Code quality

| Princípio | Status |
| --- | --- |
| Código mínimo, sem abstração de uso único | ✅ (nenhum arquivo de aplicação tocado nesta rodada) |
| Mudanças cirúrgicas, sem "melhorar" código alheio | ✅ (correção só em testes + texto de spec) |
| Sem scope creep | ✅ |
| Segue os padrões do repositório | ✅ (dublês de banco/histórico, comentários explicando o porquê da fixture) |
| Spec-anchored outcome check | ✅ 12/12 ACs com valor afirmado |
| Toda AC com evidência `file:line` | ✅ 12/12 |
| Nenhum teste órfão | ✅ (os 3 testes novos mapeiam para AFE-03 AC1/AC3/AC4 e para o edge case) |
| Diretrizes documentadas seguidas | ✅ `AGENTS.md` (nada toca o Sistec real; PII fora dos testes) |

**Imprecisão documental menor (não bloqueia)**: `spec.md:67` lista `.br-message .content` entre as regras com `max-width` de `app/assets/style.css`, mas essa regra (`:294-297`) só tem `min-width: 0` e `overflow-wrap: anywhere`; as quatro ocorrências reais de `max-width` são `.container-fluid` (`:70`), `.br-menu .menu-panel` (`:123`), `pre` (`:299`) e `.br-button` (`:303`). A conclusão da nota (nenhuma regra limita o bloco de resultado) continua verdadeira — é erro de enumeração, não de garantia. Corrigir quando a spec for tocada de novo; não vale uma rodada própria.

---

## Lições

A rodada 1 deixou um mutante sobrevivente (`try/except CampusInvalido` sem teste que force a exceção) e dois critérios cobertos por proxy sem dizer que eram proxy. A correção fechou os três sem tocar em código de aplicação: o caminho de erro ganhou um teste que **provoca** a colisão de verdade (id `envio-U9` já ocupado, não um dublê), a AC de largura passou a declarar que a garantia é estrutural, e a página renderizada passou a ser afirmada em vez do banco. Duas lições de projeto ficam registradas: (1) `try/except` de resiliência é comportamento — sem teste que levante a exceção, ele não existe para a suíte; (2) quando a verificação de uma AC depende de coisa que o harness não alcança (layout renderizado), a spec deve dizer isso explicitamente e apontar a conferência visual, em vez de aceitar um teste de fachada.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 12/12 ACs com o valor afirmado batendo com o resultado definido na spec (1 imprecisão documental menor em `spec.md:67`)
**Sensor**: 5/5 mutações mortas (a que sobrevivia na rodada 1 agora morre)
**Gate**: 685 passed, 0 failed
**Gaps da rodada 1**: 5 de 5 fechados · **Gaps restantes**: nenhum bloqueante

**Next steps**: nenhuma correção pendente. A conferência visual da largura em ≥992px segue como passo humano (declarado em `spec.md:67`), fora do alcance do `test_client`.
