# MVP 1 — Refatoração de `app.py` e das docstrings — Specification

## Problem Statement

`app/app.py` tem 1034 linhas e junta todas as rotas administrativas: login,
instalação, envio de pastas, coleta pelo Sistec, salvar/descartar, publicação,
histórico e configurações. Quem precisa mexer numa rota tem de ler o arquivo
inteiro, e as frentes seguintes do MVP (segurança, coleta experimental) mexem
justamente nessas rotas. Além disso, cerca de 200 docstrings e comentários
citam IDs de spec (`UPL-02`, `CPR-05`, `BR-MIGRAR-007`, `T17`, `Tarefa 09`) e
documentos que não existem mais (`roadmap.md`, `paradigm_decision.md`…), em vez
de dizer o que o código faz.

## Goals

- [ ] `app/app.py` só cria o app, registra blueprints e define o layout: no
      máximo 150 linhas e nenhuma `@server.route`.
- [ ] Cada grupo de rotas mora num módulo de `app/rotas/`, com as mesmas URLs,
      métodos e respostas de hoje.
- [ ] Nenhuma docstring ou comentário de `.py` em `app/`, `scripts/` e `run.py`
      cita ID de spec, "Tarefa NN" ou documento ausente (verificado por teste).
- [ ] A suíte inteira continua verde, sem nenhum teste apagado ou afrouxado.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Mudar comportamento de qualquer rota | Refatoração pura. Segurança e coleta experimental são as features 4 e 5. |
| Mudar URL, método HTTP ou formato de resposta | Quebraria o JavaScript da tela e a extensão. |
| `app/admin_campi.py` e `app/sistec/api.py` | Já são blueprints próprios. Só entram na limpeza de docstrings. |
| Docstrings e comentários dos testes (`tests/`) | Nos testes, o ID do AC é rastreabilidade útil: diz qual requisito o teste prova. |
| Comentários em `.js`, `.css` e `.html` | Fora do alcance desta feature; poucos casos. |
| Renomear identificadores em inglês | Spec futura (`.specs/MVP.md`). |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Nome e lugar do pacote | `app/rotas/`, um módulo por grupo: `comum`, `publico`, `acesso`, `instalacao`, `configuracoes`, `publicacao`, `envio`, `coleta_sistec`, `atualizar` | Os nomes seguem as áreas da tela `/admin/atualizar` e do menu administrativo | y (decisão técnica do plano) |
| `before_request` globais (`_exigir_instalacao`, `_exigir_sessao_previa`) | Viram `before_app_request` do blueprint da área (`instalacao` e `acesso`) | Continuam valendo para todo o app, como hoje | y |
| Testes que fazem `monkeypatch` em `app.app` | O alvo passa a ser o módulo novo (`.specs/MVP-PROTOCOLO.md`, seção 5) | Sem isso o patch não pega; não é afrouxar teste | y |
| O que sai das docstrings | IDs de spec, "Tarefa NN", nomes de tarefa (`T17`), histórico de mudanças ("antes era X") e caminhos de documentos ausentes. Fica a explicação da regra ou da decisão | Pedido da usuária: docstring diz o que o código faz | y |
| Nomes de regra de negócio usados como termo (ex.: "matrícula atendida", "ENIEA", "Guia PNP") | Ficam | São vocabulário do domínio, não IDs de spec | y |

**Open questions:** none.

---

## User Stories

### P1: Rotas administrativas separadas por área ⭐ MVP

**User Story**: Como pessoa que dá manutenção, quero encontrar a rota que preciso
mudar num arquivo pequeno com o nome da área, para não ler 1000 linhas.

**Acceptance Criteria**:

1. The system SHALL definir as rotas de `app/app.py` em módulos de `app/rotas/`, conforme a tabela da seção "Mapa de rotas".
2. The `app/app.py` SHALL ter no máximo 150 linhas e SHALL NOT conter `@server.route`.
3. WHEN qualquer URL da tabela "Mapa de rotas" recebe a mesma requisição de antes THEN the system SHALL devolver o mesmo código HTTP e o mesmo corpo (garantido pelos testes existentes, que continuam passando).
4. The system SHALL manter os dois `before_request` de hoje (instalação pendente e prévia sem sessão) valendo para todas as rotas do app.
5. The `README.md` SHALL citar `app/rotas/` na seção "Estrutura" e SHALL dizer, na seção "Onde mexer", que as rotas administrativas ficam em `app/rotas/`.

**Independent Test**: `python -m pytest -q` verde e `grep -c "@server.route" app/app.py` igual a 0.

---

### P1: Docstrings dizem o que o código faz ⭐ MVP

**User Story**: Como pessoa que lê o código, quero que as docstrings expliquem o
código sem me mandar para documentos e IDs que não tenho.

**Acceptance Criteria**:

1. The system SHALL NOT ter, em docstring ou comentário de `.py` de `app/`, `scripts/` e `run.py`, texto que case com os padrões proibidos da seção "Padrões proibidos".
2. WHEN uma docstring perde um ID ou uma referência THEN the system SHALL manter a explicação da regra que estava junto dele.
3. The system SHALL NOT mudar nenhuma linha executável nas tarefas de limpeza (conferido pelo script da seção 6 de `.specs/MVP-PROTOCOLO.md`).
4. The `scripts/verificar_prontidao_cutover.py` SHALL NOT imprimir "Tarefa" em nenhuma linha de saída.

