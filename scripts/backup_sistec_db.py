"""Backup de `sistec.db` antes de qualquer migração de schema — feature
`002-baixador-planilhas-sistec`, ação T002 de `actions.md`.

Copia o banco ativo para `app/data/backups/sistec-<timestamp>.db` antes de
`schema.init_db` rodar a migração para o schema v2 (ver `data-delta.md` §7).
Não apaga backups antigos: cada execução gera um arquivo novo, com timestamp
no nome, para permitir rollback manual (roadmap.md §8, "Rollback").

Uso: `python scripts/backup_sistec_db.py [caminho_do_db]`
"""

import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.schema import DEFAULT_DB_PATH  # noqa: E402

BACKUP_DIR = os.path.join(os.path.dirname(DEFAULT_DB_PATH), "backups")


def fazer_backup(db_path=DEFAULT_DB_PATH, backup_dir=BACKUP_DIR):
    """Copia `db_path` para `backup_dir/sistec-<timestamp>.db`.

    Não faz nada além da cópia: sem dados pessoais no banco (BR-DESCARTAR-001),
    o backup em si não precisa de tratamento especial de privacidade.
    Devolve o caminho do arquivo de backup criado, ou None se `db_path`
    não existir ainda (primeira execução, banco novo).
    """
    if not os.path.exists(db_path):
        print(f"Nenhum banco em {db_path} ainda — nada para copiar.")
        return None

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = os.path.join(backup_dir, f"sistec-{timestamp}.db")
    shutil.copy2(db_path, destino)
    print(f"Backup criado em {destino}")
    return destino


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    fazer_backup(caminho)
