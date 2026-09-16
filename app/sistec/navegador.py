"""Atualização a partir do Sistec pelo navegador da própria pessoa
(`002-baixador-planilhas-sistec`, emendas E003/E004, revistas pela E006).

É a mecânica do script R (`sistec_crawler_ifrs_versaoIFFar.R`): quem tem a
sessão é o **navegador de sempre**, com o login gov.br que a pessoa acabou de
fazer. O CalcSISTEC só manda abrir as URLs (troca de campus e exportação) e
vigia a pasta onde o arquivo cai (`app/sistec/downloads.py`), lendo e apagando
cada CSV assim que chega.

**Por que não há mais o modo janela.** Até a E003 o caminho preferido era abrir
o Chrome/Edge instalado e conectar o Playwright por CDP. O gov.br identifica o
navegador sob controle automático e recusa o login — a premissa P-16 do
roadmap, nunca exercitada até 2026-09-16, caiu na primeira tentativa real. Todo
esse caminho saiu (E006), junto com a dependência `playwright`.

**De onde vem a lista de campi.** Do cadastro manual (Configurações → Campi do
Sistec), não de leitura automática: o identificador de perfil (`tipo`) não
aparece na lista da tela do Sistec — só é preenchido depois que o item é
selecionado —, e as tentativas de lê-lo sozinho (extensão MV3, janela
controlada, marcador de favoritos) não se sustentaram na máquina de quem opera.

Sem identificador válido não adianta baixar: a troca de campus não acontece e
todas as planilhas vêm do mesmo perfil, ou vazias — foi o que aconteceu com a
lista gravada pela extensão antiga, que guardava a posição do item (`"0"`,
`"1"`, …), com o progresso parado em 0%. Por isso `_conferir_lista_de_campi`
recusa a coleta antes de começar, em vez de rodar 22 planilhas para nada.

Tudo o que acontece vira passo na tela (`sessao.passos`) e progresso
(`sessao.progresso`): quem usa é leigo e precisa ver que está funcionando.

A sessão roda numa thread própria; as rotas Flask só leem `status()` e acionam
`confirmar_login()`/`cancelar()` por eventos.
"""

import logging
import threading
import time

from app.data import campi as campi_store
from app.data.config_store import get_qtd_perfis
from app.data.historico import encerrar as historico_encerrar
from app.data.schema import DEFAULT_DB_PATH
from app.sistec import downloads, execucoes, urls

log = logging.getLogger(__name__)

TEMPO_MAX_LOGIN_S = 20 * 60
MAX_PAUSAS = 3

FASES_ATIVAS = {"aguardando_login", "baixando"}

ROTULO_TIPO = {"ciclo": "ciclos", "matricula": "matrículas"}


class Cancelado(Exception):
    pass


class FalhaNavegador(Exception):
    """Mensagem já pronta para a tela."""


class Sessao:
    def __init__(self, admin_email, historico_id, db_path, base):
        self.admin_email = admin_email
        self.historico_id = historico_id
        self.db_path = db_path
        self.base = base.rstrip("/")
        self.fase = "aguardando_login"
        self.mensagem = "Abrindo o Sistec no seu navegador…"
        self.passos = []
        self.progresso = {"feitos": 0, "total": 0}
        self.avisos = []
        self.execucao = None
        self.execucao_id = None
        self.qtd_perfis = None
        self.unidades_baixadas = {}  # id_perfil -> (nome_perfil, co_unidade)
        self.login_confirmado = threading.Event()
        self.parar = threading.Event()
        self.thread = None

    def ativa(self):
        return self.fase in FASES_ATIVAS

    def url(self, url):
        """As URLs de `app/sistec/urls.py` partem de `urls.BASE`; nos testes a
        sessão aponta para o Sistec simulado."""
        if url.startswith(urls.BASE):
            return self.base + url[len(urls.BASE) :]
        return url

    def como_dict(self):
        return {
            "fase": self.fase,
            "mensagem": self.mensagem,
            "passos": list(self.passos),
            "progresso": dict(self.progresso),
            "avisos": list(self.avisos),
            "ativa": self.ativa(),
            "execucao_id": self.execucao_id,
        }


_SESSOES = {}
_LOCK = threading.Lock()


