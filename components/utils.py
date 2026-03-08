import pandas as pd


EVASAO_STATUSES = {"ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"}
CONCLUSAO_STATUSES = {"CONCLUIDO"}
EM_CURSO_STATUSES = {"EM_CURSO"}


def clean_str(series):
    return (
        series.fillna("N/D")
        .astype(str)
        .str.strip()
        .replace("", "N/D")
    )


def clean_sorted(series):
    return sorted(clean_str(series).unique().tolist())


def apply_filters(df, filters):
    if df is None or len(df) == 0:
        return df

    out = df.copy()

    if not filters:
        return out

    ano_ingresso = filters.get("ano_ingresso")
    if ano_ingresso and "ANO_INGRESSO" in out.columns:
        out = out[
            (pd.to_numeric(out["ANO_INGRESSO"], errors="coerce") >= int(ano_ingresso[0]))
            & (pd.to_numeric(out["ANO_INGRESSO"], errors="coerce") <= int(ano_ingresso[1]))
        ]

    if filters.get("campus") and filters["campus"] != "Todos" and "CAMPUS" in out.columns:
        out = out[out["CAMPUS"] == filters["campus"]]

    if filters.get("subtipo") and filters["subtipo"] != "Todos" and "SUBTIPO_CURSO" in out.columns:
        out = out[out["SUBTIPO_CURSO"] == filters["subtipo"]]

    if filters.get("modalidade") and filters["modalidade"] != "Todos" and "MODALIDADE" in out.columns:
        out = out[out["MODALIDADE"] == filters["modalidade"]]

    if filters.get("oferta") and filters["oferta"] != "Todos" and "OFERTA" in out.columns:
        out = out[out["OFERTA"] == filters["oferta"]]

    if filters.get("curso") and filters["curso"] != "Todos" and "CURSO" in out.columns:
        out = out[out["CURSO"] == filters["curso"]]

    if filters.get("programa") and filters["programa"] != "Todos" and "PROGRAMA" in out.columns:
        out = out[out["PROGRAMA"] == filters["programa"]]

    if filters.get("fic_mode") == "SEM_FIC" and "SUBTIPO_CURSO" in out.columns:
        subtipo_norm = (
            out["SUBTIPO_CURSO"]
            .astype(str)
            .str.upper()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
        )
        mask_fic = (
            subtipo_norm.str.contains("FORMACAO INICIAL", na=False)
            | subtipo_norm.str.contains("FORMACAO CONTINUADA", na=False)
            | subtipo_norm.str.contains("FIC", na=False)
        )
        out = out[~mask_fic]

    return out


def classify_status(series):
    s = (
        series.fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    result = pd.Series(["OUTROS"] * len(s), index=s.index)

    result[s.str.contains("CONCL", na=False)] = "CONCLUIDO"
    result[s.str.contains("INTEGRAL", na=False)] = "CONCLUIDO"
    result[s.str.contains("EM CURSO|EM_CURSO|CURSANDO", na=False)] = "EM_CURSO"
    result[s.str.contains("ABAND", na=False)] = "ABANDONO"
    result[s.str.contains("TRANSF.*EXT", na=False)] = "TRANSF_EXT"
    result[s.str.contains("DESLIG", na=False)] = "DESLIGADO"
    result[s.str.contains("TRANSF.*INT", na=False)] = "TRANSF_INT"
    result[s.str.contains("REPROV|RETID", na=False)] = "RETIDO"

    return result


def matriculas_equivalentes(df):
    if df is None or len(df) == 0:
        return 0.0

    if "EQ_MATRICULA" in df.columns:
        return float(pd.to_numeric(df["EQ_MATRICULA"], errors="coerce").fillna(0).sum())

    return float(len(df))


def compute_equivalente(df):
    return matriculas_equivalentes(df)
