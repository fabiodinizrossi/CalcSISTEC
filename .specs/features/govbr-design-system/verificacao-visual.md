# Verificação visual e de teclado (T55)

**Resultado: PASS.** As 14 telas cabem em 320, 576, 992, 1280 e 1600px sem rolagem lateral, o menu fica
persistente a partir de 992px, o teclado e o modal cumprem a spec, e o tema escuro é legível. A verificação
achou três lacunas de código e as três foram corrigidas com teste (seção "Lacunas").

Como foi feito: Chrome (claude-in-chrome) sobre o app local (`python -m app.app`) com dados simulados
(4 campi, 96 matrículas, 13 campi cadastrados e 1 identificador inválido) num banco copiado antes e
restaurado depois. Cada tela foi carregada num `<iframe>` do tamanho da largura testada (a janela do Chrome
não muda de tamanho pela ferramenta) e medida com `documentElement.scrollWidth <= clientWidth`. A sessão
administrativa foi assinada com a chave de teste, sem digitar senha no navegador.

## Rolagem horizontal: `scrollWidth / clientWidth`

Nas telas com barra de rolagem vertical o `clientWidth` perde 15px; a comparação vale igual.

| Tela | 320 | 576 | 992 | 1280 | 1600 |
| ---- | --- | --- | --- | ---- | ---- |
| `/` | PASS 320/320 | PASS 576/576 | PASS 992/992 | PASS 1280/1280 | PASS 1600/1600 |
| `/matriculas` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/eficiencia` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/evasao` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/percentuais-legais` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/admin/login` | PASS 320/320 | PASS 576/576 | PASS 992/992 | PASS 1280/1280 | PASS 1600/1600 |
| `/recuperar-acesso` | PASS 320/320 | PASS 576/576 | PASS 992/992 | PASS 1280/1280 | PASS 1600/1600 |
| `/admin/instalacao` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/admin/atualizar` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/admin/historico` | PASS 320/320 | PASS 576/576 | PASS 992/992 | PASS 1280/1280 | PASS 1600/1600 |
| `/admin/config` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/admin/campi` | PASS 305/305 | PASS 561/561 | PASS 977/977 | PASS 1265/1265 | PASS 1585/1585 |
| `/admin/campi/<id>/editar` | PASS 320/320 | PASS 576/576 | PASS 992/992 | PASS 1280/1280 | PASS 1600/1600 |
| `/admin/campi/novo` | PASS 320/320 | PASS 576/576 | PASS 992/992 | PASS 1280/1280 | PASS 1600/1600 |

As cinco páginas públicas renderizaram o conteúdo do Dash na medição (KPIs, tabela, filtros).

## Contêiner e menu (DS-03, DS-04, DS-05)

- **Contêiner a 1600px:** `#main-content` mede 1520px (`--grid-tv-maxwidth`) nas 14 telas.
- **Menu abaixo de 992px:** `menu-container` em `display: none` a 576px (sobreposto, abre pelo botão do cabeçalho).
- **Menu persistente a partir de 992px:** `display: block` a 992px e a 1600px. PASS, sem necessidade de cair para menu sobreposto.
- Login, recuperar acesso e instalação não têm menu, como manda a spec.

## Teclado e menu (DS-37, DS-38)

Medido a 576px, com eventos de teclado no botão do cabeçalho.

- **Enter e Espaço abrem o menu e levam o foco ao primeiro item** ("Início"). PASS.
- **`aria-expanded` acompanha o menu** (`true` aberto, `false` fechado). PASS após `menu.js`.
- **Esc fecha e devolve o foco ao botão** (`botao-menu`). PASS após `menu.js`.
- Contorno de foco de 3px pela variável `--focus-color` (regra em `style.css`, coberta por teste; conferido no CSS, não em captura).
- Limite: as teclas reais enviadas pela ferramenta não chegaram ao `iframe`; a conferência usou `KeyboardEvent` no botão e no menu, que exercitam os mesmos manipuladores do DS e de `menu.js`.

## Modal de confirmação (DS-60, DS-75)

Em `/admin/campi`, botão "Excluir campus …".

- Abre com o foco em "Cancelar", com a pergunta e o rótulo "Excluir" no botão de confirmação. PASS.
- Tab e Shift+Tab ciclam entre "Cancelar" e "Excluir" e não saem do modal. PASS.
- Esc fecha, a página não sai de `/admin/campi` e o foco volta ao botão de origem. PASS.
- "Cancelar" fecha, devolve o foco e **não exclui**: 14 linhas antes e 14 depois. PASS.

## Tema (DS-48, DS-53)

- O botão de tema troca claro e escuro **sem recarregar** (marca em `window` sobreviveu), atualiza `aria-pressed` (`false` para `true`), o rótulo ("Usar tema escuro" para "Usar tema claro") e grava `calcsistec-tema` = `escuro`. PASS.
- Tema escuro em `/`, `/matriculas` e `/admin/login` a 1280px: fundo, texto, KPIs, tabela, mensagens, botões, campos, `br-radio` e `dcc.Dropdown` legíveis. PASS.
- Contraste dos pares de token (`tests/test_contraste_tema.py`): texto acima de 4,5:1 e foco acima de 3:1 nos dois temas.

## Lacunas achadas e corrigidas

1. **`core.min.js` não instancia o menu do DS** (o botão não abria). O shell carrega `core-init.min.js` (AD-004). Teste: `tests/test_shell_assets.py`.
2. **DS não atualiza `aria-expanded` nem devolve o foco ao botão ao fechar.** Novo `app/static/js/menu.js`. Teste: `tests/test_js_menu.py`.
3. **Rolagem lateral em 320px** em três telas: mensagem com texto longo (`/admin/login`), `<pre>` do assistente (`/admin/instalacao`) e botão com rótulo longo (`/admin/config`). Regras em `style.css`. Teste: `tests/test_style_css.py`.
4. **Tema escuro (T52):** botão secundário, `br-input`, `br-message`, cabeçalho, rodapé, cartão e tabela precisaram de regra própria. Listadas no commit `feat(ui): tema escuro por tokens do DS`.

## Observações fora do escopo

- **Query string quebra as páginas do Dash.** `/matriculas?x=1` não renderiza o conteúdo: o Dash chama `layout(x="1")` e os `layout()` das páginas não aceitam parâmetros. Vem do código anterior a esta feature; fica como pendência (aceitar `**_` nos cinco `layout()`).
- **Fonte:** Rawline carregou local (`/ds/vendor/rawline/`). O Font Awesome 5 (T53) **não foi vendorizado**: falta autorização de Jaline para baixar da rede. Sem ele, os botões de ícone mostram só o rótulo acessível (`aria-label`) e o ícone fica em branco.
- Colunas da matriz de Matrículas mostram `co_unidade` e `total` (nomes crus): igual ao comportamento anterior.

## `scripts/verificar_prontidao_cutover.py`

**NO-GO por ambiente**, não por código: falham "autenticação admin configurada" (sem `ADMIN_EMAIL` e `ADMIN_PASSWORD_HASH` no processo) e "HTTPS configurado" (`CALCSISTEC_HTTPS=1`). Passam PII no schema, schema v2, fatores, ano-base e (com os dados simulados) dataset publicado. Ficam abertos, fora do escopo automatizável: paridade, design em celular real (T57), onboarding com Sistec real, extensão e comunicação aos stakeholders.
