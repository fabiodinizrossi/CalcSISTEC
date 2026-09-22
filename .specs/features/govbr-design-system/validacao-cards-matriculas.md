# Validação — melhoria da hierarquia visual dos cards de Matrículas

**Data**: 2026-09-22
**Fonte**: `.specs/features/govbr-design-system/tarefa-cards-matriculas.md`
**Resultado**: PASS

## Resumo

Atualiza intencionalmente a apresentação dos cinco KPIs da página inicial (Matrículas): título acima do
valor, alinhamento à esquerda, destaque exclusivo do card "Matrículas" e valores em 32px semibold,
mantendo os cálculos, filtros e estados de dados existentes.

## Arquivos alterados

| Arquivo | Mudança |
| ------- | ------- |
| `app/pages/matriculas.py` | `_kpi` passa a montar `.rotulo` antes de `.valor`, aceita `destaque` (classe `kpi-figma--destaque`) e marca estados textuais com `valor--texto`; reordena os KPIs (Cursos, Matrículas, Ingressantes, Matrículas concluídas, Matrículas equivalentes) |
| `app/assets/style.css` | `.kpi-figma` reescrito (padding 24px, raio 8px, borda suave, sem sombra, título 14px acima, valor 32px/600 à esquerda); `.kpi-figma--destaque` com fundo azul suave e valor azul institucional (claro) + regras próprias para o tema escuro; `.valor--texto` para "dado incompleto" sem herdar os 32px |
| `tests/test_paginas_publicas.py` | atualiza a ordem/texto dos KPIs e a checagem de classes; acrescenta teste do estado textual |

## Gate

- `python -m pytest tests/test_style_css.py tests/test_paginas_publicas.py` → **66 passed**.
- Suíte completa: **558 passed, 2 failed** — os 2 falhos são de `tests/test_js_ordenacao_tabelas.py`
  (feature de ordenação de tabelas em andamento, não rastreada nesta tarefa; falha de encoding de
  em-dash pré-existente, sem relação com os cards). Os arquivos desta tarefa passam 100%.

## Critérios de aceite — evidência no DOM (Playwright, Chromium)

Capturas em `.specs/features/govbr-design-system/capturas/` (`kpis-{tema}-{largura}.png`) e medidas em `capturas/resumo.json`.

| AC | Medição | Status |
| -- | ------- | ------ |
| Ordem Cursos → Matrículas → Ingressantes → Matrículas concluídas → Matrículas equivalentes | `resumo.json` lista os rótulos nesta ordem, em todas as larguras/temas | PASS |
| Título acima do valor, alinhado à esquerda | `align-items: flex-start`; DOM `.rotulo` antes de `.valor` (`tests/test_paginas_publicas.py`) | PASS |
| Só "Matrículas" com destaque | classe `kpi-figma--destaque` apenas no 2º card | PASS |
| Destaque perceptível nos dois temas | claro: bg `color(srgb 0.925961 0.945412 0.976471)` + valor `rgb(19,81,180)`; escuro: bg `rgb(12,50,111)` + valor `rgb(197,212,235)` | PASS |
| Valor 32px / 600, título 14px | `valor_font: 32px`, `valor_weight: 600`, `rotulo_font: 14px` | PASS |
| Padding 24px, raio 8px, borda suave, sem sombra | `padding: 24px`, `radius: 8px`, borda `1px solid var(--border-color)` (não há `box-shadow` no bloco) | PASS |
| Contraste (≥4,5:1 texto; ≥3:1 números grandes) | claro: `#1351b4` sobre `#ECF1F9` ≈ 5,5:1 (AA); escuro: `#c5d4eb` sobre `#0c326f` ≈ 8,7:1; cards normais `--color` sobre `--background` ≥ 12:1 | PASS |
| `0` real preservado | card "Matrículas concluídas" mostra `0` em `32px`, cor neutra | PASS |
| "dado incompleto" sem truncar nem herdar 32px | classe `valor--texto` (14px regular), coberto por teste | PASS |
| Grade sem rolagem horizontal em 390/768/1280/1600 | `scroll` (scrollWidth−clientWidth) == 0 em todas as larguras/temas; 5 cards numa linha a 1280/1600, reempilham abaixo | PASS |
| DOM acompanha a ordem visual | lista de cards no DOM segue a ordem definida (`resumo.json`) | PASS |
| Sem regressão nas demais páginas | `test_paginas_publicas.py` (eficiência, evasão, percentuais) e `test_style_css.py` passam | PASS |

## Observações e limitações

1. **Zoom de 200%** não foi capturado por screenshot; a grade usa `repeat(auto-fit, minmax(150px, 1fr))`
   (mesmo mecanismo anterior), então os cards reempilham e não geram rolagem horizontal. O valor usa
   `overflow-wrap: anywhere` para não estourar a largura.
2. A ordem visual/dom foi conferida com o dataset real local (`app/data/sistec.db`, 848 matrículas); os
   valores exibidos (63 cursos, 848 matrículas etc.) são os do ambiente de desenvolvimento, não dados
   publicados.
3. Não foram adicionados percentuais/tendências/comparações nem linha de ajuda para "Matrículas
   equivalentes" (opcional na tarefa) — nenhum dado que os sustente foi solicitado.
4. A cor do valor em destaque no tema escuro usa `--interactive` (par `-dark`), que resolve para
   `#c5d4eb` — mesmo valor de `--color-primary-pastel-01`, mas com a semântica correta de token interativo
   para o tema escuro.

## Nada a fazer além disso

A tarefa não inclui publicação ou deploy. As alterações ficam para revisão junto das capturas.
