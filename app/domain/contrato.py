"""Filtros explícitos e ordem de dependência entre os módulos de domínio.

As funções de cálculo recebem os filtros por parâmetro e não dependem de
estado global. Os módulos de indicadores dependem dos módulos de matrículas,
nunca no sentido inverso.
"""

from dataclasses import dataclass
from typing import Literal, Optional

# Cada filtro escolhe um único eixo de quebra entre as seis dimensões possíveis.
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
    """Filtros ativos passados explicitamente às funções de domínio.

    Campos:
        ano_base: ano usado nos cálculos, sem literal fixo nas funções.
        campus: `co_unidade` selecionado, ou `None` para "todos".
        curso: `codigo_portfolio` selecionado, ou `None` para "todos".
        eixo: dimensão de quebra ativa.
        incluir_fic: estado do controle COM FIC / SEM FIC; a página escolhe o padrão.
    """

    ano_base: int
    campus: Optional[str] = None
    curso: Optional[str] = None
    eixo: EixoQuebra = "campus"
    incluir_fic: bool = False


# Ordem de dependência: os indicadores usam as regras de matrículas, não o inverso.
ORDEM_DEPENDENCIA = (
    "app.data",                      # Ingestão produz os DataFrames de entrada.
    "app.domain.shared",             # Regras comuns e eixo dinâmico.
    "app.domain.matriculas",         # Contagens por status.
    "app.domain.percentuais_legais", # Recortes legais.
    "app.domain.eficiencia",         # Eficiência acadêmica.
    "app.pages",                     # Apresentação consome os indicadores.
)
