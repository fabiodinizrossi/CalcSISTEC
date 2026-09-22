# Tarefa: melhorar a hierarquia visual dos cards de Matrículas

**Status:** pronta para implementação por outra pessoa ou agente.
**Feature:** `govbr-design-system`.
**Página:** `/` (Matrículas).
**Origem:** proposta de storytelling de dados solicitada em 21/09/2026, a partir da captura do dashboard.

## Objetivo

Facilitar a leitura dos cinco indicadores, destacar o volume de matrículas e manter a identidade institucional inspirada no GovBR. Hoje todos os cards têm o mesmo peso visual, números de 24px, rótulos de 12px abaixo do valor e conteúdo centralizado.

Esta tarefa atualiza intencionalmente a apresentação dos KPIs em relação à referência anterior de paridade com o Figma. Para esses cards, os critérios abaixo passam a orientar a implementação.

## Proposta visual

1. Exibir os cards nesta ordem, tanto visualmente quanto no DOM:
   - Cursos.
   - Matrículas.
   - Ingressantes.
   - Matrículas concluídas.
   - Matrículas equivalentes.
2. Posicionar o título acima do valor e alinhar ambos à esquerda.
3. Destacar somente o card “Matrículas” com fundo azul suave, valor em azul institucional e borda discreta no tema claro. Os demais usam a superfície padrão. Adaptar o destaque ao tema escuro, preservando a legibilidade.
4. Usar números de 32px com peso semibold e títulos de 14px com contraste suficiente. Manter a fonte Rawline já disponível no projeto.
5. Aplicar padding de 24px, cantos de 8px, borda cinza suave e nenhuma sombra. Usar os tokens existentes para espaçamento, arredondamento e cores sempre que disponíveis.
6. Manter espaçamento consistente entre título e valor e alturas coerentes entre os cards da mesma linha. Títulos longos podem quebrar; valores e estados textuais precisam caber sem cortes.
7. Preservar a grade responsiva: cinco cards na mesma linha quando houver espaço e reorganização em telas menores, sem rolagem horizontal dos KPIs.
8. Evitar ícones decorativos grandes, cores diferentes para cada indicador, animações e aparência de botão em cards sem ação.

## Contexto dos dados

- Preservar os cálculos, filtros, formatação brasileira e estados de ausência de dados existentes.
- Zero real deve continuar exibido como `0`, em apresentação neutra. Não interpretar automaticamente zero como falta de atualização ou desempenho ruim.
- Manter “dado incompleto” para matrículas equivalentes quando essa condição for retornada atualmente. Estados textuais devem usar tamanho adequado à leitura, sem obrigação de herdar os 32px dos números.
- Não acrescentar percentuais, tendências ou comparações sem dados que os sustentem.
- Uma linha de contexto ou ajuda para “Matrículas equivalentes” é opcional. Se incluída, conferir a definição nas regras de domínio e oferecer acesso por teclado e toque, além de mouse. A ajuda não pode depender exclusivamente de hover nem de um atributo `title`.

## Orientações de implementação

- `app/pages/matriculas.py`: o helper `_kpi` monta primeiro `.valor` e depois `.rotulo`; inverter essa ordem e permitir identificar explicitamente a variante de destaque. Reordenar os cards na montagem do resultado, preservando os respectivos valores.
- `app/assets/style.css`: revisar `.kpis-figma`, `.kpi-figma`, `.valor`, `.rotulo` e as regras de tema escuro. Escopar os estilos aos KPIs desta página.
- `app/components/kpi.py`: consultar para preservar `formatar_valor`. Uma alteração no componente compartilhado só é necessária se houver justificativa; conferir outras páginas caso ele seja alterado.
- Usar as variáveis do DS disponíveis localmente. O projeto proíbe cores literais em `style.css` e variáveis próprias com prefixo `--gov-`.
- Caso sejam necessárias media queries de largura, usar os pontos já admitidos pelo projeto: 576, 992, 1280 e 1600px.
- Consultar `tests/test_style_css.py` e `tests/test_paginas_publicas.py` antes de ajustar expectativas ligadas à estrutura ou à ordem dos cards.

## Critérios de aceite

- [ ] Os cinco indicadores aparecem na ordem definida, com título acima do valor e alinhamento à esquerda.
- [ ] “Matrículas” é o único card com destaque de superfície; o destaque é perceptível nos temas claro e escuro.
- [ ] Números usam 32px e peso semibold; títulos usam 14px; espaçamentos, bordas e cantos seguem a proposta.
- [ ] Textos têm contraste mínimo de 4,5:1 e números grandes de 3:1 contra suas superfícies.
- [ ] Os cards acomodam títulos longos, números grandes, `0` e “dado incompleto” sem truncamento ou sobreposição.
- [ ] A grade funciona nas larguras de 390, 768, 1280 e 1600px e com zoom de 200%, sem rolagem horizontal causada pelos cards.
- [ ] Os indicadores continuam respondendo aos filtros e mantêm os mesmos valores para o mesmo conjunto de dados.
- [ ] A ordem de leitura do DOM acompanha a ordem visual. Eventual ajuda é acessível por teclado e toque, com foco visível.
- [ ] As demais páginas que usam KPIs não apresentam regressões visuais.
- [ ] As verificações automatizadas relevantes passam e há evidências visuais da implementação.

## Validação e entrega

1. Executar `python -m pytest tests/test_style_css.py tests/test_paginas_publicas.py`. Ajustar testes existentes somente quando a nova apresentação exigir; manter as verificações de dados e filtros.
2. Inspecionar a página nas larguras listadas, nos temas claro e escuro. Conferir também zoom de 200%, zero real e dados incompletos, usando dados de teste sem substituir dados publicados.
3. Registrar capturas e um resumo da validação junto à documentação da feature, incluindo eventuais limitações.
4. Entregar as alterações de layout e as evidências para revisão. Esta tarefa não inclui publicação ou deploy.
