"""Orquestração em memória de execuções de baixa e captura de perfis
(`002-baixador-planilhas-sistec`, T039, T040, T042, D-02, D-03, roadmap §5.1).

Um registro por `admin_email` (RN-11: uma execução não terminal por vez),
guardado num `dict` protegido por `threading.Lock`. A extensão é um
executor sem estado: pede o próximo par (`proximo`), baixa e reporta
(`receber_bytes`/`reportar_falha`). Uma thread de varredura (`iniciar_
varredura`) encerra pausas com mais de 4 h e falha pares parados há mais de
900 s + 60 s sem resposta (watchdog).

O relógio é injetável (`relogio`, um `callable` sem argumento devolvendo
`datetime`) para os testes de tempo (T023) não dependerem de `sleep` real.
"""

import secrets
import threading
from datetime import datetime, timedelta

from app.sistec.urls import TEMPO_MAX_EXPORTACAO_S, par_para_extensao

TEMPO_MAX_PAUSA_S = 4 * 60 * 60
MARGEM_WATCHDOG_S = 60
INTERVALO_VARREDURA_S = 60

ESTADOS_TERMINAIS = {
    "salva",
    "descartada",
    "cancelada",
    "falhou_consolidacao",
    "encerrada_pausa",
    "interrompida",
    "sem_resultado",
    "falhou",
}


class ExecucaoInvalida(Exception):
    """Token inválido, execução inexistente, ou ação fora do estado atual."""


class ConfirmacaoNecessaria(Exception):
    """O envio preserva campi e exige confirmação explícita para salvar."""


class PreviaIndisponivel(Exception):
    """Prévia não disponível para o contexto: execução inexistente, sessão
    alheia, origem diferente de `envio` ou estado diferente de `previa`
    (`previa-paginas-publicas`, PVP-07). Distinta de `ExecucaoInvalida`."""



class Par:
    def __init__(self, n, tipo, id_perfil, nome_perfil, co_unidade=None):
        self.n = n
        self.tipo = tipo  # "ciclo" | "matricula"
        self.id_perfil = id_perfil
        self.nome_perfil = nome_perfil
        self.co_unidade = co_unidade
        self.status = "pendente"  # pendente|em_andamento|baixado|falhou|cancelado
        self.motivo = None
        self.linhas = None
        self.assinatura_cabecalho = None
        self.df = None
        self.iniciado_em = None


class Execucao:
    def __init__(self, execucao_id, admin_email, campi, qtd_perfis, historico_id, relogio, origem="baixa", sessao_dona=None):
        self.id = execucao_id
        self.admin_email = admin_email
        self.token = secrets.token_urlsafe(32)
        self.estado = "aguardando_login"
        self.qtd_perfis = qtd_perfis
        self.historico_id = historico_id
        self.origem = origem
        self.relogio = relogio
        self.pausas = 0
        self.pausada_desde = None
        self.criada_em = relogio()

        self.fila = []
        n = 1
        for campus in campi:
            self.fila.append(Par(n, "ciclo", campus["id_perfil"], campus["nome_perfil"], campus.get("co_unidade")))
            n += 1
        for campus in campi:
            self.fila.append(Par(n, "matricula", campus["id_perfil"], campus["nome_perfil"], campus.get("co_unidade")))
            n += 1

        self.previa = None
        self.campi_falhos = set()
        self.sessao_dona = sessao_dona

    def par_por_n(self, n):
        for par in self.fila:
            if par.n == n:
                return par
        return None

    def par_em_andamento(self):
        for par in self.fila:
            if par.status == "em_andamento":
                return par
        return None

    def proximo_pendente(self):
        for par in self.fila:
            if par.status == "pendente":
                return par
        return None


class Captura:
    """Máquina de estados de captura de perfis (roadmap §5.1): aguardando_
    login -> lendo_perfis -> revisao -> salva | cancelada; ou 0 perfis/erro
    -> sem_resultado | falhou."""

    def __init__(self, captura_id, admin_email, relogio):
        self.id = captura_id
        self.admin_email = admin_email
        self.token = secrets.token_urlsafe(32)
        self.estado = "aguardando_login"
        self.relogio = relogio
        self.criada_em = relogio()
        self.perfis = None
        self.motivo_falha = None


