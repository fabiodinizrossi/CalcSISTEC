"""Páginas públicas em Dash no padrão do gov.br DS (DS-06, DS-13, DS-14, DS-17, DS-35, DS-43, DS-44)."""

import importlib

import pytest

from app import app as _app  # noqa: F401  (carrega e registra as páginas)
from arvore_dash import classes, com_classe, componentes, exigir_sem_componente_do_ds_que_precisa_de_js, textos

SEM_DADOS = "Ainda não há dados publicados."


def pagina(nome):
    return importlib.import_module(f"pages.{nome}")


import pandas as pd


def _matriculas_de_teste():
    return pd.DataFrame(
        {
            "co_matricula": [1, 2, 3],
            "status_corrigido": ["CONCLUÍDA", "EM_CURSO", "EM_CURSO"],
            "ano_base": [2026, 2026, 2026],
            "codigo_ciclo_matricula": [10, 10, 11],
            "tipo_programa_curso": ["Regular"] * 3,
            "dt_data_inicio": pd.to_datetime(["2026-02-01"] * 3),
            "codigo_portfolio": ["P1", "P1", "P2"],
            "nome_curso_ajustado": ["Curso A", "Curso A", "Curso B"],
            "tipo_curso_pnp": ["Técnico"] * 3,
            "subtipo_curso": ["Integrado"] * 3,
            "modalidade_ensino": ["Presencial"] * 3,
            "eixo_tecnologico_ajustado": ["Informação"] * 3,
            "carga_horaria_total": [1200, 1200, 800],
            "fec": [1.0, 1.0, 1.0],
            "fech": [1.0, 1.0, 1.0],
            "co_unidade": ["101", "101", "102"],
            "tipo_oferta_curso": ["Integrado"] * 3,
            "categoria_origem_curso": ["Regular"] * 3,
            "cidade": ["Alegrete", "Alegrete", "Jaguari"],
        }
    )


@pytest.fixture
def matriculas_com_dados(monkeypatch):
    pagina_matriculas = pagina("matriculas")
    monkeypatch.setattr(pagina_matriculas, "carregar_matriculas", _matriculas_de_teste)
    monkeypatch.setattr(pagina_matriculas, "ano_base_ativo", lambda: 2026)
    return pagina_matriculas


def _atualizar(pagina_matriculas):
    return pagina_matriculas.atualizar("com_fic", ["campus"], "__todos__", "__todos__", "__todos__")


def test_matriculas_mostra_os_kpis_em_card_figma_com_os_mesmos_numeros(matriculas_com_dados):
    kpis, _ = _atualizar(matriculas_com_dados)
    cartoes = com_classe(kpis, "kpi-figma")
    assert [textos(c) for c in cartoes] == [
        "Cursos 2",
        "Matrículas 3",
        "Ingressantes 2",
        "Matrículas concluídas 1",
        "Matrículas equivalentes 3,00",
    ]


def test_matriculas_poe_cinco_kpis_em_linha_com_titulo_acima_e_destaque_em_todos(matriculas_com_dados):
    kpis, _ = _atualizar(matriculas_com_dados)
    assert len(kpis) == 5
    assert all("kpi-figma" in c.className.split() for c in kpis)
    assert [c.className for c in kpis] == ["kpi-figma kpi-figma--destaque"] * 5
    destaque = kpis[1]
    assert [type(filho).__name__ for filho in destaque.children] == ["Div", "Div"]
    assert destaque.children[0].className == "rotulo"
    assert destaque.children[1].className == "valor"


def test_kpi_estado_textual_nao_herda_os_32px_dos_numeros():
    pagina_matriculas = pagina("matriculas")
    cartao = pagina_matriculas._kpi(
        "Matrículas equivalentes", None, formato="#,0.00", empty_state="dado incompleto"
    )
    assert textos(cartao) == "Matrículas equivalentes dado incompleto"
    assert cartao.children[1].className == "valor valor--texto"


