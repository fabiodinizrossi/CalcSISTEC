"""BC-01 (Ingestão & Preparação): monta a versão interna a partir da baixa
consolidada do Sistec (`002-baixador-planilhas-sistec`, T037/T038, D-14,
D-18).

O upload `.xlsx` saiu do sistema (D-14, `/admin/upload` removido). A entrada
agora é o `conjunto` já consolidado por `app/sistec/consolidacao.consolidar`
(pares de ciclo/matrícula da extensão, já com a lista de permissão de
colunas aplicada). `montar_versao_interna` deriva `cursos`/`ciclos`
(`_cursos_e_ciclos_do_conjunto`, reaproveitando T-03/T-04 de
`app/data/transform.py` e os ajustes A2/A3/A5 de `app/data/ajustes_curso.py`),
aplica a regra de campus falho (RN-22, `data-delta.md` §6) e grava via
`app/data/versoes.salvar_interna` — nunca escreve incrementalmente sobre a
versão interna em uso (RN-20)."""

import pandas as pd

from app.data.ajustes_curso import (
    MAPA_NOMES_CURSO,
    aplicar_prefixo_tecnico,
    aplicar_preposicoes_minusculas,
    reclassificar_eixo_tecnologico,
)
from app.data.consulta import ano_base_ativo
from app.data.fatores import casar_fatores
from app.data.schema import DEFAULT_DB_PATH, get_connection
from app.data.transform import t03_normalizar_curso, t04_chave_curso_unica
from app.data.versoes import salvar_interna
from app.sistec.consolidacao import montar_matriculas_e_eficiencia


_COLUNAS_CURSOS_SCHEMA = [
    "codigo_portfolio",
    "nome_curso_ajustado",
    "tipo_curso_pnp",
    "subtipo_curso",
    "modalidade_ensino",
    "eixo_tecnologico_ajustado",
    "fec",
    "fech",
    "carga_horaria_total",
    "co_unidade",
    "tipo_oferta_curso",
    "categoria_origem_curso",
    "fator_nao_encontrado",
]
_COLUNAS_CICLOS_SCHEMA = [
    "codigo_ciclo_matricula",
    "codigo_portfolio",
    "co_unidade",
    "dt_data_inicio",
    "dt_data_fim_previsto",
    "tipo_programa_curso",
    "status_ciclo",
]
_COLUNAS_MATRICULAS_SCHEMA = ["co_matricula", "codigo_ciclo_matricula", "status_corrigido", "mes_ocorrencia_corrigido", "ano_base"]
_COLUNAS_EFICIENCIA_SCHEMA = ["co_matricula", "codigo_ciclo_matricula", "status_corrigido2"]


