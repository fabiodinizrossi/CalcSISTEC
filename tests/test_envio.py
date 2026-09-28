"""Contratos do leitor de pastas enviadas pelo administrador."""

import io

import pytest
import pandas as pd
from werkzeug.datastructures import FileStorage

from app.sistec.colunas import COLUNAS_CICLO, COLUNAS_MATRICULA
from app.sistec.envio import (
    EnvioInvalido,
    campi_ausentes,
    campi_nao_cadastrados,
    dados_unidades_do_envio,
    ler_pastas,
    nome_seguro,
)


def _arquivo(nome, colunas):
    cabecalho = ";".join(colunas)
    linha = ";".join("x" for _ in colunas)
    return FileStorage(io.BytesIO(f"{cabecalho}\n{linha}\n".encode("cp1252")), filename=nome)


def _ciclo(nome="ciclos.csv"):
    return _arquivo(nome, COLUNAS_CICLO)


def _matricula(nome="matriculas.csv"):
    return _arquivo(nome, COLUNAS_MATRICULA)


def test_envio_invalido_expoe_somente_arquivo_e_motivo():
    erro = EnvioInvalido("quebrado.csv", "leitura_csv")
    assert (erro.arquivo, erro.motivo, str(erro)) == ("quebrado.csv", "leitura_csv", "quebrado.csv: leitura_csv")


def test_nome_seguro_remove_diretorios_windows_e_posix():
    assert nome_seguro(r"ciclos\\subpasta/arquivo.csv") == "arquivo.csv"


def test_ler_pastas_devolve_dataframes_por_tipo_e_ignorados():
    resultado = ler_pastas([_ciclo(), _arquivo("nota.txt", ["texto"])], [_matricula("sub/matriculas.csv")])
    assert [nome for nome, _ in resultado["ciclo"]] == ["ciclos.csv"]
    assert [nome for nome, _ in resultado["matricula"]] == ["matriculas.csv"]
    assert resultado["ignorados"] == ["nota.txt"]
    assert list(resultado["ciclo"][0][1].columns) == list(COLUNAS_CICLO.values())


@pytest.mark.parametrize("ciclos,matriculas,pasta", [([], [_matricula()], "ciclos"), ([_ciclo()], [], "matrículas")])
def test_ler_pastas_recusa_pasta_sem_csv_antes_de_ler(ciclos, matriculas, pasta):
    with pytest.raises(EnvioInvalido) as excinfo:
        ler_pastas(ciclos, matriculas)
    assert (excinfo.value.arquivo, excinfo.value.motivo) == (pasta, "pasta_vazia")


def test_ler_pastas_recusa_pastas_invertidas_no_primeiro_arquivo():
    with pytest.raises(EnvioInvalido) as excinfo:
        ler_pastas([_matricula("primeiro.csv")], [_ciclo()])
    assert (excinfo.value.arquivo, excinfo.value.motivo) == ("primeiro.csv", "colunas_ausentes")


def test_ler_pastas_processa_csv_em_subpasta():
    resultado = ler_pastas([_ciclo("subpasta/ciclos.csv")], [_matricula(r"subpasta\\matriculas.csv")])
    assert [nome for nome, _ in resultado["ciclo"] + resultado["matricula"]] == ["ciclos.csv", "matriculas.csv"]


def test_ler_pastas_recusa_primeiro_csv_sem_colunas_obrigatorias():
    with pytest.raises(EnvioInvalido) as excinfo:
        ler_pastas([_arquivo("invalido.csv", ["conteudo privado"])], [_matricula()])
    assert (excinfo.value.arquivo, excinfo.value.motivo) == ("invalido.csv", "colunas_ausentes")
    assert "conteudo privado" not in str(excinfo.value)


def test_ler_pastas_traduz_erro_de_leitura_sem_conteudo(monkeypatch):
    def falhar(_bytes, _tipo):
        raise ValueError("leitura_csv")

    monkeypatch.setattr("app.sistec.envio.ler_planilha", falhar)
    with pytest.raises(EnvioInvalido) as excinfo:
        ler_pastas([_ciclo("quebrado.csv")], [_matricula()])
    assert (excinfo.value.arquivo, excinfo.value.motivo) == ("quebrado.csv", "leitura_csv")


