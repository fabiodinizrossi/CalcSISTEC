# MVP 4 — Segurança para a internet — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Exceção combinada com a usuária para executores sem suporte a skills: leia `.specs/MVP-PROTOCOLO.md` inteiro e siga-o; ele aponta o arquivo da skill que substitui a ativação.

Pré-requisito: `mvp-3-paginas-power-bi` com Verifier PASS (as rotas já estão em `app/rotas/` desde a feature 1).

---

**Spec**: `.specs/features/mvp-4-seguranca/spec.md`
**Status**: Draft

---

## Test Coverage Matrix

> Diretrizes: `.specs/PROJECT_RULES.md` (Restrições Técnicas e de Segurança; Princípio VII: operações administrativas exigem autenticação); `.specs/MVP-PROTOCOLO.md`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| `app/seguranca.py` | unit | Cada função: caminho feliz, token ausente, token errado, isenções; bloqueio com relógio controlado | `tests/test_seguranca.py` | `python -m pytest tests/test_seguranca.py -q -p no:cacheprovider` |
| Rotas e templates | integration | Todo formulário POST renderizado tem o campo; `POST` sem token → 400 com o corpo do spec; login bloqueado → 429 | `tests/test_seguranca.py` | idem |
| JavaScript (`atualizar.js`) | integration (node) | `fetch` POST leva o cabeçalho `X-CSRF-Token` | `tests/test_js_envio.py` | `python -m pytest tests/test_js_envio.py -q -p no:cacheprovider` |
| Configuração (`app/config.py`) | unit | Chave secreta obrigatória com HTTPS; ProxyFix com a variável | `tests/test_seguranca.py` | idem |
| Script de prontidão | integration | NO-GO sem chave e sem proxy | `tests/test_higiene_repositorio.py` ou teste novo | `python -m pytest -q -p no:cacheprovider` |
| Documentação | unit (higiene) | Marcadores exigidos | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Só documentação | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Full | Toda tarefa com código | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Execution Plan

### Phase 1: CSRF

```
T1 → T2 → T3
```

### Phase 2: Login, cabeçalhos e produção

```
T4 → T5 → T6 → T7 → T8
```

---

## Task Breakdown

### T1: Token CSRF nos formulários e na meta tag (sem exigir ainda)

**What**: Criar `app/seguranca.py` com `token_csrf()` e `init_seguranca(server)`
(que registra o `context_processor`); pôr o campo oculto em todo
`<form method="post">` dos templates e a meta tag em `_base.html`. A recusa
vem só em T3, para nenhum commit deixar a tela quebrada.
**Where**: `app/seguranca.py` (novo)
**Depends on**: None
**Reuses**: `flask.session`; templates `app/templates/*.html`
**Requirement**: SEG-01

**Passos**:

1. `app/seguranca.py`:

   ```python
   """Proteções das rotas administrativas: token CSRF e bloqueio de força bruta."""

   import secrets

   import flask

   CAMPO_CSRF = "csrf_token"
   CABECALHO_CSRF = "X-CSRF-Token"
   _CHAVE_SESSAO = "csrf_token"


   def token_csrf():
       """Token CSRF da sessão; cria na primeira chamada."""
       token = flask.session.get(_CHAVE_SESSAO)
       if not token:
           token = secrets.token_urlsafe(32)
           flask.session[_CHAVE_SESSAO] = token
       return token


   def init_seguranca(server):
       """Registra no app Flask as proteções deste módulo."""
       server.config.setdefault("CSRF_ATIVO", True)
       server.context_processor(lambda: {"csrf_token": token_csrf})
   ```

2. Em `app/app.py`, logo depois de `aplicar_configuracao_sessao(server)`:
   `init_seguranca(server)` (com o import).
