# Painel SISTEC (Dash) - Projeto completo (todas as páginas)

## Estrutura

```
app/
  data/        # BC-01: ingestão, validação e correção de status (Tarefa 05)
  domain/      # BC-02/BC-03: regras de negócio puras (Tarefas 04, 06, 07)
  pages/       # 1 arquivo por página (Tarefa 09)
  components/  # UI reutilizável (Tarefa 09)
  shell.py     # shell único (cabeçalho, menu, breadcrumb, rodapé): blueprint /ds/ e PainelDash
  admin_campi.py  # gestão de campi em /admin/campi (lista, edição, inclusão)
  templates/   # páginas administrativas (Jinja); shell/ tem os parciais e macros que o Dash também usa
  static/      # gov.br DS, Rawline/Font Awesome e JS compartilhado (tema, menu, confirmação e ordenação), em /ds/
  assets/      # só style.css e logotipos: o Dash carrega tudo desta pasta, por isso o DS fica fora dela
  app.py       # app Dash + callbacks
run.py         # entry point
```

## Painel público

A rota `/` é o dashboard de **Matrículas**. Ela apresenta cinco KPIs, a matriz
por campus/curso/oferta/modalidade/ciclo, filtros de campus, tipo de curso,
programa e FIC, além do botão para limpar os filtros. `/matriculas` é mantida
como redirecionamento para a página inicial.

O shell público é responsivo: abaixo de 992px o menu é sobreposto e aberto pelo
botão do cabeçalho; a partir de 992px ele ocupa a coluna lateral de 240px. Em
telas estreitas, o título do cabeçalho pode ocupar duas linhas, os filtros usam
toda a largura do card, os KPIs reorganizam a grade e a tabela preserva todas as
colunas em uma região com rolagem horizontal.

As tabelas de dados são ordenáveis pelo cabeçalho, com clique ou teclado
(`Enter`/`Espaço`). O script compartilhado
`app/static/js/ordenacao-tabelas.js` reconhece texto, números no formato
brasileiro, percentuais e datas; cabeçalhos agrupadores e os marcados com
`data-no-sort` não recebem ordenação. Valores vazios permanecem no fim.

Ver `_reversa_sdd/migration/` e `_reversa_sdd/reconstruction-plan.md` (no repositório principal) para as specs completas desta migração.

## Rodar local

Para **testar**, use o atalho que já deixa tudo configurado (credenciais de teste,
navegador aberto no login, Sistec real ou simulado) — passo a passo em
[`TESTAR.md`](TESTAR.md):

```powershell
cd projetoFabio\CalcSISTEC
.\scripts\testar.ps1              # Sistec real
.\scripts\testar.ps1 -Simulado    # Sistec de mentira
```

No Claude Code, o mesmo atalho é o comando `/testar`.

Para subir o app à mão (produção escuta em `0.0.0.0:8050`):

```bash
pip install -r requirements.txt
python run.py
```

## Rodar na EC2 (modo teste)
O `app.py` já está configurado para:
- host 0.0.0.0
- port 8050
- debug False

Libere a porta 8050 no Security Group (idealmente restrita ao seu IP).

## Atualização de dados (Sistec)

Sem extensão e sem navegador automatizado: é a mecânica do script R. Quem tem
a sessão é o **seu navegador de sempre**, com o seu login gov.br. O CalcSISTEC
manda abrir as URLs de troca de campus e de exportação, vigia a pasta fixa de
trabalho e a pasta de Downloads, e move, lê e apaga cada CSV assim que ele
chega — sempre avisando na tela (passo a passo e barra de progresso).

> O modo "janela do navegador" (Playwright + CDP) foi **removido**: o gov.br
> identifica o navegador sob controle automático e recusa o login
> ("Captcha inválido", `ERL0000900`). Com ele saiu a dependência `playwright`.

O CalcSISTEC precisa rodar **na máquina de quem faz o login** (é o navegador
dessa máquina que ele manda abrir).

Uma vez só:

```bash
pip install -r requirements.txt
```

A cada atualização:

1. `python run.py` e entre em `http://localhost:8050/admin/login`.
2. Em **Atualizar dados**, escolha a origem. Em **Atualizar do Sistec**, o Sistec
   abre no seu navegador.
3. Faça o login gov.br e clique em **Já entrei no Sistec**.
4. O CalcSISTEC troca de campus e baixa ciclos e matrículas de cada um.
5. Confira a prévia, clique em **Salvar na versão interna** e depois em **Publicar**.

### As duas formas de atualizar

A tela **Atualizar dados** tem duas origens, e as duas terminam na mesma prévia e na
mesma publicação:

- **Atualizar do Sistec** — baixa tudo pelo navegador de quem está logado, como acima.
- **Enviar pastas** — usa planilhas que você já tem em disco. Escolha **uma pasta com
  os arquivos de ciclos e outra com os de matrículas**, pelo campo de seleção de
  diretório. Os dois campos são obrigatórios: faltando um, a tela avisa e nada é
  enviado.

