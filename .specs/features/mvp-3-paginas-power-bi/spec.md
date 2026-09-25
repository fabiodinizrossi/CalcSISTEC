# MVP 3 — Páginas públicas no padrão do Power BI — Specification

## Problem Statement

As 4 páginas públicas precisam ter o mesmo estilo e as mesmas funcionalidades
do painel Power BI que o CalcSISTEC substitui, com as cores e os componentes do
gov.br DS. Nos prints (`.specs/referencias/*.png`), o Power BI tem uma coluna
lateral com o logotipo no topo, o menu das páginas logo abaixo e os filtros
abaixo do menu; o conteúdo (cartões, gráficos, "Ver tabela por" e tabela) fica
à direita. Hoje o CalcSISTEC tem o menu lateral no parcial Jinja do shell e os
filtros no fim da página, abaixo da tabela. Também faltam: filtro de Ano de
Ingresso; filtros de tipo de curso, modalidade e programa em várias páginas;
os 4 cartões e o gráfico mensal da Evasão; as colunas de concluídos, evadidos e
retidos da Eficiência; os medidores e as colunas de matrículas equivalentes dos
Percentuais; e a ordem dos cartões da Matrículas.

## Goals

- [ ] Nas páginas públicas, a coluna lateral tem, de cima para baixo: logotipo da instituição (quando houver), menu das páginas e filtros da página.
- [ ] Cada página tem os filtros, cartões, gráficos e colunas da seção "O que cada página mostra".
- [ ] Todo número mostrado vem de `app/paineis/` (feature 2).
- [ ] Funciona nos temas claro e escuro, de 320 px a 1600 px, sem rolagem horizontal da página.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Cores e fonte do Power BI (amarelo, azul-marinho) | Decisão de 20/09: cores do gov.br DS. |
| Coluna lateral nas telas administrativas Jinja | Continuam com o menu do parcial Jinja (AD-001, AD-005). |
| Ícones no cabeçalho das colunas (livros, "x") | Decorativos. |
| Tokens oficiais do gov.br e botão "voltar à capa" | Spec futura. |
| Mudar regra de cálculo | Feature 2. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Quem monta a coluna lateral nas páginas públicas | O Dash, no layout de cada página, pelo componente `lateral_painel`. O parcial Jinja `_menu.html` deixa de aparecer nas páginas públicas | Os filtros são componentes do Dash e o Dash só renderiza dentro da raiz dele; menu e filtros precisam estar no mesmo bloco. Substitui AD-001 só nas páginas públicas (AD-008) | y (pedido da Jaline: filtros na lateral como no Power BI) |
| Marcação do menu do Dash | A mesma estrutura do `_menu.html` (`br-menu`, `menu-container`, `menu-panel`, `menu-header`, `menu-body`, `menu-item`, `menu-scrim`), com `id="main-navigation"` | O CSS do DS e o `style.css` atual continuam valendo sem regra nova para o menu | y |
| Abrir e fechar o menu abaixo de 992 px | O botão do cabeçalho público passa a usar `data-toggle="menu-painel"`, e os botões de fechar do menu do Dash `data-dismiss="menu-painel"`; `menu.js` trata esses atributos por delegação de eventos | O JavaScript do DS só liga os menus que existem na carga (AD-004), e o menu do Dash nasce depois; atributos próprios evitam que o DS e o `menu.js` abram e fechem ao mesmo tempo | y |
| Filtros abaixo de 992 px | Ficam num cartão no topo do conteúdo (fora do menu sobreposto), sempre visíveis | Esconder os filtros dentro do menu sobreposto os tornaria difíceis de achar no celular | y |
| Logotipo acima do menu | Aparece só quando a instituição enviou um logotipo próprio (não o genérico); `alt` com o nome da instituição | O logotipo genérico no topo da lateral pareceria placeholder | y |
| Prévia administrativa (`/admin/previa/...`) | A coluna do Dash mostra só os filtros; o menu administrativo Jinja continua | A prévia é uma tela administrativa; o menu dela leva às telas administrativas | y |
| Cartão de IEA na Eficiência | Sai; o IEA total aparece na linha Total da tabela | O Power BI não tem cartão nessa página | y |
| Botão FIC na Evasão | Fica, com padrão **Com FIC** | Decisão da Jaline em 2026-09-24; com FIC é o recorte cujos totais batem com o print | y |
| Filtro Ano de Ingresso | Controle deslizante de dois pontos, do menor ano de início de ciclo até o ano-base; na posição inicial não filtra nada | Controle do print | y |
| Ordem inicial da tabela da Evasão | Taxa, da maior para a menor, no primeiro nível | Ordem do print | y |
| Faixas de cor da taxa de evasão | Fundo pela faixa (baixa, média, alta) e o nome da faixa em texto só para leitor de tela | Cor nunca é o único sinal | y |
| Medidores dos Percentuais | Meio círculo de 0 a 100%, barra verde se atinge a meta e vermelha se não, marca da meta, valor com 1 casa, texto "Acima da meta" / "Abaixo da meta" com a meta | Regra de cor atual (`cor_medidor`) | y |
| Biblioteca dos gráficos | Plotly (`dcc.Graph`), já no projeto; cores em hexadecimal espelhando os tokens do DS | Sem dependência nova | y |

