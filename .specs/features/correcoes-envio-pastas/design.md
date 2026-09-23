# Correções do Envio de Pastas Design

**Spec**: `.specs/features/correcoes-envio-pastas/spec.md`
**Status**: Draft

---

## Architecture Overview

Duas correções independentes, ambas no caminho que a feature anterior
(`atualizacao-por-upload`) já tinha construído. Nenhuma abre fluxo novo.

**No navegador.** O bloco de envio troca o `.br-upload` do pacote por **marcação
própria** com dois controles de pasta. O `input[type=file][webkitdirectory]` continua
sendo o mesmo elemento (mesmo `id`, mesmo `name`), só que escondido atrás de um
`button` nativo — nenhuma API do pacote participa da escolha nem da exibição do
resultado. Quem lê `input.files` e pinta o status é `atualizar.js`, sem rede.

**No servidor.** `ler_planilha` passa a decodificar com `errors="replace"`. É o único
ponto de leitura de CSV do Sistec no projeto: `envio.ler_pastas`
(`app/sistec/envio.py:30`) e `execucoes.receber_bytes`
(`app/sistec/execucoes.py:247`) chegam nele. Corrigir ali cobre as duas origens
(CEP-04 AC 4) sem tocar em nenhum dos dois chamadores.

```mermaid
graph TD
    subgraph navegador [Navegador]
        A[clique em Escolher pasta] --> B[input.click webkitdirectory]
        B -->|evento change| C[contarSelecao: nome + .csv + outros]
        C --> D[renderizarSelecao<br/>só texto, sem rede]
        D --> E[clique em Enviar pastas]
    end
    E --> F[POST /admin/atualizar/envio<br/>multipart ciclos[] + matriculas[]]
    F --> G[envio.ler_pastas]
    G --> H[ler_planilha<br/>encoding_errors=replace]
    H -->|leitura_csv / colunas_ausentes| Z[EnvioInvalido nomeia o arquivo]
    H --> I[aplicar_permissao<br/>RN-17 descarta o resto]
    I --> J[consolidação, prévia, preservação<br/>inalterados]
```

O que **não** muda: a rota de envio, a consolidação, a prévia, Salvar/Descartar,
a publicação e o polling. O `id` de cada `input` é preservado de propósito, para que
`enviarPastas` (`app/static/js/atualizar.js:416`) continue anexando os arquivos
exatamente como antes.

---

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | How to Use |
| --- | --- | --- |
| `arquivosDe(input)` | `app/static/js/atualizar.js:357` | Reusar sem alteração: já devolve `[]` quando `input.files` não existe, o que cobre o Edge Case de navegador sem `webkitdirectory`. |
| `enviarPastas`, `renderizarArquivosEnvio`, `renderizarAvisosEnvio`, `mostrarPreservacao` | `app/static/js/atualizar.js:416,384,398,374` | Reusar inteiros. A única mudança no bloco é a origem da seleção; o multipart e o pós-envio ficam iguais. |
| `escolherOrigem(valor)` | `app/static/js/atualizar.js:365` | Estender um passo: além de limpar `elStatusEnvio`, redesenhar os dois status de seleção. Os arquivos já escolhidos no `input` não são descartados por trocar de origem. |
| `postar`, `celula`, `$` | `app/static/js/atualizar.js:101,109,56` | Reusar. Nenhum `fetch` novo: o widget não faz rede nenhuma (CEP-03). |
| `confirmarAcao` | `app/static/js/confirmar.js:25` | Reusar no diálogo de preservação (inalterado). O widget de pasta **não** usa modal — escolher pasta é uma ação sem consequência. |
| `ler_planilha` | `app/sistec/colunas.py:80` | Alterar em um ponto só; os dois chamadores herdam a decodificação tolerante. |
| `aplicar_permissao` | `app/sistec/colunas.py:66` | Reusar sem alteração. É ele que garante que a coluna do byte inválido não sobreviva à leitura (CEP-04 AC 2). |
| `test_js_envio.py` (harness) | `tests/test_js_envio.py:79` (`_preparar`) | Estender: o dublê já monta o DOM da tela e `input.files`; ganha `webkitRelativePath` nos arquivos falsos. |

### Integration Points

