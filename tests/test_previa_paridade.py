"""Suíte de paridade da prévia (`previa-paginas-publicas`, T24): para os mesmos
CSVs, a fonte candidata da prévia e a versão publicada entregam os mesmos
dados, indicadores, linhas de tabela e filtros nas quatro páginas. Cobre campus
preservado, `RISK-002` (vazio/NaN/data nula), ausência de publicação inicial e
o ano-base de `config` (PVP-04/PVP-05/PVP-06).
"""

import importlib
import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arvore_dash import textos  # noqa: E402
from app import app as _app  # noqa: E402, F401
from app.data import consulta, versoes  # noqa: E402
from app.data.ingest import preparar_versao  # noqa: E402
from app.data.previa import abrir_fonte_previa  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402

matriculas = importlib.import_module("pages.matriculas")
eficiencia = importlib.import_module("pages.eficiencia")
evasao = importlib.import_module("pages.evasao")
percentuais = importlib.import_module("pages.percentuais_legais")


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    yield
    execucoes._REGISTRO.clear()


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "paridade.db")
    init_db(caminho)
    return caminho


def _linha_ciclo(co_unidade, codigo, portfolio, nome="TÉCNICO EM X", **overrides):
    base = {
        "CODIGO_CICLO_MATRICULA": codigo,
        "CO_UNIDADE": co_unidade,
        "CÓDIGO DO PORTFÓLIO": portfolio,
        "NOME_CURSO": nome,
        "TIPO_CURSO": "TECNICO",
        "CARGA_HORARIA_TOTAL": 1200,
        "MODALIDADE_ENSINO": "PRESENCIAL",
        "OFERTA": "ANUAL",
        "EIXO_TECNOLOGICO": "EIXO1",
        "TIPO_PROGRAMA_CURSO": "REGULAR",
        "DT_DATA_INICIO": "2026-01-01",
        "DT_DATA_FIM_PREVISTO": "2025-12-31",
        "STATUS_CICLO": "ATIVO",
        "SITUACAO_CICLO": "ATIVO",
    }
    base.update(overrides)
    return base


def _linha_matricula(co_unidade, codigo, co_matricula):
    return {
        "CO_MATRICULA": co_matricula,
        "CODIGO_CICLO_MATRICULA": codigo,
        "STATUS_MATRICULA_SISTEC": "EM_CURSO",
        "MES_OCORRENCIA_CORRIGIDO": "2026-01-01",
    }


def _campus():
    return pd.DataFrame(
        [
            {"co_unidade": "U1", "cidade": "Santa Maria", "nome_unidade": "Campus SM"},
            {"co_unidade": "U2", "cidade": "Jaguari", "nome_unidade": "Campus Jaguari"},
        ]
    )


def _conjunto_dois_campi(com_nulo=False):
    ciclos = [
        _linha_ciclo("U1", "C1", "P1", nome="TÉCNICO EM X"),
        _linha_ciclo("U2", "C2", "P2", nome="TÉCNICO EM Y"),
    ]
    if com_nulo:
        ciclos[0] = _linha_ciclo("U1", "C1", "P1", nome="TÉCNICO EM X", DT_DATA_INICIO=None, DT_DATA_FIM_PREVISTO=None)
    matriculas = [
        _linha_matricula("U1", "C1", "M1"),
        _linha_matricula("U2", "C2", "M2"),
    ]
    return consolidar([pd.DataFrame(ciclos)], [pd.DataFrame(matriculas)])


