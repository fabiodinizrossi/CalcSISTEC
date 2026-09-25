# Painel de Acompanhamento do SISTEC

Painel de acompanhamento dos dados de matrícula do Sistec: lê os CSVs exportados
do Sistec, calcula os indicadores baseados no Guia da PNP e publica as páginas de consulta: 
Matrículas, Eficiência Acadêmica, Taxa de Evasão Anual e Percentuais Legais.

## Começar

Precisa de Python 3.12 e de um terminal na raiz do clone.

1. Clone o repositório e entre na pasta:

   ```bash
   git clone <url-do-repositorio> CalcSISTEC
   cd CalcSISTEC
   ```

2. Crie o ambiente virtual e ative:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # Linux/macOS
   ```

3. Instale as dependências nas versões fixas testadas:

   ```bash
   pip install -r requirements-dev.txt
   ```

4. Crie o `.env` a partir do exemplo e preencha `ADMIN_EMAIL`,
   `ADMIN_PASSWORD_HASH` e `FLASK_SECRET_KEY`. As oito chaves estão explicadas
   no próprio `.env.example`:

   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # Linux/macOS
   ```

5. Rode a suíte de testes:

   ```bash
   python -m pytest -q
   ```

6. Suba o painel — para testar, com credenciais de teste já configuradas:

   ```powershell
   .\scripts\testar.ps1 -Simulado
   ```

   Para valer (escuta em `0.0.0.0:8050`):

   ```bash
   python run.py
   ```

Passo a passo do ambiente de teste em `TESTAR.md`; publicação em `DEPLOY.md`.

## Estrutura

| Caminho | Para que serve |
| --- | --- |
| `app/app.py` | App Dash e os callbacks das telas. |
| `app/shell.py` | Shell único (cabeçalho, menu, breadcrumb, rodapé) e a rota `/ds/`. |
| `app/auth.py` | Login e controle de acesso das rotas administrativas. |
| `app/config.py` | Configuração de sessão (HTTPS, cookie `SameSite`) e do ano-base. |
| `app/admin_campi.py` | Gestão de campi em `/admin/campi`. |
| `app/domain/` | Regras de cálculo puras (matrículas, eficiência, evasão, percentuais legais). |
| `app/data/` | Ingestão, correção, transformação e leitura dos dados (SQLite). |
| `app/sistec/` | Coleta no Sistec, colunas aceitas, execuções e captura de perfis. |
| `app/pages/` | Uma página pública por arquivo. |
| `app/components/` | Componentes de UI reutilizados pelas páginas (filtros, cartões, tabelas). |
| `app/templates/` | Páginas administrativas em Jinja e os parciais do shell. |
| `app/static/` | gov.br DS, Rawline/Font Awesome e o JS compartilhado, servidos em `/ds/`. |
| `app/assets/` | Só `style.css` e logotipos: o Dash carrega tudo desta pasta, por isso o DS fica fora dela. |
| `scripts/` | `testar.ps1` (ambiente de teste), `sistec_simulado.py` e `verificar_prontidao_cutover.py`. |
| `tests/` | Suíte `pytest` — paridade de domínio, telas, higiene do repositório. |
| `.specs/` | Regras do projeto, estado atual e o histórico de cada feature. |
| `extensao-sistec/` | Extensão de navegador legada; as telas atuais não a usam. |

## Onde mexer

| Quero… | Vá para |
| --- | --- |
| Mudar uma regra de cálculo | `app/domain/` — cada indicador tem seu módulo, com teste de paridade em `tests/test_parity_dominio.py`. Regra de negócio e explicação em `.specs/PROJECT_RULES.md`. |
| Adicionar uma página pública | Crie um arquivo em `app/pages/` (uma página por arquivo), registre no menu em `app/shell.py` e use os componentes de `app/components/`. |
| Mudar a coleta do Sistec | `app/sistec/` — URLs e tempos em `app/sistec/urls.py`, pastas vigiadas em `app/sistec/downloads.py`, execuções em `app/sistec/execucoes.py`. |
| Mudar o visual (DS/tema) | `app/static/` (arquivos do gov.br DS servidos em `/ds/`), `app/assets/style.css` e os tokens em `app/static/govbr-ds/dist/core-tokens.css`. |
| Mudar uma rota administrativa | `app/app.py` para a rota e o callback, `app/templates/` para a tela, `app/auth.py` se mexer no acesso. |
| Mudar o schema ou uma migração | `app/data/schema.py`, com teste em `tests/test_schema_v2.py`. |
| Instalar em outra instituição | Assistente em `/admin/instalacao`; a seção "Instalar em outra instituição" abaixo. |

## Painel público

