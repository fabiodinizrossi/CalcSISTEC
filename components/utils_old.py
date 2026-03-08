import pandas as pd

EVASAO_STATUSES = {"ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"}
CONCLUSAO_STATUSES = {"CONCLUÍDA", "INTEGRALIZADA"}
EM_CURSO_STATUSES = {"EM_CURSO"}

FIC_SUBTIPOS = {"FORMAÇÃO INICIAL", "FORMAÇÃO CONTINUADA", "FORMAÇÃO CONTINUADA ", "FORMAÇÃO INICIAL "}

def safe_to_datetime(s):
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return s

def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    out = df

    # Ano de ingresso (range)
    if f.get("ano_ingresso"):
        a0, a1 = f["ano_ingresso"]
        if "ANO_INGRESSO" in out.columns:
            out = out[(out["ANO_INGRESSO"] >= a0) & (out["ANO_INGRESSO"] <= a1)]

    # Campus
    if f.get("campus") and f["campus"] != "Todos":
        out = out[out["CAMPUS"] == f["campus"]]

    # Subtipo
    if f.get("subtipo") and f["subtipo"] != "Todos":
        out = out[out["SUBTIPO_CURSO"] == f["subtipo"]]

    # Modalidade
    if f.get("modalidade") and f["modalidade"] != "Todos":
        out = out[out["MODALIDADE"] == f["modalidade"]]

    # Oferta
    if f.get("oferta") and f["oferta"] != "Todos":
        out = out[out["OFERTA"] == f["oferta"]]

    # Curso
    if f.get("curso") and f["curso"] != "Todos":
        out = out[out["CURSO"] == f["curso"]]

    # Programa
    if f.get("programa") and f["programa"] != "Todos":
        out = out[out["PROGRAMA"] == f["programa"]]

    # FIC toggle
    fic_mode = f.get("fic_mode", "SEM_FIC")  # SEM_FIC | COM_FIC
    if fic_mode == "SEM_FIC":
        out = out[~out["SUBTIPO_CURSO"].isin(FIC_SUBTIPOS)]
    # COM_FIC: não filtra

    return out

def compute_equivalente(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return 0.0
    if "EQ_MATRICULA" in df.columns:
        return float(df["EQ_MATRICULA"].sum(skipna=True))
    return float(len(df))
