# Como testar o CalcSISTEC

> Um comando sobe tudo configurado: `.\scripts\testar.ps1`, da raiz do clone.
> No Claude Code, basta escrever **`/testar`** (ou `/testar simulado`): o atalho
> roda `scripts/testar.ps1 -Destacado -SemNavegador` e devolve o controle.

## O comando

```powershell
.\scripts\testar.ps1              # Sistec REAL (login gov.br seu)
.\scripts\testar.ps1 -Simulado    # Sistec de mentira, sem gov.br
```

Ele confere as dependências, prepara o login administrativo, sobe o app em
`http://localhost:8050` e abre o navegador na tela de login. Para parar: `Ctrl+C`.

### Subir sem prender o terminal (`-Destacado`) e derrubar (`-Parar`)

```powershell
.\scripts\testar.ps1 -Destacado -SemNavegador   # sobe e devolve o controle
.\scripts\testar.ps1 -Parar                     # encerra quem está na porta
```

`-Destacado` inicia o app em um processo separado, grava a saída em um arquivo de
log no diretório temporário do sistema (`%TEMP%`, nunca no repositório) e espera
a porta aceitar conexão por até 60 s. Em seguida imprime URL de login, e-mail,
senha, PID e o caminho do log, e sai com código 0. Se a porta não abrir em 60 s,
ele encerra o processo, imprime o caminho do log e sai com 1. Com `-Simulado`,
sobe também o Sistec simulado na porta 8051.

`-Parar` encerra o processo que escuta na porta (8050 por padrão) e sai com 0;
sem nada no ar, avisa e também sai com 0. Junto com `-Simulado`, encerra os dois.

Quem sobe em `-Destacado` **não** acompanha o servidor depois: rode o comando,
leia a saída e use `-Parar` quando terminar.

### Login de teste

Fica em `.env`, na raiz do CalcSISTEC, criado na primeira execução com uma senha
aleatória. **Esse arquivo não é versionado** (o `.gitignore` já cobre `.env`), e o
script mostra e-mail e senha no terminal toda vez. Para trocar a senha, apague o
`.env` e rode de novo.

O app de teste escuta só em `127.0.0.1`, e não em `0.0.0.0` como o `run.py` de
produção: com senha fixa, ninguém na rede deve alcançar a área administrativa.

## Uma vez só, antes do primeiro teste

```powershell
pip install -r requirements.txt
```

O CalcSISTEC **não controla navegador nenhum**: quem abre o Sistec é o seu navegador
de sempre, com o seu login. (O modo de janela automatizada foi removido — o gov.br
recusa o login quando identifica controle automático.)

## Antes da primeira atualização: cadastrar os campi

A lista de campi é **cadastrada à mão**, em `/admin/campi` (Configurações → Gerenciar
campi) ou no assistente de instalação. O campo que decide tudo é o **identificador de perfil**:
o `tipo` do Sistec, um número de 7 dígitos como `8278860`.

Como descobrir:

1. Entre no Sistec e fique na tela "Selecione o Perfil para efetuar login".
2. `F12` → aba *Elements* → procure `name="tipo"`.
3. Selecione um campus na lista: o valor de `tipo` muda para o identificador dele.
   Anote e repita para cada campus.
4. Na mesma tela, anote o `qtdPerfis` (total de perfis da sua conta — os dois papéis
   de cada campus somados) e salve-o em Configurações.

Para cadastrar tudo de uma vez, use **Importar lista de perfis**, uma linha por
campus:

```
8278860 ; ASSESSOR DA UNIDADE DE ENSINO - 13478 - INSTITUTO FEDERAL FARROUPILHA - CAMPUS SANTA ROSA
8278864 ; ASSESSOR DA UNIDADE DE ENSINO - 13479 - INSTITUTO FEDERAL FARROUPILHA - CAMPUS SÃO BORJA
```

A importação preserva código da unidade, cidade e nome já preenchidos, e troca só os
identificadores.

## Passo a passo com o Sistec real

1. `.\scripts\testar.ps1`
2. Entre com o e-mail e a senha que o terminal mostrou.
3. **Primeira vez**: cai no assistente de instalação. Preencha o nome da
   instituição, cadastre os campi e clique em **Concluir instalação**. Um banco que
   já tinha campi e dados não perde nada.
