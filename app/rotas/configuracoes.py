"""Rotas de configurações da instituição e dos dados publicados."""

import os

import flask

from app.auth import email_valido, requer_autenticacao
from app.data import campi, fatores, instalacao, versoes
from app.data.campi import listar_campi
from app.data.config_store import (
    dados_instituicao,
    get_contato_email,
    get_qtd_perfis,
    reset_contato_email,
    reset_logo,
    set_contato_email,
    set_instituicao,
    set_logo,
    set_qtd_perfis,
)
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.data.image_validation import ImagemInvalida, validar_e_normalizar_png
from app.data.schema import DEFAULT_DB_PATH
from app.data.svg_sanitize import SvgInvalido, sanitizar_svg
from app.rotas import comum
from app.rotas.acesso import _MSG_EMAIL_INVALIDO
from app.rotas.publico import UPLOADS_BRANDING_DIR
from app.sistec import execucoes

configuracoes_bp = flask.Blueprint("configuracoes_bp", __name__)

LOGO_MAX_BYTES = 500 * 1024  # Logotipos acima deste limite são rejeitados.


def historico_iniciar_e_encerrar(tipo, admin_email, desfecho):
    historico_id = historico_iniciar(tipo, admin_email)
    historico_encerrar(historico_id, desfecho)
    return historico_id


FATORES_PENDENTE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "uploads", "fatores_pendente.xlsx"
)


