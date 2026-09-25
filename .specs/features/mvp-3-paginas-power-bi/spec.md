# MVP 3 — Páginas públicas no padrão do Power BI — Specification

## Problem Statement

As 4 páginas públicas precisam ter o mesmo estilo e as mesmas funcionalidades
do painel Power BI que o CalcSISTEC substitui, com as cores e os componentes do
gov.br DS. Comparando com os prints (`.specs/referencias/*.png`), faltam:
filtro de Ano de Ingresso; filtros de tipo de curso, modalidade e programa em
várias páginas; os 4 cartões e o gráfico mensal da Evasão; as colunas de
concluídos, evadidos e retidos da Eficiência; os medidores e as colunas de
matrículas equivalentes dos Percentuais; e a ordem dos cartões da Matrículas.
Os filtros hoje ficam no fim da página, abaixo da tabela.

## Goals

- [ ] Cada página tem os filtros, cartões, gráficos e colunas da seção "O que cada página mostra".
- [ ] Todo número mostrado vem de `app/paineis/` (feature 2), então a página mostra o que a planilha de paridade conferiu.
- [ ] Funciona nos temas claro e escuro, e de 320 px a 1600 px, sem rolagem horizontal da página.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Cores e fonte do Power BI (amarelo, azul-marinho) | Decisão de 20/09: cores do gov.br DS. |
| Menu lateral com os filtros dentro, como no Power BI | O menu lateral é do shell gov.br (AD-005); os filtros ficam numa barra no topo do conteúdo. |
| Ícones no cabeçalho das colunas (livros, "x") | Decorativos; não mudam a leitura. |
| Tokens oficiais do gov.br e botão "voltar à capa" | Spec futura. |
| Mudar regra de cálculo | Feature 2. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Lugar dos filtros | Barra de filtros logo abaixo do título, antes dos cartões, em todas as páginas; quebra em várias linhas em tela estreita | O menu do shell já ocupa a coluna lateral; filtro no topo é visível sem rolar, como no Power BI | n (Jaline pode pedir outro lugar na revisão) |
| Filtro Ano de Ingresso | Controle deslizante de dois pontos, do menor ano de início de ciclo até o ano-base; na posição inicial não filtra nada | É o controle do print; na posição inicial todas as linhas contam, inclusive as sem data | y |
| Cartão de IEA na Eficiência | Sai; o IEA total aparece na linha Total da tabela | O Power BI não tem cartão nessa página | y |
| Botão FIC na Evasão | Sai; a página considera sempre com FIC | O Power BI não tem esse botão na Evasão, e os totais do print batem com "com FIC" | y |
| Ordem inicial da tabela da Evasão | Taxa de evasão, da maior para a menor, no primeiro nível | É a ordem do print | y |
| Faixas de cor da taxa de evasão | Mantém as 3 faixas atuais (baixa, média, alta), com fundo por faixa e o nome da faixa em texto só para leitor de tela | Cor nunca é o único sinal (acessibilidade), e a tabela fica limpa como no print | y |
| Medidores dos Percentuais | Meio círculo de 0 a 100%, barra verde se atinge a meta e vermelha se não, marca da meta, valor com 1 casa, e o texto "Acima da meta" / "Abaixo da meta" com a meta | Regra de cor atual (`cor_medidor`); texto garante leitura sem cor | y |
| Biblioteca dos gráficos | Plotly (`dcc.Graph`), já presente no projeto; cores passadas em hexadecimal espelhando os tokens do DS | Sem dependência nova | y |

**Open questions:** none.

---

## O que cada página mostra

### Matrículas (`/`)

- Filtros: Ano de Ingresso, Campus, Tipo de Curso, Tipo de Programa, Com FIC / Sem FIC (padrão Com FIC), Limpar Filtros.
- Cartões, nesta ordem: Cursos, Matrículas, Matrículas equivalentes, Matrículas concluídas, Ingressantes.
- "Ver tabela por" (Campus, Tipo de Curso, Oferta (Técnico), Nome do Curso, Modalidade, Ciclo), como hoje.
- Tabela: Total de Matrículas, Concluídas, Integralizadas, Em Curso, Evasões, com linha Total, como hoje.

