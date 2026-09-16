"""Regras de ajuste de nome e eixo de curso do legado — A2, A3 e A5
(`002-baixador-planilhas-sistec`, T027, D-08).

Transcrição literal de
`previaPNP2026_28032025.SemanticModel/definition/tables/dimCurso.tmdl:193-304`
(`_reversa_sdd/code-analysis.md`, itens A2, A3, A5). Fecha o GAP
`mapa_nomes_curso={}` apontado em `app.py:166-170` e `PARITY_REPORT.md` item 3.

O legado aplica os passos nesta ordem sobre `NOME DO CURSO` (cru, maiúsculo,
como vem do Sistec):
1. A2 — 24 substituições de nomes históricos para o nome-padrão PNP
   (`MAPA_NOMES_CURSO`, aplicado por `app/data/transform.t03_normalizar_curso`).
2. A3 — prefixo "TÉCNICO EM " quando o tipo é "TÉCNICO" e falta o prefixo
   (`aplicar_prefixo_tecnico`).
3. (merge com a tabela de fatores, fora deste módulo — D-07)
4. Cosmético, só para exibição: `Text.Proper` + as correções de preposição
   e dois nomes mal codificados do legado (`aplicar_preposicoes_minusculas`).
5. A5 — reclassificação do eixo tecnológico por 17 termos no nome ajustado
   (`reclassificar_eixo_tecnologico`).

O `Table.ReplaceValue` do Power BI substitui por trecho (substring), não por
igualdade exata. As 24 chaves abaixo são nomes de curso completos e
específicos o bastante para que a diferença não importe na prática; um nome
do Sistec que apenas *contenha* uma dessas chaves como trecho (e não seja
exatamente ela) não é coberto por este mapa — risco a monitorar na primeira
baixa real (ver `roadmap.md` §9, "casamento por nome" já é risco conhecido).
"""

# A2 (dimCurso.tmdl:193-216): 24 substituições, na ordem em que o legado encadeia.
MAPA_NOMES_CURSO = {
    "CURSO TÉCNICO EM AGROINDÚSTRIA INTEGRADO AO ENSINO MÉDIO NA MODALIDADE DE EDUCAÇÃO DE JOPVENS E ADULTOS-PROEJA": "TÉCNICO EM AGROINDÚSTRIA",
    "CURSO TÉCNICO EM AGROECOLOGIA - MODALIDADE INTEGRADO AO ENSINO MÉDIO": "TÉCNICO EM AGROECOLOGIA",
    "CURSO TÉCNICO EM MANUTENÇÃO E SUPORTE DE INFORMÁTICA-PROEJA": "TÉCNICO EM MANUTENÇÃO E SUPORTE DE INFORMÁTICA",
    "CURSO TÉCNICO EM AGROINDÚSTRIA COM ÊNFASE EM PRODUTOS DE ORIGEM ANIMAL-PROEJA": "TÉCNICO EM AGROINDÚSTRIA",
    "LICENCIATURA EM COMPUTAÇÃO": "COMPUTAÇÃO",
    "MANUTENÇÃO E SUPORTE DE INFORMÁTICA": "MANUTENÇÃO E SUPORTE EM INFORMÁTICA",
    "TECNICO EM AGROPECUÁRIA - HABILITAÇÃO EM AGRICULTURA": "TÉCNICO EM AGROPECUÁRIA",
    "TECNOLOGIA EM SISTEMAS PARA INTERNET": "SISTEMAS PARA INTERNET",
    "TECNOLOGIA EM ESTÉTICA E COSMÉTICA": "ESTÉTICA E COSMÉTICA",
    "CURSO DE FORMAÇÃO PEDAGÓGICA DE PROFESSORES PARA EDUCAÇÃO PROFISSIONAL - EAD": "PROGRAMA ESPECIAL DE FORMAÇÃO PEDAGÓGICA DE DOCENTES",
    "FORMAÇÃO PEDAGÓGICA DE PROFESSORES PARA EDUCAÇÃO PROFISSIONAL - EAD": "PROGRAMA ESPECIAL DE FORMAÇÃO PEDAGÓGICA DE DOCENTES",
    "FORMAÇÃO PEDAGÓGICA DE PROFESSORES PARA EDUCAÇÃO PROFISSIONAL": "PROGRAMA ESPECIAL DE FORMAÇÃO PEDAGÓGICA DE DOCENTES",
    "CURSO DE PROGRAMA ESPECIAL DE FORMAÇÃO PEDAGÓGICA DE DOCENTES": "PROGRAMA ESPECIAL DE FORMAÇÃO PEDAGÓGICA DE DOCENTES",
    "EDUCAÇÃO DO CAMPO - CIÊNCIAS AGRÁRIAS": "EDUCAÇÃO DO CAMPO",
    "LICENCIATURA EM EDUCAÇÃO DO CAMPO - CIÊNCIAS DA NATUREZA": "EDUCAÇÃO DO CAMPO",
    "TECNOLOGIA EM ALIMENTOS": "ALIMENTOS",
    "PÓS COLHEITA DE GRÃOS": "TÉCNICO EM PÓS-COLHEITA",
    "TECNICO EM AGROPECUÁRIA - HABILITAÇÃO EM AGROINDÚSTRIA": "TÉCNICO EM AGROPECUÁRIA",
    "TÉCNICO EM GERÊNCIA EM SAÚDE": "TÉCNICO EM GERÊNCIA DE SAÚDE",
    "TÉCNICO EM AGROPECUÁRIA - HABILITAÇÃO EM ZOOTECNIA": "TÉCNICO EM AGROPECUÁRIA",
    "TECNOLOGIA EM AGRONEGÓCIO": "AGRONEGÓCIO",
    "GESTÃO DO AGRONEGÓCIO": "AGRONEGÓCIO",
    "AGRICULTURA DE PRECISÃO": "TÉCNICO EM AGRICULTURA",
    "BACHARELADO EM QUÍMICA INDUSTRIAL": "QUÍMICA",
}

