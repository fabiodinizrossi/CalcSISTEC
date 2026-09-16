"""Arquivo de fatores FEC/FECH: leitura, validação, conversão e casamento
(`002-baixador-planilhas-sistec`, T028/T029, D-07, D-09, D-10, D-11).

Substitui `app/data/transform.t05_default_fec_fech`: a partir desta feature,
o casamento de fatores usa tipo + nome do curso (D-07), não mais o código do
portfólio, e a tabela `fatores` (por versão) é editável em Configurações, com
arquivo enviado, prévia e restauração ao padrão (`dados_FEC_PNP.xlsx`).
"""

import openpyxl
import pandas as pd

from app.data.schema import DEFAULT_DB_PATH, CONVERSAO_TIPO_FATORES, TIPOS_SO_PELO_TIPO, get_connection, normalizar

COLUNAS_OBRIGATORIAS = {"TIPO DE CURSO", "CURSO", "FEC", "FECH"}

# D-09: tipos convertidos sem correspondência entre os subtipos do Sistec —
# mantidos na tabela, mas sinalizados como aviso informativo na prévia
# (RN-34 não os recusa, só o arquivo malformado é recusado).
TIPOS_SEM_CORRESPONDENCIA_SISTEC = {
    "EDUCAÇÃO INFANTIL",
    "ENSINO FUNDAMENTAL I",
    "ENSINO FUNDAMENTAL II",
    "ENSINO MÉDIO",
    "ESPECIALIZAÇÃO PROFISSIONAL TÉCNICA",
    "APERFEIÇOAMENTO TECNOLÓGICO",
    "DOUTORADO (ACADÊMICO/PROFISSIONAL)",
}


class ArquivoFatoresInvalido(Exception):
    """RN-35: o arquivo inteiro é recusado, com a lista de erros encontrados."""

    def __init__(self, erros):
        self.erros = list(erros)
        super().__init__("; ".join(self.erros))


def _localizar_aba(wb):
    """D-11: a aba é a única cujo cabeçalho (1ª linha, normalizado) contém as
    4 colunas obrigatórias. Retorna a lista de abas candidatas (0, 1 ou mais)."""
    candidatas = []
    for nome in wb.sheetnames:
        ws = wb[nome]
        primeira = next(ws.iter_rows(max_row=1), None)
        if not primeira:
            continue
        cabecalho = [normalizar(c.value) if c.value is not None else "" for c in primeira]
        if COLUNAS_OBRIGATORIAS.issubset(set(cabecalho)):
            candidatas.append((ws, cabecalho))
    return candidatas


def ler_e_validar(caminho_ou_arquivo):
    """D-11/RN-34/RN-35/D-09/D-10. Lê e valida um arquivo de fatores.

    Retorna `(linhas, avisos)`, onde `linhas` é uma lista de tuplas
    `(tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome)` prontas para
    gravação em `fatores`/`interna_fatores`, e `avisos` é a lista de tipos sem
    correspondência no Sistec (D-09), mantidos mas informativos.

    Levanta `ArquivoFatoresInvalido` com a lista completa de erros (RN-35):
    nenhuma ou mais de uma aba candidata; `TIPO DE CURSO`/`CURSO` vazio;
    `FEC`/`FECH` vazio ou não numérico; linha repetida por chave após a
    conversão (o que também cobre D-10: tipo só-pelo-tipo com mais de uma
    linha, porque a chave desses tipos colapsa para `chave_nome=''`).
    """
    wb = openpyxl.load_workbook(caminho_ou_arquivo, read_only=True, data_only=True)
    try:
        candidatas = _localizar_aba(wb)
        if len(candidatas) == 0:
            raise ArquivoFatoresInvalido(["nenhuma aba com as colunas TIPO DE CURSO, CURSO, FEC, FECH"])
        if len(candidatas) > 1:
            raise ArquivoFatoresInvalido(["mais de uma aba com as colunas TIPO DE CURSO, CURSO, FEC, FECH"])

        ws, cabecalho = candidatas[0]
        indices = {nome: i for i, nome in enumerate(cabecalho)}

        erros = []
        avisos_vistos = set()
        linhas = []
        vistas = set()

        for n, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if row is None or all(v is None for v in row):
                continue

            def _valor(coluna):
                i = indices[coluna]
                return row[i] if i < len(row) else None

            tipo_bruto = _valor("TIPO DE CURSO")
            nome_bruto = _valor("CURSO")
            fec_bruto = _valor("FEC")
            fech_bruto = _valor("FECH")

            if tipo_bruto is None or str(tipo_bruto).strip() == "":
                erros.append(f"linha {n}: TIPO DE CURSO vazio")
                continue
            if nome_bruto is None or str(nome_bruto).strip() == "":
                erros.append(f"linha {n}: CURSO vazio")
                continue
            try:
                fec = float(fec_bruto)
            except (TypeError, ValueError):
                erros.append(f"linha {n}: FEC vazio ou não numérico")
                continue
            try:
                fech = float(fech_bruto)
            except (TypeError, ValueError):
                erros.append(f"linha {n}: FECH vazio ou não numérico")
                continue

            tipo_normalizado_bruto = normalizar(tipo_bruto)
            tipo_curso = CONVERSAO_TIPO_FATORES.get(tipo_normalizado_bruto, str(tipo_bruto).strip())
            chave_tipo = normalizar(tipo_curso)
            so_pelo_tipo = chave_tipo in TIPOS_SO_PELO_TIPO
            nome_curso = "TODOS" if so_pelo_tipo else str(nome_bruto).strip()
            chave_nome = "" if so_pelo_tipo else normalizar(nome_curso)
            chave = (chave_tipo, chave_nome)

            if chave in vistas:
                erros.append(f"linha {n}: chave repetida após conversão ({tipo_curso} / {nome_curso})")
                continue
            vistas.add(chave)

            if chave_tipo in TIPOS_SEM_CORRESPONDENCIA_SISTEC:
                avisos_vistos.add(tipo_curso)

            linhas.append((tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome))
    finally:
        wb.close()

    if erros:
        raise ArquivoFatoresInvalido(erros)

    return linhas, sorted(avisos_vistos)


