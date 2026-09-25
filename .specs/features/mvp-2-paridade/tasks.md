# MVP 2 — Paridade numérica com o Power BI — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

Exceção combinada com a usuária para executores sem suporte a skills: leia `.specs/MVP-PROTOCOLO.md` inteiro e siga-o; ele aponta o arquivo da skill que substitui a ativação.

Pré-requisito: a feature `mvp-1-refatoracao` com Verifier PASS.

---

**Spec**: `.specs/features/mvp-2-paridade/spec.md`
**Design**: não há `design.md`; as assinaturas estão nas tarefas.
**Status**: Draft

---

## Test Coverage Matrix

> Diretrizes: `.specs/PROJECT_RULES.md` Princípio I (regra de domínio nova exige teste de paridade com caso nominal e casos de vazio/NaN/data nula) e Princípio IV; `.specs/MVP-PROTOCOLO.md`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Domínio (`app/domain/*.py`) | unit | 1:1 com os ACs; caso nominal + vazio + NaN/nulo; números calculados à mão no próprio teste | `tests/test_parity_dominio.py` | `python -m pytest tests/test_parity_dominio.py -q -p no:cacheprovider` |
| Dados (`app/data/consulta.py`) | integration | Colunas novas presentes nas duas consultas (banco publicado e `conn` explícita) | `tests/test_consulta.py` | `python -m pytest tests/test_consulta.py -q -p no:cacheprovider` |
| Painéis (`app/paineis/*.py`) | unit | Cada chave do resultado com valor esperado calculado à mão; filtro vazio; df vazio | `tests/test_paineis_*.py` | `python -m pytest tests/test_paineis_*.py -q -p no:cacheprovider` |
| Script (`scripts/paridade.py`) | integration | Pasta sintética de 2 campi → planilha com as linhas do spec; `comparar` nos 3 códigos de saída; `sistec.db` intocado | `tests/test_paridade_script.py` | `python -m pytest tests/test_paridade_script.py -q -p no:cacheprovider` |
| Documentação | unit (higiene) | Seções exigidas presentes | `tests/test_higiene_repositorio.py` | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Tarefas humanas e relatório | none | — | — | — |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Tarefas só de documentação | `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider` |
| Full | Toda tarefa com `.py` | `python -m pytest -q -p no:cacheprovider` |
| Build | Fim de fase | `python -m pytest -q -p no:cacheprovider` |

---

## Execution Plan

### Phase 1: Dados e domínio

```
T1 → T2 → T3 → T4
```

### Phase 2: Camada `app/paineis/`

```
T5 → T6 → T7 → T8 → T9 → T10 → T11
```

### Phase 3: Script de paridade

```
T12 → T13 → T14 → T15
```

### Phase 4: Campanha

```
T16 → T17 → T18 → T19
```

---

## Task Breakdown

### T1: `carregar_eficiencia` traz tipo de curso e programa

**What**: Acrescentar `cu.tipo_curso_pnp` e `c.tipo_programa_curso` ao `SELECT`
de `carregar_eficiencia` (`app/data/consulta.py`), **nas duas consultas** da
função (a com `conn` explícita e a que abre conexão própria).
**Where**: `app/data/consulta.py`
**Depends on**: None
**Reuses**: `carregar_matriculas`, que já traz essas colunas
**Requirement**: PAR-01

**Passos**:

1. Escreva primeiro, em `tests/test_consulta.py`, um teste que chama
   `carregar_eficiencia` com um banco de teste (use o mesmo padrão de banco
   temporário dos testes que já existem no arquivo) e afirma que
   `"tipo_curso_pnp"` e `"tipo_programa_curso"` estão em `df.columns`. Faça o
   mesmo para o caminho com `conn=`. Rode e veja falhar.
2. Acrescente as duas colunas nas duas consultas.

**Done when**:

- [ ] Os dois testes novos falham antes e passam depois
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: linha de base + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(consulta): trazer tipo de curso e programa na base de eficiencia`

---

### T2: Categorias de evasão do Power BI no domínio

**What**: Em `app/domain/shared.py`, criar `CATEGORIAS_EVASAO`. Em
`app/domain/matriculas.py`, criar `contar_evasoes_por_categoria(df, filtros)`.
**Where**: `app/domain/matriculas.py`
**Depends on**: T1
**Reuses**: `STATUS_EVADIDO` (`app/domain/shared.py`), `_aplicar_filtros` (`app/domain/matriculas.py`)
**Requirement**: PAR-02

**Passos**:

1. Em `app/domain/shared.py`, logo abaixo de `STATUS_EVADIDO`:

   ```python
   # Agrupamento das evasões usado pelos cartões da página de evasão.
   CATEGORIAS_EVASAO = {
       "abandonos": frozenset({"ABANDONO"}),
       "transferencias_externas": frozenset({"TRANSF_EXT"}),
       "desligamentos": frozenset({"DESLIGADO", "DESLIGADA", "REPROVADO", "REPROVADA"}),
       "transferencias_internas": frozenset({"TRANSF_INT"}),
   }
   ```

2. Em `app/domain/matriculas.py`:

   ```python
   def contar_evasoes_por_categoria(df, filtros: FiltrosAtivos):
       """Conta as evasões do ano-base em cada categoria de CATEGORIAS_EVASAO."""
       filtrado = _aplicar_filtros(df, filtros)
       return {
           nome: int(filtrado["status_corrigido"].isin(status).sum())
           for nome, status in CATEGORIAS_EVASAO.items()
       }
   ```

3. Testes em `tests/test_parity_dominio.py` (antes do código, veja falhar):
   - a união das 4 categorias é igual a `STATUS_EVADIDO` e nenhuma categoria
     tem status em comum com outra;
   - df com ano-base 2026 e status `ABANDONO`×3, `TRANSF_EXT`×1,
     `DESLIGADO`×1, `REPROVADA`×1, `TRANSF_INT`×2, `EM_CURSO`×4 e uma linha
     `ABANDONO` com `ano_base` 2025 → `{"abandonos": 3, "transferencias_externas": 1, "desligamentos": 2, "transferencias_internas": 2}`;
   - a soma das 4 categorias é igual a `contar_evadidos(df, filtros)` nesse mesmo df;
   - df vazio (com as colunas) → as 4 categorias em 0.

   Monte o df com as colunas que `_aplicar_filtros` lê (`ano_base`,
   `status_corrigido`, `co_unidade`, `codigo_portfolio`), no mesmo estilo dos
   testes vizinhos.

**Done when**:

- [ ] Os 4 testes novos passam; falhavam antes (registre no commit)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(domain): categorizar evasoes como o power bi`

