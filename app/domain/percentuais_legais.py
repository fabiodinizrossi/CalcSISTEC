"""BC-03 (Indicadores Regulatórios): percentuais legais (Técnico/Professores/PROEJA).

Depende de BC-02 (`app/domain/shared.py`, `app/domain/matriculas.py`) — nunca o inverso,
conforme `ORDEM_DEPENDENCIA` em `app/domain/contrato.py` (Tarefa 04). Toda função
recebe `filtros: FiltrosAtivos` como parâmetro explícito.

Implementado na Tarefa 07 do plano de reconstrução (seção BC-03,
BR-MIGRAR-009 a 012, 024).

Todas as funções recebem uma única base já consolidada `df` — uma linha por
combinação curso x ciclo com as colunas: `tipo_curso_pnp`, `subtipo_curso`,
`eixo_tecnologico_ajustado`, `carga_horaria_total`, `fec`, `tipo_programa_curso`
(do ciclo) e `quantidade_matriculas` (contagem de matrículas atendidas nessa
combinação, já filtrada por `FiltrosAtivos` a montante em `app/domain/
matriculas.py`) — nunca recalculam `matricula_equivalente` por conta própria
(invariante de `AGG-IndicadoresRegulatorios`, `target_domain_model.md`).
"""

from app.domain.shared import matricula_equivalente

META_TECNICO = 0.50
META_PROFESSORES = 0.20
META_PROEJA = 0.10

EIXO_PROFESSORES = "DESENVOLVIMENTO EDUCACIONAL E SOCIAL"

# BR-MIGRAR-010: lista de exclusão externalizada (não hardcoded dentro da
# função de cálculo) — facilita auditoria e futuras mudanças de critério.
EXCLUSOES_PROFESSORES = {
    "CERVEJEIRO",
    "FORMAÇÃO COMPLEMENTAR AO ENSINO FUNDAMENTAL",
    "RELAÇÕES COM SAÚDE",
    "JOVENS ATLETAS",
    "BELEZA E GÊNERO",
}


def recorte_tecnico(df):
    """BR-MIGRAR-009: `subtipo_curso` = Técnico; meta legal >= 50% (Lei
    11.892/2008 art. 8º §1º)."""
    return df[df["subtipo_curso"] == "Técnico"]


def recorte_professores(df, exclusoes=EXCLUSOES_PROFESSORES):
    """BR-MIGRAR-010: `eixo_tecnologico_ajustado` = Desenvolvimento
    Educacional e Social, menos a lista de exclusão; meta legal = 20%
    (Q22 — o limiar de cor do medidor no legado estava errado, não a meta).

    Correção da Tarefa 11 (`parity_tests/04-percentuais-legais.feature`): a
    exclusão é por substring no nome do curso ("...tem 'cervejeiro' no nome
    ajustado"), não por igualdade exata — um curso como "TÉCNICO EM
    CERVEJEIRO" precisa ser excluído, e `.isin()` nunca casaria com isso.
    """
    no_eixo = df["eixo_tecnologico_ajustado"] == EIXO_PROFESSORES
    nomes = df["nome_curso_ajustado"].str.upper()
    padrao = "|".join(exclusoes)
    excluido = nomes.str.contains(padrao, na=False, regex=True)
    return df[no_eixo & ~excluido]


def recorte_proeja(df):
    """BR-MIGRAR-011: `tipo_programa_curso` contém "EJA"; meta legal >= 10%
    (Decreto 5.840/2006 art. 2º §1º)."""
    return df[df["tipo_programa_curso"].str.contains("EJA", na=False)]


def matriculas_equivalentes(df):
    """BR-MIGRAR-007/012: Matriculas_equivalentes linha a linha, sem excluir
    nenhum tipo de curso (Mulheres Mil incluída no denominador — decisão já
    confirmada, BR-MIGRAR-012). Base para todo percentual desta unit."""
    return df.apply(
        lambda linha: matricula_equivalente(
            linha["tipo_curso_pnp"],
            linha["carga_horaria_total"],
            linha["fec"],
            linha["quantidade_matriculas"],
            linha.get("fech", 1),
        ),
        axis=1,
    )


def _percentual(df, df_recorte, equivalentes):
    total = equivalentes.sum()
    if total == 0:
        return 0.0
    return equivalentes.loc[df_recorte.index].sum() / total


def percentual_tecnico(df):
    equivalentes = matriculas_equivalentes(df)
    return _percentual(df, recorte_tecnico(df), equivalentes)


def percentual_professores(df, exclusoes=EXCLUSOES_PROFESSORES):
    equivalentes = matriculas_equivalentes(df)
    return _percentual(df, recorte_professores(df, exclusoes), equivalentes)


def percentual_proeja(df):
    equivalentes = matriculas_equivalentes(df)
    return _percentual(df, recorte_proeja(df), equivalentes)


def cor_medidor(valor, meta):
    """BR-MIGRAR-024: cor do medidor derivada dinamicamente de `valor >= meta`
    — nos 3 medidores, nunca uma constante de cor duplicada e independente da
    meta (correção do limiar fixo incorreto de ~29,9% do legado para
    Formação de Professores)."""
    return "verde" if valor >= meta else "vermelho"