def test_matriculas_mostra_a_tabela_figma_com_total_por_campus(matriculas_com_dados):
    _, matriz = _atualizar(matriculas_com_dados)
    assert matriz.className == "matriz-figma"
    celulas = [[textos(td) for td in componentes(tr) if type(td).__name__ == "Td"] for tr in componentes(matriz) if type(tr).__name__ == "Tr"]
    assert [linha for linha in celulas if linha] == [
        ["Alegrete", "2", "1", "—", "1", "0"],
        ["Jaguari", "1", "0", "—", "1", "0"],
        ["Total", "3", "1", "—", "2", "0"],
    ]


def test_matriculas_monta_hierarquia_na_ordem_em_que_os_campos_foram_marcados(matriculas_com_dados):
    _, matriz = matriculas_com_dados.atualizar(
        "com_fic", ["nome_curso", "campus"], "__todos__", "__todos__", "__todos__"
    )
    linhas = [tr for tr in componentes(matriz) if type(tr).__name__ == "Tr" and getattr(tr, "data-level", None) is not None]
    assert [(getattr(tr, "data-level"), textos(tr)) for tr in linhas] == [
        (0, "Curso A 2 1 — 1 0"),
        (1, "Alegrete 2 1 — 1 0"),
        (0, "Curso B 1 0 — 1 0"),
        (1, "Jaguari 1 0 — 1 0"),
    ]


def test_matriculas_recalcula_totais_dos_pais_e_folhas(matriculas_com_dados):
    base = _matriculas_de_teste().copy()
    base.loc[2, "subtipo_curso"] = "Concomitante"
    matriculas_com_dados.carregar_matriculas = lambda: base
    _, matriz = matriculas_com_dados.atualizar(
        "com_fic", ["campus", "tipo_curso"], "__todos__", "__todos__", "__todos__"
    )
    linhas = [tr for tr in componentes(matriz) if type(tr).__name__ == "Tr" and getattr(tr, "data-level", None) is not None]
    assert [textos(tr) for tr in linhas] == [
        "Alegrete 2 1 — 1 0",
        "Integrado 2 1 — 1 0",
        "Jaguari 1 0 — 1 0",
        "Concomitante 1 0 — 1 0",
    ]
    assert "Total 3 1 — 2 0" in textos(matriz)


def test_ordem_dinamica_remove_e_reinsere_campo_no_fim(matriculas_com_dados):
    ordenar = matriculas_com_dados._ordenar_eixos
    assert ordenar(["campus", "modalidade"], ["campus"]) == ["campus", "modalidade"]
    assert ordenar(["modalidade"], ["campus", "modalidade"]) == ["modalidade"]
    assert ordenar(["campus", "modalidade"], ["modalidade"]) == ["modalidade", "campus"]


def test_matriculas_sem_dimensao_exibe_apenas_total_geral(matriculas_com_dados):
    _, matriz = matriculas_com_dados.atualizar(
        "com_fic", [], "__todos__", "__todos__", "__todos__"
    )
    linhas = [tr for tr in componentes(matriz) if type(tr).__name__ == "Tr" and getattr(tr, "data-level", None) is not None]
    assert linhas == []
    assert "Total geral" in textos(matriz)
    assert "Total 3 1 — 2 0" in textos(matriz)


def test_matriculas_nao_usa_classes_nem_componentes_de_tabela_ou_card_do_bootstrap(matriculas_com_dados):
    kpis, matriz = _atualizar(matriculas_com_dados)
    usadas = classes(kpis) | classes(matriz) | classes(matriculas_com_dados.layout())
    assert not (usadas & {"kpi-row", "table", "table-striped", "card", "card-body", "kpi-card", "table-scroll-wrapper", "br-table", "br-card"})
    for componente in (kpis, matriz):
        assert not [c for c in componentes(componente) if type(c).__name__ in ("Table", "Card", "CardBody") and type(c).__module__.startswith("dash_bootstrap_components")]
        exigir_sem_componente_do_ds_que_precisa_de_js(componente)


