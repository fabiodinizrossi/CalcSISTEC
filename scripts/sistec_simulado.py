"""Servidor local que imita o Sistec — feature `002-baixador-planilhas-sistec`,
ações T014/T062 de `actions.md`.

Cobre a interface descrita em `interfaces/sistec-http.md` §2, já com as
correções da F0 (`f0-resultado.md`), e o caminho usado pelo navegador
controlado pelo CalcSISTEC (`app/sistec/navegador.py`):

- login fake com cookie de sessão (sem login, as exportações devolvem a
  página de login em HTML, como numa sessão expirada);
- tela de perfis sem `<select>`: itens `<div>` sem classe, renderizados por JS
  depois do carregamento, com o id do perfil só no campo oculto `tipo`
  depois do clique (achado 3 da F0), e um perfil por papel (Assessor/Gestor,
  achado 2);
- troca de perfil por `POST /index/index` (achado 1), guardada em cookie;
- planilhas CSV `;` cp1252 com dados sintéticos do campus ativo (sem dados
  pessoais reais).

Endpoints simulados:
    GET  /                                             -> página de login fake
    POST /entrar                                       -> "loga" e redireciona para a tela de perfis
    GET  /index/selecionarinstituicao/alterar/perfil   -> tela de perfis
    POST /index/index                                  -> troca de perfil (corpo: tipo/acao/qtdPerfis)
    GET  /gridciclo/exportar-ciclo-turmas/              -> planilha de ciclo do perfil ativo
    GET  /aluno/gerar-csv/                              -> planilha de matrícula do perfil ativo

Parâmetros de simulação (variáveis de ambiente, só para teste):
    SISTEC_SIM_PORTA            porta (padrão 8051)
    SISTEC_SIM_ATRASO_S         atraso artificial antes de responder (padrão 0)
    SISTEC_SIM_SESSAO_EXPIRA    se "1", toda resposta simula sessão expirada
    SISTEC_SIM_LOGIN_AUTOMATICO se "1", a página de login entra sozinha

Uso: `python scripts/sistec_simulado.py` e, no CalcSISTEC,
`CALCSISTEC_SISTEC_BASE_URL=http://127.0.0.1:8051`.
"""

import json
import os
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORTA = int(os.environ.get("SISTEC_SIM_PORTA", "8051"))
ATRASO_S = float(os.environ.get("SISTEC_SIM_ATRASO_S", "0"))
SESSAO_EXPIRA = os.environ.get("SISTEC_SIM_SESSAO_EXPIRA") == "1"
LOGIN_AUTOMATICO = os.environ.get("SISTEC_SIM_LOGIN_AUTOMATICO") == "1"

CAMINHO_PERFIS = "/index/selecionarinstituicao/alterar/perfil"

PERFIS = [
    {"id": "8278857", "co_unidade": "101", "texto": "ASSESSOR DA UNIDADE DE ENSINO - 101 - IFFAR - CAMPUS ALEGRETE"},
    {"id": "8278870", "co_unidade": "101", "texto": "GESTOR DA UNIDADE DE ENSINO - 101 - IFFAR - CAMPUS ALEGRETE"},
    {
        "id": "8278858",
        "co_unidade": "102",
        "texto": "ASSESSOR DA UNIDADE DE ENSINO - INSTITUTO FEDERAL FARROUPILHA - CÂMPUS JÚLIO DE CASTILHOS",
    },
    {
        "id": "8278871",
        "co_unidade": "102",
        "texto": "GESTOR DA UNIDADE DE ENSINO - INSTITUTO FEDERAL FARROUPILHA - CÂMPUS JÚLIO DE CASTILHOS",
    },
]
UNIDADE_POR_PERFIL = {p["id"]: p["co_unidade"] for p in PERFIS}

CABECALHO_CICLO = (
    "CÓDIGO CICLO DE MATRÍCULA;CÓDIGO UNIDADE DE ENSINO;CÓDIGO DO PORTFÓLIO;"
    "NOME DO CURSO;SUBTIPO CURSOS;CARGA HORÁRIA TOTAL;MODALIDADE ENSINO;"
    "TIPO OFERTA DO CURSO;EIXO TECNOLÓGICO;TIPO PROGRAMA DO CURSO;"
    "DATA INÍCIO DO CURSO;DATA FIM PREVISTO DO CURSO;"
    "STATUS DO CICLO DE MATRÍCULA;SITUAÇÃO DO CICLO ;NOME_RESPONSAVEL;CPF\r\n"
)
CABECALHO_MATRICULA = "CO_MATRICULA;CO_CICLO_MATRICULA;NO_STATUS_MATRICULA;MES_DE_OCORRENCIA\r\n"


def linha_ciclo(co_unidade):
    return (
        f"{co_unidade}01;{co_unidade};{co_unidade}9;TÉCNICO EM INFORMÁTICA;TÉCNICO;800;PRESENCIAL;INTEGRADO;"
        "INFORMAÇÃO E COMUNICAÇÃO;PROEJA;01/02/2024;31/12/2026;EM_ANDAMENTO;ATIVO;RESPONSAVEL FICTICIO;00000000000\r\n"
    )


def linha_matricula(co_unidade):
    # O Sistec exporta o status com sublinhado (o painel Power BI compara
    # `NO_STATUS_MATRICULA` direto com "EM_CURSO").
    return f"{co_unidade}0001;{co_unidade}01;EM_CURSO;03/2026\r\n"


