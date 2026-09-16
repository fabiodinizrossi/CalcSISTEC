"""BC-04 (Apresentação): rodapé comum às 5 páginas públicas do Dash
(`Footer`), feature `001-govbr-design-system` (T018).

Mostra o nome da instituição, o site institucional e o e-mail de contato
vigentes (`config_store` — RF-04, RF-15, RN-12) e o link "Área
administrativa" (RF-18) para `/admin/login`. Tudo isso vem da configuração
preenchida no assistente de instalação: nenhuma instituição fica fixa no
código. O que estiver em branco simplesmente não aparece.
"""

from dash import html

from app.data.config_store import dados_instituicao


def make_footer():
    instituicao = dados_instituicao()
    itens = []
    if instituicao["nome"]:
        itens.append(html.Span(instituicao["nome"]))
    if instituicao["site"]:
        site = instituicao["site"]
        href = site if site.startswith(("http://", "https://")) else f"https://{site}"
        itens.append(html.A(site, href=href, target="_blank", rel="noopener"))
    if instituicao["contato_email"]:
        itens.append(html.Span(instituicao["contato_email"]))
    itens.append(html.A("Área administrativa", href="/admin/login", className="app-footer-admin-link"))

    return html.Footer(className="app-footer", role="contentinfo", children=itens)
