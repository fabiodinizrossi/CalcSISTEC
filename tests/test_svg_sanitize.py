"""Testes de `app/data/svg_sanitize.py` (Tarefa `001-govbr-design-system`, T006).

RF-21/RN-13: o SVG enviado como logotipo é limpo antes de ser aceito —
`<script>`, atributos `on*` e `<foreignObject>` são removidos; referências
externas (`href`/`xlink:href` para fora do próprio documento) são removidas;
um SVG com entidade externa (XXE) é rejeitado ou neutralizado sem que a
entidade seja resolvida.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.svg_sanitize import SvgInvalido, sanitizar_svg  # noqa: E402


def test_remove_tag_script():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
    <script>window.__xss = true;</script>
    <circle cx="10" cy="10" r="5" />
    </svg>"""
    limpo = sanitizar_svg(svg)
    assert b"<script" not in limpo.lower()
    assert b"__xss" not in limpo


def test_remove_atributos_on_star():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg" onload="window.__xss=true">
    <circle cx="10" cy="10" r="5" onclick="window.__xss=true" />
    </svg>"""
    limpo = sanitizar_svg(svg)
    assert b"onload" not in limpo.lower()
    assert b"onclick" not in limpo.lower()
    assert b"__xss" not in limpo


def test_remove_foreignobject():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
    <foreignObject><body xmlns="http://www.w3.org/1999/xhtml">
    <script>window.__xss = true;</script></body></foreignObject>
    </svg>"""
    limpo = sanitizar_svg(svg)
    assert b"foreignobject" not in limpo.lower()
    assert b"__xss" not in limpo


def test_remove_href_externo():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <image href="https://evil.example/tracker.png" />
    <use xlink:href="https://evil.example/other.svg#x" />
    </svg>"""
    limpo = sanitizar_svg(svg)
    assert b"evil.example" not in limpo


def test_svg_com_entidade_externa_xxe_e_rejeitado_ou_neutralizado():
    svg_xxe = b"""<?xml version="1.0"?>
    <!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <svg xmlns="http://www.w3.org/2000/svg"><text>&xxe;</text></svg>"""
    try:
        limpo = sanitizar_svg(svg_xxe)
    except SvgInvalido:
        return
    assert b"root:" not in limpo
    assert b"ENTITY" not in limpo


def test_svg_limpo_valido_e_aceito():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><circle cx="10" cy="10" r="5" fill="#1351B4"/></svg>'
    limpo = sanitizar_svg(svg)
    assert b"<circle" in limpo
    assert b"svg" in limpo.lower()