@configuracoes_bp.route("/admin/config", methods=["GET", "POST"])
@requer_autenticacao
def admin_config():
    """Configura e-mail de contato, logotipo, campi e fatores.

    Cada ação (`acao` no formulário) é
    independente — salvar/restaurar e-mail não afeta o logotipo e vice-versa.

    `iniciar_captura` e `salvar_lista_campi` respondem JSON (a
    tela precisa do `captura_id`/`token` para falar com a extensão, igual a
    `/admin/atualizar/execucoes`); as demais seguem o padrão de form POST +
    recarregar a página desta rota."""
    if flask.request.method == "POST" and flask.request.form.get("acao") == "iniciar_captura":
        try:
            captura = execucoes.criar_captura(comum.admin_email())
        except execucoes.ExecucaoInvalida:
            return flask.jsonify({"erro": "execucao_em_andamento"}), 409
        return flask.jsonify({"captura_id": captura.id, "token": captura.token})

    contexto = {
        "contato_email": get_contato_email(),
        "instituicao": dados_instituicao(),
        "erro_email": None,
        "mensagem_email": None,
        "sucesso_email": False,
        "mensagem_logo": None,
        "sucesso_logo": False,
        "campi": listar_campi(),
        "id_suspeito": campi.id_suspeito,
        "qtd_perfis": get_qtd_perfis(),
        "mensagem_campi": None,
        "fatores_diferenca": None,
        "fatores_avisos": None,
        "mensagem_fatores": None,
        "sucesso_fatores": False,
    }

    if flask.request.method == "POST":
        acao = flask.request.form.get("acao")

        if acao == "salvar_lista_campi":
            captura = execucoes.obter_captura_do_admin(comum.admin_email())
            if captura is None:
                contexto["mensagem_campi"] = "Nenhuma captura de perfis em revisão."
            else:
                try:
                    execucoes.salvar_lista_captura(captura, DEFAULT_DB_PATH)
                    contexto["mensagem_campi"] = "Lista de campi salva."
                except execucoes.ExecucaoInvalida as exc:
                    contexto["mensagem_campi"] = str(exc)
            contexto["campi"] = listar_campi()

        elif acao == "cancelar_captura":
            captura = execucoes.obter_captura_do_admin(comum.admin_email())
            if captura is None:
                contexto["mensagem_campi"] = "Nenhuma captura em andamento."
            else:
                try:
                    execucoes.cancelar_captura(captura)
                    contexto["mensagem_campi"] = "Captura cancelada."
                except execucoes.ExecucaoInvalida as exc:
                    contexto["mensagem_campi"] = str(exc)

        elif acao == "salvar_qtd_perfis":
            qtd = flask.request.form.get("qtd_perfis", "").strip()
            if qtd and not qtd.isdigit():
                contexto["mensagem_campi"] = "A quantidade de perfis precisa ser um número."
            else:
                set_qtd_perfis(qtd)
                contexto["qtd_perfis"] = get_qtd_perfis()
                contexto["mensagem_campi"] = "Quantidade de perfis salva."

        elif acao == "importar_perfis":
            from app.sistec.perfis import perfis_de_texto

            perfis, invalidas = perfis_de_texto(flask.request.form.get("lista_perfis", ""))
            if not perfis:
                contexto["mensagem_campi"] = (
                    "Nenhuma linha no formato esperado (identificador ; nome do perfil)."
                )
            else:
                try:
                    campi.salvar_captura([{**p, "ordem": i} for i, p in enumerate(perfis)], DEFAULT_DB_PATH)
                    contexto["mensagem_campi"] = f"{len(perfis)} campus(i) importados."
                    if invalidas:
                        contexto["mensagem_campi"] += f" {len(invalidas)} linha(s) ignorada(s)."
                except campi.CampusInvalido as exc:
                    contexto["mensagem_campi"] = f"Não foi possível importar: {exc}."
            contexto["campi"] = listar_campi()

        elif acao == "salvar_instituicao":
            nome = flask.request.form.get("nome", "").strip()
            if not nome:
                contexto["mensagem_campi"] = "Informe o nome da instituição."
            else:
                set_instituicao(
                    nome=nome,
                    sigla=flask.request.form.get("sigla", "").strip(),
                    site=flask.request.form.get("site", "").strip(),
                )
                contexto["mensagem_campi"] = "Dados da instituição salvos."

        elif acao == "resetar_instalacao":
            # Troca da pessoa responsável, ou levar o programa para outra
            # instituição: volta ao estado de instalação nova.
            instalacao.resetar(DEFAULT_DB_PATH, apagar_dados=flask.request.form.get("apagar_dados") == "1")
            return flask.redirect("/admin/instalacao")

        elif acao == "salvar_fator":
            linhas_atuais = fatores.ler_fatores_atuais("interna_fatores", DEFAULT_DB_PATH)
            chave_tipo = flask.request.form.get("chave_tipo", "")
            chave_nome = flask.request.form.get("chave_nome", "")
            try:
                fec = float(flask.request.form.get("fec", ""))
                fech = float(flask.request.form.get("fech", ""))
            except ValueError:
                contexto["mensagem_fatores"] = "FEC/FECH precisam ser números."
            else:
                linhas_novas = [
                    (l[0], l[1], fec, fech, l[4], l[5]) if (l[4], l[5]) == (chave_tipo, chave_nome) else l
                    for l in linhas_atuais
                ]
                fatores.substituir_interna_fatores(linhas_novas, DEFAULT_DB_PATH)
                contexto["mensagem_fatores"] = "Fator atualizado."
                contexto["sucesso_fatores"] = True

        elif acao == "enviar_fatores":
            arquivo = flask.request.files.get("arquivo_fatores")
            if arquivo is None or not arquivo.filename:
                contexto["mensagem_fatores"] = "Selecione um arquivo de fatores (.xlsx)."
            else:
                os.makedirs(os.path.dirname(FATORES_PENDENTE_PATH), exist_ok=True)
                arquivo.save(FATORES_PENDENTE_PATH)
                try:
                    linhas_novas, avisos = fatores.ler_e_validar(FATORES_PENDENTE_PATH)
                except fatores.ArquivoFatoresInvalido as exc:
                    os.remove(FATORES_PENDENTE_PATH)
                    contexto["mensagem_fatores"] = f"Arquivo rejeitado: {'; '.join(exc.erros)}"
                else:
                    linhas_atuais = fatores.ler_fatores_atuais("interna_fatores", DEFAULT_DB_PATH)
                    contexto["fatores_diferenca"] = fatores.diferenca_fatores(linhas_atuais, linhas_novas)
                    contexto["fatores_avisos"] = avisos
                    contexto["mensagem_fatores"] = "Prévia pronta — confira as diferenças e confirme a troca."

        elif acao == "confirmar_fatores":
            if not os.path.isfile(FATORES_PENDENTE_PATH):
                contexto["mensagem_fatores"] = "Nenhum arquivo pendente de confirmação."
            else:
                try:
                    linhas_novas, _avisos = fatores.ler_e_validar(FATORES_PENDENTE_PATH)
                    fatores.substituir_interna_fatores(linhas_novas, DEFAULT_DB_PATH)
                    historico_iniciar_e_encerrar("fatores_arquivo", comum.admin_email(), "aplicada")
                    contexto["mensagem_fatores"] = "Tabela de fatores atualizada na versão interna."
                    contexto["sucesso_fatores"] = True
                except fatores.ArquivoFatoresInvalido as exc:
                    contexto["mensagem_fatores"] = f"Arquivo rejeitado: {'; '.join(exc.erros)}"
                finally:
                    if os.path.isfile(FATORES_PENDENTE_PATH):
                        os.remove(FATORES_PENDENTE_PATH)

        elif acao == "restaurar_fatores":
            from app.data.schema import FATORES_PADRAO_PATH

            linhas_padrao, _avisos = fatores.ler_e_validar(FATORES_PADRAO_PATH)
            fatores.substituir_interna_fatores(linhas_padrao, DEFAULT_DB_PATH)
            historico_iniciar_e_encerrar("fatores_restaurar_padrao", comum.admin_email(), "aplicada")
            contexto["mensagem_fatores"] = "Tabela de fatores restaurada ao padrão de fábrica."
            contexto["sucesso_fatores"] = True

        elif acao == "aplicar_publico":
            versoes.aplicar_publico(DEFAULT_DB_PATH, admin_email=comum.admin_email())
            historico_iniciar_e_encerrar("configuracao_aplicada_publico", comum.admin_email(), "aplicada")
            contexto["mensagem_campi"] = "Campi e fatores aplicados ao painel público."
            contexto["campi"] = listar_campi()

        elif acao == "salvar_email":
            novo_email = flask.request.form.get("contato_email", "").strip()
            if email_valido(novo_email):
                set_contato_email(novo_email)
                contexto["contato_email"] = novo_email
                contexto["mensagem_email"] = "E-mail de contato salvo."
                contexto["sucesso_email"] = True
            else:
                contexto["erro_email"] = _MSG_EMAIL_INVALIDO
                contexto["contato_email"] = novo_email
                contexto["mensagem_email"] = "Não foi possível salvar: e-mail inválido."

        elif acao == "restaurar_email":
            reset_contato_email()
            contexto["contato_email"] = get_contato_email()
            contexto["mensagem_email"] = "E-mail de contato restaurado ao padrão de fábrica."
            contexto["sucesso_email"] = True

        elif acao == "enviar_logo":
            arquivo = flask.request.files.get("logo")
            if arquivo is None or not arquivo.filename:
                contexto["mensagem_logo"] = "Selecione um arquivo de logotipo (SVG ou PNG)."
            else:
                dados = arquivo.read()
                if len(dados) > LOGO_MAX_BYTES:
                    contexto["mensagem_logo"] = "Arquivo maior que 500 KB — envie um logotipo menor."
                else:
                    extensao = os.path.splitext(arquivo.filename)[1].lower()
                    os.makedirs(UPLOADS_BRANDING_DIR, exist_ok=True)
                    try:
                        if extensao == ".svg":
                            limpo = sanitizar_svg(dados)
                            destino = os.path.join(UPLOADS_BRANDING_DIR, "logo-atual.svg")
                            with open(destino, "wb") as f:
                                f.write(limpo)
                            set_logo(destino)
                            contexto["mensagem_logo"] = "Logotipo atualizado."
                            contexto["sucesso_logo"] = True
                        elif extensao == ".png":
                            normalizado = validar_e_normalizar_png(dados)
                            destino = os.path.join(UPLOADS_BRANDING_DIR, "logo-atual.png")
                            with open(destino, "wb") as f:
                                f.write(normalizado)
                            set_logo(destino)
                            contexto["mensagem_logo"] = "Logotipo atualizado."
                            contexto["sucesso_logo"] = True
                        else:
                            contexto["mensagem_logo"] = "Formato não suportado — envie um arquivo .svg ou .png."
                    except (SvgInvalido, ImagemInvalida) as exc:
                        contexto["mensagem_logo"] = f"Logotipo rejeitado: {exc}"

        elif acao == "restaurar_logo":
            reset_logo()
            contexto["mensagem_logo"] = "Logotipo restaurado ao padrão de fábrica."
            contexto["sucesso_logo"] = True

    return flask.render_template("configuracoes.html", **contexto)


@configuracoes_bp.route("/admin/config/captura", methods=["GET"])
@requer_autenticacao
def admin_config_captura_estado():
    """Estado JSON da captura de campi da extensão MV3.

    **Sem uso pelas telas**: a lista de campi é cadastrada à mão.
    Mantida junto com `extensao-sistec/` e `/api/sistec/capturas/*` para o caso
    de a distribuição por extensão voltar."""
    captura = execucoes.obter_ultima_captura_do_admin(comum.admin_email())
    if captura is None:
        return flask.jsonify({"estado": None})

    return flask.jsonify(
        {
            "estado": captura.estado,
            "motivo_falha": captura.motivo_falha,
            "perfis": captura.perfis if captura.estado == "revisao" else None,
        }
    )

