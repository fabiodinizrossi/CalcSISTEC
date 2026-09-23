"""Estado do envio no polling da tela (`GET /admin/atualizar/execucao`,
T9/UPL-09).

A rota é a mesma da baixa: os campos novos são só códigos institucionais,
nomes de arquivo e contagens — nunca dado pessoal nem conteúdo de célula.
"""

import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as app_module  # noqa: E402
from app.data.transform import COLUNAS_PII  # noqa: E402
from app.sistec import execucoes  # noqa: E402

ADMIN = "pi@ife.edu.br"
CELULA_SENSIVEL = "SEGREDO-DE-CELULA"

CAMPI_BAIXA = [{"id_perfil": "1", "nome_perfil": "Assessor A", "co_unidade": "U1"}]


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    execucoes._REGISTRO.clear()
    monkeypatch.setattr(app_module.navegador, "status", lambda email: None)
    yield
    execucoes._REGISTRO.clear()


@pytest.fixture
def sessao():
    cliente = app_module.server.test_client()
    with cliente.session_transaction() as s:
        s["admin_usuario"] = ADMIN
        s["admin_autenticado"] = True
    return cliente


def test_polling_de_envio_devolve_os_campos_da_tela(sessao):
    execucao = execucoes.criar_execucao_envio(ADMIN, ["ciclos-U1.csv"], ["matriculas-U1.csv"])
    execucao.estado = "previa"
    execucao.campi_falhos = {"U2", "U3"}
    execucao.campi_cadastrados_automaticamente = ["U9"]
    execucao.arquivos_ignorados = ["LEIA-ME.txt"]
    execucao.matriculas_orfas = 4

    corpo = sessao.get("/admin/atualizar/execucao").get_json()

    assert corpo["origem"] == "envio"
    assert corpo["campi_preservados"] == ["U2", "U3"]
    assert corpo["campi_cadastrados_automaticamente"] == ["U9"]
    assert corpo["arquivos_ignorados"] == ["LEIA-ME.txt"]
    assert corpo["matriculas_orfas"] == 4


def test_polling_de_baixa_mantem_a_resposta_e_zera_os_campos_novos(sessao):
    execucao = execucoes.criar_execucao(ADMIN, CAMPI_BAIXA)
    execucao.estado = "baixando"

    corpo = sessao.get("/admin/atualizar/execucao").get_json()

    assert corpo["origem"] == "baixa"
    assert corpo["campi_preservados"] == []
    assert corpo["campi_cadastrados_automaticamente"] == []
    assert corpo["arquivos_ignorados"] == []
    assert corpo["matriculas_orfas"] == 0
    # A resposta anterior continua inteira.
    assert set(corpo) >= {"estado", "execucao_id", "navegador", "erro_consolidacao", "progresso", "pares", "previa"}
    assert corpo["progresso"] == {"total": 2, "concluidos": 0}


def test_polling_sem_execucao_nao_quebra(sessao):
    corpo = sessao.get("/admin/atualizar/execucao").get_json()
    assert corpo["estado"] is None
    assert corpo["navegador"] is None


def test_previa_com_valores_ausentes_mantem_json_legivel_pelo_navegador(sessao):
    execucao = execucoes.criar_execucao_envio(ADMIN, ["ciclos-U1.csv"], ["matriculas-U1.csv"])
    execucao.estado = "previa"
    execucao.previa = {
        "ciclos": pd.DataFrame([{"curso": "TÉCNICO", "vazio": float("nan"), "infinito": float("inf"), "nulo": pd.NA}]),
        "matriculas": pd.DataFrame([{"codigo": "M1"}]),
    }

    resposta = sessao.get("/admin/atualizar/execucao")
    corpo = json.loads(
        resposta.get_data(as_text=True),
        parse_constant=lambda valor: (_ for _ in ()).throw(ValueError(f"JSON inválido: {valor}")),
    )

    assert resposta.status_code == 200
    assert corpo["estado"] == "previa"
    assert corpo["execucao_id"] == execucao.id
    assert corpo["previa"]["ciclos"] == 1
    assert corpo["previa"]["matriculas"] == 1
    assert corpo["previa"]["amostra"] == [
        {"curso": "TÉCNICO", "vazio": None, "infinito": None, "nulo": None}
    ]


def test_campos_novos_do_polling_nao_carregam_pii_nem_conteudo_de_celula(sessao):
    execucao = execucoes.criar_execucao_envio(ADMIN, ["ciclos-U1.csv"], ["matriculas-U1.csv"])
    execucao.estado = "previa"
    execucao.campi_cadastrados_automaticamente = ["U9"]
    execucao.arquivos_ignorados = ["LEIA-ME.txt"]

    bruto = sessao.get("/admin/atualizar/execucao").get_data(as_text=True)

    assert CELULA_SENSIVEL not in bruto
    for coluna_pii in COLUNAS_PII:
        assert coluna_pii not in bruto
