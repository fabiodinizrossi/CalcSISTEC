"""BC-02 (Núcleo de Matrículas, shared kernel): contagens de matrícula por status.

Depende apenas de `app/domain/shared.py` (ordem de dependência em
`app/domain/contrato.py`, Tarefa 04). Toda função recebe `filtros: FiltrosAtivos`
como parâmetro explícito. Implementado na Tarefa 06 do plano de reconstrução,
a partir de `_reversa_sdd/migration/target_architecture.md` (seção BC-02) e
`_reversa_sdd/migration/target_business_rules.md` (BR-MIGRAR-004, 005, 014).

`taxa_evasao()` e `filtrar_fic()` adicionados na Tarefa 11, após
`parity_tests/02-contagem-evasao.feature` e
`parity_tests/06-eixo-dinamico-e-fic.feature` exigirem, respectivamente, uma
função dedicada de taxa (com proteção de divisão por zero) e a correção do
toggle FIC para excluir apenas Formação Inicial/Continuada, nunca Mulheres
Mil (BR-MIGRAR-021) — a Tarefa 06 havia deixado essa função de fora do
escopo por depender de uma coluna (`categoria_origem_curso`) que só foi
criada na Tarefa 11.
"""

from app.domain.contrato import FiltrosAtivos
from app.domain.shared import eh_evadido

# BR-MIGRAR-021: conjunto FIC = exatamente Formação Inicial + Formação
# Continuada, SEM Mulheres Mil — usa `categoria_origem_curso` (preservada
# antes do colapso de BR-MIGRAR-017 em `tipo_curso_pnp`, Tarefa 11), nunca
# `tipo_curso_pnp` (que já colapsou as 3 categorias e não permite distinguir).
CATEGORIAS_FIC = {"FORMAÇÃO INICIAL", "FORMAÇÃO CONTINUADA"}


def _aplicar_filtros(df, filtros: FiltrosAtivos):
    """Filtros comuns a toda contagem de `matriculas`: ano-base (BR-MIGRAR-016,
    sempre parâmetro explícito), campus e curso quando selecionados."""
    filtrado = df[df["ano_base"] == filtros.ano_base]
    if filtros.campus is not None:
        filtrado = filtrado[filtrado["co_unidade"] == filtros.campus]
    if filtros.curso is not None:
        filtrado = filtrado[filtrado["codigo_portfolio"] == filtros.curso]
    return filtrado


def contar_por_status(df, filtros: FiltrosAtivos, status):
    """BR-MIGRAR-004: contagens devem filtrar por `status_corrigido`
    (BR-MIGRAR-003), nunca pelo status cru como o legado faz hoje."""
    filtrado = _aplicar_filtros(df, filtros)
    return int((filtrado["status_corrigido"] == status).sum())


def contar_evadidos(df, filtros: FiltrosAtivos):
    """BR-MIGRAR-005/006: usa a definição única de evasão de `shared.eh_evadido`
    (7 status, incluindo REPROVADO/REPROVADA)."""
    filtrado = _aplicar_filtros(df, filtros)
    return int(filtrado["status_corrigido"].apply(eh_evadido).sum())


def contar_matriculas(df, filtros: FiltrosAtivos):
    """Total de matrículas atendidas (grão de BR-MIGRAR-001, já aplicado na
    ingestão) dentro dos filtros ativos."""
    return int(len(_aplicar_filtros(df, filtros)))


def taxa_evasao(df, filtros: FiltrosAtivos):
    """Taxa de evasão = evadidos / total, com proteção explícita de divisão
    por zero (0, nunca erro) — `parity_tests/02-contagem-evasao.feature`."""
    total = contar_matriculas(df, filtros)
    if total == 0:
        return 0.0
    return contar_evadidos(df, filtros) / total


def filtrar_fic(df, incluir_fic):
    """BR-MIGRAR-021: toggle COM FIC / SEM FIC. SEM FIC exclui apenas
    Formação Inicial e Formação Continuada — Mulheres Mil permanece visível
    (`parity_tests/06-eixo-dinamico-e-fic.feature`, cenário crítico)."""
    if incluir_fic:
        return df
    return df[~df["categoria_origem_curso"].isin(CATEGORIAS_FIC)]


def contar_cursos_ativos(df_cursos, filtros: FiltrosAtivos):
    """BR-MIGRAR-014: contagem de cursos ativos por `codigo_portfolio` (chave
    única real), não mais pela `CHAVE_CURSO` sintética e sujeita a colisão do
    legado. `df_cursos` já vem sem duplicidade de chave (rejeitada na
    ingestão, Tarefa 05)."""
    filtrado = df_cursos
    if filtros.campus is not None:
        filtrado = filtrado[filtrado["co_unidade"] == filtros.campus]
    return int(filtrado["codigo_portfolio"].nunique())
