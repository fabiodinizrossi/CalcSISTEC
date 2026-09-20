# Design responsivo com o gov.br Design System Specification

## Problem Statement

O painel precisa funcionar bem em celulares (a partir de 320px) e em telas grandes (até 1920px), usando o
Padrão Digital de Governo (gov.br DS) de fato, e não só as suas cores, em tema claro e em tema escuro. O código atual usa o DS pela metade e não tem tema escuro:

- As 5 páginas públicas (Dash) têm cabeçalho, menu, rodapé e cartões próprios (`app-header`, `nav-menu`,
  `nav-card`, `kpi-card`) e usam `dbc.Card`, `dbc.Table`, `dbc.Nav` e `dbc.Button` sobre `dbc.themes.BOOTSTRAP`
  (`app/app.py:41`, `app/components/*.py`, `app/pages/*.py`). O gov.br DS aparece só como cores em `style.css`.
- As páginas administrativas (Flask, `app/templates/`) usam `br-button`, `br-input` e `br-table`, mas carregam só
  `core.min.css` (sem `core.min.js`) e têm cabeçalho e rodapé próprios.
- O Dash carrega recursivamente todo `.css` e `.js` de `app/assets/` (leitura estática de `Dash._walk_assets_directory`,
  Dash 4.4.1; app não executado), o que inclui os 162 arquivos de `app/assets/govbr-ds/`: bundles, componentes
  isolados e cópias `.min` duplicadas, em ordem alfabética.
- A edição de campi (`app/templates/configuracoes.html`, seção "Campi do Sistec") põe identificador, código da unidade, cidade e nome da unidade
  em quatro campos sem rótulo visível dentro de uma única célula de tabela, com um botão "Salvar" por linha. As
  confirmações usam `data-confirm` (12 usos em `atualizar.html`, `configuracoes.html` e `atualizar.js`).
- `style.css` quebra o layout em 768px e 320px. O DS define 576px, 992px, 1280px e 1600px
  (página Sistema de Grid do gov.br/ds e `--grid-breakpoint-*` em `dist/core-tokens.css`), com grid de 4, 8 e 12 colunas.

A constituição (Restrições Técnicas e de Segurança) já exige interface no gov.br DS e responsiva, com validação em
celular real antes do cutover; `CUTOVER.md` mantém esse item aberto.

## Goals

- [ ] As 5 páginas públicas e as 6 páginas administrativas usam componentes `br-*` do gov.br DS 3.7.0 para cabeçalho,
      menu, rodapé, cartões, tabelas, filtros, botões e mensagens.
- [ ] Nenhuma página tem rolagem horizontal entre 320px e 1920px, e os pontos de quebra são os do DS.
- [ ] O DS é carregado uma única vez por página (1 CSS + 1 JS), sem os 162 arquivos avulsos e sem Bootstrap.
- [ ] As 11 páginas têm tema claro e tema escuro, escolhidos pela preferência do sistema ou por um botão no cabeçalho.
- [ ] A gestão de campi do Sistec (listar, editar, incluir, desativar, excluir) segue o padrão de CRUD do DS: lista em tabela, edição em página própria com rótulos visíveis e exclusão com modal de confirmação.
- [ ] O item "design gov.br validado em dispositivo móvel real" de `CUTOVER.md` fica marcado com resultado registrado.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature                                                  | Reason                                                                 |
| -------------------------------------------------------- | ---------------------------------------------------------------------- |
| Migração para o gov.br DS v4                             | Decisão do usuário: manter 3.7.0; v4 exige rever todas as telas        |
| Barra de identidade do Governo Federal (barra gov.br)    | O painel não é sistema gov.br oficial; só adota o DS (decisão anterior RF-02) |
| Outros temas (alto contraste, cores por instituição)     | Só claro e escuro foram pedidos                                        |
| Novos gráficos ou mudança de indicadores e cálculos      | Feature só de apresentação; Princípio I (paridade) não é tocado        |
| Interface da extensão `extensao-sistec/` (`options.html`) | Fora do painel; tem ciclo de publicação próprio                        |
| Banner de cookies (`cookiebar`) do DS                    | O painel não usa cookies de rastreamento                               |
| Modelos de LGPD (termo de consentimento, política de privacidade, preferências de dados) | O painel não coleta nem guarda dado pessoal (Princípio III da constituição) |
| Aviso de expiração de sessão, "Entrar com gov.br", "Primeiro acesso" e "Manter-me conectado" dos modelos de sessão | Decisão do usuário: o painel não tem vínculo com o login gov.br; o login é só do administrador local (e-mail e senha) |
| Seleção em lote, ordenação por coluna, menu de três pontos e ação "Visualizar" da lista de CRUD do modelo | Não há caso de uso na gestão de campi |
| Painel "Filtros" recolhível da lista de CRUD              | A busca por texto cobre a lista de cerca de 22 campi                    |
| Assistente em etapas (`br-step`) do modelo de cadastro   | Os formulários de campus têm 5 campos, sem etapas                       |

---

## Assumptions & Open Questions