---

### T3: Evasões por mês no domínio

**What**: Em `app/domain/matriculas.py`, criar `evasoes_por_mes(df, filtros)`.
**Where**: `app/domain/matriculas.py`
**Depends on**: T2
**Reuses**: `parsear_mes_ocorrencia`, `eh_evadido` (`app/domain/shared.py`), `_aplicar_filtros`
**Requirement**: PAR-03

**Passos**:

1. Código:

   ```python
   def evasoes_por_mes(df, filtros: FiltrosAtivos):
       """Lista de 12 contagens (janeiro a dezembro) das evasões cujo mês de
       ocorrência cai no ano-base. Mês nulo ou inválido não conta."""
       filtrado = _aplicar_filtros(df, filtros)
       evadidos = filtrado[filtrado["status_corrigido"].apply(eh_evadido)]
       meses = parsear_mes_ocorrencia(evadidos["mes_ocorrencia_corrigido"])
       no_ano = meses[meses.dt.year == filtros.ano_base]
       contagem = no_ano.dt.month.value_counts()
       return [int(contagem.get(mes, 0)) for mes in range(1, 13)]
   ```

2. Testes em `tests/test_parity_dominio.py` (antes do código):
   - ano-base 2026: `ABANDONO` com `"MARÇO 2026"`, `TRANSF_EXT` com
     `"MARCO 2026"`, `DESLIGADO` com `"AGOSTO 2026"`, `ABANDONO` com
     `"AGOSTO 2025"` (outro ano), `EM_CURSO` com `"AGOSTO 2026"` (não é evasão),
     `ABANDONO` com `None`, `ABANDONO` com `"TEXTO"` → resultado
     `[0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0]`;
   - df vazio → 12 zeros;
   - o resultado sempre tem 12 posições.

**Done when**:

- [ ] Testes novos passam; falhavam antes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(domain): contar evasoes por mes de ocorrencia`

---

### T4: Matrículas equivalentes por recorte legal no domínio

**What**: Em `app/domain/percentuais_legais.py`, criar `equivalentes_por_recorte(df)`.
**Where**: `app/domain/percentuais_legais.py`
**Depends on**: T3
**Reuses**: `matriculas_equivalentes`, `recorte_tecnico`, `recorte_professores`, `recorte_proeja`
**Requirement**: PAR-04

**Passos**:

1. Código:

   ```python
   def equivalentes_por_recorte(df, exclusoes=EXCLUSOES_PROFESSORES):
       """Soma das matrículas equivalentes no total e em cada recorte legal."""
       if df.empty:
           return {"total": 0.0, "tecnico": 0.0, "professores": 0.0, "proeja": 0.0}
       equivalentes = matriculas_equivalentes(df)
       return {
           "total": float(equivalentes.sum()),
           "tecnico": float(equivalentes.loc[recorte_tecnico(df).index].sum()),
           "professores": float(equivalentes.loc[recorte_professores(df, exclusoes).index].sum()),
           "proeja": float(equivalentes.loc[recorte_proeja(df).index].sum()),
       }
   ```

2. Testes em `tests/test_parity_dominio.py` (antes do código). Reaproveite a
   fábrica de df que os testes de percentuais legais do arquivo já usam:
   - para esse df, `equivalentes_por_recorte(df)["tecnico"] / equivalentes_por_recorte(df)["total"]`
     é igual a `percentual_tecnico(df)` (use `pytest.approx`); o mesmo para
     professores e proeja;
   - um caso com números calculados à mão no próprio teste (2 ou 3 linhas);
   - df vazio → 4 zeros.

**Done when**:

- [ ] Testes novos passam; falhavam antes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(domain): somar equivalentes por recorte legal`

---

### T5: `app/paineis/` e os filtros comuns

**What**: Criar o pacote `app/paineis/` e `app/paineis/filtros.py` com
`FiltrosPainel` e `aplicar_filtros(df, filtros)`.
**Where**: `app/paineis/filtros.py` (novo)
**Depends on**: None
**Reuses**: `filtrar_fic` (`app/domain/matriculas.py`); os `_filtrar` das páginas (`app/pages/*.py`)
**Requirement**: PAR-05, PAR-06

**Passos**:

1. `app/paineis/__init__.py`: docstring de uma linha, "Números de cada página
   pública, calculados sem Dash."
