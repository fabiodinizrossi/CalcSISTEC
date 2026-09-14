"""Validação e normalização de PNG enviado como logotipo (`001-govbr-design-system`, T011).

RF-21/RN-13: verifica a assinatura binária do arquivo (rejeita qualquer coisa
que não seja PNG de verdade, mesmo com extensão `.png`) e reabre/regrava a
imagem com Pillow, descartando qualquer dado fora da estrutura de *chunks*
válida do formato (ex.: dado anexado após o chunk `IEND`).
"""

import io

from PIL import Image, UnidentifiedImageError

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ImagemInvalida(Exception):
    pass


def validar_e_normalizar_png(dados):
    """Recebe bytes de um upload e devolve bytes de um PNG normalizado.

    Levanta `ImagemInvalida` quando o arquivo não é um PNG válido."""
    if not dados or dados[:8] != PNG_SIGNATURE:
        raise ImagemInvalida("O arquivo não é um PNG válido (assinatura binária incorreta).")

    try:
        imagem = Image.open(io.BytesIO(dados))
        imagem.load()
        if imagem.format != "PNG":
            raise ImagemInvalida("O arquivo não é um PNG válido.")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImagemInvalida(f"Não foi possível ler o arquivo como PNG: {exc}") from exc

    buf = io.BytesIO()
    imagem.save(buf, format="PNG")
    return buf.getvalue()
