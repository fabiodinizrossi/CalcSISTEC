"""Percorre a árvore de componentes Dash para os testes das telas públicas."""

# Componentes do DS que dependem de JavaScript inicializado na carga (AD-001): o
# core.min.js não observa o DOM que o React cria depois.
CLASSES_DO_DS_QUE_PRECISAM_DE_JS = (
    "br-select",
    "br-tab",
    "br-modal",
    "br-tooltip",
    "br-accordion",
    "br-dropdown",
    "br-carousel",
    "br-upload",
)


def componentes(raiz):
    """Todos os componentes da árvore, a partir de `raiz` (inclusive)."""
    if isinstance(raiz, (list, tuple)):
        for filho in raiz:
            yield from componentes(filho)
        return
    if raiz is None or isinstance(raiz, (str, int, float, bool)):
        return
    yield raiz
    yield from componentes(getattr(raiz, "children", None))


def classes(raiz):
    """Conjunto de todas as classes CSS usadas na árvore."""
    encontradas = set()
    for componente in componentes(raiz):
        encontradas.update((getattr(componente, "className", None) or "").split())
    return encontradas


def textos(raiz):
    """Todo o texto visível da árvore, na ordem, separado por espaço."""
    pedacos = []

    def visitar(no):
        if isinstance(no, (list, tuple)):
            for filho in no:
                visitar(filho)
        elif isinstance(no, (str, int, float)) and not isinstance(no, bool):
            pedacos.append(str(no))
        elif no is not None:
            visitar(getattr(no, "children", None))

    visitar(raiz)
    return " ".join(pedacos)


def com_classe(raiz, classe):
    """Componentes da árvore que têm `classe`."""
    return [c for c in componentes(raiz) if classe in (getattr(c, "className", None) or "").split()]


def exigir_sem_componente_do_ds_que_precisa_de_js(raiz):
    usadas = classes(raiz) & set(CLASSES_DO_DS_QUE_PRECISAM_DE_JS)
    assert not usadas, f"componente do DS que depende de JS na árvore: {sorted(usadas)}"