4. **Atualizar dados › Atualizar do Sistec**. O Sistec abre numa aba do seu
   navegador.
5. Faça o login gov.br nessa aba e volte ao CalcSISTEC: clique em
   **Já entrei no Sistec**.
6. Acompanhe a barra de progresso e o passo a passo. Deve baixar 2 planilhas por
   campus (ciclos e matrículas).
7. Confira a prévia e clique em **Salvar na versão interna**.
8. Se estiver tudo certo, **Publicar**. A publicação leva os dados de ciclos e
   matrículas **e a lista de campi** (a mesma de `/admin/campi`); **Desfazer** devolve
   a versão anterior inteira, campi incluídos.

Se algum campus estiver com identificador inválido, a atualização **para antes de
começar** e diz quais corrigir — em vez de baixar 22 planilhas vazias.

## Testar o envio de pastas sem o Sistec real

O envio não precisa de login nem de navegador: ele lê arquivos que já estão no disco.
Para montar as pastas, use as planilhas de uma baixa anterior (a pasta onde o navegador
salvou os `.csv`) ou rode `python scripts/sistec_simulado.py` e faça uma baixa contra ele
— as planilhas caem na pasta de downloads configurada.

1. Separe dois diretórios, por exemplo `ciclos/` e `matriculas/`, e ponha em cada um os
   `.csv` correspondentes. O nome do arquivo é livre; só a extensão `.csv` importa.
2. Em **Atualizar dados**, marque **Enviar pastas**.
3. Selecione a pasta de ciclos em um campo e a de matrículas no outro. Deixe um deles
   vazio e clique em **Enviar pastas**: a tela avisa que as duas são obrigatórias e não
   chama o servidor.
4. Com as duas preenchidas, o resultado aparece linha por linha (arquivo, tipo, situação,
   linhas). Ponha um `.txt` numa das pastas para ver o arquivo ser ignorado e listado.
5. Confira a prévia e clique em **Salvar na versão interna**.
6. **Publicar** leva ao painel público os dados de ciclos e matrículas **e a lista de
   campi**; **Desfazer** devolve a versão anterior inteira, campi incluídos.

Ciclos **sem `MODALIDADE ENSINO`** (planilhas antigas, de programas já encerrados) são
descartados automaticamente, com as matrículas deles. A contagem não aparece na tela: ela
vem na resposta do envio e no acompanhamento, nos campos
`ciclos_sem_modalidade_descartados` e `matriculas_sem_modalidade_descartadas`.

Casos que valem conferir:

- **Arquivo quebrado**: um `.csv` sem as colunas do Sistec faz o envio inteiro parar, e a
  mensagem nomeia o arquivo e o motivo. Nada é gravado. Se a mensagem falar de colunas
  ausentes em todos os arquivos, provavelmente as pastas estão invertidas.
- **Campus ausente**: tire os arquivos de um campus da pasta e envie de novo. A tela lista
  essa unidade como preservada e **Salvar fica bloqueado até você marcar a confirmação**;
  os dados anteriores daquele campus continuam na versão interna.
- **Unidade fora do cadastro**: um `.csv` de unidade que não está em `/admin/campi` gera
  aviso e não é aplicada.
- **Prévia pendente**: com uma prévia aberta, um segundo envio é recusado com a mensagem
  de prévia pendente — salve ou descarte antes.
- **Histórico**: a atualização aparece na tela **Histórico** com o tipo `envio`, e o
  desfecho de cada envio fica registrado.

### Conferir a prévia das quatro páginas

Depois de enviar as pastas, a área **Prévia** mostra a faixa **Prévia não publicada**
e quatro links: **Matrículas**, **Eficiência Acadêmica**, **Taxa de Evasão Anual** e
**Percentuais Legais**. Abra cada um e confira filtros, indicadores e tabelas — são os
mesmos do painel público, com os dados do envio. **Voltar para Atualizar dados** fecha a
conferência sem salvar nada.

O que conferir no Salvar:

- **Conferência desatualizada**: se fatores, campi ou ano-base mudarem entre a prévia e
  o **Salvar na versão interna**, o servidor recusa com aviso para **Descartar** e
  reenviar as pastas — nada é gravado diferente do que foi conferido.
- **Página com falha**: se uma página da prévia não renderizar, o **Salvar** recusa com
  o nome da página. Recarregue a página ou **Descartar** para liberar.

