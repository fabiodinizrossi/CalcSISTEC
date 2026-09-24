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
