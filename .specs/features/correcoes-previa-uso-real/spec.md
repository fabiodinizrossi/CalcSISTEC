# Correções da prévia após o uso real — Especificação

## Problem Statement

No primeiro teste real da prévia (`previa-paginas-publicas`), com os CSVs de 11 campi (2.600 ciclos, 116.011 matrículas), a usuária relatou quatro sintomas: as páginas da prévia não carregam; a prévia mostra todas as matrículas e não só as que entram pela regra da PNP; **Salvar na versão interna** responde "Não foi possível salvar."; e a tabela da prévia só mostra colunas de ciclo, sem o código da matrícula.

A reprodução com os mesmos CSVs, numa cópia do banco, encontrou seis causas:

1. **Rota da prévia nunca casa.** `app/pages/previa.py:26` registra `path="/admin/previa/<execucao_id>/<pagina>"`. Com `path=`, o Dash trata `<execucao_id>` como texto literal; variável de caminho exige `path_template=`. Toda URL de prévia cai em "404 - Page not found". Os testes chamam `layout()` direto e não passam pelo roteamento.
2. **Regressão no painel público.** Os callbacks das quatro páginas usam `State("<pagina>-preview", "data")` (`matriculas.py:339`, `eficiencia.py:119`, `evasao.py:133`, `percentuais_legais.py:138`), mas o `dcc.Store` só entra no layout com `preview_id`. No painel público o navegador lança `ReferenceError: A nonexistent object was used in an State of a Dash callback` e KPIs e tabelas ficam vazios assim que há dado publicado.
3. **Ciclos sem modalidade derrubam a prévia e o Salvar.** Onze ciclos antigos do programa MULHERES MIL (2011–2013, concluídos) vêm do Sistec sem `MODALIDADE ENSINO`. Isso gera 7 cursos com `modalidade_ensino` nulo, e a coluna é `NOT NULL` em `cursos`/`interna_cursos`. O envio responde `500` ao montar a fonte da prévia (`app/data/previa.py:84`), deixando a execução em `previa` sem fonte e sem candidato. Por isso o Salvar falha.
4. **Campus cadastrado pelo envio fica sem cidade e nome.** O cadastro automático (`ajustes-feedback-envio`, AFE-03) grava `cidade` e `nome_unidade` nulos. A projeção `campi_sistec → interna_campus` (`app/data/campi.py:289-298`) descarta linhas com esses campos nulos. Com `campus` vazio, as junções de `app/data/consulta.py` zeram todos os indicadores, tanto na prévia quanto no painel público. O CSV de ciclos traz `MUNICIPIO` e `NOME UNIDADE DE ENSINO`, mas a lista de permissão (`app/sistec/colunas.py:24-39`) não os lê.
5. **Publicar não leva os campi.** `campus` só muda por **Aplicar ao público** em Configurações (`app/data/versoes.py:182`, RN-33). Uma instalação que nunca usou esse botão publica os dados e continua com o painel zerado. A prévia usa o `campus` publicado e herda o mesmo vazio.
6. **O resumo e a amostra da prévia vêm do consolidado bruto.** O polling mostra `2600 ciclos e 116011 matrículas` e uma amostra só de ciclos (`app/sistec/execucoes.py:409-421`). O candidato que o Salvar grava tem 11.071 matrículas e 12.704 matrículas de eficiência, já filtradas pela regra da PNP.

## Goals

- [ ] As quatro páginas da prévia carregam pela URL `/admin/previa/<execucao_id>/<pagina>` com os dados do envio.
- [ ] O painel público volta a funcionar: KPIs e tabelas preenchidos quando há dado publicado, sem erro no navegador.
- [ ] Envio, prévia e Salvar funcionam com os CSVs reais, inclusive ciclos sem modalidade.
- [ ] Uma unidade presente no envio aparece nos indicadores da prévia e, depois de Publicar, no painel público, sem passo extra em Configurações.
- [ ] O resumo e a tabela da prévia em **Atualizar dados** mostram o conjunto filtrado pela PNP, com uma linha por matrícula (dados da matrícula e do ciclo juntos).

## Out of Scope