Every ambiguity is resolved or recorded here - nothing is left silently unclear.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Nível de uso do DS nas páginas públicas | Componentes `br-*` (cabeçalho, menu, cartão, tabela, select, radio, botão, mensagem, rodapé); sem depender do visual do Bootstrap | Resposta do usuário: "usar o design system do gov.br" de fato, não só tokens | y |
| Versão do DS | 3.7.0, a já versionada em `app/assets/govbr-ds/` | Resposta do usuário; os tokens de `style.css` já foram conferidos contra ela | y |
| Referência normativa do DS | Site gov.br/ds (página Sistema de Grid, lida no navegador) e, para valores exatos, os tokens do pacote local `@govbr-ds/core` 3.7.0; a wiki `govbr-ds-wiki` é de contribuição e não define grid | Referências indicadas pelo usuário. O arquivo do Figma da comunidade não pôde ser lido (WebFetch 403; página em canvas, sem texto), então os valores de grid vêm do site e do pacote, que coincidem entre si | y |
| Pontos de quebra | 576px, 992px, 1280px e 1600px (faixas 0-575, 576-991, 992-1279, 1280-1599, 1600+); substituem os 768px e 320px de `style.css` | Página Sistema de Grid do gov.br/ds e `--grid-breakpoint-*` no pacote local | n |
| Largura mínima suportada | 320px | WCAG 1.4.10 (reflow) e já era RF-07 da feature anterior | n |
| Grid fluida ou fixa | Fluida (`container-fluid`, 100%) até 1599px; fixa com `max-width` de 1520px a partir de 1600px | O DS recomenda grid fluida para sistemas que precisam do espaço útil (tabelas largas) e fixa para TV, por legibilidade; 1520px é `--grid-tv-maxwidth` | n |
| Colunas, margem e medianiz | 4 colunas, margem 8px, medianiz 16px abaixo de 576px; 8 colunas, margem 40px, medianiz 24px de 576px a 1279px; 12 colunas, margem 40px, medianiz 24px de 1280px a 1599px e 40px a partir de 1600px | Tokens `--grid-portrait/tablet/desktop/tv-*` e página Sistema de Grid | n |
| Escopo de telas | 5 páginas públicas (Dash) e 6 administrativas (Flask: login, recuperar acesso, instalação, atualizar, histórico, configurações) | O pedido é "o design da aplicação" | n |
| Origem dos arquivos do DS | Local, sem CDN | Já versionado; painel não pode depender de rede externa nem enviar acessos a terceiros | n |
| Ativação do tema escuro | Começa pela preferência do sistema (`prefers-color-scheme`); botão no cabeçalho alterna claro e escuro e a escolha fica salva no navegador | Resposta do usuário | y |
| Escopo do tema escuro | As 11 telas (5 públicas e 6 administrativas) | Resposta do usuário; evita o sistema mudar de aparência ao entrar na área administrativa | y |
| Suporte do DS 3.7.0 a tema escuro | O pacote não tem tema global nem `prefers-color-scheme`; tem o modificador `.dark-mode` por componente (card, table, button, input, select, radio e outros). Nos arquivos locais não achei `.dark-mode` para header, menu, footer e message; o Design confirma e cobre as lacunas sobrepondo variáveis do DS em `style.css` | Busca em `dist/core.css` e `dist/core-tokens.css`; o site gov.br/ds não foi consultado sobre tema escuro | n |
| Persistência da escolha de tema | `localStorage`, chave `calcsistec-tema`, valores `claro` e `escuro`; sem cookie | Dado não pessoal, então o Princípio III da constituição não é afetado; nada vai ao servidor | n |
| Logotipo no tema escuro | Fica sobre uma superfície clara no cabeçalho nos dois temas, como o `app-header-logo` de hoje | Logotipos enviados pelo administrador são feitos para fundo claro e não dá para inverter as cores com segurança | n |
| Mudança de preferência do sistema com a página aberta | Sem escolha salva, a página segue a nova preferência sem recarregar | Comportamento esperado de quem alterna claro e escuro no sistema | n |
| Modelos visuais do Figma | Os 4 arquivos `.svg` desta pasta: "Modelos de CRUD + LGPD" (lista, edição, exclusão, erro), "Modelos de Dashboard" (5 páginas públicas), "Modelos de Sessão do Usuário" (login) e "Template V3 - Base" (cabeçalho, menu, rodapé, grades de 4, 8 e 12 colunas). O texto dos SVGs está em curvas, então li as telas renderizando-as em imagem no Chrome | Arquivos do usuário | y |
| Tela de edição de campus | Página própria com rota e breadcrumb, não linha editável na tabela nem modal | O modelo de CRUD do DS abre "Editar ... \| id" em página com título, campos com rótulo e Cancelar/Salvar | n |
| Ação "Visualizar" (olho) do modelo | Omitida | Todos os dados do campus já estão na linha da lista | n |
| Paginação da lista de campi | 10 itens por página, com opções 10, 25 e 50 | Valor do modelo do DS; hoje são cerca de 22 campi | n |
| Identificador de perfil suspeito | Salvar continua permitido; a linha mostra aviso porque `id_suspeito` (`app/data/campi.py`) só marca o caso e a atualização recusa campus sem identificador válido (Princípio VI) | Comportamento atual do código | n |
| Posição do botão de tema | Ícone de contraste no grupo de ações do `br-header`, como nos modelos do DS | Posição usada nos modelos | n |
| Menu principal | `br-menu` sobreposto abaixo de 992px e persistente, aberto por padrão, a partir de 992px, com hambúrguer sempre presente; cai para sobreposto em todas as larguras se o modo persistente falhar na verificação visual | Padrão do Template V3 Base do DS; aprovado pelo usuário no Design | y |
| Selects dos filtros públicos | `dcc.Dropdown` com variáveis do DS | `br-select` depende do JS do DS na carga e o Dash cria os filtros depois; aprovado pelo usuário no Design | y |
| Busca da lista de campi | Por envio (Enter ou lupa), processada no servidor | Evita JavaScript próprio; aprovado pelo usuário no Design | y |
| Componentes `dbc.*` que sobrarem | Podem ficar como comportamento (ex.: `dbc.RadioItems`, escolhido por evitar bug de estado de `dcc.RadioItems`), recebendo classes `br-*`; a folha do Bootstrap não é carregada | Preserva o comportamento já testado dos filtros; o Design decide caso a caso | n |
| Fonte Rawline | O pacote 3.7.0 não traz `@font-face` (nenhum encontrado em `core.css`); fonte do sistema é aceitável se Rawline não estiver disponível | Evita fonte quebrada; o Design confirma se há arquivo de fonte no pacote | n |
| Área mínima de toque | 24×24px CSS | WCAG 2.2 AA, critério 2.5.8; o projeto já adota 2.2 AA | n |
| Como verificar larguras reais | `pytest` para HTML, classes e CSS estáticos; conferência visual em 320, 576, 992, 1280 e 1600px no navegador; sem nova dependência de teste de navegador | Constituição exige justificar nova dependência no plano | n |
| Varredura de dimensões implícitas | Validação de entrada: coberta por DS-21. Falha: casos de borda. Dependência externa: DS-24 (DS local, sem CDN). Auth, idempotência, concorrência, ciclo de vida de dados, observabilidade e transição de estado: N/A porque a feature só muda apresentação | Dimensões da varredura do Specify | n |