def _cursos_e_ciclos_do_conjunto(df_ciclo):
    """Deriva `cursos` e `ciclos` (nomes de coluna do schema) a partir das
    linhas de ciclo consolidadas (`app/sistec/consolidacao.consolidar`), que
    trazem os atributos do curso embutidos em cada linha (T036, D-18).

    Aplica, nesta ordem (`app/data/ajustes_curso.py`): A2 (mapa de nomes,
    `t03_normalizar_curso`), A3 (prefixo "TÉCNICO EM"), Text.Proper + A4
    (cosmético), A5 (eixo tecnológico). `t04_chave_curso_unica` rejeita
    linhas sem `CÓDIGO DO PORTFÓLIO` (D-08)."""
    if df_ciclo.empty:
        cursos_vazio = pd.DataFrame(columns=[c for c in _COLUNAS_CURSOS_SCHEMA if c not in ("fec", "fech", "fator_nao_encontrado")])
        return cursos_vazio, pd.DataFrame(columns=_COLUNAS_CICLOS_SCHEMA), 0

    df = t03_normalizar_curso(df_ciclo, MAPA_NOMES_CURSO, col_nome="NOME_CURSO", col_tipo="TIPO_CURSO")
    df["nome_curso_ajustado"] = df.apply(
        lambda linha: aplicar_prefixo_tecnico(linha["nome_curso_ajustado"], linha["tipo_curso_pnp"]), axis=1
    )
    df["nome_curso_ajustado"] = df["nome_curso_ajustado"].str.title().map(aplicar_preposicoes_minusculas)
    df["eixo_tecnologico_ajustado"] = df.apply(
        lambda linha: reclassificar_eixo_tecnologico(linha["nome_curso_ajustado"], linha.get("EIXO_TECNOLOGICO")),
        axis=1,
    )
    df, df_rejeitados = t04_chave_curso_unica(df, col_portfolio="CÓDIGO DO PORTFÓLIO")

    cursos = (
        df.rename(
            columns={
                "TIPO_CURSO": "subtipo_curso",
                "MODALIDADE_ENSINO": "modalidade_ensino",
                "CARGA_HORARIA_TOTAL": "carga_horaria_total",
                "CO_UNIDADE": "co_unidade",
                "OFERTA": "tipo_oferta_curso",
            }
        )
        .drop_duplicates(subset="codigo_portfolio", keep="first")[
            [
                "codigo_portfolio",
                "nome_curso_ajustado",
                "tipo_curso_pnp",
                "subtipo_curso",
                "modalidade_ensino",
                "eixo_tecnologico_ajustado",
                "carga_horaria_total",
                "co_unidade",
                "tipo_oferta_curso",
                "categoria_origem_curso",
            ]
        ]
        .reset_index(drop=True)
    )

    ciclos = df.rename(
        columns={
            "CODIGO_CICLO_MATRICULA": "codigo_ciclo_matricula",
            "CO_UNIDADE": "co_unidade",
            "DT_DATA_INICIO": "dt_data_inicio",
            "DT_DATA_FIM_PREVISTO": "dt_data_fim_previsto",
            "TIPO_PROGRAMA_CURSO": "tipo_programa_curso",
            "STATUS_CICLO": "status_ciclo",
        }
    )[
        [
            "codigo_ciclo_matricula",
            "codigo_portfolio",
            "co_unidade",
            "dt_data_inicio",
            "dt_data_fim_previsto",
            "tipo_programa_curso",
            "status_ciclo",
        ]
    ].reset_index(drop=True)

    return cursos, ciclos, len(df_rejeitados)


def _ler_mantidos(conn, campi_falhos):
    """data-delta.md §6.2: linhas de `interna_*` dos campi com par falho —
    mantidas como estão, sem entrar na troca desta baixa."""
    vazio = {
        "cursos": pd.DataFrame(columns=_COLUNAS_CURSOS_SCHEMA),
        "ciclos": pd.DataFrame(columns=_COLUNAS_CICLOS_SCHEMA),
        "matriculas": pd.DataFrame(columns=_COLUNAS_MATRICULAS_SCHEMA),
        "matriculas_eficiencia": pd.DataFrame(columns=_COLUNAS_EFICIENCIA_SCHEMA),
    }
    if not campi_falhos:
        return vazio

    marcadores = ",".join("?" for _ in campi_falhos)
    ciclos = pd.read_sql_query(
        f"SELECT * FROM interna_ciclos WHERE co_unidade IN ({marcadores})", conn, params=list(campi_falhos)
    )
    if ciclos.empty:
        return vazio

    codigos_ciclo = ciclos["codigo_ciclo_matricula"].tolist()
    codigos_portfolio = ciclos["codigo_portfolio"].unique().tolist()
    marcadores_ciclo = ",".join("?" for _ in codigos_ciclo) or "NULL"
    marcadores_portfolio = ",".join("?" for _ in codigos_portfolio) or "NULL"

    cursos = pd.read_sql_query(
        f"SELECT * FROM interna_cursos WHERE codigo_portfolio IN ({marcadores_portfolio})",
        conn,
        params=codigos_portfolio,
    )
    matriculas = pd.read_sql_query(
        f"SELECT * FROM interna_matriculas WHERE codigo_ciclo_matricula IN ({marcadores_ciclo})",
        conn,
        params=codigos_ciclo,
    )
    matriculas_eficiencia = pd.read_sql_query(
        f"SELECT * FROM interna_matriculas_eficiencia WHERE codigo_ciclo_matricula IN ({marcadores_ciclo})",
        conn,
        params=codigos_ciclo,
    )
    return {"cursos": cursos, "ciclos": ciclos, "matriculas": matriculas, "matriculas_eficiencia": matriculas_eficiencia}


