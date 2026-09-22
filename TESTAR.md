# Como testar o CalcSISTEC

> Um comando sobe tudo configurado: `.\scripts\testar.ps1`
> No Claude Code, basta escrever **`/testar`** (ou `/testar simulado`).

## O comando

```powershell
cd projetoFabio\CalcSISTEC
.\scripts\testar.ps1              # Sistec REAL (login gov.br seu)
.\scripts\testar.ps1 -Simulado    # Sistec de mentira, sem gov.br
```

Ele confere as dependências, prepara o login administrativo, sobe o app em
`http://localhost:8050` e abre o navegador na tela de login. Para parar: `Ctrl+C`.

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
8. Se estiver tudo certo, **Publicar**.

Se algum campus estiver com identificador inválido, a atualização **para antes de
começar** e diz quais corrigir — em vez de baixar 22 planilhas vazias.

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
python -m pytest -q
```

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
- `_reversa_forward/002-baixador-planilhas-sistec/onboarding.md` — roteiro de teste
  detalhado por cenário (Partes A, B e C).
- `_reversa_forward/002-baixador-planilhas-sistec/interfaces/navegador-local.md` —
  como a coleta funciona por dentro.

## Conferir o design (gov.br DS)

### Abrir no celular pela rede local

O endereço `localhost` funciona somente no computador que executa o app. Para fazer o
teste físico, conecte o celular e o computador à **mesma rede Wi-Fi privada** e siga:

1. No computador, execute `ipconfig` e anote o endereço **IPv4** do adaptador Wi-Fi,
   por exemplo `192.168.1.25`.
2. Na raiz do projeto, execute `python run.py`. Esse comando escuta na rede local;
   use-o só durante o teste e pare com `Ctrl+C` ao terminar.
3. No celular, abra `http://<IPv4>:8050`, substituindo `<IPv4>` pelo endereço anotado.
   Exemplo: `http://192.168.1.25:8050`.
4. Se o Windows pedir autorização de firewall, permita o Python **somente em redes
   privadas**. Não crie regra para rede pública, não redirecione a porta no roteador e
   não exponha o endereço à internet.

O modo de dispositivo do Chrome ajuda a antecipar problemas de largura, mas não
substitui este teste: registre em `CUTOVER.md` o modelo do celular, a largura e a data.

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
- Antes do cutover, repita esse roteiro em celular real entre 320px e 430px e em uma tela
  de 1280px ou mais. Registre dispositivo, largura e data em `CUTOVER.md`; o item de
  validação em celular só pode ser marcado depois dessa evidência.
- Os testes automáticos: `python -m pytest -q`. Os de JavaScript (`tests/test_js_*.py`) precisam do `node` no PATH
  e são pulados sem ele.
