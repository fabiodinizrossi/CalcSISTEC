"""Testes da página Dash da prévia (`previa-paginas-publicas`, T16):
`app/pages/previa.py` valida o contexto e chama a página pública certa, com a
faixa "Prévia não publicada", a navegação entre as quatro páginas e os avisos
do envio. Contexto inválido devolve "Prévia indisponível"; falha de render
registra `registrar_falha_pagina` (PVP-01/PVP-02/PVP-05/PVP-09).
"""

import importlib
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arvore_dash import textos  # noqa: E402
from app import app as _app  # noqa: E402, F401
from app.data.ingest import preparar_versao  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402

previa = importlib.import_module("pages.previa")


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()
    yield
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "previa.db")
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


def _envio_com_previa(db_path, monkeypatch):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')"
        )
        conn.commit()
    finally:
        conn.close()

    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id="sessao-A"
    )
    execucoes.registrar_leitura(envio, _leitura_envio())
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)

    # cada página importou `sessao_id_atual` por nome no módulo; sem request
    # context nos testes, todos precisam devolver a sessão dona.
    modulos = [
        previa,
        importlib.import_module("pages.matriculas"),
        importlib.import_module("pages.eficiencia"),
        importlib.import_module("pages.evasao"),
        importlib.import_module("pages.percentuais_legais"),
    ]
    for modulo in modulos:
        monkeypatch.setattr(modulo, "sessao_id_atual", lambda: "sessao-A")
    return envio


def test_slug_invalido_indisponivel():
    layout = previa.layout(execucao_id="x", pagina="nao-existe")
    assert "Prévia indisponível" in textos(layout)
    assert "Prévia não publicada" not in textos(layout)


def test_execucao_perdida_indisponivel(monkeypatch):
    monkeypatch.setattr(previa, "sessao_id_atual", lambda: "sessao-A")
    layout = previa.layout(execucao_id="nao-existe", pagina="matriculas")
    assert "Prévia indisponível" in textos(layout)


def test_sessao_alheia_indisponivel(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    monkeypatch.setattr(previa, "sessao_id_atual", lambda: "sessao-B")
    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")
    assert "Prévia indisponível" in textos(layout)
    assert "Prévia não publicada" not in textos(layout)


def test_layout_matriculas_renderiza(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")
    assert layout.className == "previa-pagina"
    assert "Prévia não publicada" in textos(layout)
    assert layout.children[-1].className == "painel-landing"


def test_layout_eficiencia_renderiza(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    layout = previa.layout(execucao_id=envio.id, pagina="eficiencia")
    assert layout.children[-1].className == "painel-dashboard"


def test_layout_evasao_renderiza(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    layout = previa.layout(execucao_id=envio.id, pagina="evasao")
    assert layout.children[-1].className == "painel-dashboard"


def test_layout_percentuais_renderiza(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    layout = previa.layout(execucao_id=envio.id, pagina="percentuais-legais")
    assert layout.children[-1].className == "painel-dashboard"


def test_layout_mostra_avisos(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    envio.campi_falhos = {"U2"}
    envio.campi_cadastrados_automaticamente = ["U3"]
    envio.matriculas_orfas = 2
    envio.arquivos_ignorados = ["x.txt"]

    texto = textos(previa.layout(execucao_id=envio.id, pagina="matriculas"))

    assert "Unidades com dados preservados: U2." in texto
    assert "Unidades cadastradas pelo envio: U3." in texto
    assert "2 matrícula(s) órfã(s)." in texto
    assert "Arquivos ignorados: x.txt." in texto


def _resposta_roteamento(cliente, execucao_id, pagina):
    """PVP-01: bate no roteamento de verdade do Dash Pages (`path_template`),
    não em `previa.layout()` direto — era o que deixava toda URL de prévia
    cair em "404 - Page not found".

    O corpo do `POST` é montado a partir do próprio `callback_map`: o Dash 4
    registra o roteador de páginas só na primeira requisição ao servidor
    (`enable_pages`), e usa uma chave de saída concatenada quando o callback
    tem mais de um `Output`.
    """
    cliente.get("/")  # primeira requisição: o Dash registra o roteador de páginas
    chaves = [chave for chave in _app.app.callback_map if "_pages_content.children" in chave]
    assert chaves, "roteador de páginas do Dash não registrado"
    registro = _app.app.callback_map[chaves[0]]

    valores = {
        ("_pages_location", "pathname"): f"/admin/previa/{execucao_id}/{pagina}",
        ("_pages_location", "search"): "",
    }
    return cliente.post(
        "/_dash-update-component",
        json={
            "output": chaves[0],
            "inputs": [
                {
                    "id": entrada.component_id,
                    "property": entrada.component_property,
                    "value": valores.get((entrada.component_id, entrada.component_property)),
                }
                for entrada in registro["raw_inputs"]
            ],
            "outputs": [
                {"id": saida.component_id, "property": saida.component_property}
                for saida in registro["output"]
            ],
            "changedPropIds": ["_pages_location.pathname"],
        },
    )


def _conteudo_da_pagina(resposta):
    corpo = resposta.get_json()["response"]["_pages_content"]["children"]
    return json.dumps(corpo, ensure_ascii=False)


def test_roteamento_real_abre_a_previa(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    cliente = _app.server.test_client()

    resposta = _resposta_roteamento(cliente, envio.id, "matriculas")

    assert resposta.status_code == 200
    texto = _conteudo_da_pagina(resposta)
    assert "Page not found" not in texto and "404" not in texto
    assert "Prévia não publicada" in texto


def test_roteamento_real_slug_invalido_nao_e_404(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    cliente = _app.server.test_client()

    resposta = _resposta_roteamento(cliente, envio.id, "nao-existe")

    assert resposta.status_code == 200
    texto = _conteudo_da_pagina(resposta)
    assert "Page not found" not in texto and "404" not in texto
    assert "Prévia indisponível" in texto


def test_layout_falha_render_registra(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)
    modulo_matriculas = importlib.import_module("pages.matriculas")

    def _explodir(preview_id=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(modulo_matriculas, "layout", _explodir)

    layout = previa.layout(execucao_id=envio.id, pagina="matriculas")

    assert "Não foi possível renderizar a página Matrículas." in textos(layout)
    assert execucoes.paginas_com_falha(envio) == ["matriculas"]