| System | Integration Method |
| --- | --- |
| gov.br DS (AD-002, AD-003) | Só os **tokens** de cor: `--interactive`, `--focus-color`, `--gray-*`, como já em `app/assets/style.css:632-633`. O componente `.br-upload` e o `initInstanceUpload()` de `app/static/govbr-ds/dist/core-init.min.js` ficam fora do caminho — a regra `.br-upload input{display:none}` (`core.min.css`, linha 1) é justamente a causa do defeito. |
| Shell e carga de script (AD-001, AD-004) | Sem mudança: `app/templates/atualizar.html:157` continua carregando `/ds/js/atualizar.js`; o widget é um `button` nativo e não depende de `initInstanceAll`. |
| Leitura compartilhada (`envio` ↔ `execucoes`) | Sem mudança de assinatura: `ler_planilha(conteudo_bytes, tipo)` segue com os mesmos parâmetros e os mesmos dois `ValueError` (`leitura_csv`, `colunas_ausentes`). |
| Testes do envio | `pytest tests/` continua sendo o portão (a coleta na raiz segue inválida, ver `STATE.md` Handoff). |

---

## Components

### `campoDePasta` — widget de escolha de pasta

- **Purpose**: dar um controle visível para escolher uma pasta e mostrar, sem rede, o nome dela e o que foi escolhido.
- **Location**: marcação em `app/templates/atualizar.html` (substitui o bloco `#bloco-envio` → `<div class="br-upload">`, linhas 70-81); comportamento em `app/static/js/atualizar.js`; aparência em `app/assets/style.css`.
- **Markup** (por pasta, dois blocos; só os `id` mudam):

  ```html
  <div class="campo-pasta mr-lg-3 mb-3 mb-lg-0">
    <input type="file" id="envio-ciclos" name="ciclos" webkitdirectory multiple accept=".csv" hidden>
    <button type="button" class="br-button secondary" id="btn-escolher-ciclos"
            aria-describedby="envio-ciclos-status">Escolher pasta de ciclos</button>
    <p class="campo-pasta-status" id="envio-ciclos-status" role="status" aria-live="polite"></p>
  </div>
  ```

  O `input` guarda os `id`/`name` atuais (`envio-ciclos`, `envio-matriculas`) — o multipart de `enviarPastas` não muda. Ele fica `hidden` porque um `input[type=file]` cru é o que o usuário não enxerga hoje; quem recebe o clique é o `button`, que é focável, tem nome acessível e não depende de JS do DS para aparecer.
- **Interfaces** (JS, dentro do mesmo IIFE de `atualizar.js`):
  - `CAMPOS_PASTA` — lista de `{ input, status, rotulo }`, uma entrada por pasta, montada pelos `id` já existentes.
  - `contarSelecao(arquivos) -> { nome, csv, outros }` — função pura. `nome` é `arquivos[0].webkitRelativePath.split("/")[0]`; se o caminho vier vazio (navegador sem `webkitdirectory`), devolve `null`. `csv` conta `name` terminando em `.csv` (case-insensitive), `outros` conta o resto.
  - `renderizarSelecao(campo)` — escreve o texto de status de uma pasta: nome da pasta + contagem de `.csv` + contagem de não-`.csv` quando houver (CEP-02). Sobrescreve, nunca acumula (Edge Case de reescolha).
  - `selecaoDePasta(evento)` — manipulador de `change` dos dois `input`; chama `renderizarSelecao` do campo correspondente.
- **Dependencies**: nada além do DOM. Nenhum `fetch`, nenhum `setTimeout`, nenhum `classList` de estado "carregando" — é o que garante CEP-03 (nenhuma animação de envio antes do clique real).
- **Reuses**: `$` e `arquivosDe` de `atualizar.js`; classes `br-button secondary` e utilitários de espaçamento do DS para o botão, como o resto da tela.

### `style.css` — regra visual do widget

- **Purpose**: dar ao bloco a mesma aparência de campo de formulário que o DS daria, sem carregar o componente do DS.
- **Location**: `app/assets/style.css` (bloco novo, junto das regras administrativas).
- **Interfaces**: `.campo-pasta`, `.campo-pasta-status`. Só tokens do DS (`var(--interactive)`, `var(--focus-color)`, `var(--gray-40)`, `var(--background)`) — nenhuma cor hexadecimal literal, conforme AD-003.
- **Dependencies**: `core-tokens.css` já carregado pelo shell.
- **Reuses**: o padrão de `app/assets/style.css:632-634` (borda/foco por token) e a classe `br-button` do DS para o botão.

### `ler_planilha` — alteração pontual

- **Purpose**: ler um CSV do Sistec sem abortar por um byte que não existe em `cp1252`.
- **Location**: `app/sistec/colunas.py:80-102`.
- **Interfaces** (assinatura inalterada):
  - `ler_planilha(conteudo_bytes, tipo) -> pd.DataFrame` — as duas chamadas a `pd.read_csv` (cabeçalho em `:88`, conteúdo em `:96-98`) ganham `encoding_errors="replace"`. O `try/except` que converte em `ValueError("leitura_csv")` (`:89-90`, `:99-100`) e a checagem de colunas obrigatórias (`:92-93`) ficam como estão.
  - Os erros estruturais continuam intactos: falha de tokenização por número de campos diferente segue virando `leitura_csv`, e cabeçalho sem coluna obrigatória segue virando `colunas_ausentes` (CEP-05).