2. `app/paineis/filtros.py`:

   ```python
   """Filtros da tela aplicados aos dados de qualquer página."""

   from dataclasses import dataclass

   import pandas as pd

   from app.domain.matriculas import filtrar_fic

   COLUNAS = {
       "campus": "cidade",
       "tipo_curso": "tipo_curso_pnp",
       "programa": "tipo_programa_curso",
       "modalidade": "modalidade_ensino",
   }


   @dataclass(frozen=True)
   class FiltrosPainel:
       campus: str | None = None
       tipo_curso: str | None = None
       programa: str | None = None
       modalidade: str | None = None
       incluir_fic: bool = True
       ano_ingresso: tuple[int, int] | None = None


   def aplicar_filtros(df, filtros):
       """Devolve o df só com as linhas que passam em todos os filtros."""
       for campo, coluna in COLUNAS.items():
           valor = getattr(filtros, campo)
           if valor is not None:
               df = df[df[coluna] == valor]
       if filtros.ano_ingresso is not None:
           if "dt_data_inicio" not in df.columns:
               raise ValueError("ano_ingresso exige dt_data_inicio")
           inicio, fim = filtros.ano_ingresso
           anos = pd.to_datetime(df["dt_data_inicio"], errors="coerce").dt.year
           df = df[anos.between(inicio, fim)]
       return filtrar_fic(df, filtros.incluir_fic)
   ```

3. `tests/test_paineis_filtros.py`, um teste por AC da história "Filtros comuns":
   sem filtro devolve tudo; cada filtro de texto; `ano_ingresso=(2020, 2022)`
   com linhas de 2019, 2020, 2022, 2023 e `NaT` → só 2020 e 2022; sem a coluna
   → `ValueError` com a mensagem exata; `incluir_fic=False` tira
   `FORMAÇÃO INICIAL` e `FORMAÇÃO CONTINUADA` (coluna `categoria_origem_curso`).
4. Um teste de camada: nenhum arquivo de `app/paineis/` importa `dash`,
   `flask`, `app.data`, `app.pages`, `app.components`, `app.sistec` ou
   `app.rotas` (leia o texto de cada `.py` e procure `import dash`,
   `from dash`, `import flask`, `from flask`, `from app.data`,
   `import app.data`, e assim por diante).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(paineis): filtros comuns das paginas publicas`

---

### T6: Tabela por coluna com linha de total

**What**: `app/paineis/tabela.py` com `tabela_por(df, coluna, metricas)`.
**Where**: `app/paineis/tabela.py` (novo)
**Depends on**: T5
**Reuses**: nenhum
**Requirement**: PAR-06

**Passos**:

1. Código:

   ```python
   """Monta a tabela de uma página: uma linha por valor da coluna e o total."""


   def tabela_por(df, coluna, metricas):
       """`metricas(grupo)` devolve um dict. O resultado é uma lista de dicts com
       a chave `linha` (o valor da coluna, ou "Total") e as chaves de `metricas`.
       Valor nulo na coluna vira "Não informado"."""
       linhas = []
       rotulos = df[coluna].where(df[coluna].notna(), "Não informado")
       for valor in sorted(rotulos.unique(), key=str):
           linhas.append({"linha": valor, **metricas(df[rotulos == valor])})
       linhas.append({"linha": "Total", **metricas(df)})
       return linhas
   ```

2. `tests/test_paineis_tabela.py`: ordem alfabética; `Total` por último e
   calculado sobre o df inteiro (não soma das linhas: teste com uma métrica que
   não é soma, por exemplo `{"n_unicos": grupo["x"].nunique()}`); nulo vira
   "Não informado"; df vazio → só a linha `Total`.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(paineis): tabela por coluna com linha de total`

---

### T7: Números da página Matrículas

**What**: `app/paineis/matriculas.py` com `resumo_matriculas(df, ano_base, filtros)`
e `metricas_matriculas(grupo)`, com a mesma conta que `app/pages/matriculas.py`
faz hoje (callback `atualizar` e `_metricas`).
**Where**: `app/paineis/matriculas.py` (novo)
**Depends on**: T6
**Reuses**: `app/pages/matriculas.py` (`_metricas`, `atualizar`); `contar_matriculas`, `contar_por_status`, `contar_ingressantes`, `contar_cursos_ativos` (`app/domain/matriculas.py`); `matricula_equivalente`, `eh_evadido` (`app/domain/shared.py`); `FiltrosAtivos` (`app/domain/contrato.py`)
**Requirement**: PAR-07

**Passos**:

1. Leia `app/pages/matriculas.py`, função `atualizar` e `_metricas`, até o fim.
2. `resumo_matriculas(df, ano_base, filtros)`:
   - `df = aplicar_filtros(df, filtros)`;
   - `filtros_dominio = FiltrosAtivos(ano_base=ano_base, eixo="campus", incluir_fic=filtros.incluir_fic)`;
   - `matriculas = contar_matriculas(df, filtros_dominio)`;
   - `concluidas = contar_por_status(df, filtros_dominio, "CONCLUÍDA")`;
   - `ingressantes = contar_ingressantes(df, filtros_dominio)`;
   - `cursos = contar_cursos_ativos(df, filtros_dominio)`;
   - `equivalentes`: `None` se `df[df["ano_base"] == ano_base]` está vazio;
     senão a soma de `matricula_equivalente(tipo_curso_pnp, carga_horaria_total, fec, 1, fech)`
     sobre essas linhas (igual à página);
   - devolva `{"cursos", "matriculas", "equivalentes", "concluidas", "ingressantes"}`.
3. `metricas_matriculas(grupo)`: cópia exata de `_metricas` da página, com as
   chaves `total`, `concluidas`, `integralizadas`, `em_curso`, `evasoes`.
