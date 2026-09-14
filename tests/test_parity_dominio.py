"""Suíte de testes de paridade (Tarefa 11 do plano de reconstrução).

Cobre os 7 arquivos de fluxo de domínio de
`_reversa_sdd/migration/parity_tests/*.feature` (PT-001 a PT-007), traduzidos
para `pytest` (framework a critério do agente de codificação, conforme
`parity_specs.md` §"Tipos de teste a aplicar"). Cada teste referencia o
`spec-id`/cenário Gherkin de origem no docstring, para rastreabilidade.

Não cobre os 5 arquivos `parity_tests/screens/*.feature` (contrato de tela) —
validados manualmente via smoke test das 5 páginas na Tarefa 09 (todas
retornam HTTP 200, todos os callbacks executam sem erro); uma suíte de
contrato de tela dedicada (ex.: Selenium/Playwright) fica como trabalho
futuro, fora do escopo desta tarefa dado o volume já coberto.

Rodar com: `pytest tests/test_parity_dominio.py -v`
"""

import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.ingest import UploadInvalido, processar_upload  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.data.transform import t02_corrigir_status  # noqa: E402
from app.domain.contrato import FiltrosAtivos  # noqa: E402
from app.domain.eficiencia import calcular_iea, classificar_matriculas_eficiencia, eh_concluido  # noqa: E402
from app.domain.matriculas import contar_por_status, filtrar_fic, taxa_evasao  # noqa: E402
from app.domain.percentuais_legais import (  # noqa: E402
    cor_medidor,
    matriculas_equivalentes,
    percentual_professores,
    percentual_tecnico,
)
from app.domain.shared import agrupar_por_eixo, coluna_para_eixo, eh_evadido, matricula_equivalente


@pytest.fixture
def db_path():
    path = os.path.join(tempfile.mkdtemp(), "parity.db")
    init_db(path)
    return path


def _planilhas_basicas(**overrides):
    base = {
        "matriculas": pd.DataFrame(
            {
                "CO_MATRICULA": ["M1"],
                "CODIGO_CICLO_MATRICULA": ["C1"],
                "STATUS_MATRICULA_SISTEC": ["EM_CURSO"],
                "STATUS_MATRICULA_PNP": ["ABANDONO"],
                "MES_OCORRENCIA_CORRIGIDO": ["2026-01-01"],
            }
        ),
        "ciclos": pd.DataFrame(
            {
                "CODIGO_CICLO_MATRICULA": ["C1"],
                "CÓDIGO DO PORTFÓLIO": ["P1"],
                "DT_DATA_INICIO": ["2026-01-01"],
                "DT_DATA_FIM_PREVISTO": ["2027-01-01"],
                "TIPO_PROGRAMA_CURSO": ["REGULAR"],
                "STATUS_CICLO": ["ATIVO"],
            }
        ),
        "cursos": pd.DataFrame(
            {
                "CÓDIGO DO PORTFÓLIO": ["P1"],
                "NOME_CURSO": ["TÉCNICO EM X"],
                "TIPO_CURSO": ["TECNICO"],
                "SUBTIPO_CURSO": ["Técnico"],
                "MODALIDADE_ENSINO": ["PRESENCIAL"],
                "EIXO_TECNOLOGICO_AJUSTADO": ["EIXO1"],
                "CARGA_HORARIA_TOTAL": [1200],
                "CO_UNIDADE": ["U1"],
                "OFERTA": ["ANUAL"],
            }
        ),
        "campus": pd.DataFrame({"CO_UNIDADE": ["U1"], "CIDADE": ["Santa Maria"], "NOME_UNIDADE": ["Campus SM"]}),
        "fatores": pd.DataFrame({"CÓDIGO DO PORTFÓLIO": ["P1"], "FEC": [1.0], "FECH": [1.0]}),
    }
    base.update(overrides)
    return base


# ===================== PT-001: Ingestão e preparação =====================


