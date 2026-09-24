"""Testes de `scripts/testar.ps1`, o ambiente de teste.

WDG-03: o app sobe por `run.py`, não por um `app.run` avulso — é o que faz o
watchdog de execuções rodar também no ambiente de teste.

AMB-01: `-Destacado` sobe o app em processo separado, com log no diretório
temporário, e devolve o controle; `-Parar` derruba quem está na porta. Os testes
de integração usam sempre porta livre e `-Porta` explícito: nunca chegam perto
da 8050, onde pode haver um ambiente de teste em uso.
"""

import glob
import os
import re
import socket
import subprocess
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(RAIZ, "scripts", "testar.ps1")
TEMPORARIO = os.environ.get("TEMP", "")

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="testar.ps1 é PowerShell, só roda no Windows"
)


def ler_script():
    with open(SCRIPT, encoding="utf-8") as arquivo:
        return arquivo.read()


def test_script_sobe_o_app_por_run_py_na_porta_pedida():
    assert "run.py --host 127.0.0.1 --port $Porta" in ler_script()


def test_script_nao_chama_app_run_direto():
    assert "app.run(" not in ler_script()


PADRAO_LIMITE = re.compile(r"(?m)^\s*\$limite\s*=\s*(\S.*?)\s*$")


def test_limite_padrao_do_destacado_e_60_segundos():
    """AMB-01 AC1: "esperar a porta aceitar conexão por no máximo 60 s".

    O único outro caminho é o escape `CALCSISTEC_TESTAR_TIMEOUT`, que só
    encurta a espera de um teste — nenhum outro literal pode virar o padrão.
    """
    atribuicoes = PADRAO_LIMITE.findall(ler_script())

    assert atribuicoes, "$limite não é atribuído em testar.ps1"
    assert atribuicoes[0] == "60", atribuicoes
    assert [valor for valor in atribuicoes if valor.isdigit()] == ["60"], atribuicoes
    assert atribuicoes[1] == "$limitePedido", atribuicoes


def ler_env(caminho=None):
    """`{chave: valor}` do `.env`, sem comentários e sem linhas vazias."""
    valores = {}
    with open(caminho or os.path.join(RAIZ, ".env"), encoding="utf-8") as arquivo:
        for linha in arquivo:
            if not linha.strip() or linha.strip().startswith("#"):
                continue
            chave, _separador, valor = linha.partition("=")
            valores[chave.strip()] = valor.strip()
    return valores


# --- integração: processo real ----------------------------------------------


def porta_livre():
    """Porta que ninguém está escutando (quem escolhe é o sistema)."""
    with socket.socket() as sonda:
        sonda.bind(("127.0.0.1", 0))
        return sonda.getsockname()[1]


def porta_reservada_sem_escuta():
    """Porta presa por um socket exclusivo que não escuta.

    O Windows recusa um segundo `bind` nessa porta (SO_EXCLUSIVEADDRUSE), então
    o app não consegue subir — é o caso que força o timeout do `-Destacado`.
    Como o socket não está em `Listen`, a conferência de porta livre do script
    passa por ele sem reclamar.
    """
    sonda = socket.socket()
    sonda.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    sonda.bind(("127.0.0.1", 0))
    return sonda, sonda.getsockname()[1]


def escutando(porta):
    """Alguém aceita conexão nessa porta?"""
    with socket.socket() as sonda:
        sonda.settimeout(1)
        return sonda.connect_ex(("127.0.0.1", porta)) == 0


def rodar_script(*argumentos, timeout=180, ambiente=None):
    """Roda o script e devolve o resultado com a saída já decodificada.

    A saída vai para arquivo, nunca para um pipe: o app que o `-Destacado` deixa
    no ar herda os handles do processo que o subiu, e um pipe herdado nunca
    chega a EOF — o teste ficaria preso esperando. O arquivo é escrito pelo
    host do PowerShell na página de código do console, daí o `cp850`.
    """
    env = dict(os.environ)
    env.pop("CALCSISTEC_TESTAR_TIMEOUT", None)
    if ambiente:
        env.update(ambiente)
    arquivo = os.path.join(TEMPORARIO, f"calcsistec-teste-{uuid4().hex}.txt")
    try:
        with open(arquivo, "wb") as saida:
            processo = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    SCRIPT,
                    *argumentos,
                ],
                cwd=RAIZ,
                stdout=saida,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                env=env,
            )
        with open(arquivo, "rb") as saida:
            texto = saida.read().decode("cp850", errors="replace")
    finally:
        apagar(arquivo)
    return subprocess.CompletedProcess(processo.args, processo.returncode, texto, "")


