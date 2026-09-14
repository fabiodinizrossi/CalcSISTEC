"""Contrato único de domínio — Tarefa 04 do plano de reconstrução.

Define, antes de qualquer bounded context ser implementado (Tarefas 06/07):

1. `FiltrosAtivos`: o contrato único de filtros propagado a toda função de
   `app/domain/*` — ano-base, campus, curso e eixo de quebra são sempre um
   parâmetro explícito, nunca estado global (`BR-MIGRAR-016`, `BR-MIGRAR-020`,
   `target_domain_model.md` §"Nota de adaptação ao paradigma").
2. `ORDEM_DEPENDENCIA`: a ordem de chamada entre módulos de domínio,
   equivalente ao grafo de dependência do legado — BC-03 sempre chama BC-02,
   nunca o inverso (`target_architecture.md` §"Bounded contexts").

Regra de assinatura (vale para toda função nova em `app/domain/*`):
    def minha_funcao(df: pd.DataFrame, filtros: FiltrosAtivos, ...) -> ...:
`filtros` é sempre um parâmetro explícito — nunca lido de uma variável de
módulo, `dcc.Store` global ou similar. Isso é o que torna cada função pura e
testável isoladamente (paradigma "procedural rico, estilo funcional leve",
`paradigm_decision.md`).
"""

from dataclasses import dataclass
from typing import Literal, Optional

# Um dos seis eixos de quebra definidos em BR-MIGRAR-020 / target_domain_model.md
# (value object EixoQuebra). Seleção única por construção — nunca lista/multi-select
# (corrige o bug M-D3 do legado, singleSelect=false).
EixoQuebra = Literal[
    "campus",
    "tipo_curso",
    "nome_curso",
    "modalidade",
    "oferta",
    "ciclo",
]


@dataclass(frozen=True)
class FiltrosAtivos:
    """Contrato único de filtros ativos, propagado explicitamente a toda função
    de domínio (`app/domain/shared.py`, `matriculas.py`, `percentuais_legais.py`,
    `eficiencia.py`) e derivado dos controles de `AGG-Apresentacao`.

    Campos:
        ano_base: parâmetro único de ano-base (`BR-MIGRAR-016`), nunca um
            literal espalhado pelas funções de cálculo.
        campus: `co_unidade` selecionado, ou `None` para "todos".
        curso: `codigo_portfolio` selecionado, ou `None` para "todos".
        eixo: dimensão de quebra ativa (`BR-MIGRAR-020`/`BR-MIGRAR-025`).
        incluir_fic: estado do toggle COM FIC / SEM FIC (`BR-MIGRAR-021`).
            Default por página é decidido em `AGG-Apresentacao`, não aqui.
    """

    ano_base: int
    campus: Optional[str] = None
    curso: Optional[str] = None
    eixo: EixoQuebra = "campus"
    incluir_fic: bool = False


# Ordem de chamada entre módulos de domínio (bottom-up, equivalente ao DAG do
# legado). Um módulo nunca importa de um módulo abaixo dele nesta lista na
# direção inversa — ex.: `percentuais_legais.py`/`eficiencia.py` (BC-03) sempre
# importam de `shared.py`/`matriculas.py` (BC-02), nunca o contrário.
ORDEM_DEPENDENCIA = (
    "app.data",                      # BC-01: ingestão — produz os DataFrames de entrada
    "app.domain.shared",             # BC-02: eh_evadido, matricula_equivalente, eixo dinâmico
    "app.domain.matriculas",         # BC-02: contagens por status (usa shared.py)
    "app.domain.percentuais_legais", # BC-03: recortes legais (usa shared.py + matriculas.py)
    "app.domain.eficiencia",         # BC-03: IEA/ENIEA (usa shared.py + matriculas.py)
    "app.pages",                     # BC-04: apresentação (consome BC-02/BC-03, nunca recalcula)
)
