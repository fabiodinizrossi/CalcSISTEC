"""Modo "pasta de coleta" — a mesma mecânica do script R
(`sistec_crawler_ifrs_versaoIFFar.R`), usada como alternativa quando o modo
da janela controlada não funciona (`app/sistec/navegador.py`).

A pessoa faz o login no **navegador de sempre**, com a sessão dela. O
CalcSISTEC só manda o navegador abrir as URLs (troca de campus e exportação)
e fica vigiando a pasta onde o arquivo vai cair. Assim que ele aparece, é
movido para a pasta de trabalho do CalcSISTEC, lido e **apagado**.

Quem decide onde salvar é o navegador, não o CalcSISTEC. Por isso a vigia
cobre duas pastas: a pasta fixa do programa (criada na instalação,
`%LOCALAPPDATA%\\CalcSISTEC\\coleta` por padrão) e a pasta de Downloads do
usuário. Configurando o navegador para baixar na pasta fixa, o arquivo já
nasce no lugar certo; caindo em Downloads, ele é movido na hora.

Diferença de exposição em relação ao modo da janela (D-03): aqui os CSVs com
CPF passam pelo disco por alguns segundos, exatamente como já acontece hoje
com o script R. As colunas de dado pessoal continuam sendo descartadas na
leitura (`app/sistec/colunas.py`), então nada disso entra no banco nem no que
é enviado adiante.
"""

import logging
import os
import shutil
import time
import webbrowser
from pathlib import Path

from app.sistec import urls

log = logging.getLogger(__name__)

# Nomes com que o Sistec entrega cada exportação (script R: `ciclo-matricula.csv`
# e `sistec.csv`). O Chrome acrescenta " (1)", " (2)"... se o arquivo já existir.
NOMES_ESPERADOS = {"ciclo": "ciclo-matricula", "matricula": "sistec"}

INTERVALO_VARREDURA_S = 0.5
MARGEM_RELOGIO_S = 5
# Quanto tempo esperar antes de avisar que o arquivo não chegou (o navegador
# pode estar com "perguntar onde salvar cada arquivo", esperando a pessoa).
TEMPO_AVISO_SEM_ARQUIVO_S = 60


def pasta_coleta(criar=True):
    """Pasta fixa de trabalho do CalcSISTEC (criada na instalação):
    `CALCSISTEC_PASTA_COLETA`, senão `%LOCALAPPDATA%\\CalcSISTEC\\coleta`
    (no Windows) ou `~/.local/share/calcsistec/coleta`."""
    configurada = os.environ.get("CALCSISTEC_PASTA_COLETA")
    if configurada:
        pasta = Path(configurada)
    elif os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
        pasta = Path(base) / "CalcSISTEC" / "coleta"
    else:
        pasta = Path.home() / ".local" / "share" / "calcsistec" / "coleta"
    if criar:
        pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def pasta_downloads():
    """Pasta de downloads do usuário — vigiada porque é onde o navegador
    salva se ninguém tiver mudado a configuração dele."""
    configurada = os.environ.get("CALCSISTEC_PASTA_DOWNLOADS")
    if configurada:
        return Path(configurada)

    try:
        import winreg

        chave = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chave) as k:
            valor, _tipo = winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}")
        caminho = Path(os.path.expandvars(valor))
        if caminho.is_dir():
            return caminho
    except (ImportError, OSError):
        pass

    return Path.home() / "Downloads"


def abrir_no_navegador(url):
    """Abre a URL no navegador padrão da pessoa — é ele que tem a sessão do
    Sistec (equivalente ao `BROWSE()` do script R)."""
    webbrowser.open(url, new=2, autoraise=False)


def _em_andamento(caminho):
    """Chrome/Edge escrevem `.crdownload`/`.tmp` enquanto baixam."""
    for sufixo in (".crdownload", ".part", ".tmp"):
        if caminho.with_name(caminho.name + sufixo).exists():
            return True
    return caminho.suffix.lower() in (".crdownload", ".part", ".tmp")


def _candidatos(pastas, prefixo, desde):
    achados = []
    for pasta in pastas:
        try:
            arquivos = list(Path(pasta).iterdir())
        except OSError:
            continue
        for arquivo in arquivos:
            nome = arquivo.name.lower()
            if not nome.startswith(prefixo) or not nome.endswith(".csv"):
                continue
            try:
                if arquivo.stat().st_mtime < desde - MARGEM_RELOGIO_S:
                    continue
            except OSError:
                continue
            achados.append(arquivo)
    return sorted(achados, key=lambda a: a.stat().st_mtime, reverse=True)


