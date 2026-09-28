"""Carrega dados sintéticos do Sistec direto no banco do painel (uso local,
só para testar a interface sem tocar no Sistec real).

Monta a lista de campi, gera as planilhas de ciclo e matrícula de cada um
com `scripts/sintetico.py`, roda o pipeline real de ingestão
(`aplicar_permissao` -> `consolidar` -> `montar_versao_interna` -> `publicar`)
e projeta a lista de campi para o painel público (`aplicar_publico`). Ao fim,
o painel abre com dados publicados, sem precisar do Sistec.

Uso:
    python scripts/seed_sintetico.py
"""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import sintetico
from app.data import campi, instalacao
from app.data.config_store import set_contato_email, set_instituicao
from app.data.ingest import montar_versao_interna
from app.data.schema import DEFAULT_DB_PATH, init_db
from app.data.versoes import aplicar_publico, publicar
from app.sistec.colunas import COLUNAS_CICLO, COLUNAS_MATRICULA, aplicar_permissao
from app.sistec.consolidacao import consolidar

CAMPI = [
    ("101", "Alegrete"),
    ("102", "Frederico Westphalen"),
    ("103", "Jaguari"),
    ("104", "Júlio de Castilhos"),
    ("105", "Panambi"),
    ("106", "Santa Rosa"),
    ("107", "Santo Ângelo"),
    ("108", "Santo Augusto"),
    ("109", "São Borja"),
    ("110", "São Vicente do Sul"),
    ("111", "Uruguaiana"),
]


def _ler(texto, mapa, tipo):
    df_bruto = pd.read_csv(
        io.BytesIO(texto.encode("cp1252")), sep=";", encoding="cp1252", dtype=str, usecols=list(mapa.keys())
    )
    return aplicar_permissao(df_bruto, tipo)


def carregar(db_path=DEFAULT_DB_PATH):
    init_db(db_path)

    set_instituicao(
        nome="Instituto Federal Farroupilha",
        sigla="IFFar",
        site="www.iffarroupilha.edu.br",
        db_path=db_path,
    )
    set_contato_email("pesquisa.institucional@iffarroupilha.edu.br", db_path)

    campi.salvar_captura(
        [
            {
                "id_perfil": f"82788{i:02d}",
                "nome_perfil": (
                    "ASSESSOR DA UNIDADE DE ENSINO - INSTITUTO FEDERAL FARROUPILHA - "
                    f"CÂMPUS {nome.upper()}"
                ),
                "ordem": i,
                "co_unidade": co_unidade,
                "cidade": nome,
                "nome_unidade": f"Campus {nome}",
            }
            for i, (co_unidade, nome) in enumerate(CAMPI, start=1)
        ],
        db_path,
    )

    pares_ciclo = []
    pares_matricula = []
    for co_unidade, nome in CAMPI:
        pares_ciclo.append(_ler(sintetico.csv_ciclo(co_unidade, nome), COLUNAS_CICLO, "ciclo"))
        pares_matricula.append(_ler(sintetico.csv_matricula(co_unidade, nome), COLUNAS_MATRICULA, "matricula"))

    conjunto = consolidar(pares_ciclo, pares_matricula)
    resumo = montar_versao_interna(conjunto, campi_falhos=[], db_path=db_path, ano_base=sintetico.ANO_BASE)
    publicar(db_path)
    aplicar_publico(db_path)
    instalacao.concluir(db_path)

    return resumo


if __name__ == "__main__":
    resumo = carregar()
    print("Carga sintética concluída:", resumo)
