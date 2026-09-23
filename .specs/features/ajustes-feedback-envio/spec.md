# Ajustes de Feedback do Envio Specification

## Problem Statement

No primeiro uso real da tela "Enviar pastas" (depois de `cards-atualizar-dados`), a usuária relatou três problemas concretos, vistos em capturas de tela do próprio uso: (1) a caixa amarela pedindo confirmação de preservação confunde quem opera a tela; (2) o resultado por arquivo do envio aparece confinado à coluna do card "Enviar pastas" em vez de ocupar a largura inteira da página, apesar de já ter sido pedido antes; (3) unidades presentes no CSV de ciclos mas fora do cadastro de campi só recebem um aviso — e como a unidade está no arquivo do Sistec, ela existe de verdade e devia ser cadastrada, não só apontada como ausente.

## Goals

- [x] A caixa amarela de confirmação de preservação de campus ausente sai da tela; salvar deixa de exigir esse clique.
- [ ] O resultado por arquivo do envio (e os avisos que vêm com ele) aparece abaixo dos dois cards, com a largura inteira da página — não confinado à coluna do card "Enviar pastas".
- [ ] Unidade presente no CSV de ciclos mas ausente do cadastro de campi é cadastrada automaticamente (`app/data/campi.incluir_campus`), em vez de só listada como "fora do cadastro".

## Out of Scope

