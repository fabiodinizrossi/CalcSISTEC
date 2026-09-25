# MVP 2 — Paridade numérica com o Power BI — Specification

## Problem Statement

O Power BI só pode ser desligado quando os números do CalcSISTEC baterem com os
dele (Princípio I). Hoje só o total de matrículas foi comparado (16.832 contra
16.750 no export `Downloads/08agosto`), e várias medidas que o Power BI mostra
nem são calculadas pelo CalcSISTEC: evasões por tipo e por mês, concluídos,
evadidos e retidos por ciclo, matrículas equivalentes por recorte legal. Além
disso, os números de cada página são calculados dentro dos callbacks do Dash,
o que impede um script de gerar os mesmos números para comparar.

Referência visual e numérica: `.specs/referencias/*.png` (prints do Power BI de
2025). A comparação da campanha usa o export de agosto, carregado no Power BI e
no CalcSISTEC no mesmo dia.

## Goals

- [ ] `app/paineis/` calcula, sem Dash, cada número que o Power BI mostra nas 4 páginas.
- [ ] `scripts/paridade.py gerar` monta, a partir de uma pasta de export, uma planilha com todos esses números e uma coluna em branco para o Power BI.
- [ ] `scripts/paridade.py comparar` aponta cada diferença sem causa registrada.
- [ ] Toda diferença do export de agosto tem causa registrada em `relatorio-paridade.md` e aceita por Jaline.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Mudar o visual das páginas | Feature 3. Aqui as páginas não mudam; a feature 3 passa a usar `app/paineis/`. |
| Comparar recortes além dos padrões (ex.: cada filtro de tipo de curso) | O padrão de cada página cobre todas as regras; filtros só recortam linhas. |
| Tornar a comparação automática contra o Power BI | O Power BI não tem API aberta aqui; a PI digita os valores. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Nova camada `app/paineis/` | Funções puras (só pandas e `app/domain/`) que montam os números de cada página; usadas pelas páginas (feature 3) e por `scripts/paridade.py` | Garante que o script compara exatamente o que a página mostra. Exige emenda do Princípio II (PROJECT_RULES 1.4.0) e AD-007 | y (decisão do plano) |
| Categorias de evasão do Power BI | Abandonos = `ABANDONO`; Transferências externas = `TRANSF_EXT`; Desligamentos = `DESLIGADO`, `DESLIGADA`, `REPROVADO`, `REPROVADA`; Transferências internas = `TRANSF_INT` | No print de 2025, 1.511 + 247 + 462 + 0 = 2.220, igual ao total de evasões; as 4 categorias particionam `STATUS_EVADIDO` | n (confirmar na campanha) |
| Evasões por mês | Matrículas evadidas cujo mês de ocorrência (`MES_DE_OCORRENCIA`) cai no ano-base, contadas por mês | O gráfico do Power BI se chama "Matrículas evadidas por mês em 2025" | n (confirmar na campanha) |
| Ano de Ingresso | Ano de `dt_data_inicio` do ciclo | O Sistec não traz a data da matrícula; mesma aproximação de "Ingressantes" | n (confirmar na campanha) |
| Recorte padrão de cada página | Matrículas: com FIC e sem FIC; Eficiência: sem FIC; Evasão: com FIC (a página do Power BI não tem o botão FIC); Percentuais: com FIC | São os estados dos prints | y |
| Formato da planilha | CSV com `;`, UTF-8 com BOM, números no formato brasileiro (`22.302`, `16.278,68`, `41,44%`) | Abre direto no Excel da PI e aceita colar os números do Power BI como aparecem | y |
| Precisão da comparação | O valor do CalcSISTEC é arredondado para o número de casas decimais do valor digitado do Power BI antes de subtrair | O Power BI mostra valores arredondados | y |
| Banco usado pelo script | Um banco temporário criado pelo próprio script no diretório temporário do sistema; `app/data/sistec.db` nunca é lido nem escrito | Não misturar a conferência com os dados publicados | y |

**Open questions:** none.

---

## User Stories

