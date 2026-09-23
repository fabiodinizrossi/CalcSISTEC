# Correções do Envio de Pastas Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/correcoes-envio-pastas/design.md`
**Status**: Draft

---

## Test Coverage Matrix

> Gerada do código, das diretrizes do projeto e da spec — confirmar antes do Execute. Diretrizes encontradas: `.specs/PROJECT_RULES.md` (Princípio IV), `AGENTS.md`, `TESTAR.md`, e os testes existentes de `app/sistec/colunas.py`, `app/assets/style.css` e `app/static/js/atualizar.js` já usados como piso.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Leitura de planilha (`app/sistec/colunas.py`) | unit | Todos os ramos de `ler_planilha`; 1:1 com CEP-04/CEP-05; byte inválido em coluna descartada e em coluna mantida, cabeçalho com byte inválido, erro estrutural real ainda recusado | `tests/test_colunas.py` | `python -m pytest tests/test_colunas.py -q` |
| Config (`requirements.txt`) | none | - (build gate apenas) | - | build gate apenas |
| Infraestrutura de teste (`tests/dom_falso.py`) | none (infra) | Suíte de JS existente permanece verde após a extensão; sem asserção nova aqui, a asserção mora nas tarefas que a consomem | `tests/test_js_envio.py`, `tests/test_js_fiacao.py` | `python -m pytest tests/test_js_envio.py tests/test_js_fiacao.py -q` |
| Marcação da tela (`app/templates/atualizar.html`) | integration | O widget novo (input escondido, botão, status) presente com os `id`/`aria-describedby` corretos, para as duas pastas | `tests/test_tela_atualizar_envio.py` | `python -m pytest tests/test_tela_atualizar_envio.py -q` |
| Estilo (`app/assets/style.css`) | none (regressão) | Coberto por `tests/test_style_css.py` já existente (sem cor literal, sem variável `--gov-`, pontos de quebra do DS) — nenhuma asserção nova necessária | `tests/test_style_css.py` | `python -m pytest tests/test_style_css.py -q` |
| Script da tela (`app/static/js/atualizar.js`) | unit | Todos os ramos de `contarSelecao`/`renderizarSelecao`/`selecaoDePasta`; 1:1 com CEP-01/02/03 e os Edge Cases da spec | `tests/test_js_envio.py` | `python -m pytest tests/test_js_envio.py -q` |

## Gate Check Commands

> Gerados do código — confirmar antes do Execute. `pytest` na raiz é inválido: coleta `APAGAR/`/`.test-tmp*/` sem permissão (`.specs/STATE.md`). Todo comando aponta para `tests/`.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Depois de tarefa com testes unitários apenas | `python -m pytest tests/<arquivo_do_teste> -q` |
| Full | Depois de tarefa com testes de integração ou que mexe em mais de um arquivo de teste | `python -m pytest tests/ -q` |
| Build | Em tarefa só de configuração (sem teste próprio) | `python -m pytest tests/ -q` |

---

## Execution Plan

As fases são ordenadas e rodam em sequência — cada fase termina antes da seguinte, e as tarefas dentro de uma fase executam em ordem.

### Phase 1: Leitura tolerante a bytes fora do cp1252

```
T1 → T2
```

### Phase 2: Widget de escolha de pasta

```
T3 → T6
T4 → T5
T4 → T6
T6 → T7
```

---

## Task Breakdown

### T1: Fixar a versão mínima do pandas

**What**: acrescentar o piso `pandas>=1.3` em `requirements.txt` (é a versão que introduziu `encoding_errors` em `read_csv`, usado por T2).
**Where**: `requirements.txt`
**Depends on**: None
**Reuses**: nenhum
**Requirement**: CEP-04

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `requirements.txt` lista `pandas>=1.3` (mantendo a linha existente, só acrescentando o piso)
- [x] `pip install -r requirements.txt` (ou equivalente) não quebra no ambiente atual (`pandas==2.3.0` já instalado, confirmado nesta sessão)
- [x] Gate check passes: `python -m pytest tests/ -q`
- [x] Test count: contagem atual mantida (mudança de config, sem teste próprio)

**Status**: Done -- commit `7717641`.

**Tests**: none
**Gate**: build

**Commit**: `chore(deps): fixa a versão mínima do pandas para encoding_errors`

---

### T2: Decodificar CSV do Sistec com bytes fora do cp1252 sem abortar