**Open questions:** none.

---

## O que cada página mostra

### Coluna lateral (todas as páginas públicas)

De cima para baixo: logotipo da instituição (se houver logotipo próprio), menu
com Matrículas, Eficiência Acadêmica, Taxa de Evasão Anual e Percentuais Legais
(a página atual marcada), título "Filtros" e os filtros da página, com
"Limpar Filtros" por último.

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

- Filtros: Ano de Ingresso, Campus, Tipo de Curso, Modalidade, Com FIC / Sem FIC (padrão Com FIC), Limpar Filtros.
- Cartões: Abandonos, Transferências externas, Desligamentos, Transferências internas.
- Gráfico de área "Matrículas evadidas por mês em {ano-base}", de janeiro a dezembro.
- "Ver tabela por", como hoje.
- Tabela: Evasões em {ano-base}, Taxa de Evasão Anual (percentual, 1 casa, fundo pela faixa), com linha Total; primeiro nível em ordem decrescente de taxa.

### Percentuais Legais (`/percentuais-legais`)

- Filtros: Campus, Tipo de Curso, Modalidade, Programa Associado, Limpar Filtros; o aviso de PROEJA aparece no conteúdo quando há filtro de programa.
- Cartão Matrículas equivalentes e 3 medidores: Técnico (meta 50%), Formação de Professores (meta 20%), Proeja (meta 10%).
- "Ver tabela por", como hoje.
- Tabela: Técnicos (MatEq), Formação de Professores (MatEq), Proeja (MatEq), % Técnico, % Formação de Professores, % Proeja, com linha Total.

---

## User Stories

### P1: Componentes compartilhados ⭐ MVP

**User Story**: Como mantenedora, quero filtro de ano, bloco de filtros, medidores e gráfico mensal como componentes, para as 4 páginas usarem os mesmos.

**Acceptance Criteria**:

