# Atualização por Upload de Pastas Specification

## Problem Statement

Hoje a única porta de entrada de dados é a baixa ao vivo pelo Sistec (`/admin/atualizar`, D-14), que depende de login gov.br, da lista de campi com identificador de perfil válido e de uma sessão de navegador estável. Quando o Sistec está indisponível, o perfil de um campus está errado, ou a instituição já extraiu as planilhas por outro caminho, não há como carregar os dados no painel. A administradora precisa de um segundo caminho, equivalente em resultado, que use os CSVs de extração do Sistec que ela já tem em disco.

## Goals

- [ ] A tela "Atualizar dados" oferece duas origens à escolha da usuária: baixar do Sistec (atual) ou enviar as pastas de ciclos e de matrículas.
- [ ] O envio de pastas produz exatamente a mesma versão interna que a baixa produziria para os mesmos dados, passando pela mesma prévia, pelo mesmo Salvar/Descartar e pela mesma publicação.
- [ ] Um envio que não cobre todos os campi preserva os dados dos campi ausentes e só grava após confirmação explícita.
- [ ] Nenhum byte enviado é gravado em disco, e nenhuma coluna de dado pessoal entra na consolidação.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Reintroduzir o upload `.xlsx` de `/admin/upload` | Removido por D-14. Esta feature recebe CSVs na estrutura de extração do Sistec, não a planilha consolidada antiga. |
| Envio por `.zip` | A usuária escolheu o seletor de pasta do navegador. Compactar antes seria um passo extra e exigiria tratar arquivo compactado malicioso. |
| Mapear arquivo para campus por nome de arquivo | A atribuição de campus vem de `CO_UNIDADE` nas linhas de ciclo. Convenção de nome seria frágil e não é garantida pela extração. |
| Correção PNP dos status de matrícula | Continua fora do sistema (RN-23); o envio segue a mesma regra da baixa, com `STATUS_MATRICULA_PNP` nulo. |
| Alterar o cálculo de qualquer indicador | O envio reusa `consolidar` e `montar_versao_interna` sem tocar em `app/domain/`. Princípio I. |
| Envio agendado ou por linha de comando | A feature é uma ação administrativa manual na interface. |

---

## Assumptions & Open Questions

Toda ambiguidade está resolvida ou registrada aqui.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Campus cadastrado sem linhas no envio | Preserva os dados atuais desse campus (mesma regra RN-22 de campus falho) e exige confirmação explícita antes de gravar | Escolha da usuária. Reusa o caminho `campi_falhos` já implementado e testado em `app/data/ingest.montar_versao_interna`, e o aviso impede que um envio incompleto por engano passe despercebido. | y |
| Arquivo reprovado na validação de estrutura | Falha o envio inteiro, nomeando o arquivo e o motivo, sem gravar nada | A usuária pediu "falha o campus, segue os outros", mas um CSV ilegível ou sem as colunas obrigatórias não revela a qual campus pertence: nem a planilha de matrícula tem coluna de unidade, nem um arquivo que não abre tem linhas para ler. Seguir com os demais produziria uma versão interna com um campus silenciosamente incompleto, o que o Princípio I proíbe. O caminho para o resultado que ela quer continua existindo: retirar o arquivo problemático da pasta faz aquele campus cair na regra de campus ausente acima, que preserva os dados e avisa. | y |
| Separador e codificação dos CSVs | `;` e `cp1252`, como na extração do Sistec | É o que `app/sistec/execucoes.receber_bytes` já usa para as planilhas baixadas. Arquivo fora desse formato cai na reprovação de estrutura acima. | y |
| Limite de tamanho do envio | O `MAX_CONTENT_LENGTH` de 500 MB já configurado em `app/app.py:43`, sem limite adicional por arquivo | Evita um segundo limite para manter em sincronia. 500 MB cobre com folga a extração de uma rede de campi. | y |
| Processamento do envio | Síncrono na própria requisição `POST`, com a resposta trazendo o desfecho de cada arquivo | A extração de uma rede do porte do IFFar (cerca de 22 CSVs) é lida em poucos segundos; uma thread de fundo exigiria copiar até 500 MB para a memória antes de a requisição fechar, sem ganho perceptível. | y |
| Bytes enviados em disco | O buffer temporário do Werkzeug é aceito, desde que nada sobreviva à requisição | Mesma garantia que a baixa já dá (os CSVs do Sistec passam por uma pasta em disco e são apagados após a leitura) e é o que o Princípio III exige textualmente. Trocar o parser de formulário por um `stream_factory` em memória seria infraestrutura própria num caminho sensível, limitada pela RAM. | y |
| Linha de `CO_UNIDADE` não cadastrada em `campi_sistec` | Entra na versão interna e é listada na prévia como campus não cadastrado | O dado veio do Sistec e é legítimo; recusar obrigaria a cadastrar o campus antes de poder conferir a prévia. O aviso deixa a divergência visível. | y |
| Matrícula cujo `CODIGO_CICLO_MATRICULA` não existe nos ciclos enviados | Descartada, com a contagem exibida na prévia | É o comportamento que a junção interna de `montar_matriculas_e_eficiencia` já tem; a contagem torna a perda visível em vez de silenciosa. | y |
| Erro de consolidação global (chave repetida com conteúdo divergente, portfólio com unidade divergente) | Falha o envio inteiro em `falhou_consolidacao`, sem gravar | Mesmo desfecho que a baixa já tem para `ConsolidacaoInvalida`. A detecção é do conjunto, não de um arquivo. | y |
| Ano-base aplicado ao envio | O mesmo `ANO_BASE` de ambiente usado pela baixa (`_ano_base_config`) | Uma só fonte de ano-base para as duas origens; divergir criaria versões internas incomparáveis. | y |
| Limite de execuções simultâneas | Uma por administradora, compartilhando o registro de `app/sistec/execucoes.py` com a baixa (RN-11) | Baixa e envio gravam a mesma versão interna; permitir as duas ao mesmo tempo produziria uma prévia indeterminada. | y |

