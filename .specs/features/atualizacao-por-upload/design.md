# Atualização por Upload de Pastas Design

**Spec**: `.specs/features/atualizacao-por-upload/spec.md`
**Status**: Draft

---

## Architecture Overview

O envio entra como uma **segunda origem da mesma execução**, não como um fluxo paralelo. A máquina de estados de `app/sistec/execucoes.py`, a prévia, o Salvar/Descartar, a publicação e o polling de `/admin/atualizar/execucao` ficam intactos; muda só quem preenche a fila e de onde vêm os bytes.

Na baixa, cada `Par` da fila é um campus × tipo, alimentado pela extensão/navegador. No envio, cada `Par` é **um arquivo enviado**, alimentado pela própria requisição. A partir de `_consolidar_ou_falhar` os dois caminhos são o mesmo código.

```mermaid
graph TD
    A[POST /admin/atualizar/envio<br/>multipart: ciclos[] + matriculas[]] --> B[envio.ler_pastas]
    B -->|EnvioInvalido| Z[falhou: nomeia arquivo + motivo<br/>nada gravado]
    B --> C[execucoes.criar_execucao_envio<br/>um Par por arquivo]
    C --> D[execucoes._consolidar_ou_falhar]
    D --> E[consolidacao.consolidar]
    E --> F[envio.campi_ausentes<br/>cadastrados - presentes]
    F --> G[estado previa]
    G --> H[POST .../salvar<br/>confirmar_preservacao]
    H --> I[ingest.montar_versao_interna<br/>campi_falhos = ausentes]
    I --> J[versoes.salvar_interna]
```

Processamento **síncrono** na requisição: a resposta já traz o desfecho por arquivo. O polling existente continua atendendo a prévia e os botões.

---

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | How to Use |
| --- | --- | --- |
| `aplicar_permissao` | `app/sistec/colunas.py:62` | Importar. Descarta PII e renomeia para os nomes internos, idêntico à baixa (UPL-03). |
| `COLUNAS_CICLO` / `COLUNAS_MATRICULA` | `app/sistec/colunas.py:20,38` | Referência para a validação de estrutura por arquivo (UPL-10). |
| Leitura `;` + `cp1252` | `app/sistec/execucoes.py:202` (`receber_bytes`) | Extrair o miolo para uma função compartilhada; hoje está embutido no fluxo da extensão. |
| `Execucao` / `Par` / `ESTADOS_TERMINAIS` | `app/sistec/execucoes.py:45,60` | Reusar. Um `Par` por arquivo, com `nome_perfil` = nome do arquivo. |
| `_consolidar_ou_falhar`, `salvar`, `descartar`, `cancelar` | `app/sistec/execucoes.py:273-307` | Reusar sem alteração, exceto o portão de confirmação em `salvar`. |
| `consolidar` | `app/sistec/consolidacao.py:86` | Reusar sem alteração. |
| `montar_versao_interna` | `app/data/ingest.py:175` | Reusar. `campi_falhos` recebe os campi **ausentes** — mesma semântica de preservação (RN-22). |
| `listar_campi` | `app/data/campi.py` | Fonte dos campi cadastrados para calcular os ausentes (UPL-07). |
| `historico.iniciar` / `encerrar` | `app/data/historico.py:45,62` | Reusar, com um tipo novo `envio`. |
| Rotas `/salvar`, `/descartar`, `/cancelar`, `/execucao` | `app/app.py:381-459` | Atendem o envio sem duplicação; `/execucao` ganha campos novos. |
| Polling + prévia da tela | `app/static/js/atualizar.js:197` | Reusar. Ganha o seletor de origem e o envio. |
| `confirmarAcao` | `app/static/js/confirmar.js` | Reusar no diálogo de preservação. |

### Integration Points

| System | Integration Method |
| --- | --- |
| Registro em memória de execuções | Mesmo `_REGISTRO` por `admin_email`; baixa e envio se excluem por RN-11 (UPL-13). |
| SQLite (`interna_*`) | Só por `montar_versao_interna` → `salvar_interna`. Sem mudança de schema. |
| `historico` | Uma linha por envio, tipo novo. Sem mudança de schema (`tipo` é texto). |

---

## Components

### `envio` (novo)

- **Purpose**: transformar os arquivos de duas pastas enviadas em DataFrames válidos, ou recusar o envio inteiro nomeando o arquivo culpado.
- **Location**: `app/sistec/envio.py`
- **Interfaces**:
  - `class EnvioInvalido(Exception)` — carrega `arquivo` e `motivo` (`colunas_ausentes` | `leitura_csv` | `pasta_vazia`). Nunca carrega conteúdo de célula (UPL-12).
  - `ler_pastas(arquivos_ciclo, arquivos_matricula) -> dict` — recebe duas sequências de `FileStorage`; devolve `{"ciclo": [(nome, df)], "matricula": [(nome, df)], "ignorados": [nome]}`. Levanta `EnvioInvalido` no primeiro arquivo reprovado.
  - `nome_seguro(nome) -> str` — descarta componente de diretório do nome vindo do navegador (Edge Case de separadores).
  - `campi_ausentes(df_ciclos, campi_cadastrados) -> list[str]` — `co_unidade` cadastrados sem nenhuma linha consolidada.
  - `campi_nao_cadastrados(df_ciclos, campi_cadastrados) -> list[str]` — o inverso (UPL-09).