def ciclos_com_modalidade(df_ciclo):
    """CPR-03: descarta os ciclos sem `MODALIDADE_ENSINO` (nulo, `NaN` ou
    vazio/só espaço) antes de montar `cursos`/`ciclos`/`matriculas`.

    Ciclos antigos de programas encerrados (ex.: MULHERES MIL 2011–2013)
    chegam assim do Sistec, e `modalidade_ensino` é `NOT NULL` em
    `cursos`/`interna_cursos` — a gravação da fonte da prévia quebrava com
    `IntegrityError`. As matrículas desses ciclos saem junto: o `merge` de
    `montar_matriculas_e_eficiencia` é `inner` contra os ciclos.

    `df_ciclo` vazio ou sem a coluna volta como veio."""
    if df_ciclo is None or df_ciclo.empty or "MODALIDADE_ENSINO" not in df_ciclo.columns:
        return df_ciclo
    modalidade = df_ciclo["MODALIDADE_ENSINO"]
    sem_modalidade = modalidade.isna() | (modalidade.astype(str).str.strip() == "")
    return df_ciclo.loc[~sem_modalidade]


def calcular_assinatura_origem(db_path=DEFAULT_DB_PATH):
    """PVP-10 (`previa-paginas-publicas`, T1): assinatura de origem do
    candidato — as dependências que precisam continuar iguais entre a
    conferência e o Salvar. Devolve `rev_interna`, `rev_publicada`,
    `ano_base` e um resumo determinístico (tuplas ordenadas) de
    `interna_fatores` e de `interna_campus` (CPR-06: é a interna que vai ao
    ar no Publicar; o `campus` publicado pode estar desatualizado até lá).
    Estável entre chamadas com o mesmo banco."""
    conn = get_connection(db_path)
    try:
        rev_interna, rev_publicada = conn.execute(
            "SELECT rev_interna, rev_publicada FROM estado_versoes WHERE id = 1"
        ).fetchone()
        fatores = conn.execute(
            "SELECT tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome "
            "FROM interna_fatores ORDER BY chave_tipo, chave_nome"
        ).fetchall()
        campus = conn.execute(
            "SELECT co_unidade, cidade, nome_unidade FROM interna_campus ORDER BY co_unidade"
        ).fetchall()
    finally:
        conn.close()

    return {
        "rev_interna": rev_interna,
        "rev_publicada": rev_publicada,
        "ano_base": ano_base_ativo(db_path),
        "fatores": tuple(fatores),
        "campus": tuple(campus),
    }


