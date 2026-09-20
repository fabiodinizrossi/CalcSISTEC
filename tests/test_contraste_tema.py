"""Contraste dos pares de token do DS nos dois temas (DS-33, DS-34, DS-53, DS-54): texto
normal ≥ 4,5:1 e contorno de foco ≥ 3:1, calculados sobre `core-tokens.css` mais as
variáveis que `style.css` remapeia no tema escuro."""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1] / "app"
TOKENS = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", (RAIZ / "static" / "govbr-ds" / "dist" / "core-tokens.css").read_text(encoding="utf-8")))
STYLE = re.sub(r"/\*.*?\*/", "", (RAIZ / "assets" / "style.css").read_text(encoding="utf-8"), flags=re.S)


def _remapeamento_do_tema_escuro():
    corpo = re.search(r':root\[data-tema="escuro"\]\s*\{([^}]*)\}', STYLE).group(1)
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", corpo))


def _resolver(nome, sobre):
    valor = sobre.get(nome, TOKENS.get(nome))
    encadeado = re.fullmatch(r"var\((--[\w-]+)\)", valor.strip())
    return _resolver(encadeado.group(1), sobre) if encadeado else valor.strip()


def _luminancia(hexadecimal):
    h = hexadecimal.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    canais = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contraste(primeira, segunda):
    maior, menor = sorted([_luminancia(primeira), _luminancia(segunda)], reverse=True)
    return (maior + 0.05) / (menor + 0.05)


TEMAS = {"claro": {}, "escuro": _remapeamento_do_tema_escuro()}


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("texto", ["--color", "--interactive"])
def test_texto_tem_contraste_de_ao_menos_4_5_para_1_contra_o_fundo(tema, texto):
    sobre = TEMAS[tema]
    assert contraste(_resolver(texto, sobre), _resolver("--background", sobre)) >= 4.5


@pytest.mark.parametrize("tema", TEMAS)
def test_contorno_de_foco_tem_contraste_de_ao_menos_3_para_1_contra_o_fundo(tema):
    sobre = TEMAS[tema]
    assert contraste(_resolver("--focus-color", sobre), _resolver("--background", sobre)) >= 3


def test_o_tema_escuro_troca_o_fundo_e_o_texto_pelos_pares_dark_do_ds():
    escuro = TEMAS["escuro"]
    assert _resolver("--background", escuro) == _resolver("--background-dark", {})
    assert _resolver("--color", escuro) == _resolver("--color-dark", {})
    assert _resolver("--background", escuro) != _resolver("--background", {})


def test_contraste_calcula_o_valor_conhecido_de_preto_sobre_branco():
    assert round(contraste("#000", "#fff"), 1) == 21.0
