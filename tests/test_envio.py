"""Contratos do leitor de pastas enviadas pelo administrador."""

import io

import pytest
from werkzeug.datastructures import FileStorage

from app.sistec.colunas import COLUNAS_CICLO, COLUNAS_MATRICULA
from app.sistec.envio import EnvioInvalido, ler_pastas, nome_seguro


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
