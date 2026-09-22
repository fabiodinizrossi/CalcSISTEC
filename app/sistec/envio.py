"""Leitura das pastas CSV enviadas na atualização administrativa."""

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
    """Lê os dois conjuntos de arquivos ou recusa o primeiro CSV inválido."""
    arquivos_ciclo = list(arquivos_ciclo)
    arquivos_matricula = list(arquivos_matricula)
    ignorados = [nome_seguro(a.filename) for a in arquivos_ciclo + arquivos_matricula if not nome_seguro(a.filename).lower().endswith(".csv")]
    ciclo = _ler_pasta(arquivos_ciclo, "ciclo", "ciclos")
    matricula = _ler_pasta(arquivos_matricula, "matricula", "matrículas")
    return {"ciclo": ciclo, "matricula": matricula, "ignorados": ignorados}
