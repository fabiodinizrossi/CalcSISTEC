# Implantação — CalcSISTEC

Como instalar, subir e publicar o painel. Para o ambiente de teste local, veja
`TESTAR.md`; para instalar em outra instituição, veja a seção correspondente do
`README.md`.

## Pré-requisitos

- Python 3.12 (mesma versão de `.python-version`).
- Dependências com versão fixa:

  ```bash
  pip install -r requirements.txt
  ```

- Um `.env` na raiz, criado a partir de `.env.example`. As oito chaves estão
  descritas no próprio exemplo; sem `ADMIN_EMAIL` e `ADMIN_PASSWORD_HASH` o
  login administrativo não funciona, e sem `FLASK_SECRET_KEY` as sessões caem a
  cada reinício.

## Subir o painel

```bash
python run.py                              # host 0.0.0.0, porta 8050
python run.py --host 127.0.0.1 --port 9000 # outra interface e outra porta
```

O `run.py` inicia o watchdog das execuções antes de servir o painel: é ele que
encerra uma execução pausada há mais de 4 h e marca como falho o par de campus
parado além do limite. Subir o app por outro caminho (importando `app.app`
direto) deixa o watchdog desligado.

**Um único worker/processo.** O registro das execuções e das capturas vive em
memória, compartilhado por todas as requisições; com dois processos, o
navegador conversa com um deles e o estado aparece quebrado no outro. Não use
`--workers`/`gunicorn -w` nem réplicas atrás do balanceador enquanto o registro
for em memória.

## HTTPS

Fora de `localhost`, rode com `CALCSISTEC_HTTPS=1` e certificado válido:

- com `CALCSISTEC_HTTPS=1`, `app/config.py` liga `SESSION_COOKIE_SECURE`, e o
  cookie de sessão só trafega cifrado;
- as rotas `/api/sistec/*` recusam HTTP sem cifra fora de `localhost` — é
  falha segura: sem HTTPS, elas não entregam dado nenhum.

Em `localhost` (desenvolvimento e ambiente de teste) o HTTP puro continua
funcionando, como em `scripts/testar.ps1`.

## Checklist antes de publicar

- [ ] `python -m pytest -q` verde (0 falhas).
- [ ] `python scripts/verificar_prontidao_cutover.py` com saída 0 (GO).
- [ ] `.env` preenchido, com `FLASK_SECRET_KEY` e `ADMIN_PASSWORD_HASH` próprios
      da instalação — não os do exemplo.
- [ ] `CALCSISTEC_HTTPS=1` e certificado válido fora de `localhost`.
- [ ] Um único worker/processo.
- [ ] Banco publicado presente e `ANO_BASE` conferido.
- [ ] Validação em celular real concluída (pendência DS-42, abaixo).

## Verificação automatizada de prontidão

```bash
python scripts/verificar_prontidao_cutover.py
```

Cobre: ausência de PII no schema (`RISK-008`), autenticação administrativa
configurada (`RISK-009`), schema v2 aplicado, tabela de fatores carregada,
`CALCSISTEC_HTTPS=1` configurado (D-19), dataset publicado presente e ano-base
configurado. **Não cobre** a paridade numérica contra o Power BI, o worker único
nem os passos humanos abaixo — o script termina com `NO-GO` enquanto uma baixa
real de teste não for publicada, mesmo com os critérios técnicos OK.

## Pendências abertas

### 1. Validação em celular real (DS-42)

Passo humano: o código foi verificado no Chrome, mas o teste em aparelho real
ainda não foi feito.

Roteiro, em um celular real (**largura de 320 px a 430 px**) e depois em uma
tela de **1280 px ou mais**:

1. Abrir as 4 páginas públicas (`/`, `/eficiencia`, `/evasao`,
   `/percentuais-legais`) e confirmar que a rota legada `/matriculas` redireciona
   para `/`. Conferir: a página não rola para o lado (só as tabelas rolam dentro
   do próprio quadro), o menu abre pelo botão do cabeçalho, os cartões e filtros
   ficam em coluna única e nada fica cortado. Em `/`, conferir também o dashboard
   de Matrículas: KPIs em grade, filtros na largura do card, título em até duas
   linhas a 390 px e tabela rolando dentro do quadro.
2. Entrar em `/admin/login` e abrir `/admin/atualizar`. Conferir: os botões ficam
   empilhados e a tela cabe na largura.
3. Trocar para o tema escuro pelo botão do cabeçalho, em uma página pública e em
   `/admin/atualizar`: todo texto continua legível e a escolha fica salva ao
   recarregar.
4. Anotar o resultado **neste arquivo**. Enquanto estiver em branco, o item de
   design fica desmarcado no checklist acima.

Resultado: dispositivo ______ · largura ______ px · data ______

### 2. CSRF nas rotas administrativas

Os `POST` administrativos não têm token CSRF. Hoje só o `SameSite=Lax` do cookie
de sessão (`app/config.py`) protege. Adicionar o token antes de expor a área
administrativa além da rede da instituição.

### 3. Divergências conhecidas, para decisão humana

Levantadas na validação de paridade e ainda não resolvidas. Não bloqueiam o uso
do painel, mas precisam de decisão antes de o sistema virar canal oficial:

1. **Exemplo numérico de `BR-MIGRAR-007`**: o texto da regra diz "CH=200,
   FEC=1.10, Mat=30 → 9,075", mas a fórmula da própria regra calcula 8,25 — que
   é o valor que a suíte valida. Se o certo for 9,075, a fórmula documentada é
   que está incompleta.
2. **Nomes das colunas cruas do upload**: ainda são convenção provisória
   (`STATUS_MATRICULA_SISTEC`, `CÓDIGO DO PORTFÓLIO`, `OFERTA` etc.), nunca
   confirmada contra uma extração real do Sistec/PNP. Confirmar no primeiro
   upload de teste.
3. **`mapa_nomes_curso`** (`BR-MIGRAR-017`): ainda vazio — a tabela real de
   cerca de 40 mapeamentos históricos não foi fornecida.
4. **`AGG-IndicadoresRegulatorios.aviso_filtro_proeja`** (`BR-MIGRAR-026`,
   página Percentuais Legais): hoje é uma mensagem estática, não a lógica real de
   detecção de distorção.
5. **Botão de retorno à capa** (`BR-HUMANA-007`): cumprido pelo link "Início" da
   navegação lateral, não por um elemento dedicado.
6. **Tokens gov.br**: as cores e a tipografia ainda usam os valores não
   confirmados contra a documentação oficial do design system
   (`app/static/govbr-ds/dist/core-tokens.css`).

## Publicação e rollback

1. Conferir o checklist acima e publicar a versão conferida (o painel público só
   exibe a versão publicada).
2. Monitorar o primeiro ciclo de coleta real após a publicação, com a
   administradora validando o resultado.
3. Repetir a validação de paridade no primeiro ciclo pós-publicação.
4. Manter o painel legado (Power BI) acessível até o ciclo de monitoramento ser
   aprovado; desativá-lo só depois disso, nunca no mesmo dia da publicação.

**Rollback**: republicar o link do painel legado como fonte oficial temporária,
comunicar a volta aos interessados e corrigir o problema no CalcSISTEC. A versão
anterior dos dados continua disponível para restauração pela área
administrativa. Tempo máximo até o rollback: 1 dia útil a partir da detecção do
problema.