PAGINA_LOGIN = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Sistec simulado</title></head>
<body><h1>Login gov.br simulado</h1>
<form method="post" action="/entrar"><button type="submit">Entrar com gov.br</button></form>
{automatico}</body></html>"""

PAGINA_PERFIS = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Sistec simulado - perfis</title></head>
<body><h1>Selecione o perfil</h1>
<form id="form-perfil" method="post" action="/index/index">
  <input type="hidden" name="tipo" value="">
  <input type="hidden" name="acao" value="">
  <input type="hidden" name="qtdPerfis" value="{qtd}">
  <div id="combo"></div>
  <button type="submit">Acessar</button>
</form>
<a href="/sair">Sair</a>
<script>
  const PERFIS = {perfis};
  setTimeout(function () {{
    const combo = document.getElementById("combo");
    PERFIS.forEach(function (perfil) {{
      const item = document.createElement("div");
      item.textContent = perfil[1];
      item.addEventListener("click", function () {{
        document.querySelector('input[name="tipo"]').value = perfil[0];
      }});
      combo.appendChild(item);
    }});
  }}, 300);
</script></body></html>"""


class HandlerSimulado(BaseHTTPRequestHandler):
    login_automatico = LOGIN_AUTOMATICO
    sessao_expira = SESSAO_EXPIRA
    atraso_s = ATRASO_S

    def log_message(self, fmt, *args):  # silencia o log padrão em stdout
        pass

    def _cookies(self):
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        return {nome: morsel.value for nome, morsel in cookies.items()}

    def _logado(self):
        return not self.sessao_expira and self._cookies().get("sim_sessao") == "ok"

    def do_GET(self):
        if self.atraso_s:
            time.sleep(self.atraso_s)
        caminho = urlparse(self.path).path

        if caminho == "/sair":
            self._redirecionar("/", cookies=["sim_sessao=; Path=/; Max-Age=0"])
        elif not self._logado():
            # Inclusive nas exportações: sessão expirada devolve HTML de login.
            self._responder_login()
        elif caminho == "/":
            self._redirecionar(CAMINHO_PERFIS)
        elif caminho == CAMINHO_PERFIS:
            perfis = json.dumps([[p["id"], p["texto"]] for p in PERFIS], ensure_ascii=False)
            self._responder_html(PAGINA_PERFIS.format(qtd=len(PERFIS), perfis=perfis))
        elif caminho == "/index/index":
            # Troca de perfil por URL, do jeito do script R (o CalcSISTEC usa
            # isso no modo "pasta de Downloads"). O Sistec real pode ou não
            # continuar aceitando — é o que o teste com login real vai dizer.
            tipo = (parse_qs(urlparse(self.path).query).get("tipo") or [""])[0]
            if tipo not in UNIDADE_POR_PERFIL:
                self._responder_html("<html><body>perfil inválido</body></html>", status=400)
                return
            self._responder_html(
                "<html><body>perfil ativo <a href='/sair'>Sair</a></body></html>",
                cookies=[f"sim_perfil={tipo}; Path=/"],
            )
        elif caminho == "/gridciclo/exportar-ciclo-turmas/":
            co_unidade = self._unidade_ativa()
            self._responder_csv(CABECALHO_CICLO + (linha_ciclo(co_unidade) if co_unidade else ""))
        elif caminho == "/aluno/gerar-csv/":
            co_unidade = self._unidade_ativa()
            self._responder_csv(CABECALHO_MATRICULA + (linha_matricula(co_unidade) if co_unidade else ""))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.atraso_s:
            time.sleep(self.atraso_s)
        caminho = urlparse(self.path).path
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = parse_qs(self.rfile.read(tamanho).decode("utf-8"))

        if caminho == "/entrar":
            self._redirecionar(CAMINHO_PERFIS, cookies=["sim_sessao=ok; Path=/"])
        elif not self._logado():
            self._responder_login()
        elif caminho == "/index/index":
            # Achado 1 da F0: troca de perfil é POST, sem query string.
            tipo = (corpo.get("tipo") or [""])[0]
            if tipo not in UNIDADE_POR_PERFIL:
                self._responder_html("<html><body>perfil inválido</body></html>", status=400)
                return
            self._responder_html(
                "<html><body>perfil ativo <a href='/sair'>Sair</a></body></html>",
                cookies=[f"sim_perfil={tipo}; Path=/"],
            )
        else:
            self.send_response(404)
            self.end_headers()

    def _unidade_ativa(self):
        return UNIDADE_POR_PERFIL.get(self._cookies().get("sim_perfil", ""))

    def _responder_login(self):
        automatico = "<script>document.forms[0].submit()</script>" if self.login_automatico else ""
        self._responder_html(PAGINA_LOGIN.format(automatico=automatico))

    def _redirecionar(self, destino, cookies=()):
        self.send_response(303)
        self.send_header("Location", destino)
        for cookie in cookies:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _responder_html(self, html, status=200, cookies=()):
        corpo = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        for cookie in cookies:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _responder_csv(self, texto):
        corpo = texto.encode("cp1252")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def criar_servidor(porta=PORTA, login_automatico=None):
    """Servidor pronto para `serve_forever()`. `porta=0` escolhe uma livre
    (usado pelos testes, via `servidor.server_address[1]`)."""
    handler = HandlerSimulado
    if login_automatico is not None:
        handler = type("HandlerSimuladoConfigurado", (HandlerSimulado,), {"login_automatico": login_automatico})
    return ThreadingHTTPServer(("127.0.0.1", porta), handler)


def rodar(porta=PORTA):
    servidor = criar_servidor(porta)
    print(f"Sistec simulado em http://127.0.0.1:{servidor.server_address[1]}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    rodar()
