# Cards de Atualizar Dados — Validation

**Spec**: `.specs/features/cards-atualizar-dados/spec.md`
**Design/Tasks**: nenhum — escopo Medium, "Tasks fica implícito no Execute" (ver `spec.md:75`)
**Verdict**: **PASS**
**Commit**: `cc777b7`
**Author**: Claude (Sonnet 5)
**Verifier**: Codex (via `codex:codex-rescue`), 1ª rodada — apontou CAD-03 não conforme; Claude (Sonnet 5) corrigiu no mesmo diff e reexecutou o gate

---

## Spec-anchored outcome check

| Req | Evidência (`file:line`) | Checagem |
| --- | --- | --- |
| CAD-01 | `app/templates/atualizar.html:12-79` (sem `<fieldset id="atualizar-origem">`/rádio; os dois `div#bloco-sistec`/`div#bloco-envio` sempre presentes) | `tests/test_tela_atualizar_envio.py::test_tela_oferece_os_dois_caminhos_sempre_visiveis_em_cards` confirma ausência de `origem-sistec`/`origem-envio`/`atualizar-origem` e presença dos dois `<h2>` de card. |
| CAD-02 | `app/templates/atualizar.html:12` (`class="d-flex flex-column flex-lg-row"` envolvendo os dois cards) | `tests/test_tela_atualizar_envio.py::test_os_dois_cards_empilham_abaixo_de_992px_com_classes_do_ds` — mesmo padrão `flex-lg-row` já usado no resto da tela (AD-005), sem `@media`. |
| CAD-03 | `app/templates/atualizar.html:47-104` (`envio-arquivos-area`, `envio-preservacao`, `envio-avisos` dentro de `#bloco-envio`) | `tests/test_tela_atualizar_envio.py::test_resultados_do_envio_ficam_dentro_do_proprio_card` — **corrigido nesta rodada**: a 1ª implementação movia essas três áreas para uma `<section id="atualizar-resultados">` fora do card, junto com Progresso/Prévia (fora do escopo, `spec.md:18`). Reparentado de volta para dentro de `#bloco-envio`; Progresso/Prévia voltaram para fora dos dois cards, como estavam antes da feature. |
| CAD-04 | `app/assets/style.css:787-801` (`.card-atualizar`, só tokens `--background`/`--border-color`/`--surface-rounder-md`/`--surface-shadow-sm`/`--card-padding`, confirmados definidos em `app/static/govbr-ds/dist/core.min.css`) | `tests/test_tela_atualizar_envio.py::test_tela_oferece_os_dois_caminhos_sempre_visiveis_em_cards` confirma `"br-card" not in html`. |
| CAD-05 | `app/static/js/atualizar.js` (diff remove só `elOrigemSistec`/`elOrigemEnvio`/`escolherOrigem` e os dois listeners de `change`; nenhuma outra função tocada) | `tests/test_js_envio.py` (28 casos, incluindo os specíficos de envio/preservação) passa sem alteração de asserção sobre comportamento de botão/status; `tests/test_tela_atualizar_envio.py::test_bloco_de_envio_nao_mexe_nos_ids_e_data_confirm_da_baixa` confirma ids/`data-confirm` intactos. |

**Gaps de precisão encontrados**: 0. A única divergência (CAD-03) foi um desvio de implementação, não de spec, e foi corrigida antes de fechar este relatório.

---

## Achado da 1ª rodada e correção

Codex (`codex:codex-rescue`) verificou o *working tree* não commitado e apontou:

1. **CAD-03 (não atende)**: `envio-arquivos-area`/`envio-preservacao`/`envio-avisos` tinham sido movidos para fora de `#bloco-envio`, para uma `<section id="atualizar-resultados">` que também absorvia Progresso e Prévia — sem necessidade funcional e contrariando a AC3 ("cada card SHALL contain ... its result/preservation areas").
2. **Fora de escopo**: essa mesma seção reparentava `#atualizar-progresso`/`#atualizar-previa`, que `spec.md:18` explicitamente deixa de fora ("Ficam fora dos dois cards, como já estão hoje").
3. O teste `tests/test_tela_atualizar_envio.py::test_resultados_do_envio_ficam_abaixo_dos_dois_cards` (nome original) *codificava* essa divergência, então não protegia a AC.
4. Gate não rodou no ambiente do Codex (`python`/`pytest` fora do `PATH` daquele sandbox) — não é um problema deste repositório; confirmado nesta sessão que `python`/`pytest` funcionam normalmente aqui.

Correção: `app/templates/atualizar.html` — as três áreas do envio voltaram para dentro de `#bloco-envio`; `#atualizar-progresso`/`#atualizar-previa` voltaram para o nível anterior (fora dos cards); a `<section id="atualizar-resultados">` foi removida. `app/assets/style.css` — removida a regra `#atualizar-resultados` (o seletor não existe mais). `tests/test_tela_atualizar_envio.py` — teste renomeado para `test_resultados_do_envio_ficam_dentro_do_proprio_card`, agora afirmando o oposto (áreas dentro do card, Progresso/Prévia fora dele).

---

## Gate final

- `python -m pytest tests/test_tela_atualizar_envio.py tests/test_js_envio.py -q` → **28 passed**.
- `python -m pytest tests/ -q` → **680 passed**, 2 warnings pré-existentes (`FutureWarning` em `app/data/fatores.py`, fora do escopo desta feature).
- `python .claude/skills/tlc-spec-driven/scripts/validate_spec.py cards-atualizar-dados` → 0 erros, 0 avisos.
- Nenhum dado pessoal de estudante envolvido — feature é só reorganização de marcação/CSS/JS de uma tela administrativa, sem tocar leitura de planilha.

## Lições

Verificação num sandbox sem acesso ao `PATH` do ambiente real não deve travar o relatório do verificador, mas também não deve ser tratada como "gate passou" — o Codex sinalizou a lacuna corretamente ("Gate obrigatório não concluído") em vez de assumir sucesso. O achado real (CAD-03) veio da leitura estrutural do diff, não do gate — reforça que a leitura de diff linha a linha continua sendo a primeira linha de defesa, mesmo quando o gate automatizado não roda no ambiente do verificador.
