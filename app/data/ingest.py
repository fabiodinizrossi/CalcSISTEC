"""BC-01 (Ingestão & Preparação): leitura/parsing das planilhas (matriculas, ciclos).

Implementado na Tarefa 05 do plano de reconstrução, a partir de
`_reversa_sdd/migration/target_architecture.md` (seção BC-01) e
`_reversa_sdd/migration/data_migration_plan.md`.

Orquestra o fluxo completo descrito em `data_migration_plan.md`
§"Estratégia de ETL":
    1. validação de schema (RISK-004) — `app/data/validators.py`
    2. aplicação sequencial de T-01 a T-08 — `app/data/transform.py` +
       correção de status via `app/data/correction.py` (BR-MIGRAR-003)
    3. escrita em tabelas ativas via swap atômico (AD-02)
    4. registro do upload em `uploads_log`, válido ou inválido

Upload inválido nunca altera o dataset ativo — o dataset anterior permanece
(RISK-004, AD-02).
"""

from app.data.correction import corrigir_status_sistec_pnp
from app.data.schema import DEFAULT_DB_PATH, get_connection
from app.data.transform import (
    t01_remover_pii,
    t03_normalizar_curso,
    t04_chave_curso_unica,
    t05_default_fec_fech,
    t06_filtrar_ciclos_excluidos,
    t07_grao_matricula_atendida,
    t08_grao_eficiencia_academica,
)
from app.data.validators import validar_schema


class UploadInvalido(Exception):
    """Levantada quando o upload é rejeitado por inteiro (RISK-004)."""


def processar_upload(planilhas, mapa_nomes_curso, ano_base, uploaded_by, filename, db_path=DEFAULT_DB_PATH):
    """Processa um upload completo e, se válido, promove-o a dataset ativo.

    `planilhas` é um dict com as 5 fontes do upload: "matriculas", "ciclos",
    "cursos", "campus", "fatores" (ver `validators.REQUIRED_COLUMNS`).
    `mapa_nomes_curso` é a tabela de mapeamento externalizada de nomes
    históricos do Sistec -> nome padrão PNP (BR-MIGRAR-017).

    Retorna um resumo de contagens quando o upload é aceito; levanta
    `UploadInvalido` (e registra a rejeição em `uploads_log`) caso contrário.
    """
    erros_schema = validar_schema(planilhas)
    if erros_schema:
        mensagem = "; ".join(erros_schema)
        _registrar_upload(db_path, uploaded_by, filename, "invalido", mensagem)
        raise UploadInvalido(mensagem)

    try:
        resultado = _executar_pipeline(planilhas, mapa_nomes_curso, ano_base)
    except Exception as exc:
        _registrar_upload(db_path, uploaded_by, filename, "invalido", str(exc))
        raise UploadInvalido(str(exc)) from exc

    _swap_atomico(db_path, resultado)
    _registrar_upload(db_path, uploaded_by, filename, "valido", None)

    return {
        "matriculas": len(resultado["matriculas"]),
        "matriculas_eficiencia": len(resultado["matriculas_eficiencia"]),
        "cursos_rejeitados_sem_portfolio": resultado["cursos_rejeitados"],
        "ciclos_rejeitados_sem_portfolio": resultado["ciclos_rejeitados"],
        "matriculas_rejeitadas_status": resultado["matriculas_rejeitadas"],
        "cursos_fator_nao_encontrado": resultado["cursos_fator_nao_encontrado"],
    }