def test_matriculas_tabela_vem_em_rolagem_tabela_acessivel(matriculas_com_dados):
    _, matriz = _atualizar(matriculas_com_dados)
    rolagens = com_classe(matriz, "rolagem-tabela")
    assert len(rolagens) == 1
    wrapper = rolagens[0]
    assert wrapper.tabIndex == "0"
    assert wrapper.role == "region"
    assert getattr(wrapper, "aria-label") == "Tabela de matrículas por campus"


def test_matriculas_hierarquica_fica_excluida_da_ordenacao_compartilhada(matriculas_com_dados):
    _, matriz = matriculas_com_dados.atualizar(
        "com_fic", ["campus", "nome_curso"], "__todos__", "__todos__", "__todos__"
    )
    tabelas = [c for c in componentes(matriz) if type(c).__name__ == "Table"]
    assert len(tabelas) == 1
    assert getattr(tabelas[0], "data-sortable", None) == "false"


def test_matriculas_sem_dados_mostra_br_message_info(monkeypatch):
    pagina_matriculas = pagina("matriculas")
    monkeypatch.setattr(pagina_matriculas, "dataset_disponivel", lambda: False)
    layout = pagina_matriculas.layout()
    assert {"br-message", "info"} <= set(layout.className.split())
    assert SEM_DADOS in textos(layout)
    assert "empty-state" not in classes(layout)


def _eficiencia_de_teste():
    return pd.DataFrame(
        {
            "co_matricula": [1, 2, 3, 4, 5],
            "status_corrigido2": ["CONCLUÍDA", "ABANDONO", "EM_CURSO", "CONCLUÍDA", "CONCLUÍDA"],
            "codigo_ciclo_matricula": [10, 10, 10, 11, 11],
            "dt_data_fim_previsto": pd.to_datetime(["2025-12-01"] * 5),
            "co_unidade": ["101", "101", "101", "102", "102"],
            "modalidade_ensino": ["Presencial"] * 5,
            "subtipo_curso": ["Integrado"] * 5,
            "nome_curso_ajustado": ["Curso A", "Curso A", "Curso A", "Curso B", "Curso B"],
            "tipo_oferta_curso": ["Integrado"] * 5,
            "categoria_origem_curso": ["Regular"] * 5,
            "cidade": ["Alegrete", "Alegrete", "Alegrete", "Jaguari", "Jaguari"],
        }
    )


@pytest.fixture
def eficiencia_com_dados(monkeypatch):
    pagina_eficiencia = pagina("eficiencia")
    monkeypatch.setattr(pagina_eficiencia, "carregar_eficiencia", _eficiencia_de_teste)
    monkeypatch.setattr(pagina_eficiencia, "ano_base_ativo", lambda: 2026)
    return pagina_eficiencia


def _atualizar_eficiencia(pagina_eficiencia):
    return pagina_eficiencia.atualizar("com_fic", "campus", "__todos__", "__todos__")


def test_eficiencia_mostra_o_iea_destacado_com_o_mesmo_numero_da_regra_oficial(eficiencia_com_dados):
    kpi, _ = _atualizar_eficiencia(eficiencia_com_dados)
    cartoes = com_classe(kpi, "kpi-figma")
    assert [textos(c) for c in cartoes] == ["IEA (Índice de Eficiência Acadêmica) 0,75"]
    assert cartoes[0].className == "kpi-figma kpi-figma--destaque"


def test_eficiencia_mostra_a_matriz_publica_com_o_iea_de_cada_campus(eficiencia_com_dados):
    _, matriz = _atualizar_eficiencia(eficiencia_com_dados)
    assert matriz.className == "matriz-figma tabela-publica-quadro"
    cabecalhos = [textos(th) for th in componentes(matriz) if type(th).__name__ == "Th"]
    assert cabecalhos == ["Campus", "IEA"]
    celulas = [[textos(td) for td in componentes(tr) if type(td).__name__ == "Td"] for tr in componentes(matriz) if type(tr).__name__ == "Tr"]
    assert [linha for linha in celulas if linha] == [["Alegrete", "0,50"], ["Jaguari", "1,00"]]