**Open questions:** none - all resolved or logged above (required before the spec is confirmed).

---

## User Stories

### P1: Layout responsivo de 320px a telas grandes ⭐ MVP

**User Story**: As a usuário do painel, I want ver as páginas ajustadas ao tamanho da minha tela so that consigo ler
indicadores e navegar tanto no celular quanto no monitor.

**Why P1**: É o pedido central; sem isso o painel não serve a quem abre o link no celular.

**Acceptance Criteria**:

1. The system SHALL declarar `<meta name="viewport" content="width=device-width, initial-scale=1">` em toda página pública e administrativa.  <!-- ubiquitous -->
2. The system SHALL definir pontos de quebra somente em 576px, 992px, 1280px e 1600px, os do gov.br DS 3.7.0.  <!-- ubiquitous -->
3. WHILE a largura da viewport estiver entre 320px e 1920px, the system SHALL NOT exibir rolagem horizontal na página.  <!-- state-driven -->
4. WHILE a viewport tiver menos de 992px, the system SHALL exibir o menu principal sobreposto e fechado por padrão, aberto pelo botão hambúrguer com `aria-expanded`.  <!-- state-driven -->
5. WHILE a viewport tiver 992px ou mais, the system SHALL exibir o menu principal persistente e aberto por padrão, com o botão hambúrguer presente para recolhê-lo.  <!-- state-driven -->
6. WHILE a viewport tiver menos de 576px, the system SHALL empilhar cartões de KPI, medidores e filtros em uma única coluna.  <!-- state-driven -->
7. WHILE a viewport tiver 1600px ou mais, the system SHALL limitar o conteúdo a 1520px de largura, centralizado.  <!-- state-driven -->
8. IF uma tabela for mais larga que a viewport THEN the system SHALL rolar só a tabela na horizontal, dentro de um contêiner, sem mover o restante da página.  <!-- unwanted-behavior -->
9. The system SHALL dar a todo controle interativo área mínima de 24×24px CSS.  <!-- ubiquitous -->
10. The system SHALL organizar o layout em 4 colunas abaixo de 576px, em 8 colunas de 576px a 1279px e em 12 colunas a partir de 1280px.  <!-- ubiquitous -->
11. The system SHALL posicionar o conteúdo com as classes de grid do DS (`container-fluid`, `row`, `col-*`), sem grid próprio em `style.css`.  <!-- ubiquitous -->

**Independent Test**: Abrir cada página em 320, 576, 992, 1280 e 1600px e ver: sem barra de rolagem horizontal da
página, menu recolhido abaixo de 992px, cartões em coluna única abaixo de 576px.

---

### P1: Páginas públicas com componentes do DS ⭐ MVP

**User Story**: As a visitante do painel, I want telas com a aparência e o comportamento do gov.br so that reconheço o
padrão de governo e uso os controles sem estranhar.

**Why P1**: É o segundo pedido explícito; hoje o visual é próprio, só com as cores do DS.

**Acceptance Criteria**:

1. The system SHALL renderizar o cabeçalho das 5 páginas públicas com o componente `br-header` do DS, contendo o logotipo, o título "Painel de Acompanhamento Sistec" e o nome da instituição.  <!-- ubiquitous -->
2. The system SHALL renderizar o menu principal com o componente `br-menu`, com os itens Início, Matrículas, Eficiência Acadêmica, Taxa de Evasão Anual e Percentuais Legais, nessa ordem.  <!-- ubiquitous -->
3. WHEN uma página pública é exibida THEN the system SHALL marcar o item de menu dessa página com `aria-current="page"` e com o estado ativo do DS.  <!-- event-driven -->
4. The system SHALL renderizar KPIs, medidores e cartões de navegação da capa com o componente `br-card`.  <!-- ubiquitous -->
5. The system SHALL renderizar as tabelas de dados com o componente `br-table`.  <!-- ubiquitous -->
6. The system SHALL renderizar os filtros de opção exclusiva com `br-radio`, os filtros de lista com `dcc.Dropdown` estilizado pelas variáveis do DS e o botão "Limpar Filtros" com `br-button`.  <!-- ubiquitous -->
7. The system SHALL renderizar o rodapé com o componente `br-footer`, contendo nome, site e e-mail de contato da instituição e o link "Área administrativa".  <!-- ubiquitous -->
8. The system SHALL exibir o aviso "sem correção PNP" e o aviso de filtro PROEJA com o componente `br-message` do tipo `warning`.  <!-- ubiquitous -->
9. The system SHALL NOT carregar a folha de estilo `dbc.themes.BOOTSTRAP` nas páginas públicas.  <!-- ubiquitous -->
10. WHEN uma página pública diferente da capa é exibida THEN the system SHALL mostrar abaixo do cabeçalho o `br-breadcrumb` "Início > título da página".  <!-- event-driven -->

**Independent Test**: Abrir `/`, `/matriculas`, `/eficiencia`, `/evasao` e `/percentuais-legais` e conferir no HTML
renderizado as classes `br-header`, `br-menu`, `br-card`, `br-table`, `br-footer`, sem `card`/`table`/`navbar` do Bootstrap.

---

### P1: Páginas administrativas com o mesmo DS ⭐ MVP

**User Story**: As a administradora da Pesquisa Institucional, I want telas de login, atualização e configuração no
mesmo padrão do painel so that o sistema parece um só e funciona no celular.