| Item | Motivo |
| --- | --- |
| Mudar a regra de filtragem PNP (`transform.py`, `BR-MIGRAR-*`) | O candidato já filtra corretamente; o erro é só de exibição do resumo e da amostra. |
| Aplicar fatores ao público no Publicar | A decisão da usuária cobre só os campi; `fatores` continua indo por **Aplicar ao público** e pelo ciclo atual de publicação. |
| Corrigir as 2 falhas pré-existentes de `tests/test_paginas_publicas.py` | Dependem do `app/data/sistec.db` local vazio; fora desta rodada. |
| Tela de edição de campi | O cadastro automático só preenche cidade e nome; edição continua em `/admin/campi`. |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Campi no Publicar | **Publicar** copia `interna_campus → campus` na mesma transação, com cópia para `anterior_campus`; **Desfazer** restaura `campus` junto das demais tabelas | Pedido da usuária: sem passo extra em Configurações. Pôr `campus` no mesmo ciclo de `anterior_*` mantém o Desfazer consistente (RN-27). Supera a regra de RN-33 de que `campus` só muda por **Aplicar ao público**, mas **Aplicar ao público** continua existindo. | y — escolha da usuária em 2026-09-23 |
| Campus usado pela prévia | `interna_campus` (o que o Publicar vai levar), no lugar do `campus` publicado. A assinatura de origem passa a resumir `interna_campus`. | Com a regra acima, a prévia mostra exatamente o que vai ao ar (PVP-04). | y — consequência direta da escolha acima |
| Ciclos sem modalidade | Descartados na preparação do candidato, com as matrículas deles. O resultado do envio informa quantos ciclos e matrículas saíram por falta de modalidade. | Escolha da usuária. Os casos reais são de 2011–2013 e estão concluídos. | y — escolha da usuária em 2026-09-23 |
| Cidade e nome do campus cadastrado pelo envio | Vêm de `MUNICIPIO` e `NOME UNIDADE DE ENSINO` do CSV de ciclos (primeiro valor não vazio por `CO_UNIDADE`). Unidade já cadastrada **sem** cidade ou nome recebe esses valores; valor já preenchido nunca é sobrescrito. | Sem cidade e nome a unidade não entra em `interna_campus`. Completar só o que está vazio preserva edições feitas à mão. | y — derivado da causa 4, sem alternativa que atenda aos Goals |
| Tabela da prévia em **Atualizar dados** | Amostra de até 20 linhas do candidato: uma linha por matrícula, juntando `co_matricula`, situação e mês de ocorrência corrigidos, ano-base, código do ciclo, curso, tipo, modalidade e unidade. Nenhuma coluna pessoal. | Pedido da usuária: "merge dos dois tipos de tabela". O candidato já não tem PII (`aplicar_permissao`). | y — pedido explícito da usuária |
| Contagens do resumo | Cursos, ciclos, matrículas e matrículas de eficiência do candidato. O total bruto lido continua visível só no resultado por arquivo. | O que conta para a conferência é o que o Salvar grava. | y |

**Open questions:** none — as duas decisões de regra foram tomadas pela usuária em 2026-09-23.

## User Stories

### P1: Abrir a prévia das quatro páginas ⭐ MVP

**User Story**: Como administradora, quero abrir as quatro páginas da prévia depois de enviar as pastas e ver os indicadores do envio.

**Why P1**: É a razão de a feature `previa-paginas-publicas` existir; hoje nenhuma URL de prévia abre.

**Acceptance Criteria**:

1. WHEN a administradora abre `/admin/previa/<execucao_id>/<pagina>` para uma execução de envio em `previa` THEN the system SHALL rotear para a página de prévia pelo Dash Pages e renderizar a faixa **Prévia não publicada** e o conteúdo da página, nunca "404 - Page not found".
2. WHEN a página da prévia termina de carregar no navegador THEN the system SHALL preencher os KPIs e a tabela a partir da fonte candidata, sem erro de callback no console.
3. WHEN o envio contém dados das unidades cadastradas THEN the system SHALL mostrar indicadores diferentes de zero para essas unidades na prévia.

**Independent Test**: Com os CSVs sintéticos de dois campi, enviar as pastas, pedir o roteamento do Dash (`/_dash-update-component` com `_pages_location.pathname` da prévia) e conferir que a resposta traz o layout da página e não "404"; chamar o callback de dados com o `Store` da prévia e conferir KPIs diferentes de zero.

### P1: Painel público volta a funcionar ⭐ MVP

**User Story**: Como visitante, quero ver os indicadores do painel público depois da publicação.

**Why P1**: É uma regressão introduzida pela prévia e afeta quem não usa a área administrativa.

**Acceptance Criteria**:

1. WHEN uma das quatro páginas públicas é aberta com dados publicados THEN the system SHALL renderizar no layout todo componente citado como `Input` ou `State` dos callbacks da página, para que o navegador não lance `ReferenceError`.
2. WHEN o callback de dados de uma página pública roda sem prévia THEN the system SHALL ler só a versão publicada (comportamento anterior à prévia).
3. The system SHALL ter um teste que, para cada uma das quatro páginas, compare os IDs usados em `Input`/`State` dos callbacks com os IDs presentes no layout público e no layout de prévia, e falhe se faltar algum.

**Independent Test**: Para as quatro páginas, montar o layout sem `preview_id` e com `preview_id`, coletar os IDs do layout e confirmar que contêm todos os IDs de `Input`/`State` registrados no `callback_map` para aquela página.

### P1: Envio e Salvar com os CSVs reais ⭐ MVP

**User Story**: Como administradora, quero enviar as pastas reais do Sistec e salvar a versão interna sem erro.

**Why P1**: Hoje o envio real devolve `500` e o Salvar falha.

**Acceptance Criteria**:

1. WHEN o conjunto enviado tem ciclos com modalidade de ensino vazia THEN the system SHALL descartar esses ciclos e as matrículas ligadas a eles antes de montar o candidato, e seguir o envio até o estado `previa`.
2. WHEN ciclos foram descartados por falta de modalidade THEN the system SHALL informar na resposta do envio e no polling a quantidade de ciclos e de matrículas descartados.
3. WHEN a administradora clica em **Salvar na versão interna** numa prévia montada a partir desses CSVs THEN the system SHALL gravar a versão interna e responder sucesso.
4. IF a montagem da fonte da prévia falhar por qualquer erro THEN the system SHALL responder com erro próprio no JSON (nunca `500` sem corpo), manter a execução descartável e não gravar nada.
5. The system SHALL aplicar a mesma regra de modalidade vazia à baixa direta do Sistec, que usa a mesma preparação do candidato.

**Independent Test**: CSV sintético com um ciclo sem `MODALIDADE ENSINO` e duas matrículas nele: o envio chega a `previa`, informa 1 ciclo e 2 matrículas descartados, e o Salvar grava sem esse ciclo.

### P1: Unidades do envio aparecem nos indicadores ⭐ MVP

**User Story**: Como administradora, quero que as unidades que vieram no envio apareçam na prévia e, depois de Publicar, no painel público.

**Why P1**: Hoje o painel fica zerado mesmo com dados publicados.

**Acceptance Criteria**:

1. WHEN o envio cadastra automaticamente uma unidade THEN the system SHALL gravar `cidade` e `nome_unidade` a partir de `MUNICIPIO` e `NOME UNIDADE DE ENSINO` do CSV de ciclos daquela unidade.
2. WHEN uma unidade já cadastrada tem `cidade` ou `nome_unidade` vazio e o envio traz esses valores THEN the system SHALL preencher só o campo vazio, sem sobrescrever o que já estava preenchido.
3. WHEN a administradora clica em **Publicar** THEN the system SHALL copiar `interna_campus` para `campus` na mesma transação, guardando o `campus` anterior em `anterior_campus`.
4. WHEN a administradora clica em **Desfazer publicação** THEN the system SHALL restaurar `campus` a partir de `anterior_campus` junto das demais tabelas.
5. WHILE a prévia estiver aberta the system SHALL usar `interna_campus` como tabela `campus` da fonte candidata, e a assinatura de origem SHALL resumir `interna_campus` no lugar do `campus` publicado.
6. The system SHALL manter `MUNICIPIO` e `NOME UNIDADE DE ENSINO` fora de qualquer coluna gravada nas tabelas de ciclos/cursos; eles só alimentam o cadastro de campi.

**Independent Test**: Banco novo sem `campus` publicado; enviar CSVs de uma unidade não cadastrada; conferir `campi_sistec`/`interna_campus` com cidade e nome do CSV, prévia com indicadores diferentes de zero; salvar e publicar; conferir `campus` preenchido e painel público com os mesmos indicadores; desfazer e conferir `campus` anterior.

### P2: Resumo e tabela da prévia com o conjunto PNP

**User Story**: Como administradora, quero que o resumo e a tabela da prévia em **Atualizar dados** mostrem o que vai ser salvo, com o código da matrícula.

**Why P2**: A conferência principal agora é pelas quatro páginas; o resumo é complementar.

**Acceptance Criteria**:

1. WHEN o envio chega a `previa` THEN the system SHALL mostrar no resumo as contagens do candidato (cursos, ciclos, matrículas e matrículas de eficiência), não as do consolidado bruto.
2. WHEN a tabela da prévia é exibida THEN the system SHALL mostrar até 20 linhas do candidato, uma por matrícula, com o código da matrícula, a situação e o mês de ocorrência corrigidos, o ano-base, o código do ciclo, o curso, o tipo de curso, a modalidade e a unidade.
3. The system SHALL manter fora dessa tabela qualquer coluna pessoal (nome, CPF, e-mail, data de nascimento).
4. WHEN a execução é de baixa direta do Sistec THEN the system SHALL manter o resumo e a amostra atuais daquele fluxo.

**Independent Test**: Enviar CSVs sintéticos em que só parte das matrículas passa na regra PNP; conferir que o resumo mostra a contagem filtrada e que a amostra traz `co_matricula` e o nome do curso na mesma linha.

## Edge Cases

- IF todos os ciclos de uma unidade forem descartados por falta de modalidade THEN the system SHALL tratar a unidade como ausente no envio, preservando os dados atuais dela.
- IF o CSV de ciclos trouxer valores diferentes de `MUNICIPIO` para a mesma unidade THEN the system SHALL usar o primeiro valor não vazio na ordem dos arquivos.
- IF `interna_campus` estiver vazio no Publicar THEN the system SHALL publicar mesmo assim e manter o comportamento de junção atual (painel sem linhas para unidades sem campus).
- WHEN o Salvar recebe uma prévia cujo `interna_campus` mudou depois da montagem THEN the system SHALL recusar com o `409` de conferência desatualizada já existente.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| CPR-01 | P1: Abrir a prévia das quatro páginas | Specify | Pending |
| CPR-02 | P1: Painel público volta a funcionar | Specify | Pending |
| CPR-03 | P1: Envio e Salvar com os CSVs reais | Specify | Pending |
| CPR-04 | P1: Envio e Salvar com os CSVs reais | Specify | Pending |
| CPR-05 | P1: Unidades do envio aparecem nos indicadores | Specify | Pending |
| CPR-06 | P1: Unidades do envio aparecem nos indicadores | Specify | Pending |
| CPR-07 | P2: Resumo e tabela da prévia com o conjunto PNP | Specify | Pending |

**Detalhamento:** CPR-01 = roteamento `path_template` e KPIs da prévia (P1.1 AC1–3); CPR-02 = Store sempre no layout e teste de IDs (P1.2 AC1–3); CPR-03 = descarte de ciclos sem modalidade e aviso (P1.3 AC1–3, AC5); CPR-04 = erro de montagem da fonte com corpo JSON (P1.3 AC4); CPR-05 = cidade/nome do campus vindos do CSV (P1.4 AC1–2, AC6); CPR-06 = Publicar/Desfazer com `campus` e prévia com `interna_campus` (P1.4 AC3–5); CPR-07 = resumo e amostra do candidato (P2 AC1–4).

**Coverage:** 7 requisitos, 0 mapeados a tarefas nesta etapa.

## Project Rules & References

- Princípio I: a prévia e o painel público continuam executando o mesmo SQL; o Publicar passar a levar `campus` muda o que vai ao ar e por isso entra no teste de paridade.
- Princípio III e `RISK-008`: `MUNICIPIO` e `NOME UNIDADE DE ENSINO` são dados institucionais, não pessoais; `NOME_RESPONSAVEL` e `CPF` da planilha de ciclo continuam descartados.
- Princípio VII, `RN-21`, `RN-27`, `RN-33`: Publicar e Desfazer seguem transacionais e reversíveis; `campus` passa a fazer parte do ciclo `anterior_*`.
- `AD-001` a `AD-005`: nenhuma mudança de shell ou de tema.
- `README.md` e `TESTAR.md` devem citar que Publicar leva os campi e que ciclos sem modalidade são descartados.

## Success Criteria

- [ ] Com os CSVs reais de `Downloads/01janeiro` (verificação local, sem versionar os arquivos): envio chega a `previa`, as quatro páginas da prévia abrem com indicadores diferentes de zero, Salvar e Publicar gravam, e o painel público mostra os mesmos indicadores.
- [ ] Nenhum `ReferenceError` de callback no console do navegador nas quatro páginas públicas e nas quatro de prévia.
- [ ] `pytest tests/ -q` sem falha nova, com teste de roteamento real do Dash para a prévia e teste de IDs de `Input`/`State` para as quatro páginas.
