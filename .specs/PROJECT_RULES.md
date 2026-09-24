<!--
Sync Impact Report
- Version change: 1.2.0 → 1.3.0 (2026-09-24)
- Modified sections: "Restrições Técnicas e de Segurança" — a validação responsiva
  antes do cutover passa a ser feita no navegador (janela reduzida ou modo de
  dispositivo do DevTools, 320–430 px e 1280 px ou mais), não mais em dispositivo
  móvel real. Decisão da responsável pelo projeto (AD-006 em STATE.md).
- Principles I–VII: conteúdo preservado.
- Follow-up TODOs: nenhum.

Previous amendment:
- Version change: 1.1.0 → 1.2.0 (2026-09-24)
- Modified sections: "Fluxo de Desenvolvimento e Gates de Qualidade" — a fonte de
  regras e decisões passa a ser `.specs/`; a documentação histórica do Reversa deixa
  de ser fonte obrigatória e sai do repositório. Os identificadores herdados
  (`BR-*`, `RISK-*`, `D-*`, `P-*`) continuam válidos onde já aparecem.
- Modified references: o checklist de publicação é o do `DEPLOY.md`, que passa a ser o
  documento citado nos gates, na documentação acompanhada e em Governance.
- Principles I–VII: conteúdo preservado.
- Follow-up TODOs: nenhum.

Historical sync impact report (2026-09-22):
- Version change: 1.0.0 → 1.1.0 (2026-09-22)
- Workflow: Spec Kit substituído por tlc-spec-driven; regras do projeto movidas
  de .specify/memory/constitution.md para .specs/PROJECT_RULES.md.
- Principles I–VII: conteúdo preservado.

Historical ratification report (2026-09-16):
- Version change: (template sem valores) → 1.0.0
- Modified principles: n/a (primeira ratificação; todos os placeholders preenchidos)
  - [PRINCIPLE_1_NAME] → I. Paridade de Cálculo com a Regra Oficial (INEGOCIÁVEL)
  - [PRINCIPLE_2_NAME] → II. Domínio Puro e Camadas Separadas
  - [PRINCIPLE_3_NAME] → III. Privacidade: Nenhum Dado Pessoal Persistido (INEGOCIÁVEL)
  - [PRINCIPLE_4_NAME] → IV. Testes Automatizados como Gate
  - [PRINCIPLE_5_NAME] → V. Configuração no Lugar de Código Fixo
  - Adicionado: VI. Acesso ao Sistec pela Sessão do Usuário
  - Adicionado: VII. Publicação Versionada e Reversível
- Added sections: Restrições Técnicas e de Segurança; Fluxo de Desenvolvimento e Gates de Qualidade
- Removed sections: nenhuma
- Templates: dependentes (plan/spec/tasks) leem a constituição em tempo de execução; não alterados
  por este comando.
- Follow-up TODOs: nenhum. RATIFICATION_DATE = data desta primeira adoção formal (2026-09-16).
-->

# CalcSISTEC Constitution

## Core Principles

### I. Paridade de Cálculo com a Regra Oficial (INEGOCIÁVEL)

- Todo indicador (matrículas, matrícula equivalente, eficiência, evasão, percentuais legais,
  IEA) MUST reproduzir a regra oficial da PNP/Sistec e o resultado validado do painel legado
  (Power BI) para os mesmos dados de entrada.
- Toda alteração em regra `BR-MIGRAR-*` ou em função de `app/domain/` MUST vir acompanhada de
  teste de paridade que cubra o caso nominal e os edge cases de `RISK-002`
  (vazio/NaN/data nula).
- Uma métrica implementada como *proxy* MUST ser identificada como tal na documentação e na
  spec da feature até ser substituída pela regra oficial.
- Divergência de cálculo não explicada é critério de no-go para qualquer publicação.

**Rationale**: o painel informa decisões institucionais e prestação de contas; um número
errado é pior que nenhum número.

### II. Domínio Puro e Camadas Separadas

- `app/domain/` MUST conter apenas funções puras: sem I/O, sem banco, sem Dash/Flask, sem
  variáveis de ambiente. Só pode importar a biblioteca padrão, `pandas` e outros módulos de
  `app/domain/`.
- Ingestão, validação, correção e persistência ficam em `app/data/`; integração com o Sistec
  em `app/sistec/`; UI em `app/pages/` (uma página por arquivo) e `app/components/`.
- Dependências apontam para dentro: `pages`/`components` → `domain`/`data`; `domain` nunca
  depende das demais camadas.

**Rationale**: regras de negócio puras são testáveis isoladamente, o que torna a paridade
(Princípio I) verificável.

### III. Privacidade: Nenhum Dado Pessoal Persistido (INEGOCIÁVEL)

- O schema do banco MUST NOT conter colunas de dados pessoais de estudantes (nome, CPF,
  e-mail, data de nascimento ou equivalentes) (`RISK-008`).
- Colunas pessoais presentes nos CSVs do Sistec MUST ser descartadas na ingestão, antes de
  qualquer escrita em disco ou banco; arquivos brutos baixados MUST ser apagados após a leitura.
- Credenciais gov.br do usuário MUST NOT ser solicitadas, armazenadas ou registradas em log.
- `scripts/verificar_prontidao_cutover.py` MUST continuar verificando ausência de PII; nova
  tabela ou coluna exige atualização dessa verificação quando aplicável.