4. `tests/test_paineis_matriculas.py`: um df sintético de uns 12 registros, com
   2 campi, 2 cursos, os status `CONCLUÍDA`, `INTEGRALIZADA`, `EM_CURSO`,
   `ABANDONO`, `TRANSF_EXT`, ciclos iniciados em 2025 e 2026 e uma linha FIC.
   Calcule à mão, num comentário do teste, cada número esperado. Teste:
   - `resumo_matriculas` com filtros padrão (com FIC) e com `incluir_fic=False`;
   - filtro de campus;
   - `metricas_matriculas` do df inteiro;
   - df filtrado vazio → `matriculas`, `concluidas`, `ingressantes`, `cursos` em 0 e `equivalentes` `None`.
5. Não mude `app/pages/matriculas.py` nesta tarefa (a feature 3 faz a página usar esta função).

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(paineis): numeros da pagina de matriculas`

---

### T8: Números da página Eficiência Acadêmica

**What**: `app/paineis/eficiencia.py` com `resumo_eficiencia(df, filtros)` e
`metricas_eficiencia(grupo)`.
**Where**: `app/paineis/eficiencia.py` (novo)
**Depends on**: T7
**Reuses**: `classificar_matriculas_eficiencia`, `calcular_iea` (`app/domain/eficiencia.py`)
**Requirement**: PAR-08

**Passos**:

1. `metricas_eficiencia(grupo)`:
   `concluidos, evadidos, retidos = classificar_matriculas_eficiencia(grupo, None)`
   e devolva `{"iea": calcular_iea(concluidos, evadidos, retidos), "concluidos": ..., "evadidos": ..., "retidos": ...}`.
   Atenção: a base de eficiência usa a coluna `status_corrigido2`, não
   `status_corrigido`; `classificar_matriculas_eficiencia` já lê a coluna certa.
   Confira que o segundo argumento (`filtros`) não é usado dentro dela antes de
   passar `None`; se for usado, passe um `FiltrosAtivos` com o ano-base.
2. `resumo_eficiencia(df, filtros)`: `metricas_eficiencia(aplicar_filtros(df, filtros))`.
3. `tests/test_paineis_eficiencia.py`: reproduza o total do print do Power BI
   (`.specs/referencias/eficiencia-por-campus-sem-fic.png`): um df com 1.849
   `CONCLUÍDA`, 2.613 `ABANDONO` e 502 `EM_CURSO` dá `iea` ≈ 0,4144
   (`pytest.approx(0.4144, abs=1e-4)`), `concluidos=1849`, `evadidos=2613`,
   `retidos=502`. Mais: df vazio → tudo 0; filtro sem FIC.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(paineis): numeros da pagina de eficiencia`

---

### T9: Números da página Taxa de Evasão Anual

**What**: `app/paineis/evasao.py` com `resumo_evasao(df, ano_base, filtros)`,
`evasoes_por_mes(df, ano_base, filtros)` e `metricas_evasao(grupo, ano_base)`.
**Where**: `app/paineis/evasao.py` (novo)
**Depends on**: T8
**Reuses**: `contar_evasoes_por_categoria`, `evasoes_por_mes` (domínio, T2 e T3), `contar_evadidos`, `contar_matriculas`, `taxa_evasao` (`app/domain/matriculas.py`)
**Requirement**: PAR-09

**Passos**:

1. `resumo_evasao`: aplique `aplicar_filtros`, monte
   `FiltrosAtivos(ano_base=ano_base, incluir_fic=filtros.incluir_fic)` e
   devolva as 4 categorias de `contar_evasoes_por_categoria`, mais
   `evasoes = contar_evadidos(...)`, `matriculas = contar_matriculas(...)` e
   `taxa = taxa_evasao(...)`.
2. `evasoes_por_mes(df, ano_base, filtros)`: aplica os filtros e chama a função
   do domínio (importe-a com outro nome, `from app.domain.matriculas import evasoes_por_mes as _evasoes_por_mes_dominio`).
3. `metricas_evasao(grupo, ano_base)`: `{"evasoes": ..., "taxa": ...}` do grupo.
   Como `tabela_por` chama `metricas(grupo)` com um argumento só, as páginas e o
   script vão usar `functools.partial(metricas_evasao, ano_base=ano_base)`;
   escreva isso na docstring.