- **Dependencies**: `pandas`, `app/sistec/colunas`.
- **Reuses**: `aplicar_permissao`, os dois mapas de colunas, e a leitura `;`/`cp1252` extraída de `receber_bytes`.

### `execucoes` (alteração pontual)

- **Purpose**: aceitar uma execução cuja fila vem de arquivos e exigir confirmação antes de gravar com campi preservados.
- **Location**: `app/sistec/execucoes.py`
- **Interfaces**:
  - `criar_execucao_envio(admin_email, nomes_ciclo, nomes_matricula, historico_id=None, relogio=None) -> Execucao` — mesma trava RN-11 de `criar_execucao`; monta um `Par` por arquivo (`id_perfil=None`, `nome_perfil=nome do arquivo`); `estado` inicial `consolidando`; define `origem="envio"`.
  - `registrar_leitura(execucao, leitura)` — preenche `par.df`, `linhas` e `status="baixado"` a partir do resultado de `ler_pastas`.
  - `definir_campi_preservados(execucao, codigos)` — grava em `campi_falhos`, que `salvar` já repassa a `montar_versao_interna`.
  - `salvar(execucao, db_path, ano_base, confirmado=False)` — WHERE `origem == "envio"` e `campi_falhos` não vazio, levanta `ConfirmacaoNecessaria` se `confirmado` for falso (UPL-08).
  - `Execucao.origem` — `"baixa"` (padrão, retrocompatível) | `"envio"`.
- **Dependencies**: as atuais.
- **Reuses**: todo o resto do módulo.

### Rota de envio (`app/app.py`)

- **Purpose**: receber o multipart, orquestrar leitura → consolidação → prévia, e registrar o histórico.
- **Location**: `app/app.py`
- **Interfaces**:
  - `POST /admin/atualizar/envio` (`@requer_autenticacao`) — campos `ciclos` e `matriculas` (múltiplos arquivos). `409` com `execucao_em_andamento` / `previa_pendente`; `400` com `{arquivo, motivo}` em `EnvioInvalido`; `413` acima do limite; `200` com o resumo por arquivo.
  - `POST /admin/atualizar/execucoes/<id>/salvar` — passa a aceitar `{"confirmar_preservacao": true}`; responde `409` `confirmacao_necessaria` sem ele.
  - `GET /admin/atualizar/execucao` — ganha `origem`, `campi_preservados`, `campi_nao_cadastrados`, `arquivos_ignorados`, `matriculas_orfas`.
- **Dependencies**: `envio`, `execucoes`, `historico`, `listar_campi`.
- **Reuses**: `_execucao_da_sessao`, `_ano_base_config`, `historico_iniciar`/`historico_encerrar`.

### Tela e script

- **Purpose**: oferecer as duas origens e conduzir o envio.
- **Location**: `app/templates/atualizar.html`, `app/static/js/atualizar.js`
- **Interfaces**: bloco de escolha de origem (dois `br-radio` do DS); `<input type="file" webkitdirectory multiple>` para ciclos e outro para matrículas; botão Enviar; área de resultado por arquivo; caixa de confirmação de preservação antes de habilitar Salvar.
- **Dependencies**: `confirmar.js`, gov.br DS já carregado pelo shell (AD-001, AD-002).
- **Reuses**: polling, tabela de prévia, botões Salvar/Descartar/Publicar existentes.

### `historico` (alteração de uma linha)

Acrescentar `"envio"` a `TIPOS_VALIDOS` (`app/data/historico.py:16`). Os desfechos necessários já existem.

---

## Data Models

Sem mudança de schema. Só um atributo novo em memória:

```python
class Execucao:
    origem: str          # "baixa" | "envio"
    campi_falhos: set     # na baixa, campi com par falho; no envio, campi ausentes
```

`montar_versao_interna` já trata `campi_falhos` como "campi cujos dados atuais devem ser preservados", que é exatamente a regra do envio — nenhuma alteração em `app/data/ingest.py`.

---

## Error Handling Strategy

