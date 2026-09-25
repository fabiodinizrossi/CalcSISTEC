# MVP 4 — Segurança para a internet — Specification

## Problem Statement

O CalcSISTEC vai rodar num servidor na internet, com `/admin` acessível de fora.
Hoje os `POST` administrativos não têm token CSRF (só o `SameSite=Lax` do
cookie protege), o login aceita tentativas sem limite, as respostas não trazem
cabeçalhos de segurança, a sessão não expira e o app sobe mesmo sem
`FLASK_SECRET_KEY` (sorteia uma chave por processo). Atrás de um proxy (nginx),
o app também não enxerga o IP real nem o HTTPS do visitante.

## Goals

- [ ] Todo `POST` administrativo sem token CSRF válido é recusado com 400.
- [ ] Depois de 5 senhas erradas em 15 minutos, o login fica bloqueado por 15 minutos para aquele IP.
- [ ] Respostas com cabeçalhos básicos de segurança; sessão administrativa expira em 8 horas.
- [ ] Com `CALCSISTEC_HTTPS=1`, o app não sobe sem `FLASK_SECRET_KEY`; com `CALCSISTEC_PROXY=1`, lê IP e protocolo do proxy.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Content-Security-Policy | O Dash usa scripts que exigem ajuste fino de CSP; spec futura (`.specs/MVP.md`). |
| Várias contas e perfis | Spec futura. |
| Bloqueio distribuído (Redis etc.) | Produção roda com um processo só (P-09); memória basta. |
| API da extensão (`/api/sistec/*`) | Já autentica por token `Authorization: Bearer` por execução; não usa cookie de sessão, então CSRF não se aplica. |
| Callbacks do Dash (`/_dash-*`) | Só leem dados; não mudam estado. |
| Logout por `GET` | Risco baixo (só encerra a sessão); fica como está. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Biblioteca de CSRF | Implementação própria em `app/seguranca.py` (token na sessão, `secrets.compare_digest`) | Evita dependência nova (Flask-WTF) para ~40 linhas | y |
| Onde o token vai | Campo oculto `csrf_token` em todo `<form method="post">`; cabeçalho `X-CSRF-Token` nos `fetch` do JavaScript, lido de `<meta name="csrf-token">` | Padrão comum; o JavaScript da tela de atualizar usa `fetch` | y |
| Meta tag só nas telas administrativas | Em `app/templates/_base.html`, não em `shell/_head.html` | `_head.html` também serve às páginas públicas; gerar token nelas criaria sessão para todo visitante | y |
| CSRF nos testes | `tests/conftest.py` desliga a checagem por padrão (`server.config["CSRF_ATIVO"] = False`); os testes marcados com `@pytest.mark.csrf` a ligam | Padrão de Flask-WTF (`WTF_CSRF_ENABLED=False` em teste); a checagem em si tem testes próprios | y |
| Chave do bloqueio | IP do cliente (`request.remote_addr`, correto atrás do proxy com `CALCSISTEC_PROXY=1`) | Uma conta só; bloquear por conta travaria a própria PI | y |
| Números do bloqueio | 5 falhas em 15 minutos → bloqueio de 15 minutos; sucesso zera | Padrão usual para uma conta administrativa | y |
| Resposta do bloqueio | Tela de login com a mensagem "Muitas tentativas de acesso. Tente de novo em 15 minutos." e código 429 | Mensagem clara, sem dizer se a senha estava certa | y |
| Duração da sessão | 8 horas (`PERMANENT_SESSION_LIFETIME`) | Um dia de trabalho | y |

**Open questions:** none.

---

## User Stories

### P1: Token CSRF em todo POST administrativo ⭐ MVP

**Acceptance Criteria**:

1. The system SHALL guardar um token aleatório (`secrets.token_urlsafe(32)`) na sessão na primeira vez que uma tela administrativa o pede, e SHALL reutilizá-lo depois.
2. The system SHALL incluir `<input type="hidden" name="csrf_token" value="...">` em todo `<form method="post">` dos templates.
3. The `_base.html` SHALL incluir `<meta name="csrf-token" content="...">`, e o JavaScript de `atualizar.js` SHALL enviar o cabeçalho `X-CSRF-Token` em todo `fetch` com método `POST`.
4. IF um `POST`, `PUT`, `PATCH` ou `DELETE` chega sem token, ou com token diferente do da sessão, THEN the system SHALL responder 400, sem executar a rota.
5. WHEN a requisição recusada espera JSON (caminho começa com `/admin/atualizar/`) THEN the system SHALL responder `{"erro": "csrf_invalido"}`; nos outros casos, SHALL responder uma página curta com "Sua sessão expirou ou o formulário é inválido. Recarregue a página e tente de novo."
6. The system SHALL NOT exigir token em `/api/sistec/*` nem em `/_dash-*`.
7. The páginas públicas SHALL NOT criar sessão só por serem abertas.

### P1: Bloqueio de força bruta no login ⭐ MVP

**Acceptance Criteria**:

1. WHEN o mesmo IP erra a senha 5 vezes em 15 minutos THEN the system SHALL recusar o próximo login desse IP por 15 minutos, com código 429 e a mensagem da tabela de Assumptions, mesmo que a senha esteja certa.
2. WHEN o login dá certo THEN the system SHALL zerar as falhas daquele IP.
3. WHEN passam 15 minutos do bloqueio THEN the system SHALL aceitar o login de novo.
4. The falhas de validação de formato (e-mail inválido, senha curta) SHALL NOT contar como tentativa.

### P1: Cabeçalhos e sessão ⭐ MVP

**Acceptance Criteria**:

1. The system SHALL enviar em toda resposta `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Referrer-Policy: same-origin`.
2. WHERE `CALCSISTEC_HTTPS=1`, the system SHALL enviar também `Strict-Transport-Security: max-age=31536000`.
3. WHEN o login dá certo THEN the system SHALL marcar a sessão como permanente, com duração de 8 horas.
4. The cookie de sessão SHALL ser `HttpOnly`.

### P1: Configuração de produção ⭐ MVP

**Acceptance Criteria**:

1. IF `CALCSISTEC_HTTPS=1` e `FLASK_SECRET_KEY` está vazia ou ausente THEN the system SHALL recusar subir, com o erro "FLASK_SECRET_KEY é obrigatória com CALCSISTEC_HTTPS=1".
2. WHERE `CALCSISTEC_PROXY=1`, the system SHALL aplicar `werkzeug.middleware.proxy_fix.ProxyFix(x_for=1, x_proto=1, x_host=1)`.
3. The `.env.example` SHALL ter a chave `CALCSISTEC_PROXY`, com comentário.
4. The `scripts/verificar_prontidao_cutover.py` SHALL conferir `FLASK_SECRET_KEY` definida e `CALCSISTEC_PROXY=1`, e SHALL dar NO-GO sem elas.
5. The `DEPLOY.md` SHALL tirar o CSRF das pendências e explicar `CALCSISTEC_PROXY`.

---

## Edge Cases

- IF o token da sessão não existe (sessão nova) e chega um `POST` THEN the system SHALL responder 400.
- WHEN o envio de pastas (multipart) chega THEN o token SHALL poder vir no cabeçalho `X-CSRF-Token`, sem depender do campo do formulário.
- IF dois IPs diferentes erram a senha THEN o bloqueio de um SHALL NOT afetar o outro.
- WHEN o processo reinicia THEN as falhas e os bloqueios SHALL zerar (ficam em memória).

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| SEG-01 | CSRF — AC1, AC2, AC7 (token e formulários) | Tasks | Pending |
| SEG-02 | CSRF — AC3 (meta e JavaScript) | Tasks | Pending |
| SEG-03 | CSRF — AC4, AC5, AC6 (recusa) | Tasks | Pending |
| SEG-04 | Força bruta — AC1..AC4 | Tasks | Pending |
| SEG-05 | Cabeçalhos e sessão — AC1..AC4 | Tasks | Pending |
| SEG-06 | Produção — AC1, AC2, AC3 | Tasks | Pending |
| SEG-07 | Produção — AC4 (prontidão) | Tasks | Pending |
| SEG-08 | Produção — AC5 (DEPLOY) | Tasks | Pending |

**Coverage:** 8 total, 8 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `python -m pytest -q` verde, com os testes marcados `csrf` exercitando a recusa real.
- [ ] Em produção, `verificar_prontidao_cutover.py` dá GO só com chave secreta e proxy configurados.