def _executar_pipeline(planilhas, mapa_nomes_curso, ano_base):
    """T-01 a T-08, na ordem descrita em `data_migration_plan.md`."""

    # T-01: remoção de PII na borda (BR-DESCARTAR-001, RISK-008).
    df_matriculas = t01_remover_pii(planilhas["matriculas"])

    # T-02: correção de status Sistec x PNP (BR-MIGRAR-003), via correction.py.
    df_matriculas, df_matriculas_rejeitadas = corrigir_status_sistec_pnp(df_matriculas)

    # T-03: normalização de nome/tipo de curso (BR-MIGRAR-017).
    df_cursos = t03_normalizar_curso(planilhas["cursos"], mapa_nomes_curso)

    # T-04: chave de curso única (BR-MIGRAR-014) — aplicada a cursos e ciclos.
    df_cursos, df_cursos_rejeitados = t04_chave_curso_unica(df_cursos)
    df_ciclos, df_ciclos_rejeitados = t04_chave_curso_unica(planilhas["ciclos"])

    # T-05: default explícito de FEC/FECH quando a planilha de fatores não
    # tem par (BR-MIGRAR-008) — nunca NULL silencioso.
    df_fatores = planilhas["fatores"].rename(columns={"CÓDIGO DO PORTFÓLIO": "codigo_portfolio"})
    df_cursos = t05_default_fec_fech(df_cursos, df_fatores)
    # BR-MIGRAR-008 exige um sinal explícito (não silêncio) quando o default é
    # aplicado; `fator_nao_encontrado` é contado aqui e devolvido no resumo do
    # upload para revisão, em vez de ser descartado ao selecionar as colunas
    # finais de `cursos` abaixo.
    cursos_fator_nao_encontrado = int(df_cursos["fator_nao_encontrado"].sum())

    # T-06: filtra ciclos excluídos (BR-MIGRAR-018) — a regra exige checar as
    # duas colunas de status do ciclo (`STATUS DO CICLO DE MATRÍCULA` e
    # `SITUAÇÃO DO CICLO`); `t06_filtrar_ciclos_excluidos` cobre a primeira,
    # a segunda (opcional na fonte) é filtrada aqui.
    df_ciclos = t06_filtrar_ciclos_excluidos(df_ciclos)
    if "SITUACAO_CICLO" in df_ciclos.columns:
        df_ciclos = df_ciclos.loc[df_ciclos["SITUACAO_CICLO"] != "EXCLUÍDO"].copy()

    # Junta matrículas ao ciclo correspondente para expor as colunas exigidas
    # pelo grão (dt_data_inicio, dt_data_fim_previsto, mes_ocorrencia_corrigido)
    # com os nomes já usados pelas funções T-07/T-08 (nomes do schema alvo).
    df_ciclos_para_join = df_ciclos.rename(
        columns={
            "DT_DATA_INICIO": "dt_data_inicio",
            "DT_DATA_FIM_PREVISTO": "dt_data_fim_previsto",
        }
    )
    df_matriculas = df_matriculas.rename(columns={"MES_OCORRENCIA_CORRIGIDO": "mes_ocorrencia_corrigido"})
    df_matriculas_ciclo = df_matriculas.merge(
        df_ciclos_para_join,
        on="CODIGO_CICLO_MATRICULA",
        how="inner",
    )

    # T-07: grão de matrícula atendida (BR-MIGRAR-001, BR-MIGRAR-028 — inclui
    # dt_data_inicio nula, BR-HUMANA-010).
    df_matriculas_final = t07_grao_matricula_atendida(df_matriculas_ciclo, ano_base)

    # T-08: grão de eficiência acadêmica (BR-MIGRAR-002) — universo
    # independente do T-07, derivado da mesma junção matrícula x ciclo.
    df_eficiencia_final = t08_grao_eficiencia_academica(df_matriculas_ciclo, ano_base)

    return {
        "campus": planilhas["campus"].rename(
            columns={"CO_UNIDADE": "co_unidade", "CIDADE": "cidade", "NOME_UNIDADE": "nome_unidade"}
        )[["co_unidade", "cidade", "nome_unidade"]],
        "cursos": df_cursos.rename(
            columns={
                "SUBTIPO_CURSO": "subtipo_curso",
                "MODALIDADE_ENSINO": "modalidade_ensino",
                "EIXO_TECNOLOGICO_AJUSTADO": "eixo_tecnologico_ajustado",
                "CARGA_HORARIA_TOTAL": "carga_horaria_total",
                "CO_UNIDADE": "co_unidade",
                # Tarefa 11: colunas adicionadas após divergência encontrada
                # em parity_tests/06-eixo-dinamico-e-fic.feature.
                "OFERTA": "tipo_oferta_curso",
            }
        )[
            [
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
            ]
        ],
        "ciclos": df_ciclos.rename(
            columns={
                "CODIGO_CICLO_MATRICULA": "codigo_ciclo_matricula",
                "DT_DATA_INICIO": "dt_data_inicio",
                "DT_DATA_FIM_PREVISTO": "dt_data_fim_previsto",
                "TIPO_PROGRAMA_CURSO": "tipo_programa_curso",
                "STATUS_CICLO": "status_ciclo",
            }
        )[
            [
                "codigo_ciclo_matricula",
                "codigo_portfolio",
                "dt_data_inicio",
                "dt_data_fim_previsto",
                "tipo_programa_curso",
                "status_ciclo",
            ]
        ],
        "matriculas": df_matriculas_final.rename(
            columns={"CO_MATRICULA": "co_matricula", "CODIGO_CICLO_MATRICULA": "codigo_ciclo_matricula"}
        ).assign(ano_base=ano_base)[
            ["co_matricula", "codigo_ciclo_matricula", "status_corrigido", "mes_ocorrencia_corrigido", "ano_base"]
        ],
        "matriculas_eficiencia": df_eficiencia_final.rename(
            columns={
                "CO_MATRICULA": "co_matricula",
                "CODIGO_CICLO_MATRICULA": "codigo_ciclo_matricula",
                "status_corrigido": "status_corrigido2",
            }
        )[["co_matricula", "codigo_ciclo_matricula", "status_corrigido2"]],
        "cursos_rejeitados": len(df_cursos_rejeitados),
        "ciclos_rejeitados": len(df_ciclos_rejeitados),
        "matriculas_rejeitadas": len(df_matriculas_rejeitadas),
        "cursos_fator_nao_encontrado": cursos_fator_nao_encontrado,
    }


def _swap_atomico(db_path, resultado):
    """AD-02: grava as tabelas ativas dentro de uma única transação SQLite —
    nunca escreve incrementalmente sobre o dataset em uso. Se qualquer escrita
    falhar, a transação inteira é revertida e o dataset anterior permanece."""
    tabelas = ["campus", "cursos", "ciclos", "matriculas", "matriculas_eficiencia"]
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN")
        for tabela in tabelas:
            conn.execute(f"DELETE FROM {tabela}")
            df = resultado[tabela]
            if not df.empty:
                df.to_sql(tabela, conn, if_exists="append", index=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _registrar_upload(db_path, uploaded_by, filename, status, error_message):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO uploads_log (uploaded_by, filename, status, error_message) VALUES (?, ?, ?, ?)",
            (uploaded_by, filename, status, error_message),
        )
        conn.commit()
    finally:
        conn.close()
