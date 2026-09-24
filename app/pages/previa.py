"""Página da prévia (`previa-paginas-publicas`, T16): decide qual das quatro
páginas públicas chamar, valida o contexto (sessão dona, origem `envio`,
estado `previa`) e monta a faixa **Prévia não publicada**, a navegação entre
as quatro páginas e os avisos do envio.

O guarda de sessão (`app.app._exigir_sessao_previa`, T15) já barra a requisição
sem login; aqui a validação de posse de `obter_previa` (T4) é a segunda camada.
Uma falha ao renderizar registra `registrar_falha_pagina` (T8); uma renderização
bem-sucedida limpa a falha anterior.
"""

import importlib

import dash
from dash import html

from app.auth import sessao_id_atual
from app.components.mensagem import mensagem_ds
from app.sistec.execucoes import (
    PreviaIndisponivel,
    limpar_falha_pagina,
    obter_previa,
    registrar_falha_pagina,
)

dash.register_page(
    __name__,
    path_template="/admin/previa/<execucao_id>/<pagina>",
    title="Prévia - Pesquisa Institucional - SISTEC",
)

# slug da URL -> (rótulo, módulo da página pública em `pages/`).
_PAGINAS = {
    "matriculas": ("Matrículas", "matriculas"),
    "eficiencia": ("Eficiência Acadêmica", "eficiencia"),
    "evasao": ("Taxa de Evasão Anual", "evasao"),
    "percentuais-legais": ("Percentuais Legais", "percentuais_legais"),
}


def _voltar_atualizar():
    return html.A("Atualizar dados", href="/admin/atualizar", className="br-button secondary")


def _indisponivel():
    """PVP-08: slug desconhecido, execução perdida, sessão alheia ou estado
    terminal — nunca a mensagem pública de ausência de dados."""
    return html.Div(
        [
            mensagem_ds("warning", "Prévia indisponível."),
            html.P(_voltar_atualizar()),
        ],
        className="previa-indisponivel",
    )


def _faixa(execucao_id, pagina):
    """Faixa "Prévia não publicada" + navegação entre as quatro páginas."""
    links = []
    for slug, (rotulo, _modulo) in _PAGINAS.items():
        classe = "br-button primary" if slug == pagina else "br-button secondary"
        links.append(html.A(rotulo, href=f"/admin/previa/{execucao_id}/{slug}", className=classe))
    links.append(_voltar_atualizar())
    return html.Div(
        [
            mensagem_ds("warning", "Prévia não publicada. Nada foi salvo ainda."),
            html.Div(links, className="previa-navegacao"),
        ],
        className="previa-faixa",
    )


def _avisos(execucao):
    """PVP-05: avisos já apurados no envio — campi preservados, unidades
    cadastradas pelo envio, matrículas órfãs e arquivos ignorados."""
    itens = []
    campi = sorted(execucao.campi_falhos or ())
    if campi:
        itens.append(f"Unidades com dados preservados: {', '.join(campi)}.")
    cadastrados = list(getattr(execucao, "campi_cadastrados_automaticamente", []) or [])
    if cadastrados:
        itens.append(f"Unidades cadastradas pelo envio: {', '.join(cadastrados)}.")
    orfas = getattr(execucao, "matriculas_orfas", 0) or 0
    if orfas:
        itens.append(f"{orfas} matrícula(s) órfã(s).")
    ignorados = list(getattr(execucao, "arquivos_ignorados", []) or [])
    if ignorados:
        itens.append(f"Arquivos ignorados: {', '.join(ignorados)}.")
    if not itens:
        return None
    return html.Ul([html.Li(item) for item in itens], className="previa-avisos")


def layout(execucao_id=None, pagina=None, **kwargs):
    """Dash Pages injeta `execucao_id` e `pagina` das variáveis de caminho."""
    if pagina not in _PAGINAS:
        return _indisponivel()

    try:
        execucao = obter_previa(execucao_id, sessao_id_atual())
    except PreviaIndisponivel:
        return _indisponivel()

    rotulo, modulo = _PAGINAS[pagina]
    try:
        pagina_modulo = importlib.import_module(f"pages.{modulo}")
        conteudo = pagina_modulo.layout(preview_id=execucao_id)
    except PreviaIndisponivel:
        return _indisponivel()
    except Exception:
        registrar_falha_pagina(execucao, pagina)
        conteudo = mensagem_ds("danger", f"Não foi possível renderizar a página {rotulo}. Descarte ou recarregue.")
    else:
        limpar_falha_pagina(execucao, pagina)

    filhos = [_faixa(execucao_id, pagina)]
    avisos = _avisos(execucao)
    if avisos is not None:
        filhos.append(avisos)
    filhos.append(conteudo)

    return html.Div(filhos, className="previa-pagina")