3. Templates: em cada `<form method="post" ...>` de `app/templates/*.html`
   (liste com `git grep -n -i 'method="post"' app/templates`), acrescente na
   linha seguinte `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
   São 18 formulários em `login.html`, `instalacao.html`, `configuracoes.html`,
   `campi_form.html` e `campi_lista.html`.
4. `app/templates/_base.html`, dentro do `<head>`, depois do include de
   `shell/_head.html`: `<meta name="csrf-token" content="{{ csrf_token() }}">`.
   **Não** ponha em `shell/_head.html` (as páginas públicas também o usam).
5. `tests/test_seguranca.py`:
   - `token_csrf` devolve o mesmo valor em duas chamadas na mesma sessão e
     valores diferentes em sessões diferentes (use `server.test_request_context()`);
   - para cada tela com formulário (`/admin/login` sem login; `/admin/instalacao`,
     `/admin/config`, `/admin/campi` e o formulário de inclusão de campus com
     login e instalação concluída, como os testes de `tests/test_admin_paginas.py`
     e `tests/test_admin_campi.py` fazem), todo `<form` com `method="post"` do
     HTML tem um `input` `name="csrf_token"` com valor não vazio (use
     `html.parser.HTMLParser` da biblioteca padrão);
   - `/admin/atualizar` (com login) tem a meta `csrf-token`;
   - abrir `/` (página pública) com o cliente de teste não cria cookie de sessão
     (confira o cabeçalho `Set-Cookie` da resposta).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: linha de base + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(seguranca): token csrf nos formularios administrativos`

---

### T2: `atualizar.js` envia o token no cabeçalho

**What**: Todo `fetch` com `POST` em `app/static/js/atualizar.js` envia
`X-CSRF-Token` com o valor da meta `csrf-token`.
**Where**: `app/static/js/atualizar.js`
**Depends on**: T1
**Reuses**: função `postar` (`atualizar.js`, perto da linha 102) e o `fetch` do envio de pastas (perto da linha 491)
**Requirement**: SEG-02

**Passos**:

1. No topo do módulo, uma função:

   ```javascript
   function tokenCsrf() {
     const meta = document.querySelector('meta[name="csrf-token"]');
     return meta ? meta.getAttribute("content") : "";
   }
   ```

2. Em `postar`, acrescente `"X-CSRF-Token": tokenCsrf()` aos `headers`.
3. No `fetch("/admin/atualizar/envio", { method: "POST", body: dados })`,
   acrescente `headers: { "X-CSRF-Token": tokenCsrf() }` **sem** `Content-Type`
   (o navegador monta o multipart).
4. Procure outros `fetch` com `POST` em `app/static/js/` (`git grep -n "method: \"POST\"" app/static/js`) e faça o mesmo.
5. Em `tests/test_js_envio.py`, leia como o DOM falso (`tests/dom_falso.py`) e o
   `fetch` falso são montados. Acrescente a meta no DOM falso do teste e afirme
   que o `fetch` do envio e o de `postar` recebem o cabeçalho com o valor da meta.

**Done when**:

- [ ] Testes novos passam (precisam do `node` no PATH, como os outros `test_js_*`)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(seguranca): enviar o token csrf nas chamadas da tela de atualizar`

---

### T3: Recusar `POST` sem token válido

**What**: `verificar_csrf()` em `app/seguranca.py`, registrado como
`before_request` por `init_seguranca`; `tests/conftest.py` desliga a checagem
por padrão nos testes e a marca `csrf` a religa.
**Where**: `app/seguranca.py`
**Depends on**: T2
**Reuses**: T1
**Requirement**: SEG-03

**Passos**:

1. Código:

   ```python
   _METODOS_PROTEGIDOS = {"POST", "PUT", "PATCH", "DELETE"}
   _PREFIXOS_ISENTOS = ("/api/sistec/", "/_dash-")
   MENSAGEM_CSRF = "Sua sessão expirou ou o formulário é inválido. Recarregue a página e tente de novo."


   def verificar_csrf():
       """Recusa com 400 o POST administrativo sem o token da sessão."""
       if not flask.current_app.config.get("CSRF_ATIVO", True):
           return None
       if flask.request.method not in _METODOS_PROTEGIDOS:
           return None
       if flask.request.path.startswith(_PREFIXOS_ISENTOS):
           return None
       esperado = flask.session.get(_CHAVE_SESSAO)
       enviado = flask.request.headers.get(CABECALHO_CSRF) or flask.request.form.get(CAMPO_CSRF)
       if esperado and enviado and secrets.compare_digest(esperado, enviado):
           return None
       if flask.request.path.startswith("/admin/atualizar/"):
           return flask.jsonify({"erro": "csrf_invalido"}), 400
       return flask.Response(MENSAGEM_CSRF, status=400, mimetype="text/plain; charset=utf-8")
   ```

   Em `init_seguranca`, acrescente `server.before_request(verificar_csrf)`.
   Atenção: o cabeçalho é lido **antes** de `request.form`, para o envio de
   pastas grande não ser lido inteiro à toa.
2. `tests/conftest.py` (novo, ou acrescente se já existir):

   ```python
   import sys

   import pytest


   def pytest_configure(config):
       config.addinivalue_line("markers", "csrf: liga a checagem de CSRF neste teste")


   @pytest.fixture(autouse=True)
   def _csrf_so_nos_testes_marcados(request):
       modulo = sys.modules.get("app.app")
       if modulo is None:
           yield
           return
       anterior = modulo.server.config.get("CSRF_ATIVO", True)
       modulo.server.config["CSRF_ATIVO"] = request.node.get_closest_marker("csrf") is not None
       yield
       modulo.server.config["CSRF_ATIVO"] = anterior
   ```

3. Em `tests/test_seguranca.py`, com `@pytest.mark.csrf`:
   - `POST /admin/login` sem token → 400 e o texto `MENSAGEM_CSRF`;
   - `POST /admin/atualizar/publicar` autenticado, sem token → 400 e JSON `{"erro": "csrf_invalido"}`;
   - o mesmo com token errado → 400;
   - com o token certo no campo do formulário → não é 400 (o login segue o fluxo normal);
   - com o token certo no cabeçalho, no `POST /admin/atualizar/envio` → não é 400;
   - `POST /api/sistec/execucoes/x/proximo` sem token → não é 400 de CSRF (a
     API responde pelo próprio motivo, 401 ou 404);
   - `POST /_dash-update-component` sem token → não é 400 de CSRF.
   Para pegar o token nos testes: faça `GET` numa tela, leia a sessão com
   `cliente.session_transaction()` e copie `sessao["csrf_token"]`.
4. Um teste **sem** a marca afirma que, em produção, `CSRF_ATIVO` é `True` por
   padrão: importe `app.seguranca`, crie um `flask.Flask("x")`, rode
   `init_seguranca(app_teste)` e confira `app_teste.config["CSRF_ATIVO"] is True`.

**Done when**:

- [ ] Testes novos passam; nenhum teste antigo foi alterado para passar
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(seguranca): recusar post administrativo sem token csrf`

---

### T4: Bloqueio de força bruta no login

**What**: Em `app/seguranca.py`: `login_bloqueado(ip)`, `registrar_falha_login(ip)`,
`limpar_falhas_login(ip)`; a rota de login (`app/rotas/acesso.py`) passa a usá-las.
**Where**: `app/seguranca.py`
**Depends on**: None
**Reuses**: rota `admin_login` (`app/rotas/acesso.py`)
**Requirement**: SEG-04

**Passos**:

1. Código:

   ```python
   import threading
   from datetime import datetime, timedelta

   MAX_FALHAS = 5
   JANELA_FALHAS = timedelta(minutes=15)
   DURACAO_BLOQUEIO = timedelta(minutes=15)
   MENSAGEM_BLOQUEIO = "Muitas tentativas de acesso. Tente de novo em 15 minutos."

   _falhas = {}
   _bloqueados = {}
   _trava = threading.Lock()


   def _agora():
       return datetime.now()


   def login_bloqueado(ip):
       with _trava:
           ate = _bloqueados.get(ip)
           if ate is None:
               return False
           if _agora() >= ate:
               del _bloqueados[ip]
               _falhas.pop(ip, None)
               return False
           return True


   def registrar_falha_login(ip):
       agora = _agora()
       with _trava:
           recentes = [t for t in _falhas.get(ip, []) if agora - t < JANELA_FALHAS]
           recentes.append(agora)
           _falhas[ip] = recentes
           if len(recentes) >= MAX_FALHAS:
               _bloqueados[ip] = agora + DURACAO_BLOQUEIO


   def limpar_falhas_login(ip):
       with _trava:
           _falhas.pop(ip, None)
           _bloqueados.pop(ip, None)
   ```

2. Na rota de login (`POST`), leia o código atual inteiro antes. Depois das
   validações de formato (e-mail e tamanho da senha, que **não** contam):
   - se `login_bloqueado(flask.request.remote_addr)`, renderize `login.html`
     como hoje renderiza erro, com `erro_global=MENSAGEM_BLOQUEIO`, e devolva
     com status 429, **sem** chamar `autenticar_sessao`;
   - se `autenticar_sessao` falhar, chame `registrar_falha_login(ip)`;
   - se der certo, `limpar_falhas_login(ip)`.