A rota `/` é o dashboard de **Matrículas**. Ele apresenta cinco KPIs, a matriz
por campus/curso/oferta/modalidade/ciclo, filtros de campus, tipo de curso,
programa e FIC, além do botão para limpar os filtros. `/matriculas` é mantida
como redirecionamento para a página inicial.

O shell público é responsivo: abaixo de 992px o menu é sobreposto e aberto pelo
botão do cabeçalho; a partir de 992px ele ocupa a coluna lateral de 240px. Em
telas estreitas, o título do cabeçalho pode ocupar duas linhas, os filtros usam
toda a largura do card, os KPIs reorganizam a grade e a tabela preserva todas as
colunas em uma região com rolagem horizontal.

As tabelas de dados são ordenáveis pelo cabeçalho, com clique ou teclado
(`Enter`/`Espaço`). O script `app/static/js/ordenacao-tabelas.js` reconhece
texto, números no formato brasileiro, percentuais e datas; cabeçalhos
agrupadores e os marcados com `data-no-sort` não recebem ordenação. Valores
vazios permanecem no fim.

## Atualização de dados (Sistec)

Sem extensão e sem navegador automatizado: quem tem a sessão é o **seu navegador
de sempre**, com o seu login gov.br. O CalcSISTEC manda abrir as URLs de troca de
campus e de exportação, vigia a pasta fixa de trabalho e a pasta de Downloads, e
move, lê e apaga cada CSV assim que ele chega — sempre avisando na tela (passo a
passo e barra de progresso).

> O modo "janela do navegador" (Playwright + CDP) foi **removido**: o gov.br
> identifica o navegador sob controle automático e recusa o login
> ("Captcha inválido", `ERL0000900`). Com ele saiu a dependência `playwright`.

O CalcSISTEC precisa rodar **na máquina de quem faz o login** (é o navegador
dessa máquina que ele manda abrir).

A cada atualização:

1. `python run.py` e entre em `http://localhost:8050/admin/login`.
2. Em **Atualizar dados**, escolha a origem. Em **Atualizar do Sistec**, o Sistec
   abre no seu navegador.
3. Faça o login gov.br e clique em **Já entrei no Sistec**.
4. O CalcSISTEC troca de campus e baixa ciclos e matrículas de cada um.
5. Confira a prévia, clique em **Salvar na versão interna** e depois em **Publicar**.

**Publicar** leva a versão interna inteira ao painel público: os dados de ciclos e
matrículas e também a lista de campi (`interna_campus`, a projeção do cadastro de
`/admin/campi`). A publicação anterior fica guardada, e **Desfazer** devolve a versão
anterior por inteiro, campi incluídos. **Aplicar ao público**, em Configurações,
continua existindo para levar só as edições de campi e de fatores, fora do ciclo de
baixa.

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

### Conferir antes de salvar (envio de pastas)

Depois de enviar as pastas, a tela mostra a faixa **Prévia não publicada** e quatro
links para conferir as páginas públicas com os dados que o **Salvar na versão
interna** gravaria: **Matrículas**, **Eficiência Acadêmica**, **Taxa de Evasão
Anual** e **Percentuais Legais**. Os filtros, os indicadores e as tabelas são os
mesmos do painel público, aplicados ao conjunto do envio (inclusive os campi
preservados).

Conferir **não grava nada**: nem a versão interna nem a publicada são alteradas
enquanto você navega. A prévia é **privada** — só a sessão que fez o envio a
abre — e dura enquanto o envio estiver pendente. **Salvar na versão interna** ou
**Descartar** encerram a prévia; uma URL antiga de prévia passa a mostrar
**Prévia indisponível**. Se a configuração (fatores, campi, ano-base) mudar entre
a conferência e o Salvar, o sistema recusa com um aviso para descartar e reenviar
as pastas — nada é gravado diferente do que você conferiu.

A **baixa direta do Sistec** não tem essa prévia das quatro páginas: ela mostra a
prévia resumida (contagens e amostra) e salva como antes.

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

As variáveis de ambiente que o app lê estão descritas em `.env.example`, uma a
uma.

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

Isso pode ser ajustado depois conforme a regra oficial do seu Power BI. As
divergências conhecidas que aguardam decisão humana estão listadas em `DEPLOY.md`.

## Onde ler mais

- `TESTAR.md` — ambiente de teste local, com Sistec real ou simulado.
- `DEPLOY.md` — instalação, subida, checklist de publicação e pendências.
- `AGENTS.md` — como agentes de IA trabalham neste repositório.
- `.specs/README.md` — como ler as specs; `.specs/PROJECT_RULES.md` tem os
  princípios do projeto e `.specs/STATE.md`, o estado atual.