_REGISTRO = {}
_REGISTRO_CAPTURAS = {}
_LOCK = threading.Lock()
_VARREDURA_THREAD = None
_VARREDURA_PARAR = threading.Event()


def _relogio_padrao():
    return datetime.now()


def criar_execucao(admin_email, campi, historico_id=None, relogio=None):
    """RN-11: 409 (via `ExecucaoInvalida`) se o administrador já tem uma
    execução não terminal. `campi`: lista de dicts `{id_perfil, nome_perfil}`
    dos perfis com `co_unidade` preenchido, na ordem da fila (RN-06)."""
    relogio = relogio or _relogio_padrao
    with _LOCK:
        atual = _REGISTRO.get(admin_email)
        if atual is not None and atual.estado not in ESTADOS_TERMINAIS:
            raise ExecucaoInvalida("já existe uma execução em andamento para este administrador")

        execucao_id = secrets.token_urlsafe(16)
        execucao = Execucao(execucao_id, admin_email, campi, len(campi), historico_id, relogio)
        _REGISTRO[admin_email] = execucao
        return execucao


def criar_execucao_envio(admin_email, nomes_ciclo, nomes_matricula, historico_id=None, relogio=None, sessao_id=None):
    """Cria uma execução cuja fila é composta pelos arquivos enviados. Vincula
    a execução à `sessao_id` que a iniciou (PVP-07, `previa-paginas-publicas`)."""
    relogio = relogio or _relogio_padrao
    with _LOCK:
        atual = _REGISTRO.get(admin_email)
        if atual is not None and atual.estado not in ESTADOS_TERMINAIS:
            raise ExecucaoInvalida("já existe uma execução em andamento para este administrador")

        execucao = Execucao(secrets.token_urlsafe(16), admin_email, [], 0, historico_id, relogio, origem="envio", sessao_dona=sessao_id)
        execucao.estado = "consolidando"
        nomes = [("ciclo", nome) for nome in nomes_ciclo] + [("matricula", nome) for nome in nomes_matricula]
        execucao.fila = [Par(n, tipo, None, nome) for n, (tipo, nome) in enumerate(nomes, start=1)]
        _REGISTRO[admin_email] = execucao
        return execucao


def registrar_leitura(execucao, leitura):
    """Preenche a fila de um envio e consolida os DataFrames recebidos."""
    for tipo in ("ciclo", "matricula"):
        pares = [par for par in execucao.fila if par.tipo == tipo]
        for par, (_nome, df) in zip(pares, leitura[tipo], strict=True):
            par.df = df
            par.linhas = len(df)
            par.assinatura_cabecalho = tuple(sorted(df.columns))
            par.status = "baixado"
    _consolidar_ou_falhar(execucao)


def definir_campi_preservados(execucao, codigos):
    """Registra os campi ausentes cujas linhas internas devem ser mantidas."""
    execucao.campi_falhos = set(codigos)


def obter_por_token(execucao_id, token):
    for execucao in _REGISTRO.values():
        if execucao.id == execucao_id:
            if not secrets.compare_digest(execucao.token, token):
                raise ExecucaoInvalida("token não autorizado para esta execução")
            return execucao
    raise ExecucaoInvalida("execução não encontrada")


def obter_do_admin(admin_email):
    return _REGISTRO.get(admin_email)


def obter_previa(execucao_id, sessao_id):
    """PVP-07 (`previa-paginas-publicas`): devolve a execução de envio em
    estado `previa` apenas para a sessão dona. Qualquer outra combinação —
    execução inexistente, sessão alheia (inclusive outra sessão do mesmo
    e-mail), origem diferente de `envio` ou estado diferente de `previa` —
    levanta `PreviaIndisponivel`. A recusa nunca devolve nem abre a fonte
    candidata nem recai no banco publicado."""
    for execucao in _REGISTRO.values():
        if execucao.id == execucao_id:
            if (
                execucao.origem != "envio"
                or execucao.estado != "previa"
                or not secrets.compare_digest(execucao.sessao_dona or "", sessao_id or "")
            ):
                raise PreviaIndisponivel("prévia indisponível para esta sessão")
            return execucao
    raise PreviaIndisponivel("prévia indisponível: execução não encontrada")


