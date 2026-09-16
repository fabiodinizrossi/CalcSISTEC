"""Leitura do texto dos perfis da tela de seleção do Sistec
(`002-baixador-planilhas-sistec`, achados 2 e 3 da F0).

Cada perfil é uma linha de texto no padrão
"<PAPEL> DA UNIDADE DE ENSINO - [<código da unidade> -] <instituição> - CAMPUS <nome>".
No Sistec real o código da unidade nem sempre aparece, e alguns campi vêm
como "CÂMPUS". Porta em Python de `extrairPerfilDoTexto`
(`extensao-sistec/sistec-content.js`), usada pelo navegador controlado pelo
servidor (`app/sistec/navegador.py`) e pela lista de campi
(`app/data/campi.py`).
"""

import re
import unicodedata

REGEX_ITEM_PERFIL = re.compile(
    r"^(?P<papel>.*?DA UNIDADE DE ENSINO)\s*-\s*(?:(?P<codigo>\d+)\s*-\s*)?"
    r"(?P<instituicao>.*?)\s*-\s*(?P<campus>C[AÂ]MPUS\s+.*)$",
    re.IGNORECASE,
)
REGEX_PREFIXO_CAMPUS = re.compile(r"^C[AÂ]MPUS\s+", re.IGNORECASE)

# Preposições que o português mantém em minúsculo num nome próprio (exceto
# como primeira palavra) — ex.: "Júlio de Castilhos", "São Vicente do Sul".
PREPOSICOES_MINUSCULAS = {"de", "do", "da", "dos", "das", "e"}


def normalizar_texto(texto):
    return " ".join((texto or "").split())


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _nome_proprio(texto):
    palavras = normalizar_texto(texto).lower().split(" ")
    return " ".join(
        palavra if indice > 0 and palavra in PREPOSICOES_MINUSCULAS else palavra[:1].upper() + palavra[1:]
        for indice, palavra in enumerate(palavras)
    )


def extrair_perfil_do_texto(texto):
    """`nome_perfil` é o texto inteiro normalizado (igual ao que já está
    salvo em `campi_sistec`); `cidade`/`nome_unidade` saem do trecho
    "CAMPUS <nome>", que costuma ser o nome da cidade. Quando não for, os dois
    campos continuam editáveis em Configurações → Campi do Sistec."""
    limpo = normalizar_texto(texto)
    m = REGEX_ITEM_PERFIL.match(limpo)
    if not m:
        return {"nome_perfil": limpo, "co_unidade": None, "cidade": None, "nome_unidade": None}
    cidade = _nome_proprio(REGEX_PREFIXO_CAMPUS.sub("", m.group("campus"))) or None
    return {
        "nome_perfil": limpo,
        "co_unidade": m.group("codigo"),
        "cidade": cidade,
        "nome_unidade": f"Campus {cidade}" if cidade else None,
    }


REGEX_LINHA_DE_PERFIL = re.compile(r"^(?P<id>\d{3,})\s*[;,\t|]\s*(?P<nome>.+)$")


def perfis_de_texto(texto):
    """Lê uma lista colada de perfis: uma linha por campus, no formato
    `identificador ; nome do perfil` (também aceita vírgula, tabulação ou
    barra vertical).

    Serve para instalar em qualquer instituição sem depender da leitura
    campus a campus na tela de Configurações. Devolve
    `(perfis, linhas_invalidas)`: o identificador é obrigatório, porque é ele
    que troca o campus ativo no Sistec."""
    perfis = []
    invalidas = []
    for linha in (texto or "").splitlines():
        limpa = normalizar_texto(linha)
        if not limpa:
            continue
        m = REGEX_LINHA_DE_PERFIL.match(limpa)
        if not m:
            invalidas.append(limpa)
            continue
        dados = extrair_perfil_do_texto(m.group("nome"))
        perfis.append({**dados, "id_perfil": m.group("id")})
    return perfis, invalidas


def chave_campus(nome_perfil):
    """Reconhece o mesmo campus em perfis de papéis diferentes (Assessor/
    Gestor) e em capturas antigas: o nome depois de "CAMPUS", em maiúsculas
    e sem acento. Sem "CAMPUS" no texto, vale o texto inteiro."""
    texto = _sem_acento(normalizar_texto(nome_perfil)).upper()
    posicao = texto.rfind("CAMPUS ")
    if posicao < 0:
        return texto
    return texto[posicao + len("CAMPUS ") :].strip()


def deduplicar_por_campus(perfis, nomes_preferidos=()):
    """Um perfil por campus — o Sistec lista um por papel (achado 2 da F0),
    e baixar o mesmo campus duas vezes só duplicaria o trabalho.

    Mantém a ordem da primeira aparição. Dentro do mesmo campus, prefere o
    perfil cujo `nome_perfil` já está salvo (preserva a escolha anterior) e
    completa o `co_unidade` com o de outro papel quando o escolhido não tem."""
    preferidos = set(nomes_preferidos)
    escolhidos = {}
    codigos = {}
    for perfil in perfis:
        chave = chave_campus(perfil["nome_perfil"])
        if perfil.get("co_unidade"):
            codigos.setdefault(chave, perfil["co_unidade"])
        atual = escolhidos.get(chave)
        if atual is None or (perfil["nome_perfil"] in preferidos and atual["nome_perfil"] not in preferidos):
            escolhidos[chave] = perfil

    resultado = []
    for chave, perfil in escolhidos.items():
        if not perfil.get("co_unidade") and codigos.get(chave):
            perfil = {**perfil, "co_unidade": codigos[chave]}
        resultado.append(perfil)
    return resultado
