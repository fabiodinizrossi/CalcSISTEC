"""Salvar de uma execução de envio (`/admin/atualizar/execucoes/<id>/salvar`,
T8/UPL-08).

O portão de confirmação vive no servidor: sem `confirmar_preservacao`, um
envio que preserva campi ausentes não grava nada. A gravação em si é
substituída por um dublê — o que este arquivo cobre é a rota.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as app_module  # noqa: E402
from app.data import ingest, versoes  # noqa: E402
from app.sistec import execucoes  # noqa: E402

ADMIN = "pi@ife.edu.br"
HISTORICO = []
GRAVACOES = []

CAMPI_BAIXA = [
    {"id_perfil": "1", "nome_perfil": "Assessor A", "co_unidade": "U1"},
]


def _iniciar(tipo, email):
    HISTORICO.append({"tipo": tipo, "admin_email": email, "desfecho": None, "campi_mantidos": None})
    return len(HISTORICO)


def _encerrar(historico_id, desfecho, **kwargs):
    HISTORICO[historico_id - 1]["desfecho"] = desfecho
    HISTORICO[historico_id - 1]["campi_mantidos"] = kwargs.get("campi_mantidos")


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    HISTORICO.clear()
    GRAVACOES.clear()
    execucoes._REGISTRO.clear()

    def montar(conjunto, campi_falhos, db_path=None, ano_base=None):
        GRAVACOES.append({"campi_falhos": set(campi_falhos), "ano_base": ano_base})
        return {"matriculas": 2, "ciclos": 1, "campi_mantidos": sorted(campi_falhos)}

    def gravar(conjunto, db_path=None, assinatura_esperada=None):
        GRAVACOES.append({"assinatura_esperada": assinatura_esperada})

    monkeypatch.setattr(ingest, "montar_versao_interna", montar)
    monkeypatch.setattr(versoes, "salvar_interna", gravar)
    monkeypatch.setattr(app_module, "historico_iniciar", _iniciar)
    monkeypatch.setattr(app_module, "historico_encerrar", _encerrar)
    yield
    execucoes._REGISTRO.clear()


@pytest.fixture
def sessao():
    cliente = app_module.server.test_client()
    with cliente.session_transaction() as s:
        s["admin_usuario"] = ADMIN
        s["admin_autenticado"] = True
    return cliente


@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    from app.data.consulta import ano_base_ativo
    from app.data.schema import init_db

    caminho = str(tmp_path / "salvar.db")
    init_db(caminho)
    monkeypatch.setattr(app_module, "DEFAULT_DB_PATH", caminho)
    monkeypatch.setattr(app_module, "ano_base_ativo", lambda: ano_base_ativo(caminho))
    return caminho


def _execucao_de_envio_com_previa(preservados=("U2",), ano_base=2026):
    execucao = execucoes.criar_execucao_envio(
        ADMIN, ["ciclos-U1.csv"], ["matriculas-U1.csv"], historico_id=len(HISTORICO) + 1
    )
    _iniciar("envio", ADMIN)
    execucao.estado = "previa"
    execucoes.definir_campi_preservados(execucao, preservados)
    # T23: o salvar de um envio grava o candidato já preparado — o dublê cobre
    # só a chamada a `versoes.salvar_interna`.
    execucao.candidato = {
        "tabelas": {},
        "resumo": {"matriculas": 2, "ciclos": 1, "campi_mantidos": sorted(preservados)},
        "assinatura_origem": {
            "ano_base": ano_base,
            "rev_interna": 0,
            "rev_publicada": None,
            "fatores": (),
            "campus": (),
        },
    }
    return execucao


def test_salvar_envio_com_campi_preservados_sem_confirmacao_nao_grava(sessao):
    execucao = _execucao_de_envio_com_previa()

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={})

    assert resposta.status_code == 409
    assert resposta.get_json() == {"erro": "confirmacao_necessaria", "campi_preservados": ["U2"]}
    assert GRAVACOES == []
    assert execucao.estado == "previa"


def test_salvar_envio_com_confirmacao_grava_e_registra_os_campi_preservados(sessao, banco_temporario):
    from app.data.consulta import ano_base_ativo

    ano = ano_base_ativo(banco_temporario)
    execucao = _execucao_de_envio_com_previa(ano_base=ano)

    resposta = sessao.post(
        f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={"confirmar_preservacao": True}
    )

    assert resposta.status_code == 200
    assert GRAVACOES == [{"assinatura_esperada": execucao.candidato["assinatura_origem"]}]
    # o ano-base recebido vem da assinatura de origem, igual ao config.ano_base
    assert GRAVACOES[0]["assinatura_esperada"]["ano_base"] == ano
    assert execucao.estado == "salva"
    assert HISTORICO[0]["desfecho"] == "salva"
    assert HISTORICO[0]["campi_mantidos"] == ["U2"]


def test_salvar_envio_sem_campi_preservados_nao_exige_confirmacao(sessao):
    execucao = _execucao_de_envio_com_previa(preservados=())

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={})

    assert resposta.status_code == 200
    assert execucao.estado == "salva"


def test_salvar_baixa_continua_sem_exigir_o_campo(sessao):
    execucao = execucoes.criar_execucao(ADMIN, CAMPI_BAIXA, historico_id=len(HISTORICO) + 1)
    _iniciar("baixa", ADMIN)
    execucao.estado = "previa"
    execucao.previa = {"ciclos": None, "matriculas": None}

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar")

    assert resposta.status_code == 200
    assert execucao.estado == "salva"
    # a baixa direta continua gravando pelo ano-base do ambiente
    assert GRAVACOES == [{"campi_falhos": set(), "ano_base": app_module._ano_base_config()}]


def test_confirmacao_nao_grava_conteudo_de_planilha_no_historico(sessao):
    execucao = _execucao_de_envio_com_previa(preservados=("U2",))
    sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={"confirmar_preservacao": True})

    assert "U1" not in json.dumps(HISTORICO[0], ensure_ascii=False, default=str)