def iniciar_baixa(execucao):
    """RF-10 dispara "Baixar": só a partir de `aguardando_login`."""
    if execucao.estado != "aguardando_login":
        raise ExecucaoInvalida(f"não é possível iniciar a baixa a partir do estado '{execucao.estado}'")
    execucao.estado = "baixando"


def retomar(execucao):
    if execucao.estado != "pausada":
        raise ExecucaoInvalida(f"não é possível retomar a partir do estado '{execucao.estado}'")
    execucao.estado = "baixando"
    execucao.pausada_desde = None


def cancelar(execucao):
    if execucao.estado in ESTADOS_TERMINAIS:
        raise ExecucaoInvalida(f"execução já está em estado terminal '{execucao.estado}'")
    execucao.estado = "cancelada"


def proximo(execucao):
    """§4.1: idempotente — repetir sem reportar devolve o mesmo par em
    andamento. Devolve um dict pronto para a resposta HTTP."""
    if execucao.estado in ("aguardando_login", "pausada"):
        return {"acao": "aguardar"}

    if execucao.estado != "baixando":
        return {"acao": "encerrar"}

    par = execucao.par_em_andamento()
    if par is None:
        par = execucao.proximo_pendente()
        if par is None:
            _consolidar_ou_falhar(execucao)
            return {"acao": "encerrar"}
        par.status = "em_andamento"
        par.iniciado_em = execucao.relogio()

    payload = par_para_extensao(par.n, len(execucao.fila), par.tipo, par.id_perfil, par.nome_perfil, execucao.qtd_perfis)
    return {"acao": "baixar", "par": payload}


def receber_bytes(execucao, n, conteudo_bytes):
    """§4.2. `204` (None) se aceito; levanta `ValueError` com um código curto
    (`par_inesperado`/`colunas_ausentes`/`leitura_csv`) para o chamador HTTP
    traduzir em status (D-03: bytes nunca persistidos, descartados após a
    leitura; erro nunca ecoa o conteúdo, RN-13)."""
    par = execucao.par_em_andamento()
    if par is None or par.n != n:
        raise ValueError("par_inesperado")

    from app.sistec.colunas import ler_planilha

    par.df = ler_planilha(conteudo_bytes, par.tipo)
    par.assinatura_cabecalho = tuple(sorted(par.df.columns))
    par.linhas = len(par.df)
    par.status = "baixado"
    par.motivo = None


def reportar_falha(execucao, n, motivo):
    """§4.3. `sessao_expirada`/`aba_fechada` pausam a execução (o par volta a
    `pendente`); os demais motivos falham só o par, e a fila segue."""
    motivos_validos = {"tempo_esgotado", "erro_http", "resposta_invalida", "sessao_expirada", "aba_fechada"}
    if motivo not in motivos_validos:
        raise ValueError(f"motivo desconhecido: {motivo!r}")

    par = execucao.par_em_andamento()
    if par is None or par.n != n:
        raise ExecucaoInvalida("par_inesperado")

    if motivo in ("sessao_expirada", "aba_fechada"):
        par.status = "pendente"
        par.iniciado_em = None
        execucao.estado = "pausada"
        execucao.pausada_desde = execucao.relogio()
        execucao.pausas += 1
    else:
        par.status = "falhou"
        par.motivo = motivo
        if par.tipo in ("ciclo", "matricula"):
            execucao.campi_falhos.add(par.co_unidade or par.id_perfil)


def definir_co_unidade(execucao, id_perfil, co_unidade):
    """Código da unidade descoberto durante a baixa (planilha de ciclos de um
    campus sem código salvo): vale para os pares desse perfil, para que
    `campi_falhos` use o código (comparado com `CO_UNIDADE` em
    `app/data/ingest.montar_versao_interna`)."""
    for par in execucao.fila:
        if par.id_perfil == id_perfil:
            par.co_unidade = co_unidade


