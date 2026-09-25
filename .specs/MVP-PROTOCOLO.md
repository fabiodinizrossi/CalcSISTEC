# Protocolo de execução do MVP

Leia este arquivo inteiro antes da primeira tarefa. Ele vale para toda tarefa
de toda feature do MVP (`.specs/MVP.md`). Se uma instrução de um `tasks.md`
contradisser este protocolo, **pare e avise**; não escolha sozinho.

## 1. Antes de começar uma feature

1. Leia, até o fim: `AGENTS.md`, `.specs/PROJECT_RULES.md`, `.specs/MVP.md`, o
   `spec.md` e o `tasks.md` da feature.
2. Se o seu ambiente carrega skills, ative a skill `tlc-spec-driven` e siga o
   fluxo Execute dela. Se não carrega, leia
   `.claude/skills/tlc-spec-driven/references/implement.md` e siga-o.
3. Confira a árvore e o gate de partida:

   ```bash
   git status --short
   python -m pytest -q -p no:cacheprovider
   ```

   `git status --short` tem de estar vazio e o pytest tem de terminar com
   `0 failed`. Anote o número de `passed`: é a sua linha de base. Se algo
   falhar **antes** de você mexer, pare e avise.

## 2. Ciclo de cada tarefa (sempre nesta ordem)

1. Leia a tarefa inteira: **What**, **Where**, **Passos**, **Done when**,
   **Tests**, **Gate**, **Commit**.
2. Abra e leia todos os arquivos citados em **Where** e **Reuses** antes de
   editar. Não edite de memória.
3. Se a tarefa pede teste primeiro, escreva o teste, rode só ele e confirme que
   **falha** pelo motivo esperado. Anote a falha para o corpo do commit.
4. Faça a mudança do **What**. Mexa só nos arquivos da tarefa.
5. Rode o gate indicado:
   - `quick`: o comando de teste da própria tarefa.
   - `full`: `python -m pytest -q -p no:cacheprovider` (a suíte inteira).
   - `build`: igual ao `full`.
6. O gate precisa terminar com `0 failed` e com `passed` maior ou igual à linha
   de base mais os testes novos. Menos testes do que antes é erro: algum teste
   sumiu.
7. Marque `[x]` em cada item do **Done when** da tarefa no `tasks.md`.
8. Valide a mensagem de commit:

   ```bash
   python .claude/skills/tlc-spec-driven/scripts/check_commit.py --message "<mensagem>"
   ```

9. Faça `git add` **só** dos arquivos da tarefa, pelo nome (nunca `git add -A`
   nem `git add .`), e faça o commit.
10. Rode `git status --short`. Tem de estar vazio.

Uma tarefa = um commit. Nunca junte duas tarefas no mesmo commit.

## 3. Mensagem de commit

- Formato Conventional Commits: `tipo(escopo): descrição curta em português`,
  sem acento no título, até 72 caracteres. Use a mensagem indicada na tarefa.
- No corpo, diga em uma ou duas linhas o que mudou e, quando houver, qual teste
  falhou antes da mudança.
- Termine com as linhas de coautoria que o orquestrador passar no prompt. Se o
  prompt não passar nenhuma, não invente.

## 4. Regras de teste

- Nunca apague, pule (`skip`) nem enfraqueça um teste para fazer o gate passar.
- Um teste existente só pode mudar quando o **spec desta feature** muda o
  comportamento que ele verifica. Nesse caso, altere só a asserção afetada e cite
  o AC do spec no corpo do commit (ex.: "PBI-03 AC2 muda a ordem dos KPIs").
- Se um teste existente quebrar e o spec não explicar por quê, **pare e avise**.
- Teste novo afirma o resultado que o spec define (o número, o texto, o código
  HTTP), não o que o seu código faz.
- Dados de teste são sintéticos. Nunca use nome, CPF ou e-mail de pessoa real.

## 5. Quando o teste usa `monkeypatch` em `app.app`

Vários testes fazem `monkeypatch.setattr(app_module, "nome", ...)`, com
`import app.app as app_module`. Quando uma rota sai de `app/app.py` para um
módulo de `app/rotas/`, o nome passa a ser procurado no módulo novo. Então:

1. Procure os testes que trocam esse nome: `git grep -n "app_module, \"nome\"" tests`.
2. Troque o alvo para o módulo novo. Exemplo: `monkeypatch.setattr(app_module, "listar_campi", ...)`
   vira `monkeypatch.setattr(rotas_envio, "listar_campi", ...)`, com
   `import app.rotas.envio as rotas_envio` no topo do arquivo de teste.
3. `monkeypatch.setattr(app_module.instalacao, ...)` vira
   `monkeypatch.setattr(instalacao_mod, ...)`, com
   `import app.data.instalacao as instalacao_mod`.
4. Não mude mais nada no teste.

## 6. Quando a tarefa diz "só docstrings e comentários"

Depois da mudança, confira que nenhuma linha executável mudou. Rode, na raiz do
repositório:

```bash
python - <<'EOF'
import ast, subprocess, sys
def norm(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body \
           and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant) \
           and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return ast.dump(t)
arquivos = subprocess.run(["git", "diff", "--name-only", "--", "*.py"], capture_output=True, text=True).stdout.split()
ruins = []
for f in arquivos:
    antes = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, text=True, encoding="utf-8").stdout
    depois = open(f, encoding="utf-8").read()
    if antes and norm(antes) != norm(depois):
        ruins.append(f)
print("mudanca executavel em:", ruins)
sys.exit(1 if ruins else 0)
EOF
```

A saída precisa ser `mudanca executavel em: []`. Se listar um arquivo, desfaça a
mudança executável nele.

## 7. O que nunca fazer

- `git push`, merge, PR, deploy, `git reset --hard`, `git stash`,
  `git checkout -- .`, `git clean`.
- Apagar ou alterar `.env`, `app/data/sistec.db` ou qualquer arquivo fora do
  repositório.
- Derrubar processo na porta **8050** ou **8051**: pode ser o ambiente de teste
  da usuária. Em teste, use porta livre (`socket.bind(("127.0.0.1", 0))`).
- Instalar pacote que a tarefa não mande instalar.
- Criar arquivo temporário dentro do repositório. Use o diretório temporário do
  sistema (`tempfile`, `tmp_path` do pytest) e apague ao terminar. Nunca deixe
  `.pytest_cache/`, `.test-*` ou `.verifier-scratch-*` no repositório.
- Editar artefatos antigos em `.specs/features/*/` (só os da feature atual).
- Começar a tarefa seguinte com o gate vermelho.

## 8. Quando parar e avisar

Pare na hora, sem tentar contornar, e escreva no relatório o que aconteceu, se:

- a tarefa é **[HUMANO]**;
- o código real não bate com o que a tarefa descreve (arquivo, função ou linha
  diferentes do esperado);
- um teste existente quebra e o spec não explica;
- o gate continua vermelho depois de duas tentativas de correção;
- a tarefa pede uma decisão que não está escrita no spec.

## 9. Relatório ao terminar (ou ao parar)

Em português, curto, uma linha por tarefa:

```
T<n> — feita | parada — commit <hash> — testes novos: <n> em <arquivo> — gate: <N> passed, <M> failed — desvios: <nenhum | quais>
```

No fim: `git log --oneline <primeiro-commit>^..HEAD`, `git status --short` e a
contagem final do pytest.
