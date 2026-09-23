# LESSONS - auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Specify/Design)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation - do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 - Testar so as funcoes puras de um .js deixa cliques, teclas e observadores sem rede; cubra a fiacao com node e um DOM simulado (tests/dom_falso.py).
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `app/static/js` · harmful: 0
- features: govbr-design-system
- evidence: P3,P4,P5,P8,P13,P14,P15 (app/static/js)
- last seen: 2026-09-20T03:05:32Z

### L-002 - Em listas geradas por template, assertar href, action e valor do botao, nao so o aria-label.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `app/templates` · harmful: 0
- features: govbr-design-system
- evidence: P7,P12 (app/templates)
- last seen: 2026-09-20T03:05:32Z

### L-003 - Teste que so confere a presenca de um seletor em um bloco @media pode codificar o oposto da spec; assertar a propriedade e o valor.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `app/assets/style.css` · harmful: 0
- features: govbr-design-system
- evidence: DS-05 (app/assets/style.css)
- last seen: 2026-09-20T03:05:32Z

### L-004 - Confirmar no navegador o que o pacote do DS inicializa (core.min.js nao instancia br-menu) antes de fixar a premissa no Design, e atualizar o AC da spec quando um AD mudar o texto.
- signal: `spec_deviation` · recurrence: 1 feature(s) · scope: `.specs` · harmful: 0
- features: govbr-design-system
- evidence: AD-004 (.specs)
- last seen: 2026-09-20T03:05:33Z

### L-005 - Testes de tabelas dinâmicas devem exercitar o observador de DOM e os eventos de teclado, não apenas funções internas.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `app/static/js` · harmful: 0
- features: chips-e-ordenacao-publica
- evidence: app/static/js/ordenacao-tabelas.js:184 (M3) (app/static/js)
- last seen: 2026-09-22T17:51:19Z

### L-006 - Antes de travar AC sobre comportamento de parser de CSV (pandas), reproduza com usecols/dtype reais: pandas 2.3.0 tolera campo a mais/a menos silenciosamente mesmo sem encoding_errors, não levanta ParserError como um 'modo estrito' genérico sugeriria.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `app/sistec/colunas.py` · harmful: 0
- features: correcoes-envio-pastas
- evidence: CEP-05 (app/sistec/colunas.py)
- last seen: 2026-09-23T02:57:51Z

### L-007 - Ao testar um redesenho de status disparado por evento de troca de contexto (ex.: escolherOrigem chamando renderizarSelecao para todos os campos), inclua o caso do campo ainda vazio — é fácil só testar o caminho 'já tem seleção'.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `app/static/js/atualizar.js` · harmful: 0
- features: correcoes-envio-pastas
- evidence: app/static/js/atualizar.js:395 (if arquivos.length === 0) (app/static/js/atualizar.js)
- last seen: 2026-09-23T02:57:51Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
