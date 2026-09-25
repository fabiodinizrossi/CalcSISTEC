# MVP 1 — Refatoração de `app.py` e das docstrings — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Exceção combinada com a usuária para executores sem suporte a skills: leia `.specs/MVP-PROTOCOLO.md` inteiro e siga-o; ele aponta o arquivo da skill que substitui a ativação.

---

**Spec**: `.specs/features/mvp-1-refatoracao/spec.md`
**Design**: não há `design.md`; o "Mapa de rotas" do spec é o design.
**Status**: Draft

---

## Test Coverage Matrix

> Diretrizes: `AGENTS.md`, `.specs/PROJECT_RULES.md` (Princípio IV), `.specs/MVP-PROTOCOLO.md`. Sem lint configurado.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Rotas (`app/rotas/*.py`) | integration | Cada URL movida aparece em `server.url_map` com o endpoint do blueprint novo; os testes de rota existentes continuam passando sem mudar asserção | `tests/test_rotas_modulos.py` + testes existentes `tests/test_admin_*.py` | `python -m pytest -q -p no:cacheprovider` |
| `app/app.py` | unit | Nenhuma `@server.route`; no máximo 150 linhas | `tests/test_rotas_modulos.py` | `python -m pytest tests/test_rotas_modulos.py -q -p no:cacheprovider` |
| Docstrings e comentários | unit (higiene) | Nenhum padrão proibido nos diretórios já limpos; a mensagem de falha cita arquivo, linha e trecho | `tests/test_higiene_docstrings.py` | `python -m pytest tests/test_higiene_docstrings.py -q -p no:cacheprovider` |
| `README.md`, `.specs/STATE.md` | unit (higiene) / none | O teste de higiene existente já exige que o README cite cada subdiretório de `app/` | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Nunca nesta feature: toda tarefa mexe em `.py` usado pelo app | — |
| Full | Toda tarefa | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Receita R1 — mover um grupo de rotas para `app/rotas/`

Use em T2 a T9. Leia a receita inteira antes de começar a tarefa.

1. Leia em `app/app.py` todas as funções listadas na tarefa, do decorador até a
   última linha. Anote quais nomes cada uma usa (funções importadas, constantes,
   helpers de `app/rotas/comum.py`).
2. Crie o módulo novo com este esqueleto (troque `envio` pelo nome da tarefa):

   ```python
   """Rotas de <área em uma frase>."""

   import flask

   envio_bp = flask.Blueprint("envio_bp", __name__)
   ```

3. Recorte as funções de `app/app.py` e cole no módulo novo. Troque cada
   `@server.route(` por `@envio_bp.route(`, sem mudar URL nem `methods`.
   Troque `@server.before_request` por `@<nome>_bp.before_app_request`.
4. No módulo novo, importe exatamente os nomes que as funções usam, **pelo mesmo
   nome** que tinham em `app/app.py` (ex.: `from app.data.historico import iniciar as historico_iniciar`).
   Isso é o que permite aos testes trocarem o nome no módulo novo.
5. Helpers de `app/rotas/comum.py`: importe como módulo e chame com prefixo,
   por exemplo `from app.rotas import comum` e `comum.admin_email()`.
6. Em `app/app.py`: apague as funções movidas, apague os imports que ficaram sem
   uso (confira cada um com busca no arquivo) e registre o blueprint junto dos
   outros: `server.register_blueprint(envio_bp)`, com
   `from app.rotas.envio import envio_bp` no topo.
7. Não importe `app.app` dentro de `app/rotas/` (import circular).
8. Atualize os testes que fazem `monkeypatch` nos nomes movidos (seção 5 de
   `.specs/MVP-PROTOCOLO.md`). Encontre-os com
   `git grep -n "app_module, \"<nome>\"" tests` para cada nome movido.
9. Acrescente em `tests/test_rotas_modulos.py` uma linha por URL movida na lista
   `ROTAS_ESPERADAS` (ver T1).
10. Rode o gate full.

---

## Execution Plan

### Phase 1: Rotas em `app/rotas/`

```
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9
```

### Phase 2: Docstrings e comentários

```
T10 → T11 → T12 → T13 → T14 → T15 → T16
```