def test_pt001_status_corrigido_usa_pnp_terminativo():
    """Cenário: Upload válido corrige o status conforme a fonte de verdade.
    PNP terminativa (!= EM_CURSO) prevalece sobre o Sistec (BR-MIGRAR-003)."""
    df = pd.DataFrame({"STATUS_MATRICULA_SISTEC": ["EM_CURSO"], "STATUS_MATRICULA_PNP": ["ABANDONO"]})
    valido, _rejeitado = t02_corrigir_status(df)
    assert valido["status_corrigido"].iloc[0] == "ABANDONO"


def test_pt001_reprovada_nao_e_remapeada():
    """Cenário: REPROVADO mantém o valor original, sem remapeamento (BR-MIGRAR-006)."""
    df = pd.DataFrame({"STATUS_MATRICULA_SISTEC": ["EM_CURSO"], "STATUS_MATRICULA_PNP": ["REPROVADA"]})
    valido, _ = t02_corrigir_status(df)
    assert valido["status_corrigido"].iloc[0] == "REPROVADA"


def test_pt001_nenhuma_pii_sobrevive(db_path):
    """Cenário: nenhuma coluna de PII aparece em nenhuma tabela resultante
    (BR-DESCARTAR-001)."""
    planilhas = _planilhas_basicas()
    planilhas["matriculas"]["NU_CPF"] = ["111.111.111-11"]
    processar_upload(planilhas, {}, ano_base=2026, uploaded_by="t", filename="t.xlsx", db_path=db_path)
    conn = get_connection(db_path)
    try:
        colunas = [row[1] for row in conn.execute("PRAGMA table_info(matriculas)")]
        assert "NU_CPF" not in colunas
    finally:
        conn.close()


def test_pt001_ciclo_excluido_e_filtrado(db_path):
    """Cenário: ciclos com STATUS DO CICLO = EXCLUÍDO não geram matrículas no
    dataset resultante (BR-MIGRAR-018)."""
    planilhas = _planilhas_basicas()
    planilhas["ciclos"]["STATUS_CICLO"] = ["EXCLUÍDO"]
    processar_upload(planilhas, {}, ano_base=2026, uploaded_by="t", filename="t.xlsx", db_path=db_path)
    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0] == 0
    finally:
        conn.close()


