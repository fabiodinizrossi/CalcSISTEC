"""Histórico de execuções (`002-baixador-planilhas-sistec`, T035, RF-13,
`data-delta.md` §3.4).

A linha nasce quando a execução/captura começa, com `desfecho` NULL. No
*startup*, `schema.init_db` marca como `interrompida` as linhas em aberto
(já coberto por T012/`test_schema_v2.py`). Edições de campus ou fatores só
na versão interna não geram linha; troca por arquivo e restauração sempre
geram (RF-13).
"""

import datetime
import json

from app.data.schema import DEFAULT_DB_PATH, get_connection

TIPOS_VALIDOS = {
    "captura",
    "baixa",
    "publicacao",
    "desfazer_publicacao",
    "configuracao_aplicada_publico",
    "fatores_arquivo",
    "fatores_restaurar_padrao",
}

DESFECHOS_VALIDOS = {
    "salva",
    "descartada",
    "cancelada",
    "interrompida",
    "encerrada_pausa",
    "falhou_consolidacao",
    "sem_resultado",
    "falhou",
    "publicada",
    "publicacao_desfeita",
    "aplicada",
}


def _now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def iniciar(tipo, admin_email, db_path=DEFAULT_DB_PATH):
    """Abre uma linha de histórico (`desfecho` NULL) e devolve o `id`."""
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"tipo de histórico desconhecido: {tipo!r}")

    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO historico (tipo, admin_email, inicio) VALUES (?, ?, ?)",
            (tipo, admin_email, _now_iso()),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def encerrar(
    historico_id,
    desfecho,
    sucessos=None,
    falhas=None,
    pausas=None,
    linhas_consolidadas=None,
    campi_mantidos=None,
    detalhe=None,
    db_path=DEFAULT_DB_PATH,
):
    """Grava o desfecho de uma linha aberta. `campi_mantidos`/`detalhe` são
    serializados como JSON (RN-13: `detalhe` nunca carrega conteúdo de
    planilha nem dado pessoal, só contagens e motivos)."""
    if desfecho not in DESFECHOS_VALIDOS:
        raise ValueError(f"desfecho de histórico desconhecido: {desfecho!r}")

    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE historico SET fim = ?, desfecho = ?, sucessos = ?, falhas = ?, pausas = ?, "
            "linhas_consolidadas = ?, campi_mantidos = ?, detalhe = ? WHERE id = ?",
            (
                _now_iso(),
                desfecho,
                sucessos,
                falhas,
                pausas,
                linhas_consolidadas,
                json.dumps(campi_mantidos, ensure_ascii=False) if campi_mantidos is not None else None,
                json.dumps(detalhe, ensure_ascii=False) if detalhe is not None else None,
                historico_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def listar(limite=50, db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        colunas = [
            "id", "tipo", "admin_email", "inicio", "fim", "desfecho",
            "sucessos", "falhas", "pausas", "linhas_consolidadas", "campi_mantidos", "detalhe",
        ]
        rows = conn.execute(
            f"SELECT {', '.join(colunas)} FROM historico ORDER BY inicio DESC LIMIT ?", (limite,)
        ).fetchall()
        resultado = []
        for row in rows:
            item = dict(zip(colunas, row))
            item["campi_mantidos"] = json.loads(item["campi_mantidos"]) if item["campi_mantidos"] else None
            item["detalhe"] = json.loads(item["detalhe"]) if item["detalhe"] else None
            resultado.append(item)
        return resultado
    finally:
        conn.close()
