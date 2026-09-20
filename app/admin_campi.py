"""Lista de campi do painel administrativo: busca, paginação e telas do CRUD."""

TAMANHOS_DE_PAGINA = (10, 25, 50)
CAMPOS_DA_BUSCA = ("nome_perfil", "cidade", "nome_unidade")


def _inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def filtrar_e_paginar(campi, q, pagina, por_pagina):
    """Filtra `campi` pelo texto `q` (perfil, cidade ou nome da unidade, sem
    diferenciar maiúsculas) e devolve a página pedida.

    `por_pagina` fora de 10, 25 e 50 vira 10; `pagina` inválida ou além da
    última vira 1. `inicio` e `fim` são índices de 1 em diante dos itens
    exibidos (0 e 0 quando não há nenhum)."""
    texto = (q or "").strip().lower()
    if texto:
        campi = [c for c in campi if any(texto in str(c.get(campo) or "").lower() for campo in CAMPOS_DA_BUSCA)]

    tamanho = _inteiro(por_pagina)
    if tamanho not in TAMANHOS_DE_PAGINA:
        tamanho = 10

    total = len(campi)
    ultima = max(1, -(-total // tamanho))
    numero = _inteiro(pagina)
    if numero is None or not 1 <= numero <= ultima:
        numero = 1

    primeiro = (numero - 1) * tamanho
    itens = campi[primeiro : primeiro + tamanho]
    return {
        "itens": itens,
        "total": total,
        "pagina": numero,
        "por_pagina": tamanho,
        "inicio": primeiro + 1 if itens else 0,
        "fim": primeiro + len(itens),
    }
