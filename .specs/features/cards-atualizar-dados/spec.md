# Cards de Atualizar Dados Specification

## Problem Statement

Depois do primeiro teste real da tela "Atualizar dados", a usuária pediu uma reorganização visual: em vez do seletor "De onde vêm os dados" (rádio) que só mostra um bloco por vez, ela quer os dois caminhos — Sistec e envio de pastas — sempre visíveis, cada um dentro de um card do padrão gov.br, com a explicação junto da ação.

## Goals

- [ ] A tela mostra dois cards sempre visíveis, lado a lado em telas largas e empilhados no celular: um para "Atualizar do Sistec", outro para "Enviar pastas".
- [ ] Cada card contém sua explicação e sua ação (botões) juntos, sem exigir uma escolha prévia de origem.
- [ ] A aparência do card usa os tokens do gov.br DS (AD-003), sem depender da classe `.br-card` do pacote (defeituosa para este uso, ver Assumptions).

## Out of Scope

| Feature | Reason |
| --- | --- |
| Mudar o comportamento de qualquer botão, rota ou lógica de envio/baixa | É reorganização visual; nenhuma acceptance criteria de `atualizacao-por-upload`/`correcoes-envio-pastas` muda de comportamento. |
| Mexer no bloco de Progresso, Prévia ou Publicação | Ficam fora dos dois cards, como já estão hoje. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Interação dos dois cards | Sempre visíveis lado a lado (`flex-column flex-lg-row`, como o resto da tela); remove o `<fieldset>` de rádio "De onde vêm os dados" por completo | Confirmado com a usuária: sem etapa de escolha prévia, cada card já é a ação. | y |
| Classe do card | Classe própria `.cartao`/`.cartao-titulo`, usando só os tokens de card do DS (`--card-padding`, `--surface-shadow-sm`, `--surface-rounder-md`, `--border-color`, `--background`) — nunca a classe `.br-card` | `.br-card` no pacote vendorizado (`app/static/govbr-ds/dist/core.min.css`) é `position: absolute` — construído para menus flutuantes/cookiebar (`.br-cookiebar .br-card`, `.br-breadcrumb .br-card`), não para conteúdo de página. Usar a classe literal quebraria o layout (card flutuando fora do fluxo). Os tokens de espaçamento/sombra/borda do próprio card (`--card-padding`, `--surface-shadow-sm`) continuam disponíveis e corretos para uso fora de `.br-card`. | y |
| Título de cada card | `<h2>`, mesmo nível hierárquico de "Progresso"/"Prévia"/"Publicação" já existentes na página | Mantém a árvore de headings coerente (H1 da página, H2 das seções). | y |

**Open questions:** none — resolvidas acima.

---

## User Stories

### P1: Ver os dois caminhos sempre, sem escolher origem antes ⭐ MVP

**User Story**: Como administradora, quero ver os dois cards (Sistec e envio de pastas) ao abrir a tela, cada um com sua explicação e seu botão, para escolher o que usar sem uma etapa de seleção antes.

**Why P1**: É o pedido direto desta rodada; sem isso a tela continua com o rádio que a usuária quer remover.

**Acceptance Criteria**:

1. WHEN the administradora opens `/admin/atualizar` THEN the system SHALL show two cards, always visible, without any prior origin-selection control.
2. WHILE the viewport is at least 992px wide THE system SHALL lay the two cards side by side; WHILE narrower THE system SHALL stack them.
3. Each card SHALL contain its own explanatory text and its own action controls (the Sistec card keeps `btn-atualizar-sistec`/`btn-login-feito`/`btn-cancelar`/status/progress-steps; the envio card keeps the two folder pickers, `btn-enviar-pastas`, and its result/preservation areas), unchanged in id and behavior from before this feature.
   > **Superseded by `AFE-02`** (`.specs/features/ajustes-feedback-envio/spec.md`, 2026-09-23): a leitura real de tela mostrou o resultado por arquivo confinado à coluna do card, e a usuária já tinha pedido antes que ele ocupasse a largura inteira. O resultado/avisos do envio saíram do card; o resto desta AC (texto, ações, seletores de pasta) continua valendo.
4. The system SHALL NOT render the `br-card` class from the vendored gov.br DS package (it is `position: absolute` in this bundle and unsuitable for page content).
5. IF a submission or download is already in progress THEN the existing per-card visibility rules for buttons/status (e.g. `btn-cancelar` hidden until active) SHALL continue to work exactly as before — this feature only changes the outer container, not the inner logic.

**Independent Test**: Abrir a tela sem nenhuma execução em andamento e conferir que os dois cards aparecem lado a lado (≥992px) e empilhados (<992px), cada um com seu texto e seus botões, sem nenhum controle de "escolher origem".

---

## Edge Cases

- IF the administradora already has files selected in the envio card's folder inputs THEN switching viewport width (resize) SHALL NOT clear the selection — it is a CSS-only stacking change, not a re-render.
- IF a baixa or envio is in progress WHEN the page loads THEN both cards SHALL still render (no visibility toggle depends on origin choice anymore); the existing per-element `hidden` attributes inside each card continue to govern what's shown mid-execution.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| CAD-01 | P1: Ver os dois caminhos sempre | Design | Pending |
| CAD-02 | P1: Ver os dois caminhos sempre | Design | Pending |
| CAD-03 | P1: Ver os dois caminhos sempre | Design | Pending |
| CAD-04 | P1: Ver os dois caminhos sempre | Design | Pending |
| CAD-05 | P1: Ver os dois caminhos sempre | Design | Pending |

**Detalhamento:** CAD-01 = AC1 (sem seleção prévia); CAD-02 = AC2 (responsivo); CAD-03 = AC3 (conteúdo intacto por card); CAD-04 = AC4 (sem `.br-card`); CAD-05 = AC5 (lógica interna inalterada).

**ID format:** `CAD-[NUMBER]`

**Coverage:** 5 total, 0 mapped to tasks, 5 unmapped ⚠️ (escopo Medium — Tasks fica implícito no Execute, ver auto-sizing do skill)

---

## Success Criteria

- [ ] Os dois cards aparecem sempre, sem rádio de origem.
- [ ] Nenhuma classe `br-card` na marcação.
- [ ] `pytest tests/` verde, incluindo os testes ajustados de `test_tela_atualizar_envio.py` e `test_js_envio.py` que hoje dependem do rádio.