1. The `app/components/cores.py` SHALL definir as cores dos gráficos, e cada valor SHALL existir em `app/static/govbr-ds/dist/core-tokens.css`.
2. WHEN `filtro_ano_ingresso(id_, ano_min, ano_max)` é criado THEN the system SHALL mostrar um controle de dois pontos com valor inicial `[ano_min, ano_max]` e o rótulo "Ano de Ingresso".
3. WHEN `ano_ingresso_do_valor(valor, ano_min, ano_max)` recebe `[ano_min, ano_max]` THEN the system SHALL devolver `None`; com outro intervalo, SHALL devolver `(inicio, fim)`.
4. WHEN `filtros_laterais(campos, id_limpar)` é criado THEN the system SHALL mostrar o título "Filtros", os campos na ordem dada, um embaixo do outro, e o botão "Limpar Filtros" por último, num contêiner com a classe `lateral-filtros`.
5. WHEN `medidor(rotulo, valor, meta)` é criado THEN the system SHALL mostrar o rótulo, um gráfico de meio círculo de 0 a 100 com o valor em percentual de 1 casa, a marca da meta, a cor de `cor_medidor`, e os textos da situação e da meta.
6. WHEN `grafico_evasoes_mes(valores, ano)` é criado THEN the system SHALL mostrar os 12 meses em português, na ordem, com um ponto por mês e a área preenchida.
7. The gráficos SHALL ter fundo transparente, sem barra de ferramentas, e textos legíveis nos temas claro e escuro.
8. WHERE `tabela_hierarquica_ds` recebe `chave_ordem`, the system SHALL ordenar o primeiro nível pelo valor dessa função, do maior para o menor.

**Independent Test**: `tests/test_componentes_publicos.py` e `tests/test_style_css.py`.

---

### P1: Coluna lateral como no Power BI ⭐ MVP

**User Story**: Como visitante do painel, quero o logotipo, o menu e os filtros na coluna da esquerda, como no painel que eu já conheço.

**Acceptance Criteria**:

1. WHEN `lateral_painel(caminho_atual, filtros, logo=...)` é criado para uma página pública THEN the system SHALL devolver, de cima para baixo: o logotipo (se `logo` não for `None`), o menu com as 4 páginas públicas e os filtros.
2. The menu do Dash SHALL ter `id="main-navigation"`, as classes do `_menu.html`, `aria-current="page"` e a classe `active` só no item da página atual, e botões de fechar com `data-dismiss="menu-painel"`.
3. WHEN `lateral_painel` é criado em modo prévia (`preview=True`) THEN the system SHALL devolver só os filtros, sem logotipo e sem menu.
4. The `tem_logo_personalizado()` (`app/data/config_store.py`) SHALL devolver `True` só quando o caminho do logotipo configurado é diferente de `DEFAULT_LOGO_PATH`.
5. WHILE a página é pública, the shell SHALL NOT renderizar o parcial `_menu.html`, e o botão de menu do cabeçalho público SHALL usar `data-toggle="menu-painel"` e `data-target="#main-navigation"`.
6. WHEN o botão do cabeçalho com `data-toggle="menu-painel"` é clicado THEN `menu.js` SHALL alternar a classe `active` do alvo e o `aria-expanded` do botão; WHEN um elemento com `data-dismiss="menu-painel"` é clicado ou `Esc` é pressionado com o menu aberto THEN `menu.js` SHALL fechar o menu e devolver o foco ao botão.
7. The telas administrativas Jinja SHALL continuar com o menu do `_menu.html` e o comportamento de hoje.
8. WHILE a largura é de 992 px ou mais, the coluna lateral SHALL ficar à esquerda do conteúdo, com a largura de hoje (`--menu-largura`), e o menu sempre aberto; WHILE é menor que 992 px, o menu SHALL ser sobreposto e fechado por padrão, e os filtros SHALL aparecer num cartão no topo do conteúdo.

**Independent Test**: `tests/test_lateral_painel.py`, `tests/test_shell_parciais.py`, `tests/test_js_menu.py`.

---

### P1: Página Matrículas como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar a coluna lateral com os filtros e os cartões da seção "O que cada página mostra", na ordem dada.
2. WHEN o Ano de Ingresso muda THEN the system SHALL recalcular cartões e tabela só com os ciclos iniciados no intervalo.
3. WHEN "Limpar Filtros" é clicado THEN the system SHALL voltar todos os filtros ao estado inicial, inclusive o Ano de Ingresso ao intervalo completo.
4. The números SHALL vir de `resumo_matriculas` e `metricas_matriculas`.