---

## Task Breakdown

### T1: Criar `app/rotas/`, o módulo `comum` e o teste de rotas

**What**: Criar o pacote `app/rotas/` com `__init__.py` vazio e `comum.py` com as
quatro funções auxiliares; criar `tests/test_rotas_modulos.py`; citar
`app/rotas/` no README.
**Where**: `app/rotas/comum.py` (novo)
**Depends on**: None
**Reuses**: `app/app.py:89` (`_contexto_base`), `:254` (`_admin_email`), `:258` (`_execucao_da_sessao`), `:265` (`_ano_base_config`)
**Requirement**: REF-01, REF-04

**Passos**:

1. Crie `app/rotas/__init__.py` vazio.
2. Crie `app/rotas/comum.py` com docstring de módulo "Funções auxiliares
   usadas por mais de um grupo de rotas administrativas." e as funções, já
   com o nome novo, sem sublinhado:
   `contexto_base()`, `admin_email()`, `execucao_da_sessao()`,
   `ano_base_config()`. Copie o corpo de cada uma de `app/app.py` sem mudar a
   lógica. Traga os imports que elas usam (`flask`, `os`,
   `get_contato_email`, `dados_instituicao`, `execucoes`).
3. Em `app/app.py`, apague as quatro funções e troque cada chamada:
   `_contexto_base()` → `comum.contexto_base()`, `_admin_email()` →
   `comum.admin_email()`, `_execucao_da_sessao()` →
   `comum.execucao_da_sessao()`, `_ano_base_config()` →
   `comum.ano_base_config()`. Acrescente `from app.rotas import comum`.
4. Em `tests/test_admin_envio_salvar.py:155`, troque
   `app_module._ano_base_config()` por `comum.ano_base_config()` com
   `from app.rotas import comum` no topo. Procure outros usos:
   `git grep -n "_ano_base_config\|_admin_email\|_contexto_base\|_execucao_da_sessao" tests app`.
5. Crie `tests/test_rotas_modulos.py`:

   ```python
   """Cada rota administrativa mora no blueprint da sua área (REF-01, REF-02)."""

   import pathlib

   import pytest

   import app.app as app_module

   RAIZ = pathlib.Path(__file__).resolve().parent.parent

   # (URL como aparece em url_map, método, prefixo esperado do endpoint)
   ROTAS_ESPERADAS = []


   def _endpoint(url, metodo):
       for regra in app_module.server.url_map.iter_rules():
           if regra.rule == url and metodo in regra.methods:
               return regra.endpoint
       return None


   @pytest.mark.parametrize("url,metodo,prefixo", ROTAS_ESPERADAS)
   def test_rota_mora_no_blueprint_da_area(url, metodo, prefixo):
       endpoint = _endpoint(url, metodo)
       assert endpoint is not None, f"{metodo} {url} não está registrada"
       assert endpoint.startswith(prefixo + "."), f"{metodo} {url} está em {endpoint}, esperado {prefixo}"
   ```

   Com `ROTAS_ESPERADAS` vazia o teste parametrizado não gera casos; isso é
   esperado nesta tarefa. Acrescente também:

   ```python
   def test_pacote_rotas_existe_com_modulo_comum():
       assert (RAIZ / "app" / "rotas" / "__init__.py").exists()
       from app.rotas import comum
       for nome in ("contexto_base", "admin_email", "execucao_da_sessao", "ano_base_config"):
           assert callable(getattr(comum, nome))
   ```

6. No `README.md`, seção "Estrutura", acrescente a linha de `app/rotas/`
   ("rotas administrativas do Flask, um módulo por área") no mesmo formato das
   outras linhas. Na seção "Onde mexer", na linha "Mudar uma rota
   administrativa", troque `app/app.py` por `app/rotas/` (o módulo da área).
   O teste de higiene já existente exige que o README cite todo subdiretório de
   `app/`; sem este passo ele falha.

**Done when**:

- [ ] `app/app.py` não define mais as quatro funções e chama `comum.*`
- [ ] `tests/test_rotas_modulos.py` existe e passa
- [ ] README cita `app/rotas/` em "Estrutura" e em "Onde mexer"
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: linha de base + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): criar app/rotas com as funcoes comuns`

---

### T2: Mover as rotas públicas para `app/rotas/publico.py`

**What**: `GET /matriculas` (`matriculas_legado`, `app/app.py:210`) e
`GET /branding/logo` (`branding_logo`, `app/app.py:1007`) vão para o blueprint
`publico_bp`.
**Where**: `app/rotas/publico.py` (novo)
**Depends on**: T1
**Reuses**: Receita R1
**Requirement**: REF-01

**Passos**: siga a Receita R1. Em `ROTAS_ESPERADAS`, acrescente
`("/matriculas", "GET", "publico_bp")` e `("/branding/logo", "GET", "publico_bp")`.
Se `branding_logo` usar `UPLOADS_BRANDING_DIR` ou `DEFAULT_LOGO_PATH`,
importe `DEFAULT_LOGO_PATH` de `app.data.config_store` e **mova**
`UPLOADS_BRANDING_DIR` para `app/rotas/configuracoes.py` só em T5; até lá,
defina-o em `publico.py` com o mesmo valor e, em T5, faça
`configuracoes.py` importá-lo de `publico.py` (uma única definição).
Atenção: `os.path.dirname(__file__)` muda de pasta quando o código sai de
`app/app.py` para `app/rotas/publico.py`. O caminho precisa continuar
apontando para `app/data/uploads/branding`: use
`os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads", "branding")`.

**Done when**:

- [ ] As duas rotas respondem como antes (testes existentes verdes)
- [ ] `UPLOADS_BRANDING_DIR` aponta para `app/data/uploads/branding` (teste novo em `tests/test_rotas_modulos.py` compara com `RAIZ / "app" / "data" / "uploads" / "branding"`)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover rotas publicas para app/rotas/publico`

---

### T3: Mover login, logout e recuperação de acesso para `app/rotas/acesso.py`

**What**: `/admin/login` (`:93`), `/admin/logout` (`:134`), `/recuperar-acesso`
(`:217`), o `before_request` `_exigir_sessao_previa` (`:242`) e as constantes
`_MSG_EMAIL_INVALIDO`, `_MSG_SENHA_CURTA`, `_MSG_CONFIG_AUSENTE` (`:77-83`) vão
para `acesso_bp`.
**Where**: `app/rotas/acesso.py` (novo)
**Depends on**: T2
**Reuses**: Receita R1
**Requirement**: REF-01, REF-03

**Passos**: siga a Receita R1. `_exigir_sessao_previa` vira
`@acesso_bp.before_app_request`. Os testes que trocam
`credenciais_configuradas`, `autenticar_sessao` e `_exigir_sessao_previa` em
`app_module` (`tests/test_admin_paginas.py`, `tests/test_admin_previa_guarda.py`
e outros achados com `git grep`) passam a trocar em `app.rotas.acesso`.
`ROTAS_ESPERADAS`: `("/admin/login", "GET", "acesso_bp")`,
`("/admin/login", "POST", "acesso_bp")`, `("/admin/logout", "GET", "acesso_bp")`,
`("/recuperar-acesso", "GET", "acesso_bp")`.

**Done when**:

- [ ] Login, logout e a guarda de `/admin/previa/...` sem sessão funcionam como antes (testes existentes verdes)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover login e logout para app/rotas/acesso`

---

### T4: Mover a instalação para `app/rotas/instalacao.py`

**What**: `/admin/instalacao` (`:140`), o `before_request` `_exigir_instalacao`
(`:227`) e `_ROTAS_SEM_INSTALACAO` (`:224`) vão para `instalacao_bp`.
**Where**: `app/rotas/instalacao.py` (novo)
**Depends on**: T3
**Reuses**: Receita R1
**Requirement**: REF-01, REF-03

**Passos**: siga a Receita R1. O módulo de dados `app.data.instalacao` tem o mesmo
nome curto do módulo novo: dentro de `app/rotas/instalacao.py`, importe-o como
`from app.data import instalacao as dados_instalacao` e troque os usos. Nos
testes, `monkeypatch.setattr(app_module.instalacao, "concluida", ...)` vira
`monkeypatch.setattr(instalacao_mod, "concluida", ...)` com
`import app.data.instalacao as instalacao_mod` (seção 5 do protocolo; há
ocorrências em `tests/test_admin_campi.py`, `tests/test_admin_envio.py`,
`tests/test_admin_paginas.py`). `ROTAS_ESPERADAS`:
`("/admin/instalacao", "GET", "instalacao_bp")`, `("/admin/instalacao", "POST", "instalacao_bp")`.

