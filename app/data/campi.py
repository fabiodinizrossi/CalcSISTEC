"""Lista de campi do Sistec (`002-baixador-planilhas-sistec`, T034, RN-03,
RN-05, `data-delta.md` §3.2).

`campi_sistec` não tem versão (não faz parte do ciclo interna/publicada/
anterior). A projeção para `interna_campus`/`campus` acontece em
`app/data/versoes.aplicar_publico`.

A lista é regravada a cada leitura do Sistec (`app/sistec/navegador.py`),
preservando o que foi editado em Configurações: código, cidade e nome da
unidade, campus desativado (`ativo = 0`, deixa de ser baixado) e perfis
incluídos à mão (`origem = 'manual'`).
"""

import datetime
import sqlite3

from app.data.schema import DEFAULT_DB_PATH, get_connection
from app.sistec.perfis import chave_campus, extrair_perfil_do_texto

COLUNAS = ["id_perfil", "nome_perfil", "ordem", "co_unidade", "cidade", "nome_unidade", "capturado_em", "ativo", "origem"]

# O identificador real do Sistec (o campo `tipo` do formulário de perfil) tem 7
# dígitos — ex.: 8278860. A extensão MV3 gravava a **posição** do item na lista
# ("0", "1", …), e com isso a troca de campus nunca acontecia: a baixa rodava
# inteira e vinha vazia. Qualquer coisa com menos de 5 dígitos é tratada como
# identificador inválido, e a coleta se recusa a começar (`app/sistec/navegador.py`).
DIGITOS_MINIMOS_ID = 5


class CampusInvalido(ValueError):
    """Identificador do perfil ou código da unidade já usado por outro campus."""


def id_suspeito(id_perfil):
    """`True` para o que o Sistec não aceitaria como identificador de perfil."""
    texto = str(id_perfil or "").strip()
    return not texto.isdigit() or len(texto) < DIGITOS_MINIMOS_ID


def campi_suspeitos(db_path=DEFAULT_DB_PATH, somente_ativos=True):
    """Campi cujo identificador não serve para trocar de campus no Sistec."""
    return [c for c in listar_campi(db_path, somente_ativos=somente_ativos) if id_suspeito(c["id_perfil"])]


def _now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _ler(conn, somente_ativos=False):
    filtro = " WHERE ativo = 1" if somente_ativos else ""
    rows = conn.execute(f"SELECT {', '.join(COLUNAS)} FROM campi_sistec{filtro} ORDER BY ordem").fetchall()
    return [dict(zip(COLUNAS, row)) for row in rows]


