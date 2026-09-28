# MVP 5 — Coleta pelo Sistec marcada como experimental — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Exceção combinada com a usuária para executores sem suporte a skills: leia `.specs/MVP-PROTOCOLO.md` inteiro e siga-o; ele aponta o arquivo da skill que substitui a ativação.

Pré-requisito: `mvp-4-seguranca` com Verifier PASS.

---

**Spec**: `.specs/features/mvp-5-coleta-experimental/spec.md`
**Status**: Draft

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Template `atualizar.html` | integration | Selo e aviso no HTML renderizado; ids da coleta intactos | `tests/test_tela_atualizar_envio.py` | `python -m pytest tests/test_tela_atualizar_envio.py -q -p no:cacheprovider` |
| Script de prontidão e documentos | unit (higiene) | Itens da coleta fora da saída; termos exigidos nos documentos | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Full | Toda tarefa | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Execution Plan

### Phase 1: Tela e documentos

```
T1 → T2
```

---

## Task Breakdown

### T1: Selo e aviso na seção "Atualizar do Sistec"

**What**: Em `app/templates/atualizar.html`, o título `<h2>Atualizar do Sistec</h2>`
(perto da linha 14) ganha o selo, e logo abaixo dele entra o parágrafo do aviso.
**Where**: `app/templates/atualizar.html`
**Depends on**: None
**Reuses**: classe `br-tag` do gov.br DS; mensagem `br-message warning` se já usada no arquivo
**Requirement**: EXP-01

**Passos**:

1. Troque o título por:
   `<h2>Atualizar do Sistec <span class="br-tag">Experimental</span></h2>`.
2. Logo abaixo, antes do parágrafo de instruções:

   ```html
   <p class="aviso-experimental">
     <strong>Experimental:</strong> ainda não validada com uma baixa real e só funciona quando o
     CalcSISTEC roda no mesmo computador do seu navegador. A via oficial é
     <strong>Enviar pastas</strong>, abaixo.
   </p>
   ```

3. Não mude nenhum `id`, botão ou script.
4. Testes em `tests/test_tela_atualizar_envio.py` (reaproveite o jeito que o
   arquivo já abre `/admin/atualizar` com login): o HTML tem `br-tag` com o texto
   `Experimental` dentro do `h2` de "Atualizar do Sistec"; o aviso aparece antes
   de `id="btn-atualizar-sistec"`; `btn-atualizar-sistec` e `btn-login-feito`
   continuam no HTML.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: linha de base + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(atualizar): marcar a coleta pelo sistec como experimental`

---

### T2: Tirar a coleta do checklist e dos documentos

**What**: `scripts/verificar_prontidao_cutover.py` sem os dois itens manuais da
coleta (hoje perto das linhas 155 e 156, mais as linhas equivalentes da docstring,
perto das linhas 20 e 21); `README.md`, `TESTAR.md` e `DEPLOY.md` dizendo que a
coleta é experimental e o envio de pastas é a via oficial; handoff no `STATE.md`.
**Where**: `scripts/verificar_prontidao_cutover.py`
**Depends on**: T1
**Reuses**: nenhum
**Requirement**: EXP-02

**Passos**:

1. No script, apague os dois `print` dos itens da coleta (roteiro com o Sistec
   simulado e extensão instalada) e as duas linhas correspondentes da docstring.
2. `README.md`, seção "As duas formas de atualizar": comece dizendo que o envio
   de pastas é a via oficial e que a coleta pelo Sistec é experimental (mesmo
   motivo do aviso da tela). `TESTAR.md`, seção "Passo a passo com o Sistec real":
   uma frase no começo marcando o passo a passo como experimental. `DEPLOY.md`:
   no checklist, nada da coleta.
3. Testes em `tests/test_higiene_repositorio.py`: a saída do script (use o
   `carregar_script` existente) não tem `onboarding` nem `Extensão`; `README.md`
   e `TESTAR.md` contêm `experimental`.
4. `.specs/STATE.md`: handoff curto da feature.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(coleta): tratar a coleta pelo sistec como experimental`

---

## Verificação (depois de T2)

Verifier independente. Sensor mínimo: tirar o selo; mover o aviso para depois do
botão; devolver um item da coleta à saída do script.

---

## Phase Execution Map

```
Phase 1:  T1 → T2
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | 1 template | ✅ |
| T2 | script + 3 documentos + STATE | ⚠️ coeso: uma mensagem em todos os documentos |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | template | integration | integration | ✅ |
| T2 | script e documentos | unit (higiene) | unit | ✅ |