No envio, cada pasta deve conter arquivos `.csv` exportados do Sistec (mesmo separador
`;` e mesma codificação `cp1252` das planilhas da baixa). O nome do arquivo é livre, e
**arquivo que não seja `.csv` é ignorado** e listado no resultado. A tela mostra o que
foi lido de cada arquivo, linha por linha, e nada é gravado antes de você clicar em
**Salvar na versão interna**. Um envio que passa de 500 MB é recusado: envie em partes.

**Campus que não veio no envio tem os dados atuais preservados** — o envio não apaga
unidade ausente. Antes de salvar, a tela lista essas unidades e pede uma confirmação
explícita; sem ela, o servidor recusa a gravação. Unidade que não está no cadastro de
campi é apenas avisada (não é atualizada nem preservada por essa regra), e matrículas
apontando para ciclos que não vieram aparecem contadas como órfãs. A tela **Histórico**
registra a atualização por envio com o tipo `envio`.

Antes da primeira atualização é preciso **cadastrar os campi** (`/admin/campi`, com
vínculo em Configurações → Gerenciar campi, ou o assistente de instalação). O campo decisivo é o
**identificador de perfil**: o `tipo` do Sistec, um número de 7 dígitos como
`8278860`. Para descobri-lo, na tela "Selecione o Perfil para efetuar login"
abra `F12` → *Elements*, procure `name="tipo"` e selecione cada campus — o valor
muda a cada escolha. Anote junto o `qtdPerfis` da mesma tela.

Com identificador faltando ou inválido a atualização **não começa**: ela avisa
quais campi corrigir. Isso é proposital — sem o `tipo` certo o Sistec ignora a
troca de campus e as planilhas viriam vazias, com o progresso parado em 0%.

A lista de campi fica em **`/admin/campi`** (Configurações → Gerenciar campi): buscar,
mudar de página, ver em lista ou em cards, editar o identificador do perfil, o código,
a cidade e o nome da unidade, desativar (deixa de ser baixado), excluir (com confirmação)
ou incluir um perfil à mão. Colar a lista inteira de uma vez e ajustar o `qtdPerfis`
continuam em Configurações. Código da unidade vazio é preenchido com o código que vem na
planilha de ciclos; se a planilha de um campus vier com o código de outro, a
tela avisa (sinal de que a troca de perfil não funcionou).

Teste sem o Sistec real: rode `python scripts/sistec_simulado.py` num terminal
e o CalcSISTEC com `CALCSISTEC_SISTEC_BASE_URL=http://127.0.0.1:8051`
(`SISTEC_SIM_LOGIN_AUTOMATICO=1` pula o login fake).

Variáveis de ambiente relevantes:
- `ADMIN_EMAIL` / `ADMIN_PASSWORD_HASH`: credenciais da área administrativa.
- `CALCSISTEC_SISTEC_BASE_URL`: só para desenvolvimento — aponta para o
  Sistec simulado em vez do Sistec real.
- `CALCSISTEC_PASTA_COLETA`: pasta fixa de trabalho da coleta (padrão
  `%LOCALAPPDATA%\CalcSISTEC\coleta`, criada sozinha). Os CSVs são lidos e
  apagados ali; configurar o navegador para baixar nessa pasta evita o
  arquivo passar pela pasta de Downloads.
- `CALCSISTEC_PASTA_DOWNLOADS`: a outra pasta vigiada (padrão: a pasta de
  Downloads do usuário, lida do registro do Windows).
- `CALCSISTEC_HTTPS=1`: liga `SESSION_COOKIE_SECURE` e faz `/api/sistec/*`
  recusar HTTP simples fora de `localhost` (D-19).

A extensão `extensao-sistec/` e as rotas `/api/sistec/*` continuam no
repositório, mas as telas não as usam mais.

## Instalar em outra instituição

Nada de identidade fica fixo no código: nome, sigla, site, e-mail de contato,
logotipo e lista de campi são configuração. Na primeira execução, qualquer
tela administrativa leva ao assistente em `/admin/instalacao`, que pede:

1. **Dados da instituição** — nome, sigla, site e e-mail de contato do rodapé.
   O logotipo é enviado em Configurações; enquanto não houver um, entra um
   genérico (`app/assets/branding/padrao-generico.svg`).
2. **Campi e identificadores do Sistec** — o identificador de perfil de cada
   campus pertence à conta de quem acessa o Sistec. O jeito recomendado é
   clicar em **Atualizar do Sistec**, que lê a lista junto com o login. Quem
   já tiver os identificadores pode colar uma lista, uma linha por campus no
   formato `identificador ; nome do perfil`.
3. **Concluir** — libera as telas administrativas.

**Resetar instalação** (Configurações → Recomeçar do zero) apaga identidade,
campi e dados baixados e volta ao assistente. Serve para a troca da pessoa
responsável pelo setor ou para levar o programa a outra instituição. O
ano-base e a tabela de fatores (FEC/FECH), que são regra nacional da PNP,
são preservados.

## Observação sobre métricas
Algumas métricas (ex.: Matrículas equivalentes) estão implementadas como *proxy*:
- `EQ_MATRICULA = NU_CARGA_HORARIA / CARGA_TOTAL` (quando disponível; senão 1.0)
- `MatEq = soma(EQ_MATRICULA)`

Isso pode ser ajustado depois conforme a regra oficial do seu Power BI.