| Feature | Reason |
| --- | --- |
| Mudar a leitura ou consolidação dos CSVs (`ler_planilha`, `consolidar`, `montar_versao_interna`) | Os três pedidos são de UI e de cadastro de campi, não de parsing/consolidação — confirmado que `ingest.py` já grava dados de qualquer `co_unidade` presente no CSV, cadastrado ou não (ver Assumptions). |
| Cadastro automático a partir da baixa direta do Sistec (`criar_execucao`/`atualizar_lista`) | A baixa já cadastra via captura de perfis; o gap descrito pela usuária é só no envio de pastas. |
| Remover por completo a máquina de confirmação do servidor (`execucoes.ConfirmacaoNecessaria`, `salvar(..., confirmado=...)`) | AFE-01 só precisa que o cliente pare de exigir o clique — ver decisão em Assumptions. |
| Trocar o layout dos dois cards (`cards-atualizar-dados`) | Os cards continuam lado a lado; só o que estava preso na coluna do envio some de lá. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| AFE-01: como parar de exigir o clique de confirmação | O cliente (`atualizar.js`) sempre manda `confirmar_preservacao: true` ao salvar; a rota `POST /admin/atualizar/execucoes/<id>/salvar` e `execucoes.ConfirmacaoNecessaria` continuam existindo sem alteração, só nunca mais disparam a partir desta tela. A caixa `#envio-preservacao` (texto + checkbox) e a 2ª frase do parágrafo do card ("Antes de salvar, o sistema mostra a lista... e pede a sua confirmação.") saem da marcação. | "Preservado" já significa "nada é apagado" — o card já avisa isso na 1ª frase, antes de qualquer envio. Um clique extra para confirmar algo não destrutivo é o que a usuária chamou de confuso. Reverte a intenção original da confirmação (UPL-08/RN-22, `atualizacao-por-upload`), registrado aqui porque é o pedido direto desta rodada. | y — pedido explícito da usuária nesta conversa |
| AFE-02: onde entra o bloco de resultado | Sai de dentro de `#bloco-envio` para um bloco de largura inteira logo abaixo do `<div class="d-flex flex-column flex-lg-row">` dos dois cards, antes de `#atualizar-progresso` — mesma posição que `#atualizar-progresso`/`#atualizar-previa` já ocupam hoje. | É onde a página já tem largura inteira disponível; os dois cards mantêm sua largura de coluna (identificador da pasta, botão Enviar, status), só o resultado tabular sai. **Supera `CAD-03`** de `.specs/features/cards-atualizar-dados/spec.md` — aquela AC (cada card mantém sua própria área de resultado) partiu de uma leitura errada do pedido original da usuária, que já tinha pedido esse layout antes. | y — a captura de tela (Image #1) mostra o resultado hoje confinado à coluna, e a usuária cita um pedido anterior não atendido |
| AFE-03: dados do cadastro automático | `incluir_campus(id_perfil=f"envio-{co_unidade}", nome_perfil=f"Unidade {co_unidade} (cadastrada pelo envio de pastas)", co_unidade=co_unidade, origem="manual")`, um por código presente em `envio.campi_nao_cadastrados(...)`, antes de montar a resposta. `origem="manual"` (não um valor novo como `"envio"`) para reusar a proteção que já existe em `app/data/campi.py:113` (`atualizar_lista` só apaga o que **não** é `origem == "manual"` numa futura recaptura de perfis pelo Sistec) sem tocar nesse código. `id_perfil` prefixado com `envio-` (nunca dígito) garante que `id_suspeito()` (`app/data/campi.py:52-55`) sinaliza esse campus como "identificador inválido: a atualização não roda assim" em Configurações — correto, porque não existe um identificador de perfil real vindo do CSV; a baixa direta do Sistec para essa unidade só funciona depois que alguém completa o cadastro à mão. | Não há coluna de nome da unidade nas planilhas de ciclo (`app/sistec/colunas.py:26`, só `CÓDIGO UNIDADE DE ENSINO`→`CO_UNIDADE`) — não há nome real para usar. `id_perfil` não-numérico é a única forma de garantir que o aviso de "identificador inválido" (já existente, `app/templates/configuracoes.html:71`) apareça sozinho, sem inventar um aviso novo. | n — decisão técnica default; revisar o texto de `nome_perfil` com a usuária se ela tiver uma preferência |
| AFE-03: mensagem depois de cadastrar | Sem `br-message warning`; opcionalmente uma linha neutra (texto simples, sem cor de alerta) do tipo "N unidade(s) nova(s) cadastrada(s) automaticamente: …", no mesmo padrão de `#envio-ignorados` (texto simples, não `<ul class="br-message warning">`). | A usuária pediu para tirar a mensagem que diz que elas **não** estão cadastradas — não necessariamente qualquer menção a elas. Uma linha neutra evita que o cadastro automático pareça silencioso demais para conferir depois. | n — se a usuária preferir nada nenhuma, é só apagar essa linha; o cadastro em si (Goal 3) não depende dela |
| AFE-03: erro de cadastro automático | Se `incluir_campus` levantar `CampusInvalido` (colisão inesperada), o envio não falha por causa disso: a unidade é pulada do cadastro automático (fica só na prévia, como hoje), sem interromper a prévia nem o restante do envio. | O cadastro automático é uma melhoria de cadastro, não parte crítica do caminho de salvar dados — uma colisão rara não deve travar quem só queria enviar planilhas. | n — não deve acontecer na prática (o código já vem filtrado por `campi_nao_cadastrados`, que exclui `co_unidade` já cadastrado) |

**Open questions:** o texto de `nome_perfil` do cadastro automático (AFE-03) e se a linha neutra pós-cadastro deve existir ou não — ambos marcados `n` acima, decisões default sujeitas a ajuste sem replanejar o resto.

---

## User Stories

### P1: Salvar sem o clique extra de confirmação ⭐ MVP

**User Story**: Como administradora, quero salvar um envio que preserva algumas unidades sem precisar marcar uma caixa numa mensagem amarela, porque já sei (o card já avisa) que nada é apagado.

**Why P1**: Pedido direto; hoje a caixa aparece e confunde, e sem essa mudança o Salvar continua pedindo o clique.

**Acceptance Criteria**:

1. WHEN a prévia do envio tem unidades ausentes (preservadas) THEN the system SHALL NOT show any yellow confirmation box/checkbox on screen.
2. WHEN the administradora clicks Salvar on an envio preview with preserved units THEN the system SHALL save without requiring any extra confirmation click, exactly as it already does when there are no preserved units.
3. The explanatory paragraph in the "Enviar pastas" card SHALL keep saying that absent units are preserved, but SHALL NOT say a confirmation will be required before saving.
4. The server-side gate (`ConfirmacaoNecessaria`, `POST .../salvar`) SHALL remain in the codebase unchanged in behavior — the client always sends `confirmar_preservacao: true`, so it is satisfied on the first request.

**Independent Test**: Enviar duas pastas que deixam uma unidade cadastrada de fora, conferir que nenhuma caixa amarela aparece, e que clicar Salvar grava de primeira sem nenhum aviso de confirmação pendente.

---

### P1: Resultado por arquivo com a largura inteira da página

**User Story**: Como administradora, quero ver o resultado por arquivo do envio ocupando toda a largura da tela, não só a metade do lado do card, para conseguir ler a tabela sem espremer.

**Why P1**: Pedido direto, com captura de tela mostrando o problema atual; já tinha sido pedido antes.

**Acceptance Criteria**:

1. WHEN an envio finishes reading (successfully or with `falhou_consolidacao`) THEN the result-by-file table, the ignored-files line, and any envio warnings SHALL render in a block whose width is the full content width of the page, not constrained to the "Enviar pastas" card's column.
2. WHILE the viewport is at least 992px wide (the two cards side by side) THE result block SHALL still span the full width below both cards, not just the width of one card.
3. The two cards (`Atualizar do Sistec`, `Enviar pastas`) SHALL keep their current explanatory text, action buttons, and folder pickers unchanged — only the result/warnings content moves.

**Independent Test**: Com a tela em pelo menos 992px, enviar pastas válidas e conferir que a tabela "Resultado por arquivo" (e os avisos, se houver) se estende da margem esquerda à direita da área de conteúdo, abaixo dos dois cards — não alinhada só sob o card da direita.

---

### P1: Cadastro automático de unidade presente no envio

**User Story**: Como administradora, quero que uma unidade que aparece nos ciclos enviados, mas ainda não está na lista de campi, seja cadastrada sozinha — porque se ela está no arquivo do Sistec, ela existe.

**Why P1**: Pedido direto; hoje a tela só avisa "fora do cadastro, não atualizada", que a usuária considera errado — a unidade devia entrar no cadastro.

**Acceptance Criteria**:

1. WHEN an envio's ciclos contain a `co_unidade` not present in `campi_sistec` THEN the system SHALL create a new row in `campi_sistec` for that `co_unidade` (via `incluir_campus`) before responding, instead of leaving it uncadastered.
2. The response SHALL NOT contain a message stating that the unit is "fora do cadastro" / "não atualizada".
3. IF `incluir_campus` fails for a given `co_unidade` (unexpected conflict) THEN the envio SHALL still complete for the rest of the data — that one unit's auto-registration is skipped without failing the request.
4. A unit auto-registered this way SHALL show up afterward in `/admin/campi` (Gerenciar campi) and count toward the totals shown in Configurações, exactly like any other cadastro.
5. A unit auto-registered this way SHALL survive a future recaptura de perfis via login no Sistec (não deve ser apagada por `atualizar_lista` só porque não veio na lista capturada).

**Independent Test**: Enviar um envio cujos ciclos citam um `co_unidade` que não está em `/admin/campi`; depois do envio, abrir `/admin/campi` e confirmar que a unidade aparece na lista (sinalizada com identificador inválido, já que não veio nenhum id_perfil real do CSV), sem nenhuma mensagem de "fora do cadastro" na tela de envio.

---

## Edge Cases

- IF the same `co_unidade` appears twice across two different envios (one already auto-registered) THEN the second envio SHALL NOT try to register it again — it is already in `campi_sistec`, so `envio.campi_nao_cadastrados` already excludes it.
- IF an envio has zero preserved units and zero unregistered units THEN nothing from AFE-01/AFE-03 SHALL render (same as before this feature) — the "os dois lados" nunca aparecem sem motivo.
- IF a `falhou_consolidacao` happens THEN no result/warnings/auto-cadastro SHALL run — nothing is read far enough to know any of that (unchanged from today).

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| AFE-01 | P1: Salvar sem o clique extra de confirmação | Design | Passed |
| AFE-02 | P1: Resultado por arquivo com a largura inteira da página | Design | Pending |
| AFE-03 | P1: Cadastro automático de unidade presente no envio | Design | Pending |

**Detalhamento:**

- **AFE-01** — Remove a caixa amarela de confirmação; salvar não exige mais o clique (P1.1 AC 1-4).
- **AFE-02** — Resultado por arquivo em largura inteira, fora da coluna do card (P1.2 AC 1-3).
- **AFE-03** — Unidade fora do cadastro é cadastrada automaticamente, sem aviso de "não cadastrada" (P1.3 AC 1-5).

**ID format:** `AFE-[NUMBER]`

**Coverage:** 3 total, 0 mapped to tasks, 3 unmapped ⚠️ (escopo Medium — Tasks fica implícito no Execute)

---

## Success Criteria

- [ ] Nenhuma caixa amarela de confirmação de preservação aparece em nenhum fluxo de envio; Salvar nunca pede esse clique.
- [ ] O resultado por arquivo do envio (tabela + avisos) ocupa a largura inteira da página, abaixo dos dois cards.
- [ ] Unidade presente nos ciclos enviados mas fora do cadastro é cadastrada automaticamente; nenhuma mensagem de "fora do cadastro"/"não atualizada" aparece.
- [ ] `cards-atualizar-dados/spec.md` (AC3/CAD-03) recebe uma nota de superação apontando para esta feature (AFE-02), sem reescrever o relato histórico de `validation.md` daquela feature.
- [ ] `pytest tests/ -q` verde, incluindo os testes de `tests/test_tela_atualizar_envio.py`, `tests/test_js_envio.py` e `tests/test_admin_envio*.py` ajustados para o novo comportamento.
