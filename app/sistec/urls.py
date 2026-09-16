"""URLs do Sistec entregues à extensão por par (`002-baixador-planilhas-
sistec`, T041, D-01, `interfaces/sistec-http.md`).

Centralizadas aqui (e não fixas na extensão) para que uma mudança de URL no
Sistec se corrija só no servidor (roadmap §9). Os valores refletem a F0
(`f0-resultado.md`): troca de perfil é `POST` sem query string, `qtdPerfis`
é dinâmico (igual ao total de perfis lidos na captura), e a exportação de
ciclos tem timeout de 900 s (RN-06 d).
"""

import os

# Só para desenvolvimento/teste (T062, `scripts/sistec_simulado.py`):
# `CALCSISTEC_SISTEC_BASE_URL` aponta o servidor (e, por consequência, a
# extensão) para o Sistec simulado em vez do Sistec real. Em produção, a
# variável não é definida e o padrão vale.
BASE = os.environ.get("CALCSISTEC_SISTEC_BASE_URL", "https://sistec.mec.gov.br")

URL_PAGINA_PERFIS = f"{BASE}/index/selecionarinstituicao/alterar/perfil"
URL_TROCA_PERFIL = f"{BASE}/index/index"
URL_EXPORTACAO_CICLO = (
    f"{BASE}/gridciclo/exportar-ciclo-turmas/?coCiclo=&noInstituicao=&tipoCurso=&Ano=&stCicloName=&acoes="
)
URL_EXPORTACAO_MATRICULA = (
    f"{BASE}/aluno/gerar-csv/?tipoAluno=comCpf&cpfAluno=&codigoAluno=&filtro_nome=1&no_aluno=%20"
    "&no_social=&tipoPesquisa=parteNome&vizualizarGrid=0,1,2,3,4,5,6"
)

# Quantidade de perfis usada na troca por URL quando ela ainda não foi lida da
# tela (o script R usava este literal e funciona com ele).
QTD_PERFIS_PADRAO = 16


def url_troca_perfil_get(id_perfil, qtd_perfis=QTD_PERFIS_PADRAO):
    """Troca de perfil pela URL, para abrir no navegador da pessoa (modo do
    script R, `app/sistec/downloads.py`).

    A F0 viu o Sistec trocando de perfil por `POST` no formulário; o script R
    usa esta URL com query string e funciona hoje. Se o Sistec deixar de
    aceitá-la, todas as planilhas vêm do mesmo campus — e
    `navegador._conferir_unidade` avisa, comparando o código da unidade dentro
    de cada planilha."""
    return f"{URL_TROCA_PERFIL}?tipo={id_perfil}&acao=&qtdPerfis={qtd_perfis}"


ESPERA_MINIMA_TROCA_PERFIL_S = 3  # RN-06 b, após a troca de perfil (achado 1 da F0: POST, sem GET).
TEMPO_MAX_EXPORTACAO_S = 900  # RN-06 d / RN-09.
TIMEOUT_TROCA_PERFIL_S = 60
TIMEOUT_PAGINA_PERFIS_S = 60


def url_exportacao(tipo):
    if tipo == "ciclo":
        return URL_EXPORTACAO_CICLO
    if tipo == "matricula":
        return URL_EXPORTACAO_MATRICULA
    raise ValueError(f"tipo de exportação desconhecido: {tipo!r}")


def par_para_extensao(n, total, tipo, id_perfil, nome_perfil, qtd_perfis):
    """Monta o payload de `POST /api/sistec/execucoes/<id>/proximo` (§4.1 da
    interface) para um par a baixar. `qtd_perfis`: total de perfis lidos na
    captura para esta conta (achado 2 da F0 — nunca um literal fixo)."""
    return {
        "n": n,
        "total": total,
        "tipo": tipo,
        "id_perfil": id_perfil,
        "nome_perfil": nome_perfil,
        "url_pagina_perfis": URL_PAGINA_PERFIS,
        "url_troca_perfil": URL_TROCA_PERFIL,
        "metodo_troca_perfil": "POST",
        "corpo_troca_perfil": {"tipo": id_perfil, "acao": "", "qtdPerfis": qtd_perfis},
        "espera_minima_s": ESPERA_MINIMA_TROCA_PERFIL_S,
        "url_exportacao": url_exportacao(tipo),
        "tempo_max_s": TEMPO_MAX_EXPORTACAO_S,
    }