def diferenca_fatores(linhas_atuais, linhas_novas):
    """Prévia da troca (data-delta.md §3.1): diferença por (chave_tipo,
    chave_nome) entre a tabela atual (linhas de `(chave_tipo, chave_nome, fec,
    fech)`, ou tuplas completas de `ler_e_validar`) e a nova. Retorna dict com
    `incluidas`, `removidas` e `alteradas` (cada item com fec/fech antes e
    depois)."""

    def _mapa(linhas):
        return {(l[4], l[5]): (l[2], l[3]) for l in linhas}

    atuais = _mapa(linhas_atuais)
    novas = _mapa(linhas_novas)

    incluidas = sorted(set(novas) - set(atuais))
    removidas = sorted(set(atuais) - set(novas))
    alteradas = sorted(
        chave
        for chave in set(atuais) & set(novas)
        if atuais[chave] != novas[chave]
    )

    return {
        "incluidas": [{"chave": c, "fec": novas[c][0], "fech": novas[c][1]} for c in incluidas],
        "removidas": [{"chave": c, "fec": atuais[c][0], "fech": atuais[c][1]} for c in removidas],
        "alteradas": [
            {"chave": c, "antes": atuais[c], "depois": novas[c]} for c in alteradas
        ],
    }


def casar_fatores(df_cursos, df_fatores):
    """D-07: substitui `transform.t05_default_fec_fech`. A chave é
    `normalizar(tipo_curso_pnp)` + `normalizar(nome_curso_ajustado)`; para os
    3 tipos só-pelo-tipo (D-07/D-10), a chave usa `chave_nome=''`. Sem
    casamento: FEC 1, FECH 1 e `fator_nao_encontrado=1`.

    `df_cursos` precisa ter `tipo_curso_pnp` e `nome_curso_ajustado`.
    `df_fatores` precisa ter `chave_tipo`, `chave_nome`, `fec`, `fech` (lida
    direto de `fatores`/`interna_fatores`). Retorna uma cópia de `df_cursos`
    com `fec`, `fech` e `fator_nao_encontrado` (re)calculados.
    """
    df = df_cursos.copy()
    chave_tipo = df["tipo_curso_pnp"].map(normalizar)
    chave_nome = df["nome_curso_ajustado"].map(normalizar)
    so_pelo_tipo = chave_tipo.isin(TIPOS_SO_PELO_TIPO)
    chave_nome_efetiva = chave_nome.where(~so_pelo_tipo, "")

    chaves = df.assign(_chave_tipo=chave_tipo, _chave_nome=chave_nome_efetiva)[
        ["_chave_tipo", "_chave_nome"]
    ]
    fatores_unicos = df_fatores.drop_duplicates(subset=["chave_tipo", "chave_nome"])
    merged = chaves.merge(
        fatores_unicos[["chave_tipo", "chave_nome", "fec", "fech"]],
        left_on=["_chave_tipo", "_chave_nome"],
        right_on=["chave_tipo", "chave_nome"],
        how="left",
    )

    df["fec"] = merged["fec"].fillna(1.0).to_numpy()
    df["fech"] = merged["fech"].fillna(1.0).to_numpy()
    df["fator_nao_encontrado"] = merged["fec"].isna().to_numpy().astype(int)
    return df


def ler_fatores_atuais(tabela, db_path=DEFAULT_DB_PATH):
    """Lê `fatores`/`interna_fatores`/`anterior_fatores` no formato de
    tupla usado por `diferenca_fatores`/`ler_e_validar`."""
    conn = get_connection(db_path)
    try:
        linhas = conn.execute(
            f"SELECT tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome FROM {tabela}"
        ).fetchall()
        return linhas
    finally:
        conn.close()


def substituir_interna_fatores(linhas, db_path=DEFAULT_DB_PATH):
    """Troca o conteúdo de `interna_fatores` (arquivo enviado ou restauração
    do padrão) e recasa `interna_cursos.fec`/`.fech`/`.fator_nao_encontrado`
    na mesma transação (data-delta.md §6: "toda gravação de `interna_fatores`
    reexecuta o casamento na mesma transação")."""
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM interna_fatores")
        conn.executemany(
            "INSERT INTO interna_fatores (tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            linhas,
        )

        cursos = pd.read_sql_query("SELECT * FROM interna_cursos", conn)
        if not cursos.empty:
            fatores_novos = pd.read_sql_query(
                "SELECT tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome FROM interna_fatores", conn
            )
            cursos_recasados = casar_fatores(cursos, fatores_novos)
            conn.execute("DELETE FROM interna_cursos")
            cursos_recasados.to_sql("interna_cursos", conn, if_exists="append", index=False)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