def apagar(caminho):
    try:
        os.remove(caminho)
    except OSError:
        pass


def derrubar(porta):
    """`-Parar` na porta dada; nunca falha o teste por si."""
    try:
        rodar_script("-Parar", "-Porta", str(porta), timeout=60)
    except (subprocess.SubprocessError, OSError):
        pass


def apagar_logs(porta):
    """Limpa os logs do app e os arquivos de saída deste teste no `%TEMP%`.

    O app em execução segura o arquivo de saída que ele herdou, então a limpeza
    só funciona depois de `derrubar`.
    """
    alvos = [
        os.path.join(TEMPORARIO, f"calcsistec-{porta}{sufixo}.log") for sufixo in ("", ".err")
    ]
    alvos += [
        os.path.join(TEMPORARIO, f"calcsistec-simulado-8051{sufixo}.log")
        for sufixo in ("", ".err")
    ]
    alvos += glob.glob(os.path.join(TEMPORARIO, "calcsistec-teste-*.txt"))
    for alvo in alvos:
        apagar(alvo)


def test_destacado_sobe_o_app_e_parar_derruba():
    """AMB-01 AC1, AC2 e AC5: `-Destacado` volta com a porta no ar, imprimindo a
    URL de login e as credenciais do `.env`, citando o log fora do repositório; e
    `-Parar` libera a porta."""
    porta = porta_livre()
    try:
        subida = rodar_script("-Destacado", "-SemNavegador", "-Porta", str(porta))

        assert subida.returncode == 0, subida.stdout + subida.stderr
        assert escutando(porta), "o app não ficou escutando depois de -Destacado"

        linha_log = next(
            (linha for linha in subida.stdout.splitlines() if "calcsistec-" in linha), ""
        )
        assert os.path.join(TEMPORARIO, f"calcsistec-{porta}.log") in subida.stdout
        assert RAIZ not in linha_log, f"log dentro do repositorio: {linha_log}"

        assert f"http://localhost:{porta}/admin/login" in subida.stdout, subida.stdout
        credenciais = ler_env()
        assert credenciais["ADMIN_EMAIL"] in subida.stdout, subida.stdout
        assert credenciais["ADMIN_SENHA"] in subida.stdout, subida.stdout
        assert "PID" in subida.stdout

        parada = rodar_script("-Parar", "-Porta", str(porta))

        assert parada.returncode == 0, parada.stdout + parada.stderr
        assert not escutando(porta), "a porta continuou escutando depois de -Parar"
    finally:
        derrubar(porta)
        apagar_logs(porta)


def test_porta_ocupada_sai_1_sem_subir_outro_processo():
    """AMB-01 AC4: porta ocupada aborta citando o PID de quem a ocupa."""
    with socket.socket() as ocupa:
        ocupa.bind(("127.0.0.1", 0))
        ocupa.listen(1)
        porta = ocupa.getsockname()[1]

        saida = rodar_script("-Destacado", "-SemNavegador", "-Porta", str(porta))

        assert saida.returncode == 1, saida.stdout + saida.stderr
        assert str(os.getpid()) in saida.stdout, saida.stdout
        assert escutando(porta), "o script não pode derrubar quem já estava na porta"

    assert not os.path.exists(os.path.join(TEMPORARIO, f"calcsistec-{porta}.log"))


def test_timeout_encerra_o_app_e_sai_1():
    """AMB-01 AC3: sem a porta abrir, o script encerra o que subiu e sai com 1.

    `CALCSISTEC_TESTAR_TIMEOUT` só encurta a espera deste teste; sem ela o script
    continua esperando os 60 s de sempre.
    """
    sonda, porta = porta_reservada_sem_escuta()
    try:
        saida = rodar_script(
            "-Destacado",
            "-SemNavegador",
            "-Porta",
            str(porta),
            ambiente={"CALCSISTEC_TESTAR_TIMEOUT": "5"},
        )

        assert saida.returncode == 1, saida.stdout + saida.stderr
        assert f"calcsistec-{porta}.log" in saida.stdout, saida.stdout
        assert not escutando(porta)
    finally:
        sonda.close()
        derrubar(porta)
        apagar_logs(porta)


def test_parar_sem_nada_no_ar_sai_0():
    """AMB-01 AC5: parar o que não está no ar não é erro."""
    porta = porta_livre()

    saida = rodar_script("-Parar", "-Porta", str(porta))

    assert saida.returncode == 0, saida.stdout + saida.stderr
    assert "nada no ar" in saida.stdout.lower()
