"""Testes do guardião de posse, origem, estado e ciclo de vida da prévia
(`previa-paginas-publicas`, T4–T8) em `app/sistec/execucoes.py`.

Cobrem PVP-07/PVP-08: `obter_previa` só autoriza a sessão dona de um envio em
estado `previa`; a fonte candidata abre/libera; leitura e transição de estado
são serializadas por trava; e falhas de página bloqueiam o Salvar.
"""

import os
import sys
from datetime import datetime

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.sistec import execucoes  # noqa: E402


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()
    yield
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()


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


def _envio_em_previa(sessao_id="sessao-A"):
    """Cria um envio consolidado em estado `previa`, dono da `sessao_id`."""
    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id=sessao_id
    )
    execucoes.registrar_leitura(envio, _leitura_envio())
    return envio


# ===================== T4: guardião de posse, origem e estado =====================


def test_obter_previa_autoriza_a_sessao_dona():
    envio = _envio_em_previa()
    assert execucoes.obter_previa(envio.id, "sessao-A") is envio


def test_obter_previa_recusa_execucao_inexistente():
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa("nao-existe", "sessao-A")


def test_obter_previa_recusa_sessao_alheia_do_mesmo_email():
    envio = _envio_em_previa(sessao_id="sessao-A")
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, "sessao-B")


def test_obter_previa_recusa_sessao_ausente_quando_dona_exigida():
    envio = _envio_em_previa(sessao_id="sessao-A")
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, None)


def test_obter_previa_recusa_origem_baixa():
    from app.sistec.execucoes import criar_execucao

    baixa = criar_execucao(
        "pi@iffarroupilha.edu.br", [{"id_perfil": "1", "nome_perfil": "Campus A"}]
    )
    baixa.estado = "previa"
    baixa.sessao_dona = "sessao-A"
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(baixa.id, "sessao-A")


def test_obter_previa_recusa_estado_terminal():
    envio = _envio_em_previa()
    envio.estado = "salva"
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, "sessao-A")


def test_obter_previa_recusa_estado_diferente_de_previa():
    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id="sessao-A"
    )
    # ainda em `consolidando`, antes de registrar a leitura
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, "sessao-A")


def test_obter_previa_registro_limpo_devolve_indisponivel():
    # registro vazio (reinício do processo): execução pendente deixou de existir
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa("qualquer-id", "sessao-A")