**What**: os dois `pd.read_csv` de `ler_planilha` (cabeçalho e conteúdo completo) ganham `encoding_errors="replace"`, para que um byte sem mapeamento em `cp1252` vire `�` em vez de levantar `UnicodeDecodeError`.
**Where**: `app/sistec/colunas.py`
**Depends on**: T1
**Reuses**: `ler_planilha` (assinatura inalterada), `aplicar_permissao`
**Requirement**: CEP-04, CEP-05

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] Um CSV sintético com byte `0x81` numa coluna fora de `COLUNAS_CICLO`/`COLUNAS_MATRICULA` é lido com sucesso por `ler_planilha`, e a coluna com o byte não aparece no resultado (`aplicar_permissao` descarta)
- [x] Um CSV sintético com o mesmo byte dentro de uma coluna **mantida** (ex.: `NO_STATUS_MATRICULA`) é lido com sucesso, com o valor daquela célula contendo o caractere de substituição — sem lançar exceção (CEP-04 AC 1, Risco aceito por decisão da spec)
- [x] Um CSV com cabeçalho sem uma coluna obrigatória continua levantando `ValueError("colunas_ausentes")`, mesmo com bytes inválidos em outras colunas
- [x] Um CSV cuja estrutura real está quebrada continua levantando `ValueError("leitura_csv")` (CEP-05 AC 3) — **desvio**: o exemplo de "linha com número de campos diferente do cabeçalho" de tasks.md não quebra no pandas 2.3.0 (ele preenche/ignora os campos extras, antes e depois desta mudança, com ou sem `usecols`); o caso foi coberto com o defeito estrutural que o pandas realmente recusa (aspas desbalanceadas → `ParserError` → `leitura_csv`) e com o delimitador errado (`colunas_ausentes`)
- [x] Um CSV sem nenhum byte inválido produz exatamente o mesmo `DataFrame` que antes da mudança (não regressão)
- [x] O arquivo real reproduzido nesta sessão (`sistec_Campus Santa Rosa_sistec.csv`) não faz parte do repositório nem dos testes (dado pessoal) — só o CSV sintético equivalente
- [x] Gate check passes: `python -m pytest tests/test_colunas.py tests/test_execucoes.py tests/test_envio.py -q`
- [x] Test count: contagem anterior + no mínimo 5 testes novos, um por item acima (7 novos)

**Status**: Done -- commit `026f26b`.

**Tests**: unit
**Gate**: quick

**Commit**: `fix(sistec): lê CSV do Sistec com bytes fora do cp1252 sem abortar a leitura`

---

### T3: Dar suporte a clique e arquivos com caminho de pasta no dublê de DOM

**What**: `tests/dom_falso.py` ganha `click()` no elemento simulado (dispara os ouvintes de `"click"`, como `disparar` já faz para outros eventos) e o helper de preparação de arquivos passa a aceitar `webkitRelativePath` além de `name`.
**Where**: `tests/dom_falso.py`
**Depends on**: None (abre a Phase 2; a Phase 1 já terminou)
**Reuses**: `criarElemento`, `disparar` (mesmo padrão de despacho de evento)
**Requirement**: CEP-01, CEP-02

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] `elemento.click()` existe e dispara os ouvintes registrados via `addEventListener("click", ...)`, no mesmo padrão de `disparar`
- [x] Um `input.files` simulado aceita objetos com `name` e `webkitRelativePath` opcionais, sem quebrar os testes existentes que só passam `name` (helper `arquivoFalso(nome, caminho)` no harness: `caminho` ausente ou `null` omite `webkitRelativePath`)
- [x] Gate check passes: `python -m pytest tests/test_js_envio.py tests/test_js_fiacao.py -q`
- [x] Test count: contagem atual mantida (25 passados, mesma contagem; extensão de infraestrutura, sem asserção nova nesta tarefa — a asserção chega em T6)

**Status**: Done -- commit `47139b7`.

**Tests**: none
**Gate**: quick

**Commit**: `test(js): dá suporte a clique e webkitRelativePath no DOM simulado dos testes`

---

### T4: Trocar a marcação do bloco de envio pelo widget próprio de pasta