3. Testes em `tests/test_seguranca.py` (sem a marca `csrf`; troque `_agora`
   com `monkeypatch.setattr(seguranca, "_agora", lambda: instante)` e zere
   `_falhas`/`_bloqueados` numa fixture):
   - 5 falhas seguidas → a 6.ª tentativa, com a senha **certa**, recebe 429 e a mensagem;
   - 4 falhas + 1 sucesso → falhas zeradas (mais 4 falhas não bloqueiam);
   - bloqueado; 15 minutos depois → aceita;
   - falhas espaçadas mais de 15 minutos não acumulam;
   - e-mail inválido 10 vezes → não bloqueia;
   - IP diferente (`environ_base={"REMOTE_ADDR": "10.0.0.2"}`) não é afetado.
   Use as credenciais de teste do mesmo jeito que `tests/test_admin_paginas.py`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(seguranca): bloquear o login depois de cinco senhas erradas`

---

### T5: Cabeçalhos de segurança e sessão de 8 horas

**What**: `after_request` com os cabeçalhos do spec; sessão permanente de 8 horas
no login; cookie `HttpOnly` explícito.
**Where**: `app/config.py`
**Depends on**: T4
**Reuses**: `aplicar_configuracao_sessao`, `https_ativo` (`app/config.py`); `autenticar_sessao` (`app/auth.py`)
**Requirement**: SEG-05

**Passos**:

1. Em `aplicar_configuracao_sessao(server)`:
   `server.config["SESSION_COOKIE_HTTPONLY"] = True` e
   `server.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)`; e registre:

   ```python
   @server.after_request
   def _cabecalhos_de_seguranca(resposta):
       resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
       resposta.headers.setdefault("X-Frame-Options", "DENY")
       resposta.headers.setdefault("Referrer-Policy", "same-origin")
       if https_ativo():
           resposta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
       return resposta
   ```

2. Em `app/auth.py`, `autenticar_sessao`: quando der certo, `flask.session.permanent = True`.
3. Testes: `GET /` traz os 3 cabeçalhos; com `monkeypatch.setenv("CALCSISTEC_HTTPS", "1")`
   traz também o HSTS (o `https_ativo()` lê a variável na hora); sem ela, não traz;
   depois do login, a sessão é permanente (leia com `session_transaction()`);
   `server.permanent_session_lifetime == timedelta(hours=8)`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(seguranca): cabecalhos de seguranca e sessao de oito horas`

---

### T6: Chave secreta obrigatória com HTTPS e proxy reverso

**What**: Em `app/config.py`, `chave_secreta()` e `aplicar_proxy(server)`;
`app/app.py` passa a usá-las; `.env.example` ganha `CALCSISTEC_PROXY`.
**Where**: `app/config.py`
**Depends on**: T5
**Reuses**: `app/app.py:48` (`server.secret_key = ...`)
**Requirement**: SEG-06

**Passos**:

1. Código em `app/config.py`:

   ```python
   def chave_secreta():
       """Chave de sessão do Flask. Com HTTPS, a chave do .env é obrigatória."""
       chave = os.environ.get("FLASK_SECRET_KEY", "")
       if chave:
           return chave
       if https_ativo():
           raise RuntimeError("FLASK_SECRET_KEY é obrigatória com CALCSISTEC_HTTPS=1")
       return os.urandom(24)


   def aplicar_proxy(server):
       """Atrás de um proxy reverso, lê IP, protocolo e host dos cabeçalhos X-Forwarded-*."""
       if os.environ.get("CALCSISTEC_PROXY") == "1":
           from werkzeug.middleware.proxy_fix import ProxyFix
           server.wsgi_app = ProxyFix(server.wsgi_app, x_for=1, x_proto=1, x_host=1)
   ```

2. `app/app.py`: `server.secret_key = chave_secreta()` e `aplicar_proxy(server)`
   logo depois de `aplicar_configuracao_sessao(server)`.
3. `.env.example`: acrescente `CALCSISTEC_PROXY=` com o comentário "Use 1 quando
   o CalcSISTEC roda atrás de um proxy reverso (nginx) que termina o HTTPS."
   O teste de higiene das chaves do `.env.example` lista as chaves esperadas:
   acrescente `CALCSISTEC_PROXY` à lista (cite SEG-06 AC3 no commit).