def test_eficiencia_layout_poem_contexto_kpi_eixo_tabela_e_filtros_nesta_ordem(eficiencia_com_dados, monkeypatch):
    monkeypatch.setattr(eficiencia_com_dados, "data_ultima_publicacao", lambda: "2026-09-22")
    layout = eficiencia_com_dados.layout()
    filhos = layout.children
    assert layout.className == "painel-dashboard"
    assert [getattr(filho, "className", None) for filho in filhos] == ["cabecalho-pagina", None, "filter-item", None, "card-filtros"]
    assert filhos[1].children.className == "kpis-figma"
    assert "br-radio" in classes(filhos[2])
    assert "Atualizado em 22/09/2026" in textos(filhos[0])


def test_eficiencia_zero_real_e_recorte_vazio_nao_se_confundem(eficiencia_com_dados):
    base = _eficiencia_de_teste().copy()
    base["status_corrigido2"] = "EM_CURSO"
    eficiencia_com_dados.carregar_eficiencia = lambda: base
    kpi_zero, _ = _atualizar_eficiencia(eficiencia_com_dados)
    kpi_vazio, aviso = eficiencia_com_dados.atualizar("sem_fic", "campus", "Inexistente", "__todos__")

    assert "0,00" in textos(kpi_zero)
    assert textos(kpi_vazio) == ""
    assert "Sem dados para o eixo selecionado." in textos(aviso)


def test_eficiencia_nao_usa_componentes_de_tabela_do_bootstrap(eficiencia_com_dados):
    kpi, matriz = _atualizar_eficiencia(eficiencia_com_dados)
    assert not (classes(kpi) | classes(matriz)) & {"table", "table-striped", "card", "card-body", "table-scroll-wrapper"}
    assert not [c for c in componentes(matriz) if type(c).__module__.startswith("dash_bootstrap_components")]
    exigir_sem_componente_do_ds_que_precisa_de_js(matriz)


def test_eficiencia_sem_dados_mostra_br_message_info(monkeypatch):
    pagina_eficiencia = pagina("eficiencia")
    monkeypatch.setattr(pagina_eficiencia, "dataset_disponivel", lambda: False)
    layout = pagina_eficiencia.layout()
    assert {"br-message", "info"} <= set(layout.className.split())
    assert SEM_DADOS in textos(layout)


def _matriculas_para_evasao():
    base = _matriculas_de_teste().iloc[:1]
    linhas = []
    for cidade, co_unidade, status in (
        [("Alta", "1", s) for s in ("ABANDONO", "EM_CURSO")]
        + [("Media", "2", s) for s in ("ABANDONO", "EM_CURSO", "EM_CURSO", "EM_CURSO", "EM_CURSO")]
        + [("Baixa", "3", s) for s in ("EM_CURSO", "EM_CURSO", "EM_CURSO")]
    ):
        linha = base.iloc[0].to_dict()
        linha.update({"cidade": cidade, "co_unidade": co_unidade, "status_corrigido": status, "co_matricula": len(linhas) + 1})
        linhas.append(linha)
    return pd.DataFrame(linhas)


@pytest.fixture
def evasao_com_dados(monkeypatch):
    pagina_evasao = pagina("evasao")
    monkeypatch.setattr(pagina_evasao, "carregar_matriculas", _matriculas_para_evasao)
    monkeypatch.setattr(pagina_evasao, "ano_base_ativo", lambda: 2026)
    return pagina_evasao


def _celulas_de_evasao(tabela):
    return {
        textos(tds[0]): (textos(tds[1]), getattr(tds[1], "className", None))
        for tds in (
            [td for td in componentes(tr) if type(td).__name__ == "Td"]
            for tr in componentes(tabela)
            if type(tr).__name__ == "Tr"
        )
        if tds
    }


def test_evasao_mostra_percentual_e_texto_da_faixa_com_a_classe_de_cor(evasao_com_dados):
    tabela = evasao_com_dados.atualizar("com_fic", "__todos__", "__todos__")
    assert _celulas_de_evasao(tabela) == {
        "Alta": ("50,0% (Alta)", "evasao-alta"),
        "Media": ("20,0% (Média)", "evasao-media"),
        "Baixa": ("0,0% (Baixa)", "evasao-baixa"),
    }