**Done when**:

- [ ] Sem instalação concluída, uma tela administrativa autenticada continua redirecionando para `/admin/instalacao` (testes existentes verdes)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover a instalacao para app/rotas/instalacao`

---

### T5: Mover as configurações para `app/rotas/configuracoes.py`

**What**: `/admin/config` (`:752`, a maior função do arquivo) e
`/admin/config/captura` (`:986`), mais `LOGO_MAX_BYTES`, vão para
`configuracoes_bp`. `UPLOADS_BRANDING_DIR` passa a ser importado de
`app.rotas.publico` (definido em T2).
**Where**: `app/rotas/configuracoes.py` (novo)
**Depends on**: T4
**Reuses**: Receita R1
**Requirement**: REF-01

**Passos**: siga a Receita R1. O teste que troca `DEFAULT_LOGO_PATH` em
`app_module` passa a trocar no módulo onde a rota o lê. `ROTAS_ESPERADAS`:
`("/admin/config", "GET", "configuracoes_bp")`, `("/admin/config", "POST", "configuracoes_bp")`,
`("/admin/config/captura", "GET", "configuracoes_bp")`.

**Done when**:

- [ ] Upload de logotipo, reset, contato e quantidade de perfis funcionam como antes (testes existentes verdes)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover configuracoes para app/rotas/configuracoes`

---

### T6: Mover publicação, desfazer e histórico para `app/rotas/publicacao.py`

**What**: `/admin/atualizar/publicar` (`:719`), `/admin/atualizar/desfazer`
(`:728`), `/admin/historico` (`:740`) e `historico_iniciar_e_encerrar` (`:269`)
vão para `publicacao_bp`.
**Where**: `app/rotas/publicacao.py` (novo)
**Depends on**: T5
**Reuses**: Receita R1
**Requirement**: REF-01

**Passos**: siga a Receita R1. Os testes que trocam `historico_listar` em
`app_module` (`tests/test_admin_paginas.py:158,169,176`) passam a trocar em
`app.rotas.publicacao`. `ROTAS_ESPERADAS`:
`("/admin/atualizar/publicar", "POST", "publicacao_bp")`,
`("/admin/atualizar/desfazer", "POST", "publicacao_bp")`,
`("/admin/historico", "GET", "publicacao_bp")`.

**Done when**:

- [ ] Publicar, desfazer e a tela de histórico respondem como antes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover publicacao e historico para app/rotas/publicacao`

---

### T7: Mover o envio de pastas para `app/rotas/envio.py`

**What**: `/admin/atualizar/envio` (`:407`) e os helpers
`_resumo_arquivos_envio` (`:335`), `_matriculas_orfas_envio` (`:343`),
`_cadastrar_unidades_do_envio` (`:355`), `_completar_unidades_incompletas`
(`:388`) vão para `envio_bp`.
**Where**: `app/rotas/envio.py` (novo)
**Depends on**: T6
**Reuses**: Receita R1
**Requirement**: REF-01

**Passos**: siga a Receita R1. O módulo `app.sistec.envio` tem o mesmo nome
curto: dentro de `app/rotas/envio.py`, importe-o como
`from app.sistec import envio as sistec_envio` e troque os usos (`envio.ler_pastas` →
`sistec_envio.ler_pastas` etc.). Este é o grupo com mais `monkeypatch`:
`listar_campi`, `historico_iniciar`, `historico_encerrar`, `DEFAULT_DB_PATH`,
`ano_base_ativo`, `preparar_versao` e `navegador` em
`tests/test_admin_envio.py`, `tests/test_admin_envio_salvar.py`,
`tests/test_admin_envio_salvar_previa.py`, `tests/test_admin_envio_polling.py`.
Troque o alvo só nos testes que exercitam `/admin/atualizar/envio`; os que
exercitam salvar/descartar mudam em T9. Se um mesmo teste exercita as duas
rotas, troque o nome **nos dois módulos** (dois `monkeypatch.setattr`), e só
nesse caso. `ROTAS_ESPERADAS`: `("/admin/atualizar/envio", "POST", "envio_bp")`.

**Done when**:

- [ ] Envio válido, pasta vazia, CSV inválido e falha ao montar a prévia respondem como antes (testes existentes verdes)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover o envio de pastas para app/rotas/envio`