| Error Scenario | Handling | User Impact |
| --- | --- | --- |
| Pasta sem nenhum `.csv` | `EnvioInvalido("pasta_vazia")` antes de ler qualquer arquivo | "A pasta de ciclos não tem nenhum arquivo .csv." Nada gravado. |
| Arquivo sem coluna obrigatória | `EnvioInvalido("colunas_ausentes", arquivo)` | Nomeia o arquivo e sugere retirá-lo da pasta para preservar aquele campus. Nada gravado. |
| Arquivo ilegível em `;`/`cp1252` | `EnvioInvalido("leitura_csv", arquivo)` | Mesma mensagem, motivo diferente. Nada gravado. |
| Pastas invertidas | Cai em `colunas_ausentes` no primeiro arquivo | Mensagem nomeia o arquivo; a tela sugere conferir qual pasta foi em qual campo. |
| `ConsolidacaoInvalida` | Estado `falhou_consolidacao`, mensagem exposta em `erro_consolidacao` | Texto já existente, só com códigos institucionais. Nada gravado. |
| Ciclos vazios após filtro | `ConsolidacaoInvalida("nenhum par de ciclo consolidado")` | Idem. |
| Envio acima de 500 MB | `413` do Werkzeug | "O envio passa de 500 MB." |
| Baixa ou envio já em andamento | `409` `execucao_em_andamento` / `previa_pendente` | Reusa as mensagens já existentes em `atualizar.js`. |
| Salvar com campi preservados sem confirmar | `409` `confirmacao_necessaria` | O portão é do servidor, não só do JS; a tela mostra a lista e pede a confirmação. |

---

## Risks & Concerns

| Concern | Location (file:line) | Impact | Mitigation |
| --- | --- | --- | --- |
| `campi_falhos` passa a significar duas coisas (par falho na baixa, campus ausente no envio) | `app/sistec/execucoes.py:83`, `app/data/ingest.py:175` | Leitura futura pode concluir que houve falha onde só houve ausência | Manter o nome interno (a semântica de preservação é idêntica) e expor ao cliente como `campi_preservados`; documentar no docstring de `criar_execucao_envio`. |
| Werkzeug grava upload grande em arquivo temporário | Parser de formulário do Flask | Bytes com PII tocam o disco durante a requisição | Aceito por decisão registrada na spec: nada sobrevive à requisição, e `aplicar_permissao` descarta PII antes de qualquer escrita em banco. Teste de validação deve conferir que o diretório temporário fica limpo após a resposta. |
| POST administrativos sem token CSRF | Pré-existente, registrado em `CUTOVER.md` | O envio acrescenta mais uma rota mutadora sem proteção | Fora do escopo desta feature; a rota nova segue o mesmo `@requer_autenticacao` das demais. Não ampliar o débito nem fingir que foi resolvido. |
| Leitura `;`/`cp1252` duplicada entre `receber_bytes` e o envio | `app/sistec/execucoes.py:211-231` | Divergência silenciosa se um dos dois mudar | Extrair para uma função em `app/sistec/colunas.py` ou `envio.py` e fazer `receber_bytes` chamá-la, com o teste de baixa existente protegendo a extração. |
| `_deduplicar_por_chave` compara linha a linha dentro de cada grupo duplicado | `app/sistec/consolidacao.py:71` | Envio com muita chave repetida fica lento | Sem mudança nesta feature; o caso normal (uma linha por ciclo por campus) não entra no laço. Medir só se aparecer. |
| `atualizar.js` cresce com um segundo fluxo | `app/static/js/atualizar.js` | Arquivo de 297 linhas vira difícil de seguir | Isolar o envio numa função por responsabilidade no mesmo arquivo; cobrir com teste no padrão de `tests/test_js_*.py`. |
| Princípio VI proíbe automação de navegador, mas `app/sistec/navegador.py` usa driver | `app/sistec/navegador.py` | Divergência pré-existente entre princípio e código | Fora do escopo. Esta feature reduz a dependência desse caminho, não a amplia. |

---

## Tech Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Onde encaixar o envio | Segunda origem da mesma `Execucao` | Reusa máquina de estados, prévia, Salvar, publicação e polling. Um módulo paralelo duplicaria tudo isso e divergiria com o tempo. |
| Granularidade do `Par` | Um por arquivo enviado | A fila já existe e é renderizada pela tela; arquivo é a unidade que a usuária reconhece e a única que a mensagem de erro pode nomear com certeza. |
| Processamento | Síncrono na requisição | Poucos segundos para o volume real; thread de fundo exigiria copiar até 500 MB para a memória sem ganho perceptível. |
| Portão de confirmação | No servidor, em `salvar` | Um portão só no JS não é verificável por teste de backend nem resiste a uma requisição direta. |
| Semântica de campus ausente | Reusar `campi_falhos` / RN-22 | O código de preservação já existe, é testado e faz exatamente o que a decisão da usuária pede. |

> Nenhuma decisão aqui estabelece convenção nova para features futuras. Nada a acrescentar em `.specs/STATE.md`.
