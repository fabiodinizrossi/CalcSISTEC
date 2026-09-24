"""Verificação automatizada de prontidão para o cutover — Tarefa 10 do plano
de reconstrução, atualizada por `002-baixador-planilhas-sistec` (T068).

O roteiro de implantação e as pendências humanas estão em `DEPLOY.md`.

Cobre a parte do checklist que é verificável por código antes do corte:

- RISK-008 (crítico): nenhuma coluna de PII em nenhuma tabela do schema ativo.
- RISK-009 (alto): autenticação da rota administrativa configurada.
- Schema v2 aplicado (`config.schema_versao`, D-14: `RISK-004`/`uploads_log`
  saíram do sistema com o upload `.xlsx`).
- Fatores carregados (`fatores`/`interna_fatores` não vazias, D-11).
- HTTPS configurado (D-19: `CALCSISTEC_HTTPS=1`) — as rotas `/api/sistec/*`
  bloqueiam bytes com dado pessoal sem cifrar fora de `localhost`.
- Dataset publicado presente e ano-base configurado.

NÃO cobre (são passos humanos, não automatizáveis):
- Paridade numérica 100% (`parity_specs.md`/`parity_tests/` — Tarefa 11).
- Validação de design responsivo em dispositivo móvel real.
- Roteiro de `onboarding.md` (Sistec simulado + 1 baixa real).
- Instalação da extensão na máquina da PI e política institucional (P-10).
- Comunicação aos stakeholders e decommission do Power BI Service.

Uso: `python scripts/verificar_prontidao_cutover.py`
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.schema import DEFAULT_DB_PATH, SCHEMA_VERSAO_ATUAL, get_connection  # noqa: E402
from app.data.transform import COLUNAS_PII  # noqa: E402

TABELAS = [
    "campus", "cursos", "ciclos", "matriculas", "matriculas_eficiencia",
    "interna_campus", "interna_cursos", "interna_ciclos", "interna_matriculas", "interna_matriculas_eficiencia",
    "anterior_campus", "anterior_cursos", "anterior_ciclos", "anterior_matriculas", "anterior_matriculas_eficiencia",
    "fatores", "interna_fatores", "anterior_fatores",
    "campi_sistec", "historico", "config",
]


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


def verificar_schema_v2(db_path=DEFAULT_DB_PATH):
    """D-14: substitui a checagem de RISK-004 (validação de upload, removida
    com a rota `/admin/upload`) — o que garante um dataset consistente agora
    é o schema v2 aplicado (T004-T012)."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave='schema_versao'").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def verificar_fatores_carregados(db_path=DEFAULT_DB_PATH):
    """D-11: `fatores`/`interna_fatores` não vazias — sem isso, todo curso
    cai no default `fec=1, fech=1, fator_nao_encontrado=1` (D-07)."""
    conn = get_connection(db_path)
    try:
        publicada = conn.execute("SELECT COUNT(*) FROM fatores").fetchone()[0]
        interna = conn.execute("SELECT COUNT(*) FROM interna_fatores").fetchone()[0]
        return publicada > 0 and interna > 0
    finally:
        conn.close()


def verificar_https_configurado():
    """D-19: `CALCSISTEC_HTTPS=1` liga `SESSION_COOKIE_SECURE` e faz as
    rotas `/api/sistec/*` recusarem HTTP simples fora de `localhost` — bytes
    com dado pessoal só podem trafegar cifrados."""
    return os.environ.get("CALCSISTEC_HTTPS") == "1"


def rodar_verificacoes(db_path=DEFAULT_DB_PATH):
    resultados = []

    achados_pii = verificar_ausencia_pii(db_path)
    resultados.append(("RISK-008: ausência de PII no schema", not achados_pii, achados_pii))

    resultados.append(("RISK-009: autenticação admin configurada", verificar_autenticacao_admin(), None))

    schema_versao = verificar_schema_v2(db_path)
    resultados.append(
        ("Schema v2 aplicado (substitui RISK-004/uploads_log, D-14)", schema_versao == SCHEMA_VERSAO_ATUAL, schema_versao)
    )

    resultados.append(("Fatores carregados (D-11)", verificar_fatores_carregados(db_path), None))

    resultados.append(("HTTPS configurado (D-19, CALCSISTEC_HTTPS=1)", verificar_https_configurado(), None))

    resultados.append(("Dataset publicado presente", verificar_dataset_ativo(db_path), None))

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
    print("--- Fora do escopo automatizável (ver DEPLOY.md) ---")
    print("[ ] Paridade 100% em parity_specs.md/parity_tests/ (Tarefa 11)")
    print("[ ] Design gov.br responsivo validado em dispositivo móvel real")
    print("[ ] Roteiro de onboarding.md com o Sistec simulado e 1 baixa real")
    print("[ ] Extensão Baixador Sistec instalada na máquina da PI (P-10)")
    print("[ ] Comunicação da data de transição aos stakeholders")
    print()
    print("GO" if todos_ok else "NO-GO", "(critérios automatizáveis)")
    return todos_ok


if __name__ == "__main__":
    ok = imprimir_relatorio(rodar_verificacoes())
    sys.exit(0 if ok else 1)
