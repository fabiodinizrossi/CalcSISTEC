"""Dados sintéticos do Sistec no formato real das exportações (`002-baixador-
planilhas-sistec`, T062).

Gera as planilhas de ciclo e de matrícula com a estrutura exata que o Sistec
exporta (CSV separado por `;`, codificação cp1252): 37 colunas na de ciclo e
26 na de matrícula, com cursos e alunos fictícios — sem nenhum dado pessoal
real. O painel lê só as colunas da lista de permissão
(`app/sistec/colunas.py`) por cabeçalho; as demais (inclusive CPF e nome,
preenchidos aqui com valores obviamente fictícios) são descartadas na leitura
(defesa em profundidade).

Serve ao Sistec simulado (`scripts/sistec_simulado.py`) e, se necessário, a
gerar arquivos de teste em disco.

A geração é determinística por `co_unidade` (semente fixa), para que ciclo e
matrícula da mesma unidade casem no `CODIGO_CICLO_MATRICULA`.
"""

import random

ANO_BASE = 2026

# ---- Cabeçalhos no formato real do Sistec ---------------------------------

CABECALHO_CICLO = (
    "UF;MUNICIPIO;SISTEMA DE ENSINO;DEPENDÊNCIA ADMINISTRATIVA;"
    "SUB-DEPENDÊNCIA ADMINISTRATIVA;TIPO DE ESCOLA;NOME UNIDADE DE ENSINO;"
    "CÓDIGO UNIDADE DE ENSINO;CÓDIGO INSTITUIÇÃO;SUBTIPO CURSOS;"
    "CÓDIGO CURSO;NOME DO CURSO;CARGA HORÁRIA MÍNIMA;OFERTA;"
    "CÓDIGO CICLO DE MATRÍCULA;CICLO DE MATRÍCULA;CARGA HORÁRIA TOTAL;"
    "DATA INÍCIO DO CURSO;DATA FIM PREVISTO DO CURSO;MODALIDADE ENSINO;"
    "STATUS DO CICLO DE MATRÍCULA;SITUAÇÃO DO CICLO ;TIPO OFERTA DO CURSO;"
    "TIPO PROGRAMA DO CURSO;EIXO TECNOLÓGICO;"
    "SITUAÇÃO SE POSSUI ESTÁGIO: SIM OU NÃO?;CARGA HORÁRIA ESTÁGIO;"
    "PROJETO PEDAGÓGICO;SITUAÇÃO ETEC;CÓDIGO DO PORTFÓLIO;"
    "CÓDIGO DO POLO;QTD DE VAGAS;QTD DE INSCRITOS;QTD DE MATRICULAS;"
    "DATA_CRIACAO;NOME_RESPONSAVEL;CPF\r\n"
)

CABECALHO_MATRICULA = (
    "CO_ALUNO_IDENTIFICADO;CO_ALUNO;NO_ALUNO;NO_MAE_ALUNO;SG_SEXO;"
    "DT_DATA_NASCIMENTO;NU_CPF;DS_EMAIL;CO_PESSOA_FISICA_ALUNO;DS_SENHA;"
    "CO_MATRICULA;CO_CICLO_MATRICULA;CO_CURSO;NU_CARGA_HORARIA;"
    "DT_DATA_INICIO;DT_DATA_FIM_PREVISTO;CO_PERIODO_CADASTRO;"
    "NO_CICLO_MATRICULA;CO_TIPO_OFERTA_CURSO;CO_TIPO_INSTITUICAO;"
    "CO_PORTFOLIO;NU_VAGAS_OFERTADAS;NU_TOTAL_INSCRITOS;"
    "NO_STATUS_MATRICULA;CO_UNIDADE_ENSINO;MES_DE_OCORRENCIA\r\n"
)

# ---- Catálogo de cursos/ciclos por unidade --------------------------------
#
# `fim` em 2025 alimenta a Eficiência Acadêmica (ciclos com fim previsto no
# ano-base - 1); `fim` >= 2026 são os ciclos ainda ativos (matrículas EM_CURSO).