4. `tests/test_paineis_evasao.py`: soma das 4 categorias igual a `evasoes`;
   reproduza a taxa de um campus do print (`.specs/referencias/evasao-por-campus.png`,
   Jaguari: 131 evasões em 794 matrículas → `taxa` ≈ 0,165); df vazio → zeros
   e taxa 0,0; `evasoes_por_mes` com 12 posições.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(paineis): numeros da pagina de evasao`

---

### T10: Números da página Percentuais Legais

**What**: `app/paineis/percentuais.py` com `resumo_percentuais(df, ano_base, filtros)`
e `metricas_percentuais(grupo)`.
**Where**: `app/paineis/percentuais.py` (novo)
**Depends on**: T9
**Reuses**: `equivalentes_por_recorte` (T4); `_base_percentuais` e o callback `atualizar` de `app/pages/percentuais_legais.py`
**Requirement**: PAR-10

**Passos**:

1. Leia `app/pages/percentuais_legais.py`, callback `atualizar` e `_base_percentuais`.
2. `metricas_percentuais(grupo)`: `grupo.assign(quantidade_matriculas=1)` (como
   `_base_percentuais`), `r = equivalentes_por_recorte(base)` e devolva
   `equivalentes=r["total"]`, `tecnico_mateq`, `professores_mateq`,
   `proeja_mateq` e os três `pct_*` (`r["tecnico"] / r["total"]`, 0,0 se o
   total for 0).
3. `resumo_percentuais(df, ano_base, filtros)`: filtre `df["ano_base"] == ano_base`
   (a página faz isso), aplique `aplicar_filtros` e chame `metricas_percentuais`.
4. `tests/test_paineis_percentuais.py`: `pct_tecnico` igual a
   `percentual_tecnico` do domínio para o mesmo df; df vazio → zeros; linhas de
   outro ano-base ficam fora.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `feat(paineis): numeros da pagina de percentuais legais`

---

### T11: Emendar o Princípio II para a camada `app/paineis/`

**What**: `PROJECT_RULES.md` 1.3.0 → 1.4.0 (MINOR): o Princípio II passa a
listar `app/paineis/` e a regra de dependência dela. Registrar AD-007 no
`STATE.md`. README: `app/paineis/` na "Estrutura" (o teste de higiene exige) e
em "Onde mexer" ("Mudar um número mostrado numa página").
**Where**: `.specs/PROJECT_RULES.md`
**Depends on**: T10
**Reuses**: formato do Sync Impact Report atual
**Requirement**: PAR-11

**Passos**:

1. Sync Impact Report no topo: "1.3.0 → 1.4.0 (data de hoje) — Princípio II:
   nova camada `app/paineis/`, que monta os números de cada página pública a
   partir de `app/domain/`, sem Dash; usada pelas páginas e por
   `scripts/paridade.py`." Mantenha os relatórios anteriores abaixo, como já está.
2. No Princípio II, acrescente dois itens:
   - "`app/paineis/` monta os números de cada página pública. MUST importar só
     a biblioteca padrão, `pandas` e `app/domain/`."
   - "Páginas (`app/pages/`) e scripts MUST obter os números por `app/paineis/`,
     nunca recalculando a regra no callback."
3. Rodapé: `**Version**: 1.4.0`, `**Last Amended**:` data de hoje.
4. `STATE.md`, seção Decisions: AD-007 no formato das outras (Decision, Reason,
   Trade-off, Scope, Date, Status).
5. README: linha de `app/paineis/` na "Estrutura"; linha nova em "Onde mexer".
6. Teste em `tests/test_higiene_repositorio.py`: `PROJECT_RULES.md` cita
   `app/paineis/`.

**Done when**:

- [ ] Princípios I e III–VII inalterados (`git diff` só toca o cabeçalho, o Princípio II e o rodapé)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: full

**Commit**: `docs(rules): emendar PROJECT_RULES para 1.4.0 com a camada de paineis`

---

### T12: `scripts/paridade.py` monta a base a partir de uma pasta

**What**: Criar `scripts/paridade.py` com `montar_base(pasta, ano_base)` que devolve
`(df_matriculas, df_eficiencia)` passando pelo mesmo caminho do envio de pastas,
num banco temporário. Esta é a tarefa mais delicada da feature: se algum passo
não bater com o código real, **pare e avise**.
**Where**: `scripts/paridade.py` (novo)
**Depends on**: None
**Reuses**: `app/sistec/envio.ler_pastas`, `envio.dados_unidades_do_envio`; `app/sistec/consolidacao.consolidar`; `app/data/ingest.preparar_versao`; `app/data/previa.abrir_fonte_previa`; `app/data/consulta.carregar_matriculas` e `carregar_eficiencia`; `app/data/schema.init_db`; `app/data/fatores`
**Requirement**: PAR-12

**Passos**:

1. Leia antes: `app/rotas/envio.py` (a rota de envio, depois da feature 1),
   `app/sistec/execucoes.py` função `_consolidar_ou_falhar`,
   `app/data/ingest.py` função `preparar_versao`, `app/data/previa.py` função
   `abrir_fonte_previa` e a classe da fonte que ela devolve.
2. Estrutura do script:

   ```python
   """Gera e confere a planilha de paridade entre o CalcSISTEC e o Power BI.

   Uso:
     python scripts/paridade.py gerar --pasta DIR --ano-base 2026 --saida paridade.csv
     python scripts/paridade.py comparar --arquivo paridade.csv
   """

   import argparse
   import pathlib
   import sys
   import tempfile

   RAIZ = pathlib.Path(__file__).resolve().parent.parent
   sys.path.insert(0, str(RAIZ))
   ```

3. Uma classe pequena que imita o arquivo enviado pelo navegador:

   ```python
   class _ArquivoLocal:
       def __init__(self, caminho):
           self._caminho = pathlib.Path(caminho)
           self.filename = self._caminho.name

       def read(self):
           return self._caminho.read_bytes()

       def close(self):
           pass
   ```

4. `montar_base(pasta, ano_base)`:
   1. `pasta = pathlib.Path(pasta)`; se faltar `pasta / "ciclos"` ou
      `pasta / "matriculas"`, levante `ValueError` com a mensagem
      `"falta a subpasta ciclos/"` ou `"falta a subpasta matriculas/"`.
   2. `leitura = envio.ler_pastas([_ArquivoLocal(p) for p in sorted((pasta / "ciclos").iterdir())], [_ArquivoLocal(p) for p in sorted((pasta / "matriculas").iterdir())])`.
   3. `conjunto = consolidar([df for _nome, df in leitura["ciclo"]], [df for _nome, df in leitura["matricula"]])`.
   4. Abra `tempfile.TemporaryDirectory()`; `db = pathlib.Path(tmp) / "paridade.db"`; `init_db(db)`.
   5. Confira se o banco novo tem fatores: `SELECT COUNT(*) FROM interna_fatores`
      (use `get_connection(db)`). Se for 0, carregue os fatores padrão:
      `linhas = fatores.ler_e_validar(RAIZ / "app" / "data" / "padroes" / "dados_FEC_PNP.xlsx")`
      e `fatores.substituir_interna_fatores(linhas, db_path=db)`. Se
      `ler_e_validar` devolver outra estrutura (tupla, dict), leia a função e
      passe o que `substituir_interna_fatores` espera. Se não achar como
      carregar os fatores, pare e avise.
   6. `candidato = preparar_versao(conjunto, set(), db_path=db, ano_base=ano_base)`.
   7. Monte o DataFrame de campus a partir do próprio CSV:
      `campus = envio.dados_unidades_do_envio(ciclos_com_modalidade(conjunto["ciclos"]))`.
      Leia o que essa função devolve; `abrir_fonte_previa` espera um DataFrame
      com as colunas `co_unidade`, `cidade`, `nome_unidade`. Converta se preciso.
   8. `fonte = abrir_fonte_previa(candidato, campus_publico=campus_df, db_path=db)`.
      Leia com a conexão de leitura que a classe da fonte oferece (veja
      `abrir_leitura` e como `abrir_leitura_previa` em `app/sistec/execucoes.py`
      a usa): `df_m = carregar_matriculas(conn=...)`,
      `df_e = carregar_eficiencia(conn=...)`. Feche a conexão e a fonte.
   9. Devolva `(df_m, df_e)`. O diretório temporário some ao sair do `with`.
5. `tests/test_paridade_script.py`:
   - fixture que monta, em `tmp_path`, `ciclos/` e `matriculas/` com os CSVs de
     `scripts/sintetico.py` (`csv_ciclo(co_unidade, nome_unidade)` e
     `csv_matricula(co_unidade, nome_unidade)`) para 2 campi. Leia as funções:
     se devolvem texto, grave com a codificação que `app/sistec/colunas.ler_planilha`
     espera (veja os testes de `tests/test_envio.py`);
   - importe o script com `importlib.util.spec_from_file_location`;
   - `montar_base` devolve dois DataFrames não vazios, e `df_m["cidade"]` tem 2 valores;
   - pasta sem `matriculas/` → `ValueError` com a mensagem exata;
   - `app/data/sistec.db`: se existir, a data de modificação e o tamanho são
     os mesmos antes e depois de `montar_base`; se não existir, continua não existindo.

**Done when**:

- [ ] Testes novos passam
- [ ] Nenhum arquivo criado dentro do repositório (`git status --short` vazio depois do gate)
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(paridade): montar a base de uma pasta de export sem tocar o banco`

