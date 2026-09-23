"""Leitura das pastas CSV enviadas na atualização administrativa."""

import pandas as pd

from app.sistec.colunas import ler_planilha


class EnvioInvalido(Exception):
    """Envio recusado sem expor conteúdo de planilha."""

    def __init__(self, arquivo, motivo):
        self.arquivo = arquivo
        self.motivo = motivo
        super().__init__(f"{arquivo}: {motivo}")


def nome_seguro(nome):
    """Mantém somente o nome de exibição, sem diretórios do navegador."""
    return (nome or "").replace("\\", "/").rsplit("/", 1)[-1]


def _ler_pasta(arquivos, tipo, nome_pasta):
    csvs = [(nome_seguro(arquivo.filename), arquivo) for arquivo in arquivos if nome_seguro(arquivo.filename).lower().endswith(".csv")]
    if not csvs:
        raise EnvioInvalido(nome_pasta, "pasta_vazia")

    lidos = []
    for nome, arquivo in csvs:
        try:
            lidos.append((nome, ler_planilha(arquivo.read(), tipo)))
        except ValueError as exc:
            motivo = str(exc)
            if motivo in {"colunas_ausentes", "leitura_csv"}:
                raise EnvioInvalido(nome, motivo) from None
            raise
    return lidos


def ler_pastas(arquivos_ciclo, arquivos_matricula):
    """Lê os dois conjuntos de arquivos ou recusa o primeiro CSV inválido.

    UPL-06: encerra cada `FileStorage` no fim (inclusive nos arquivos
    ignorados e no caminho de recusa) — é o que apaga o buffer temporário que
    o parser criou para um envio grande, sem esperar o coletor de lixo.
    """
    arquivos_ciclo = list(arquivos_ciclo)
    arquivos_matricula = list(arquivos_matricula)
    try:
        ignorados = [nome_seguro(a.filename) for a in arquivos_ciclo + arquivos_matricula if not nome_seguro(a.filename).lower().endswith(".csv")]
        ciclo = _ler_pasta(arquivos_ciclo, "ciclo", "ciclos")
        matricula = _ler_pasta(arquivos_matricula, "matricula", "matrículas")
        return {"ciclo": ciclo, "matricula": matricula, "ignorados": ignorados}
    finally:
        for arquivo in arquivos_ciclo + arquivos_matricula:
            arquivo.close()


def _codigos_ciclo(df_ciclos):
    """Códigos de unidades com ciclos válidos, preservando a ordem de entrada."""
    if df_ciclos.empty or "CO_UNIDADE" not in df_ciclos:
        return []
    ciclos = df_ciclos
    if "SITUACAO_CICLO" in ciclos:
        ciclos = ciclos.loc[ciclos["SITUACAO_CICLO"] != "EXCLUÍDO"]
    return list(dict.fromkeys(str(codigo).strip() for codigo in ciclos["CO_UNIDADE"] if pd.notna(codigo) and str(codigo).strip()))


def _codigos_cadastrados(campi_cadastrados):
    """Códigos configurados nos campi, na ordem estável da lista."""
    return list(
        dict.fromkeys(
            str(campus.get("co_unidade") or "").strip()
            for campus in campi_cadastrados
            if str(campus.get("co_unidade") or "").strip()
        )
    )


def campi_ausentes(df_ciclos, campi_cadastrados):
    """Códigos cadastrados sem ciclo válido no envio."""
    presentes = set(_codigos_ciclo(df_ciclos))
    return [codigo for codigo in _codigos_cadastrados(campi_cadastrados) if codigo not in presentes]


def campi_nao_cadastrados(df_ciclos, campi_cadastrados):
    """Códigos de ciclos válidos ainda ausentes da lista de campi."""
    cadastrados = set(_codigos_cadastrados(campi_cadastrados))
    return [codigo for codigo in _codigos_ciclo(df_ciclos) if codigo not in cadastrados]