- **Dependencies**: `pandas >= 1.3` (parâmetro `encoding_errors` em `read_csv`). Instalado aqui: **2.3.0**, confirmado nesta sessão. `requirements.txt:3` lista `pandas` sem versão mínima.
- **Reuses**: `io.BytesIO`, o `dtype=str`, o `sep=";"`, o `encoding="cp1252"` e o mapa de permissão — nada mais muda.

---

## Data Models

Sem persistência nova e sem mudança de schema. Um tipo em memória, só para o widget:

```js
// Resultado de contarSelecao(arquivos), usado apenas dentro de atualizar.js.
SelecaoPasta = {
  nome: string | null,   // primeiro segmento de webkitRelativePath; null se o navegador não informa
  csv: number,           // arquivos cujo nome termina em .csv
  outros: number         // o resto; contado agora, listado só depois do envio (UPL-04)
}
```

Nada deste objeto vai ao servidor: o multipart continua sendo montado a partir de
`input.files` (`app/static/js/atualizar.js:426-427`), e a lista de ignorados que o
usuário lê continua vindo da resposta do servidor (`renderizarAvisosEnvio`), não da
contagem local. As duas contagens podem divergir e a do servidor é a que vale — a
local existe só para dar retorno imediato ao escolher a pasta.

---

## Error Handling Strategy

| Error Scenario | Handling | User Impact |
| --- | --- | --- |
| Botão "Escolher pasta" clicado duas vezes / pasta reescolhida | `renderizarSelecao` escreve no mesmo nó de status (substitui, não acrescenta) | O texto passa a descrever a pasta nova; nada da anterior fica visível |
| `webkitRelativePath` vazio (navegador sem `webkitdirectory`) | `contarSelecao` devolve `nome = null`; o status mostra só a contagem | "3 arquivo(s) .csv escolhido(s)." — sem nome de pasta e sem erro |
| Seleção com arquivos que não são `.csv` | `contarSelecao` separa `outros`; o status informa a contagem na mesma linha | "Pasta ciclos: 4 arquivo(s) .csv. 1 arquivo que não é .csv será ignorado."; a lista nominal continua vindo do servidor após o envio (UPL-04) |
| Nenhuma pasta escolhida | Status inicial é o texto de obrigatoriedade, definido na marcação e redesenhado em `escolherOrigem` | "Nenhuma pasta de ciclos escolhida — obrigatória."; o `enviarPastas` já recusa com "As duas pastas são obrigatórias…" |
| Pasta escolhida sem nenhum `.csv` | O widget mostra `0`; a recusa real continua no servidor (`EnvioInvalido("pasta_vazia")`, `app/sistec/envio.py:25`) | "A pasta de ciclos não tem nenhum arquivo .csv." — mesma mensagem de hoje, nada gravado |
| Byte sem mapeamento em `cp1252` em coluna **descartada** (CEP-04) | `encoding_errors="replace"` na leitura; o byte vira `�` e `aplicar_permissao` descarta a coluna inteira | O arquivo é lido normalmente; o envio chega à prévia |
| Byte inválido em posição adjacente a um `;` | A substituição produz **um** caractere, não um delimitador; a contagem de campos da linha não muda. Se a linha já tinha número de campos diferente, `pandas` levanta `ParserError`, capturado em `:99-100` | Linha estruturalmente quebrada continua recusada como `leitura_csv` (CEP-05 AC 3) |
| Cabeçalho com byte inválido | O `read_csv` de `nrows=0` (`:88`) também recebe `encoding_errors="replace"` | Arquivo segue legível; coluna obrigatória ausente continua virando `colunas_ausentes` pelo nome, sem exceção de codificação |
| Arquivo com todos os bytes válidos | `errors="replace"` não substitui nada por definição | Texto idêntico ao de hoje; nenhuma coluna de `COLUNAS_CICLO`/`COLUNAS_MATRICULA` muda de valor |
| `pandas` antigo no ambiente (< 1.3) | `read_csv` rejeita o parâmetro `encoding_errors` com `TypeError`, que cai no `except Exception` e viraria `leitura_csv` enganoso | Mitigado por teste (ver Riscos): a suíte passa a exigir `encoding_errors` funcional, não só presente |

---

## Risks & Concerns

