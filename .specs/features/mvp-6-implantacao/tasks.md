# MVP 6 — Implantação e primeiro ciclo real — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Exceção combinada com a usuária para executores sem suporte a skills: leia `.specs/MVP-PROTOCOLO.md` inteiro e siga-o; ele aponta o arquivo da skill que substitui a ativação.

Pré-requisito: `mvp-5-coleta-experimental` com Verifier PASS.

---

**Spec**: `.specs/features/mvp-6-implantacao/spec.md`
**Status**: Draft

---

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| `run.py` | unit | `--producao` chama varredura e `waitress.serve` com os argumentos do spec; sem a opção, `app.run` como hoje | `tests/test_run.py` | `python -m pytest tests/test_run.py -q -p no:cacheprovider` |
| `scripts/backup_banco.py` | integration | Cópia consistente; rotação; códigos de saída | `tests/test_backup_banco.py` | `python -m pytest tests/test_backup_banco.py -q -p no:cacheprovider` |
| Arquivos de `deploy/` e documentos | unit (higiene) | Diretivas exigidas pelo spec presentes | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Tarefas humanas | none | — | — | — |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Só documentação e exemplos | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Full | Toda tarefa com `.py` | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Execution Plan

### Phase 1: Artefatos de produção

```
T1 → T2 → T3 → T4 → T5
```

### Phase 2: Servidor e primeiro ciclo

```
T6 → T7 → T8
```

---

## Task Breakdown

### T1: `run.py --producao` com waitress

**What**: Instalar `waitress==3.0.2`, fixá-lo em `requirements.txt` e acrescentar
`--producao` ao `run.py`.
**Where**: `run.py`
**Depends on**: None
**Reuses**: `main(argv)` atual de `run.py`; `tests/test_run.py`
**Requirement**: IMP-01

**Passos**:

1. `pip install waitress==3.0.2`. Se falhar, pare e avise.
2. `requirements.txt`: acrescente a linha `waitress==3.0.2`. O teste de higiene
   compara as linhas do arquivo com uma lista exata: acrescente a linha nova à
   lista do teste (cite IMP-01 AC3 no commit).
3. `run.py`, em `main`: `parser.add_argument("--producao", action="store_true")`.
   Depois de `execucoes.iniciar_varredura()`:

   ```python
   if args.producao:
       try:
           from waitress import serve
       except ImportError:
           sys.exit("Instale as dependências: pip install -r requirements.txt")
       serve(app.server, host=args.host, port=args.port, threads=8)
       return
   app.run(host=args.host, port=args.port, debug=False)
   ```

   (com `import sys` no topo).
4. Testes em `tests/test_run.py`, no mesmo estilo dos que já existem (espiões no
   lugar das funções): com `--producao`, a ordem é varredura → `serve`, com
   `app.server`, `host`, `port` e `threads=8`, e `app.run` **não** é chamado;
   sem `--producao`, nada muda (os testes atuais continuam passando). Para o
   espião de `serve`, faça `monkeypatch.setattr("waitress.serve", espiao)`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: linha de base + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(run): subir em producao com waitress num processo`

---

### T2: Exemplo de serviço systemd

**What**: `deploy/calcsistec.service`.
**Where**: `deploy/calcsistec.service` (novo)
**Depends on**: T1
**Reuses**: nenhum
**Requirement**: IMP-02

**Passos**:

1. Conteúdo:

   ```ini
   # Exemplo de serviço systemd para o CalcSISTEC.
   # Copie para /etc/systemd/system/calcsistec.service e ajuste os caminhos.
   [Unit]
   Description=CalcSISTEC - painel de acompanhamento do Sistec
   After=network.target

   [Service]
   Type=simple
   User=calcsistec
   Group=calcsistec
   WorkingDirectory=/opt/calcsistec
   EnvironmentFile=/opt/calcsistec/.env
   ExecStart=/opt/calcsistec/.venv/bin/python run.py --producao --host 127.0.0.1 --port 8050
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

2. Teste de higiene: o arquivo existe e contém `EnvironmentFile=`,
   `run.py --producao --host 127.0.0.1 --port 8050` e `Restart=on-failure`.
