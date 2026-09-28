"""Ingestão & Preparação: correção de status Sistec x PNP.

Delega para `app/data/transform.t02_corrigir_status` (função pura), mantendo
aqui o ponto de entrada da ingestão para esta regra de negócio.
"""

from app.data.transform import t02_corrigir_status


def corrigir_status_sistec_pnp(df, col_sistec="STATUS_MATRICULA_SISTEC", col_pnp="STATUS_MATRICULA_PNP"):
    """PNP terminativo (!= EM_CURSO, != nulo) prevalece; PNP EM_CURSO ou nulo
    -> vale o Sistec.

    Retorna (df_valido, df_rejeitado): linhas cujo status corrigido não
    pertence ao domínio fechado de `StatusMatricula` são rejeitadas em vez de
    passar silenciosamente (correção do `returnErrorValuesAsNull` do legado).
    """
    return t02_corrigir_status(df, col_sistec=col_sistec, col_pnp=col_pnp)
