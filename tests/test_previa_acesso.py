"""Suíte de acesso, posse e ciclo de vida da prévia (`previa-paginas-publicas`,
T25): sem sessão redireciona, sessão alheia/identificador forjado/execução
perdida/URL antiga mostram "Prévia indisponível", e nenhuma resposta expõe dado
pessoal (PVP-07/PVP-08/PVP-10).
"""

import importlib
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arvore_dash import textos  # noqa: E402
from app import app as app_module  # noqa: E402
from app.data.ingest import preparar_versao  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402

previa = importlib.import_module("pages.previa")
matriculas = importlib.import_module("pages.matriculas")

PII = {"nome", "cpf", "email", "e_mail", "data_nascimento", "nascimento"}


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    yield
    execucoes._REGISTRO.clear()


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "acesso.db")
    init_db(caminho)
    return caminho


def _leitura_envio():
    ciclo = {
        "CODIGO_CICLO_MATRICULA": "C1",
        "CO_UNIDADE": "U1",
        "CÓDIGO DO PORTFÓLIO": "P1",
        "NOME_CURSO": "TÉCNICO EM X",
        "TIPO_CURSO": "TECNICO",
        "CARGA_HORARIA_TOTAL": 1200,
        "MODALIDADE_ENSINO": "PRESENCIAL",
        "OFERTA": "ANUAL",
        "EIXO_TECNOLOGICO": "EIXO1",
        "TIPO_PROGRAMA_CURSO": "REGULAR",
        "DT_DATA_INICIO": "2026-01-01",
        "DT_DATA_FIM_PREVISTO": "2027-01-01",
        "STATUS_CICLO": "ATIVO",
        "SITUACAO_CICLO": "ATIVO",
    }
    matricula = {
        "CO_MATRICULA": "M1",
        "CODIGO_CICLO_MATRICULA": "C1",
        "STATUS_MATRICULA_SISTEC": "EM_CURSO",
        "MES_OCORRENCIA_CORRIGIDO": "2026-01-01",
    }
    return {
        "ciclo": [("ciclos.csv", pd.DataFrame([ciclo]))],
        "matricula": [("matriculas.csv", pd.DataFrame([matricula]))],
    }


def _candidato(db_path):
    leitura = _leitura_envio()
    conjunto = consolidar([leitura["ciclo"][0][1]], [leitura["matricula"][0][1]])
    return preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)


def _envio_com_previa(db_path, monkeypatch, sessao="sessao-A"):
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')")
        conn.commit()
    finally:
        conn.close()

    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["c.csv"], ["m.csv"], sessao_id=sessao)
    execucoes.registrar_leitura(envio, _leitura_envio())
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)

    for pagina in (previa, matriculas):
        monkeypatch.setattr(pagina, "sessao_id_atual", lambda: sessao)
    return envio


def test_get_previa_sem_sessao_redireciona_para_login():
    cliente = app_module.server.test_client()
    resposta = cliente.get("/admin/previa/abc/matriculas", follow_redirects=False)
    assert resposta.status_code in (301, 302)
    assert "/admin/login" in resposta.headers.get("Location", "")


def test_segunda_sessao_do_mesmo_email_recebe_indisponivel(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch, sessao="sessao-A")
    monkeypatch.setattr(previa, "sessao_id_atual", lambda: "sessao-B")

    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")

    assert "Prévia indisponível" in textos(layout)
    assert "Prévia não publicada" not in textos(layout)


def test_preview_id_forjado_o_callback_recusa(db_path, monkeypatch):
    _envio_com_previa(db_path, monkeypatch, sessao="sessao-A")

    layout = previa.layout(execucao_id="forjado", pagina="matriculas")

    assert "Prévia indisponível" in textos(layout)


def test_caminho_publico_ignora_contexto_forjado(monkeypatch):
    # o caminho público nunca lê preview_id: devolve a página pública normal
    monkeypatch.setattr(matriculas, "dataset_disponivel", lambda: True)
    monkeypatch.setattr(matriculas, "carregar_matriculas", lambda: pd.DataFrame(
        [{"cidade": "Santa Maria", "tipo_curso_pnp": "TECNICO", "tipo_programa_curso": "REGULAR"}]
    ))
    monkeypatch.setattr(matriculas, "ano_base_ativo", lambda: 2026)
    monkeypatch.setattr(matriculas, "data_ultima_publicacao", lambda: "2026-09-22")

    layout = matriculas.layout()

    assert layout.className == "painel-landing"
    assert "Prévia indisponível" not in textos(layout)


def test_url_previa_apos_salvar_indisponivel(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    execucoes.salvar(envio, db_path, 2026)

    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")

    assert "Prévia indisponível" in textos(layout)


def test_url_previa_apos_descartar_indisponivel(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    execucoes.descartar(envio)

    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")

    assert "Prévia indisponível" in textos(layout)


def test_registro_limpo_execucao_perdida_indisponivel(monkeypatch):
    monkeypatch.setattr(previa, "sessao_id_atual", lambda: "sessao-A")

    layout = previa.layout(execucao_id="qualquer-id", pagina="matriculas")

    assert "Prévia indisponível" in textos(layout)


def test_resposta_da_previa_sem_dado_pessoal(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    fonte = envio.previa_fonte
    conn = fonte.abrir_leitura()
    try:
        colunas = {linha[1] for linha in conn.execute("PRAGMA table_info(matriculas)")}
    finally:
        conn.close()

    assert not (colunas & PII)

    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")
    texto = textos(layout).lower()
    assert "cpf" not in texto and "email" not in texto
