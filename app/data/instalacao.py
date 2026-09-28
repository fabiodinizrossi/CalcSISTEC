"""Instalação: primeira configuração e reinício do zero.

O mesmo programa serve qualquer instituição, então nada de identidade vem
fixo no código: na primeira execução o assistente (`/admin/instalacao`) pede
o nome da instituição e a lista de campi. A lista é cadastrada à mão: colada de
uma vez (`identificador ; nome do perfil`) ou campus a campus em Configurações.
O identificador de perfil é o campo `tipo` do Sistec, que a pessoa lê na tela de
seleção de perfil com o próprio login.

`resetar` devolve tudo ao estado de instalação nova — pensado para a troca da
pessoa responsável pelo setor ou para levar o programa a outra instituição.
"""

from app.data import config_store
from app.data.schema import DEFAULT_DB_PATH, get_connection

CHAVE_CONCLUIDA = "instalacao_concluida"

# Dados coletados/derivados do Sistec. Os fatores (FEC/FECH) ficam fora: são
# da regra nacional da PNP, não da instituição.
_TABELAS_DE_DADOS = (
    "matriculas_eficiencia",
    "matriculas",
    "ciclos",
    "cursos",
    "campus",
    "interna_matriculas_eficiencia",
    "interna_matriculas",
    "interna_ciclos",
    "interna_cursos",
    "interna_campus",
    "anterior_matriculas_eficiencia",
    "anterior_matriculas",
    "anterior_ciclos",
    "anterior_cursos",
    "anterior_campus",
    "campi_sistec",
    "historico",
)


def concluida(db_path=DEFAULT_DB_PATH):
    return config_store.get_valor(CHAVE_CONCLUIDA, "", db_path) == "1"


def concluir(db_path=DEFAULT_DB_PATH):
    config_store.set_valor(CHAVE_CONCLUIDA, "1", db_path)


def pendencias(db_path=DEFAULT_DB_PATH):
    """O que ainda falta para a instalação fazer sentido — mostrado no
    assistente, sem impedir de concluir (a lista de campi pode ser lida depois,
    na primeira atualização)."""
    from app.data.campi import listar_campi

    faltando = []
    if not config_store.get_instituicao_nome(db_path):
        faltando.append("nome da instituição")
    if not listar_campi(db_path):
        faltando.append("lista de campi")
    return faltando


def resetar(db_path=DEFAULT_DB_PATH, apagar_dados=True):
    """Volta ao estado de instalação nova: identidade da instituição, lista de
    campi e (por padrão) os dados baixados e publicados. O ano-base e a tabela
    de fatores são preservados."""
    config_store.reset_instituicao(db_path)
    config_store.reset_contato_email(db_path)
    config_store.reset_logo(db_path)
    config_store.reset_qtd_perfis(db_path)
    config_store.reset_valor(CHAVE_CONCLUIDA, db_path)

    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        tabelas = _TABELAS_DE_DADOS if apagar_dados else ("campi_sistec", "interna_campus")
        for tabela in tabelas:
            conn.execute(f"DELETE FROM {tabela}")
        if apagar_dados:
            conn.execute(
                "UPDATE estado_versoes SET rev_interna = 0, rev_publicada = NULL, rev_anterior = NULL, "
                "interna_gravada_em = NULL, publicada_em = NULL, publicada_por = NULL WHERE id = 1"
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