def salvar_captura(perfis, db_path=DEFAULT_DB_PATH):
    """RN-05: grava os perfis lidos do Sistec numa transação, preservando o
    que já estava salvo para o mesmo perfil.

    - Casa pelo `id_perfil`; sem casamento, pelo nome do campus
      (`chave_campus`). Isso cobre linhas antigas gravadas com um id que não
      era o do Sistec (a extensão salvava a posição na lista: "0", "1"...).
    - `co_unidade`, `cidade` e `nome_unidade` já salvos têm prioridade sobre
      os lidos agora (preserva edição manual); `ativo` é mantido.
    - Perfis lidos antes e que não vieram agora saem da lista; os incluídos à
      mão (`origem = 'manual'`) ficam.
    - Um código de unidade já usado por outra linha é gravado vazio, em vez
      de estourar o `UNIQUE`.

    `perfis`: lista de dicts `{id_perfil, nome_perfil, ordem, co_unidade?,
    cidade?, nome_unidade?}`."""
    agora = _now_iso()
    ids_novos = {p["id_perfil"] for p in perfis}

    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        existentes = _ler(conn)
        por_id = {e["id_perfil"]: e for e in existentes}
        por_campus = {}
        for existente in existentes:
            if existente["id_perfil"] not in ids_novos:
                por_campus.setdefault(chave_campus(existente["nome_perfil"]), existente)

        anteriores = {}
        for perfil in perfis:
            anterior = por_id.get(perfil["id_perfil"])
            if anterior is None:
                anterior = por_campus.pop(chave_campus(perfil["nome_perfil"]), None)
            anteriores[perfil["id_perfil"]] = anterior

        herdados = {a["id_perfil"] for a in anteriores.values() if a is not None and a["id_perfil"] not in ids_novos}
        removidos = {
            e["id_perfil"]
            for e in existentes
            if e["id_perfil"] not in ids_novos and (e["origem"] != "manual" or e["id_perfil"] in herdados)
        }
        conn.executemany("DELETE FROM campi_sistec WHERE id_perfil = ?", [(i,) for i in removidos])
        # Solta os códigos das linhas que serão regravadas, para uma troca de
        # código entre dois perfis não bater no UNIQUE no meio do laço.
        conn.executemany(
            "UPDATE campi_sistec SET co_unidade = NULL WHERE id_perfil = ?", [(i,) for i in ids_novos if i in por_id]
        )
        codigos_ocupados = {
            e["co_unidade"]
            for e in existentes
            if e["co_unidade"] and e["id_perfil"] not in ids_novos and e["id_perfil"] not in removidos
        }

        for perfil in perfis:
            anterior = anteriores[perfil["id_perfil"]]
            co_unidade = perfil.get("co_unidade")
            cidade = perfil.get("cidade")
            nome_unidade = perfil.get("nome_unidade")
            ativo = 1
            if anterior is not None:
                co_unidade = anterior["co_unidade"] or co_unidade
                cidade = anterior["cidade"] or cidade
                nome_unidade = anterior["nome_unidade"] or nome_unidade
                ativo = anterior["ativo"]
            if co_unidade in codigos_ocupados:
                co_unidade = None
            if co_unidade:
                codigos_ocupados.add(co_unidade)

            conn.execute(
                "INSERT INTO campi_sistec "
                "(id_perfil, nome_perfil, ordem, co_unidade, cidade, nome_unidade, capturado_em, ativo, origem) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'sistec') "
                "ON CONFLICT(id_perfil) DO UPDATE SET nome_perfil=excluded.nome_perfil, ordem=excluded.ordem, "
                "co_unidade=excluded.co_unidade, cidade=excluded.cidade, nome_unidade=excluded.nome_unidade, "
                "capturado_em=excluded.capturado_em, ativo=excluded.ativo, origem='sistec'",
                (
                    perfil["id_perfil"],
                    perfil["nome_perfil"],
                    perfil.get("ordem", 0),
                    co_unidade,
                    cidade,
                    nome_unidade,
                    agora,
                    ativo,
                ),
            )

        _regravar_interna_campus(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def salvar_campus_manual(id_perfil, co_unidade, cidade, nome_unidade, db_path=DEFAULT_DB_PATH, novo_id_perfil=None):
    """RF-10: corrige identificador do perfil, código, cidade e nome da unidade.

    `novo_id_perfil` troca o próprio identificador — é o campo que o Sistec usa
    para mudar o campus ativo, e o que precisa ser corrigido numa lista gravada
    pela extensão antiga. Sem ele, a única saída seria excluir e cadastrar de
    novo, perdendo código, cidade e nome já preenchidos."""
    novo = str(novo_id_perfil or "").strip() or id_perfil
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE campi_sistec SET id_perfil = ?, co_unidade = ?, cidade = ?, nome_unidade = ? WHERE id_perfil = ?",
            (novo, co_unidade, cidade, nome_unidade, id_perfil),
        )
        _regravar_interna_campus(conn)
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if novo != id_perfil:
            raise CampusInvalido("esse identificador de perfil já está em outro campus") from exc
        raise CampusInvalido("esse código da unidade já está em outro campus") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def incluir_campus(id_perfil, nome_perfil, co_unidade=None, cidade=None, nome_unidade=None, db_path=DEFAULT_DB_PATH):
    """Inclui um perfil à mão (`origem = 'manual'`), no fim da lista. Uma
    leitura do Sistec não o remove."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        (ordem,) = conn.execute("SELECT COALESCE(MAX(ordem), -1) + 1 FROM campi_sistec").fetchone()
        conn.execute(
            "INSERT INTO campi_sistec "
            "(id_perfil, nome_perfil, ordem, co_unidade, cidade, nome_unidade, capturado_em, ativo, origem) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'manual')",
            (id_perfil, nome_perfil, ordem, co_unidade, cidade, nome_unidade, _now_iso()),
        )
        _regravar_interna_campus(conn)
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise CampusInvalido("já existe um campus com esse identificador ou código da unidade") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def definir_ativo(id_perfil, ativo, db_path=DEFAULT_DB_PATH):
    """Campus desativado continua na lista (e no painel), mas não é baixado."""
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE campi_sistec SET ativo = ? WHERE id_perfil = ?", (1 if ativo else 0, id_perfil))
        conn.commit()
    finally:
        conn.close()


def preencher_unidade(id_perfil, co_unidade, db_path=DEFAULT_DB_PATH):
    """Preenche o código da unidade (e cidade/nome, se vazios, a partir do
    texto do perfil) quando o campus ainda não tem código. `False` se o
    campus já tem outro código ou se o código está em outro campus."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        linha = conn.execute(
            "SELECT co_unidade, nome_perfil FROM campi_sistec WHERE id_perfil = ?", (id_perfil,)
        ).fetchone()
        if linha is None:
            conn.rollback()
            return False
        if linha[0]:
            conn.rollback()
            return linha[0] == co_unidade
        (em_uso,) = conn.execute(
            "SELECT COUNT(*) FROM campi_sistec WHERE co_unidade = ? AND id_perfil <> ?", (co_unidade, id_perfil)
        ).fetchone()
        if em_uso:
            conn.rollback()
            return False

        lido = extrair_perfil_do_texto(linha[1])
        conn.execute(
            "UPDATE campi_sistec SET co_unidade = ?, cidade = COALESCE(cidade, ?), "
            "nome_unidade = COALESCE(nome_unidade, ?) WHERE id_perfil = ?",
            (co_unidade, lido["cidade"], lido["nome_unidade"], id_perfil),
        )
        _regravar_interna_campus(conn)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def excluir_campus(id_perfil, db_path=DEFAULT_DB_PATH):
    """Exclui um perfil da lista. Se ele ainda existir no Sistec, volta na
    próxima leitura; para deixar de baixá-lo de vez, use `definir_ativo`."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM campi_sistec WHERE id_perfil = ?", (id_perfil,))
        _regravar_interna_campus(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _regravar_interna_campus(conn):
    """data-delta.md §3.2: `interna_campus` é a projeção (co_unidade,
    cidade, nome_unidade) das linhas de `campi_sistec` com os três campos
    preenchidos, regravada a cada gravação de `campi_sistec`."""
    conn.execute("DELETE FROM interna_campus")
    conn.execute(
        "INSERT INTO interna_campus (co_unidade, cidade, nome_unidade) "
        "SELECT co_unidade, cidade, nome_unidade FROM campi_sistec "
        "WHERE co_unidade IS NOT NULL AND cidade IS NOT NULL AND nome_unidade IS NOT NULL"
    )


def listar_campi(db_path=DEFAULT_DB_PATH, somente_ativos=False):
    conn = get_connection(db_path)
    try:
        return _ler(conn, somente_ativos=somente_ativos)
    finally:
        conn.close()


def existe_campus_sem_unidade(db_path=DEFAULT_DB_PATH):
    """RF-10: algum campus ativo ainda sem `co_unidade`."""
    conn = get_connection(db_path)
    try:
        (n,) = conn.execute("SELECT COUNT(*) FROM campi_sistec WHERE co_unidade IS NULL AND ativo = 1").fetchone()
        return n > 0
    finally:
        conn.close()
