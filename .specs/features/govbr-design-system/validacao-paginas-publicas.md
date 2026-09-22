# Validação — extensão das páginas públicas (T65)

**Data**: 2026-09-22
**Fonte**: T58–T64 de `.specs/features/govbr-design-system/tasks.md`
**Resultado**: PASS técnico; **DS-42 permanece pendente de teste humano em celular real**.

## Ambiente e método

- Chrome em `http://127.0.0.1:8050`, com a carga sintética de `scripts/seed_sintetico.py`:
  66 cursos, 848 matrículas e 346 registros de eficiência, publicados no banco local temporariamente.
- Cada rota foi aberta em 390, 768, 1280 e 1600 px, nos temas claro e escuro. A medida foi
  `documentElement.scrollWidth <= documentElement.clientWidth`; `clientWidth` perde 15 px quando
  há barra vertical.
- Também foi conferida a largura CSS de 640 px, equivalente a zoom de 200% em uma tela de 1280 px.
  A viewport foi restaurada ao final da inspeção.

## Matriz responsiva e de interação

Em cada célula, foram encontrados menu, cartões, tabela e filtros; o tema aplicado coincidiu com o
tema solicitado. O foco por teclado foi exercitado em `/percentuais-legais`: depois de `Tab`, o
link seguinte recebeu contorno `rgb(255, 190, 46) dashed 4px`.

| Rota | Cartões | 390 claro / escuro | 768 claro / escuro | 1280 claro / escuro | 1600 claro / escuro | Zoom 200% (640 CSS) |
| --- | ---: | --- | --- | --- | --- | --- |
| `/` | 5 | PASS 375/375 | PASS 753/753 | PASS 1265/1265 | PASS 1585/1585 | PASS 625/625 |
| `/eficiencia` | 1 | PASS 375/375 | PASS 753/753 | PASS 1265/1265 | PASS 1585/1585 | PASS 625/625 |
| `/evasao` | 1 | PASS 375/375 | PASS 753/753 | PASS 1265/1265 | PASS 1585/1585 | PASS 625/625 |
| `/percentuais-legais` | 4 | PASS 375/375 | PASS 753/753 | PASS 1265/1265 | PASS 1585/1585 | PASS 625/625 |

O menu comum, a tabela rolável e o painel de filtros ficaram presentes em todas as 32 combinações
rota × largura × tema. As verificações anteriores de abertura por Enter/Espaço, fechamento por Esc,
devolução de foco e aparência do menu a partir de 992 px continuam registradas em
[verificacao-visual.md](verificacao-visual.md). As capturas da validação de cartões de Matrículas e
suas medidas ficam ligadas em [validacao-cards-matriculas.md](validacao-cards-matriculas.md).

Em Percentuais Legais, a troca de Campus para Modalidade mudou a legenda para
`Recorte exploratório por Modalidade. Os percentuais não avaliam o cumprimento da meta por grupo.`;
os quatro cartões permaneceram no conjunto filtrado. Isso confirma DS-95 sem interpretar os
recortes como aferição de meta legal.

## Paridade com a base sintética publicada

Os valores exibidos foram comparados com as funções de domínio usando a mesma base e os filtros
iniciais (`Sem FIC` quando a rota o adota; Campus/Todos). A inspeção do DOM e a chamada direta
produziram os mesmos valores.

| Rota | Indicador no DOM | Cálculo de domínio | Resultado |
| --- | --- | --- | --- |
| `/` | 848 matrículas; 855,44 equivalentes | 848 matrículas; `matriculas_equivalentes(...).sum() = 855,44` | PASS |
| `/eficiencia` | IEA 0,52 | `iea(...) = 0,52` | PASS |
| `/evasao` | Taxa de evasão anual 0,26 | `taxa_evasao(...) = 0,26` | PASS |
| `/percentuais-legais` | Técnico 0,0%; Professores 0,0%; PROEJA 0,0%; 855,44 equivalentes | `percentual_tecnico/professores/proeja = 0,0%`; equivalentes = 855,44 | PASS |

Os testes co-localizados ainda exercitam os mesmos contratos com fixtures controladas:
`tests/test_paginas_publicas.py` compara IEA, `taxa_evasao`, os três percentuais, denominadores por
grupo, estados vazios, limpar filtros e o aviso PROEJA. A carga sintética não contém recortes
Técnico, Formação de Professores ou PROEJA, por isso seus percentuais publicados são 0,0%; isso é
um dado do cenário, não ausência de cálculo.

## Gates e cutover

- `python -m compileall -q app`: PASS.
- Suíte completa dividida somente pelo limite local de temporário: 218 + 16 + 340 = **574 passed**.
- `scripts/verificar_prontidao_cutover.py`: **NO-GO de ambiente**, não falha visual: faltam
  `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` e `CALCSISTEC_HTTPS=1`. Passaram ausência de PII, schema v2,
  fatores, dataset publicado e ano-base.

## Limitações e pendências

1. Esta inspeção usa uma viewport de navegador, não um aparelho físico. **DS-42 continua bloqueado**
   até Jaline registrar dispositivo, largura e data em `CUTOVER.md`.
2. O NO-GO de cutover acima não invalida a apresentação: são configurações de ambiente que continuam
   necessárias antes de qualquer publicação.
3. A pendência anterior de query string nas páginas Dash e CSRF nos POSTs administrativos continua
   fora desta extensão, como registrado em `STATE.md` e `CUTOVER.md`.