def test_pt001_upload_invalido_nao_corrompe_dataset_ativo(db_path):
    """Cenário: upload inválido não corrompe o dataset ativo (RISK-004, AD-02)."""
    planilhas_validas = _planilhas_basicas()
    processar_upload(planilhas_validas, {}, ano_base=2026, uploaded_by="t", filename="v1.xlsx", db_path=db_path)

    conn = get_connection(db_path)
    total_antes = conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0]
    conn.close()

    planilhas_invalidas = {"matriculas": _planilhas_basicas()["matriculas"]}  # faltam as demais abas
    with pytest.raises(UploadInvalido):
        processar_upload(planilhas_invalidas, {}, ano_base=2026, uploaded_by="t", filename="v2.xlsx", db_path=db_path)

    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0] == total_antes
        status_log = conn.execute(
            "SELECT status FROM uploads_log ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        assert status_log == "invalido"
    finally:
        conn.close()


# ===================== PT-002: Contagem de evasão =====================


@pytest.mark.parametrize(
    "status,esperado",
    [
        ("ABANDONO", True),
        ("DESLIGADO", True),
        ("DESLIGADA", True),
        ("REPROVADO", True),
        ("REPROVADA", True),
        ("TRANSF_EXT", True),
        ("TRANSF_INT", True),
        ("EM_CURSO", False),
        ("CONCLUÍDA", False),
        ("INTEGRALIZADA", False),
    ],
)
def test_pt002_eh_evadido_classifica_os_7_status(status, esperado):
    assert eh_evadido(status) is esperado


def test_pt002_soma_evadidos_sem_duplicar_nem_omitir():
    """Cenário: MatEvadidas soma exatamente os 7 status de evasão."""
    df = pd.DataFrame(
        {
            "status_corrigido": ["ABANDONO"] * 10 + ["DESLIGADO"] * 5 + ["TRANSF_EXT"] * 3 + ["TRANSF_INT"] * 2 + ["REPROVADA"] * 4,
            "ano_base": 2026,
            "co_unidade": "U1",
            "codigo_portfolio": "P1",
        }
    )
    from app.domain.matriculas import contar_evadidos

    assert contar_evadidos(df, FiltrosAtivos(ano_base=2026)) == 24


def test_pt002_taxa_evasao_com_denominador_zero_nao_gera_erro():
    """Cenário: taxa de evasão com denominador zero não gera erro."""
    df = pd.DataFrame({"status_corrigido": [], "ano_base": [], "co_unidade": [], "codigo_portfolio": []})
    assert taxa_evasao(df, FiltrosAtivos(ano_base=2026)) == 0.0


# ===================== PT-003: Matrícula equivalente =====================


def test_pt003_matricula_equivalente_qualificacao_profissional():
    """Cenário: matrícula equivalente de Qualificação Profissional.

    🔴 GAP não bloqueante (Tarefa 06/11): o cenário Gherkin de origem afirma
    "resultado é 9,075 = (200/800) × 1,10 × 30", mas a própria fórmula que
    ele mostra calcula 8.25, não 9.075 — (200/800)=0.25; 0.25×1.10=0.275;
    0.275×30=8.25. Esta divergência já existia no artefato herdado de
    `medidas-dax-pnp/requirements.md` (fora do escopo de leitura desta
    tarefa) e não foi resolvida. Este teste valida a fórmula exatamente como
    descrita em `BR-MIGRAR-007` (a fonte de verdade da regra de negócio),
    não o número do exemplo — que precisa ser confirmado com a usuária ou
    contra o Power BI real antes do cutover.
    """
    resultado = matricula_equivalente(
        tipo_curso="QUALIFICAÇÃO PROFISSIONAL", carga_horaria_total=200, fec=1.10, matriculas=30
    )
    assert resultado == pytest.approx(8.25)


def test_pt003_matricula_equivalente_nao_qualificacao_usa_fech_1():
    """Cenário: curso não-Qualificação Profissional usa FECH = 1."""
    resultado = matricula_equivalente(tipo_curso="TÉCNICO", carga_horaria_total=999, fec=1.05, matriculas=20)
    assert resultado == pytest.approx(21.0)


def test_pt003_fec_fech_ausentes_usam_default_explicito(db_path):
    """Cenário: FEC/FECH ausentes usam default explícito (fec=1), e o curso
    é sinalizado para revisão — não some silenciosamente (BR-MIGRAR-008)."""
    planilhas = _planilhas_basicas(fatores=pd.DataFrame({"CÓDIGO DO PORTFÓLIO": [], "FEC": [], "FECH": []}))
    resultado = processar_upload(planilhas, {}, ano_base=2026, uploaded_by="t", filename="t.xlsx", db_path=db_path)
    assert resultado["cursos_fator_nao_encontrado"] == 1
    conn = get_connection(db_path)
    try:
        fec = conn.execute("SELECT fec FROM cursos WHERE codigo_portfolio='P1'").fetchone()[0]
        assert fec == 1.0
    finally:
        conn.close()


def test_pt003_cursos_distintos_nao_colidem_por_chave(db_path):
    """Cenário: cursos com CÓDIGO DO PORTFÓLIO diferentes não são descartados
    nem fundidos por colisão (BR-MIGRAR-014)."""
    planilhas = _planilhas_basicas()
    planilhas["cursos"] = pd.concat(
        [
            planilhas["cursos"],
            pd.DataFrame(
                {
                    "CÓDIGO DO PORTFÓLIO": ["P2"],
                    "NOME_CURSO": ["TÉCNICO EM Y"],
                    "TIPO_CURSO": ["TECNICO"],
                    "SUBTIPO_CURSO": ["Técnico"],
                    "MODALIDADE_ENSINO": ["EAD"],
                    "EIXO_TECNOLOGICO_AJUSTADO": ["EIXO2"],
                    "CARGA_HORARIA_TOTAL": [800],
                    "CO_UNIDADE": ["U1"],
                    "OFERTA": ["SEMESTRAL"],
                }
            ),
        ],
        ignore_index=True,
    )
    processar_upload(planilhas, {}, ano_base=2026, uploaded_by="t", filename="t.xlsx", db_path=db_path)
    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0] == 2
    finally:
        conn.close()