### Eficiência Acadêmica (`/eficiencia`)

- Filtros: Campus, Tipo de Curso, Modalidade, Programa, Com FIC / Sem FIC (padrão Sem FIC), Limpar Filtros.
- Sem cartões.
- "Ver tabela por", como hoje.
- Tabela: Índice de Eficiência Acadêmica (percentual, 2 casas), Concluídos por Ciclo, Evadidos por Ciclo, Retidos por Ciclo, com linha Total.

### Taxa de Evasão Anual (`/evasao`)

- Filtros: Ano de Ingresso, Campus, Tipo de Curso, Modalidade, Limpar Filtros.
- Cartões: Abandonos, Transferências externas, Desligamentos, Transferências internas.
- Gráfico de área "Matrículas evadidas por mês em {ano-base}", de janeiro a dezembro.
- "Ver tabela por", como hoje.
- Tabela: Evasões em {ano-base}, Taxa de Evasão Anual (percentual, 1 casa, fundo pela faixa), com linha Total; primeiro nível em ordem decrescente de taxa.

### Percentuais Legais (`/percentuais-legais`)

- Filtros: Campus, Tipo de Curso, Modalidade, Programa Associado, Limpar Filtros; o aviso de PROEJA continua aparecendo quando há filtro de programa.
- Cartão Matrículas equivalentes e 3 medidores: Técnico (meta 50%), Formação de Professores (meta 20%), Proeja (meta 10%).
- "Ver tabela por", como hoje.
- Tabela: Técnicos (MatEq), Formação de Professores (MatEq), Proeja (MatEq), % Técnico, % Formação de Professores, % Proeja, com linha Total.

---

## User Stories

### P1: Componentes compartilhados ⭐ MVP

**User Story**: Como mantenedora, quero a barra de filtros, o filtro de ano, os
medidores e o gráfico mensal como componentes, para as 4 páginas usarem o mesmo.

**Acceptance Criteria**:

1. The `app/components/cores.py` SHALL definir as cores usadas nos gráficos, e cada valor SHALL existir em `app/static/govbr-ds/dist/core-tokens.css`.
2. WHEN `filtro_ano_ingresso(id_, ano_min, ano_max)` é criado THEN the system SHALL mostrar um controle de dois pontos com valor inicial `[ano_min, ano_max]` e o rótulo "Ano de Ingresso".
3. WHEN `ano_ingresso_do_valor(valor, ano_min, ano_max)` recebe `[ano_min, ano_max]` THEN the system SHALL devolver `None`; com outro intervalo, SHALL devolver a tupla `(inicio, fim)`.
4. WHEN `barra_filtros(campos, id_limpar)` é criada THEN the system SHALL mostrar os campos na ordem dada e o botão "Limpar Filtros" por último, dentro de um contêiner com a classe `barra-filtros`.
5. WHEN `medidor(rotulo, valor, meta)` é criado THEN the system SHALL mostrar o rótulo, um gráfico de meio círculo de 0 a 100 com o valor em percentual de 1 casa, a marca da meta, a cor de `cor_medidor`, e os textos da situação e da meta.
6. WHEN `grafico_evasoes_mes(valores, ano)` é criado THEN the system SHALL mostrar os 12 meses em português, na ordem, com um ponto por mês e a área preenchida.
7. The gráficos SHALL ter fundo transparente, sem barra de ferramentas, e textos legíveis nos temas claro e escuro.
8. WHERE `tabela_hierarquica_ds` recebe `chave_ordem`, the system SHALL ordenar o primeiro nível pelo valor dessa função, do maior para o menor.

**Independent Test**: `tests/test_componentes_publicos.py` (casos novos) e `tests/test_style_css.py`.

---