---

### T8: Mover a coleta pelo Sistec para `app/rotas/coleta_sistec.py`

**What**: `/admin/atualizar/sistec` (`:285`), `/admin/atualizar/sistec/login-feito`
(`:309`), `/admin/atualizar/sistec/cancelar` (`:318`), `/admin/atualizar/execucoes`
(`:528`) e `/admin/atualizar/execucoes/<execucao_id>/iniciar`, `/retomar`,
`/cancelar` (`:544`, `:560`, `:573`) vão para `coleta_sistec_bp`.
**Where**: `app/rotas/coleta_sistec.py` (novo)
**Depends on**: T7
**Reuses**: Receita R1
**Requirement**: REF-01

**Passos**: siga a Receita R1. `ROTAS_ESPERADAS`: uma linha para cada uma das 7
rotas, todas com método `POST` e prefixo `coleta_sistec_bp`. Em `url_map`, a
parte variável aparece como `<execucao_id>` (ex.:
`"/admin/atualizar/execucoes/<execucao_id>/iniciar"`).

**Done when**:

- [ ] Os testes de execução e de navegador existentes continuam verdes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover a coleta pelo sistec para app/rotas/coleta_sistec`

---

### T9: Mover a tela de atualizar, salvar e descartar; enxugar `app.py`

**What**: `GET /admin/atualizar` (`:277`), `GET /admin/atualizar/execucao`
(`:650`), `/admin/atualizar/execucoes/<execucao_id>/salvar` (`:588`) e
`/descartar` (`:635`) vão para `atualizar_bp`. Depois, `app/app.py` fica só
com o que o spec lista no fim do "Mapa de rotas".
**Where**: `app/rotas/atualizar.py` (novo)
**Depends on**: T8
**Reuses**: Receita R1
**Requirement**: REF-01, REF-02

**Passos**:

1. Siga a Receita R1 para as quatro rotas. Troque nos testes os alvos de
   `monkeypatch` que essas rotas leem (`DEFAULT_DB_PATH`, `ano_base_ativo`,
   `historico_*`, conforme o que a rota usa).
2. Apague de `app/app.py` todo import que ficou sem uso e todo comentário que
   descrevia rotas que saíram. Mantenha a ordem: `init_db` antes de registrar
   blueprints, `init_shell` depois.
3. `ROTAS_ESPERADAS`: as quatro rotas com prefixo `atualizar_bp`.
4. Acrescente em `tests/test_rotas_modulos.py`:

   ```python
   def test_app_py_so_monta_o_app():
       texto = (RAIZ / "app" / "app.py").read_text(encoding="utf-8")
       assert "@server.route" not in texto
       assert "before_request" not in texto
       assert len(texto.splitlines()) <= 150
   ```

**Done when**:

- [ ] `app/app.py` sem `@server.route`, sem `before_request` e com no máximo 150 linhas
- [ ] `ROTAS_ESPERADAS` tem todas as URLs do "Mapa de rotas" do spec
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `refactor(rotas): mover a tela de atualizar e enxugar app.py`

---

### T10: Teste de higiene das docstrings e limpeza de `app/domain/`

**What**: Criar `tests/test_higiene_docstrings.py` com os padrões proibidos do
spec, aplicados só a docstrings e comentários, e limpar `app/domain/`.
**Where**: `tests/test_higiene_docstrings.py` (novo)
**Depends on**: None
**Reuses**: seção "Padrões proibidos" do spec; seção 6 do protocolo
**Requirement**: REF-05, REF-06

**Passos**:

1. Crie o teste:

   ```python
   """Docstrings e comentários dizem o que o código faz, sem IDs de spec (REF-05)."""

   import ast
   import io
   import pathlib
   import re
   import tokenize

   import pytest

   RAIZ = pathlib.Path(__file__).resolve().parent.parent

   PADROES = [
       re.compile(r"\b(BR-MIGRAR|BR-HUMANA|RISK|UPL|CPR|PVP|MAT|DS|AD|RF|RN|DEV|AMB|WDG|LIM|DEP|DOC|EST|PT|AGG|BC|REF|PAR|PBI|SEG|EXP|IMP)-\d+"),
       re.compile(r"\b[DP]-\d+\b"),
       re.compile(r"\bT-?\d{1,3}\b"),
       re.compile(r"\bTarefa \d+"),
       re.compile(r"roadmap\.md|data-delta\.md|f0-resultado\.md|data_migration_plan\.md|target_[a-z_]+\.md|paradigm_decision\.md|parity_tests|parity_specs|onboarding\.md|regression-watch|cutover_plan|_reversa_|reconstruction-plan|\d{3}-[a-z]+-[a-z-]+"),
   ]

   # Cada tarefa de limpeza acrescenta aqui o que limpou.
   ALVOS_LIMPOS = [
       "app/domain",
   ]


   def _arquivos(alvo):
       caminho = RAIZ / alvo
       if caminho.is_file():
           return [caminho]
       return sorted(caminho.rglob("*.py"))


   def _trechos(caminho):
       fonte = caminho.read_text(encoding="utf-8")
       for tok in tokenize.generate_tokens(io.StringIO(fonte).readline):
           if tok.type == tokenize.COMMENT:
               yield tok.start[0], tok.string
       arvore = ast.parse(fonte)
       for no in ast.walk(arvore):
           if isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
               doc = ast.get_docstring(no, clean=False)
               if doc:
                   linha = no.body[0].lineno if no.body else 1
                   yield linha, doc


   @pytest.mark.parametrize("alvo", ALVOS_LIMPOS)
   def test_docstrings_e_comentarios_sem_ids_de_spec(alvo):
       achados = []
       for caminho in _arquivos(alvo):
           for linha, texto in _trechos(caminho):
               for padrao in PADROES:
                   m = padrao.search(texto)
                   if m:
                       achados.append(f"{caminho.relative_to(RAIZ)}:{linha}: {m.group(0)!r}")
       assert not achados, "Docstring ou comentário com ID de spec:\n" + "\n".join(achados)


   @pytest.mark.parametrize("alvo", ALVOS_LIMPOS)
   def test_nenhuma_docstring_ficou_vazia(alvo):
       vazias = []
       for caminho in _arquivos(alvo):
           arvore = ast.parse(caminho.read_text(encoding="utf-8"))
           for no in ast.walk(arvore):
               if isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                   doc = ast.get_docstring(no)
                   if doc is not None and not doc.strip():
                       vazias.append(f"{caminho.relative_to(RAIZ)}:{getattr(no, 'lineno', 1)}")
       assert not vazias, "Docstring vazia:\n" + "\n".join(vazias)
   ```

2. O teste novo contém, de propósito, termos que `tests/test_higiene_repositorio.py`
   proíbe em `tests/*.py` (`_reversa_`, `cutover_plan`, `parity_tests`). Abra
   `tests/test_higiene_repositorio.py`, ache onde ele exclui a si mesmo da
   varredura de `tests/*.py` e acrescente `test_higiene_docstrings.py` na mesma
   exclusão, com um comentário de uma linha: "lista os termos proibidos de
   propósito". Não mude mais nada nesse arquivo.
3. Rode o teste novo e veja a lista de achados em `app/domain/`.
4. Reescreva cada docstring e comentário achado. Regras:
   - tire o ID, o "Tarefa NN", o nome de tarefa e o caminho de documento;
   - tire o histórico ("antes era X", "a Tarefa 07 usava Y", "correção de …");
   - mantenha, em frase direta, **o que** a função faz e **a regra** que ela
     segue (ex.: "Concluídos = CONCLUÍDA ou INTEGRALIZADA.");
   - comentário que só tinha o ID: apague a linha inteira.
5. Rode o script da seção 6 do protocolo: tem de listar `[]`.

**Done when**:

- [ ] `tests/test_higiene_docstrings.py` passa com `ALVOS_LIMPOS = ["app/domain"]`
- [ ] `tests/test_higiene_repositorio.py` continua passando, com a exclusão nova
- [ ] Script da seção 6 do protocolo lista `[]`
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(domain): docstrings de app/domain sem ids de spec`

---

### T11: Limpar docstrings e comentários de `app/data/`

**What**: Mesmo trabalho de T10 em `app/data/`.
**Where**: `app/data/`
**Depends on**: T10
**Reuses**: passos 3 a 5 de T10
**Requirement**: REF-05, REF-06

**Passos**: acrescente `"app/data"` em `ALVOS_LIMPOS` e siga os passos 3 a 5 de T10.

**Done when**:

- [ ] Teste de higiene passa com `app/data` na lista
- [ ] Script da seção 6 do protocolo lista `[]`
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(data): docstrings de app/data sem ids de spec`

---

### T12: Limpar docstrings e comentários de `app/sistec/`

**What**: Mesmo trabalho de T10 em `app/sistec/`.
**Where**: `app/sistec/`
**Depends on**: T11
**Reuses**: passos 3 a 5 de T10
**Requirement**: REF-05, REF-06

**Passos**: acrescente `"app/sistec"` em `ALVOS_LIMPOS` e siga os passos 3 a 5 de T10.

**Done when**:

- [ ] Teste de higiene passa com `app/sistec` na lista
- [ ] Script da seção 6 do protocolo lista `[]`
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(sistec): docstrings de app/sistec sem ids de spec`

---

### T13: Limpar docstrings e comentários de `app/pages/` e `app/components/`

**What**: Mesmo trabalho de T10 nos dois diretórios de interface.
**Where**: `app/pages/`
**Depends on**: T12
**Reuses**: passos 3 a 5 de T10
**Requirement**: REF-05, REF-06

**Passos**: acrescente `"app/pages"` e `"app/components"` em `ALVOS_LIMPOS` e
siga os passos 3 a 5 de T10.

**Done when**:

- [ ] Teste de higiene passa com os dois diretórios na lista
- [ ] Script da seção 6 do protocolo lista `[]`
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(pages): docstrings das paginas e componentes sem ids de spec`

---

### T14: Limpar `app/rotas/`, os módulos da raiz de `app/` e `run.py`

**What**: Mesmo trabalho de T10 em `app/rotas/`, `app/app.py`, `app/shell.py`,
`app/auth.py`, `app/config.py`, `app/admin_campi.py`, `app/__init__.py` e `run.py`.
**Where**: `app/rotas/`
**Depends on**: T13
**Reuses**: passos 3 a 5 de T10
**Requirement**: REF-05, REF-06

**Passos**: acrescente em `ALVOS_LIMPOS`: `"app/rotas"`, `"app/app.py"`,
`"app/shell.py"`, `"app/auth.py"`, `"app/config.py"`, `"app/admin_campi.py"`,
`"app/__init__.py"`, `"run.py"`. Siga os passos 3 a 5 de T10. Confira com
`git ls-files "app/*.py"` que nenhum `.py` da raiz de `app/` ficou de fora.

**Done when**:

- [ ] Teste de higiene passa com esses alvos na lista
- [ ] Todo `.py` de `app/` está coberto por algum alvo de `ALVOS_LIMPOS` (acrescente um teste que compara `git ls-files app/*.py app/**/*.py` com os alvos)
- [ ] Script da seção 6 do protocolo lista `[]`
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(app): docstrings das rotas e modulos raiz sem ids de spec`

