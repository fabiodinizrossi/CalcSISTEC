"""Testes de `app/data/image_validation.py` (Tarefa `001-govbr-design-system`, T007).

RF-21/RN-13: PNG válido é aceito; qualquer arquivo cuja assinatura binária não
seja PNG é rejeitado mesmo com extensão `.png`; dado anexado após o chunk
`IEND` (esteganografia/anexo malicioso) é descartado na regravação.
"""

import io
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.image_validation import ImagemInvalida, validar_e_normalizar_png  # noqa: E402


def _png_bytes(size=(10, 10), color=(255, 0, 0)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_png_valido_e_aceito():
    dados = _png_bytes()
    resultado = validar_e_normalizar_png(dados)
    assert resultado[:8] == b"\x89PNG\r\n\x1a\n"


def test_arquivo_com_assinatura_diferente_de_png_e_rejeitado_mesmo_com_extensao_png():
    dados_jpeg = io.BytesIO()
    Image.new("RGB", (10, 10)).save(dados_jpeg, format="JPEG")
    with pytest.raises(ImagemInvalida):
        validar_e_normalizar_png(dados_jpeg.getvalue())


def test_arquivo_texto_renomeado_para_png_e_rejeitado():
    with pytest.raises(ImagemInvalida):
        validar_e_normalizar_png(b"isto nao e uma imagem, apenas texto simples")


def test_png_com_dado_anexado_apos_iend_e_regravado_sem_esse_dado():
    dados = _png_bytes() + b"DADO-ANEXADO-MALICIOSO-APOS-IEND"
    resultado = validar_e_normalizar_png(dados)
    assert b"DADO-ANEXADO-MALICIOSO-APOS-IEND" not in resultado
    Image.open(io.BytesIO(resultado)).verify()