**Why P1**: Compõem "a aplicação"; hoje têm cabeçalho e rodapé próprios, diferentes dos públicos.

**Acceptance Criteria**:

1. The system SHALL renderizar cabeçalho e rodapé de todas as páginas administrativas com os mesmos `br-header` e `br-footer` das páginas públicas.  <!-- ubiquitous -->
2. The system SHALL renderizar campos, botões e tabelas dos formulários administrativos com `br-input` ou `br-password` ou `br-select`, `br-button` e `br-table`.  <!-- ubiquitous -->
3. IF um campo de formulário for inválido THEN the system SHALL marcar o campo com o estado `danger` do DS e ligar a mensagem de erro ao campo por `aria-describedby`.  <!-- unwanted-behavior -->
4. WHEN uma ação administrativa termina THEN the system SHALL informar o resultado com `br-message` do tipo `success` ou `danger`, com `role="alert"`.  <!-- event-driven -->
5. WHILE a viewport tiver menos de 576px, the system SHALL exibir formulários administrativos em largura total, com os botões empilhados.  <!-- state-driven -->
6. The system SHALL exibir `br-breadcrumb` abaixo do cabeçalho em todas as páginas administrativas, exceto login, recuperar acesso e instalação.  <!-- ubiquitous -->
7. The system SHALL apresentar o login administrativo com o título "Acesso ao sistema", campos com rótulo acima e texto de apoio, o link "Esqueci minha senha" abaixo do campo de senha e o botão "Entrar" na largura do formulário.  <!-- ubiquitous -->
8. The system SHALL pedir confirmação de ação administrativa destrutiva com `br-modal`, contendo ícone de alerta, a pergunta e os botões "Cancelar" (`secondary`) e de confirmação (`primary`).  <!-- ubiquitous -->
9. The system SHALL NOT usar o diálogo nativo `confirm()` do navegador.  <!-- ubiquitous -->
10. WHILE um `br-modal` estiver aberto, the system SHALL manter o foco do teclado dentro dele, fechá-lo com Esc e devolver o foco ao controle que o abriu.  <!-- state-driven -->

**Independent Test**: Abrir `/admin/login`, `/admin/atualizar`, `/admin/historico` e `/admin/config` em 320px e ver
cabeçalho e rodapé iguais aos públicos, campos e botões em largura total, e a tabela de campi rolando dentro do seu contêiner.

---

### P1: Gestão de campi no padrão de CRUD do DS ⭐ MVP

**User Story**: As a administradora da Pesquisa Institucional, I want listar, editar, incluir, desativar e excluir os
campi do Sistec em telas organizadas so that corrijo identificador, código e nome da unidade sem errar campo.

**Why P1**: A edição atual é o ponto mais mal formatado da área administrativa e bloqueia a atualização quando o
identificador está errado.

**Acceptance Criteria**:

1. The system SHALL exibir a lista de campi com o título "Campi do Sistec", em `br-table`, com as colunas Perfil, Identificador, Código da unidade, Cidade, Nome da unidade, Situação e Ações.  <!-- ubiquitous -->
2. The system SHALL exibir a situação de cada campus como `br-tag` com o texto "Ativo" ou "Desativado", além da cor.  <!-- ubiquitous -->
3. IF o identificador de um campus for suspeito segundo `id_suspeito` THEN the system SHALL exibir na linha o aviso "Identificador inválido: a atualização não roda assim".  <!-- unwanted-behavior -->
4. The system SHALL exibir na coluna Ações de cada linha os botões de ícone Editar, Desativar (ou Reativar) e Excluir, cada um com nome acessível que cita o perfil, como "Editar campus {nome do perfil}".  <!-- ubiquitous -->
5. WHEN o usuário aciona Editar THEN the system SHALL abrir a tela "Editar campus | {nome do perfil}" com o `br-breadcrumb` "Configurações > Campi > Editar".  <!-- event-driven -->
6. The system SHALL apresentar na tela de edição os campos Identificador do perfil, Código da unidade, Cidade e Nome da unidade, cada um em `br-input` com rótulo visível acima do campo, em linhas da grade do DS.  <!-- ubiquitous -->
7. WHILE a tela de edição ou de inclusão é exibida, the system SHALL apresentar os botões "Cancelar" (`br-button secondary`) e "Salvar" (`br-button primary`) no rodapé do formulário, alinhados à direita a partir de 576px.  <!-- state-driven -->
8. WHEN o usuário aciona Salvar com todos os campos válidos THEN the system SHALL gravar o campus, voltar à lista e exibir `br-message` do tipo `success` "Campus atualizado.".  <!-- event-driven -->
9. IF um campo obrigatório estiver vazio ao Salvar THEN the system SHALL manter a tela, marcar o campo com o estado `danger` e exibir abaixo dele "Preencha o campo obrigatório".  <!-- unwanted-behavior -->
10. IF o identificador ou o código da unidade já pertencer a outro campus THEN the system SHALL marcar o campo com o estado `danger` e exibir a mensagem da regra ("esse identificador de perfil já está em outro campus" ou "esse código da unidade já está em outro campus").  <!-- unwanted-behavior -->
11. IF ao menos um campo obrigatório estiver vazio ao Salvar THEN the system SHALL exibir no topo da página `br-message` do tipo `danger` "Erro. Preencha abaixo os campos obrigatórios antes de enviar os dados.", com `role="alert"`.  <!-- unwanted-behavior -->
12. WHEN o usuário aciona Excluir THEN the system SHALL abrir `br-modal` com a pergunta "Tem certeza que deseja excluir o campus {nome do perfil}?", o aviso de que o perfil volta na próxima atualização se ainda existir no Sistec, e os botões "Cancelar" e "Excluir".  <!-- event-driven -->
13. WHEN o usuário confirma "Excluir" THEN the system SHALL remover o perfil da lista e exibir `br-message` do tipo `success` "Perfil excluído da lista.".  <!-- event-driven -->
14. WHEN o usuário aciona "Cancelar" no modal de exclusão THEN the system SHALL fechar o modal sem excluir o campus.  <!-- event-driven -->
15. WHEN o usuário aciona Desativar ou Reativar THEN the system SHALL alterar a situação do campus sem pedir confirmação e exibir `br-message` do tipo `success`.  <!-- event-driven -->
16. WHEN o usuário aciona "Incluir campus" THEN the system SHALL abrir a tela "Incluir campus" com os campos Identificador do perfil, Nome do perfil, Código da unidade, Cidade e Nome da unidade, no mesmo layout da edição.  <!-- event-driven -->
17. WHEN o usuário aciona Salvar na inclusão com identificador e nome do perfil preenchidos THEN the system SHALL gravar o campus, voltar à lista e exibir `br-message` do tipo `success` "Campus incluído.".  <!-- event-driven -->
18. The system SHALL NOT exibir campos de edição de campus dentro de célula de tabela.  <!-- ubiquitous -->

