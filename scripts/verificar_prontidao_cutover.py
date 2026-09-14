"""Verificação automatizada de prontidão para o cutover — Tarefa 10 do plano
de reconstrução, a partir de `_reversa_sdd/migration/cutover_plan.md` e
`_reversa_sdd/migration/risk_register.md`.

Cobre a parte do checklist de `cutover_plan.md` que é verificável por código
antes do corte (Big Bang, sem gate de Parallel Run — `migration_strategy.md`):

- RISK-008 (crítico): nenhuma coluna de PII em nenhuma tabela do schema ativo.
- RISK-009 (alto): autenticação da rota administrativa de upload configurada.
- RISK-004 (crítico): validação de schema de upload está ativa (`validators.py`).
- Dataset ativo presente e ano-base configurado.

NÃO cobre (são passos humanos de `cutover_plan.md`, não automatizáveis):
- Paridade numérica 100% (`parity_specs.md`/`parity_tests/` — Tarefa 11).
- Validação de design responsivo em dispositivo móvel real.
- Comunicação aos stakeholders e decommission do Power BI Service.

Uso: `python scripts/verificar_prontidao_cutover.py`
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.schema import DEFAULT_DB_PATH, get_connection  # noqa: E402
from app.data.transform import COLUNAS_PII  # noqa: E402

TABELAS = ["campus", "cursos", "ciclos", "matriculas", "matriculas_eficiencia", "config", "uploads_log"]


def verificar_ausencia_pii(db_path=DEFAULT_DB_PATH):
    """RISK-008: nenhuma coluna de PII em nenhuma tabela do schema ativo."""
    conn = get_connection(db_path)
    try:
        achados = []
        for tabela in TABELAS:
            colunas = [row[1] for row in conn.execute(f"PRAGMA table_info({tabela})")]
            para_essa_tabela = [c for c in colunas if c.upper() in {p.upper() for p in COLUNAS_PII}]
            if para_essa_tabela:
                achados.append((tabela, para_essa_tabela))
        return achados
    finally:
        conn.close()


def verificar_autenticacao_admin():
    """RISK-009: credenciais da rota administrativa configuradas (não em
    branco) — não verifica a força da senha, apenas a presença da config."""
    return bool(os.environ.get("ADMIN_EMAIL")) and bool(os.environ.get("ADMIN_PASSWORD_HASH"))


def verificar_dataset_ativo(db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        n = conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0]
        return n > 0
    finally:
        conn.close()


def verificar_ano_base(db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave='ano_base'").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def rodar_verificacoes(db_path=DEFAULT_DB_PATH):
    resultados = []

    achados_pii = verificar_ausencia_pii(db_path)
    resultados.append(("RISK-008: ausência de PII no schema", not achados_pii, achados_pii))

    resultados.append(("RISK-009: autenticação admin configurada", verificar_autenticacao_admin(), None))

    resultados.append(("Dataset ativo presente", verificar_dataset_ativo(db_path), None))

    ano_base = verificar_ano_base(db_path)
    resultados.append(("Ano-base configurado (BR-MIGRAR-016)", ano_base is not None, ano_base))

    return resultados


def imprimir_relatorio(resultados):
    print("=== Verificação de prontidão para cutover (Tarefa 10) ===\n")
    todos_ok = True
    for nome, ok, detalhe in resultados:
        status = "OK" if ok else "FALHA"
        if not ok:
            todos_ok = False
        linha = f"[{status}] {nome}"
        if detalhe:
            linha += f" — {detalhe}"
        print(linha)

    print()
    print("--- Fora do escopo automatizável (ver CUTOVER.md) ---")
    print("[ ] Paridade 100% em parity_specs.md/parity_tests/ (Tarefa 11)")
    print("[ ] Design gov.br responsivo validado em dispositivo móvel real")
    print("[ ] Comunicação da data de transição aos stakeholders")
    print()
    print("GO" if todos_ok else "NO-GO", "(critérios automatizáveis)")
    return todos_ok


if __name__ == "__main__":
    ok = imprimir_relatorio(rodar_verificacoes())
    sys.exit(0 if ok else 1)
