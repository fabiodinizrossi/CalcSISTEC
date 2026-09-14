"""Sanitização de SVG enviado como logotipo (`001-govbr-design-system`, T010).

RF-21/RN-13: o logotipo pode ser enviado como SVG; antes de ser aceito, o
arquivo passa por uma lista de permissão explícita de elementos/atributos,
removendo `<script>`, `<foreignObject>`, atributos `on*` e referências
externas (`href`/`xlink:href` para fora do próprio documento) — defesa contra
XSS embutido em SVG. O parse usa `defusedxml` para não resolver entidades
externas (XXE).
"""

import re
import xml.etree.ElementTree as ET

from defusedxml import ElementTree as DefusedET

XLINK_NS = "http://www.w3.org/1999/xlink"
SVG_NS = "http://www.w3.org/2000/svg"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

_ALLOWED_TAGS = {
    "svg", "g", "path", "circle", "ellipse", "line", "polyline", "polygon",
    "rect", "text", "tspan", "defs", "clippath", "lineargradient",
    "radialgradient", "stop", "title", "desc", "symbol", "use", "image",
    "mask", "pattern", "style",
}

_ALLOWED_ATTRS = {
    "id", "class", "style", "d", "fill", "stroke", "stroke-width",
    "stroke-linecap", "stroke-linejoin", "stroke-dasharray", "cx", "cy", "r",
    "rx", "ry", "x", "y", "x1", "y1", "x2", "y2", "width", "height",
    "viewbox", "xmlns", "version", "points", "transform", "opacity",
    "fill-opacity", "stroke-opacity", "offset", "stop-color", "stop-opacity",
    "gradientunits", "gradienttransform", "clip-path", "font-family",
    "font-size", "font-weight", "text-anchor", "preserveaspectratio",
    "aria-hidden", "role", "focusable", "alt",
}

_DENY_TAGS = {"script", "foreignobject", "animate", "animatetransform", "animatemotion", "set", "iframe"}


class SvgInvalido(Exception):
    pass


def _strip_ns(tag):
    return tag.split("}", 1)[-1].lower() if "}" in tag else tag.lower()


def _is_external_ref(value):
    value = (value or "").strip()
    if not value:
        return False
    if value.startswith("#"):
        return False
    if value.lower().startswith("data:image/"):
        return False
    return True


def sanitizar_svg(dados):
    """Recebe bytes de um SVG e devolve bytes do SVG limpo.

    Levanta `SvgInvalido` quando o conteúdo não é um XML/SVG parseável."""
    try:
        root = DefusedET.fromstring(dados)
    except Exception as exc:
        raise SvgInvalido(f"SVG malformado ou não suportado: {exc}") from exc

    if _strip_ns(root.tag) != "svg":
        raise SvgInvalido("Documento raiz não é um <svg>.")

    _limpar_elemento(root)
    return ET.tostring(root, encoding="utf-8")


def _limpar_elemento(elem):
    for filho in list(elem):
        tag = _strip_ns(filho.tag)
        if tag in _DENY_TAGS or tag not in _ALLOWED_TAGS:
            elem.remove(filho)
            continue
        _limpar_atributos(filho)
        _limpar_elemento(filho)
    _limpar_atributos(elem)


def _limpar_atributos(elem):
    for nome in list(elem.attrib.keys()):
        nome_local = _strip_ns(nome)
        valor = elem.attrib[nome]
        if nome_local.startswith("on"):
            del elem.attrib[nome]
            continue
        if nome_local in ("href", "xlink:href") or nome.endswith("}href"):
            if _is_external_ref(valor):
                del elem.attrib[nome]
            continue
        if nome_local not in _ALLOWED_ATTRS:
            del elem.attrib[nome]
            continue
        if nome_local == "style" and re.search(r"expression\s*\(|javascript:", valor, re.I):
            del elem.attrib[nome]