---

### T13: `paridade.py gerar` grava a planilha

**What**: Função `linhas_paridade(df_m, df_e, ano_base)` que devolve as linhas da
seção "Linhas da planilha" do spec, e o subcomando `gerar`.
**Where**: `scripts/paridade.py`
**Depends on**: T12
**Reuses**: `app/paineis/*` (T5 a T10), `functools.partial`
**Requirement**: PAR-13

**Passos**:

1. Funções de formato brasileiro no script:
   - `_inteiro(v)` → `f"{int(v):,}".replace(",", ".")` (`22302` → `"22.302"`);
   - `_decimal(v, casas=2)` → `f"{v:,.{casas}f}"` com troca de `,` e `.` (`16278.684` → `"16.278,68"`);
   - `_pct(v, casas)` → `_decimal(v * 100, casas) + "%"` (`0.4144` → `"41,44%"`);
   - `None` vira texto vazio.
2. `linhas_paridade` monta a lista de dicts com as chaves
   `pagina`, `recorte`, `linha`, `indicador`, `calcsistec`, `powerbi` (`""`),
   `diferenca` (`""`), `causa` (`""`), exatamente na ordem da tabela do spec:
   - Matrículas com FIC: `resumo_matriculas(df_m, ano_base, FiltrosPainel())`
     para os 5 KPIs; `tabela_por(aplicar_filtros(df_m, FiltrosPainel()), "cidade", metricas_matriculas)`
     para as linhas por campus e o Total.
   - Matrículas sem FIC: igual, com `FiltrosPainel(incluir_fic=False)`.
   - Eficiência sem FIC: `tabela_por(aplicar_filtros(df_e, FiltrosPainel(incluir_fic=False)), "cidade", metricas_eficiencia)`;
     IEA com `_pct(v, 2)`.
   - Evasão com FIC: 4 KPIs de `resumo_evasao`; 12 linhas `Mês` de
     `evasoes_por_mes` com os nomes `janeiro` … `dezembro`; tabela por campus com
     `functools.partial(metricas_evasao, ano_base=ano_base)`, indicador
     `Evasões no ano` (inteiro) e `Taxa de Evasão Anual` (`_pct(v, 1)`).
   - Percentuais com FIC: KPI `Matrículas equivalentes` (`_decimal`, 2) e os três
     `%` com `_pct(v, 1)`; tabela por campus sobre as linhas do ano-base, com os
     3 MatEq (`_decimal`, 2) e os 3 `%` (`_pct(v, 2)`).
   Os rótulos de `indicador` são os da tabela do spec, escritos igual.
3. Subcomando `gerar`: `argparse` com `--pasta`, `--ano-base` (int) e `--saida`.
   Grave com `csv.DictWriter(..., delimiter=";")`, `encoding="utf-8-sig"`,
   `newline=""`. Se `montar_base` levantar `ValueError`, imprima a mensagem e
   saia com código 2.
