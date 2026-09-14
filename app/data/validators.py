"""BC-01 (Ingestão & Preparação): validação de schema do upload (RISK-004).

Implementado na Tarefa 05 do plano de reconstrução, a partir de
`_reversa_sdd/migration/target_architecture.md` (seção BC-01) e
`_reversa_sdd/migration/risk_register.md` (RISK-004).

Um upload é composto por 5 fontes (planilha com abas `matriculas`/`ciclos`,
mais as fontes complementares de curso/campus/fatores — ver
`data_migration_plan.md` §"Estratégia de ETL"). Se qualquer coluna obrigatória
faltar em qualquer fonte, o upload inteiro é rejeitado (RISK-004): nenhuma
tabela é escrita, o dataset anterior permanece ativo (AD-02).

GAP herdado de `app/data/transform.py` (sinalizado na Tarefa 03, não resolvido
até a Tarefa 05 por falta de planilha real de teste): os nomes de coluna
abaixo são a convenção provisória já usada pelas funções T-01 a T-08; devem
ser confirmados contra a extração real do Sistec/PNP na Tarefa 11 (Validação
de Paridade).
"""

REQUIRED_COLUMNS = {
    "matriculas": [
        "CO_MATRICULA",
        "CODIGO_CICLO_MATRICULA",
        "STATUS_MATRICULA_SISTEC",
        "STATUS_MATRICULA_PNP",
        "MES_OCORRENCIA_CORRIGIDO",
    ],
    "ciclos": [
        "CODIGO_CICLO_MATRICULA",
        "CÓDIGO DO PORTFÓLIO",
        "DT_DATA_INICIO",
        "DT_DATA_FIM_PREVISTO",
        "TIPO_PROGRAMA_CURSO",
        "STATUS_CICLO",
    ],
    "cursos": [
        "CÓDIGO DO PORTFÓLIO",
        "NOME_CURSO",
        "TIPO_CURSO",
        "SUBTIPO_CURSO",
        "MODALIDADE_ENSINO",
        "EIXO_TECNOLOGICO_AJUSTADO",
        "CARGA_HORARIA_TOTAL",
        "CO_UNIDADE",
        # Tarefa 11: coluna de origem do eixo "oferta" (BR-MIGRAR-020),
        # ausente da validação original da Tarefa 05 (GAP nunca implementado).
        "OFERTA",
    ],
    "campus": ["CO_UNIDADE", "CIDADE", "NOME_UNIDADE"],
    "fatores": ["CÓDIGO DO PORTFÓLIO", "FEC", "FECH"],
}


class ErroValidacaoSchema(Exception):
    """Levantada quando o upload não passa na validação de schema (RISK-004)."""


def validar_schema(planilhas):
    """Valida que cada fonte obrigatória está presente e tem as colunas exigidas.

    `planilhas` é um dict {nome_da_fonte: DataFrame}. Retorna a lista de erros
    (vazia se válido) — não lança exceção, para permitir que o chamador decida
    como registrar a rejeição (ex.: `uploads_log`, RISK-004).
    """
    erros = []
    for fonte, colunas_obrigatorias in REQUIRED_COLUMNS.items():
        df = planilhas.get(fonte)
        if df is None:
            erros.append(f"fonte obrigatória ausente: {fonte}")
            continue
        faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
        if faltantes:
            erros.append(f"{fonte}: colunas obrigatórias ausentes: {', '.join(faltantes)}")
    return erros