---

### T15: Limpar `scripts/` e a saída do script de prontidão

**What**: Mesmo trabalho de T10 em `scripts/`, mais a linha impressa
`"[ ] Paridade 100% em parity_specs.md/parity_tests/ (Tarefa 11)"` de
`scripts/verificar_prontidao_cutover.py`, que passa a ser
`"[ ] Paridade com o Power BI conferida (.specs/features/mvp-2-paridade/relatorio-paridade.md)"`.
Nesta tarefa, e só nesta, uma linha executável muda: essa string impressa.
**Where**: `scripts/`
**Depends on**: T14
**Reuses**: passos 3 a 5 de T10
**Requirement**: REF-05, REF-07

**Passos**:

1. Acrescente `"scripts"` em `ALVOS_LIMPOS` e siga os passos 3 e 4 de T10.
2. Troque a string impressa acima. Procure outras strings impressas com
   "Tarefa": `git grep -n "Tarefa" scripts`.
3. Acrescente em `tests/test_higiene_docstrings.py` um teste que roda a função
   que imprime a seção manual de `scripts/verificar_prontidao_cutover.py`
   (ou o script inteiro com `subprocess` e `sys.executable`, num diretório
   temporário, se ele precisar do banco) e afirma que nenhuma linha contém
   `Tarefa`.