**What**: substituir os dois `<div class="br-upload">` do bloco `#bloco-envio` por marcação própria: `input[type=file][hidden]` (mesmos `id`/`name` de hoje) + `button` visível + parágrafo de status, uma vez para ciclos e uma para matrículas.
**Where**: `app/templates/atualizar.html`
**Depends on**: None (a Phase 1 já terminou; T3 é de teste, não de marcação)
**Reuses**: `id`/`name` atuais (`envio-ciclos`, `envio-matriculas`), classe `br-button secondary` do DS
**Requirement**: CEP-01, CEP-02

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [x] Os dois `input[type=file]` mantêm `id="envio-ciclos"`/`id="envio-matriculas"`, `name` iguais, `webkitdirectory multiple accept=".csv"`, e ganham o atributo `hidden`
- [x] Cada pasta tem um `button` visível (`btn-escolher-ciclos`/`btn-escolher-matriculas`) com `aria-describedby` apontando para o parágrafo de status correspondente
- [x] Cada pasta tem um parágrafo de status (`envio-ciclos-status`/`envio-matriculas-status`) com `role="status" aria-live="polite"`, texto inicial dizendo que a pasta é obrigatória
- [x] A marcação não usa mais a classe `br-upload`
- [x] Gate check passes: `python -m pytest tests/test_tela_atualizar_envio.py -q`
- [x] Test count: 5 anteriores + 6 novos = 11 passados (botão visível ×2, status anunciado ×2, input escondido, ausência de `br-upload`)
- [x] **Desvio**: dois testes existentes foram ajustados porque a marcação que eles liam deixou de existir por decisão da spec — `test_bloco_de_envio_tem_uma_pasta_para_ciclos_e_uma_para_matriculas` (o `<label for="envio-...">` virou botão com `aria-describedby`; o teste agora cobra `hidden` no input) e `test_blocos_empilham_abaixo_de_992px_com_classes_do_ds` (o sentinela `class="br-upload` virou `id="btn-enviar-pastas"`). Nenhuma asserção foi afrouxada.

**Status**: Done -- commit `<hash>`.

**Tests**: integration
**Gate**: quick

**Commit**: `feat(ui): troca o br-upload por um widget próprio de escolha de pasta`

---

### T5: Estilizar o widget de pasta só com tokens do DS

**What**: regra `.campo-pasta`/`.campo-pasta-status` em `style.css`, dando ao botão e ao status a aparência de campo de formulário do DS, usando só variáveis (`--interactive`, `--focus-color`, `--gray-*`, `--background`).
**Where**: `app/assets/style.css`
**Depends on**: T4
**Reuses**: padrão de borda/foco por token já usado em `app/assets/style.css:632-634`
**Requirement**: CEP-01

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] `.campo-pasta`/`.campo-pasta-status` existem e são referenciadas pela marcação de T4
- [ ] Nenhuma cor hexadecimal ou `rgb()/hsl()` literal nas regras novas (só `var(--token)`)
- [ ] O botão tem um estado de foco visível via `var(--focus-color)`
- [ ] Gate check passes: `python -m pytest tests/test_style_css.py -q`
- [ ] Test count: contagem atual mantida (a regressão de `test_style_css.py` já cobre; sem teste novo necessário)

**Tests**: none
**Gate**: quick

**Commit**: `style(ui): dá aparência de campo do DS ao widget de pasta, só com tokens`

---

### T6: Implementar a seleção de pasta sem rede em atualizar.js

**What**: `CAMPOS_PASTA`, `contarSelecao`, `renderizarSelecao` e `selecaoDePasta` — ao escolher uma pasta, mostrar nome (via `webkitRelativePath`) e contagem de `.csv`/outros no parágrafo de status correspondente, sem nenhuma chamada de rede nem animação de carregamento.
**Where**: `app/static/js/atualizar.js`
**Depends on**: T3, T4
**Reuses**: `arquivosDe`, `$`, padrão de manipulador de evento já usado no arquivo
**Requirement**: CEP-01, CEP-02, CEP-03

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Clicar no botão de escolher pasta aciona `input.click()` do campo correspondente
- [ ] Ao trocar `input.files` (evento `change`), o status mostra o nome da pasta (primeiro segmento de `webkitRelativePath` do primeiro arquivo) e a contagem de `.csv`
- [ ] Seleção com arquivos que não são `.csv` mostra a contagem de "outros" na mesma linha de status
- [ ] `webkitRelativePath` vazio (ou ausente) faz o status mostrar só a contagem, sem nome de pasta, sem lançar erro
- [ ] Reescolher a pasta substitui o texto de status anterior, nunca acrescenta
- [ ] Nenhum `fetch`, `setTimeout` ou classe de estado "carregando" é usado nesse fluxo (CEP-03)
- [ ] Gate check passes: `python -m pytest tests/test_js_envio.py -q`
- [ ] Test count: contagem anterior + no mínimo 6 testes novos, um por item acima