def iniciar(admin_email, historico_id=None, db_path=DEFAULT_DB_PATH, base=None):
    """Roda a atualização numa thread própria. `ExecucaoInvalida` se já há uma
    em andamento para este administrador."""
    with _LOCK:
        atual = _SESSOES.get(admin_email)
        if atual is not None and atual.ativa():
            raise execucoes.ExecucaoInvalida("já existe uma atualização em andamento para este administrador")
        sessao = Sessao(admin_email, historico_id, db_path, base or urls.BASE)
        _SESSOES[admin_email] = sessao

    sessao.thread = threading.Thread(target=_rodar, args=(sessao,), name="calcsistec-navegador", daemon=True)
    sessao.thread.start()
    return sessao


def status(admin_email):
    sessao = _SESSOES.get(admin_email)
    return sessao.como_dict() if sessao is not None else None


def confirmar_login(admin_email):
    sessao = _SESSOES.get(admin_email)
    if sessao is None or sessao.fase != "aguardando_login":
        return False
    sessao.login_confirmado.set()
    return True


def cancelar(admin_email):
    """`True` se havia uma atualização ativa (a thread encerra a execução e o
    histórico assim que o que estava em andamento terminar)."""
    sessao = _SESSOES.get(admin_email)
    if sessao is None or not sessao.ativa():
        return False
    sessao.parar.set()
    _passo(sessao, "Cancelando… (esperando terminar o que já estava em andamento)")
    return True


# ============================== thread da sessão ==============================


def _passo(sessao, texto, tipo="info"):
    """Registra o que está acontecendo, para a tela mostrar passo a passo."""
    sessao.mensagem = texto
    sessao.passos.append({"hora": time.strftime("%H:%M:%S"), "texto": texto, "tipo": tipo})
    del sessao.passos[:-200]
    log.info("[%s] %s", sessao.admin_email, texto)


def _rodar(sessao):
    try:
        _coletar(sessao)
        _concluir(sessao)
    except Cancelado:
        _encerrar(sessao, "cancelada", "Atualização cancelada.", "cancelada")
    except FalhaNavegador as exc:
        _encerrar(sessao, "falhou", str(exc), "falhou")
    except execucoes.ExecucaoInvalida as exc:
        _encerrar(sessao, "falhou", f"Não foi possível iniciar a baixa: {exc}.", "falhou")
    except Exception:  # noqa: BLE001 — qualquer erro precisa virar estado visível na tela
        log.exception("Falha inesperada na atualização")
        _encerrar(sessao, "falhou", "Erro inesperado na atualização (detalhes no terminal do CalcSISTEC).", "falhou")


def _concluir(sessao):
    execucao = sessao.execucao
    if execucao is not None and execucao.estado == "previa":
        sessao.fase = "concluida"
        _passo(
            sessao,
            f"Coleta concluída: {len(execucao.previa['ciclos'])} ciclo(s) e "
            f"{len(execucao.previa['matriculas'])} matrícula(s). Confira a prévia e clique em "
            "“Salvar na versão interna”.",
            "sucesso",
        )
        return
    if execucao is not None and execucao.estado == "falhou_consolidacao":
        sessao.fase = "falhou"
        _passo(
            sessao,
            "As planilhas foram baixadas, mas a consolidação falhou: "
            f"{getattr(execucao, 'erro_consolidacao', 'erro desconhecido')}.",
            "erro",
        )
        _encerrar_historico(sessao, "falhou_consolidacao")
        return
    _encerrar(sessao, "falhou", "A coleta terminou num estado inesperado.", "falhou")


def _encerrar(sessao, fase, mensagem, desfecho):
    execucao = sessao.execucao
    if execucao is not None and execucao.estado not in execucoes.ESTADOS_TERMINAIS:
        execucoes.cancelar(execucao)
    sessao.fase = fase
    _passo(sessao, mensagem, "erro" if fase == "falhou" else "info")
    _encerrar_historico(sessao, desfecho)


def _encerrar_historico(sessao, desfecho):
    if sessao.historico_id:
        historico_encerrar(
            sessao.historico_id,
            desfecho,
            pausas=sessao.execucao.pausas if sessao.execucao is not None else None,
            db_path=sessao.db_path,
        )


def _checar_cancelado(sessao):
    if sessao.parar.is_set():
        raise Cancelado()


def _atualizar_progresso(sessao, execucao):
    sessao.progresso = {
        "feitos": sum(1 for p in execucao.fila if p.status in ("baixado", "falhou")),
        "total": len(execucao.fila),
    }