4. Testes:
   - `chave_secreta()` com a variável → devolve o valor; sem ela e sem HTTPS →
     `bytes` de 24; sem ela e com HTTPS → `RuntimeError` com a mensagem exata;
   - `aplicar_proxy` num `flask.Flask("x")` com uma rota que devolve
     `request.remote_addr` e `request.scheme`: com a variável e
     `X-Forwarded-For: 203.0.113.9` / `X-Forwarded-Proto: https`, a rota vê
     `203.0.113.9` e `https`; sem a variável, vê o IP do cliente de teste.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(config): exigir chave secreta com https e aceitar proxy reverso`

---

### T7: Verificação de prontidão confere chave e proxy

**What**: `scripts/verificar_prontidao_cutover.py` ganha dois critérios:
`FLASK_SECRET_KEY` definida e `CALCSISTEC_PROXY=1`. Sem eles, NO-GO.
**Where**: `scripts/verificar_prontidao_cutover.py`
**Depends on**: T6
**Reuses**: o critério existente de `CALCSISTEC_HTTPS=1` no mesmo script (copie o formato)
**Requirement**: SEG-07

**Passos**:

1. Leia o script inteiro. Ache como o critério de `CALCSISTEC_HTTPS` é declarado
   e impresso, e acrescente os dois novos do mesmo jeito, logo depois dele.
2. Testes (use o `carregar_script` que `tests/test_higiene_repositorio.py` já
   usa, e `monkeypatch.setenv`/`delenv`): sem `FLASK_SECRET_KEY` → o critério
   aparece como não cumprido e o resultado é NO-GO; com as duas variáveis → os
   dois critérios aparecem como cumpridos.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(prontidao): conferir chave secreta e proxy antes do cutover`

---

### T8: Documentar a segurança e registrar a feature

**What**: `DEPLOY.md`: tirar o CSRF das pendências; seção "Segurança" curta
(token CSRF, bloqueio de login, cabeçalhos, sessão de 8 h, `CALCSISTEC_PROXY`,
`FLASK_SECRET_KEY` obrigatória). `README.md`: `app/seguranca.py` em "Onde mexer".
`STATE.md`: handoff da feature. Não tire a palavra `CSRF` do `DEPLOY.md` (o teste
de higiene a exige): ela passa a aparecer na seção "Segurança".
**Where**: `DEPLOY.md`
**Depends on**: T7
**Reuses**: nenhum
**Requirement**: SEG-08

**Done when**:

- [ ] Teste de higiene: `DEPLOY.md` cita `CALCSISTEC_PROXY` e não tem mais "Os `POST` administrativos não têm token CSRF"
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(deploy): documentar as protecoes para a internet`

---

## Verificação (depois de T8)

Verifier independente. Sensor mínimo: trocar `compare_digest` por comparação
que aceita token vazio; isentar `/admin/`; `MAX_FALHAS = 50`; tirar o
`session.permanent`; `chave_secreta` sortear chave mesmo com HTTPS.

---

## Phase Execution Map

```
Phase 1:  T1 → T2 → T3
Phase 2:  T4 → T5 → T6 → T7 → T8
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | módulo novo + 5 templates + `_base.html` | ⚠️ coeso: o mesmo campo em todo formulário |
| T2 | 1 arquivo JS | ✅ |
| T3 | 1 função + conftest | ⚠️ coeso: a recusa exige o conftest no mesmo commit |
| T4 | 3 funções + rota de login | ✅ |
| T5 | `config.py` + 1 linha em `auth.py` | ✅ |
| T6 | 2 funções + `app.py` + `.env.example` | ⚠️ coeso: configuração de produção |
| T7 | 1 script | ✅ |
| T8 | documentação | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | T2 | T2 → T3 | ✅ |
| T4 | None | início da fase 2 | ✅ |
| T5 | T4 | T4 → T5 | ✅ |
| T6 | T5 | T5 → T6 | ✅ |
| T7 | T6 | T6 → T7 | ✅ |
| T8 | T7 | T7 → T8 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1, T3, T4 | seguranca + rotas/templates | integration | integration | ✅ |
| T2 | JavaScript | integration | integration | ✅ |
| T5, T6 | configuração | unit | unit | ✅ |
| T7 | script | integration | integration | ✅ |
| T8 | documentação | unit (higiene) | unit | ✅ |