3. README, seção "Estrutura": linha de `deploy/` ("exemplos de configuração do
   servidor de produção").

**Done when**:

- [ ] Teste de higiene novo passa
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(deploy): exemplo de servico systemd`

---

### T3: Exemplo de configuração do nginx

**What**: `deploy/nginx-calcsistec.conf`.
**Where**: `deploy/nginx-calcsistec.conf` (novo)
**Depends on**: T2
**Reuses**: nenhum
**Requirement**: IMP-03

**Passos**:

1. Conteúdo (troque `painel.exemplo.edu.br` só no `DEPLOY.md`, aqui fica o exemplo):

   ```nginx
   # Exemplo de nginx na frente do CalcSISTEC. Copie para /etc/nginx/sites-available/
   # e troque painel.exemplo.edu.br pelo endereço real. Certificado: certbot --nginx.
   server {
       listen 80;
       server_name painel.exemplo.edu.br;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name painel.exemplo.edu.br;

       ssl_certificate /etc/letsencrypt/live/painel.exemplo.edu.br/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/painel.exemplo.edu.br/privkey.pem;

       client_max_body_size 500m;

       location / {
           proxy_pass http://127.0.0.1:8050;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 300s;
       }
   }
   ```

2. Teste de higiene: o arquivo contém `return 301 https://`,
   `proxy_pass http://127.0.0.1:8050`, `X-Forwarded-For`, `X-Forwarded-Proto`,
   `client_max_body_size 500m` e `proxy_read_timeout 300s`.

**Done when**:

- [ ] Teste de higiene novo passa
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider`

**Tests**: unit
**Gate**: quick

**Commit**: `feat(deploy): exemplo de nginx com https`

---

### T4: Script de backup do banco

**What**: `scripts/backup_banco.py`.
**Where**: `scripts/backup_banco.py` (novo)
**Depends on**: T3
**Reuses**: nenhum
**Requirement**: IMP-04

**Passos**:

1. Código:

   ```python
   """Copia o banco do CalcSISTEC com a API de backup do SQLite e mantém só as N cópias mais novas.

   Uso: python scripts/backup_banco.py --banco app/data/sistec.db --destino /var/backups/calcsistec --manter 30
   """

   import argparse
   import pathlib
   import sqlite3
   import sys
   from datetime import datetime


   def fazer_backup(banco, destino, manter, agora=None):
       banco = pathlib.Path(banco)
       destino = pathlib.Path(destino)
       if not banco.exists():
           raise FileNotFoundError(f"banco não encontrado: {banco}")
       if manter < 1:
           raise ValueError("--manter precisa ser 1 ou mais")
       destino.mkdir(parents=True, exist_ok=True)
       carimbo = (agora or datetime.now()).strftime("%Y%m%d-%H%M%S")
       alvo = destino / f"sistec-{carimbo}.db"
       origem = sqlite3.connect(banco)
       copia = sqlite3.connect(alvo)
       try:
           origem.backup(copia)
       finally:
           copia.close()
           origem.close()
       copias = sorted(destino.glob("sistec-*.db"))
       for antiga in copias[:-manter]:
           antiga.unlink()
       return alvo


   def main(argv=None):
       parser = argparse.ArgumentParser(description="Backup do banco do CalcSISTEC.")
       parser.add_argument("--banco", required=True)
       parser.add_argument("--destino", required=True)
       parser.add_argument("--manter", type=int, default=30)
       args = parser.parse_args(argv)
       try:
           alvo = fazer_backup(args.banco, args.destino, args.manter)
       except (FileNotFoundError, ValueError) as erro:
           print(erro)
           return 2
       print(f"Backup gravado em {alvo}")
       return 0


   if __name__ == "__main__":
       sys.exit(main())
   ```

2. `tests/test_backup_banco.py` (tudo em `tmp_path`): cria um banco com uma
   tabela e 3 linhas; `fazer_backup` grava `sistec-AAAAMMDD-HHMMSS.db` e a cópia
   tem as 3 linhas; com `agora` diferente em 4 chamadas e `manter=2`, sobram as
   2 mais novas; banco inexistente → `main` devolve 2 e o destino não foi criado;
   `--manter 0` → `main` devolve 2.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(backup): script de backup do banco com rotacao`

---

### T5: Roteiro "Implantar em servidor Linux" no `DEPLOY.md`

**What**: Seção nova no `DEPLOY.md` com passos numerados e a seção "Registro de
implantação".
**Where**: `DEPLOY.md`
**Depends on**: T4
**Reuses**: `deploy/*`, `scripts/backup_banco.py`, `scripts/verificar_prontidao_cutover.py`, `.env.example`
**Requirement**: IMP-05

**Passos** — escreva, em frases curtas, estes passos:

1. Criar o usuário `calcsistec` e clonar o repositório em `/opt/calcsistec`.
2. Criar o venv com Python 3.12 e `pip install -r requirements.txt`.
3. `cp .env.example .env` e preencher:
   - `FLASK_SECRET_KEY`: gerar com `python -c "import secrets; print(secrets.token_hex(32))"`;
   - `ADMIN_EMAIL` e `ADMIN_PASSWORD_HASH`: gerar o hash com o comando do próprio
     `.env.example`, digitando a senha só no terminal;
   - `CALCSISTEC_HTTPS=1`, `CALCSISTEC_PROXY=1`, `ANO_BASE`.
   `chmod 600 .env` e dono `calcsistec`.
4. Copiar `deploy/calcsistec.service`, `systemctl enable --now calcsistec` e
   conferir com `systemctl status calcsistec`.
5. Copiar `deploy/nginx-calcsistec.conf`, trocar o endereço, `certbot --nginx`,
   `nginx -t` e recarregar.
6. Agendar o backup diário no `crontab` do usuário `calcsistec`, por exemplo
   `0 2 * * * cd /opt/calcsistec && .venv/bin/python scripts/backup_banco.py --banco app/data/sistec.db --destino /var/backups/calcsistec --manter 30`.
7. Rodar `python scripts/verificar_prontidao_cutover.py` com o `.env` carregado
   (ex.: `set -a; . ./.env; set +a`) e conferir GO nos critérios técnicos.
8. Abrir `https://<endereço>/admin/login`, concluir a instalação e publicar o primeiro ciclo (tarefa T7).
9. Para atualizar a versão: `git pull`, `pip install -r requirements.txt`,
   `systemctl restart calcsistec`.

Depois, a seção "Registro de implantação" com os campos: data, servidor,
commit implantado (`git rev-parse --short HEAD`), resultado da verificação,
primeiro ciclo publicado (mês e data), responsável.

Teste de higiene: `DEPLOY.md` contém `Implantar em servidor Linux`,
`Registro de implantação`, `deploy/calcsistec.service`,
`deploy/nginx-calcsistec.conf`, `scripts/backup_banco.py` e `secrets.token_hex`.

**Done when**:

- [ ] Teste de higiene novo passa
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider`

**Tests**: unit
**Gate**: quick

**Commit**: `docs(deploy): roteiro de implantacao em servidor linux`

---

### T6: [HUMANO] Implantar no servidor

**What**: Alguém com acesso ao servidor segue a seção "Implantar em servidor
Linux" e preenche o "Registro de implantação" até a verificação com GO.
**Where**: `DEPLOY.md`
**Depends on**: None
**Reuses**: roteiro de T5
**Requirement**: IMP-05

**O agente executor para aqui** e avisa: "T6 é humana: implantar no servidor".
Dúvida ou erro no roteiro vira tarefa de correção neste arquivo.

**Done when**:

- [ ] "Registro de implantação" com data, servidor, commit e verificação GO

**Tests**: none
**Gate**: build

**Commit**: `docs(deploy): registrar a implantacao no servidor`

---

### T7: [HUMANO] A PI publica o primeiro ciclo real sozinha

**What**: A PI envia as pastas do mês pelo servidor, confere a prévia e publica,
sem ajuda, seguindo só `TESTAR.md` e `DEPLOY.md`. Anota no "Registro de
implantação" o mês, a data e qualquer dúvida que teve (cada dúvida vira ajuste
de documentação).
**Where**: `DEPLOY.md`
**Depends on**: T6
**Reuses**: nenhum
**Requirement**: IMP-06

**O agente executor para aqui** e avisa: "T7 é humana: primeiro ciclo real da PI".

**Done when**:

- [ ] Registro com o ciclo publicado e as dúvidas anotadas

**Tests**: none
**Gate**: build

**Commit**: `docs(deploy): registrar o primeiro ciclo real publicado`

---

### T8: Fechar o MVP

**What**: Em `.specs/MVP.md`, marcar cada critério de pronto com a evidência
(arquivo e commit). Em `.specs/STATE.md`, "Estado atual" com o MVP concluído e o
handoff desta feature.
**Where**: `.specs/MVP.md`
**Depends on**: T7
**Reuses**: nenhum
**Requirement**: IMP-06

**Done when**:

- [ ] Os 4 critérios de pronto marcados com evidência
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`

**Tests**: none
**Gate**: build

**Commit**: `docs(mvp): fechar o mvp com as evidencias`

---

## Verificação (depois de T8)

Verifier independente. Sensor mínimo: `--producao` chamar `app.run`; `threads=1`;
backup copiar o arquivo com `shutil.copy` em vez da API do SQLite (o teste de
consistência precisa pegar se houver); rotação apagar a mais nova.

---

## Phase Execution Map

```
Phase 1:  T1 → T2 → T3 → T4 → T5
Phase 2:  T6 → T7 → T8
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | `run.py` + 1 linha de `requirements.txt` | ✅ |
| T2–T5 | 1 arquivo cada | ✅ |
| T6–T8 | registro humano e fechamento | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | T2 | T2 → T3 | ✅ |
| T4 | T3 | T3 → T4 | ✅ |
| T5 | T4 | T4 → T5 | ✅ |
| T6 | None | início da fase 2 | ✅ |
| T7 | T6 | T6 → T7 | ✅ |
| T8 | T7 | T7 → T8 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | `run.py` | unit | unit | ✅ |
| T2, T3, T5 | exemplos e documentos | unit (higiene) | unit | ✅ |
| T4 | script de backup | integration | integration | ✅ |
| T6–T8 | tarefas humanas e registro | none | none | ✅ |
