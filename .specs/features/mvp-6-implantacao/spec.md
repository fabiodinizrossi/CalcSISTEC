# MVP 6 — Implantação e primeiro ciclo real — Specification

## Problem Statement

O CalcSISTEC ainda não tem jeito de rodar em produção. `python run.py` usa o
servidor de desenvolvimento do Flask, que não é feito para a internet; não há
exemplo de serviço que reinicie sozinho, de proxy com HTTPS nem de backup do
banco; e o `DEPLOY.md` não tem um passo a passo que alguém siga do zero. O MVP
só termina quando a PI publica sozinha um ciclo real no servidor.

## Goals

- [ ] `python run.py --producao` sobe o app com um servidor WSGI de produção, num processo só.
- [ ] O repositório traz exemplos prontos de serviço (systemd) e de proxy (nginx) e um script de backup.
- [ ] O `DEPLOY.md` leva alguém do servidor vazio ao painel publicado.
- [ ] A PI publica sozinha um ciclo real, seguindo só `TESTAR.md` e `DEPLOY.md`.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Automatizar o provisionamento (Ansible, Docker) | O MVP precisa de um servidor, não de uma esteira. |
| Vários processos ou vários servidores | O registro de execuções é em memória (P-09): um processo só. |
| Servidor Windows | O roteiro cobre Linux; ver Assumptions. |
| Monitoramento e alertas | Fora do MVP. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Sistema do servidor | Linux com systemd e nginx (ex.: Ubuntu 24.04 LTS) | O README já cita EC2; é o caso mais comum. Se for Windows, o roteiro muda | n (Jaline pode corrigir na revisão) |
| Servidor WSGI | `waitress==3.0.2` | Puro Python, roda em Linux e Windows, multithread num processo só (compatível com P-09). Dependência nova justificada aqui, como o PROJECT_RULES exige | y |
| Threads do waitress | 8 | Suficiente para o painel público de uma instituição | y |
| Endereço do app atrás do nginx | `127.0.0.1:8050`; só o nginx fica exposto | O app não precisa aceitar conexão de fora | y |
| Tamanho máximo do envio no nginx | `client_max_body_size 500m` | Igual ao `MAX_CONTENT_LENGTH` do app (500 MB) | y |
| Tempo máximo de resposta no nginx | `proxy_read_timeout 300s` | O envio de 11 campi processa por mais de 1 minuto | y |
| Backup | `scripts/backup_banco.py` com a API de backup do SQLite, mantendo as 30 cópias mais novas; agendado 1 vez por dia (cron) | Cópia consistente mesmo com o app no ar | y |
| Arquivos de exemplo | Pasta nova `deploy/` | Separa configuração de servidor do código | y |

**Open questions:** none.

---

## User Stories

### P1: Servidor de produção ⭐ MVP

**Acceptance Criteria**:

1. WHEN `run.py` recebe `--producao` THEN the system SHALL chamar `execucoes.iniciar_varredura()` e depois `waitress.serve(app.server, host=H, port=P, threads=8)`, sem chamar `app.run`.
2. WHEN `run.py` roda sem `--producao` THEN the system SHALL continuar chamando `app.run(host, port, debug=False)`, como hoje.
3. The `requirements.txt` SHALL ter `waitress==3.0.2`.

### P1: Exemplos de serviço e proxy ⭐ MVP

**Acceptance Criteria**:

1. The `deploy/calcsistec.service` SHALL rodar `python run.py --producao --host 127.0.0.1 --port 8050` a partir de um ambiente virtual, carregar o `.env` com `EnvironmentFile` e reiniciar sozinho em falha (`Restart=on-failure`).
2. The `deploy/nginx-calcsistec.conf` SHALL redirecionar HTTP para HTTPS, repassar para `http://127.0.0.1:8050` com os cabeçalhos `X-Forwarded-For`, `X-Forwarded-Proto` e `Host`, e ter `client_max_body_size 500m` e `proxy_read_timeout 300s`.

### P1: Backup do banco ⭐ MVP

**Acceptance Criteria**:

1. WHEN `python scripts/backup_banco.py --banco B --destino D --manter N` roda THEN the system SHALL gravar em `D` uma cópia `sistec-AAAAMMDD-HHMMSS.db` feita com `sqlite3.Connection.backup`.
2. WHEN há mais de `N` cópias em `D` THEN the system SHALL apagar as mais antigas até sobrarem `N`.
3. IF o banco `B` não existe THEN the system SHALL sair com código 2 sem criar nada.

### P1: Roteiro de implantação ⭐ MVP

**Acceptance Criteria**:

1. The `DEPLOY.md` SHALL ter a seção "Implantar em servidor Linux", com passos numerados do servidor vazio até `verificar_prontidao_cutover.py` com GO.
2. The roteiro SHALL mostrar como gerar `FLASK_SECRET_KEY` e `ADMIN_PASSWORD_HASH` sem gravar a senha em texto puro.
3. The `DEPLOY.md` SHALL ter a seção "Registro de implantação", com campos para data, servidor, commit implantado, resultado da verificação e primeiro ciclo publicado.

### P1: Primeiro ciclo real ⭐ MVP

**Acceptance Criteria**:

1. WHEN o servidor está no ar THEN a PI SHALL enviar as pastas do mês, conferir a prévia e publicar, sem ajuda, seguindo só `TESTAR.md` e `DEPLOY.md`.
2. The "Registro de implantação" SHALL anotar a data e o resultado desse ciclo.

---

## Edge Cases

- IF `--producao` é usado e o `waitress` não está instalado THEN o `run.py` SHALL sair com a mensagem "Instale as dependências: pip install -r requirements.txt".
- IF `--manter` é 0 ou negativo THEN `backup_banco.py` SHALL sair com código 2.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| IMP-01 | Servidor — AC1..AC3 | Tasks | Pending |
| IMP-02 | Exemplos — AC1 (systemd) | Tasks | Pending |
| IMP-03 | Exemplos — AC2 (nginx) | Tasks | Pending |
| IMP-04 | Backup — AC1..AC3 | Tasks | Pending |
| IMP-05 | Roteiro — AC1..AC3 | Tasks | Pending |
| IMP-06 | Primeiro ciclo — AC1, AC2 | Tasks | Pending |

**Coverage:** 6 total, 6 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `verificar_prontidao_cutover.py` com GO no servidor.
- [ ] Primeiro ciclo real publicado pela PI e registrado no `DEPLOY.md`.
- [ ] Os 4 critérios de pronto de `.specs/MVP.md` marcados.
