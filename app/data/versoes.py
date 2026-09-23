"""Transações de versão: salvar interna, publicar, desfazer e aplicar no
público (`002-baixador-planilhas-sistec`, T033, D-05, D-06, `data-delta.md`
§3.3, §6).

As tabelas atuais (`campus`, `cursos`, `ciclos`, `matriculas`,
`matriculas_eficiencia`, `fatores`) são a versão **publicada**. `interna_*` e
`anterior_*` têm DDL idêntico. Cada operação roda em uma única transação
`BEGIN IMMEDIATE`, nunca mistura leitor com estado parcial (RN-21, RN-27).

`campus` só muda por `aplicar_publico` (projeção de `campi_sistec` via
`interna_campus`, RN-33) — nunca pelo ciclo salvar/publicar/desfazer de
baixa, que cobre `cursos`, `ciclos`, `matriculas`, `matriculas_eficiencia` e
`fatores`.
"""

import datetime

import pandas as pd

from app.data.schema import DEFAULT_DB_PATH, get_connection

# FKs: interna_ciclos/ciclos -> cursos; interna_matriculas(_eficiencia)/matriculas(_eficiencia) -> ciclos.
# DELETE precisa ir do filho para o pai; INSERT, do pai para o filho.
_ORDEM_DELETE_BAIXA = ("matriculas_eficiencia", "matriculas", "ciclos", "cursos")
_ORDEM_INSERT_BAIXA = ("cursos", "ciclos", "matriculas", "matriculas_eficiencia")
_ORDEM_DELETE_PUBLICACAO = _ORDEM_DELETE_BAIXA + ("fatores",)
_ORDEM_INSERT_PUBLICACAO = ("fatores",) + _ORDEM_INSERT_BAIXA

# Colunas explícitas de cada tabela interna (mesma ordem do schema v2). A
# gravação por `executemany` não infere colunas como `DataFrame.to_sql` fazia.
_COLUNAS_INTERNA = {
    "cursos": [
        "codigo_portfolio", "nome_curso_ajustado", "tipo_curso_pnp", "subtipo_curso",
        "modalidade_ensino", "eixo_tecnologico_ajustado", "fec", "fech",
        "carga_horaria_total", "co_unidade", "tipo_oferta_curso",
        "categoria_origem_curso", "fator_nao_encontrado",
    ],
    "ciclos": [
        "codigo_ciclo_matricula", "codigo_portfolio", "co_unidade", "dt_data_inicio",
        "dt_data_fim_previsto", "tipo_programa_curso", "status_ciclo",
    ],
    "matriculas": [
        "co_matricula", "codigo_ciclo_matricula", "status_corrigido",
        "mes_ocorrencia_corrigido", "ano_base",
    ],
    "matriculas_eficiencia": ["co_matricula", "codigo_ciclo_matricula", "status_corrigido2"],
}

# Inserção em lotes limitados para não estourar a memória do `executemany` num
# envio próximo do teto de 500 MB.
_TAMANHO_LOTE = 1000


class ConflitoDeConferencia(Exception):
    """A assinatura de origem do candidato divergiu do estado atual do banco
    (revisões, ano-base, `interna_fatores` ou `campus` publicado) entre a
    conferência da prévia e o Salvar (`previa-paginas-publicas`, PVP-10)."""


