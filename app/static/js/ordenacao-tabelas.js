/** Ordenacao reutilizavel para todas as tabelas de dados do painel. */
(function (raiz, fabrica) {
  var api = fabrica();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (raiz && raiz.document) api.iniciar(raiz.document);
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  var colador = new Intl.Collator("pt-BR", { numeric: true, sensitivity: "base" });

  function textoDaCelula(celula) {
    return (celula && (celula.dataset.sortValue || celula.textContent) || "").trim();
  }

  function valorComparavel(texto) {
    var limpo = String(texto || "").trim();
    if (!limpo || /^[\u2013\u2014-]$/.test(limpo)) return { tipo: "vazio", valor: null };

    var dataBr = limpo.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/);
    if (dataBr) {
      return {
        tipo: "numero",
        valor: Date.UTC(+dataBr[3], +dataBr[2] - 1, +dataBr[1], +(dataBr[4] || 0), +(dataBr[5] || 0), +(dataBr[6] || 0)),
      };
    }
    if (/^\d{4}-\d{2}-\d{2}(?:[ T].*)?$/.test(limpo)) {
      var instante = Date.parse(limpo);
      if (!Number.isNaN(instante)) return { tipo: "numero", valor: instante };
    }

    var numero = limpo.replace(/\s/g, "").replace(/%$/, "");
    if (/^[+-]?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?$/.test(numero)) {
      return { tipo: "numero", valor: Number(numero.replace(/\./g, "").replace(",", ".")) };
    }
    if (/^[+-]?\d+(?:\.\d+)?$/.test(numero)) return { tipo: "numero", valor: Number(numero) };
    return { tipo: "texto", valor: limpo };
  }

  function comparar(a, b) {
    var va = valorComparavel(a);
    var vb = valorComparavel(b);
    if (va.tipo === "vazio" || vb.tipo === "vazio") {
      if (va.tipo === vb.tipo) return 0;
      return va.tipo === "vazio" ? 1 : -1;
    }
    if (va.tipo === "numero" && vb.tipo === "numero") return va.valor - vb.valor;
    return colador.compare(String(va.valor), String(vb.valor));
  }

  function indiceDaColuna(th) {
    var linhas = Array.from(th.closest("thead").rows);
    var grade = [];
    for (var r = 0; r < linhas.length; r += 1) {
      grade[r] = grade[r] || [];
      var coluna = 0;
      for (var c = 0; c < linhas[r].cells.length; c += 1) {
        var celula = linhas[r].cells[c];
        while (grade[r][coluna]) coluna += 1;
        var inicio = coluna;
        var colspan = celula.colSpan || 1;
        var rowspan = celula.rowSpan || 1;
        for (var rr = r; rr < r + rowspan; rr += 1) {
          grade[rr] = grade[rr] || [];
          for (var cc = inicio; cc < inicio + colspan; cc += 1) grade[rr][cc] = celula;
        }
        if (celula === th) return inicio;
        coluna += colspan;
      }
    }
    return -1;
  }

  function ehOrdenavel(th) {
    var tabela = th.closest("table");
    return Boolean(
      tabela && tabela.tBodies.length && th.closest("thead") &&
      th.colSpan <= 1 && !th.hasAttribute("data-no-sort") &&
      tabela.getAttribute("data-sortable") !== "false"
    );
  }

  function preparar(tabela) {
    if (!tabela.tHead || !tabela.tBodies.length || tabela.getAttribute("data-sortable") === "false") return;
    Array.from(tabela.tHead.querySelectorAll("th")).forEach(function (th) {
      if (!ehOrdenavel(th)) return;
      th.classList.add("cabecalho-ordenavel");
      th.setAttribute("tabindex", "0");
      if (!th.hasAttribute("aria-sort")) th.setAttribute("aria-sort", "none");
      th.setAttribute("title", "Ordenar por esta coluna");
    });
    if (tabela.dataset.sortColumn !== undefined && tabela.dataset.sortDirection) {
      ordenarLinhas(tabela, Number(tabela.dataset.sortColumn), tabela.dataset.sortDirection);
    }
  }

  function ordenarLinhas(tabela, indice, direcao) {
    Array.from(tabela.tBodies).forEach(function (tbody) {
      var linhas = Array.from(tbody.rows);
      var hierarquica = linhas.some(function (linha) {
        return linha.dataset && linha.dataset.groupId !== undefined;
      });
      var itens;

      if (hierarquica) {
        var porPai = {};
        linhas.forEach(function (linha) {
          var pai = linha.dataset.parentId || "";
          porPai[pai] = porPai[pai] || [];
          porPai[pai].push(linha);
        });
        function blocoDaLinha(linha) {
          var bloco = [linha];
          (porPai[linha.dataset.groupId] || []).forEach(function (filha) {
            bloco = bloco.concat(blocoDaLinha(filha));
          });
          return bloco;
        }
        itens = (porPai[""] || []).map(function (linha, posicao) {
          return {
            linha: linha,
            linhas: blocoDaLinha(linha),
            posicao: posicao,
            texto: textoDaCelula(linha.cells[indice]),
          };
        });
      } else {
        itens = linhas.map(function (linha, posicao) {
          return { linha: linha, linhas: [linha], posicao: posicao, texto: textoDaCelula(linha.cells[indice]) };
        });
      }

      itens.sort(function (a, b) {
        var vaziaA = valorComparavel(a.texto).tipo === "vazio";
        var vaziaB = valorComparavel(b.texto).tipo === "vazio";
        var resultado = comparar(a.texto, b.texto);
        if (!(vaziaA || vaziaB) && direcao === "descending") resultado *= -1;
        return resultado || a.posicao - b.posicao;
      });
      var ordenadas = [];
      itens.forEach(function (item) { ordenadas = ordenadas.concat(item.linhas); });
      ordenadas.forEach(function (linha, posicao) {
        if (tbody.rows[posicao] !== linha) tbody.insertBefore(linha, tbody.rows[posicao] || null);
      });
    });
  }

  function ordenar(th) {
    if (!ehOrdenavel(th)) return;
    var tabela = th.closest("table");
    var indice = indiceDaColuna(th);
    if (indice < 0) return;
    var mesmaColuna = tabela.dataset.sortColumn === String(indice);
    var direcao = mesmaColuna && tabela.dataset.sortDirection === "descending" ? "ascending" : "descending";
    tabela.dataset.sortColumn = String(indice);
    tabela.dataset.sortDirection = direcao;

    Array.from(tabela.tHead.querySelectorAll("th[aria-sort]")).forEach(function (cabecalho) {
      cabecalho.setAttribute("aria-sort", cabecalho === th ? direcao : "none");
    });
    ordenarLinhas(tabela, indice, direcao);
  }

  function iniciar(documento) {
    function prepararNo(alvo) {
      if (!alvo || alvo.nodeType !== 1) return;
      if (alvo.matches && alvo.matches("table")) preparar(alvo);
      var tabelaPai = alvo.closest && alvo.closest("table");
      if (tabelaPai) preparar(tabelaPai);
      if (alvo.querySelectorAll) Array.from(alvo.querySelectorAll("table")).forEach(preparar);
    }
    function pronto() {
      Array.from(documento.querySelectorAll("table")).forEach(preparar);
      documento.addEventListener("click", function (evento) {
        var th = evento.target.closest && evento.target.closest("th");
        if (th) ordenar(th);
      });
      documento.addEventListener("keydown", function (evento) {
        var th = evento.target.closest && evento.target.closest("th.cabecalho-ordenavel");
        if (th && (evento.key === "Enter" || evento.key === " ")) {
          evento.preventDefault();
          ordenar(th);
        }
      });
      if (typeof MutationObserver === "function") {
        new MutationObserver(function (mudancas) {
          mudancas.forEach(function (mudanca) { Array.from(mudanca.addedNodes).forEach(prepararNo); });
        }).observe(documento.body, { childList: true, subtree: true });
      }
    }
    if (documento.readyState === "loading") documento.addEventListener("DOMContentLoaded", pronto);
    else pronto();
  }

  return {
    comparar: comparar,
    indiceDaColuna: indiceDaColuna,
    iniciar: iniciar,
    ordenar: ordenar,
    ordenarLinhas: ordenarLinhas,
    valorComparavel: valorComparavel,
  };
});