**Open questions:** none — todas resolvidas ou registradas acima. A única linha marcada `n` já tem default escolhido e justificativa; basta aceitá-la ou corrigi-la ao confirmar esta spec.

---

## User Stories

### P1: Escolher a origem dos dados ⭐ MVP

**User Story**: Como administradora, quero escolher entre baixar do Sistec e enviar as pastas que já tenho, para atualizar o painel mesmo quando a baixa ao vivo não é possível.

**Why P1**: Sem a escolha visível na tela, o segundo caminho não existe para a usuária. É a porta de entrada de todo o resto.

**Acceptance Criteria**:

1. WHEN the administradora opens `/admin/atualizar` THEN the system SHALL present both origins — "Atualizar do Sistec" and "Enviar pastas" — as two selectable alternatives on the same page.
2. WHILE no origin is selected the system SHALL keep the controls of both origins inactive and show no progress area.
3. WHERE the "Enviar pastas" origin is selected the system SHALL show one folder field for ciclos and one folder field for matrículas, each accepting a directory selection.
4. The system SHALL require an authenticated administrator session for every route of the envio flow, returning the login redirect for an unauthenticated request.

**Independent Test**: Abrir `/admin/atualizar` e conferir que a marcação traz as duas origens, os dois campos de pasta e que uma requisição sem sessão é recusada.

---

### P1: Enviar as duas pastas e ver a prévia ⭐ MVP

**User Story**: Como administradora, quero enviar a pasta de ciclos e a pasta de matrículas e ver a prévia dos dados consolidados, para conferir antes de gravar.

**Why P1**: É o núcleo da feature: sem consolidação e prévia, o envio não produz versão interna nenhuma.

**Acceptance Criteria**:

1. WHEN the administradora submits both folders THEN the system SHALL read every `.csv` file in each folder with separator `;` and encoding `cp1252`, keeping only the allowlisted columns of the corresponding type via `app/sistec/colunas.aplicar_permissao`.
2. IF the ciclos folder or the matrículas folder contains no `.csv` file THEN the system SHALL reject the submission with the message naming which folder is empty, and SHALL NOT write anything.
3. WHEN a folder contains files whose extension is not `.csv` THEN the system SHALL ignore those files and SHALL list their names in the submission result.
4. WHEN every file passes the structure validation THEN the system SHALL consolidate the read rows through `app/sistec/consolidacao.consolidar` and SHALL reach the `previa` state with the same counts of ciclos and matrículas the baixa would produce for the same rows.
5. WHILE the submission is being read and consolidated the system SHALL show an in-progress indicator naming the total number of submitted files, and WHEN the submission finishes the system SHALL list the per-file outcome.
6. The system SHALL discard the submitted bytes once the request ends, keeping no submitted file, temporary buffer or derived raw copy readable after the response.
7. The system SHALL NOT include any column of `app/data/transform.COLUNAS_PII` in the consolidated result, regardless of the columns present in the submitted files.
8. WHEN the administradora confirms the prévia THEN the system SHALL write the internal version through `app/data/ingest.montar_versao_interna` using the `ANO_BASE` of the environment.
9. WHEN the administradora discards the prévia THEN the system SHALL leave the current internal version unchanged.