4. O script da seção 6 do protocolo vai listar
   `scripts/verificar_prontidao_cutover.py` por causa da string: confira com
   `git diff` que é a única mudança executável.

**Done when**:

- [ ] Teste de higiene passa com `scripts` na lista
- [ ] Saída do script de prontidão sem "Tarefa" (teste novo)
- [ ] A única mudança executável é a string impressa (conferido no `git diff`)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(scripts): docstrings e saida dos scripts sem ids de spec`

---

### T16: Registrar a feature no `STATE.md`

**What**: Atualizar o bloco "Estado atual" e acrescentar o handoff desta
feature em `.specs/STATE.md`: faixa de commits, contagem de testes, módulos
criados em `app/rotas/`. Tirar dos follow-ups os itens "refatorar `app.py`",
"IDs de spec nas docstrings", "~40 linhas com documentos Reversa" e
"`(Tarefa 10)`". Não marcar como validada: o Verifier ainda roda.
**Where**: `.specs/STATE.md`
**Depends on**: T15
**Reuses**: formato dos handoffs existentes
**Requirement**: REF-04

**Done when**:

- [ ] "Estado atual" diz que `mvp-1-refatoracao` está implementada e aguarda o Verifier
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior, 0 failed

**Tests**: none
**Gate**: build

**Commit**: `docs(state): registrar a refatoracao de app.py`

---

## Verificação (depois de T16)

Verifier independente, em outra sessão, de preferência com modelo mais forte.
Além do fluxo da skill:

- Sensor de discriminação, no mínimo: registrar uma rota movida de volta em `server` direto (o teste de rotas tem de falhar); pôr `Tarefa 09` numa docstring de `app/data/` (higiene falha); apagar o `before_app_request` de instalação (testes de instalação falham); deixar `app/app.py` com 151 linhas.
- Conferir por amostragem (5 funções) que a docstring nova descreve o que a função faz.

---

## Phase Execution Map

```
Phase 1:  T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9
Phase 2:  T10 → T11 → T12 → T13 → T14 → T15 → T16
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | 1 módulo novo + chamadas em `app.py` + 1 teste + 1 linha de README | ⚠️ coeso: o README é exigido pelo teste de higiene no mesmo commit |
| T2–T9 | 1 módulo novo por tarefa (mais os `monkeypatch` que o acompanham) | ✅ |
| T10 | 1 teste novo + 1 diretório | ✅ |
| T11–T15 | 1 diretório | ✅ |
| T16 | 1 arquivo | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | T2 | T2 → T3 | ✅ |
| T4 | T3 | T3 → T4 | ✅ |
| T5 | T4 | T4 → T5 | ✅ |
| T6 | T5 | T5 → T6 | ✅ |
| T7 | T6 | T6 → T7 | ✅ |
| T8 | T7 | T7 → T8 | ✅ |
| T9 | T8 | T8 → T9 | ✅ |
| T10 | None | início da fase 2 | ✅ |
| T11 | T10 | T10 → T11 | ✅ |
| T12 | T11 | T11 → T12 | ✅ |
| T13 | T12 | T12 → T13 | ✅ |
| T14 | T13 | T13 → T14 | ✅ |
| T15 | T14 | T14 → T15 | ✅ |
| T16 | T15 | T15 → T16 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1–T9 | rotas / `app.py` | integration | integration | ✅ |
| T10–T15 | docstrings | unit (higiene) | unit | ✅ |
| T16 | `.specs/STATE.md` | none | none | ✅ |
