"""BC-02 (Núcleo de Matrículas, shared kernel): eh_evadido(), matricula_equivalente(), eixo dinâmico.

Contrato de domínio (filtros ativos, ordem de dependência entre módulos) definido em
`app/domain/contrato.py` (Tarefa 04). Toda função deste módulo deve receber
`filtros: FiltrosAtivos` como parâmetro explícito. Funções implementadas na
Tarefa 06, a partir de `_reversa_sdd/migration/target_architecture.md` (seção BC-02),
`_reversa_sdd/migration/target_domain_model.md` e
`_reversa_sdd/migration/target_business_rules.md` (BR-MIGRAR-005, 007, 008, 014, 019, 020).

Paradigma alvo (`paradigm_decision.md`): procedural rico, estilo funcional leve —
cada função pura, recebendo os filtros ativos como parâmetro explícito, sem estado global.
"""

from app.domain.contrato import EixoQuebra, FiltrosAtivos

# BR-MIGRAR-005: definição única de evasão (7 status) — o legado tinha 3
# definições divergentes entre medida e coluna de agrupamento; esta é a
# única fonte de verdade, consumida por todas as páginas/indicadores.
STATUS_EVADIDO = {
    "ABANDONO",
    "DESLIGADO",
    "DESLIGADA",
    "REPROVADO",
    "REPROVADA",
    "TRANSF_EXT",
    "TRANSF_INT",
}

# BR-MIGRAR-007/008: fech = 1 para todos os tipos de curso, exceto
# Qualificação Profissional, onde fech = carga_horaria_total / 800.
TIPO_CURSO_QUALIFICACAO_PROFISSIONAL = "QUALIFICAÇÃO PROFISSIONAL"
CARGA_HORARIA_REFERENCIA_FECH = 800

# BR-MIGRAR-020: mapeia cada eixo de quebra (seleção única) para a coluna do
# dataset consolidado usada para agrupar — corrige o bug M-D3 do legado
# (field parameter do Power BI permitia, indevidamente, seleção múltipla).
# Correção da Tarefa 11 (parity_tests/06-eixo-dinamico-e-fic.feature): a
# Tarefa 06 mapeava "tipo_curso" para `tipo_curso_pnp` e não mapeava "oferta"
# a coluna alguma — a spec exige `subtipo_curso` e `tipo_oferta_curso`
# respectivamente (coluna adicionada ao schema na própria Tarefa 11).
COLUNA_POR_EIXO = {
    "campus": "co_unidade",
    "tipo_curso": "subtipo_curso",
    "nome_curso": "nome_curso_ajustado",
    "modalidade": "modalidade_ensino",
    "oferta": "tipo_oferta_curso",
    "ciclo": "codigo_ciclo_matricula",
}


def eh_evadido(status):
    """BR-MIGRAR-005/006: True se `status` (já corrigido, BR-MIGRAR-003) está
    no conjunto único de evasão. REPROVADO/REPROVADA contam como evasão sem
    remapeamento prévio no ETL (BR-MIGRAR-006) — a classificação acontece
    inteiramente aqui, não na ingestão."""
    return status in STATUS_EVADIDO


def matricula_equivalente(tipo_curso, carga_horaria_total, fec, matriculas, fech=1):
    """BR-MIGRAR-007: Mateq = Mat x fech x fec (Portaria 146/2021 art. 2º).

    `fec` já chega com o default explícito aplicado na ingestão quando a
    planilha de fatores não tinha par (BR-MIGRAR-008, hoje via
    `app/data/fatores.casar_fatores`, D-07) — esta função nunca recebe `fec`
    nulo.

    `fech` (D-07, `002-baixador-planilhas-sistec`): para curso não FIC, vale
    o `fech` do curso (`cursos.fech`, casado por `casar_fatores`), passado
    explicitamente pelo chamador. Para Qualificação Profissional (FIC), o
    `fech` recebido é ignorado — continua sendo a carga horária total / 800,
    como antes desta feature.
    """
    if tipo_curso == TIPO_CURSO_QUALIFICACAO_PROFISSIONAL:
        fech_efetivo = carga_horaria_total / CARGA_HORARIA_REFERENCIA_FECH
    else:
        fech_efetivo = fech
    return matriculas * fech_efetivo * fec


def coluna_para_eixo(eixo: EixoQuebra):
    """BR-MIGRAR-020: resolve o eixo de quebra ativo (parâmetro explícito,
    nunca estado implícito) para a coluna correspondente no dataset."""
    return COLUNA_POR_EIXO[eixo]


def agrupar_por_eixo(df, filtros: FiltrosAtivos, coluna_valor, agregacao="sum"):
    """BR-MIGRAR-020/025: agrega `coluna_valor` por exatamente um eixo de
    quebra por vez — `filtros.eixo` é sempre uma seleção única por construção
    (`EixoQuebra` é um `Literal`, não uma lista), o que corrige o bug M-D3 do
    legado (field parameter com `singleSelect=false`)."""
    coluna = coluna_para_eixo(filtros.eixo)
    return df.groupby(coluna, dropna=False)[coluna_valor].agg(agregacao).reset_index()


def modalidade(df):
    """BR-MIGRAR-019: fonte única de "Modalidade". O legado usava
    `dimCiclo[MODALIDADE ENSINO]` ou `dimCurso[MODALIDADE ENSINO]` de forma
    inconsistente entre páginas; a ingestão (Tarefa 05) já grava uma única
    coluna `modalidade_ensino` em `cursos` — este acessor existe para que
    nenhuma página leia outra coluna divergente."""
    return df["modalidade_ensino"]
