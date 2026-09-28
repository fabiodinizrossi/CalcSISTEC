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

### L-008 - Quando uma rota promete nenhuma gravação após falha, cadastros auxiliares devem ser adiados ou revertidos junto com a operação principal.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `app/app.py` · harmful: 0
- features: correcoes-previa-uso-real
- evidence: app/app.py:468 (app/app.py)
- last seen: 2026-09-24T02:51:41Z

### L-009 - Edge cases de assinatura/versionamento devem dizer quem mudou o estado: a spec recusava 409 para qualquer mudanca em interna_campus depois da montagem, mas a escrita do proprio envio (P1.3 AC3) precisa passar - a distincao 'por outra origem' so existia no tasks.md.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `app/app.py;app/sistec/execucoes.py;spec-ac` · harmful: 0
- features: correcoes-previa-uso-real
- evidence: .specs/features/correcoes-previa-uso-real/spec.md:129 (app/app.py;app/sistec/execucoes.py;spec-ac)
- last seen: 2026-09-24T05:19:03Z

### L-010 - Antes de registrar na spec uma hipotese de causa para um residuo de paridade, teste a hipotese contra o dado real; hipotese nao confirmada entra como causa nao identificada, nao como explicacao.
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `paridade/spec` · harmful: 0
- features: correcao-matricula-atendida
- evidence: G2 / .specs/features/correcao-matricula-atendida/spec.md (Out of Scope, residuo 16.750 vs 16.832) (paridade/spec)
- last seen: 2026-09-24T06:26:46Z

### L-011 - Assertar o numero que a spec fixa (timeout, limite) no proprio valor, nao so o resultado da operacao.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `scripts/testar.ps1` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: tests/test_testar_ps1.py:147 (M9) (scripts/testar.ps1)
- last seen: 2026-09-24T17:11:13Z

### L-012 - Assertar cada dado que a spec manda o comando imprimir (URL, credenciais, identificadores), nao so o codigo de saida e a porta.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `scripts/testar.ps1` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: scripts/testar.ps1:215 (M12) (scripts/testar.ps1)
- last seen: 2026-09-24T17:11:13Z

### L-013 - Dar teste automatizado a todo AC: criterio verificado so a mao deixa o ramo invisivel para o sensor.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: scripts/testar.ps1:82 (M13) (tests)
- last seen: 2026-09-24T17:11:13Z

### L-014 - Cobrir com teste os edge cases declarados de funcao pre-existente, mesmo quando a feature so passa a chama-la.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `tests` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: app/sistec/execucoes.py:571 (M11) (tests)
- last seen: 2026-09-24T17:11:13Z

### L-015 - Quando o AC enumera N itens obrigatorios, assertar os N itens; assertar so o recipiente deixa implementacao parcial passar.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `docs` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: DOC-03 AC8 (tests/test_higiene_repositorio.py:177) (docs)
- last seen: 2026-09-24T17:11:14Z

### L-016 - Assertar o conjunto inteiro de chaves que o criterio enumera, nao so as uma ou duas que carregam risco.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `docs` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: DEP-02 AC4 (tests/test_higiene_repositorio.py:402) (docs)
- last seen: 2026-09-24T17:11:14Z

### L-017 - Assertar o efeito preparatorio que um passo exige antes de rodar (arquivo criado, pasta garantida), nao so o estado final.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `scripts/testar.ps1` · harmful: 0
- features: limpeza-onboarding-repo
- evidence: edge case .env (scripts/testar.ps1:122) (scripts/testar.ps1)
- last seen: 2026-09-24T17:11:14Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
