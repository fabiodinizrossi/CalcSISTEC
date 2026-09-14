"""BC-01 (Ingestão & Preparação): correção de status Sistec x PNP (BR-MIGRAR-003).

Implementado na Tarefa 05 do plano de reconstrução, a partir de
`_reversa_sdd/migration/target_architecture.md` (seção BC-01) e
`_reversa_sdd/migration/target_business_rules.md` (BR-MIGRAR-003).

`AGG-Ingestao.corrigir_status` citado em `data_migration_plan.md` — delega para
`app/data/transform.t02_corrigir_status` (função pura já implementada na
Tarefa 03), mantendo aqui a responsabilidade de BC-01 sobre esta regra de
negócio específica.
"""

from app.data.transform import t02_corrigir_status


def corrigir_status_sistec_pnp(df, col_sistec="STATUS_MATRICULA_SISTEC", col_pnp="STATUS_MATRICULA_PNP"):
    """BR-MIGRAR-003: PNP terminativo (!= EM_CURSO, != nulo) prevalece; PNP
    EM_CURSO ou nulo -> vale o Sistec.

    Retorna (df_valido, df_rejeitado): linhas cujo status corrigido não
    pertence ao domínio fechado de `StatusMatricula` são rejeitadas em vez de
    passar silenciosamente (T-02 de `data_migration_plan.md`, correção do
    `returnErrorValuesAsNull` do legado).
    """
    return t02_corrigir_status(df, col_sistec=col_sistec, col_pnp=col_pnp)