def _garantir_execucao(sessao):
    """Monta a fila a partir dos campi ativos cadastrados em Configurações."""
    if sessao.execucao is not None:
        return sessao.execucao
    campi = campi_store.listar_campi(sessao.db_path, somente_ativos=True)
    if not campi:
        raise FalhaNavegador(
            "Ainda não tenho a lista de campi deste Sistec. Cadastre os campi em "
            "Configurações → Campi do Sistec e tente de novo."
        )
    execucao = execucoes.criar_execucao(sessao.admin_email, campi, historico_id=sessao.historico_id)
    sessao.execucao = execucao
    sessao.execucao_id = execucao.id
    execucoes.iniciar_baixa(execucao)
    _atualizar_progresso(sessao, execucao)
    return execucao


def _esperar_confirmacao_login(sessao, texto):
    sessao.fase = "aguardando_login"
    _passo(sessao, texto)
    limite = time.monotonic() + TEMPO_MAX_LOGIN_S
    while not sessao.login_confirmado.wait(timeout=1):
        _checar_cancelado(sessao)
        if time.monotonic() > limite:
            raise FalhaNavegador(
                "O tempo para o login (20 minutos) acabou. Clique em “Atualizar do Sistec” para tentar de novo."
            )
    sessao.login_confirmado.clear()


# ============================== conferência da lista ==============================


def _conferir_lista_de_campi(sessao):
    """Recusa a baixa quando algum campus ativo está sem identificador válido.

    O identificador (o campo `tipo` do Sistec) é o que troca o campus ativo. Com
    ele errado — como na lista gravada pela extensão antiga, que guardava a
    posição do item (`"0"`, `"1"`, …) — o Sistec ignora a troca, devolve a tela
    de perfis em HTML e nenhuma planilha chega: a baixa roda as 22 e termina em
    nada. Melhor parar aqui, dizendo o que corrigir."""
    suspeitos = campi_store.campi_suspeitos(sessao.db_path)
    if not suspeitos:
        return

    nomes = ", ".join(f"{c['nome_perfil']} (identificador “{c['id_perfil']}”)" for c in suspeitos[:3])
    if len(suspeitos) > 3:
        nomes += f" e mais {len(suspeitos) - 3}"
    raise FalhaNavegador(
        f"{len(suspeitos)} campus(i) estão sem um identificador de perfil válido: {nomes}. "
        "O identificador é o número de 7 dígitos do campo “tipo” do Sistec, e sem ele a troca de campus não "
        "acontece (as planilhas viriam vazias). Cadastre-os em Configurações → Campi do Sistec e clique em "
        "“Atualizar do Sistec” de novo."
    )


# ============================== coleta ==============================


def _coletar(sessao, abrir=None, pasta=None, pastas_extras=None):
    """Jeito do script R: a pessoa loga no navegador de sempre e o CalcSISTEC
    só manda abrir as URLs, vigiando a pasta de coleta (e a de Downloads, para
    onde o navegador salva se ninguém tiver mudado a configuração dele)."""
    sessao.qtd_perfis = get_qtd_perfis(sessao.db_path) or urls.QTD_PERFIS_PADRAO
    baixador = downloads.Baixador(
        sessao.base,
        pasta=pasta,
        pastas_extras=pastas_extras,
        abrir=abrir,
        qtd_perfis=sessao.qtd_perfis,
    )
    _passo(
        sessao,
        f"Pasta de trabalho: {baixador.pasta}. Cada planilha é lida e apagada assim que chega "
        f"(também vigio {', '.join(str(p) for p in baixador.pastas[1:]) or 'nenhuma outra pasta'}).",
    )
    _passo(sessao, "Abrindo o Sistec no seu navegador de sempre…")
    baixador.abrir_sistec()
    _esperar_confirmacao_login(
        sessao,
        "Faça o login no Sistec na aba que abriu e, quando ele carregar, clique em “Já entrei no Sistec”.",
    )

    _conferir_lista_de_campi(sessao)
    execucao = _garantir_execucao(sessao)
    if execucao.estado == "pausada":
        execucoes.retomar(execucao)

    while True:
        _checar_cancelado(sessao)
        resposta = execucoes.proximo(execucao)
        if resposta["acao"] == "encerrar":
            return
        if resposta["acao"] == "aguardar":
            baixador.abrir_sistec()
            _esperar_confirmacao_login(
                sessao,
                "A sessão do Sistec expirou. Entre de novo na aba que abriu e clique em “Já entrei no Sistec”; "
                "a baixa continua de onde parou.",
            )
            execucoes.retomar(execucao)
            continue

        par = resposta["par"]
        sessao.fase = "baixando"
        _passo(
            sessao,
            f"Pedindo ao navegador {ROTULO_TIPO[par['tipo']]} de {par['nome_perfil']} "
            f"(planilha {par['n']} de {par['total']})…",
        )
        corpo, motivo = baixador.baixar_par(
            par,
            cancelado=sessao.parar.is_set,
            aviso=lambda: _passo(
                sessao,
                "O arquivo ainda não chegou. Se o navegador abriu uma janela perguntando onde salvar, "
                f"escolha a pasta {baixador.pasta} — ou desligue “Perguntar onde salvar cada arquivo” "
                "em chrome://settings/downloads e clique em Cancelar aqui para recomeçar.",
                "aviso",
            ),
        )
        if motivo == "tempo_esgotado" and sessao.parar.is_set():
            raise Cancelado()
        if motivo == "tempo_esgotado":
            _passo(
                sessao,
                "O arquivo não apareceu na pasta de Downloads. Confira se o navegador está perguntando onde salvar "
                "ou pedindo permissão para baixar vários arquivos.",
                "aviso",
            )
        _registrar_par(sessao, execucao, par, corpo, motivo)
        _atualizar_progresso(sessao, execucao)


