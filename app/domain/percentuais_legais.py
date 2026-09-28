"""Recortes e percentuais legais para Técnico, Professores e PROEJA.

Todas as funções recebem uma única base já consolidada `df` — uma linha por
combinação curso x ciclo com as colunas: `tipo_curso_pnp`, `subtipo_curso`,
`eixo_tecnologico_ajustado`, `carga_horaria_total`, `fec`, `tipo_programa_curso`
(do ciclo) e `quantidade_matriculas` (contagem de matrículas atendidas nessa
combinação, já filtrada por `FiltrosAtivos` a montante) — e usam a mesma regra
de matrícula equivalente.
"""

from app.domain.shared import matricula_equivalente

META_TECNICO = 0.50
META_PROFESSORES = 0.20
META_PROEJA = 0.10

EIXO_PROFESSORES = "DESENVOLVIMENTO EDUCACIONAL E SOCIAL"

# Lista de cursos excluídos do recorte de Formação de Professores.
EXCLUSOES_PROFESSORES = {
    "CERVEJEIRO",
    "FORMAÇÃO COMPLEMENTAR AO ENSINO FUNDAMENTAL",
    "RELAÇÕES COM SAÚDE",
    "JOVENS ATLETAS",
    "BELEZA E GÊNERO",
}


def recorte_tecnico(df):
    """Seleciona cursos do subtipo Técnico; a meta legal é de 50%."""
    return df[df["subtipo_curso"] == "Técnico"]


def recorte_professores(df, exclusoes=EXCLUSOES_PROFESSORES):
    """Seleciona o eixo Desenvolvimento Educacional e Social, com exclusões.

    Exclui cursos cujo nome contenha qualquer termo da lista, inclusive quando
    o termo é parte de um nome maior. A meta legal é de 20%.
    """
    no_eixo = df["eixo_tecnologico_ajustado"] == EIXO_PROFESSORES
    nomes = df["nome_curso_ajustado"].str.upper()
    padrao = "|".join(exclusoes)
    excluido = nomes.str.contains(padrao, na=False, regex=True)
    return df[no_eixo & ~excluido]


def recorte_proeja(df):
    """Seleciona programas cujo tipo contém EJA; a meta legal é de 10%."""
    return df[df["tipo_programa_curso"].str.contains("EJA", na=False)]


def matriculas_equivalentes(df):
    """Calcula matrículas equivalentes por linha para o denominador comum.

    Nenhum tipo de curso é excluído; Mulheres Mil também entra no denominador.
    """
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
    """Retorna verde quando o valor alcança a meta, vermelho caso contrário."""
    return "verde" if valor >= meta else "vermelho"