def esperar_arquivo(pastas, prefixo, desde, tempo_max_s, cancelado=None, aviso=None):
    """Espera um arquivo novo `<prefixo>*.csv` aparecer em alguma das `pastas`
    e terminar de baixar. Devolve o caminho, ou `None` se o tempo acabar (ou
    se `cancelado()`).

    `aviso` é chamado uma vez se nada aparecer em
    `TEMPO_AVISO_SEM_ARQUIVO_S` — normalmente porque o navegador está com
    "perguntar onde salvar cada arquivo" e abriu uma janela esperando a
    pessoa. Sem isso, a espera ficaria muda até o tempo máximo (15 min)."""
    if isinstance(pastas, (str, Path)):
        pastas = [pastas]
    inicio = time.monotonic()
    limite = inicio + tempo_max_s
    tamanho_anterior = {}
    avisado = False
    while time.monotonic() < limite:
        if cancelado is not None and cancelado():
            return None
        if aviso is not None and not avisado and time.monotonic() - inicio > TEMPO_AVISO_SEM_ARQUIVO_S:
            avisado = True
            aviso()
        for arquivo in _candidatos(pastas, prefixo.lower(), desde):
            if _em_andamento(arquivo):
                continue
            try:
                tamanho = arquivo.stat().st_size
            except OSError:
                continue
            # Só entrega quando o tamanho para de crescer entre duas varreduras.
            if tamanho > 0 and tamanho_anterior.get(arquivo) == tamanho:
                return arquivo
            tamanho_anterior[arquivo] = tamanho
        time.sleep(INTERVALO_VARREDURA_S)
    return None


def _caminho_livre(pasta, nome):
    destino = Path(pasta) / nome
    contador = 1
    while destino.exists():
        destino = Path(pasta) / f"{Path(nome).stem}-{contador}{Path(nome).suffix}"
        contador += 1
    return destino


def mover_para(pasta, arquivo):
    """Traz para a pasta de trabalho o que o navegador salvou em outro lugar."""
    arquivo = Path(arquivo)
    if arquivo.parent == Path(pasta):
        return arquivo
    destino = _caminho_livre(pasta, arquivo.name)
    for _tentativa in range(10):
        try:
            shutil.move(str(arquivo), str(destino))
            return destino
        except OSError:
            time.sleep(0.3)
    log.warning("Não consegui mover %s para %s; leio do lugar mesmo.", arquivo, pasta)
    return arquivo


def apagar(caminho):
    """Apaga o CSV baixado (ele tem dado pessoal). O Windows pode segurar o
    arquivo por um instante logo depois do download."""
    for _tentativa in range(10):
        try:
            Path(caminho).unlink()
            return True
        except FileNotFoundError:
            return True
        except OSError:
            time.sleep(0.3)
    log.warning("Não consegui apagar o arquivo baixado: %s", caminho)
    return False


def parece_html(conteudo):
    inicio = conteudo[:64].decode("latin-1", "ignore").lstrip().lower()
    return inicio.startswith("<!doctype") or inicio.startswith("<html")


class Baixador:
    """Baixa um par (campus + planilha) pelo navegador da pessoa.

    `abrir` é injetável para os testes (no lugar do navegador de verdade).
    `pastas_extras` são as outras pastas vigiadas além da de trabalho; por
    padrão, a pasta de Downloads do usuário."""

    def __init__(self, base, pasta=None, pastas_extras=None, abrir=None, qtd_perfis=None, aguardar=None):
        self.base = base.rstrip("/")
        self.pasta = Path(pasta) if pasta else pasta_coleta()
        self.pasta.mkdir(parents=True, exist_ok=True)
        extras = [Path(p) for p in (pastas_extras if pastas_extras is not None else [pasta_downloads()])]
        self.pastas = [self.pasta] + [p for p in extras if p != self.pasta]
        self.abrir = abrir or abrir_no_navegador
        self.qtd_perfis = qtd_perfis
        self.aguardar = aguardar or time.sleep

    def _url(self, url):
        return self.base + url[len(urls.BASE) :] if url.startswith(urls.BASE) else url

    def abrir_sistec(self):
        self.abrir(self.base)

    def trocar_perfil(self, par):
        self.abrir(self._url(urls.url_troca_perfil_get(par["id_perfil"], self.qtd_perfis)))
        self.aguardar(par.get("espera_minima_s", urls.ESPERA_MINIMA_TROCA_PERFIL_S))

    def baixar_par(self, par, cancelado=None, aviso=None):
        """`(conteudo, None)` em caso de sucesso; `(None, motivo)` nos motivos
        conhecidos de `interfaces/sistec-http.md` §4. `aviso` é chamado se o
        arquivo demorar demais a aparecer (ver `esperar_arquivo`)."""
        self.trocar_perfil(par)

        desde = time.time()
        self.abrir(self._url(par["url_exportacao"]))
        caminho = esperar_arquivo(
            self.pastas,
            NOMES_ESPERADOS[par["tipo"]],
            desde,
            par.get("tempo_max_s", urls.TEMPO_MAX_EXPORTACAO_S),
            cancelado,
            aviso,
        )
        if caminho is None:
            return None, "tempo_esgotado"

        caminho = mover_para(self.pasta, caminho)
        try:
            conteudo = caminho.read_bytes()
        except OSError:
            return None, "erro_http"
        finally:
            apagar(caminho)

        if not conteudo:
            return None, "resposta_invalida"
        if parece_html(conteudo):
            return None, "sessao_expirada"
        return conteudo, None