4. Testes em `tests/test_paridade_script.py`:
   - as funções de formato com os exemplos do passo 1;
   - com a pasta sintética: `gerar` via `subprocess.run([sys.executable, "scripts/paridade.py", "gerar", ...], cwd=RAIZ)`
     sai com 0; o arquivo abre com `utf-8-sig`; o cabeçalho é exatamente
     `pagina;recorte;linha;indicador;calcsistec;powerbi;diferenca;causa`;
   - a sequência de `(pagina, recorte, linha)` segue a ordem do spec (confira ao
     menos: primeira linha é `Matrículas;com_fic;KPI;Cursos`, existem 12 linhas
     `Mês`, a última linha é `Percentuais Legais;com_fic;Total;% Proeja`);
   - o `calcsistec` da linha `Matrículas;com_fic;Total;Total de Matrículas` é
     igual a `_inteiro` do número de linhas de `df_m` do ano-base (use
     `montar_base` no próprio teste);
   - pasta sem `ciclos/` → código 2.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(paridade): gerar a planilha de comparacao com o power bi`

---

### T14: `paridade.py comparar` confere a planilha

**What**: Subcomando `comparar --arquivo ARQ.csv` com os códigos de saída do spec.
**Where**: `scripts/paridade.py`
**Depends on**: T13
**Reuses**: formato da planilha de T13
**Requirement**: PAR-14

**Passos**:

1. `_numero(texto)`: tira espaços e `%`, tira `.` de milhar, troca `,` por `.`,
   devolve `(float, casas_decimais)`; texto vazio ou não numérico devolve `None`.
   Exemplos: `"22.302"` → `(22302.0, 0)`; `"16.278,68"` → `(16278.68, 2)`;
   `"41,44%"` → `(41.44, 2)`; `"-"` → `None`.
2. Para cada linha com `powerbi` numérico: arredonde o `calcsistec` para as casas
   do `powerbi` e grave `diferenca = calcsistec - powerbi` no formato brasileiro
   com as mesmas casas (`0` quando zero, sem sinal negativo em zero).
3. Regrave o arquivo no mesmo formato.
4. Saída:
   - linhas com `powerbi` ausente ou não numérico > 0 → imprima
     `"Faltam N valores do Power BI."` e saia com 2;
   - senão, linhas com `diferenca` diferente de zero e `causa` vazia → imprima
     uma por linha (`pagina | recorte | linha | indicador | calcsistec | powerbi | diferenca`)
     e saia com 1;
   - senão → imprima `"Paridade conferida: nenhuma diferença sem causa."` e saia com 0.
5. Testes em `tests/test_paridade_script.py`, com planilhas pequenas escritas
   pelo próprio teste em `tmp_path`: os exemplos de `_numero`; um caso para cada
   código de saída (0, 1, 2); diferença `41,44%` contra `41,4%` com 1 casa → 0;
   causa preenchida torna a diferença aceita; a coluna `diferenca` é regravada.

**Done when**:

- [ ] Testes novos passam
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: integration
**Gate**: full

**Commit**: `feat(paridade): comparar a planilha preenchida com o power bi`

---

### T15: Roteiro da paridade no `TESTAR.md` e esqueleto do relatório

**What**: Seção "Conferir a paridade com o Power BI" no `TESTAR.md` e o arquivo
`.specs/features/mvp-2-paridade/relatorio-paridade.md` com a estrutura vazia.
**Where**: `TESTAR.md`
**Depends on**: T14
**Reuses**: nenhum
**Requirement**: PAR-15

**Passos**:

1. `TESTAR.md`, seção nova com os passos para a PI, em frases curtas:
   1. Exportar do Sistec as pastas `ciclos/` e `matriculas/` do mês.
   2. Carregar o **mesmo** export no Power BI, no mesmo dia.
   3. Rodar `python scripts/paridade.py gerar --pasta <pasta> --ano-base <ano> --saida paridade.csv`.
   4. Abrir `paridade.csv` no Excel e digitar, na coluna `powerbi`, o número que
      o Power BI mostra em cada linha, como ele aparece (`22.302`, `41,44%`).
      Célula vazia no Power BI: digite `0`.
   5. Rodar `python scripts/paridade.py comparar --arquivo paridade.csv`.
   6. Para cada diferença listada, escrever a causa na coluna `causa` depois de
      investigada (nunca antes).
2. `relatorio-paridade.md`: título; "Export usado" (pasta, data, ano-base);
   "Resumo" (total de linhas, iguais, com diferença); "Diferenças" (tabela:
   linha da planilha, CalcSISTEC, Power BI, causa, tipo = bug corrigido | regra
   aceita, commit ou aceite); "Aceite" (texto a ser assinado por Jaline com data).
3. Teste de higiene: `TESTAR.md` contém `scripts/paridade.py gerar` e
   `scripts/paridade.py comparar`.

**Done when**:

- [ ] Teste de higiene novo passa
- [ ] Gate check passes: `python -m pytest tests/test_higiene_repositorio.py -q -p no:cacheprovider`
- [ ] Test count: total anterior + novos, 0 failed

**Tests**: unit
**Gate**: quick

**Commit**: `docs(testar): roteiro de paridade com o power bi`

---

### T16: [HUMANO] A PI preenche a planilha com o export de agosto

**What**: A PI roda `gerar` sobre `Downloads/08agosto` (ano-base do export),
carrega o mesmo export no Power BI, preenche a coluna `powerbi` e salva o
arquivo em `.specs/features/mvp-2-paridade/paridade-08agosto.csv`.
**Where**: `.specs/features/mvp-2-paridade/paridade-08agosto.csv`
**Depends on**: None
**Reuses**: roteiro de T15
**Requirement**: PAR-15

**O agente executor para aqui** e avisa: "T16 é humana: a PI precisa preencher
a planilha de paridade". Ele pode rodar o `gerar` e deixar o arquivo pronto
para a PI, com commit `chore(paridade): planilha de agosto para preenchimento`.

**Done when**:

- [ ] Arquivo com a coluna `powerbi` preenchida commitado
- [ ] O total de Matrículas com FIC do CalcSISTEC é 16.832 (conferência da medição de 2026-09-24)

**Tests**: none
**Gate**: build

**Commit**: `chore(paridade): planilha de agosto preenchida pela pi`

---

### T17: Investigar cada diferença e registrar a causa

**What**: Rodar `comparar`; para cada diferença, achar a causa. Bug do
CalcSISTEC: nova tarefa de correção neste arquivo (T17a, T17b…), cada uma com
teste que reproduz a falha primeiro (Princípio I), e a linha volta a dar 0.
Regra diferente: registrar no `relatorio-paridade.md` com números e explicação,
e escrever a causa na planilha.
**Where**: `.specs/features/mvp-2-paridade/relatorio-paridade.md`
**Depends on**: T16
**Reuses**: `scripts/paridade.py`, `app/paineis/`, `app/domain/`
**Requirement**: PAR-15

**Executor recomendado**: modelo forte ou a orquestradora. É investigação
aberta. Um executor pequeno pode fazer a parte mecânica (rodar `comparar`,
listar as diferenças no relatório) e parar para a investigação.

**Done when**:

- [ ] Toda diferença tem causa no relatório e na planilha
- [ ] Toda correção de bug tem teste que falhava antes
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`

