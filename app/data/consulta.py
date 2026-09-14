"""BC-01/consulta: leitura do dataset ativo para consumo por `app/domain/*` e
`app/pages/*`.

Não faz parte da árvore aprovada em `target_architecture.md` §"Honra à
topologia escolhida" (que só lista `ingest.py`/`validators.py`/`correction.py`
em `app/data/*`, cobrindo apenas a escrita do dataset). É glue necessária para
materializar a seta `Domain --> Store` do diagrama de `target_architecture.md`
— cada função de `app/domain/*` recebe `DataFrame` como parâmetro explícito
(`target_domain_model.md`), e algo precisa montá-lo a partir do SQLite antes
de chamar essas funções. Implementado na Tarefa 09 (BC-04), por ser onde essa
necessidade concretamente aparece pela primeira vez.
"""

import pandas as pd

from app.data.schema import DEFAULT_DB_PATH, get_connection


def dataset_disponivel(db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        n = conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0]
        return n > 0
    finally:
        conn.close()


def data_ultimo_upload_valido(db_path=DEFAULT_DB_PATH):
    """BR-MIGRAR-015: "atualizado em" derivado do timestamp real do último
    upload válido, nunca uma string fixa editada manualmente."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT uploaded_at FROM uploads_log WHERE status='valido' ORDER BY uploaded_at DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def ano_base_ativo(db_path=DEFAULT_DB_PATH):
    """BR-MIGRAR-016: ano-base como único ponto de configuração."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave='ano_base'").fetchone()
        return int(row[0]) if row else None
    finally:
        conn.close()


def carregar_matriculas(db_path=DEFAULT_DB_PATH):
    """Base consolidada de `matriculas` (grão de BR-MIGRAR-001, já aplicado
    na ingestão) com curso/ciclo/campus já juntados — pronta para
    `app/domain/matriculas.py` e `app/domain/percentuais_legais.py`."""
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(
            """
            SELECT m.co_matricula, m.status_corrigido, m.ano_base,
                   c.codigo_ciclo_matricula, c.tipo_programa_curso, c.dt_data_inicio,
                   cu.codigo_portfolio, cu.nome_curso_ajustado, cu.tipo_curso_pnp,
                   cu.subtipo_curso, cu.modalidade_ensino, cu.eixo_tecnologico_ajustado,
                   cu.carga_horaria_total, cu.fec, cu.co_unidade,
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


def carregar_eficiencia(db_path=DEFAULT_DB_PATH):
    """Base consolidada de `matriculas_eficiencia` (grão de BR-MIGRAR-002)
    com `dt_data_fim_previsto` do ciclo já junto — pronta para
    `app/domain/eficiencia.py`."""
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
