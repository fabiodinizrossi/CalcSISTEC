# Relatório de Validação de Paridade — Tarefa 11

> A partir de `_reversa_sdd/migration/parity_specs.md` e
> `_reversa_sdd/migration/parity_tests/*.feature` (PT-001 a PT-007).
> Suíte executável: `tests/test_parity_dominio.py` (39 testes, `pytest`).

## Como rodar

```bash
pip install pytest
pytest tests/test_parity_dominio.py -v
```

**Resultado atual: 39/39 passam.**

## Escopo coberto

- PT-001 a PT-007 (fluxos de domínio): cobertos integralmente por
  `tests/test_parity_dominio.py`.
- `parity_tests/screens/*.feature` (5 arquivos, contrato de tela): **não**
  convertidos em suíte automatizada dedicada nesta tarefa — validados
  manualmente via smoke test das 5 páginas (Tarefa 09): todas retornam HTTP
  200 e todos os callbacks executam sem erro com dados reais do pipeline de
  ingestão. Uma suíte de contrato de tela real (Selenium/Playwright,
  verificando hierarquia de componentes e estados idle/loading/error/success)
  fica como trabalho futuro.
- Não há teste de "idempotência" automatizado para reprocessar o mesmo
  arquivo duas vezes byte-a-byte (`PT-001`, cenário `@idempotencia`) — as
  funções são puras por construção (T-01 a T-08 sem estado), mas o teste
  específico de bit-a-bit não foi escrito.
- Paridade **numérica real** contra o Power BI (o critério primário de
  `parity_specs.md`, "divergência de cálculo = 0% ... sobre o dataset do mês
  corrente") não foi executada — não há acesso a uma planilha real do
  Sistec/PNP nem ao Power BI publicado neste ambiente. A suíte valida a
  **lógica** das regras `BR-MIGRAR-*` com dados sintéticos, não a paridade
  contra uma extração real. Isso precisa ser feito manualmente pela usuária
  antes do cutover, conforme `CUTOVER.md`.

## Divergências encontradas e corrigidas nesta tarefa

Ao escrever os testes a partir dos cenários Gherkin, encontrei 6 divergências
reais entre o que as Tarefas 02-09 haviam implementado e o que as specs
exigem. Todas foram corrigidas nesta tarefa:

| # | Onde | Divergência | Correção |
|---|---|---|---|
| 1 | `app/domain/shared.COLUNA_POR_EIXO` (Tarefa 06) | Eixo "tipo_curso" mapeava para `tipo_curso_pnp`; eixo "oferta" não tinha coluna nenhuma | Corrigido para `subtipo_curso`; adicionada coluna `tipo_oferta_curso` ao schema (`app/data/schema.py`), ingestão (`ingest.py`) e consulta (`consulta.py`) |
| 2 | `app/domain/percentuais_legais.recorte_professores` (Tarefa 07) | Exclusão por igualdade exata (`.isin()`) nunca casaria com "TÉCNICO EM CERVEJEIRO" | Trocado para `.str.contains()` (substring) |
| 3 | `app/domain/eficiencia.eh_retido` (Tarefa 07) | Comparação de datas (`ano_base > prazo+1`, estrita) sempre `False` no limite exato que o próprio grão de eficiência seleciona — deixava `EM_CURSO` fora de todos os 3 buckets | Simplificado: dentro da base já filtrada pelo grão (T-08), `EM_CURSO` é sempre Retido por construção — não precisa (nem deveria) recalcular datas |
| 4 | `app/data/transform.STATUS_MATRICULA_VALIDOS` (Tarefa 03) | Domínio fechado provisório (`CONCLUINTE`, `EVADIDO`, `TRANCADO`, `TRANSFERIDO`) não batia com o `StatusMatricula` canônico usado por `shared.py`/`eficiencia.py` — um status válido no upload podia não pertencer a nenhum bucket de eficiência | Corrigido para o domínio de 8+2 valores (variantes de gênero) realmente consumido pelo resto do sistema |
| 5 | Toggle FIC (`app/pages/matriculas.py`, `evasao.py`, Tarefa 09) | Filtrava por `tipo_curso_pnp != "QUALIFICAÇÃO PROFISSIONAL"`, excluindo também Mulheres Mil (deveria permanecer visível) | Nova coluna `categoria_origem_curso` (tipo cru, antes do colapso de BR-MIGRAR-017) preservada na ingestão; nova função `app/domain/matriculas.filtrar_fic()` usada pelas 3 páginas com toggle |
| 6 | `app/pages/eficiencia.py` (Tarefa 09) | Toggle FIC calculava `filtros.incluir_fic` mas nunca aplicava nenhum filtro ao `df` — o controle não tinha efeito nenhum | Corrigido para chamar `filtrar_fic()` antes de calcular o IEA |

## Divergências conhecidas e não resolvidas (não bloqueantes, para revisão humana)

1. **Exemplo numérico de `BR-MIGRAR-007`** (`target_business_rules.md` e
   `parity_tests/03-matricula-equivalente.feature`): o texto diz "CH=200,
   FEC=1.10, Mat=30 → 9,075 = (200/800) × 1,10 × 30", mas essa própria
   fórmula calcula 8.25, não 9.075. A suíte de testes valida 8.25 (a fórmula
   literal da regra), não o número do exemplo. **Precisa ser confirmado com
   a usuária ou contra `medidas-dax-pnp/requirements.md`/o Power BI real
   antes do cutover** — se o número certo for 9.075, a fórmula documentada
   em `BR-MIGRAR-007` está incompleta ou incorreta, não a implementação.
2. **Nomes de colunas cruas do upload** (`app/data/validators.py`): ainda são
   uma convenção provisória (`STATUS_MATRICULA_SISTEC`, `CÓDIGO DO
   PORTFÓLIO`, `OFERTA`, etc.), nunca confirmada contra uma extração real do
   Sistec/PNP. Validar no primeiro upload de teste real.
3. **`mapa_nomes_curso`** (`/admin/upload`, BR-MIGRAR-017): ainda é um dict
   vazio — a tabela real de ~40 mapeamentos históricos não foi fornecida.
4. **`AGG-IndicadoresRegulatorios.aviso_filtro_proeja`** (BR-MIGRAR-026,
   página Percentuais Legais): aproximado por uma mensagem estática, não pela
   lógica real de detecção de distorção.
5. **Botão de retorno à capa** (`BR-HUMANA-007`): cumprido pelo link "Início"
   já presente na navegação lateral, não por um elemento dedicado.
6. **Tokens gov.br**: ainda são os valores 🟡 (não confirmados) de
   `tokens-derived.md`.

## Conclusão

A suíte de paridade de domínio passa 100% (39/39) após as 6 correções acima.
Isso satisfaz o critério de bloqueio de `parity_specs.md` para os fluxos
cobertos, mas **não substitui** a validação de paridade numérica real contra
o Power BI com uma extração de dados de produção — essa etapa, e as 6
divergências não resolvidas acima, precisam de decisão/validação humana
antes do cutover (ver `CUTOVER.md`).
