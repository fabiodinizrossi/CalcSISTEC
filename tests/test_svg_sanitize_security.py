"""Teste de segurança dedicado (Tarefa `001-govbr-design-system`, T041).

Usa literalmente o payload de `_reversa_forward/001-govbr-design-system/onboarding.md`
§6 (passo 6 — "Teste de segurança obrigatório") para confirmar que nenhum dos
três vetores (`<script>`, `onload`, `onclick`) sobrevive à sanitização.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.svg_sanitize import sanitizar_svg  # noqa: E402

PAYLOAD_ONBOARDING = b"""<svg xmlns="http://www.w3.org/2000/svg" onload="window.__xss=true">
  <script>window.__xss = true;</script>
  <circle cx="10" cy="10" r="5" onclick="window.__xss=true" />
</svg>"""


def test_payload_do_onboarding_nao_sobrevive_a_sanitizacao():
    limpo = sanitizar_svg(PAYLOAD_ONBOARDING)
    texto = limpo.decode("utf-8", errors="ignore").lower()
    assert "<script" not in texto
    assert "onload" not in texto
    assert "onclick" not in texto
    assert "__xss" not in texto
    # O upload deve ser aceito (é um SVG válido depois de limpo) — o círculo
    # continua presente, só os vetores de execução de script são removidos.
    assert "<circle" in texto
