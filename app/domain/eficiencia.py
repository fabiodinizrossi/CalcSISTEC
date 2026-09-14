"""BC-03 (Indicadores Regulatórios): eficiência acadêmica (IEA/ENIEA).

Depende de BC-02 (`app/domain/shared.py`, `app/domain/matriculas.py`) — nunca o inverso,
conforme `ORDEM_DEPENDENCIA` em `app/domain/contrato.py` (Tarefa 04). Toda função
recebe `filtros: FiltrosAtivos` como parâmetro explícito.

Implementado na Tarefa 07 do plano de reconstrução, a partir de
`_reversa_sdd/migration/target_architecture.md` (seção BC-03) e
`_reversa_sdd/migration/target_business_rules.md` (BR-MIGRAR-013, IEA = 0 quando pC+pE=0).

`classificar_matriculas_eficiencia` espera um `df` já consolidado (matrículas
de `matriculas_eficiencia` — grão de BR-MIGRAR-002, já aplicado na ingestão —
junto do `dt_data_fim_previsto` do ciclo correspondente) com as colunas
`status_corrigido2` e `dt_data_fim_previsto`.
"""

from app.domain.shared import eh_evadido

# BR-MIGRAR-013: buckets de eficiência acadêmica (Guia PNP/ENIEA).
STATUS_CONCLUIDO = {"CONCLUÍDA", "INTEGRALIZADA"}


def eh_concluido(status):
    """BR-MIGRAR-013: bucket Concluídos = {CONCLUÍDA, INTEGRALIZADA}."""
    return status in STATUS_CONCLUIDO


def eh_retido(status):
    """BR-MIGRAR-013: Retidos = em curso além do prazo de integralização + 1
    ano. Correção da Tarefa 11 (`parity_tests/05-eficiencia-academica-iea.
    feature`, "nenhum status some do total"): dentro da base já filtrada
    pelo grão de eficiência (`T-08`/BR-MIGRAR-002, `dt_data_fim_previsto` no
    ano-base - 1), qualquer matrícula `EM_CURSO` já está, por construção,
    pelo menos 1 ano além do prazo — não é necessário (nem correto) recalcular
    a diferença de anos aqui. A implementação original da Tarefa 07 usava
    `ano_base > ano_prazo_integralizacao + 1` (comparação estrita), que dava
    sempre `False` no limite exato que o próprio grão seleciona, deixando
    matrículas `EM_CURSO` fora de todos os 3 buckets."""
    return status == "EM_CURSO"


def classificar_matriculas_eficiencia(df, filtros):
    """Classifica a base de eficiência nos 3 buckets de BR-MIGRAR-013.
    Como `StatusMatricula` é um domínio fechado de 8 valores — 2 em
    Concluídos, 5 em Evadidos (`shared.STATUS_EVADIDO`), 1 (`EM_CURSO`) em
    Retidos — os 3 buckets são exaustivos: nenhum status some do total."""
    concluidos = int(df["status_corrigido2"].apply(eh_concluido).sum())
    evadidos = int(df["status_corrigido2"].apply(eh_evadido).sum())
    retidos = int(df["status_corrigido2"].apply(eh_retido).sum())
    return concluidos, evadidos, retidos


def calcular_iea(concluidos, evadidos, retidos):
    """BR-MIGRAR-013: IEA = pC + (pC/(pC+pE))*pR, com proteção explícita de
    divisão por zero — `if`/`np.where` explícito em vez do `DIVIDE` do DAX,
    que devolve 0 silenciosamente sem sinalizar o edge case (Implicação 3 do
    `paradigm_decision.md`). Resultado 0 quando `Total=0` ou `pC+pE=0`
    (`AMB-005`)."""
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
    """Ponto de entrada de BC-03 para o IEA: classifica e calcula em um só
    passo, a partir da base já consolidada (ver docstring do módulo)."""
    concluidos, evadidos, retidos = classificar_matriculas_eficiencia(df, filtros)
    return calcular_iea(concluidos, evadidos, retidos)
