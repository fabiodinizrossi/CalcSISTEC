# MVP 5 — Coleta pelo Sistec marcada como experimental — Specification

## Problem Statement

A via oficial de atualização no MVP é o envio de pastas. A coleta pelo botão
"Atualizar do Sistec" continua na tela por decisão da responsável, mas ainda
não foi validada com uma baixa real. Ela abre o Sistec no navegador e vigia a
pasta de downloads **do computador onde o CalcSISTEC roda**, então só funciona
quando o app roda no mesmo computador do navegador da PI; num servidor na
internet, ela não tem como funcionar. Hoje a tela apresenta as duas vias como
equivalentes, e o checklist de cutover ainda cobra itens da coleta.

## Goals

- [ ] Quem abre `/admin/atualizar` vê que a coleta é experimental e que o envio de pastas é a via oficial.
- [ ] Documentos e checklist de cutover não cobram mais nada da coleta.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Esconder ou desligar a coleta | Decisão da responsável: continua visível. |
| Validar a coleta com baixa real | Spec futura. |
| Fazer a coleta funcionar com o app no servidor | Spec futura (`.specs/MVP.md`, "Fora do MVP"). |
| Mudar o funcionamento da coleta | Nada muda além do texto. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Visual do selo | `<span class="br-tag">Experimental</span>` ao lado do título "Atualizar do Sistec" (componente de tag do gov.br DS) | Componente pronto do DS | y |
| Texto do aviso | "Experimental: ainda não validada com uma baixa real e só funciona quando o CalcSISTEC roda no mesmo computador do seu navegador. A via oficial é **Enviar pastas**, abaixo." | Diz o risco e aponta a via oficial | y |
| Ordem das seções | Mantida | Mudar a ordem mexe no JavaScript da tela; o aviso basta | y |

**Open questions:** none.

---

## User Stories

### P1: Coleta sinalizada como experimental ⭐ MVP

**Acceptance Criteria**:

1. WHEN a PI abre `/admin/atualizar` THEN the system SHALL mostrar o selo "Experimental" junto do título "Atualizar do Sistec".
2. The seção "Atualizar do Sistec" SHALL mostrar o texto do aviso da tabela de Assumptions, antes do botão.
3. The system SHALL NOT mudar ids, botões nem o JavaScript da coleta.

### P1: Documentos e checklist sem a coleta ⭐ MVP

**Acceptance Criteria**:

1. The `scripts/verificar_prontidao_cutover.py` SHALL NOT listar nos itens manuais o roteiro com o Sistec simulado e a instalação da extensão.
2. The `README.md`, o `TESTAR.md` e o `DEPLOY.md` SHALL chamar a coleta de experimental e o envio de pastas de via oficial.

---

## Edge Cases

- WHEN a tela abre em tema escuro THEN o selo SHALL continuar legível (vem do DS).

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| EXP-01 | Coleta sinalizada — AC1..AC3 | Tasks | Pending |
| EXP-02 | Documentos — AC1, AC2 | Tasks | Pending |

**Coverage:** 2 total, 2 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `python -m pytest -q` verde com os testes novos.