Uma URL antiga de prévia (`/admin/previa/<execucao_id>/<pagina>`) deixa de funcionar
depois de **Salvar** ou **Descartar**: passa a mostrar **Prévia indisponível**. A prévia
é privada da sessão que fez o envio — outra sessão, mesmo com o mesmo e-mail, vê
**Prévia indisponível**.

### O que olhar enquanto roda

- Os **identificadores** em `/admin/campi`: números de 7 dígitos.
  `0`, `1`, `2`… são lista velha da extensão, e a tela marca em vermelho.
- Os **avisos**: se a planilha de um campus vier com o código de outra unidade, ou
  se dois campi trouxerem a mesma unidade, a troca de perfil não funcionou.
- O número de **linhas por planilha** — zero em todas é sinal de problema.

### Conferir uma URL à mão

Logada no Sistec, no seu navegador, com `<id>` de um campus:

```
http://sistec.mec.gov.br/index/index?tipo=<id>&acao=&qtdPerfis=22
http://sistec.mec.gov.br/gridciclo/exportar-ciclo-turmas/?coCiclo=&noInstituicao=&tipoCurso=&Ano=&stCicloName=&acoes=
http://sistec.mec.gov.br/aluno/gerar-csv/?tipoAluno=comCpf&cpfAluno=&codigoAluno=&filtro_nome=1&no_aluno=%20&no_social=&tipoPesquisa=parteNome&vizualizarGrid=0,1,2,3,4,5,6
```

A primeira troca o campus ativo (confira no cabeçalho do Sistec); as outras duas
baixam `ciclo-matricula.csv` e `sistec.csv` desse campus. São as mesmas do script R —
é assim que se confirma se um identificador está certo antes de cadastrá-lo.

## Passo a passo com o Sistec simulado

```powershell
.\scripts\testar.ps1 -Simulado
```

Sobe junto um Sistec de mentira (2 campi, dados sintéticos, login automático) e
aponta o CalcSISTEC para ele. Serve para exercitar a tela inteira sem tocar no
Sistec real nem em dado de aluno. Cadastre os campi `8278857` e `8278858` (os do
simulado) para a coleta rodar. O simulado é encerrado junto com o `Ctrl+C`.

Ao final, confira que a pasta de coleta (`%LOCALAPPDATA%\CalcSISTEC\coleta`) e a de
Downloads ficaram **vazias** — nenhum CSV com CPF pode sobrar.

## Testes automatizados

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

`requirements-dev.txt` traz o `requirements.txt` inteiro mais o `pytest`.

Cobrem a coleta contra o Sistec simulado, a recusa de rodar com identificador
inválido, o CRUD de campi (inclusive a troca do identificador preservando o resto),
o assistente de instalação e o reset. Também cobrem o shell responsivo, a página
inicial de Matrículas e a ordenação compartilhada das tabelas (texto, números,
percentuais, datas, células vazias, cabeçalhos com `rowspan`/`colspan` e teclado).

## Quando algo dá errado

| Sintoma | O que fazer |
|---|---|
| "A porta 8050 já está em uso" | Um CalcSISTEC antigo ficou aberto. Feche aquele terminal ou use o `Stop-Process -Id <PID>` que o script sugere |
| "Falta a dependência ..." | Rode `pip install -r requirements.txt` |
| "Servidor sem credenciais administrativas" | O app foi aberto fora do script (sem as variáveis). Use `.\scripts\testar.ps1` |
| "N campus(i) estão sem um identificador de perfil válido" | Cadastre o `tipo` de cada um em `/admin/campi` (veja a seção acima) |
| Progresso parado em 0%, planilha nenhuma chega | Identificador errado (aceito no formato, mas não é o do campus). Confira pela URL de troca de campus, à mão |
| Planilhas de campi diferentes com a mesma unidade | Dois campi com o mesmo `tipo`, ou o Sistec deixou de aceitar a troca por URL. A tela avisa |
| O arquivo não chega na pasta | A tela avisa em 1 minuto: o Chrome está com "perguntar onde salvar cada arquivo". Desligue em `chrome://settings/downloads`, ou escolha a pasta de coleta na janela que abriu |
| Quer recomeçar do zero | Configurações → **Recomeçar do zero** (preserva ano-base e fatores). Para zerar de verdade, apague `app/data/sistec.db` |