### P1: Página Matrículas como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar os filtros e os cartões da seção "O que cada página mostra", na ordem dada.
2. WHEN o Ano de Ingresso muda THEN the system SHALL recalcular cartões e tabela só com os ciclos iniciados no intervalo.
3. WHEN "Limpar Filtros" é clicado THEN the system SHALL voltar todos os filtros ao estado inicial, inclusive o Ano de Ingresso ao intervalo completo.
4. The números SHALL vir de `resumo_matriculas` e `metricas_matriculas` (`app/paineis/matriculas.py`).

### P1: Página Eficiência como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar os filtros e as colunas da seção "O que cada página mostra" e SHALL NOT mostrar cartão.
2. The IEA SHALL aparecer em percentual com 2 casas (ex.: `41,44%`).
3. The números SHALL vir de `metricas_eficiencia` (`app/paineis/eficiencia.py`).

### P1: Página Evasão como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar os filtros, os 4 cartões, o gráfico mensal e as colunas da seção "O que cada página mostra", e SHALL NOT mostrar o botão FIC.
2. The tabela SHALL começar ordenada pela taxa, da maior para a menor, no primeiro nível.
3. The célula da taxa SHALL ter a classe da faixa e o nome da faixa em texto visível só para leitor de tela.
4. The números SHALL vir de `resumo_evasao`, `evasoes_por_mes` e `metricas_evasao` (`app/paineis/evasao.py`).

### P1: Página Percentuais como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar os filtros, o cartão, os 3 medidores e as colunas da seção "O que cada página mostra".
2. WHEN há filtro de Programa Associado THEN the system SHALL continuar mostrando o aviso de possível distorção do percentual PROEJA.
3. The números SHALL vir de `resumo_percentuais` e `metricas_percentuais` (`app/paineis/percentuais.py`).

### P1: Conferência no navegador ⭐ MVP

**Acceptance Criteria**:

1. The `TESTAR.md` SHALL ter um roteiro por página que compara com o print correspondente de `.specs/referencias/`.
2. WHEN Jaline conclui a conferência THEN `DEPLOY.md` SHALL registrar navegador, larguras e data no item DS-42.

---

## Edge Cases

- IF o banco não tem ciclo com data de início THEN o filtro de Ano de Ingresso SHALL usar o ano-base como mínimo e máximo, e a página SHALL continuar funcionando.
- IF um filtro deixa a página sem dados THEN os cartões SHALL mostrar 0 e a tabela SHALL mostrar a mensagem "Sem dados para os filtros selecionados.".
- WHEN a página abre em modo prévia (`/admin/previa/<id>/...`) THEN tudo acima SHALL funcionar igual, lendo a fonte da prévia.
- IF o ano-base não tem evasão num mês THEN o gráfico SHALL mostrar 0 nesse mês.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| PBI-01 | Componentes — AC1 (cores) | Tasks | Pending |
| PBI-02 | Componentes — AC2, AC3 (ano de ingresso) | Tasks | Pending |
| PBI-03 | Componentes — AC4 (barra de filtros) | Tasks | Pending |
| PBI-04 | Componentes — AC5, AC6, AC7 (gráficos) | Tasks | Pending |
| PBI-05 | Componentes — AC8 (ordem da tabela) | Tasks | Pending |
| PBI-06 | Componentes — AC7 (CSS dos gráficos e da barra) | Tasks | Pending |
| PBI-07 | Matrículas — AC1..AC4 | Tasks | Pending |
| PBI-08 | Eficiência — AC1..AC3 | Tasks | Pending |
| PBI-09 | Evasão — AC1..AC4 | Tasks | Pending |
| PBI-10 | Percentuais — AC1..AC3 | Tasks | Pending |
| PBI-11 | Conferência — AC1, AC2 | Tasks | Pending |

**Coverage:** 11 total, 11 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `python -m pytest -q` verde.
- [ ] Jaline confere as 4 páginas contra os prints e registra no `DEPLOY.md` (DS-42).