**Independent Test**: Em `/admin/config`, ver a lista de campi em tabela com tags e três ícones por linha; editar um
campus na página própria deixando o código vazio e ver o erro no campo e o banner; corrigir e salvar e ver a mensagem
de sucesso; excluir um campus e ver o modal, cancelar e ver a linha mantida.

---

### P1: Entrega única e limpa do DS ⭐ MVP

**User Story**: As a mantenedora do painel, I want o DS carregado de forma previsível so that as telas não mudam de
aparência por ordem de arquivos e a página não baixa centenas de arquivos.

**Why P1**: Sem isso os componentes `br-*` das outras histórias podem ser sobrescritos ou ficar sem JavaScript.

**Acceptance Criteria**:

1. The system SHALL servir o gov.br DS 3.7.0 a partir de `app/assets/govbr-ds/`, sem dependência de CDN.  <!-- ubiquitous -->
2. The system SHALL carregar `core.min.css` exatamente uma vez por página, pública ou administrativa.  <!-- ubiquitous -->
3. The system SHALL carregar `core-init.min.js` (o script do DS que também instancia os componentes, AD-004) exatamente uma vez por página, pública ou administrativa.  <!-- ubiquitous -->
4. The system SHALL usar, em conteúdo renderizado pelo Dash, apenas componentes do DS que funcionam sem JavaScript.  <!-- ubiquitous -->
5. The system SHALL NOT carregar arquivos individuais de `dist/components/` nem versões não minificadas dos bundles do DS.  <!-- ubiquitous -->
6. The system SHALL definir em `app/assets/style.css` apenas regras que o DS não cobre, sem cores hexadecimais literais e sem `@media` de largura fora dos pontos de quebra do DS (`prefers-color-scheme` é permitido).  <!-- ubiquitous -->
7. The system SHALL NOT declarar em `app/assets/style.css` variáveis `--gov-*` de cor ou espaçamento que dupliquem os tokens do DS.  <!-- ubiquitous -->

**Independent Test**: Listar os `<link>` e `<script>` do HTML de uma página pública e de uma administrativa: um CSS e um
JS do DS em cada; e rodar o teste estático de `style.css` (sem hex, sem `@media` de 768px/320px, sem `--gov-*`).

---

### P2: Busca e paginação na lista de campi

**User Story**: As a administradora, I want buscar um campus e paginar a lista so that acho o perfil certo sem
percorrer as 22 linhas.

**Why P2**: A gestão funciona sem isso; a busca e a paginação seguem o modelo de lista do DS e ajudam em telas pequenas.

**Acceptance Criteria**:

1. The system SHALL exibir acima da tabela de campi uma barra com o título "Campi" e um campo de busca por texto.  <!-- ubiquitous -->
2. WHEN o usuário envia a busca (Enter ou botão de lupa) THEN the system SHALL listar só os campi cujo perfil, cidade ou nome da unidade contêm o texto, sem diferenciar maiúsculas de minúsculas.  <!-- event-driven -->
3. IF a busca não encontrar nenhum campus THEN the system SHALL exibir `br-message` do tipo `info` "Nenhum campus encontrado.".  <!-- unwanted-behavior -->
4. The system SHALL paginar a lista no rodapé da tabela, com o seletor "Exibir" (10, 25 ou 50 itens, padrão 10), o texto "1-10 de N itens" e os botões de página anterior e próxima.  <!-- ubiquitous -->

**Independent Test**: Digitar parte do nome de uma cidade e ver só as linhas que a contêm; buscar um texto inexistente
e ver a mensagem; trocar "Exibir" para 25 e ver a contagem mudar.

---

### P2: Acessibilidade (WCAG 2.2 AA)

**User Story**: As a pessoa que usa teclado ou leitor de tela, I want navegar e ler o painel sem barreiras so that
tenho o mesmo acesso aos indicadores.

**Why P2**: O DS já traz a base acessível e a constituição cita WCAG 2.2 AA; é obrigatório antes do cutover, mas não
bloqueia a demonstração do layout.

**Acceptance Criteria**:

1. The system SHALL declarar `lang="pt-BR"` no elemento `<html>` de todas as páginas.  <!-- ubiquitous -->
2. The system SHALL oferecer, como primeiro elemento focável de toda página, o link "Ir para o conteúdo principal", que leva o foco a `#main-content`.  <!-- ubiquitous -->
3. WHILE um controle interativo estiver com foco de teclado, the system SHALL exibir contorno visível de ao menos 3px, com contraste mínimo de 3:1 contra o fundo, nos temas claro e escuro.  <!-- state-driven -->
4. The system SHALL manter contraste mínimo de 4,5:1 entre texto normal e fundo em todas as páginas, nos temas claro e escuro.  <!-- ubiquitous -->
5. The system SHALL apresentar a situação dos medidores (dentro ou fora do limite) e a faixa de evasão (baixa, média, alta) com rótulo textual, além da cor.  <!-- ubiquitous -->
6. The system SHALL fornecer texto alternativo em toda imagem informativa, incluindo o logotipo.  <!-- ubiquitous -->
7. WHEN o usuário aciona o botão do menu recolhido com Enter ou Espaço THEN the system SHALL abrir o menu e mover o foco para o primeiro item.  <!-- event-driven -->
8. WHEN o usuário pressiona Esc com o menu recolhido aberto THEN the system SHALL fechá-lo e devolver o foco ao botão.  <!-- event-driven -->