def _consolidar_ou_falhar(execucao):
    """Fila vazia: consolida os pares baixados. Erro de consolidação vai
    para `falhou_consolidacao`; sucesso vai para `previa` (RF-08)."""
    from app.sistec.consolidacao import ConsolidacaoInvalida, consolidar

    execucao.estado = "consolidando"
    pares_ciclo = [p.df for p in execucao.fila if p.tipo == "ciclo" and p.status == "baixado"]
    pares_matricula = [p.df for p in execucao.fila if p.tipo == "matricula" and p.status == "baixado"]

    try:
        execucao.previa = consolidar(pares_ciclo, pares_matricula)
        execucao.estado = "previa"
    except ConsolidacaoInvalida as exc:
        execucao.estado = "falhou_consolidacao"
        execucao.erro_consolidacao = str(exc)


def salvar(execucao, db_path, ano_base, confirmado=False):
    """Estado `previa` -> Salvar (RF-08): grava a versão interna e marca
    `salva`."""
    if execucao.estado != "previa":
        raise ExecucaoInvalida(f"não é possível salvar a partir do estado '{execucao.estado}'")
    if execucao.origem == "envio" and execucao.campi_falhos and not confirmado:
        raise ConfirmacaoNecessaria("confirmação necessária para preservar campi ausentes")

    from app.data.ingest import montar_versao_interna

    resultado = montar_versao_interna(execucao.previa, execucao.campi_falhos, db_path=db_path, ano_base=ano_base)
    execucao.estado = "salva"
    return resultado


def descartar(execucao):
    if execucao.estado != "previa":
        raise ExecucaoInvalida(f"não é possível descartar a partir do estado '{execucao.estado}'")
    execucao.estado = "descartada"


def varrer(execucao, agora=None):
    """Thread de varredura (a cada 60 s): encerra pausa com mais de 4 h e
    falha (tempo esgotado) o par em andamento há mais de 900 s + 60 s sem
    resposta."""
    agora = agora or execucao.relogio()

    if execucao.estado == "pausada" and execucao.pausada_desde is not None:
        if agora - execucao.pausada_desde > timedelta(seconds=TEMPO_MAX_PAUSA_S):
            execucao.estado = "encerrada_pausa"
            return

    par = execucao.par_em_andamento()
    if par is not None and par.iniciado_em is not None:
        limite = timedelta(seconds=TEMPO_MAX_EXPORTACAO_S + MARGEM_WATCHDOG_S)
        if agora - par.iniciado_em > limite:
            par.status = "falhou"
            par.motivo = "tempo_esgotado"
            execucao.campi_falhos.add(par.co_unidade or par.id_perfil)


def iniciar_varredura(intervalo_s=INTERVALO_VARREDURA_S):
    """Inicia a thread de varredura de produção (relógio real). Idempotente:
    chamar mais de uma vez não cria threads duplicadas."""
    global _VARREDURA_THREAD
    if _VARREDURA_THREAD is not None and _VARREDURA_THREAD.is_alive():
        return

    _VARREDURA_PARAR.clear()

    def _loop():
        while not _VARREDURA_PARAR.wait(intervalo_s):
            with _LOCK:
                execucoes = list(_REGISTRO.values())
            for execucao in execucoes:
                if execucao.estado not in ESTADOS_TERMINAIS:
                    varrer(execucao)

    _VARREDURA_THREAD = threading.Thread(target=_loop, daemon=True)
    _VARREDURA_THREAD.start()


def parar_varredura():
    _VARREDURA_PARAR.set()


# ===================== Captura de perfis (roadmap §5.1) =====================