**Rationale**: o sistema trata dados educacionais sujeitos à LGPD e só precisa de agregados.

### IV. Testes Automatizados como Gate

- Mudança de comportamento em `app/domain/`, `app/data/` ou `app/sistec/` MUST incluir ou
  atualizar testes `pytest` em `tests/`.
- A suíte completa (`pytest`) MUST passar antes de commit em branch compartilhada e antes de
  qualquer publicação.
- Correção de bug MUST começar por um teste que reproduz a falha.
- Integração com o Sistec MUST ser testável sem o Sistec real, via
  `scripts/sistec_simulado.py` ou fixtures.

**Rationale**: não há Parallel Run antes do cutover; testes são a principal defesa contra
regressão.

### V. Configuração no Lugar de Código Fixo

- Identidade institucional (nome, sigla, site, contato, logotipo) e a lista de campi com seus
  identificadores de perfil MUST ser configuração, nunca literais no código.
- Regras nacionais (ano-base, fatores FEC/FECH) ficam em dados versionados (`app/data/padroes/`,
  tabela `fatores`) e MUST sobreviver a um reset de instalação.
- Segredos e parâmetros de ambiente (`ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`, `CALCSISTEC_*`)
  MUST vir de variáveis de ambiente; `.env` MUST NOT ser versionado.

**Rationale**: o CalcSISTEC deve poder ser instalado em outra instituição da Rede Federal sem
alteração de código.

### VI. Acesso ao Sistec pela Sessão do Usuário

- A coleta de dados MUST usar o navegador habitual do usuário, com o login gov.br feito por
  ele; automação de navegador (Playwright, CDP, Selenium ou similares) MUST NOT ser
  reintroduzida.
- A atualização MUST NOT iniciar com campus sem identificador de perfil válido, e MUST
  informar quais campi corrigir.
- Todo passo da coleta (abrir URL, aguardar, mover, ler, apagar arquivo) MUST ser visível ao
  usuário com progresso e mensagens de erro acionáveis.

**Rationale**: o gov.br recusa sessões automatizadas (`ERL0000900`); falhas silenciosas geram
planilhas vazias que parecem dados válidos.

### VII. Publicação Versionada e Reversível

- Dados novos MUST passar pelo ciclo interna → prévia conferida → publicada, mantendo a
  versão anterior disponível para restauração.
- O painel público MUST exibir apenas a versão publicada.
- Operações administrativas de dados (atualizar, publicar, restaurar, resetar) MUST ser
  registradas no histórico e exigir autenticação (`RISK-009`).

**Rationale**: uma coleta com problema não pode substituir o dado público sem conferência
humana nem ficar sem caminho de volta.

## Restrições Técnicas e de Segurança

- Stack: Python 3.12, Dash + dash-bootstrap-components, Flask (rotas administrativas), pandas,
  Plotly, SQLite. Nova dependência em `requirements.txt` MUST ser justificada no plano da
  feature.
- Interface MUST seguir o Padrão Digital de Governo (gov.br DS) e ser responsiva, com
  validação no navegador antes do cutover: janela reduzida ou modo de dispositivo do
  DevTools em 320–430 px e em 1280 px ou mais.
- Uploads de imagem MUST passar por validação de imagem e sanitização de SVG
  (`app/data/image_validation.py`, `app/data/svg_sanitize.py`); XML externo MUST ser lido com
  `defusedxml`.
- Produção MUST rodar com um único worker/processo enquanto o registro de execuções for em
  memória (P-09), e com `CALCSISTEC_HTTPS=1` e certificado válido fora de `localhost` (D-19).
- Textos de interface e documentação de usuário são em português do Brasil.

## Fluxo de Desenvolvimento e Gates de Qualidade

- Features seguem `/tlc-spec-driven`: Specify → Design (quando necessário) → Tasks
  (quando necessário) → Execute, com artefatos em `.specs/features/<feature>/`.
- A especificação e o design MUST conferir os Princípios I–VII; qualquer exceção MUST ser
  registrada com justificativa e alternativa mais simples rejeitada.
- `.specs/` é a fonte de regras e decisões do projeto. Os identificadores herdados
  (`BR-*`, `RISK-*`, `D-*`, `P-*`) continuam válidos onde já aparecem, e specs novas MUST
  referenciá-los quando aplicáveis.
- Antes de publicar em produção: `pytest` verde,
  `scripts/verificar_prontidao_cutover.py` com saída 0 e checklist de `DEPLOY.md` atualizado.
- Alterações em `README.md`, `TESTAR.md` ou `DEPLOY.md` MUST acompanhar mudanças de fluxo de
  uso, instalação ou operação.

## Governance

- Esta constituição prevalece sobre outras práticas do projeto. Em conflito com uma spec ou
  plano, a constituição vence até ser formalmente emendada.
- Emendas são feitas neste arquivo, com Sync Impact Report no topo,
  aprovação da responsável pelo projeto (Jaline) e commit dedicado.
- Versionamento semântico: MAJOR para remoção ou redefinição incompatível de princípio; MINOR
  para princípio ou seção nova ou orientação materialmente ampliada; PATCH para esclarecimentos
  e redação.
- Conformidade é verificada durante o design, na validação independente de
  `/tlc-spec-driven` e em revisão de código; complexidade adicional MUST ser
  justificada por escrito.
- Orientação operacional do dia a dia fica em `README.md`, `TESTAR.md` e `DEPLOY.md`.

**Version**: 1.3.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-24