def _registrar_par(sessao, execucao, par, corpo, motivo):
    """Entrega ao `execucoes` o resultado de um par."""
    n = par["n"]
    _checar_cancelado(sessao)

    if motivo == "sessao_expirada" and execucao.pausas >= MAX_PAUSAS:
        motivo = "resposta_invalida"  # evita laço de login se o Sistec responder HTML sempre
    if motivo:
        execucoes.reportar_falha(execucao, n, motivo)
        _passo(sessao, f"Planilha {n} ({par['nome_perfil']}) não veio: {motivo.replace('_', ' ')}.", "aviso")
        return

    try:
        execucoes.receber_bytes(execucao, n, corpo)
    except ValueError as exc:
        execucoes.reportar_falha(execucao, n, "resposta_invalida")
        execucao.par_por_n(n).motivo = str(exc)  # colunas_ausentes | leitura_csv
        _passo(sessao, f"Planilha {n} ({par['nome_perfil']}) veio fora do formato esperado ({exc}).", "aviso")
        return
    finally:
        corpo = None  # D-03: os bytes crus não ficam referenciados

    linhas = execucao.par_por_n(n).linhas
    _passo(sessao, f"Planilha {n} de {par['total']} lida: {linhas} linha(s) de {par['nome_perfil']}.", "sucesso")

    if par["tipo"] == "ciclo":
        _conferir_unidade(sessao, execucao, execucao.par_por_n(n))


def _conferir_unidade(sessao, execucao, par):
    """Usa o `CÓDIGO UNIDADE DE ENSINO` da planilha de ciclos para preencher o
    código do campus quando está vazio, e avisa quando a planilha não é do
    campus esperado (sinal de que a troca de perfil não funcionou)."""
    df = par.df
    if df is None or "CO_UNIDADE" not in df.columns:
        return
    codigos = sorted({str(c).strip() for c in df["CO_UNIDADE"].dropna() if str(c).strip()})
    if len(codigos) > 1:
        sessao.avisos.append(
            f"A planilha de ciclos de {par.nome_perfil} veio com mais de um código de unidade ({', '.join(codigos)})."
        )
    if len(codigos) != 1:
        return
    codigo = codigos[0]

    for id_perfil, (nome_outro, codigo_outro) in sessao.unidades_baixadas.items():
        if id_perfil != par.id_perfil and codigo_outro == codigo:
            sessao.avisos.append(
                f"As planilhas de {par.nome_perfil} e de {nome_outro} vieram da mesma unidade ({codigo}): "
                "a troca de perfil no Sistec pode não ter funcionado."
            )
    sessao.unidades_baixadas[par.id_perfil] = (par.nome_perfil, codigo)

    if par.co_unidade and par.co_unidade != codigo:
        sessao.avisos.append(
            f"{par.nome_perfil} está com o código {par.co_unidade} em Configurações, mas a planilha veio da "
            f"unidade {codigo}. Confira em Configurações → Campi do Sistec."
        )
    elif not par.co_unidade:
        if campi_store.preencher_unidade(par.id_perfil, codigo, sessao.db_path):
            execucoes.definir_co_unidade(execucao, par.id_perfil, codigo)
        else:
            sessao.avisos.append(
                f"Não preenchi o código {codigo} em {par.nome_perfil}: ele já está em outro campus da lista."
            )
