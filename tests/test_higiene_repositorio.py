"""Higiene do repositório (`limpeza-onboarding-repo`).

Afirma o que não existe mais (módulos e funções sem uso, arquivos soltos) e o
que passou a existir (arquivos de instalação reproduzível). A raiz do
repositório vem de `__file__`, nunca do diretório corrente: o pytest pode ser
rodado de qualquer lugar.
"""

import ast
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def caminho(*partes):
    return os.path.join(RAIZ, *partes)


def definicoes(arquivo_relativo):
    """Nomes de funções definidas no arquivo, lidos por AST."""
    with open(caminho(*arquivo_relativo.split("/")), encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read())
    return {
        no.name
        for no in ast.walk(arvore)
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def arquivos_py(*pastas):
    """Todos os `.py` das pastas, em ordem estável."""
    for pasta in pastas:
        for raiz, _subpastas, nomes in os.walk(caminho(*pasta.split("/"))):
            for nome in sorted(nomes):
                if nome.endswith(".py"):
                    yield os.path.join(raiz, nome)


TERMOS_PROIBIDOS = [
    "_reversa_sdd",
    "_reversa_forward",
    "cutover_plan.md",
    "PARITY_REPORT.md",
    "CUTOVER.md",
    "APAGAR",
]


def test_app_nao_cita_documentos_ausentes():
    """DOC-01 AC1: nenhum `.py` de `app/` aponta para arquivo que não existe."""
    for arquivo in arquivos_py("app"):
        with open(arquivo, encoding="utf-8") as fonte:
            conteudo = fonte.read()
        for termo in TERMOS_PROIBIDOS:
            if termo in conteudo:
                pytest.fail(f"{os.path.relpath(arquivo, RAIZ)} cita {termo}")


def test_scripts_tests_e_run_nao_citam_documentos_ausentes():
    """DOC-01 AC1: o mesmo vale para `scripts/`, `tests/` e `run.py`. O próprio
    teste de higiene é a exceção — ele lista os termos proibidos."""
    arquivos = list(arquivos_py("scripts", "tests")) + [caminho("run.py")]

    for arquivo in arquivos:
        if os.path.basename(arquivo) == "test_higiene_repositorio.py":
            continue
        with open(arquivo, encoding="utf-8") as fonte:
            conteudo = fonte.read()
        for termo in TERMOS_PROIBIDOS:
            if termo in conteudo:
                pytest.fail(f"{os.path.relpath(arquivo, RAIZ)} cita {termo}")


def carregar_script(nome):
    """Importa um `scripts/*.py` pelo caminho (não é pacote)."""
    import importlib.util

    espec = importlib.util.spec_from_file_location(nome, caminho("scripts", f"{nome}.py"))
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def test_verificacao_de_prontidao_aponta_para_o_deploy(capsys):
    """DOC-02 AC5: a seção fora do escopo automatizável manda ler o `DEPLOY.md`."""
    modulo = carregar_script("verificar_prontidao_cutover")

    modulo.imprimir_relatorio([])
    saida = capsys.readouterr().out

    assert "DEPLOY.md" in saida
    assert "CUTOVER.md" not in saida


def test_modulo_validators_foi_removido():
    """LIM-01 AC1: `app/data/validators.py` não era importado por ninguém."""
    assert not os.path.exists(caminho("app", "data", "validators.py"))


SIMBOLOS_REMOVIDOS = [
    ("app/components/kpi.py", "kpi_colunas"),
    ("app/data/consulta.py", "data_ultimo_upload_valido"),
    ("app/data/transform.py", "t01_remover_pii"),
    ("app/pages/percentuais_legais.py", "_rotulo_eixo"),
]


@pytest.mark.parametrize("arquivo_relativo,nome", SIMBOLOS_REMOVIDOS)
def test_funcao_sem_chamador_foi_removida(arquivo_relativo, nome):
    """LIM-01 AC2: nenhuma das quatro funções tem chamador."""
    assert nome not in definicoes(arquivo_relativo)


COLUNAS_PII_ESPERADAS = [
    "DS_SENHA",
    "DS_EMAIL",
    "CO_PESSOA_FISICA_ALUNO",
    "NO_ALUNO",
    "NO_MAE_ALUNO",
    "SG_SEXO",
    "DT_DATA_NASCIMENTO",
    "NU_CPF",
    "NOME_RESPONSAVEL",
    "CPF",
]


def test_colunas_pii_continua_com_as_mesmas_entradas():
    """LIM-01 AC3: `COLUNAS_PII` fica — `app/sistec/colunas.py` depende dela."""
    from app.data.transform import COLUNAS_PII

    assert COLUNAS_PII == COLUNAS_PII_ESPERADAS


def test_arquivos_soltos_na_raiz_nao_existem():
    """LIM-02 AC4: `nonascii.txt` e `chromedriver/` (Princípio VI: nada de
    automação de navegador no repositório)."""
    assert not os.path.exists(caminho("nonascii.txt"))
    assert not os.path.exists(caminho("chromedriver"))


ENTRADAS_GITIGNORE = [".agents/", ".uv-cache/", ".uv-python/"]


def test_gitignore_lista_o_estado_das_ferramentas_locais():
    """LIM-02 AC5: pastas de ferramenta ficam fora do versionamento, mas
    continuam existindo no disco (não são apagadas)."""
    with open(caminho(".gitignore"), encoding="utf-8") as arquivo:
        linhas = {linha.strip() for linha in arquivo}

    for entrada in ENTRADAS_GITIGNORE:
        assert entrada in linhas, f"{entrada} nao esta no .gitignore"


def linhas_uteis(arquivo_relativo):
    """Linhas não vazias de um arquivo de texto, sem espaços nas pontas."""
    with open(caminho(*arquivo_relativo.split("/")), encoding="utf-8") as arquivo:
        return [linha.strip() for linha in arquivo if linha.strip()]


REQUIREMENTS_ESPERADOS = [
    "dash==4.4.1",
    "dash-bootstrap-components==2.0.4",
    "pandas==2.3.0",
    "openpyxl==3.1.5",
    "plotly==6.8.0",
    "defusedxml==0.7.1",
    "Pillow==11.2.1",
    "Flask==3.1.3",
    "Werkzeug==3.1.8",
]


def test_requirements_fixa_as_versoes_testadas():
    """DEP-01 AC1: sem `==`, um `pip install` de amanhã pode quebrar o gate."""
    assert linhas_uteis("requirements.txt") == REQUIREMENTS_ESPERADOS


def test_requirements_dev_inclui_o_principal_e_o_pytest():
    """DEP-01 AC2: quem instala o `-dev` tem o app e a suíte."""
    assert linhas_uteis("requirements-dev.txt") == [
        "-r requirements.txt",
        "pytest==9.1.1",
    ]


def test_python_version_declara_a_versao_do_projeto():
    """DEP-02 AC3: projeto é Python 3.12 (PROJECT_RULES, Restrições Técnicas)."""
    assert linhas_uteis(".python-version") == ["3.12"]


CHAVES_ENV = [
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD_HASH",
    "FLASK_SECRET_KEY",
    "CALCSISTEC_HTTPS",
    "CALCSISTEC_SISTEC_BASE_URL",
    "CALCSISTEC_PASTA_DOWNLOADS",
    "CALCSISTEC_PASTA_COLETA",
    "ANO_BASE",
]


def valores_env_exemplo():
    """`{chave: valor}` de `.env.example`, sem as linhas de comentário."""
    valores = {}
    for linha in linhas_uteis(".env.example"):
        if linha.startswith("#"):
            continue
        chave, _separador, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip()
    return valores


def test_env_exemplo_documenta_todas_as_chaves_de_ambiente():
    """DEP-02 AC4: quem clona sabe o que definir antes de subir."""
    valores = valores_env_exemplo()

    for chave in CHAVES_ENV:
        assert chave in valores, f"{chave} fora do .env.example"


def test_env_exemplo_nao_traz_segredo_nenhum():
    """DEP-02 AC4: arquivo versionado não pode carregar segredo real."""
    valores = valores_env_exemplo()

    assert valores["FLASK_SECRET_KEY"] == ""
    assert valores["ADMIN_PASSWORD_HASH"] == ""