**Independent Test**: Enviar duas pastas de CSVs sintéticos válidos, conferir as contagens da prévia contra as de uma consolidação direta dos mesmos DataFrames, e conferir que nenhum arquivo temporário sobrou.

---

### P1: Preservar e confirmar os campi ausentes ⭐ MVP

**User Story**: Como administradora, quero que os campi que não estão no envio mantenham os dados que já tinham e que o sistema me avise antes de gravar, para não apagar um campus por ter enviado a pasta incompleta.

**Why P1**: É a diferença entre um envio parcial ser um recurso e ser um acidente de perda de dados.

**Acceptance Criteria**:

1. WHEN the consolidated ciclos contain no row for a campus registered in `campi_sistec` with a filled `co_unidade` THEN the system SHALL treat that `co_unidade` as a preserved campus and SHALL keep its existing rows in `interna_cursos`, `interna_ciclos`, `interna_matriculas` and `interna_matriculas_eficiencia` unchanged.
2. WHILE the prévia lists at least one preserved campus the system SHALL show those campi by name and SHALL keep the Salvar action blocked until the administradora explicitly confirms the preservation.
3. WHEN the administradora confirms and saves THEN the system SHALL record the preserved `co_unidade` list in the histórico entry of that submission.
4. WHEN the consolidated ciclos cover every registered campus THEN the system SHALL require no extra confirmation and SHALL enable Salvar directly.
5. WHEN the consolidated ciclos contain a `CO_UNIDADE` that is not registered in `campi_sistec` THEN the system SHALL include those rows in the internal version and SHALL list that `CO_UNIDADE` in the prévia as a campus não cadastrado.

**Independent Test**: Enviar uma pasta de ciclos cobrindo 2 de 3 campi cadastrados, conferir que Salvar só grava após a confirmação e que as linhas do terceiro campus continuam idênticas na versão interna.

---

### P1: Recusar um envio estruturalmente inválido ⭐ MVP

**User Story**: Como administradora, quero que um arquivo quebrado pare o envio com uma mensagem que diga qual arquivo e qual o problema, para corrigir a pasta em vez de publicar um número errado.

**Why P1**: Um envio meio processado grava uma versão interna com um campus incompleto, e o número errado é o pior desfecho possível (Princípio I).

**Acceptance Criteria**:

1. IF any submitted `.csv` file lacks at least one of the required columns of its type (`COLUNAS_CICLO` for ciclos, `COLUNAS_MATRICULA` for matrículas) THEN the system SHALL fail the whole submission with motivo `colunas_ausentes`, naming that file, and SHALL NOT write anything to the internal version.
2. IF any submitted `.csv` file cannot be parsed with separator `;` and encoding `cp1252` THEN the system SHALL fail the whole submission with motivo `leitura_csv`, naming that file, and SHALL NOT write anything to the internal version.
3. IF consolidation raises `ConsolidacaoInvalida` THEN the system SHALL end the submission in state `falhou_consolidacao`, SHALL expose the error message, and SHALL NOT write anything to the internal version.
4. The system SHALL NOT include any cell content of a submitted file in an error message, restricting it to the file name, the motivo and institutional codes (RN-13).
5. IF the submitted payload exceeds `MAX_CONTENT_LENGTH` THEN the system SHALL respond `413` and SHALL show a message stating the 500 MB limit.

**Independent Test**: Enviar uma pasta com um CSV sem a coluna `CÓDIGO CICLO DE MATRÍCULA` e conferir que a resposta nomeia o arquivo, que a versão interna não mudou e que a mensagem não traz conteúdo de célula.

---

### P2: Impedir dois caminhos de atualização ao mesmo tempo

**User Story**: Como administradora, quero que o sistema recuse um envio enquanto há uma baixa ou outro envio em andamento, para não acabar com duas prévias disputando a mesma versão interna.

**Why P2**: A regra já existe para a baixa (RN-11); estendê-la ao envio evita um estado indeterminado, mas não é o que faz a feature funcionar no caso feliz.

**Acceptance Criteria**:

1. WHILE a baixa is in a non-terminal state for the same administradora the system SHALL reject a new envio with status `409` and erro `execucao_em_andamento`.
2. WHILE an envio is in a non-terminal state for the same administradora the system SHALL reject a new baixa with status `409`.
3. WHILE an envio is in state `previa` the system SHALL reject a new envio with status `409` and erro `previa_pendente`.
4. WHEN the administradora cancels an envio in progress THEN the system SHALL move it to a terminal state and SHALL allow a new envio immediately afterwards.

**Independent Test**: Criar um envio, tentar criar outro e conferir o `409` com o código de erro; cancelar e conferir que o próximo é aceito.

---

### P2: Registrar o envio no histórico

**User Story**: Como administradora, quero ver no histórico que a atualização veio de um envio de pastas e como ela terminou, para auditar de onde cada versão publicada saiu.

**Why P2**: O Princípio VII exige registro das operações de dados; a feature não fica completa sem ele, mas a consolidação funciona antes dele existir.

**Acceptance Criteria**:

1. WHEN an envio starts THEN the system SHALL open a histórico entry of a tipo that distinguishes it from `baixa`.
2. WHEN an envio reaches a terminal state THEN the system SHALL close that histórico entry with the corresponding desfecho among the already valid ones (`salva`, `descartada`, `cancelada`, `falhou`, `falhou_consolidacao`).
3. WHEN an envio is saved THEN the system SHALL record in that entry the number of consolidated matrículas, the preserved campi and the number of processed files.
4. The system SHALL NOT record any submitted file content or personal data in the histórico entry, restricting `detalhe` to counts, file names and motivos (RN-13).

**Independent Test**: Rodar um envio até salvar e conferir a linha de histórico: tipo próprio, desfecho `salva`, contagens preenchidas e `detalhe` sem conteúdo de planilha.

---

## Edge Cases

- IF a folder field is submitted empty THEN the system SHALL reject the submission stating that both folders are required, before reading anything.
- IF the two folders are inverted (ciclos content sent as matrículas) THEN the system SHALL fail with motivo `colunas_ausentes` naming the first offending file, since neither column set satisfies the other type.
- WHEN the same `CODIGO_CICLO_MATRICULA` appears in more than one submitted ciclos file with identical content THEN the system SHALL deduplicate it and SHALL keep one row.
- IF the same `CODIGO_CICLO_MATRICULA` appears in more than one submitted file with divergent content THEN the system SHALL fail the submission in `falhou_consolidacao`.
- WHEN a submitted ciclos file contains only rows whose status or situação is `EXCLUÍDO` THEN the system SHALL filter them out and SHALL treat the resulting campus as absent, falling under the preservation rule.
- WHEN the matrículas folder contains rows whose ciclo is absent from the ciclos folder THEN the system SHALL discard those rows and SHALL show the discarded count in the prévia.
- IF the consolidated ciclos end up empty after filtering THEN the system SHALL fail the submission in `falhou_consolidacao` with the existing message `nenhum par de ciclo consolidado`.
- WHEN a subfolder exists inside a selected folder THEN the system SHALL process the `.csv` files it contains under the same rules as the top level.
- IF the browser sends a file with a name containing path separators THEN the system SHALL use the name only for display, after stripping any directory component.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| UPL-01 | P1: Escolher a origem dos dados | Design | Pending |
| UPL-02 | P1: Escolher a origem dos dados | Design | Pending |
| UPL-03 | P1: Enviar as duas pastas e ver a prévia | Design | Pending |
| UPL-04 | P1: Enviar as duas pastas e ver a prévia | Design | Pending |
| UPL-05 | P1: Enviar as duas pastas e ver a prévia | Design | Pending |
| UPL-06 | P1: Enviar as duas pastas e ver a prévia | Design | Pending |
| UPL-07 | P1: Preservar e confirmar os campi ausentes | Design | Pending |
| UPL-08 | P1: Preservar e confirmar os campi ausentes | Design | Pending |
| UPL-09 | P1: Preservar e confirmar os campi ausentes | Design | Pending |
| UPL-10 | P1: Recusar um envio estruturalmente inválido | Design | Pending |
| UPL-11 | P1: Recusar um envio estruturalmente inválido | Design | Pending |
| UPL-12 | P1: Recusar um envio estruturalmente inválido | Design | Pending |
| UPL-13 | P2: Impedir dois caminhos de atualização ao mesmo tempo | - | Pending |
| UPL-14 | P2: Registrar o envio no histórico | - | Pending |