def _now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def salvar_interna(conjunto, db_path=DEFAULT_DB_PATH, assinatura_esperada=None):
    """RN-20: grava `conjunto` (dict com DataFrames "cursos", "ciclos",
    "matriculas", "matriculas_eficiencia", já com `casar_fatores` aplicado
    pelo chamador) em `interna_*`, substituindo o conteúdo anterior, numa
    única transação. Incrementa `estado_versoes.rev_interna`.

    PVP-10 (`previa-paginas-publicas`): com `assinatura_esperada`, confere a
    assinatura de origem dentro do `BEGIN IMMEDIATE`, antes do primeiro
    `DELETE`; divergência faz rollback e levanta `ConflitoDeConferencia`, sem
    trocar nenhuma tabela. `assinatura_esperada=None` mantém o caminho da
    baixa direta. A gravação usa `sqlite3.executemany` em lotes (colunas
    explícitas, NaN/NaT normalizados para None), revertível na transação."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")

        if assinatura_esperada is not None:
            # Import tardio: `ingest` importa `versoes`, então a importação no
            # topo seria circular. A leitura roda por outra conexão, mas o
            # `BEGIN IMMEDIATE` já segura o lock de escrita — o estado lido é
            # o mesmo que será gravado.
            from app.data.ingest import calcular_assinatura_origem

            if calcular_assinatura_origem(db_path) != assinatura_esperada:
                raise ConflitoDeConferencia("a conferência da prévia está desatualizada")

        for tabela in _ORDEM_DELETE_BAIXA:
            conn.execute(f"DELETE FROM interna_{tabela}")
        for tabela in _ORDEM_INSERT_BAIXA:
            df = conjunto[tabela]
            if df.empty:
                continue
            colunas = _COLUNAS_INTERNA[tabela]
            marcadores = ", ".join("?" * len(colunas))
            sql = f"INSERT INTO interna_{tabela} ({', '.join(colunas)}) VALUES ({marcadores})"
            linhas = [
                tuple(None if pd.isna(valor) else valor for valor in linha)
                for linha in df[colunas].itertuples(index=False, name=None)
            ]
            for inicio in range(0, len(linhas), _TAMANHO_LOTE):
                conn.executemany(sql, linhas[inicio:inicio + _TAMANHO_LOTE])

        conn.execute(
            "UPDATE estado_versoes SET rev_interna = rev_interna + 1, interna_gravada_em = ? WHERE id = 1",
            (_now_iso(),),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def publicar(db_path=DEFAULT_DB_PATH, admin_email=None):
    """RN-21/RN-27/RN-30: `anterior_* <- publicada` (só se já havia uma
    publicação), `publicada <- interna_*`, `rev_anterior <- rev_publicada`,
    `rev_publicada <- rev_interna`. `interna_*` não é alterada (RN-20)."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        rev_publicada, rev_interna = conn.execute(
            "SELECT rev_publicada, rev_interna FROM estado_versoes WHERE id = 1"
        ).fetchone()

        for tabela in _ORDEM_DELETE_PUBLICACAO:
            conn.execute(f"DELETE FROM anterior_{tabela}")
        if rev_publicada is not None:
            # Snapshot da publicada ATUAL (antes de apagá-la) para anterior_*.
            for tabela in _ORDEM_INSERT_PUBLICACAO:
                conn.execute(f"INSERT INTO anterior_{tabela} SELECT * FROM {tabela}")
        for tabela in _ORDEM_DELETE_PUBLICACAO:
            conn.execute(f"DELETE FROM {tabela}")
        for tabela in _ORDEM_INSERT_PUBLICACAO:
            conn.execute(f"INSERT INTO {tabela} SELECT * FROM interna_{tabela}")

        conn.execute(
            "UPDATE estado_versoes SET rev_anterior = ?, rev_publicada = ?, "
            "publicada_em = ?, publicada_por = ? WHERE id = 1",
            (rev_publicada, rev_interna, _now_iso(), admin_email),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def desfazer(db_path=DEFAULT_DB_PATH):
    """RN-27: `publicada <- anterior_*`, `rev_publicada <- rev_anterior`,
    esvazia `anterior_*` e `rev_anterior <- NULL`. `interna_*` intocada."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        (rev_anterior,) = conn.execute("SELECT rev_anterior FROM estado_versoes WHERE id = 1").fetchone()
        if rev_anterior is None:
            raise ValueError("nada a desfazer: rev_anterior é NULL")

        for tabela in _ORDEM_DELETE_PUBLICACAO:
            conn.execute(f"DELETE FROM {tabela}")
        for tabela in _ORDEM_INSERT_PUBLICACAO:
            conn.execute(f"INSERT INTO {tabela} SELECT * FROM anterior_{tabela}")
        for tabela in _ORDEM_DELETE_PUBLICACAO:
            conn.execute(f"DELETE FROM anterior_{tabela}")

        conn.execute(
            "UPDATE estado_versoes SET rev_publicada = ?, rev_anterior = NULL WHERE id = 1",
            (rev_anterior,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def aplicar_publico(db_path=DEFAULT_DB_PATH, admin_email=None):
    """RN-33: aplica no painel público as edições feitas só na versão interna
    de `campus` (projeção de `campi_sistec` via `interna_campus`) e
    `fatores`, fora do ciclo de baixa. Não mexe em `anterior_*` (não é uma
    publicação de baixa, e "Desfazer" continua se referindo só à baixa).

    `data-delta.md` §3.3: se `rev_interna == rev_publicada` antes, as duas
    passam a `rev_interna + 1`; senão só `rev_interna` avança (a publicada
    recebe a alteração do mesmo jeito)."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        rev_publicada, rev_interna = conn.execute(
            "SELECT rev_publicada, rev_interna FROM estado_versoes WHERE id = 1"
        ).fetchone()

        conn.execute("DELETE FROM campus")
        conn.execute("INSERT INTO campus SELECT * FROM interna_campus")
        conn.execute("DELETE FROM fatores")
        conn.execute("INSERT INTO fatores SELECT * FROM interna_fatores")

        # data-delta.md §3.3: nas duas ramificações (rev_publicada == rev_interna
        # ou não) o resultado da publicada é o mesmo — a diferença do texto é só
        # sobre se a interna "também" avança (sempre avança) ou se as duas já
        # estavam empatadas antes.
        nova_rev_interna = rev_interna + 1
        nova_rev_publicada = nova_rev_interna

        agora = _now_iso()
        conn.execute(
            "UPDATE estado_versoes SET rev_interna = ?, rev_publicada = ?, "
            "interna_gravada_em = ?, publicada_em = ?, publicada_por = ? WHERE id = 1",
            (nova_rev_interna, nova_rev_publicada, agora, agora, admin_email),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