**Independent Test**: Percorrer cada página só com o teclado (Tab, Enter, Esc) e ver foco sempre visível, link de
salto funcionando e menu abrindo e fechando; rodar verificação de contraste nas cores do `style.css`.

---

### P2: Tema escuro

**User Story**: As a usuário do painel, I want ver as telas em tema escuro so that leio com conforto em ambiente
escuro e respeito a preferência do meu aparelho.

**Why P2**: Foi pedido junto com o layout; depende dos componentes `br-*` das histórias P1, por isso vem depois.

**Acceptance Criteria**:

1. WHEN uma página carrega sem escolha salva e o sistema do usuário prefere o tema escuro THEN the system SHALL exibir o tema escuro.  <!-- event-driven -->
2. WHEN uma página carrega sem escolha salva e o sistema do usuário prefere o tema claro ou não informa preferência THEN the system SHALL exibir o tema claro.  <!-- event-driven -->
3. The system SHALL exibir no cabeçalho de todas as páginas um botão que alterna entre os temas claro e escuro, com rótulo textual ("Usar tema escuro" ou "Usar tema claro") e `aria-pressed`.  <!-- ubiquitous -->
4. WHEN o usuário aciona o botão de tema THEN the system SHALL aplicar o novo tema a todos os componentes da página sem recarregá-la.  <!-- event-driven -->
5. WHEN o usuário aciona o botão de tema THEN the system SHALL salvar a escolha em `localStorage` na chave `calcsistec-tema`.  <!-- event-driven -->
6. WHEN uma página carrega com escolha salva THEN the system SHALL aplicar a escolha salva, ignorando a preferência do sistema.  <!-- event-driven -->
7. IF o navegador bloquear o acesso ao `localStorage` THEN the system SHALL manter o tema escolhido na página atual e voltar à preferência do sistema no próximo carregamento, sem mostrar erro.  <!-- unwanted-behavior -->
8. The system SHALL aplicar o tema antes da primeira pintura da página, sem exibir quadro claro antes do escuro.  <!-- ubiquitous -->
9. The system SHALL aplicar o tema escuro a cabeçalho, menu, cartões, tabelas, filtros, botões, mensagens, formulários e rodapé, sem componente que permaneça no tema claro.  <!-- ubiquitous -->
10. The system SHALL definir as cores do tema escuro somente por tokens do DS ou por sobreposição de variáveis do DS, sem cor hexadecimal literal.  <!-- ubiquitous -->
11. The system SHALL exibir o logotipo da instituição sobre superfície clara em ambos os temas.  <!-- ubiquitous -->

**Independent Test**: Com o sistema em modo escuro e sem escolha salva, abrir `/` e ver o tema escuro; acionar o
botão, ver o tema claro sem recarregar; recarregar e ver o tema claro mantido; repetir em `/admin/login`.

---

### P2: Identidade institucional configurável no cabeçalho e no rodapé

**User Story**: As a administradora de outra instituição da Rede Federal, I want o nome, o site, o contato e o
logotipo da minha instituição no cabeçalho e no rodapé so that o painel serve à minha instituição sem mudar código.

**Why P2**: Já existe e a constituição (Princípio V) exige; precisa continuar valendo ao trocar para `br-header` e `br-footer`.

**Acceptance Criteria**:

1. The system SHALL obter nome, sigla, site, e-mail de contato e logotipo exibidos no cabeçalho e no rodapé da configuração da instituição, nunca de literal no código.  <!-- ubiquitous -->
2. IF a instituição não tiver logotipo enviado THEN the system SHALL exibir o logotipo genérico `app/assets/branding/padrao-generico.svg`.  <!-- unwanted-behavior -->
3. IF um dado de contato da instituição estiver em branco THEN the system SHALL omiti-lo do rodapé, sem deixar rótulo ou espaço vazio.  <!-- unwanted-behavior -->

**Independent Test**: Renderizar cabeçalho e rodapé com a configuração preenchida, com logotipo ausente e com e-mail
e site em branco, e conferir o HTML nos três casos.

---

### P3: Lista de campi em cards

**User Story**: As a administradora usando o celular, I want ver os campi em cards so that leio cada campus sem
rolar a tabela na horizontal.

**Why P3**: O modelo do DS traz o botão "Visualizar em Cards", mas a tabela com rolagem contida já atende (DS-08).

**Acceptance Criteria**:

1. The system SHALL exibir acima da lista de campi um botão que alterna entre "Visualizar em Cards" e "Visualizar em Lista", com `aria-pressed`.  <!-- ubiquitous -->
2. WHEN o usuário escolhe "Visualizar em Cards" THEN the system SHALL exibir cada campus em um `br-card` com perfil, identificador, código, cidade, nome da unidade, situação e as mesmas ações da linha.  <!-- event-driven -->

**Independent Test**: Em 320px, acionar "Visualizar em Cards" e ver um card por campus, com os botões Editar, Desativar
e Excluir funcionando.

---

### P3: Validação em dispositivo real

**User Story**: As a responsável pelo cutover, I want ver o painel em um celular de verdade so that confirmo o que os
testes de largura não pegam (toque, teclado virtual, barra de endereço).

**Why P3**: É passo humano, depois da implementação; já é pendência de `CUTOVER.md`.

**Acceptance Criteria**:

1. WHEN a validação de cutover é feita THEN o checklist de `CUTOVER.md` SHALL registrar o resultado do teste em ao menos 1 celular real (largura de 320px a 430px) e em 1 tela de 1280px ou mais, para as 5 páginas públicas e a tela `/admin/atualizar`.  <!-- event-driven -->