**Tests**: none
**Gate**: build

**Commit**: `docs(paridade): registrar a causa de cada diferenca`

---

### T18: [HUMANO] Jaline aceita as diferenças de regra

**What**: Jaline lê o relatório e escreve, na seção "Aceite", "Aceito as
diferenças de regra listadas" com nome e data. Depois, `comparar` sai com 0.
**Where**: `.specs/features/mvp-2-paridade/relatorio-paridade.md`
**Depends on**: T17
**Reuses**: nenhum
**Requirement**: PAR-15

**O agente executor para aqui** e avisa: "T18 é humana: falta o aceite da Jaline".

**Done when**:

- [ ] Seção "Aceite" assinada e datada
- [ ] `python scripts/paridade.py comparar --arquivo .specs/features/mvp-2-paridade/paridade-08agosto.csv` sai com 0

**Tests**: none
**Gate**: build

**Commit**: `docs(paridade): aceite das diferencas de regra`

---

### T19: Registrar a feature no `STATE.md`

**What**: Handoff da feature: commits, testes, resultado da campanha. Tirar das
"Divergências conhecidas" do `DEPLOY.md` os itens que a campanha resolveu
(exemplo de `BR-MIGRAR-007`, nomes das colunas cruas, `mapa_nomes_curso`),
citando o relatório.
**Where**: `.specs/STATE.md`
**Depends on**: T18
**Reuses**: formato dos handoffs existentes
**Requirement**: PAR-15

**Done when**:

- [ ] "Estado atual" diz que `mvp-2-paridade` está implementada e aguarda o Verifier
- [ ] `DEPLOY.md` sem os itens resolvidos pela campanha
- [ ] Gate check passes: `python -m pytest -q -p no:cacheprovider`

**Tests**: none
**Gate**: build

**Commit**: `docs(state): registrar a paridade com o power bi`

---

## Verificação (depois de T19)

Verifier independente, modelo forte. Sensor mínimo: trocar `REPROVADA` de
categoria em `CATEGORIAS_EVASAO`; pular o filtro de ano-base em `evasoes_por_mes`;
`tabela_por` somar as linhas no Total em vez de recalcular; `comparar` ignorar
`causa`; `montar_base` escrever em `app/data/sistec.db`.

---

## Phase Execution Map

```
Phase 1:  T1 → T2 → T3 → T4
Phase 2:  T5 → T6 → T7 → T8 → T9 → T10 → T11
Phase 3:  T12 → T13 → T14 → T15
Phase 4:  T16 → T17 → T18 → T19
```

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | 1 função (2 consultas) | ✅ |
| T2 | 1 constante + 1 função | ⚠️ coeso: a função usa a constante |
| T3, T4 | 1 função | ✅ |
| T5–T10 | 1 módulo novo | ✅ |
| T11 | emenda + AD + README | ⚠️ coeso: uma decisão, três registros |
| T12–T14 | 1 função/subcomando do script | ✅ |
| T15 | 1 seção + 1 esqueleto | ✅ |
| T16–T19 | campanha e registro | ✅ |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | início da fase 1 | ✅ |
| T2 | T1 | T1 → T2 | ✅ |
| T3 | T2 | T2 → T3 | ✅ |
| T4 | T3 | T3 → T4 | ✅ |
| T5 | None | início da fase 2 | ✅ |
| T6 | T5 | T5 → T6 | ✅ |
| T7 | T6 | T6 → T7 | ✅ |
| T8 | T7 | T7 → T8 | ✅ |
| T9 | T8 | T8 → T9 | ✅ |
| T10 | T9 | T9 → T10 | ✅ |
| T11 | T10 | T10 → T11 | ✅ |
| T12 | None | início da fase 3 | ✅ |
| T13 | T12 | T12 → T13 | ✅ |
| T14 | T13 | T13 → T14 | ✅ |
| T15 | T14 | T14 → T15 | ✅ |
| T16 | None | início da fase 4 | ✅ |
| T17 | T16 | T16 → T17 | ✅ |
| T18 | T17 | T17 → T18 | ✅ |
| T19 | T18 | T18 → T19 | ✅ |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | dados | integration | integration | ✅ |
| T2–T4 | domínio | unit | unit | ✅ |
| T5–T10 | painéis | unit | unit | ✅ |
| T11 | documentação | unit (higiene) | unit | ✅ |
| T12–T14 | script | integration | integration | ✅ |
| T15 | documentação | unit (higiene) | unit | ✅ |
| T16–T19 | tarefas humanas e relatório | none | none | ✅ |
