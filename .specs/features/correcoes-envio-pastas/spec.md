# Correções do Envio de Pastas Specification

## Problem Statement

O primeiro uso real da atualização por envio de pastas (`.specs/features/atualizacao-por-upload`) revelou dois defeitos: a tela não mostra nenhum controle clicável para escolher as pastas nem o que foi escolhido, e o envio falha inteiro sempre que algum arquivo do Sistec traz um byte fora do padrão `cp1252` — mesmo quando esse byte cai numa coluna que o sistema descarta sempre.

## Goals

- [ ] A tela mostra um controle visível e clicável para escolher cada pasta, com o nome da pasta e a quantidade de arquivos escolhidos, sem depender de comportamento que o pacote do DS não fornece nesta versão.
- [ ] Um arquivo do Sistec com bytes fora do `cp1252` em qualquer posição não impede mais a leitura do arquivo nem do envio.
- [ ] Nenhuma correção de codificação altera o conteúdo das colunas que o sistema usa (RN-17); o efeito fica restrito a texto de colunas já descartadas.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Detectar ou alternar entre múltiplas codificações (cp1252/utf-8/latin-1) | A usuária confirmou que os arquivos nunca são reabertos/salvos por outro programa (`.specs/features/atualizacao-por-upload`, decisão já registrada); o defeito reproduzido é um byte pontual fora do cp1252 dentro do próprio export do Sistec, não uma troca de codificação do arquivo inteiro. |
| Consolidar múltiplos meses de extração num único envio | Não fazia parte da reprodução confirmada nesta rodada (11 ciclos e 11 matrículas de um único mês). Fica para uma spec própria se a usuária pedir. |
| Refazer o layout inteiro da tela "Atualizar dados" | O escopo é só o bloco de envio (origem, pastas, resultado, preservação); o bloco da baixa pelo Sistec não muda. |
| Adotar o `br-upload` do gov.br DS como vem no pacote | Decisão já tomada: widget próprio, ver Assumptions. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Widget de escolha de pasta | Construído com JS próprio (reusa cores/bordas do DS via tokens, AD-003), sem o `.br-upload`/`initInstanceUpload()` do pacote | O pacote vendorizado (`app/static/govbr-ds/dist/components/upload/` está vazio de CSS próprio; o núcleo em `core.min.css`/`core-init.min.js` exige `input.upload-input` + `.upload-list` dentro de `.br-upload`, que a Fase 4 não usou — por isso nada aparecia. Mesmo corrigindo a marcação, o `initInstanceUpload()` embutido dispara um "Carregando..." de 0,5s por arquivo assim que a pasta é escolhida, antes do envio real — a usuária preferiu widget próprio a esse comportamento enganoso. | y |
| Correção de bytes fora do cp1252 | Decodificar com `errors="replace"` em vez do padrão estrito | Reproduzido: um único byte `0x81` (indefinido em cp1252) em qualquer posição do arquivo faz `pandas.read_csv` levantar `UnicodeDecodeError`, capturado hoje como `leitura_csv` (`app/sistec/colunas.py:90,100`). O byte encontrado no arquivo real caía em `NO_MAE_ALUNO`, fora da lista de permissão de `COLUNAS_MATRICULA` (`app/sistec/colunas.py:42-47`) — descartado de qualquer forma. `errors="replace"` deixa o arquivo inteiro ser lido, trocando só o byte inválido por `�`, sem re-lançar exceção. | y |
| Byte inválido dentro de uma coluna que o sistema mantém (não descartada) | Aceita a leitura com `�` no lugar do byte, sem aviso adicional na prévia | Corrigir a codificação real do byte é impossível sem saber a intenção original (o defeito é do export do Sistec, não documentado); recusar o arquivo inteiro por um byte fora de uma coluna de interesse já é o comportamento problemático que esta spec corrige. O caso concreto reproduzido caiu numa coluna descartada; nada nesta spec piora o caso de uma coluna mantida — ele já seria pior hoje (arquivo inteiro recusado). | y |
| Escopo do arquivo de teste da reprodução | Não versionar o CSV real (dado pessoal de estudantes) | O arquivo com o defeito contém `NO_MAE_ALUNO` de estudantes reais; os testes desta feature usam um CSV sintético mínimo com o mesmo byte na mesma coluna descartada, reproduzido e confirmado nesta sessão (145 bytes, mesma exceção). | y |

**Open questions:** none — todas resolvidas e registradas acima.

---

## User Stories

### P1: Ver e escolher as pastas de verdade ⭐ MVP

**User Story**: Como administradora, quero ver um controle clicável para escolher cada pasta e conferir o que escolhi, para não ficar sem saber se o envio está pronto pra disparar.

**Why P1**: Sem isso a origem "Enviar pastas" é inutilizável — é o defeito relatado em primeiro lugar.

**Acceptance Criteria**:

1. WHEN the administradora selects "Enviar pastas" THEN the system SHALL show one clickable control for the ciclos folder and one for the matrículas folder, each visible without relying on `.br-upload`'s built-in `input.upload-input` auto-detection.
2. WHEN the administradora chooses a folder in either control THEN the system SHALL display, next to that control, the folder name (from `webkitRelativePath` of the first selected file) and the count of `.csv` files found in it.
3. WHILE no folder has been chosen for a control THE system SHALL show a placeholder text stating the folder is required.
4. IF the browser selection contains files outside `.csv` THEN the system SHALL still show the folder name and the `.csv` count, counting non-`.csv` files separately in the same status line (they are still reported as ignored only after the real submission, per the existing UPL-04 behavior).
5. The system SHALL NOT show any per-file "uploading" animation before the administradora clicks "Enviar pastas" — the status reflects selection only, never a network state that has not happened.

**Independent Test**: Escolher uma pasta com arquivos mistos (`.csv` e outros) e conferir que o nome da pasta e a contagem aparecem imediatamente, sem nenhuma chamada de rede.

---

### P1: Não falhar o envio por um byte fora do cp1252 numa coluna descartada ⭐ MVP

**User Story**: Como administradora, quero que um arquivo do Sistec com um caractere estranho no meio dos dados continue sendo lido, para não perder o envio inteiro por um defeito de exportação que não afeta os dados que uso.

**Why P1**: É o erro reproduzido ("não foi possível ler... como planilha do Sistec") em arquivos confirmadamente corretos.

**Acceptance Criteria**:

1. WHEN a submitted `.csv` file contains a byte that has no mapping in `cp1252` THEN the system SHALL still parse the file, replacing that byte with the Unicode replacement character, and SHALL NOT raise `leitura_csv` for that reason alone.
2. WHEN the invalid byte falls inside a column outside `COLUNAS_CICLO`/`COLUNAS_MATRICULA` THEN the system SHALL produce a result identical to the same file without that byte (the column is dropped by `aplicar_permissao` regardless).
3. IF a submitted `.csv` file still cannot be parsed after the lenient decoding (e.g., wrong delimiter, truncated file) THEN the system SHALL keep raising `leitura_csv`, naming the file as today (UPL-10 unchanged).
4. The system SHALL apply the same lenient decoding to the existing baixa path (`app/sistec/execucoes.receber_bytes`, shared via `ler_planilha`), since the defect is in the shared reading function, not exclusive to envio.

**Independent Test**: Enviar um CSV sintético com um byte `0x81` numa coluna fora da lista de permissão e confirmar que o envio chega à prévia normalmente; enviar o mesmo CSV com o cabeçalho corrompido e confirmar que `leitura_csv` continua sendo recusado.

---

### P2: Deixar claro que "Enviar pastas" ainda não rodou

**User Story**: Como administradora, quero que a tela deixe óbvio quando os arquivos foram só escolhidos (não enviados), para não confundir seleção com envio.

**Why P2**: Reforça a história P1 acima; não é o que quebra o uso, mas evita confusão futura.

**Acceptance Criteria**:

1. WHILE a folder has been chosen but "Enviar pastas" has not been clicked yet THE system SHALL keep the status text saying the folder was selected, never "enviado" ou "lido".
2. WHEN the administradora clicks "Enviar pastas" THEN the system SHALL disable the button and show progress text distinct from the pre-click selection text (reusing the existing `Enviando N arquivo(s)...` message).

**Independent Test**: Escolher as duas pastas, conferir o texto de status antes de clicar, clicar em Enviar e conferir que o texto muda.

---

## Edge Cases

- IF the administradora reselects a folder (clicking the control again) THEN the system SHALL replace the previous folder name/count shown, not append to it.
- IF `webkitRelativePath` is empty (browser without `webkitdirectory` support falling back to plain file selection) THEN the system SHALL show the count of files without a folder name, instead of failing.
- IF every byte in the file is valid `cp1252` THEN the lenient decoding SHALL produce byte-identical text to today's strict decoding (no behavior change for well-formed files).
- IF the invalid byte falls inside a delimiter-adjacent position such that it changes the number of fields parsed on that row THEN the row SHALL still be rejected as `leitura_csv`/`colunas_ausentes` as appropriate — lenient decoding fixes character mapping, not structural column-count mismatches.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| CEP-01 | P1: Ver e escolher as pastas de verdade | Design | Pending |
| CEP-02 | P1: Ver e escolher as pastas de verdade | Design | Pending |
| CEP-03 | P1: Ver e escolher as pastas de verdade | Design | Pending |
| CEP-04 | P1: Não falhar por byte fora do cp1252 | Design | Pending |
| CEP-05 | P1: Não falhar por byte fora do cp1252 | Design | Pending |
| CEP-06 | P2: Deixar claro que envio ainda não rodou | - | Pending |

**Detalhamento:**

- **CEP-01** — Controles clicáveis próprios para as duas pastas, sem depender do `br-upload` padrão (P1.1 AC 1, 5).
- **CEP-02** — Nome da pasta + contagem de `.csv` exibidos ao escolher (P1.1 AC 2-4).
- **CEP-03** — Nenhuma animação de "enviando" antes do clique real (P1.1 AC 5; P2 AC 1).
- **CEP-04** — Decodificação tolerante a byte fora do cp1252, aplicada em `ler_planilha` (P1.2 AC 1-2, 4).
- **CEP-05** — `leitura_csv`/`colunas_ausentes` continuam recusando defeito estrutural real (P1.2 AC 3).
- **CEP-06** — Status distingue seleção de envio de fato (P2 AC 1-2).

**ID format:** `CEP-[NUMBER]`

**Coverage:** 6 total, 0 mapped to tasks, 6 unmapped ⚠️

---

## Success Criteria

- [ ] A tela mostra, sem nenhum clique além de escolher a pasta, o nome dela e a contagem de `.csv` encontrados.
- [ ] O arquivo real que falhava (`sistec_Campus Santa Rosa_sistec.csv`, com byte `0x81` em `NO_MAE_ALUNO`) passa a ser lido com sucesso, comprovado por teste automatizado com CSV sintético equivalente.
- [ ] Nenhuma coluna de `COLUNAS_CICLO`/`COLUNAS_MATRICULA` muda de valor para arquivos sem byte inválido (não-regressão).
- [ ] `pytest tests/` verde após a correção.