def test_campi_ausentes_devolve_cadastrados_sem_ciclo_em_ordem_estavel():
    ciclos = pd.DataFrame({"CO_UNIDADE": ["2", "4", "2"]})
    campi = [{"co_unidade": "1"}, {"co_unidade": "2"}, {"co_unidade": "3"}]

    assert campi_ausentes(ciclos, campi) == ["1", "3"]


def test_campi_nao_cadastrados_devolve_codigos_do_ciclo_em_ordem_estavel():
    ciclos = pd.DataFrame({"CO_UNIDADE": ["2", "4", "3", "4"]})
    campi = [{"co_unidade": "2"}, {"co_unidade": "3"}]

    assert campi_nao_cadastrados(ciclos, campi) == ["4"]


def test_campi_ignoram_cadastro_sem_codigo_de_unidade():
    ciclos = pd.DataFrame({"CO_UNIDADE": ["2"]})
    campi = [{"co_unidade": ""}, {"co_unidade": None}, {"co_unidade": "2"}]

    assert campi_ausentes(ciclos, campi) == []
    assert campi_nao_cadastrados(ciclos, campi) == []


def test_ciclos_vazios_deixam_todos_os_campi_cadastrados_ausentes():
    campi = [{"co_unidade": "1"}, {"co_unidade": "2"}]

    assert campi_ausentes(pd.DataFrame(columns=["CO_UNIDADE"]), campi) == ["1", "2"]


def test_campus_com_todos_ciclos_excluidos_aparece_como_ausente():
    ciclos = pd.DataFrame({"CO_UNIDADE": ["1"], "SITUACAO_CICLO": ["EXCLUÍDO"]})

    assert campi_ausentes(ciclos, [{"co_unidade": "1"}]) == ["1"]


def _ciclos(cidade, nome):
    return pd.DataFrame(
        {
            "CO_UNIDADE": ["1", "1"],
            "MUNICIPIO_UNIDADE": cidade,
            "NOME_UNIDADE_ENSINO": nome,
        }
    )


def test_dados_unidades_do_envio_usa_o_primeiro_valor_nao_vazio():
    """CPR-05 AC1: linha com valor vazio não fecha o campo — vale o primeiro
    valor não vazio na ordem das linhas."""
    ciclos = _ciclos(["", "Santa Maria"], ["", "Campus SM"])

    assert dados_unidades_do_envio(ciclos) == {
        "1": {"cidade": "Santa Maria", "nome_unidade": "Campus SM"}
    }


def test_dados_unidades_do_envio_sem_valor_preenchido_fica_none():
    ciclos = _ciclos(["   ", None], [None, "   "])

    assert dados_unidades_do_envio(ciclos) == {"1": {"cidade": None, "nome_unidade": None}}


def test_dados_unidades_do_envio_separa_cada_unidade():
    ciclos = pd.DataFrame(
        {
            "CO_UNIDADE": ["1", "2", "1", "2"],
            "MUNICIPIO_UNIDADE": ["Alegrete", "Jaguari", "", ""],
            "NOME_UNIDADE_ENSINO": ["Campus Alegrete", None, "", "Campus Jaguari"],
        }
    )

    assert dados_unidades_do_envio(ciclos) == {
        "1": {"cidade": "Alegrete", "nome_unidade": "Campus Alegrete"},
        "2": {"cidade": "Jaguari", "nome_unidade": "Campus Jaguari"},
    }


def test_dados_unidades_do_envio_tolera_df_vazio_ou_sem_as_colunas():
    assert dados_unidades_do_envio(pd.DataFrame(columns=["CO_UNIDADE"])) == {}
    assert dados_unidades_do_envio(pd.DataFrame({"CO_UNIDADE": ["1"]})) == {}


def test_dados_unidades_do_envio_remove_espacos_das_pontas():
    ciclos = _ciclos(["  Santa Maria  ", ""], ["  Campus SM  ", ""])

    assert dados_unidades_do_envio(ciclos) == {
        "1": {"cidade": "Santa Maria", "nome_unidade": "Campus SM"}
    }