**Independent Test**: Ler `CUTOVER.md` e ver o item de design marcado, com dispositivo, largura e data.

---

## Edge Cases

Edge cases are usually unwanted-behavior (IF/THEN) or boundary (WHEN) criteria:

- IF não houver dados publicados THEN the system SHALL exibir "Ainda não há dados publicados." em `br-message` do tipo `info`, sem KPIs zerados.
- WHEN o sistema do usuário muda entre claro e escuro com a página aberta e sem escolha salva THEN the system SHALL seguir a nova preferência sem recarregar.
- IF um medidor ou aviso usar cor de estado (verde, vermelho, amarelo) THEN the system SHALL manter o rótulo textual legível no tema escuro (ver DS-35).
- IF não houver campus cadastrado THEN the system SHALL exibir `br-message` do tipo `info` convidando a importar a lista de perfis ou incluir um campus.
- IF o usuário abrir a tela de edição de um campus que foi excluído em outra aba THEN the system SHALL voltar à lista com `br-message` do tipo `danger` "Campus não encontrado.".
- IF `core-init.min.js` não carregar THEN the system SHALL manter os links de navegação visíveis e acionáveis, sem menu preso fechado.
- IF a tabela de campi tiver mais colunas do que cabem em 320px THEN the system SHALL rolar só o contêiner da tabela (ver AC 8 da primeira história).
- WHEN o usuário amplia o zoom para 200% em uma tela de 1280px THEN the system SHALL se comportar como em 640px, sem perda de conteúdo nem rolagem horizontal da página.
- WHEN a orientação do aparelho muda entre retrato e paisagem THEN the system SHALL reorganizar o layout sem recarregar a página.
- IF a fonte Rawline não estiver disponível THEN the system SHALL usar a fonte do sistema, sem alterar quebras de linha a ponto de criar rolagem horizontal.
- IF a viewport tiver menos de 320px THEN the system SHALL manter o conteúdo legível, mesmo com rolagem horizontal (fora do suportado).

---

## Requirement Traceability

Each requirement gets a unique ID for tracking across design, tasks, and validation.