**Tests**: unit
**Gate**: quick

**Commit**: `feat(ui): mostra pasta e contagem de arquivos escolhidos, sem chamada de rede`

---

### T7: Redesenhar o status de seleção ao trocar de origem

**What**: `escolherOrigem` passa a redesenhar os dois status de seleção de pasta (chamando `renderizarSelecao` de novo para os campos já preenchidos) ao alternar entre "Atualizar do Sistec" e "Enviar pastas", sem descartar os arquivos já escolhidos no `input`.
**Where**: `app/static/js/atualizar.js`
**Depends on**: T6
**Reuses**: `escolherOrigem` (existente), `renderizarSelecao`, `CAMPOS_PASTA` (T6)
**Requirement**: CEP-02

**Tools**:

- MCP: NONE
- Skill: `tlc-spec-driven`

**Done when**:

- [ ] Trocar para "Enviar pastas" com um `input` já tendo arquivos escolhidos redesenha o status correto (nome + contagem), sem exigir escolher de novo
- [ ] Trocar de volta para "Atualizar do Sistec" e depois para "Enviar pastas" não duplica nem perde o texto de status
- [ ] O comportamento existente de `escolherOrigem` (mostrar/esconder os blocos, limpar `elStatusEnvio`) continua igual
- [ ] Gate check passes: `python -m pytest tests/ -q`
- [ ] Test count: contagem anterior + no mínimo 2 testes novos

**Tests**: unit
**Gate**: full

**Commit**: `feat(ui): mantém o status de seleção de pasta ao trocar de origem`

---

## Phase Execution Map

```
Phase 1 → Phase 2

Phase 1:  T1 ------→ T2
Phase 2:  T3 ------→ T6 ------→ T7
          T4 ------→ T5
          T4 ------→ T6
```

Dentro da Phase 2, T3 e T4 não dependem uma da outra — executam na ordem escrita (T3, depois T4, depois T5, depois T6, depois T7), mas a dependência real de cada tarefa é a que está no seu próprio "Depends on", não a ordem de leitura. 7 tarefas cabem num único lote (≤ ~8), sem necessidade de sub-agentes.

---

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1: Piso do pandas | 1 arquivo de config | ✅ Granular |
| T2: Decodificação tolerante | 1 função | ✅ Granular |
| T3: Suporte a clique/arquivos no dublê | 1 arquivo, 2 capacidades coesas | ✅ Granular |
| T4: Marcação do widget | 1 template | ✅ Granular |
| T5: Estilo do widget | 1 arquivo CSS | ✅ Granular |
| T6: Lógica de seleção de pasta | 1 arquivo, 1 conjunto coeso de funções | ✅ Granular |
| T7: Integração com troca de origem | 1 função existente, 1 alteração | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | (início da Phase 1) | ✅ Match |
| T2 | T1 | T1 → T2 | ✅ Match |
| T3 | None | (início da Phase 2, fase anterior já terminou) | ✅ Match |
| T4 | None | (início da Phase 2, fase anterior já terminou) | ✅ Match |
| T5 | T4 | T4 → T5 | ✅ Match |
| T6 | T3, T4 | T3 → T6, T4 → T6 | ✅ Match |
| T7 | T6 | T6 → T7 | ✅ Match |

Nenhuma dependência aponta para fase posterior. T3 e T4 não dependem uma da outra (ambas abrem a Phase 2) mas executam na ordem escrita dentro da fase.

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | Config | none | none | ✅ OK |
| T2 | Leitura de planilha | unit | unit | ✅ OK |
| T3 | Infraestrutura de teste | none (infra) | none | ✅ OK |
| T4 | Marcação da tela | integration | integration | ✅ OK |
| T5 | Estilo | none (regressão) | none | ✅ OK |
| T6 | Script da tela | unit | unit | ✅ OK |
| T7 | Script da tela | unit | unit | ✅ OK |

---

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| CEP-01 | T3, T4, T5, T6 |
| CEP-02 | T3, T4, T6, T7 |
| CEP-03 | T6 |
| CEP-04 | T1, T2 |
| CEP-05 | T2 |
| CEP-06 | T7 |

6 requisitos, 6 mapeados, 0 sem tarefa.