def test_evasao_e_br_table_sem_dbc_nem_wrapper_antigo(evasao_com_dados):
    tabela = evasao_com_dados.atualizar("com_fic", "__todos__", "__todos__")
    assert tabela.className == "br-table"
    assert "table-scroll-wrapper" not in classes(tabela)
    assert not [c for c in componentes(tabela) if type(c).__module__.startswith("dash_bootstrap_components")]
    exigir_sem_componente_do_ds_que_precisa_de_js(tabela)


def test_evasao_sem_dados_mostra_br_message_info(monkeypatch):
    pagina_evasao = pagina("evasao")
    monkeypatch.setattr(pagina_evasao, "dataset_disponivel", lambda: False)
    layout = pagina_evasao.layout()
    assert {"br-message", "info"} <= set(layout.className.split())
    assert SEM_DADOS in textos(layout)


@pytest.fixture
def percentuais_com_dados(monkeypatch):
    pagina_percentuais = pagina("percentuais_legais")
    monkeypatch.setattr(pagina_percentuais, "carregar_matriculas", _matriculas_de_teste)
    monkeypatch.setattr(pagina_percentuais, "ano_base_ativo", lambda: 2026)
    return pagina_percentuais


def test_percentuais_mostra_os_3_medidores_em_br_card_com_valor_meta_e_situacao_em_texto(percentuais_com_dados):
    from app.domain.percentuais_legais import (
        META_PROEJA,
        META_PROFESSORES,
        META_TECNICO,
        percentual_proeja,
        percentual_professores,
        percentual_tecnico,
    )

    base = _matriculas_de_teste().assign(quantidade_matriculas=1)
    esperados = [
        ("Técnico", percentual_tecnico(base), META_TECNICO),
        ("Formação de Professores", percentual_professores(base), META_PROFESSORES),
        ("PROEJA", percentual_proeja(base), META_PROEJA),
    ]
    medidores, _, _ = percentuais_com_dados.atualizar("campus", "__todos__", "__todos__")
    cartoes = [c for coluna in medidores for c in com_classe(coluna, "br-card")]
    assert len(cartoes) == 3
    for cartao, (rotulo, valor, meta) in zip(cartoes, esperados):
        situacao = "Acima da meta" if valor >= meta else "Abaixo da meta"
        assert textos(cartao) == f"{rotulo} {valor:.1%} {situacao} Meta: {meta:.0%}"


def test_percentuais_poe_os_medidores_em_colunas_que_comecam_em_col_12_sem_card_do_bootstrap(percentuais_com_dados):
    medidores, kpi, _ = percentuais_com_dados.atualizar("campus", "__todos__", "__todos__")
    assert len(medidores) == 3
    for coluna in medidores:
        assert "col-12" in coluna.className.split()
    assert not (classes(medidores) | classes(kpi)) & {"gauge-card", "card", "card-body", "gauge-row"}
    assert not [c for c in componentes(medidores) if type(c).__module__.startswith("dash_bootstrap_components")]
    exigir_sem_componente_do_ds_que_precisa_de_js(medidores)


def test_percentuais_com_programa_filtrado_mostra_o_aviso_proeja_em_br_message_warning(percentuais_com_dados):
    _, _, aviso = percentuais_com_dados.atualizar("campus", "__todos__", "Regular")
    assert {"br-message", "warning"} <= set(aviso.className.split())
    assert "Atenção: o filtro de Programa Associado pode distorcer o percentual PROEJA." in textos(aviso)


def test_percentuais_sem_filtro_de_programa_nao_mostra_o_aviso(percentuais_com_dados):
    _, _, aviso = percentuais_com_dados.atualizar("campus", "__todos__", "__todos__")
    assert not aviso


def test_percentuais_sem_dados_mostra_br_message_info(monkeypatch):
    pagina_percentuais = pagina("percentuais_legais")
    monkeypatch.setattr(pagina_percentuais, "dataset_disponivel", lambda: False)
    layout = pagina_percentuais.layout()
    assert {"br-message", "info"} <= set(layout.className.split())
    assert SEM_DADOS in textos(layout)