## Notas de manutenção do script

- **Política de execução**: se o Windows recusar o `.ps1` ("execução de scripts foi
  desabilitada"), rode com
  `powershell -ExecutionPolicy Bypass -File scripts\testar.ps1` (ou `pwsh` no lugar
  de `powershell`). É o que o comando `/testar` já faz.
- **O arquivo precisa continuar em UTF-8 com BOM**. Sem BOM, o Windows PowerShell 5.1
  lê o script como CP1252: os travessões viram `â€"`, e essa aspa tipográfica abre uma
  string que engole o resto do arquivo — o erro aparece como "'}' de fechamento
  ausente" numa linha inocente. Se editar o script com uma ferramenta que salva sem
  BOM, regrave com
  `[System.IO.File]::WriteAllText($caminho, $texto, [System.Text.UTF8Encoding]::new($true))`.
- **Duas armadilhas do 5.1 já contornadas no script**, para não voltarem numa edição
  futura: *here-string* não pode ser passado direto como argumento de comando nativo
  (vai antes para uma variável), e aspas dentro do trecho são colapsadas a caminho do
  `python` (por isso o teste de dependências não usa aspas nenhuma).

## Onde ler mais

- `README.md` — visão geral, variáveis de ambiente e instalação em outra instituição.
- `DEPLOY.md` — instalação, subida, checklist antes de publicar e as pendências
  abertas (validação responsiva, CSRF, divergências conhecidas).

## Conferir o design (gov.br DS)

### Conferir larguras no navegador

A validação responsiva é feita no navegador do computador, sem celular físico:
reduza a janela ou abra o modo de dispositivo do DevTools (`Ctrl+Shift+M` no Chrome
e no Edge) e confira as telas entre 320 px e 430 px e depois com 1280 px ou mais.
Registre em `DEPLOY.md` o navegador, as larguras e a data.

- O botão **Usar tema escuro** fica no cabeçalho de todas as telas. A escolha fica salva no navegador
  (`localStorage`, chave `calcsistec-tema`) e a página não recarrega ao trocar.
- Teste o menu com o teclado: **Enter** e **Espaço** abrem, **Esc** fecha; em telas de 992px ou mais ele fica
  sempre à vista.
- Em **Excluir** (na lista de campi) abre um modal: **Esc** ou **Cancelar** não excluem nada.
- Nas tabelas, clique em um cabeçalho ou use **Enter/Espaço** para alternar entre ordem
  decrescente e crescente. Cabeçalhos de agrupamento e a coluna **Ações** não ordenam.
- Em 390px, confira que o título público fica em no máximo duas linhas, os filtros ocupam
  a largura do card e somente a região da tabela rola horizontalmente.
- Nas páginas públicas, confira nesta ordem: **Eficiência Acadêmica** (`/eficiencia`),
  **Taxa de Evasão Anual** (`/evasao`) e **Percentuais Legais** (`/percentuais-legais`).
  Em cada uma, leia o contexto e o indicador principal antes do seletor de eixo, da tabela
  e dos filtros; altere os filtros FIC disponíveis e use **Limpar Filtros** para confirmar
  o retorno aos valores iniciais.
- Em **Percentuais Legais**, alterne o eixo da tabela entre Campus, Unidade, Modalidade
  e Tipo de curso. A tabela é um **recorte exploratório**: as metas legais são avaliadas
  no conjunto filtrado, não em cada linha ou grupo. Ao filtrar Programa Associado, confira
  que o aviso sobre a possível distorção do percentual PROEJA continua junto do resumo.
- Nas três rotas, repita a conferência nos temas claro e escuro. Use teclado para alcançar
  o seletor de eixo, os filtros, **Limpar Filtros** e os cabeçalhos ordenáveis das tabelas;
  o foco deve permanecer visível.
- Antes de publicar, repita esse roteiro no navegador com a largura entre 320px e 430px e
  com 1280px ou mais. Registre navegador, larguras e data em `DEPLOY.md`; o item de
  validação responsiva só pode ser marcado depois dessa evidência.
- Os testes automáticos: `python -m pytest -q`. Os de JavaScript (`tests/test_js_*.py`) precisam do `node` no PATH
  e são pulados sem ele.
