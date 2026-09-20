"""Lista de campi do painel administrativo: busca, paginação e telas do CRUD."""

from urllib.parse import urlencode

from flask import Blueprint, abort, flash, get_flashed_messages, redirect, render_template, request

from app.auth import requer_autenticacao
from app.data.campi import (
    CampusInvalido,
    definir_ativo,
    excluir_campus,
    id_suspeito,
    incluir_campus,
    listar_campi,
    obter_campus,
    salvar_campus_manual,
    validar_campos_campus,
)
from app.data.schema import DEFAULT_DB_PATH

TAMANHOS_DE_PAGINA = (10, 25, 50)
CAMPOS_DA_BUSCA = ("nome_perfil", "cidade", "nome_unidade")

# Os testes trocam o banco por um temporário.
DB_PATH = DEFAULT_DB_PATH

campi_bp = Blueprint("campi_bp", __name__)


def _inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def filtrar_e_paginar(campi, q, pagina, por_pagina):
    """Filtra `campi` pelo texto `q` (perfil, cidade ou nome da unidade, sem
    diferenciar maiúsculas) e devolve a página pedida.

    `por_pagina` fora de 10, 25 e 50 vira 10; `pagina` inválida ou além da
    última vira 1. `inicio` e `fim` são índices de 1 em diante dos itens
    exibidos (0 e 0 quando não há nenhum)."""
    texto = (q or "").strip().lower()
    if texto:
        campi = [c for c in campi if any(texto in str(c.get(campo) or "").lower() for campo in CAMPOS_DA_BUSCA)]

    tamanho = _inteiro(por_pagina)
    if tamanho not in TAMANHOS_DE_PAGINA:
        tamanho = 10

    total = len(campi)
    ultima = max(1, -(-total // tamanho))
    numero = _inteiro(pagina)
    if numero is None or not 1 <= numero <= ultima:
        numero = 1

    primeiro = (numero - 1) * tamanho
    itens = campi[primeiro : primeiro + tamanho]
    return {
        "itens": itens,
        "total": total,
        "pagina": numero,
        "por_pagina": tamanho,
        "inicio": primeiro + 1 if itens else 0,
        "fim": primeiro + len(itens),
    }


def _url_da_lista(q, pagina, por_pagina):
    params = {"por_pagina": por_pagina, "pagina": pagina}
    if q:
        params["q"] = q
    return "/admin/campi?" + urlencode(params)


@campi_bp.route("/admin/campi")
@requer_autenticacao
def lista():
    todos = listar_campi(DB_PATH)
    q = request.args.get("q", "").strip()
    pagina = filtrar_e_paginar(todos, q, request.args.get("pagina"), request.args.get("por_pagina"))
    ultima = max(1, -(-pagina["total"] // pagina["por_pagina"]))
    return render_template(
        "campi_lista.html",
        existem_campi=bool(todos),
        pagina=pagina,
        q=q,
        tamanhos_de_pagina=TAMANHOS_DE_PAGINA,
        href_anterior=_url_da_lista(q, pagina["pagina"] - 1, pagina["por_pagina"]) if pagina["pagina"] > 1 else None,
        href_proxima=_url_da_lista(q, pagina["pagina"] + 1, pagina["por_pagina"]) if pagina["pagina"] < ultima else None,
        id_suspeito=id_suspeito,
        mensagens=get_flashed_messages(with_categories=True),
    )


CAMPOS_DA_EDICAO = ("id_perfil", "co_unidade", "cidade", "nome_unidade")
MENSAGEM_ERRO_DO_FORMULARIO = "Erro. Preencha abaixo os campos obrigatórios antes de enviar os dados."


def _campus_nao_encontrado():
    flash("Campus não encontrado.", "danger")
    return redirect("/admin/campi")


@campi_bp.route("/admin/campi/<id_perfil>/editar", methods=["GET", "POST"])
@requer_autenticacao
def editar(id_perfil):
    campus = obter_campus(id_perfil, DB_PATH)
    if campus is None:
        return _campus_nao_encontrado()

    valores, erros, faltam_campos = campus, {}, False
    if request.method == "POST":
        valores = {campo: request.form.get(campo, "").strip() for campo in CAMPOS_DA_EDICAO}
        erros = validar_campos_campus(valores)
        faltam_campos = bool(erros)
        if not erros:
            try:
                salvar_campus_manual(
                    id_perfil,
                    valores["co_unidade"],
                    valores["cidade"],
                    valores["nome_unidade"],
                    DB_PATH,
                    novo_id_perfil=valores["id_perfil"],
                )
            except CampusInvalido as exc:
                erros = {exc.campo or "id_perfil": str(exc)}
            else:
                flash("Campus atualizado.", "success")
                return redirect("/admin/campi")

    return render_template(
        "campi_form.html",
        titulo_pagina="Editar campus | " + campus["nome_perfil"],
        acao="/admin/campi/" + id_perfil + "/editar",
        valores=valores,
        erros=erros,
        mensagem_erro=MENSAGEM_ERRO_DO_FORMULARIO if faltam_campos else None,
    )


CAMPOS_DA_INCLUSAO = ("id_perfil", "nome_perfil", "co_unidade", "cidade", "nome_unidade")


@campi_bp.route("/admin/campi/novo", methods=["GET", "POST"])
@requer_autenticacao
def incluir():
    valores, erros, faltam_campos = {}, {}, False
    if request.method == "POST":
        valores = {campo: request.form.get(campo, "").strip() for campo in CAMPOS_DA_INCLUSAO}
        erros = validar_campos_campus(valores, inclusao=True)
        faltam_campos = bool(erros)
        if not erros:
            try:
                incluir_campus(
                    valores["id_perfil"],
                    valores["nome_perfil"],
                    valores["co_unidade"] or None,
                    valores["cidade"] or None,
                    valores["nome_unidade"] or None,
                    DB_PATH,
                )
            except CampusInvalido as exc:
                erros = {exc.campo or "id_perfil": str(exc)}
            else:
                flash("Campus incluído.", "success")
                return redirect("/admin/campi")

    return render_template(
        "campi_form.html",
        titulo_pagina="Incluir campus",
        acao="/admin/campi/novo",
        inclusao=True,
        valores=valores,
        erros=erros,
        mensagem_erro=MENSAGEM_ERRO_DO_FORMULARIO if faltam_campos else None,
    )


@campi_bp.route("/admin/campi/<id_perfil>/situacao", methods=["POST"])
@requer_autenticacao
def situacao(id_perfil):
    valor = request.form.get("ativo")
    if valor not in ("0", "1"):
        abort(400)
    if obter_campus(id_perfil, DB_PATH) is None:
        return _campus_nao_encontrado()
    definir_ativo(id_perfil, valor == "1", DB_PATH)
    flash("Campus reativado." if valor == "1" else "Campus desativado.", "success")
    return redirect("/admin/campi")


@campi_bp.route("/admin/campi/<id_perfil>/excluir", methods=["POST"])
@requer_autenticacao
def excluir(id_perfil):
    if obter_campus(id_perfil, DB_PATH) is None:
        return _campus_nao_encontrado()
    excluir_campus(id_perfil, DB_PATH)
    flash("Perfil excluído da lista.", "success")
    return redirect("/admin/campi")
