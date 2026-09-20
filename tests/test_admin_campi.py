"""Lista de campi do painel administrativo (DS-62 a DS-85): busca, paginação e telas."""

import pytest

from app.admin_campi import filtrar_e_paginar


def _campi(quantidade):
    return [
        {
            "id_perfil": str(8278800 + i),
            "nome_perfil": f"Perfil {i:02d}",
            "cidade": f"Cidade {i:02d}",
            "nome_unidade": f"Campus {i:02d}",
        }
        for i in range(1, quantidade + 1)
    ]


def test_terceira_pagina_de_10_com_22_campi_tem_2_itens_e_indices_21_a_22():
    pagina = filtrar_e_paginar(_campi(22), "", 3, 10)
    assert len(pagina["itens"]) == 2
    assert pagina["inicio"] == 21
    assert pagina["fim"] == 22
    assert pagina["total"] == 22
    assert pagina["pagina"] == 3
    assert pagina["por_pagina"] == 10


def test_25_por_pagina_com_22_campi_cabe_em_uma_pagina():
    pagina = filtrar_e_paginar(_campi(22), "", 1, 25)
    assert len(pagina["itens"]) == 22
    assert (pagina["inicio"], pagina["fim"], pagina["total"]) == (1, 22, 22)


def test_primeira_e_segunda_pagina_pegam_as_faixas_certas():
    campi = _campi(22)
    primeira = filtrar_e_paginar(campi, "", 1, 10)
    segunda = filtrar_e_paginar(campi, "", 2, 10)
    assert [c["nome_perfil"] for c in primeira["itens"]] == [f"Perfil {i:02d}" for i in range(1, 11)]
    assert [c["nome_perfil"] for c in segunda["itens"]] == [f"Perfil {i:02d}" for i in range(11, 21)]
    assert (segunda["inicio"], segunda["fim"]) == (11, 20)


def test_busca_acha_perfil_cidade_ou_nome_da_unidade_sem_diferenciar_caixa():
    campi = [
        {"id_perfil": "1", "nome_perfil": "Assessor Santa Rosa", "cidade": "X", "nome_unidade": "Y"},
        {"id_perfil": "2", "nome_perfil": "Assessor B", "cidade": "Santa Maria", "nome_unidade": "Y"},
        {"id_perfil": "3", "nome_perfil": "Assessor C", "cidade": "X", "nome_unidade": "Campus Santana"},
        {"id_perfil": "4", "nome_perfil": "Assessor D", "cidade": "Jaguari", "nome_unidade": "Campus Jaguari"},
    ]
    for texto in ("santa", "SANTA", "  Santa  "):
        pagina = filtrar_e_paginar(campi, texto, 1, 10)
        assert [c["id_perfil"] for c in pagina["itens"]] == ["1", "2", "3"]
        assert pagina["total"] == 3


def test_busca_sem_resultado_zera_itens_total_e_indices():
    pagina = filtrar_e_paginar(_campi(22), "zzz", 1, 10)
    assert pagina["itens"] == []
    assert (pagina["total"], pagina["inicio"], pagina["fim"]) == (0, 0, 0)


@pytest.mark.parametrize("por_pagina", [7, "x", 0, -10, None, "100"])
def test_por_pagina_invalido_vira_10(por_pagina):
    assert filtrar_e_paginar(_campi(22), "", 1, por_pagina)["por_pagina"] == 10


@pytest.mark.parametrize("por_pagina,esperado", [(10, 10), (25, 25), (50, 50), ("25", 25)])
def test_por_pagina_valido_e_mantido(por_pagina, esperado):
    assert filtrar_e_paginar(_campi(22), "", 1, por_pagina)["por_pagina"] == esperado


@pytest.mark.parametrize("pagina", [0, -1, "x", None, 99, "4"])
def test_pagina_invalida_ou_alem_do_fim_vira_1(pagina):
    resultado = filtrar_e_paginar(_campi(22), "", pagina, 10)
    assert resultado["pagina"] == 1
    assert (resultado["inicio"], resultado["fim"]) == (1, 10)