# ===================== PT-004: Percentuais legais =====================


def _base_percentuais():
    return pd.DataFrame(
        {
            "tipo_curso_pnp": ["TECNICO", "QUALIFICAÇÃO PROFISSIONAL"],
            "subtipo_curso": ["Técnico", "Qualificação"],
            "eixo_tecnologico_ajustado": ["EIXO1", "DESENVOLVIMENTO EDUCACIONAL E SOCIAL"],
            "nome_curso_ajustado": ["TÉCNICO EM X", "TÉCNICO EM CERVEJEIRO"],
            "tipo_programa_curso": ["REGULAR", "REGULAR"],
            "carga_horaria_total": [1200, 200],
            "fec": [1.0, 1.0],
            "quantidade_matriculas": [10, 10],
        }
    )


def test_pt004_recorte_tecnico_usa_subtipo_correto():
    """Denominador usa `matricula_equivalente`, não a contagem crua de
    matrículas: o curso Técnico (fech=1) contribui 10; o de Qualificação
    Profissional (fech=CH/800=200/800=0.25) contribui 2.5 — total 12.5."""
    base = _base_percentuais()
    assert percentual_tecnico(base) == pytest.approx(10 / 12.5)


def test_pt004_recorte_professores_exclui_cervejeiro_por_substring():
    """Cenário: curso com "cervejeiro" no nome ajustado é excluído do
    recorte de Formação de Professores — a exclusão é por substring, não
    igualdade exata (divergência corrigida na Tarefa 11)."""
    base = _base_percentuais()
    assert percentual_professores(base) == 0.0


def test_pt004_denominador_inclui_mulheres_mil():
    """Cenário: Mulheres Mil (colapsada em QUALIFICAÇÃO PROFISSIONAL,
    BR-MIGRAR-017) permanece no denominador (BR-MIGRAR-012) — 10 (Técnico,
    fech=1) + 2.5 (Qualificação Profissional, fech=200/800=0.25) = 12.5;
    se Mulheres Mil fosse excluída, o total seria 10, não 12.5."""
    base = _base_percentuais()
    assert matriculas_equivalentes(base).sum() == pytest.approx(12.5)


def test_pt004_cor_medidor_professores_segue_a_meta_nao_limiar_fixo():
    """Cenário: 20% acende verde (meta correta), não o limiar incorreto de
    ~29,9% do legado (BR-MIGRAR-024)."""
    assert cor_medidor(0.20, 0.20) == "verde"
    assert cor_medidor(0.199, 0.20) == "vermelho"


# ===================== PT-005: IEA / eficiência acadêmica =====================


def test_pt005_iea_exemplo_numerico_oficial():
    """Cenário: pC=50%, pE=20%, pR=30% -> IEA ≈ 71,42%."""
    resultado = calcular_iea(concluidos=50, evadidos=20, retidos=30)
    assert resultado == pytest.approx(0.7142857, rel=1e-4)


def test_pt005_iea_sem_concluidos_nem_evadidos_nao_gera_nan():
    """Cenário: 0 concluídos, 0 evadidos, 12 retidos -> 0, não NaN
    (BR-MIGRAR-013/BR-HUMANA-001)."""
    resultado = calcular_iea(concluidos=0, evadidos=0, retidos=12)
    assert resultado == 0.0


