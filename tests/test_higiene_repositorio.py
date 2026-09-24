"""Higiene do repositório (`limpeza-onboarding-repo`).

Afirma o que não existe mais (módulos e funções sem uso, arquivos soltos) e o
que passou a existir (arquivos de instalação reproduzível). A raiz do
repositório vem de `__file__`, nunca do diretório corrente: o pytest pode ser
rodado de qualquer lugar.
"""

import ast
import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def caminho(*partes):
    return os.path.join(RAIZ, *partes)


def test_modulo_validators_foi_removido():
    """LIM-01 AC1: `app/data/validators.py` não era importado por ninguém."""
    assert not os.path.exists(caminho("app", "data", "validators.py"))