### P1: Números de cada página calculados fora do Dash ⭐ MVP

**User Story**: Como mantenedora, quero uma função por página que devolva os
números que a página mostra, para testar e comparar sem abrir o navegador.

**Acceptance Criteria**:

1. The `app/paineis/` SHALL importar só a biblioteca padrão, `pandas` e `app/domain/`.
2. WHEN `resumo_matriculas(df, ano_base, filtros)` é chamada THEN the system SHALL devolver `cursos`, `matriculas`, `equivalentes`, `concluidas` e `ingressantes`, calculados como a página Matrículas calcula hoje.
3. WHEN `metricas_matriculas(grupo)` é chamada THEN the system SHALL devolver `total`, `concluidas`, `integralizadas`, `em_curso` e `evasoes` do grupo.
4. WHEN `resumo_eficiencia(df, filtros)` ou `metricas_eficiencia(grupo)` é chamada THEN the system SHALL devolver `iea`, `concluidos`, `evadidos` e `retidos`.
5. WHEN `resumo_evasao(df, ano_base, filtros)` é chamada THEN the system SHALL devolver `abandonos`, `transferencias_externas`, `desligamentos`, `transferencias_internas`, `evasoes`, `matriculas` e `taxa`, com `abandonos + transferencias_externas + desligamentos + transferencias_internas == evasoes`.
6. WHEN `evasoes_por_mes(df, ano_base, filtros)` é chamada THEN the system SHALL devolver uma lista de 12 inteiros, de janeiro a dezembro.
7. WHEN `resumo_percentuais(df, ano_base, filtros)` ou `metricas_percentuais(grupo)` é chamada THEN the system SHALL devolver `equivalentes`, `tecnico_mateq`, `professores_mateq`, `proeja_mateq`, `pct_tecnico`, `pct_professores` e `pct_proeja`.
8. WHEN `tabela_por(df, coluna, metricas)` é chamada THEN the system SHALL devolver uma linha por valor da coluna, em ordem alfabética, mais uma linha `Total` calculada sobre o `df` inteiro.
9. IF o `df` filtrado fica vazio THEN the system SHALL devolver zeros (nunca erro, nunca NaN) e `equivalentes = None` em `resumo_matriculas`, como a página faz hoje.

**Independent Test**: testes unitários em `tests/test_paineis_*.py` com DataFrames sintéticos e números esperados calculados à mão.

---

### P1: Filtros comuns a todas as páginas ⭐ MVP

**User Story**: Como mantenedora, quero um único jeito de aplicar os filtros da
tela aos dados, para que página e script filtrem igual.

**Acceptance Criteria**:

1. The system SHALL oferecer `FiltrosPainel(campus, tipo_curso, programa, modalidade, incluir_fic, ano_ingresso)`, todos opcionais, `incluir_fic=True` por padrão.
2. WHEN um filtro de texto é `None` THEN the system SHALL não filtrar por ele.
3. WHEN `ano_ingresso=(inicio, fim)` THEN the system SHALL manter só as linhas com ano de `dt_data_inicio` entre `inicio` e `fim`, inclusive, e SHALL descartar as linhas com `dt_data_inicio` nulo.
4. IF `ano_ingresso` está definido e o `df` não tem `dt_data_inicio` THEN the system SHALL levantar `ValueError("ano_ingresso exige dt_data_inicio")`.
5. WHEN `incluir_fic=False` THEN the system SHALL aplicar `app.domain.matriculas.filtrar_fic(df, False)`.

**Independent Test**: `tests/test_paineis_filtros.py`.

---

### P1: Regras novas no domínio, com teste de paridade ⭐ MVP

**User Story**: Como mantenedora, quero as regras novas (categorias de evasão,
evasões por mês, equivalentes por recorte) no domínio puro, com teste, como o
Princípio I exige.

**Acceptance Criteria**:

1. The `app/domain/shared.py` SHALL definir `CATEGORIAS_EVASAO` com as 4 categorias da tabela de Assumptions, e a união delas SHALL ser igual a `STATUS_EVADIDO`, sem interseção entre categorias.
2. WHEN `contar_evasoes_por_categoria(df, filtros)` é chamada THEN the system SHALL devolver um dict com as 4 categorias, contando `status_corrigido` no ano-base.
3. WHEN `evasoes_por_mes(df, filtros)` (domínio) é chamada THEN the system SHALL contar só evadidos cujo mês de ocorrência cai no ano-base, ignorando mês nulo ou inválido.
4. WHEN `equivalentes_por_recorte(df)` é chamada THEN the system SHALL devolver `total`, `tecnico`, `professores` e `proeja`, e `tecnico / total` SHALL ser igual a `percentual_tecnico(df)` (o mesmo para os outros dois).
5. IF o `df` está vazio THEN as três funções SHALL devolver zeros sem erro.
6. The `app/data/consulta.carregar_eficiencia` SHALL trazer também `tipo_curso_pnp` e `tipo_programa_curso` (nas duas consultas SQL da função).

**Independent Test**: `tests/test_parity_dominio.py` (casos novos) e `tests/test_consulta.py`.

---

### P1: Planilha de paridade ⭐ MVP

**User Story**: Como PI, quero rodar um comando sobre a pasta do export e receber
uma planilha com os números do CalcSISTEC e um espaço para os do Power BI, para
conferir número a número.

**Acceptance Criteria**:

1. WHEN `python scripts/paridade.py gerar --pasta DIR --ano-base N --saida ARQ.csv` roda com uma pasta que tem `ciclos/` e `matriculas/` THEN the system SHALL gravar `ARQ.csv` com as colunas `pagina;recorte;linha;indicador;calcsistec;powerbi;diferenca;causa`.
2. The planilha SHALL ter as linhas da seção "Linhas da planilha", nesta ordem.
3. The system SHALL NOT ler nem escrever `app/data/sistec.db` (usa banco temporário, apagado no fim).
4. WHEN `python scripts/paridade.py comparar --arquivo ARQ.csv` roda THEN the system SHALL preencher `diferenca` em toda linha com `powerbi` preenchido e regravar o arquivo.
5. IF alguma linha tem `diferenca` diferente de zero e `causa` vazia THEN `comparar` SHALL listar essas linhas e sair com código 1.
6. IF alguma linha tem `powerbi` vazio THEN `comparar` SHALL dizer quantas faltam e sair com código 2.
7. WHEN todas as linhas têm `powerbi` e toda diferença é zero ou tem causa THEN `comparar` SHALL sair com código 0.
8. IF `--pasta` não tem `ciclos/` ou `matriculas/` THEN `gerar` SHALL sair com código 2 e dizer qual subpasta falta.

**Independent Test**: `tests/test_paridade_script.py` com pastas sintéticas feitas por `scripts/sintetico.py`.

---

### P1: Campanha de paridade do export de agosto ⭐ MVP

**User Story**: Como responsável, quero cada diferença entre CalcSISTEC e Power BI
explicada e aceita antes de desligar o Power BI.

**Acceptance Criteria**:

1. The `.specs/features/mvp-2-paridade/paridade-08agosto.csv` SHALL ter a coluna `powerbi` preenchida pela PI com o export de agosto.
2. WHEN a diferença vem de bug do CalcSISTEC THEN the system SHALL ganhar um teste que reproduz o bug e a correção, e a linha SHALL ficar com diferença zero.
3. WHEN a diferença vem de regra diferente e aceita THEN `relatorio-paridade.md` SHALL registrar a causa, os números e o aceite de Jaline com data.
4. The `python scripts/paridade.py comparar --arquivo .specs/features/mvp-2-paridade/paridade-08agosto.csv` SHALL sair com código 0 ao fim da campanha.

**Independent Test**: rodar o `comparar` sobre a planilha final.

---

## Linhas da planilha

`recorte` indica o estado do filtro FIC. `linha` é `KPI`, `Mês`, o nome do campus
ou `Total`. Casas decimais do `calcsistec`: inteiros sem casa; matrículas
equivalentes com 2; IEA e percentuais de tabela com 2 (ex.: `41,44%`); taxa de
evasão com 1 (`16,5%`); medidores de Percentuais com 1 (`45,4%`).

