"""Classificação de matrículas e cálculo da eficiência acadêmica (IEA/ENIEA).

`classificar_matriculas_eficiencia` espera um `df` já consolidado (matrículas
de `matriculas_eficiencia` junto do fim previsto do ciclo) com as colunas
`status_corrigido2` e `dt_data_fim_previsto`.
"""

from app.domain.shared import eh_evadido

# Status concluídos para o cálculo de eficiência acadêmica (Guia PNP/ENIEA).
STATUS_CONCLUIDO = {"CONCLUÍDA", "INTEGRALIZADA"}


def eh_concluido(status):
    """Classifica CONCLUÍDA e INTEGRALIZADA como concluídas."""
    return status in STATUS_CONCLUIDO


def eh_retido(status):
    """Classifica EM_CURSO como retida na base de eficiência já filtrada.

    Nessa base, o fim previsto está no ano anterior ao ano-base, portanto
    cada matrícula EM_CURSO já está pelo menos um ano além do prazo.
    """
    return status == "EM_CURSO"


def classificar_matriculas_eficiencia(df, filtros):
    """Conta matrículas concluídas, evadidas e retidas na base de eficiência.

    Os três grupos cobrem os status aceitos nessa base.
    """
    concluidos = int(df["status_corrigido2"].apply(eh_concluido).sum())
    evadidos = int(df["status_corrigido2"].apply(eh_evadido).sum())
    retidos = int(df["status_corrigido2"].apply(eh_retido).sum())
    return concluidos, evadidos, retidos


def calcular_iea(concluidos, evadidos, retidos):
    """Calcula IEA = pC + (pC / (pC + pE)) × pR.

    Retorna zero quando o total ou a soma pC + pE é zero.
    """
    total = concluidos + evadidos + retidos
    if total == 0:
        return 0.0
    pc = concluidos / total
    pe = evadidos / total
    pr = retidos / total
    if (pc + pe) == 0:
        return 0.0
    return pc + (pc / (pc + pe)) * pr


def iea(df, filtros):
    """Classifica a base consolidada e calcula o IEA em um passo."""
    concluidos, evadidos, retidos = classificar_matriculas_eficiencia(df, filtros)
    return calcular_iea(concluidos, evadidos, retidos)