def criar_captura(admin_email, relogio=None):
    """RN-11 também vale para captura-vs-baixa: bloqueia se o administrador
    tem uma execução de baixa em andamento (mesmo registro `_REGISTRO`).

    RN-05 (clarify 2026-09-15, Q2): ao contrário da baixa, uma captura
    anterior do mesmo administrador presa em estado não terminal (ex.:
    `aguardando_login` sem conclusão) não bloqueia uma nova — é descartada
    automaticamente (`cancelada`), sem exigir cancelamento manual antes."""
    relogio = relogio or _relogio_padrao
    with _LOCK:
        atual = _REGISTRO.get(admin_email)
        if atual is not None and atual.estado not in ESTADOS_TERMINAIS:
            raise ExecucaoInvalida("já existe uma execução de baixa em andamento para este administrador")

        for captura_presa in _REGISTRO_CAPTURAS.values():
            if captura_presa.admin_email == admin_email and captura_presa.estado not in ESTADOS_TERMINAIS | {"cancelada"}:
                captura_presa.estado = "cancelada"

        captura_id = secrets.token_urlsafe(16)
        captura = Captura(captura_id, admin_email, relogio)
        _REGISTRO_CAPTURAS[captura_id] = captura
        return captura


def obter_captura_do_admin(admin_email):
    for captura in _REGISTRO_CAPTURAS.values():
        if captura.admin_email == admin_email and captura.estado not in ESTADOS_TERMINAIS | {"cancelada"}:
            return captura
    return None


def obter_ultima_captura_do_admin(admin_email):
    """Para o polling de status (`/admin/config/captura`): ao contrário de
    `obter_captura_do_admin`, não filtra estados terminais — sem isso, uma
    falha (`falhou`/`sem_resultado`) some do polling antes da tela conseguir
    mostrá-la ao administrador."""
    capturas = [c for c in _REGISTRO_CAPTURAS.values() if c.admin_email == admin_email]
    if not capturas:
        return None
    return max(capturas, key=lambda c: c.criada_em)


def obter_captura_por_token(captura_id, token):
    captura = _REGISTRO_CAPTURAS.get(captura_id)
    if captura is None:
        raise ExecucaoInvalida("captura não encontrada")
    if not secrets.compare_digest(captura.token, token):
        raise ExecucaoInvalida("token não autorizado para esta captura")
    return captura


def receber_perfis(captura, perfis):
    """§4.4: `perfis` vazio -> `sem_resultado` (RN-05, lista salva não
    muda). Não vazio -> `revisao`, aguardando "Salvar lista".

    O Sistec real lista um perfil por papel (Assessor/Gestor) para o mesmo
    campus, repetindo o código da unidade (achado 2 da F0: `qtdPerfis` = 2x
    o número de campi) — como `co_unidade` é `UNIQUE` em `campi_sistec`
    (`app/data/campi.py`), mantém só o primeiro perfil de cada código de
    unidade; perfis sem código lido (`co_unidade` vazio) não colidem entre
    si e passam todos."""
    if not perfis:
        captura.estado = "sem_resultado"
        return
    vistos = set()
    deduplicados = []
    for perfil in perfis:
        co_unidade = perfil.get("co_unidade")
        if co_unidade:
            if co_unidade in vistos:
                continue
            vistos.add(co_unidade)
        deduplicados.append(perfil)
    captura.perfis = deduplicados
    captura.estado = "revisao"


def reportar_falha_captura(captura, motivo):
    captura.motivo_falha = motivo
    captura.estado = "falhou" if motivo != "nenhum_perfil" else "sem_resultado"


def cancelar_captura(captura):
    if captura.estado in ESTADOS_TERMINAIS | {"cancelada"}:
        raise ExecucaoInvalida(f"captura já está em estado terminal '{captura.estado}'")
    captura.estado = "cancelada"


def salvar_lista_captura(captura, db_path):
    """"Salvar lista" a partir de `revisao` (RN-05): grava via
    `app/data/campi.salvar_captura`."""
    if captura.estado != "revisao":
        raise ExecucaoInvalida(f"não é possível salvar a lista a partir do estado '{captura.estado}'")

    from app.data.campi import salvar_captura

    perfis_com_ordem = [{**p, "ordem": indice} for indice, p in enumerate(captura.perfis)]
    salvar_captura(perfis_com_ordem, db_path)
    captura.estado = "salva"