def test_pt005_nenhum_status_some_do_total():
    """Cenário: nenhum status some do total do IEA — os 3 buckets são
    exaustivos sobre o domínio fechado de StatusMatricula.

    Divergência corrigida na Tarefa 11: `eh_retido` original (Tarefa 07)
    exigia uma comparação de datas que dava sempre falso no limite exato
    selecionado pelo próprio grão de eficiência, deixando `EM_CURSO` fora de
    todos os buckets.
    """
    df = pd.DataFrame(
        {"status_corrigido2": ["CONCLUÍDA", "INTEGRALIZADA", "ABANDONO", "DESLIGADO", "REPROVADA", "TRANSF_EXT", "TRANSF_INT", "EM_CURSO"]}
    )
    concluidos, evadidos, retidos = classificar_matriculas_eficiencia(df, FiltrosAtivos(ano_base=2026))
    assert concluidos + evadidos + retidos == len(df)
    assert concluidos == 2
    assert evadidos == 5
    assert retidos == 1


# ===================== PT-006: Eixo dinâmico e FIC =====================


@pytest.mark.parametrize(
    "eixo,coluna_esperada",
    [
        ("campus", "co_unidade"),
        ("tipo_curso", "subtipo_curso"),
        ("nome_curso", "nome_curso_ajustado"),
        ("modalidade", "modalidade_ensino"),
        ("oferta", "tipo_oferta_curso"),
        ("ciclo", "codigo_ciclo_matricula"),
    ],
)
def test_pt006_cada_eixo_mapeia_para_a_coluna_correta(eixo, coluna_esperada):
    """Divergência corrigida na Tarefa 11: a Tarefa 06 mapeava "tipo_curso"
    para `tipo_curso_pnp` (deveria ser `subtipo_curso`) e não mapeava
    "oferta" a coluna alguma."""
    assert coluna_para_eixo(eixo) == coluna_esperada


def test_pt006_fic_exclui_apenas_fic_nunca_mulheres_mil():
    """Cenário crítico: SEM FIC exclui Formação Inicial/Continuada, preserva
    Mulheres Mil (BR-MIGRAR-021) — GAP da Tarefa 06 corrigido na Tarefa 11."""
    df = pd.DataFrame(
        {
            "categoria_origem_curso": ["FORMAÇÃO INICIAL", "FORMAÇÃO CONTINUADA", "MULHERES MIL", "TECNICO"],
        }
    )
    resultado = filtrar_fic(df, incluir_fic=False)
    assert set(resultado["categoria_origem_curso"]) == {"MULHERES MIL", "TECNICO"}


def test_pt006_com_fic_nao_filtra_nada():
    df = pd.DataFrame({"categoria_origem_curso": ["FORMAÇÃO INICIAL", "TECNICO"]})
    resultado = filtrar_fic(df, incluir_fic=True)
    assert len(resultado) == 2


def test_pt006_modalidade_fonte_unica():
    """BR-MIGRAR-019: eixo "modalidade" e o acessor `shared.modalidade` usam
    a mesma coluna (`modalidade_ensino`), nunca fontes divergentes."""
    from app.domain.shared import modalidade

    df = pd.DataFrame({"modalidade_ensino": ["EAD", "PRESENCIAL"]})
    assert coluna_para_eixo("modalidade") == "modalidade_ensino"
    assert list(modalidade(df)) == list(df["modalidade_ensino"])


# ===================== PT-007: Navegação e autenticação =====================


def test_pt007_paginas_publicas_nao_exigem_autenticacao():
    os.environ.setdefault("ADMIN_EMAIL", "x")
    os.environ.setdefault("ADMIN_PASSWORD_HASH", "x")
    import app.app as app_module

    client = app_module.app.server.test_client()
    for path in ["/", "/matriculas", "/eficiencia", "/evasao", "/percentuais-legais"]:
        resposta = client.get(path)
        assert resposta.status_code == 200


def test_pt007_upload_administrativo_exige_autenticacao():
    os.environ.setdefault("ADMIN_EMAIL", "x")
    os.environ.setdefault("ADMIN_PASSWORD_HASH", "x")
    import app.app as app_module

    client = app_module.app.server.test_client()
    resposta = client.get("/admin/upload", follow_redirects=False)
    assert resposta.status_code in (301, 302)
    assert "/admin/login" in resposta.headers.get("Location", "")