**Independent Test**: `tests/test_higiene_docstrings.py` verde.

---

## Mapa de rotas

| Módulo novo | Blueprint | Rotas e funções que vão para ele (hoje em `app/app.py`) |
| --- | --- | --- |
| `app/rotas/comum.py` | — (só funções) | `_contexto_base` → `contexto_base`, `_admin_email` → `admin_email`, `_execucao_da_sessao` → `execucao_da_sessao`, `_ano_base_config` → `ano_base_config` |
| `app/rotas/publico.py` | `publico_bp` | `GET /matriculas` (`matriculas_legado`), `GET /branding/logo` (`branding_logo`) |
| `app/rotas/acesso.py` | `acesso_bp` | `/admin/login`, `/admin/logout`, `/recuperar-acesso`, o `before_request` `_exigir_sessao_previa`, as mensagens `_MSG_*` |
| `app/rotas/instalacao.py` | `instalacao_bp` | `/admin/instalacao`, o `before_request` `_exigir_instalacao`, `_ROTAS_SEM_INSTALACAO` |
| `app/rotas/configuracoes.py` | `configuracoes_bp` | `/admin/config`, `/admin/config/captura`, `LOGO_MAX_BYTES`, `UPLOADS_BRANDING_DIR` |
| `app/rotas/publicacao.py` | `publicacao_bp` | `/admin/atualizar/publicar`, `/admin/atualizar/desfazer`, `/admin/historico`, `historico_iniciar_e_encerrar` |
| `app/rotas/envio.py` | `envio_bp` | `/admin/atualizar/envio`, `_resumo_arquivos_envio`, `_matriculas_orfas_envio`, `_cadastrar_unidades_do_envio`, `_completar_unidades_incompletas` |
| `app/rotas/coleta_sistec.py` | `coleta_sistec_bp` | `/admin/atualizar/sistec`, `/admin/atualizar/sistec/login-feito`, `/admin/atualizar/sistec/cancelar`, `/admin/atualizar/execucoes` (criar), `/admin/atualizar/execucoes/<id>/iniciar`, `/retomar`, `/cancelar` |
| `app/rotas/atualizar.py` | `atualizar_bp` | `GET /admin/atualizar`, `GET /admin/atualizar/execucao`, `/admin/atualizar/execucoes/<id>/salvar`, `/admin/atualizar/execucoes/<id>/descartar` |

`app/app.py` fica com: imports, criação do `PainelDash`, `server` e sua
configuração, `init_db`, registro dos blueprints (os de hoje mais os novos),
`init_shell`, `serve_layout` e `app.layout`.

## Padrões proibidos (em docstrings e comentários)

Expressões regulares, aplicadas só ao texto de docstrings e comentários `#`:

- `\b(BR-MIGRAR|BR-HUMANA|RISK|UPL|CPR|PVP|MAT|DS|AD|RF|RN|DEV|AMB|WDG|LIM|DEP|DOC|EST|PT|AGG|BC|REF|PAR|PBI|SEG|EXP|IMP)-\d+`
- `\b[DP]-\d+\b`
- `\bT-?\d{1,3}\b` (nomes de tarefa como `T17` e de etapa como `T-01`)
- `\bTarefa \d+`
- `roadmap\.md|data-delta\.md|f0-resultado\.md|data_migration_plan\.md|target_[a-z_]+\.md|paradigm_decision\.md|parity_tests|parity_specs|onboarding\.md|regression-watch|cutover_plan|_reversa_|reconstruction-plan|\d{3}-[a-z]+-[a-z-]+`

---

## Edge Cases

- IF um nome movido é importado por outro módulo de `app/` (não só por testes) THEN the system SHALL atualizar esse import para o módulo novo, sem manter cópia em `app/app.py`.
- IF uma docstring fica vazia depois da limpeza THEN the system SHALL escrever uma frase curta dizendo o que a função faz (docstring vazia não é aceita).
- WHEN um comentário só continha o ID (ex.: `# RN-13`) THEN the system SHALL apagar o comentário inteiro.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| REF-01 | P1: Rotas — AC1, AC3 (um módulo por grupo) | Tasks | Pending |
| REF-02 | P1: Rotas — AC2 (`app.py` enxuto) | Tasks | Pending |
| REF-03 | P1: Rotas — AC4 (`before_request`) | Tasks | Pending |
| REF-04 | P1: Rotas — AC5 (README) | Tasks | Pending |
| REF-05 | P1: Docstrings — AC1, AC2, edge cases | Tasks | Pending |
| REF-06 | P1: Docstrings — AC3 (nada executável muda) | Tasks | Pending |
| REF-07 | P1: Docstrings — AC4 (saída do script de prontidão) | Tasks | Pending |

**Coverage:** 7 total, 7 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `wc -l app/app.py` ≤ 150 e nenhuma `@server.route` nele.
- [ ] `python -m pytest -q` verde, com `passed` ≥ linha de base + testes novos.
- [ ] `tests/test_higiene_docstrings.py` verde.