def _publicar_os_mesmos_dados(db_path, candidato):
    # CPR-06: a semente de campus vai para `interna_campus` — `publicar` passa
    # a copiar essa tabela para `campus` (antes dela, quem escrevia `campus`
    # era só `aplicar_publico`, e a semente ia direto na tabela publicada).
    conn = get_connection(db_path)
    try:
        _campus().to_sql("interna_campus", conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()
    versoes.salvar_interna(candidato["tabelas"], db_path)
    versoes.publicar(db_path)


def test_paridade_matriculas_previa_vs_publicada(db_path):
    candidato = preparar_versao(_conjunto_dois_campi(), (), db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    conn = fonte.abrir_leitura()
    try:
        da_previa = consulta.carregar_matriculas(conn=conn)
    finally:
        conn.close()
    fonte.fechar()
    do_publico = consulta.carregar_matriculas(db_path)

    pd.testing.assert_frame_equal(da_previa.reset_index(drop=True), do_publico.reset_index(drop=True))


def test_paridade_eficiencia_previa_vs_publicada(db_path):
    candidato = preparar_versao(_conjunto_dois_campi(), (), db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    conn = fonte.abrir_leitura()
    try:
        da_previa = consulta.carregar_eficiencia(conn=conn)
    finally:
        conn.close()
    fonte.fechar()
    do_publico = consulta.carregar_eficiencia(db_path)

    pd.testing.assert_frame_equal(da_previa.reset_index(drop=True), do_publico.reset_index(drop=True))


def test_paridade_campus_preservado(db_path):
    # U1 não vem no envio -> preservado; a prévia precisa trazer os dados de U1
    conjunto = _conjunto_dois_campi()
    conjunto["ciclos"] = conjunto["ciclos"][conjunto["ciclos"]["CO_UNIDADE"] != "U1"]
    conjunto["matriculas"] = conjunto["matriculas"][conjunto["matriculas"]["CODIGO_CICLO_MATRICULA"] != "C1"]

    # semente: grava U1 na interna antes
    _publicar_os_mesmos_dados(db_path, preparar_versao(_conjunto_dois_campi(), (), db_path=db_path, ano_base=2026))

    candidato = preparar_versao(conjunto, ["U1"], db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)

    conn = fonte.abrir_leitura()
    try:
        da_previa = consulta.carregar_matriculas(conn=conn)
    finally:
        conn.close()
    fonte.fechar()

    cidades = set(da_previa["cidade"])
    assert cidades == {"Santa Maria", "Jaguari"}  # U1 preservado + U2 novo


def test_paridade_risco_002_nan_e_data_nula(db_path):
    candidato = preparar_versao(_conjunto_dois_campi(com_nulo=True), (), db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    conn = fonte.abrir_leitura()
    try:
        da_previa = consulta.carregar_matriculas(conn=conn)
    finally:
        conn.close()
    fonte.fechar()
    do_publico = consulta.carregar_matriculas(db_path)

    # data nula não diverge: a linha com dt_data_inicio nulo aparece igual nos dois lados
    pd.testing.assert_frame_equal(da_previa.reset_index(drop=True), do_publico.reset_index(drop=True))
    assert da_previa["dt_data_inicio"].isna().any()  # o nulo foi preservado


def test_ano_base_da_previa_e_o_de_config(db_path):
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE config SET valor = '2027' WHERE chave = 'ano_base'")
        conn.commit()
    finally:
        conn.close()

    candidato = preparar_versao(_conjunto_dois_campi(), (), db_path=db_path)  # ano_base=None lê config

    assert candidato["ano_base"] == 2027
    assert candidato["assinatura_origem"]["ano_base"] == 2027


def test_previa_sem_publicacao_inicial_renderiza_quatro_paginas(db_path, monkeypatch):
    # banco sem publicação: nenhuma página de prévia mostra a mensagem pública de vazio
    candidato = preparar_versao(_conjunto_dois_campi(), (), db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)

    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["c.csv"], ["m.csv"], sessao_id="sessao-A")
    execucoes.registrar_leitura(envio, {
        "ciclo": [("c.csv", pd.DataFrame([_linha_ciclo("U1", "C1", "P1")]))],
        "matricula": [("m.csv", pd.DataFrame([_linha_matricula("U1", "C1", "M1")]))],
    })
    execucoes.abrir_previa(envio, candidato, db_path=db_path)

    for pagina in (matriculas, eficiencia, evasao, percentuais):
        monkeypatch.setattr(pagina, "sessao_id_atual", lambda: "sessao-A")
        layout = pagina.layout(preview_id=envio.id)
        assert "Ainda não há dados publicados." not in textos(layout), pagina.__name__
        assert layout.className in ("painel-landing", "painel-dashboard"), pagina.__name__

    execucoes.liberar_previa(envio)
    fonte.fechar()


def _comparar_pagina(pagina, args, carregar, envio_id, db_path, monkeypatch):
    monkeypatch.setattr(pagina, "sessao_id_atual", lambda: "sessao-A")
    da_previa = pagina.atualizar(*args, preview_id=envio_id)

    for atributo, func in carregar.items():
        monkeypatch.setattr(pagina, atributo, func)
    monkeypatch.setattr(pagina, "ano_base_ativo", lambda: 2026)
    do_publico = pagina.atualizar(*args, preview_id=None)

    return da_previa, do_publico


def _textos_de(saida):
    if isinstance(saida, tuple):
        return [textos(parte) for parte in saida]
    return textos(saida)


def test_paridade_kpis_das_quatro_paginas(db_path, monkeypatch):
    candidato = preparar_versao(_conjunto_dois_campi(), (), db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["c.csv"], ["m.csv"], sessao_id="sessao-A")
    execucoes.registrar_leitura(envio, {
        "ciclo": [("c.csv", pd.DataFrame([_linha_ciclo("U1", "C1", "P1")]))],
        "matricula": [("m.csv", pd.DataFrame([_linha_matricula("U1", "C1", "M1")]))],
    })
    execucoes.abrir_previa(envio, candidato, db_path=db_path)

    casos = [
        (matriculas, ("com_fic", ["campus"], "__todos__", "__todos__", "__todos__"), {"carregar_matriculas": lambda: consulta.carregar_matriculas(db_path)}),
        (eficiencia, ("sem_fic", ["campus"], "__todos__", "__todos__"), {"carregar_eficiencia": lambda: consulta.carregar_eficiencia(db_path)}),
        (evasao, ("sem_fic", ["campus"], "__todos__", "__todos__"), {"carregar_matriculas": lambda: consulta.carregar_matriculas(db_path)}),
        (percentuais, ("campus", "__todos__", "__todos__"), {"carregar_matriculas": lambda: consulta.carregar_matriculas(db_path)}),
    ]

    for pagina, args, carregar in casos:
        da_previa, do_publico = _comparar_pagina(pagina, args, carregar, envio.id, db_path, monkeypatch)
        assert _textos_de(da_previa) == _textos_de(do_publico), pagina.__name__

    execucoes.liberar_previa(envio)
    fonte.fechar()


def test_paridade_filtros_das_quatro_paginas(db_path):
    candidato = preparar_versao(_conjunto_dois_campi(), (), db_path=db_path, ano_base=2026)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    conn = fonte.abrir_leitura()
    try:
        da_previa = consulta.carregar_matriculas(conn=conn)
    finally:
        conn.close()
    fonte.fechar()
    do_publico = consulta.carregar_matriculas(db_path)

    for coluna in ("cidade", "tipo_curso_pnp", "tipo_programa_curso"):
        assert sorted(da_previa[coluna].dropna().unique()) == sorted(do_publico[coluna].dropna().unique()), coluna