| Concern | Location (file:line) | Impact | Mitigation |
| --- | --- | --- | --- |
| `encoding_errors="replace"` silencia corrupção de dado numa coluna **mantida** (`CO_MATRICULA`, `CO_CICLO_MATRICULA`, `NO_STATUS_MATRICULA`, `MES_DE_OCORRENCIA`) | `app/sistec/colunas.py:96-98` | Um código de matrícula com byte inválido entra como `�` sem nenhum aviso na prévia ou no histórico | **Nenhuma — aceito por decisão da spec** (Assumption "Byte inválido dentro de uma coluna que o sistema mantém"). O caso não piora: hoje o arquivo inteiro é recusado, e não há como reconstruir o byte original de um export defeituoso. Não acrescentar heurística nem aviso sem novo pedido da usuária. |
| `pandas` sem versão mínima em `requirements.txt` | `requirements.txt:3` | `encoding_errors` exige pandas >= 1.3; num ambiente antigo o `TypeError` viraria `leitura_csv` e a correção pareceria não funcionar | Fixar a versão mínima em `requirements.txt` (`pandas>=1.3`) e cobrir com teste que envia o CSV sintético com o byte `0x81` — o teste falha alto no ambiente errado em vez de degradar em silêncio |
| Remover `.br-upload` da marcação pode levar junto espaçamento e borda que vinham do pacote | `app/templates/atualizar.html:70-81` → `app/assets/style.css` | Bloco de envio fica visualmente solto ou sem foco visível | Regra `.campo-pasta` nova só com tokens do DS (AD-003) e `:focus-visible` com `var(--focus-color)`, como `app/assets/style.css:633`. Conferir no navegador antes de fechar a tarefa |
| O DOM simulado dos testes não tem `click()` nem `files` por padrão | `tests/dom_falso.py:23-45` | O widget chama `input.click()`; sem isso a suíte de `atualizar.js` quebra com `TypeError`, não por defeito do widget | Acrescentar `click()` ao elemento simulado (1 linha, guardando a contagem) e `webkitRelativePath` nos arquivos falsos de `_preparar` (`tests/test_js_envio.py:108-109`). É mudança de dublê, não de asserção |
| O widget evita `parentElement`/`closest`/`querySelector` | `tests/dom_falso.py:23-45` | Qualquer uma dessas APIs deixaria o teste impossível sem reescrever o dublê | Referenciar os nós por `id` com `$()`, como o resto de `atualizar.js:56`; a lista `CAMPOS_PASTA` liga `input` a `status` explicitamente |
| `accept=".csv"` é ignorado em seleção de pasta na maioria dos navegadores | `app/templates/atualizar.html:73,78` | Arquivos que não são `.csv` chegam ao multipart e são descartados no servidor | Comportamento já existente e coberto por UPL-04; o widget só conta (`outros`) e o servidor continua sendo a autoridade da lista de ignorados |
| `.br-upload input{display:none}` continua no pacote e vale para qualquer marcação futura que reuse a classe | `app/static/govbr-ds/dist/core.min.css` (linha 1) | Um `input` futuro dentro de `.br-upload` some de novo | A marcação nova não usa mais a classe `.br-upload`; o widget é a referência para as próximas telas com pasta |

---

## Tech Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Componente de escolha de pasta | Widget próprio em `atualizar.js` + marcação nova, com `button` nativo sobre o `input` escondido | O pacote vendorizado não traz CSS nem JS próprios em `components/upload/`, e o núcleo exige `input.upload-input` + `.upload-list` dentro de `.br-upload` — que a tela não usava, por isso nada aparecia. Corrigir a marcação não bastaria: o `initInstanceUpload()` embutido dispara "Carregando…" de 0,5 s por arquivo assim que a pasta é escolhida, antes de qualquer envio real (CEP-03 proíbe). Decidido com a usuária. |
| Aparência do widget | Tokens do DS em `app/assets/style.css`, sem reusar o `.br-upload` | Mantém uma só fonte de cor e um só par claro/escuro (AD-003) sem reintroduzir o componente defeituoso. |
| Decodificação tolerante | `encoding_errors="replace"` nos dois `pd.read_csv` de `ler_planilha` | O defeito é um byte pontual do export, não uma troca de codificação do arquivo. `replace` deixa a leitura terminar e troca só o byte inválido por `�`; o caminho estrutural (`leitura_csv`/`colunas_ausentes`) não muda. Corrige envio e baixa de uma vez, porque os dois passam por `ler_planilha`. |
| Onde aplicar a correção | Em `ler_planilha`, não em `envio.py` | É o ponto único de leitura do Sistec; duplicar em `envio` recriaria a divergência que a extração da feature anterior eliminou. |

> Nenhuma decisão aqui estabelece convenção nova para features futuras: a regra de cor já é AD-003, e a leitura tolerante é propriedade de uma função que já é o ponto único de leitura. Nada a acrescentar em `.specs/STATE.md`.