| pagina | recorte | linha | indicadores |
| --- | --- | --- | --- |
| Matrículas | com_fic | KPI | Cursos, Matrículas, Matrículas equivalentes, Matrículas concluídas, Ingressantes |
| Matrículas | com_fic | cada campus, depois Total | Total de Matrículas, Concluídas, Integralizadas, Em Curso, Evasões |
| Matrículas | sem_fic | KPI | os mesmos 5 |
| Matrículas | sem_fic | cada campus, depois Total | os mesmos 5 |
| Eficiência Acadêmica | sem_fic | cada campus, depois Total | Índice de Eficiência Acadêmica, Concluídos por Ciclo, Evadidos por Ciclo, Retidos por Ciclo |
| Taxa de Evasão Anual | com_fic | KPI | Abandonos, Transferências externas, Desligamentos, Transferências internas |
| Taxa de Evasão Anual | com_fic | Mês | janeiro, fevereiro, …, dezembro |
| Taxa de Evasão Anual | com_fic | cada campus, depois Total | Evasões no ano, Taxa de Evasão Anual |
| Percentuais Legais | com_fic | KPI | Matrículas equivalentes, % Técnico, % Formação de Professores, % Proeja |
| Percentuais Legais | com_fic | cada campus, depois Total | Técnicos (MatEq), Formação de Professores (MatEq), Proeja (MatEq), % Técnico, % Formação de Professores, % Proeja |

---

## Edge Cases

- IF uma célula `powerbi` tem texto que não é número (ex.: `-`, `n/d`) THEN `comparar` SHALL tratá-la como vazia e contá-la entre as que faltam.
- WHEN o Power BI mostra célula em branco (ex.: Integralizadas sem valor) THEN a PI SHALL digitar `0`, e o `calcsistec` SHALL mostrar `0`.
- IF um campus existe só num dos dois painéis THEN a PI SHALL acrescentar a linha que falta com `calcsistec` vazio ou `powerbi` `0`, e a diferença SHALL ter causa.
- WHEN o ano-base não tem nenhuma evasão num mês THEN a linha do mês SHALL ter `0`.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| PAR-01 | Regras novas — AC6 (`carregar_eficiencia`) | Tasks | Pending |
| PAR-02 | Regras novas — AC1, AC2, AC5 (categorias de evasão) | Tasks | Pending |
| PAR-03 | Regras novas — AC3, AC5 (evasões por mês) | Tasks | Pending |
| PAR-04 | Regras novas — AC4, AC5 (equivalentes por recorte) | Tasks | Pending |
| PAR-05 | Filtros — AC1..AC5 | Tasks | Pending |
| PAR-06 | Painéis — AC1, AC8, AC9 (`tabela_por`, camada pura) | Tasks | Pending |
| PAR-07 | Painéis — AC2, AC3 (Matrículas) | Tasks | Pending |
| PAR-08 | Painéis — AC4 (Eficiência) | Tasks | Pending |
| PAR-09 | Painéis — AC5, AC6 (Evasão) | Tasks | Pending |
| PAR-10 | Painéis — AC7 (Percentuais) | Tasks | Pending |
| PAR-11 | Emenda do Princípio II e AD-007 | Tasks | Pending |
| PAR-12 | Planilha — AC1, AC3, AC8 (montar base) | Tasks | Pending |
| PAR-13 | Planilha — AC1, AC2 (gerar) | Tasks | Pending |
| PAR-14 | Planilha — AC4..AC7 (comparar) | Tasks | Pending |
| PAR-15 | Campanha — AC1..AC4 | Tasks | Pending |

**Coverage:** 15 total, 15 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `python -m pytest -q` verde com os testes novos.
- [ ] `scripts/paridade.py gerar` roda sobre `Downloads/08agosto` e o total de Matrículas (com FIC) é 16.832, como na medição de 2026-09-24.
- [ ] `scripts/paridade.py comparar` sai com 0 sobre a planilha final da campanha.
