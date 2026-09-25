# MVP do CalcSISTEC

Documento de entrada do MVP. Diz o que é o MVP, em que ordem as features rodam e
quando o MVP está pronto. O detalhe de cada parte fica no `spec.md` e no
`tasks.md` de cada feature.

## Objetivo

Substituir o painel Power BI do IFFar pelo CalcSISTEC com segurança. O MVP é o
mínimo para essa troca: números iguais aos do Power BI, páginas públicas com o
mesmo estilo e as mesmas funcionalidades, área administrativa segura na
internet e a Pesquisa Institucional (PI) atualizando os dados todo mês sem
ajuda. Não há data fixa; o objetivo é trocar logo, sem perder qualidade.

## Decisões da responsável (2026-09-24)

| Tema | Decisão |
| --- | --- |
| Entrada de dados | Só o **envio de pastas** é a via oficial. A coleta automática pela extensão continua visível, marcada como **experimental**. Validar a coleta é spec futura. |
| Paridade numérica | Número a número nas 4 páginas públicas. Toda diferença maior que zero em relação ao Power BI precisa de causa registrada: bug corrigido ou diferença de regra aceita por escrito. |
| Paridade visual | As 4 páginas públicas seguem a estrutura, os indicadores, os filtros e as interações do Power BI (prints em `.specs/referencias/`), com as cores e os componentes do gov.br DS. O amarelo do Power BI não volta. A coluna lateral tem, como no Power BI, o logotipo no topo, o menu e os filtros abaixo dele. A Evasão mantém o botão Com FIC / Sem FIC. |
| Hospedagem | Servidor na internet, com `/admin` acessível de fora. CSRF, bloqueio de força bruta e HTTPS entram no MVP. |
| Acesso administrativo | Uma conta, definida no `.env`. Cadastro de pessoas com perfis é spec futura. |
| Validação responsiva | No navegador, com a janela reduzida ou o modo de dispositivo (AD-006). Nunca em celular físico. |
| Código | Separar `app/app.py` em blueprints e limpar as docstrings dentro do MVP. |

## Features, em ordem de execução

| Ordem | Feature | Pasta | O que entrega |
| --- | --- | --- | --- |
| 1 | Refatoração | `.specs/features/mvp-1-refatoracao/` | `app/app.py` dividido em `app/rotas/`; docstrings só com o que o código faz. |
| 2 | Paridade numérica | `.specs/features/mvp-2-paridade/` | `app/paineis/` calcula todos os números do Power BI; `scripts/paridade.py` gera e confere a planilha de comparação; campanha com o export de agosto. |
| 3 | Páginas como o Power BI | `.specs/features/mvp-3-paginas-power-bi/` | Coluna lateral com logotipo, menu e filtros; as 4 páginas com os indicadores, medidores, gráfico e colunas do Power BI. |
| 4 | Segurança para internet | `.specs/features/mvp-4-seguranca/` | CSRF, bloqueio de força bruta, cabeçalhos de segurança, proxy, chave de sessão obrigatória. |
| 5 | Coleta experimental | `.specs/features/mvp-5-coleta-experimental/` | Selo e aviso na coleta automática; documentos e checklist sem a coleta. |
| 6 | Implantação | `.specs/features/mvp-6-implantacao/` | Servidor de produção (waitress), exemplos de systemd e nginx, backup, roteiro no `DEPLOY.md`, primeiro ciclo real. |

Rode as features nessa ordem. A 2 e a 3 dependem da 1. A 3 usa o `app/paineis/`
criado na 2. A 4 e a 5 só dependem da 1, mas rodam depois da 3 para não
disputar os mesmos arquivos. A 6 fecha o MVP.

Cada feature termina com um **Verifier independente** (outra sessão ou outro
modelo, de preferência mais forte que o executor), como manda a skill
`tlc-spec-driven`. Só comece a feature seguinte depois do PASS da anterior.

## Tarefas humanas

Algumas tarefas só uma pessoa pode fazer. Elas aparecem nos `tasks.md` com
**[HUMANO]** no título. O agente executor **para** quando chega nelas e avisa.

| Feature | Tarefa humana |
| --- | --- |
| 2 | A PI preenche a coluna do Power BI na planilha de paridade, com o mesmo export. |
| 2 | Jaline aceita por escrito as diferenças de regra registradas. |
| 3 | Jaline confere as 4 páginas contra os prints no navegador (320–430 px e 1280 px ou mais). |
| 6 | Alguém com acesso ao servidor segue o roteiro do `DEPLOY.md`. |
| 6 | A PI publica sozinha um ciclo real, seguindo só `TESTAR.md` e `DEPLOY.md`. |

## Critério de pronto do MVP

1. As 4 páginas batem com o Power BI no export de agosto, ou cada diferença tem
   causa registrada e aceita por Jaline (`.specs/features/mvp-2-paridade/relatorio-paridade.md`).
2. As 4 páginas têm os filtros, indicadores, gráficos e colunas listados no
   spec da feature 3, conferidos no navegador em 320–430 px e em 1280 px ou mais.
3. `python scripts/verificar_prontidao_cutover.py` sai com GO no servidor, e
   CSRF e bloqueio de força bruta estão cobertos por teste.
4. A PI publicou sozinha um ciclo real, seguindo só `TESTAR.md` e `DEPLOY.md`.

## Fora do MVP (specs futuras)

- Validar e oficializar a coleta automática pelo Sistec.
- Cadastro de pessoas com perfis diferentes na área administrativa.
- Tokens oficiais do gov.br DS e botão dedicado de "voltar à capa".
- Renomear identificadores em inglês (`filter_panel`, `correction.py`…).
- Funções usadas só por testes (`filter_panel`, `agrupar_por_eixo`,
  `paginas_com_falha`, `deduplicar_por_campus`).
- Content-Security-Policy (o Dash precisa de ajuste fino para funcionar com CSP).

## Antes de começar

- A árvore de trabalho precisa estar limpa (`git status --short` vazio). Em
  2026-09-24 havia edições locais em `README.md` e `.env.example`; resolva-as
  antes da feature 1.
- Todo executor lê `.specs/MVP-PROTOCOLO.md` inteiro antes da primeira tarefa.