CURSOS = [
    ("TÉCNICO EM INFORMÁTICA", "TÉCNICO", "INFORMAÇÃO E COMUNICAÇÃO", "INTEGRADO", "ENSINO MÉDIO", 3200, 3000, 2022, 2025),
    ("TÉCNICO EM INFORMÁTICA", "TÉCNICO", "INFORMAÇÃO E COMUNICAÇÃO", "INTEGRADO", "ENSINO MÉDIO", 3200, 3000, 2024, 2027),
    ("TÉCNICO EM AGROPECUÁRIA", "TÉCNICO", "RECURSOS NATURAIS", "INTEGRADO", "ENSINO MÉDIO", 3360, 3200, 2023, 2026),
    ("TÉCNICO EM ADMINISTRAÇÃO", "TÉCNICO", "GESTÃO E NEGÓCIOS", "SUBSEQUENTE", "EDUCAÇÃO PROFISSIONAL TÉCNICA", 800, 800, 2024, 2026),
    ("TÉCNICO EM ELETROTÉCNICA", "TÉCNICO", "CONTROLE E PROCESSOS INDUSTRIAIS", "INTEGRADO", "ENSINO MÉDIO", 3200, 3000, 2022, 2025),
    ("FIC INFORMÁTICA BÁSICA", "FORMAÇÃO CONTINUADA", "INFORMAÇÃO E COMUNICAÇÃO", "FORMAÇÃO INICIAL E CONTINUADA", "FIC", 200, 160, 2025, 2025),
]

NOMES = [
    "ANA", "BRUNO", "CARLA", "DIEGO", "ELISA", "FELIPE", "GABRIELA", "HENRIQUE",
    "ISABELA", "JOÃO", "LARISSA", "MARCOS", "NATÁLIA", "OTÁVIO", "PAULA", "RAFAEL",
    "SABRINA", "THIAGO", "VANESSA", "WILLIAM", "YASMIN", "EDUARDO", "FERNANDA",
    "GUSTAVO", "HELENA",
]
SOBRENOMES = [
    "SILVA", "SANTOS", "OLIVEIRA", "SOUZA", "PEREIRA", "COSTA", "RODRIGUES",
    "ALMEIDA", "NUNES", "MARTINS", "GOMES", "ROCHA", "RIBEIRO", "CARVALHO", "LIMA",
]


def _catalogo_ciclos(co_unidade):
    """Ciclos determinísticos de uma unidade: (codigo, nome, sub_tipo, eixo,
    oferta, programa, carga, carga_min, inicio, fim)."""
    ciclos = []
    for indice, (nome, sub_tipo, eixo, oferta, programa, carga, carga_min, inicio, fim) in enumerate(CURSOS, start=1):
        codigo = f"{co_unidade}{indice:02d}"
        ciclos.append(
            {
                "codigo": codigo,
                "portfolio": f"{co_unidade}9{indice}",
                "nome": nome,
                "sub_tipo": sub_tipo,
                "eixo": eixo,
                "oferta": oferta,
                "programa": programa,
                "carga": carga,
                "carga_min": carga_min,
                "inicio": inicio,
                "fim": fim,
            }
        )
    return ciclos


def _rng(co_unidade):
    return random.Random(f"sintetico-{co_unidade}")


def _nome_ficticio(rng):
    return f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}"


def _cpf_ficticio(rng):
    return f"{rng.randint(0, 99999999999):011d}"


def _status_aluno(rng, fim):
    """Distribuição realista: ciclos concluídos concentram concluídos/evadidos;
    ciclos ativos concentram EM_CURSO."""
    if fim <= ANO_BASE - 1:
        return rng.choices(
            ["CONCLUÍDA", "ABANDONO", "DESLIGADO", "TRANSF_EXT", "INTEGRALIZADA", "REPROVADO", "EM_CURSO"],
            weights=[5, 2, 1, 1, 1, 1, 1],
        )[0]
    return rng.choices(
        ["EM_CURSO", "ABANDONO", "TRANSF_EXT", "REPROVADO"],
        weights=[8, 1, 1, 1],
    )[0]


def _mes_ocorrencia(rng, fim):
    ano = min(fim, ANO_BASE)
    mes = rng.randint(1, 12)
    return f"{mes:02d}/{ano}"


def _data(fmt_ano, rng):
    mes = rng.randint(1, 12)
    dia = rng.randint(1, 28)
    return f"{dia:02d}/{mes:02d}/{fmt_ano}"


