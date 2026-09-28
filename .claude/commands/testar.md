---
description: Sobe o ambiente de teste do CalcSISTEC destacado e devolve o controle
argument-hint: [simulado]
---

Rode o ambiente de teste sem prender esta sessão:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testar.ps1 -Destacado -SemNavegador
```

Com o argumento `simulado`, use o Sistec de mentira (sem login gov.br):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/testar.ps1 -Destacado -SemNavegador -Simulado
```

Depois de rodar:

- Repasse a saída à usuária: URL de login, e-mail, senha, PID e caminhos dos logs.
- **Não** acompanhe o servidor: não consulte, não espere, não fique lendo o log.
  O comando já esperou a porta responder e devolveu o controle.
- Para derrubar, rode `powershell -ExecutionPolicy Bypass -File scripts/testar.ps1 -Parar`
  (com `-Simulado` para encerrar também o simulado da porta 8051).
- Porta 8050 pode estar em uso por um ambiente manual da usuária: não rode `-Parar`
  sem `-Porta` e não encerre processo nenhum nessa porta por conta própria.
