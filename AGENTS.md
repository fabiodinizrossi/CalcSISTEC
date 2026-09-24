# Orientações do CalcSISTEC

## Começar

Ordem de leitura antes de mexer no repositório:

1. `README.md` — o que é o projeto, como instalar e onde mexer.
2. `.specs/PROJECT_RULES.md` — princípios e restrições do projeto.
3. `.specs/STATE.md` — decisões e estado atual.

O gate é `python -m pytest -q` (0 falhas). Antes, instale as dependências com
`pip install -r requirements-dev.txt`.

## Subir o ambiente de teste

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testar.ps1 -Destacado -SemNavegador
powershell -ExecutionPolicy Bypass -File scripts/testar.ps1 -Parar
```

`-Destacado` sobe o app em processo separado, espera a porta responder e devolve
o controle, com os logs em `%TEMP%`; `-Parar` derruba quem está na porta.
Acrescente `-Simulado` para usar o Sistec de mentira. Quem sobe em `-Destacado`
**não** monitora o servidor depois: roda, lê a saída e para com `-Parar`.

## Regras

- Para SDD, use `tlc-spec-driven` (instalada em `.claude/skills/tlc-spec-driven/`).
- Antes de planejar ou implementar uma feature, leia `.specs/PROJECT_RULES.md` e
  `.specs/STATE.md`.
- Registre requisitos, decisões, tarefas e validação em `.specs/`, conforme a
  complexidade da feature e o fluxo da skill.
- Após testes internos, remova os diretórios temporários que criou. Use o
  diretório temporário do sistema sempre que possível; nunca deixe `.test-*`,
  `.pytest_cache/` ou `.verifier-scratch-*` no repositório.
- Não faça `git push`, merge, PR nem deploy sem pedido explícito: o trabalho fica
  em commits locais até a usuária pedir.
- A porta 8050 pode estar com um ambiente de teste manual da usuária: nunca rode
  `-Parar` sem `-Porta` nem encerre processo nessa porta por conta própria.