# A3 (dimCurso.tmdl:224-231).
_PREFIXO_TECNICO = "TÉCNICO EM "


def aplicar_prefixo_tecnico(nome_curso, tipo_curso_pnp):
    """A3: se o tipo (já com trim) é "TÉCNICO" e o nome não começa com
    "TÉCNICO EM" (comparação sem diferenciar maiúsculas), prefixa "TÉCNICO EM "."""
    if str(tipo_curso_pnp).strip() != "TÉCNICO":
        return nome_curso
    if nome_curso.upper().startswith("TÉCNICO EM"):
        return nome_curso
    return _PREFIXO_TECNICO + nome_curso


# Correções cosméticas de preposição em "NOME DO CURSO AJUSTADO", aplicadas
# depois de um Text.Proper equivalente (dimCurso.tmdl:260-273), na ordem do
# legado, mais dois nomes mal codificados do legado (dimCurso.tmdl:274-276)
# corrigidos no mesmo bloco.
_CORRECOES_APOS_PROPER = [
    (" Em ", " em "),
    (" De ", " de "),
    (" E ", " e "),
    (" À ", " à "),
    (" Para ", " para "),
    (" Do ", " do "),
    (" Nas ", " nas "),
    (" A ", " a "),
    (" Na ", " na "),
    (" Os ", " os "),
    (" Nos ", " nos "),
    (" Da ", " da "),
    (" Com ", " com "),
    (" Ead ", " EAD "),
    ("Pós-Graduação Emeducação Profissional e Tecnológica", "Pós-Graduação em Educação Profissional e Tecnológica"),
    ("Curso de Educação de Jovens e Adultos Integrada à Educação Profissional e Tecnológica ? Operador de Computador", "Operador de Computador"),
    ("Curso de Educação de Jovens e Adultos Integrada à Educação Profissional e Tecnológica ? Padeiro", "Padeiro"),
]


def aplicar_preposicoes_minusculas(nome_curso_proper):
    """Aplica, na ordem do legado, as correções de preposição e os dois nomes
    mal codificados sobre um nome já em Text.Proper (uma palavra maiúscula
    por vez). Não faz o Text.Proper em si — isso é responsabilidade de quem
    chama, com a biblioteca de capitalização escolhida para PT-BR."""
    resultado = nome_curso_proper
    for origem, destino in _CORRECOES_APOS_PROPER:
        resultado = resultado.replace(origem, destino)
    return resultado


# A5 (dimCurso.tmdl:277-304): 17 termos, qualquer um presente no nome ajustado
# reclassifica o eixo tecnológico.
_TERMOS_DESENVOLVIMENTO_EDUCACIONAL_SOCIAL = [
    "Ensino",
    "Docência",
    "Escolar",
    "Educação",
    "Práticas Educativas",
    "Metodologias Ativas",
    "Tecnologias Digitais",
    "Ead",
    "Espanhol",
    "Italiana",
    "Professores",
    "Deficiência",
    "Hablando",
    "English",
    "Inglês",
    "Libras",
    "Redação",
]

EIXO_DESENVOLVIMENTO_EDUCACIONAL_SOCIAL = "DESENVOLVIMENTO EDUCACIONAL E SOCIAL"


def reclassificar_eixo_tecnologico(nome_curso_ajustado, eixo_tecnologico_original):
    """A5: se qualquer um dos 17 termos aparece no nome ajustado (substring,
    sem diferenciar maiúsculas), o eixo vira "DESENVOLVIMENTO EDUCACIONAL E
    SOCIAL"; senão herda o eixo original vindo da planilha de ciclo."""
    nome_lower = nome_curso_ajustado.lower()
    if any(termo.lower() in nome_lower for termo in _TERMOS_DESENVOLVIMENTO_EDUCACIONAL_SOCIAL):
        return EIXO_DESENVOLVIMENTO_EDUCACIONAL_SOCIAL
    return eixo_tecnologico_original