def preparar_versao(conjunto, campi_falhos, db_path=DEFAULT_DB_PATH, ano_base=None):
    """PVP-03/PVP-04 (`previa-paginas-publicas`, T1): prepara, sem gravar, as
    quatro tabelas que `salvar_interna` receberia para o `conjunto` — com os
    campi preservados concatenados e os fatores casados (RN-22, D-07).

    Devolve `{"tabelas", "resumo", "ano_base", "assinatura_origem"}`. Nenhuma
    conexão de escrita é aberta. `ano_base=None` lê `config.ano_base`
    (`consulta.ano_base_ativo`); um valor explícito prevalece."""
    if ano_base is None:
        ano_base = ano_base_ativo(db_path)

    campi_falhos = set(campi_falhos or ())
    df_ciclo = conjunto["ciclos"]
    df_matricula = conjunto["matriculas"]

    if campi_falhos and "CO_UNIDADE" in df_ciclo.columns:
        df_ciclo_novos = df_ciclo.loc[~df_ciclo["CO_UNIDADE"].isin(campi_falhos)].copy()
    else:
        df_ciclo_novos = df_ciclo

    # CPR-03: ciclos sem modalidade de ensino são descartados antes de montar
    # o candidato — as matrículas deles saem por não casarem no merge interno.
    df_ciclo_novos_validos = ciclos_com_modalidade(df_ciclo_novos)
    codigos_descartados = set(df_ciclo_novos["CODIGO_CICLO_MATRICULA"]) - set(
        df_ciclo_novos_validos["CODIGO_CICLO_MATRICULA"]
    )
    n_ciclos_descartados = int(len(df_ciclo_novos) - len(df_ciclo_novos_validos))
    if codigos_descartados and "CODIGO_CICLO_MATRICULA" in df_matricula.columns:
        n_matriculas_descartadas = int(
            df_matricula["CODIGO_CICLO_MATRICULA"].isin(codigos_descartados).sum()
        )
    else:
        n_matriculas_descartadas = 0

    cursos_novos, ciclos_novos, cursos_rejeitados = _cursos_e_ciclos_do_conjunto(df_ciclo_novos_validos)
    matriculas_novos, eficiencia_novos = montar_matriculas_e_eficiencia(
        df_matricula, df_ciclo_novos_validos, ano_base
    )
    matriculas_novos = matriculas_novos.rename(
        columns={"CO_MATRICULA": "co_matricula", "CODIGO_CICLO_MATRICULA": "codigo_ciclo_matricula"}
    ).assign(ano_base=ano_base)[_COLUNAS_MATRICULAS_SCHEMA] if not matriculas_novos.empty else pd.DataFrame(
        columns=_COLUNAS_MATRICULAS_SCHEMA
    )
    eficiencia_novos = eficiencia_novos.rename(
        columns={
            "CO_MATRICULA": "co_matricula",
            "CODIGO_CICLO_MATRICULA": "codigo_ciclo_matricula",
            "status_corrigido": "status_corrigido2",
        }
    )[_COLUNAS_EFICIENCIA_SCHEMA] if not eficiencia_novos.empty else pd.DataFrame(columns=_COLUNAS_EFICIENCIA_SCHEMA)

    conn = get_connection(db_path)
    try:
        mantidos = _ler_mantidos(conn, campi_falhos)
        fatores_atuais = pd.read_sql_query(
            "SELECT tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome FROM interna_fatores", conn
        )
    finally:
        conn.close()

    cursos_final = pd.concat([mantidos["cursos"], cursos_novos], ignore_index=True).drop_duplicates(
        subset="codigo_portfolio", keep="first"
    )
    cursos_final = casar_fatores(cursos_final, fatores_atuais)

    ciclos_final = pd.concat([mantidos["ciclos"], ciclos_novos], ignore_index=True).drop_duplicates(
        subset="codigo_ciclo_matricula", keep="first"
    )
    matriculas_final = pd.concat([mantidos["matriculas"], matriculas_novos], ignore_index=True).drop_duplicates(
        subset="co_matricula", keep="first"
    )
    eficiencia_final = pd.concat(
        [mantidos["matriculas_eficiencia"], eficiencia_novos], ignore_index=True
    ).drop_duplicates(subset="co_matricula", keep="first")

    tabelas = {
        "cursos": cursos_final[_COLUNAS_CURSOS_SCHEMA],
        "ciclos": ciclos_final[_COLUNAS_CICLOS_SCHEMA],
        "matriculas": matriculas_final[_COLUNAS_MATRICULAS_SCHEMA],
        "matriculas_eficiencia": eficiencia_final[_COLUNAS_EFICIENCIA_SCHEMA],
    }
    resumo = {
        "cursos": len(cursos_final),
        "ciclos": len(ciclos_final),
        "matriculas": len(matriculas_final),
        "matriculas_eficiencia": len(eficiencia_final),
        "cursos_rejeitados_sem_portfolio": cursos_rejeitados,
        "cursos_fator_nao_encontrado": int(cursos_final["fator_nao_encontrado"].sum()),
        "campi_mantidos": sorted(campi_falhos),
        "ciclos_sem_modalidade_descartados": n_ciclos_descartados,
        "matriculas_sem_modalidade_descartadas": n_matriculas_descartadas,
    }
    return {
        "tabelas": tabelas,
        "resumo": resumo,
        "ano_base": ano_base,
        "assinatura_origem": calcular_assinatura_origem(db_path),
    }


def montar_versao_interna(conjunto, campi_falhos, db_path=DEFAULT_DB_PATH, ano_base=2026):
    """RN-20/RN-22 (`data-delta.md` §6): monta a versão interna a partir do
    `conjunto` consolidado (`app/sistec/consolidacao.consolidar`) e dos
    `campi_falhos` (códigos de unidade com algum par que falhou nesta
    execução — os dados desses campi na interna atual são preservados, e as
    linhas novas desses campi no `conjunto` são descartadas, P-06).

    Grava via `app/data/versoes.salvar_interna` (transação única), reusando a
    preparação de `preparar_versao` (que calcula a assinatura de origem por
    `calcular_assinatura_origem`). Retorna o resumo de contagens para a
    prévia (RN-18: cursos sem fator)."""
    candidato = preparar_versao(conjunto, campi_falhos, db_path=db_path, ano_base=ano_base)
    salvar_interna(candidato["tabelas"], db_path)
    return candidato["resumo"]
