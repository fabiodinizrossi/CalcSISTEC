"""Leitura do dataset ativo para consumo por `app/domain/*` e `app/pages/*`.

É a cola entre o domínio e o armazenamento: cada função de `app/domain/*`
recebe `DataFrame` como parâmetro explícito, e algo precisa montá-lo a partir
do SQLite antes de chamar essas funções.
"""

import pandas as pd

from app.data.schema import DEFAULT_DB_PATH, get_connection


def dataset_disponivel(db_path=DEFAULT_DB_PATH, conn=None):
    """`conn` explícita (fonte da prévia) faz a leitura sem abrir nem
    fechar conexão própria nem tocar `DEFAULT_DB_PATH`; sem ela, o caminho é o
    banco publicado, como antes."""
    if conn is not None:
        return conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0] > 0
    conn = get_connection(db_path)
    try:
        n = conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0]
        return n > 0
    finally:
        conn.close()


def data_ultima_publicacao(db_path=DEFAULT_DB_PATH, conn=None):
    """Timestamp da última publicação (`estado_versoes.publicada_em`), usado
    pela página inicial no rótulo "Atualizado em". Com `conn` explícita (fonte
    da prévia), `publicada_em` fica vazio e o carimbo é omitido."""
    if conn is not None:
        row = conn.execute("SELECT publicada_em FROM estado_versoes WHERE id = 1").fetchone()
        return row[0] if row else None
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT publicada_em FROM estado_versoes WHERE id = 1").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def ano_base_ativo(db_path=DEFAULT_DB_PATH, conn=None):
    """Ano-base como único ponto de configuração. Com `conn`
    explícita, lê `config` da fonte da prévia (o ano-base do candidato)."""
    if conn is not None:
        row = conn.execute("SELECT valor FROM config WHERE chave='ano_base'").fetchone()
        return int(row[0]) if row else None
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave='ano_base'").fetchone()
        return int(row[0]) if row else None
    finally:
        conn.close()


def carregar_matriculas(db_path=DEFAULT_DB_PATH, conn=None):
    """Base consolidada de `matriculas` (grão já aplicado na ingestão) com
    curso/ciclo/campus já juntados — pronta para `app/domain/matriculas.py` e
    `app/domain/percentuais_legais.py`.

    Com `conn` explícita (fonte da prévia), roda o mesmo SQL e os
    mesmos `parse_dates` contra ela, sem abrir nem fechar conexão própria."""
    if conn is not None:
        return pd.read_sql_query(
            """
            SELECT m.co_matricula, m.status_corrigido, m.ano_base,
                   m.mes_ocorrencia_corrigido,
                   c.codigo_ciclo_matricula, c.tipo_programa_curso, c.dt_data_inicio,
                   cu.codigo_portfolio, cu.nome_curso_ajustado, cu.tipo_curso_pnp,
                   cu.subtipo_curso, cu.modalidade_ensino, cu.eixo_tecnologico_ajustado,
                   cu.carga_horaria_total, cu.fec, cu.fech, cu.co_unidade,
                   cu.tipo_oferta_curso, cu.categoria_origem_curso,
                   camp.cidade
            FROM matriculas m
            JOIN ciclos c ON c.codigo_ciclo_matricula = m.codigo_ciclo_matricula
            JOIN cursos cu ON cu.codigo_portfolio = c.codigo_portfolio
            JOIN campus camp ON camp.co_unidade = cu.co_unidade
            """,
            conn,
            parse_dates=["dt_data_inicio"],
        )
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(
            """
            SELECT m.co_matricula, m.status_corrigido, m.ano_base,
                   m.mes_ocorrencia_corrigido,
                   c.codigo_ciclo_matricula, c.tipo_programa_curso, c.dt_data_inicio,
                   cu.codigo_portfolio, cu.nome_curso_ajustado, cu.tipo_curso_pnp,
                   cu.subtipo_curso, cu.modalidade_ensino, cu.eixo_tecnologico_ajustado,
                   cu.carga_horaria_total, cu.fec, cu.fech, cu.co_unidade,
                   cu.tipo_oferta_curso, cu.categoria_origem_curso,
                   camp.cidade
            FROM matriculas m
            JOIN ciclos c ON c.codigo_ciclo_matricula = m.codigo_ciclo_matricula
            JOIN cursos cu ON cu.codigo_portfolio = c.codigo_portfolio
            JOIN campus camp ON camp.co_unidade = cu.co_unidade
            """,
            conn,
            parse_dates=["dt_data_inicio"],
        )
    finally:
        conn.close()


def carregar_eficiencia(db_path=DEFAULT_DB_PATH, conn=None):
    """Base consolidada de `matriculas_eficiencia` com `dt_data_fim_previsto`
    do ciclo já junto — pronta para `app/domain/eficiencia.py`. Com `conn`
    explícita, roda o mesmo SQL contra a fonte da prévia."""
    if conn is not None:
        return pd.read_sql_query(
            """
            SELECT e.co_matricula, e.status_corrigido2,
                   c.codigo_ciclo_matricula, c.dt_data_fim_previsto,
                   cu.co_unidade, cu.modalidade_ensino, cu.subtipo_curso,
                   cu.nome_curso_ajustado, cu.tipo_oferta_curso,
                   cu.categoria_origem_curso, camp.cidade
            FROM matriculas_eficiencia e
            JOIN ciclos c ON c.codigo_ciclo_matricula = e.codigo_ciclo_matricula
            JOIN cursos cu ON cu.codigo_portfolio = c.codigo_portfolio
            JOIN campus camp ON camp.co_unidade = cu.co_unidade
            """,
            conn,
            parse_dates=["dt_data_fim_previsto"],
        )
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(
            """
            SELECT e.co_matricula, e.status_corrigido2,
                   c.codigo_ciclo_matricula, c.dt_data_fim_previsto,
                   cu.co_unidade, cu.modalidade_ensino, cu.subtipo_curso,
                   cu.nome_curso_ajustado, cu.tipo_oferta_curso,
                   cu.categoria_origem_curso, camp.cidade
            FROM matriculas_eficiencia e
            JOIN ciclos c ON c.codigo_ciclo_matricula = e.codigo_ciclo_matricula
            JOIN cursos cu ON cu.codigo_portfolio = c.codigo_portfolio
            JOIN campus camp ON camp.co_unidade = cu.co_unidade
            """,
            conn,
            parse_dates=["dt_data_fim_previsto"],
        )
    finally:
        conn.close()