**Detalhamento dos IDs:**

- **UPL-01** — A tela oferece as duas origens e os dois campos de pasta (P1.1 AC 1-3).
- **UPL-02** — Toda rota do envio exige sessão administrativa (P1.1 AC 4).
- **UPL-03** — Leitura dos `.csv` com `;`/`cp1252` e lista de permissão de colunas (P1.2 AC 1, AC 7).
- **UPL-04** — Pasta vazia e arquivos não-`.csv`: recusa e listagem (P1.2 AC 2-3).
- **UPL-05** — Consolidação e prévia equivalentes às da baixa, com progresso por arquivo (P1.2 AC 4-5).
- **UPL-06** — Bytes descartados após a leitura, nada gravado em disco; Salvar/Descartar (P1.2 AC 6, AC 8-9).
- **UPL-07** — Campus cadastrado ausente é preservado (P1.3 AC 1).
- **UPL-08** — Confirmação explícita antes de gravar com campi preservados (P1.3 AC 2-4).
- **UPL-09** — `CO_UNIDADE` não cadastrado entra e é sinalizado (P1.3 AC 5).
- **UPL-10** — Arquivo sem colunas obrigatórias ou ilegível falha o envio inteiro (P1.4 AC 1-2).
- **UPL-11** — `ConsolidacaoInvalida` termina em `falhou_consolidacao` sem gravar (P1.4 AC 3).
- **UPL-12** — Mensagens de erro sem conteúdo de planilha; `413` acima do limite (P1.4 AC 4-5).
- **UPL-13** — Exclusividade entre baixa e envio (P2.1 AC 1-4).
- **UPL-14** — Histórico com tipo próprio, desfecho e contagens sem PII (P2.2 AC 1-4).

**ID format:** `UPL-[NUMBER]`

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 14 total, 0 mapped to tasks, 14 unmapped ⚠️

---

## Dimensões de Requisito Implícito

Varredura completa exigida pelo escopo Large. Nenhuma entrada em branco.

| Dimensão | Cobertura |
| --- | --- |
| Validação de entrada e limites | UPL-03, UPL-04, UPL-10, UPL-12 — extensão, separador, codificação, colunas obrigatórias, pasta vazia, limite de 500 MB. |
| Falha e falha parcial | UPL-07, UPL-10, UPL-11 — arquivo inválido falha o envio inteiro sem gravar; campus ausente é preservado em vez de apagado. |
| Idempotência / repetição / duplicata | Reenviar a mesma pasta produz a mesma versão interna; chave repetida com conteúdo idêntico é deduplicada, com conteúdo divergente falha (Edge Cases). |
| Limites de autorização e taxa | UPL-02 — sessão administrativa em toda rota. Limite de taxa N/A porque o sistema roda com processo único e uma execução por administradora (P-09, RN-11). |
| Concorrência / ordenação | UPL-13 — baixa e envio compartilham o registro de execuções; um bloqueia o outro com `409`. |
| Ciclo de vida do dado / expiração | UPL-06 — bytes descartados após a leitura, nunca gravados; a prévia vive em memória e morre com o estado terminal. Versão anterior preservada por `salvar_interna` (RN-20). |
| Observabilidade | UPL-05 (progresso por arquivo), UPL-14 (histórico com tipo, desfecho e contagens). |
| Falha de dependência externa | N/A — o envio não chama nenhum serviço externo; é exatamente o caminho que existe para quando o Sistec está indisponível. |
| Integridade de transição de estado | UPL-11, UPL-13 — o envio percorre a mesma máquina de estados da execução, sem os estados de navegador, e só grava a partir de `previa`. |

---

## Success Criteria

- [ ] Para um mesmo conjunto de linhas, a versão interna gravada pelo envio de pastas é idêntica, tabela por tabela, à gravada pela baixa do Sistec.
- [ ] Um envio cobrindo parte dos campi cadastrados nunca reduz o número de linhas dos campi ausentes na versão interna.
- [ ] Nenhum arquivo enviado existe em disco depois do envio, e nenhuma coluna de `COLUNAS_PII` aparece em qualquer tabela `interna_*`.
- [ ] Um envio com um arquivo inválido deixa a versão interna byte a byte inalterada.
- [ ] `pytest` verde e `scripts/verificar_prontidao_cutover.py` com saída 0 após a feature.