| Requirement ID | Story                                   | Phase  | Status  |
| -------------- | --------------------------------------- | ------ | ------- |
| DS-01          | P1: Layout responsivo (AC 1, viewport)  | Design | Verified |
| DS-02          | P1: Layout responsivo (AC 2, breakpoints) | Design | Verified |
| DS-03          | P1: Layout responsivo (AC 3, sem rolagem horizontal) | Design | Verified |
| DS-04          | P1: Layout responsivo (AC 4, menu sobreposto < 992px) | Design | Verified |
| DS-05          | P1: Layout responsivo (AC 5, menu persistente >= 992px) | Design | Verified |
| DS-06          | P1: Layout responsivo (AC 6, coluna única < 576px) | Design | Verified |
| DS-07          | P1: Layout responsivo (AC 7, máx. 1520px em 1600px+) | Design | Verified |
| DS-08          | P1: Layout responsivo (AC 8, tabela rolável) | Design | Verified |
| DS-09          | P1: Layout responsivo (AC 9, área de toque) | Design | Verified |
| DS-10          | P1: Páginas públicas (AC 1, br-header)  | Design | Verified |
| DS-11          | P1: Páginas públicas (AC 2, br-menu)    | Design | Verified |
| DS-12          | P1: Páginas públicas (AC 3, aria-current) | Design | Verified |
| DS-13          | P1: Páginas públicas (AC 4, br-card)    | Design | Verified |
| DS-14          | P1: Páginas públicas (AC 5, br-table)   | Design | Verified |
| DS-15          | P1: Páginas públicas (AC 6, filtros)    | Design | Verified |
| DS-16          | P1: Páginas públicas (AC 7, br-footer)  | Design | Verified |
| DS-17          | P1: Páginas públicas (AC 8, br-message) | Design | Verified |
| DS-18          | P1: Páginas públicas (AC 9, sem Bootstrap) | Design | Verified |
| DS-19          | P1: Páginas administrativas (AC 1, header e footer) | Design | Verified |
| DS-20          | P1: Páginas administrativas (AC 2, formulários) | Design | Verified |
| DS-21          | P1: Páginas administrativas (AC 3, campo inválido) | Design | Verified |
| DS-22          | P1: Páginas administrativas (AC 4, resultado da ação) | Design | Verified |
| DS-23          | P1: Páginas administrativas (AC 5, < 576px) | Design | Verified |
| DS-24          | P1: Entrega do DS (AC 1, local)         | Design | Implementing |
| DS-25          | P1: Entrega do DS (AC 2, um CSS)        | Design | Verified |
| DS-26          | P1: Entrega do DS (AC 3, um JS)         | Design | Verified |
| DS-27          | P1: Entrega do DS (AC 4, só componentes sem JS no Dash) | Design | Verified |
| DS-28          | P1: Entrega do DS (AC 5, sem avulsos)   | Design | Verified |
| DS-29          | P1: Entrega do DS (AC 6, style.css enxuto) | Design | Verified |
| DS-30          | P1: Entrega do DS (AC 7, sem --gov-*)   | Design | Verified |
| DS-31          | P2: Acessibilidade (AC 1, lang)         | Design | Verified |
| DS-32          | P2: Acessibilidade (AC 2, link de salto) | Design | Verified |
| DS-33          | P2: Acessibilidade (AC 3, foco visível, 2 temas) | Design | Verified |
| DS-34          | P2: Acessibilidade (AC 4, contraste, 2 temas) | Design | Verified |
| DS-35          | P2: Acessibilidade (AC 5, rótulo textual) | Design | Verified |
| DS-36          | P2: Acessibilidade (AC 6, alt)          | Design | Verified |
| DS-37          | P2: Acessibilidade (AC 7, abrir menu por teclado) | Design | Verified |
| DS-38          | P2: Acessibilidade (AC 8, Esc fecha o menu) | Design | Verified |
| DS-39          | P2: Identidade (AC 1, da configuração)  | -      | Verified |
| DS-40          | P2: Identidade (AC 2, logotipo genérico) | -     | Verified |
| DS-41          | P2: Identidade (AC 3, contato em branco) | -     | Verified |
| DS-42          | P3: Dispositivo real (AC 1)             | -      | In Tasks |
| DS-43          | P1: Layout responsivo (AC 10, 4/8/12 colunas) | Design | Verified |
| DS-44          | P1: Layout responsivo (AC 11, classes de grid do DS) | Design | Verified |
| DS-45          | P2: Tema escuro (AC 1, sistema escuro) | Design | Verified |
| DS-46          | P2: Tema escuro (AC 2, sistema claro) | Design | Verified |
| DS-47          | P2: Tema escuro (AC 3, botão no cabeçalho) | Design | Verified |
| DS-48          | P2: Tema escuro (AC 4, aplica sem recarregar) | Design | Verified |
| DS-49          | P2: Tema escuro (AC 5, salva em localStorage) | Design | Verified |
| DS-50          | P2: Tema escuro (AC 6, escolha salva vence) | Design | Verified |
| DS-51          | P2: Tema escuro (AC 7, localStorage bloqueado) | Design | Verified |
| DS-52          | P2: Tema escuro (AC 8, sem flash) | Design | Verified |
| DS-53          | P2: Tema escuro (AC 9, todos os componentes) | Design | Verified |
| DS-54          | P2: Tema escuro (AC 10, só tokens do DS) | Design | Verified |
| DS-55          | P2: Tema escuro (AC 11, logotipo em superfície clara) | Design | Verified |
| DS-56          | P1: Páginas administrativas (AC 6, breadcrumb) | Design | Verified |
| DS-57          | P1: Páginas administrativas (AC 7, login "Acesso ao sistema") | Design | Verified |
| DS-58          | P1: Páginas administrativas (AC 8, confirmação em br-modal) | Design | Verified |
| DS-59          | P1: Páginas administrativas (AC 9, sem confirm() nativo) | Design | Verified |
| DS-60          | P1: Páginas administrativas (AC 10, foco e Esc no modal) | Design | Verified |
| DS-61          | P1: Páginas públicas (AC 10, breadcrumb) | Design | Verified |
| DS-62          | P1: CRUD de campi (AC 1, lista em br-table) | Design | Verified |
| DS-63          | P1: CRUD de campi (AC 2, br-tag de situação) | Design | Verified |
| DS-64          | P1: CRUD de campi (AC 3, aviso de identificador suspeito) | Design | Verified |
| DS-65          | P1: CRUD de campi (AC 4, botões de ícone com nome acessível) | Design | Verified |
| DS-66          | P1: CRUD de campi (AC 5, tela Editar campus) | Design | Verified |
| DS-67          | P1: CRUD de campi (AC 6, campos com rótulo visível) | Design | Verified |
| DS-68          | P1: CRUD de campi (AC 7, Cancelar e Salvar) | Design | Verified |
| DS-69          | P1: CRUD de campi (AC 8, salvar com sucesso) | Design | Verified |
| DS-70          | P1: CRUD de campi (AC 9, campo obrigatório vazio) | Design | Verified |
| DS-71          | P1: CRUD de campi (AC 10, identificador ou código duplicado) | Design | Verified |
| DS-72          | P1: CRUD de campi (AC 11, banner de erro) | Design | Verified |
| DS-73          | P1: CRUD de campi (AC 12, modal de exclusão) | Design | Verified |
| DS-74          | P1: CRUD de campi (AC 13, confirmar exclusão) | Design | Verified |
| DS-75          | P1: CRUD de campi (AC 14, cancelar exclusão) | Design | Verified |
| DS-76          | P1: CRUD de campi (AC 15, desativar e reativar) | Design | Verified |
| DS-77          | P1: CRUD de campi (AC 16, tela Incluir campus) | Design | Verified |
| DS-78          | P1: CRUD de campi (AC 17, incluir com sucesso) | Design | Verified |
| DS-79          | P1: CRUD de campi (AC 18, sem campos em célula de tabela) | Design | Verified |
| DS-80          | P2: Busca e paginação (AC 1, barra de busca) | Design | Verified |
| DS-81          | P2: Busca e paginação (AC 2, filtra ao enviar a busca) | Design | Verified |
| DS-82          | P2: Busca e paginação (AC 3, nenhum resultado) | Design | Verified |
| DS-83          | P2: Busca e paginação (AC 4, paginação) | Design | Verified |
| DS-84          | P3: Cards (AC 1, botão de visualização) | Design | Verified |
| DS-85          | P3: Cards (AC 2, br-card por campus) | Design | Verified |

**ID format:** `[CATEGORY]-[NUMBER]` (e.g., `DS-01`)

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 85 total, 85 mapped to tasks, 0 unmapped ✅

---

## Success Criteria

How we know the feature is successful:

- [ ] Em 320, 576, 992, 1280 e 1600px, as 11 páginas (5 públicas, 6 administrativas) não têm rolagem horizontal da página.
- [ ] O HTML de qualquer página carrega 1 CSS e 1 JS do DS e nenhum dos 162 arquivos avulsos de `app/assets/govbr-ds/`.
- [ ] Nenhuma página pública usa classes visuais do Bootstrap (`card`, `table`, `navbar`, `btn`).
- [ ] As 11 páginas abrem no tema escuro com o sistema em modo escuro, e o botão troca o tema sem recarregar e sem quadro claro na abertura.
- [ ] Em `/admin/config`, nenhum campo de campus fica dentro de célula de tabela, e editar, incluir e excluir um campus seguem o fluxo lista, página de edição e modal.
- [ ] `pytest` passa e `scripts/verificar_prontidao_cutover.py` sai com 0 (Constituição, Fluxo de Desenvolvimento).
- [ ] `CUTOVER.md` registra o teste em celular real e em tela grande.