def csv_ciclo(co_unidade, nome_unidade):
    """Texto CSV (cp1252) da planilha de ciclo de uma unidade."""
    rng = _rng(co_unidade)
    linhas = [CABECALHO_CICLO]
    for ciclo in _catalogo_ciclos(co_unidade):
        vagas = 40
        matriculas = rng.randint(18, 30)
        inscritos = matriculas + rng.randint(2, 8)
        campos = [
            "RS",
            nome_unidade,
            "FEDERAL",
            "FEDERAL",
            "",
            "INSTITUTO FEDERAL",
            f"INSTITUTO FEDERAL FARROUPILHA - {nome_unidade.upper()}",
            co_unidade,
            "1559",
            ciclo["sub_tipo"],
            ciclo["portfolio"],
            ciclo["nome"],
            str(ciclo["carga_min"]),
            ciclo["oferta"],
            ciclo["codigo"],
            f"{ciclo['inicio']}/{ciclo['inicio'] + 1}",
            str(ciclo["carga"]),
            _data(ciclo["inicio"], rng),
            _data(ciclo["fim"], rng),
            "PRESENCIAL",
            "EM_ANDAMENTO" if ciclo["fim"] >= ANO_BASE else "CONCLUÍDO",
            "ATIVO",
            ciclo["oferta"],
            ciclo["programa"],
            ciclo["eixo"],
            "NÃO",
            "0",
            "NOVO",
            "",
            ciclo["portfolio"],
            "",
            str(vagas),
            str(inscritos),
            str(matriculas),
            _data(ciclo["inicio"], rng),
            "RESPONSAVEL FICTICIO",
            _cpf_ficticio(rng),
        ]
        linhas.append(";".join(campos) + "\r\n")
    return "".join(linhas)


def csv_matricula(co_unidade, nome_unidade):
    """Texto CSV (cp1252) da planilha de matrícula de uma unidade, casando com
    os ciclos de `csv_ciclo` pelo `CODIGO_CICLO_MATRICULA`."""
    rng = _rng(co_unidade)
    linhas = [CABECALHO_MATRICULA]
    sequencia = 1
    for ciclo in _catalogo_ciclos(co_unidade):
        for _ in range(rng.randint(18, 30)):
            status = _status_aluno(rng, ciclo["fim"])
            campos = [
                f"{sequencia:07d}",                      # CO_ALUNO_IDENTIFICADO
                f"{sequencia:07d}",                      # CO_ALUNO
                _nome_ficticio(rng),                     # NO_ALUNO
                _nome_ficticio(rng),                     # NO_MAE_ALUNO
                rng.choice("MF"),                        # SG_SEXO
                _data(rng.randint(1995, 2008), rng),     # DT_DATA_NASCIMENTO
                _cpf_ficticio(rng),                      # NU_CPF
                "aluno.ficticio@exemplo.edu.br",         # DS_EMAIL
                f"{sequencia:011d}",                     # CO_PESSOA_FISICA_ALUNO
                "senha-ficticia",                        # DS_SENHA
                f"{co_unidade}{sequencia:05d}",          # CO_MATRICULA
                ciclo["codigo"],                         # CO_CICLO_MATRICULA
                ciclo["portfolio"],                      # CO_CURSO
                str(ciclo["carga"]),                     # NU_CARGA_HORARIA
                _data(ciclo["inicio"], rng),             # DT_DATA_INICIO
                _data(ciclo["fim"], rng),                # DT_DATA_FIM_PREVISTO
                str(ciclo["inicio"]),                    # CO_PERIODO_CADASTRO
                f"{ciclo['inicio']}/{ciclo['inicio'] + 1}",  # NO_CICLO_MATRICULA
                ciclo["oferta"],                         # CO_TIPO_OFERTA_CURSO
                "FEDERAL",                               # CO_TIPO_INSTITUICAO
                ciclo["portfolio"],                      # CO_PORTFOLIO
                "40",                                    # NU_VAGAS_OFERTADAS
                "45",                                    # NU_TOTAL_INSCRITOS
                status,                                  # NO_STATUS_MATRICULA
                co_unidade,                              # CO_UNIDADE_ENSINO
                _mes_ocorrencia(rng, ciclo["fim"]),      # MES_DE_OCORRENCIA
            ]
            linhas.append(";".join(campos) + "\r\n")
            sequencia += 1
    return "".join(linhas)