### P1: Página Eficiência como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar a coluna lateral com os filtros e as colunas da seção "O que cada página mostra" e SHALL NOT mostrar cartão.
2. The IEA SHALL aparecer em percentual com 2 casas (ex.: `41,44%`).
3. The números SHALL vir de `metricas_eficiencia`.

### P1: Página Evasão como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar a coluna lateral com os filtros (inclusive Com FIC / Sem FIC, padrão Com FIC), os 4 cartões, o gráfico mensal e as colunas da seção "O que cada página mostra".
2. The tabela SHALL começar ordenada pela taxa, da maior para a menor, no primeiro nível.
3. The célula da taxa SHALL ter a classe da faixa e o nome da faixa em texto visível só para leitor de tela.
4. The números SHALL vir de `resumo_evasao`, `evasoes_por_mes` e `metricas_evasao`.

### P1: Página Percentuais como no Power BI ⭐ MVP

**Acceptance Criteria**:

1. The página SHALL mostrar a coluna lateral com os filtros, o cartão, os 3 medidores e as colunas da seção "O que cada página mostra".
2. WHEN há filtro de Programa Associado THEN the system SHALL mostrar o aviso de possível distorção do percentual PROEJA no conteúdo.
3. The números SHALL vir de `resumo_percentuais` e `metricas_percentuais`.

### P1: Conferência no navegador ⭐ MVP

**Acceptance Criteria**:

1. The `TESTAR.md` SHALL ter um roteiro por página que compara com o print correspondente de `.specs/referencias/`.
2. WHEN Jaline conclui a conferência THEN `DEPLOY.md` SHALL registrar navegador, larguras e data no item DS-42.

---

## Edge Cases

- IF o banco não tem ciclo com data de início THEN o filtro de Ano de Ingresso SHALL usar o ano-base como mínimo e máximo.
- IF um filtro deixa a página sem dados THEN os cartões SHALL mostrar 0 e a tabela SHALL mostrar "Sem dados para os filtros selecionados.".
- WHEN a página abre em modo prévia THEN os filtros, cartões, gráficos e tabelas SHALL funcionar igual, lendo a fonte da prévia.
- IF o JavaScript não carrega THEN o menu SHALL continuar visível como lista de links (regra `.ds-sem-js` de hoje) e os filtros SHALL continuar no lugar.
- IF o ano-base não tem evasão num mês THEN o gráfico SHALL mostrar 0 nesse mês.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| PBI-01 | Componentes — AC1 (cores) | Tasks | Pending |
| PBI-02 | Componentes — AC2, AC3 (ano de ingresso) | Tasks | Pending |
| PBI-03 | Componentes — AC4 (bloco de filtros) | Tasks | Pending |
| PBI-04 | Componentes — AC5, AC6, AC7 (gráficos) | Tasks | Pending |
| PBI-05 | Componentes — AC8 (ordem da tabela) | Tasks | Pending |
| PBI-06 | Lateral — AC4 (logotipo personalizado) | Tasks | Pending |
| PBI-07 | Lateral — AC1, AC2, AC3 (componente) | Tasks | Pending |
| PBI-08 | Lateral — AC5, AC7 (shell) | Tasks | Pending |
| PBI-09 | Lateral — AC6 (`menu.js`) | Tasks | Pending |
| PBI-10 | Lateral — AC8; Componentes — AC7 (CSS) | Tasks | Pending |
| PBI-11 | Matrículas — AC1..AC4 | Tasks | Pending |
| PBI-12 | Eficiência — AC1..AC3 | Tasks | Pending |
| PBI-13 | Evasão — AC1..AC4 | Tasks | Pending |
| PBI-14 | Percentuais — AC1..AC3 | Tasks | Pending |
| PBI-15 | Conferência — AC1, AC2 | Tasks | Pending |

**Coverage:** 15 total, 15 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `python -m pytest -q` verde.
- [ ] Jaline confere as 4 páginas contra os prints e registra no `DEPLOY.md` (DS-42).
