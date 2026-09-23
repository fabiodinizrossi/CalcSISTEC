# Prévia das páginas públicas antes de salvar — Especificação

## Problem Statement

Após ler as pastas de CSVs, a tela administrativa mostra contagens e uma amostra de ciclos. A administradora ainda não consegue conferir os indicadores, tabelas e filtros das quatro páginas públicas com o conjunto que pretende salvar. A publicação pode, portanto, apresentar números ou recortes inesperados que não foram vistos na conferência.

## Goals

- [ ] Após a consolidação válida dos CSVs, permitir a conferência das quatro páginas públicas completas e interativas antes de salvar a versão interna.
- [ ] Garantir que a prévia represente o conjunto efetivo que seria salvo, inclusive os campi preservados, sem alterar a versão interna ou a publicada durante a conferência.
- [ ] Manter o acesso à prévia restrito à sessão administrativa dona da atualização.

## Out of Scope

| Item | Motivo |
| --- | --- |
| Alterar regras de cálculo, indicadores ou filtros públicos | A prévia reutiliza o comportamento das páginas existentes; divergências de cálculo são outro trabalho. |
| Mudar a coleta direta do Sistec | Esta entrega começa no envio das duas pastas de CSVs. |
| Publicação automática, agendamento ou comparação lado a lado com a versão publicada | A decisão de salvar e publicar continua manual. |
| Guardar os CSVs brutos ou criar uma versão publicada temporária | A conferência deve respeitar a privacidade e o ciclo de versões existentes. |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Momento da prévia | Depois da leitura e consolidação válida dos CSVs, antes de **Salvar na versão interna** | A usuária escolheu conferir as páginas antes de qualquer gravação da nova versão. | y |
| Profundidade da prévia | Quatro páginas completas, com os mesmos filtros, indicadores e tabelas interativos do painel público | A usuária escolheu páginas completas e interativas. | y |
| Conjunto exibido | Resultado final que o comando Salvar gravaria: novos dados, campi preservados, fatores e ano-base aplicáveis | Mostrar só as linhas recém-lidas ocultaria o efeito real da publicação. | y |
| Navegação | Links para as quatro páginas dentro da área administrativa, com aviso visível **Prévia não publicada** e retorno a **Atualizar dados** | Deixa claro o caráter privado da conferência e permite percorrer as telas. | y |
| Vida da prévia | Disponível enquanto a execução do envio estiver pendente; desaparece após salvar, descartar ou perder essa execução | Segue a máquina de estados existente, sem reter outra cópia dos dados. | y |
| Conferência das quatro páginas | As quatro ficam acessíveis, mas Salvar não exige que a administradora clique em todas; uma falha de renderização conhecida bloqueia Salvar | O botão Salvar já é uma decisão explícita; impor quatro cliques mediria navegação, não a qualidade da conferência. | y |


**Open questions:** none — especificação aprovada pela usuária em 2026-09-23.

## User Stories

### P1: Abrir as páginas após ler os CSVs ⭐ MVP

**User Story**: Como administradora, quero abrir as páginas do painel com os dados recém-carregados para conferir o resultado antes de salvar.

**Why P1**: É o benefício central desta entrega.

**Acceptance Criteria**:

1. WHEN o envio das pastas de ciclos e matrículas chegar ao estado `previa` com consolidação válida THEN the system SHALL oferecer, na área administrativa, acesso à prévia de Matrículas (`/`), Eficiência Acadêmica (`/eficiencia`), Taxa de Evasão Anual (`/evasao`) e Percentuais Legais (`/percentuais-legais`).
2. WHEN a administradora abrir uma dessas páginas de prévia THEN the system SHALL mostrar a identificação **Prévia não publicada**, a página escolhida e um caminho de volta para **Atualizar dados**.
3. WHILE a prévia do envio estiver aberta the system SHALL manter as ações existentes **Salvar na versão interna** e **Descartar** disponíveis no fluxo administrativo.
4. WHEN a administradora apenas abrir ou navegar pela prévia THEN the system SHALL deixar `rev_interna`, `rev_publicada` e as tabelas internas e públicas inalteradas.

**Independent Test**: Enviar CSVs válidos, abrir cada uma das quatro páginas antes de Salvar e verificar que as revisões e os dados persistidos não mudaram.

### P1: Conferir o resultado que seria publicado ⭐ MVP

**User Story**: Como administradora, quero ver os mesmos indicadores, tabelas e filtros do painel público aplicados ao resultado do envio para identificar erros antes de gravar.

**Why P1**: Uma amostra de linhas não revela o efeito final nos indicadores.

**Acceptance Criteria**:

1. WHILE a prévia estiver válida the system SHALL calcular os indicadores e as tabelas das quatro páginas a partir do mesmo conjunto efetivo que **Salvar na versão interna** gravaria para aquele envio, com o mesmo ano-base e fatores aplicáveis.
2. WHEN a administradora alterar um filtro, o eixo ou a opção FIC na prévia THEN the system SHALL aplicar a mesma regra e produzir os mesmos valores que a respectiva página pública produziria se esse conjunto estivesse publicado.
3. WHEN o envio preservar um campus ausente THEN the system SHALL incluir na prévia os dados preservados desse campus exatamente como apareceriam na versão interna após Salvar.
4. WHILE a prévia estiver visível the system SHALL mostrar os avisos já apurados para campi preservados, unidades não cadastradas, matrículas órfãs e arquivos ignorados, quando houver.
5. IF ainda não existir versão publicada THEN the system SHALL renderizar as quatro páginas de prévia com o conjunto válido do envio, sem exibir a mensagem pública **Ainda não há dados publicados.**
6. WHILE a prévia estiver visível the system SHALL omitir o carimbo **Atualizado em** da versão publicada e identificar os dados como não publicados.

**Independent Test**: Para CSVs sintéticos, conferir KPIs, linhas e filtros das quatro páginas antes de Salvar; depois salvar e publicar em banco isolado e conferir igualdade dos mesmos resultados, inclusive com um campus preservado.

### P1: Restringir e encerrar a conferência ⭐ MVP

**User Story**: Como administradora, quero que a prévia fique privada e só exista enquanto o envio está pendente, para não expor dados não publicados nem confundir versões.

**Why P1**: A prévia antecede a decisão de publicação e carrega dados ainda não aprovados.

**Acceptance Criteria**:

1. IF uma sessão sem autenticação administrativa pedir uma página de prévia THEN the system SHALL redirecionar para `/admin/login` sem entregar seus dados.
2. IF uma sessão diferente da dona da execução pedir dados ou callbacks da prévia THEN the system SHALL negar o acesso sem entregar indicadores, tabelas ou linhas do envio.
3. WHEN a administradora salvar ou descartar a execução THEN the system SHALL encerrar o acesso à prévia daquela execução; uma URL antiga deve mostrar **Prévia indisponível** e voltar a **Atualizar dados**.
4. IF a consolidação dos CSVs falhar THEN the system SHALL manter o erro do envio visível na tela **Atualizar dados** e não oferecer prévia para esse envio.
5. IF o conjunto ou a configuração usados para calcular a prévia mudarem antes de Salvar THEN the system SHALL impedir que a administradora salve um resultado diferente do conferido e pedir nova conferência.
6. WHILE a prévia estiver pendente the system SHALL manter as páginas públicas normais ligadas exclusivamente à versão publicada.
7. The system SHALL excluir da prévia e de suas respostas qualquer coluna pessoal descartada na ingestão, inclusive nome, CPF, e-mail e data de nascimento de estudantes.

**Independent Test**: Verificar acesso com e sem sessão, uso de URL antiga após Salvar/Descartar, falha de CSV e isolamento entre prévia e páginas públicas.

## Edge Cases

- IF o envio válido não produzir linhas para um filtro selecionado THEN the system SHALL mostrar o mesmo estado **Sem dados para o eixo selecionado.** da página pública correspondente.
- IF uma página da prévia falhar ao calcular ou renderizar THEN the system SHALL identificar a página com falha e impedir Salvar até que a prévia completa possa ser conferida ou o envio seja descartado.
- WHEN a administradora recarregar uma página de prévia com a execução ainda pendente THEN the system SHALL manter a conferência do mesmo envio sem solicitar novo upload dos CSVs.
- IF a execução pendente deixar de existir após reinício do processo THEN the system SHALL mostrar **Prévia indisponível** sem usar a versão pública como substituta silenciosa.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| PVP-01 | P1: Abrir as páginas após ler os CSVs | Design | Pending |
| PVP-02 | P1: Abrir as páginas após ler os CSVs | Design | Pending |
| PVP-03 | P1: Abrir as páginas após ler os CSVs | Design | Pending |
| PVP-04 | P1: Conferir o resultado que seria publicado | Design | Pending |
| PVP-05 | P1: Conferir o resultado que seria publicado | Design | Pending |
| PVP-06 | P1: Conferir o resultado que seria publicado | Design | Pending |
| PVP-07 | P1: Restringir e encerrar a conferência | Design | Pending |
| PVP-08 | P1: Restringir e encerrar a conferência | Design | Pending |
| PVP-09 | P1: Restringir e encerrar a conferência | Design | Pending |
| PVP-10 | P1: Restringir e encerrar a conferência | Design | Pending |

**Detalhamento:** PVP-01 = acesso às quatro páginas (P1.1 AC 1); PVP-02 = identificação, retorno e ações (P1.1 AC 2–3); PVP-03 = leitura sem escrita (P1.1 AC 4); PVP-04 = paridade de dados e cálculos (P1.2 AC 1–3); PVP-05 = avisos e estado sem publicação (P1.2 AC 4–6); PVP-06 = estados vazios (Edge Case 1); PVP-07 = autenticação e posse da execução (P1.3 AC 1–2); PVP-08 = encerramento e recarga da prévia (P1.3 AC 3 e Edge Cases 3–4); PVP-09 = falha de CSV e de página (P1.3 AC 4 e Edge Case 2); PVP-10 = invalidação, isolamento público e privacidade (P1.3 AC 5–7).

**Coverage:** 10 requisitos, 0 mapeados a tarefas nesta etapa, 10 aguardando design.

## Implicit-Requirement Dimensions

| Dimensão | Resolução nesta feature |
| --- | --- |
| Validação de entrada e limites | Reusa a validação e o limite de 500 MB do envio; esta feature não aceita novo formato de entrada. |
| Falha e falha parcial | PVP-09: CSV inválido ou página com erro não autoriza salvar resultado não conferido. |
| Repetição e duplicatas | Reabrir/recarregar a prévia pendente não grava nem duplica registros (PVP-03, PVP-08). |
| Autorização e taxa | PVP-07 exige sessão e posse da execução; limite de taxa adicional N/A porque a feature não cria nova escrita nem serviço externo. |
| Concorrência e ordenação | PVP-10 invalida conferência se o conjunto ou sua configuração mudar antes de Salvar; a exclusão mútua do envio existente continua. |
| Ciclo de vida dos dados | PVP-08 encerra a prévia com a execução; CSVs brutos continuam descartados após a leitura. |
| Observabilidade | A conferência mostra erros e avisos (PVP-05, PVP-09); novo registro de histórico por navegação N/A porque é leitura. |
| Dependência externa | N/A: após a leitura dos CSVs, esta feature não chama o Sistec nem outro serviço. |
| Integridade de estados | PVP-01 exige `previa`; PVP-08 encerra acesso após Salvar/Descartar; PVP-10 isola a versão publicada. |

## Project Rules & References

- Princípio I: os resultados da prévia devem ser iguais aos que a publicação exibirá para os mesmos dados e filtros; verificar casos vazios/NaN/data nula de `RISK-002`. Regras `BR-MIGRAR-*` não mudam aqui.
- Princípio II: a lógica de domínio continua pura; leitura e preparação de dados ficam na camada de dados, apresentação nas páginas e componentes.
- Princípio III e `RISK-008`: nenhum CSV bruto ou dado pessoal persistido ou exposto na prévia.
- Princípio IV: testes `pytest` de paridade, acesso, ciclo de vida e falhas serão gate da implementação.
- Princípio V: ano-base, fatores, campi e identidade institucional continuam vindos da configuração.
- Princípio VI: a coleta do Sistec permanece na sessão do navegador da usuária; esta feature não a modifica.
- Princípio VII, `RN-20`, `RN-21`, `RN-22`, `RN-27` e `RISK-009`: a prévia usa a versão candidata antes de Salvar, preserva campi conforme a regra existente e mantém a publicação manual, autenticada e reversível.
- `AD-001` a `AD-005`: a navegação administrativa usa o shell compartilhado e o gov.br DS, inclusive em tela móvel.
- O fluxo de uso em `README.md` e `TESTAR.md` precisará refletir a nova etapa quando a feature for implementada.

## Success Criteria

- [ ] Os quatro caminhos de prévia carregam antes de Salvar e permitem usar os filtros, eixos e tabelas existentes.
- [ ] Para os mesmos dados e filtros, os resultados da prévia são iguais aos das quatro páginas após Salvar e Publicar em banco de teste.
- [ ] Abrir, recarregar e descartar a prévia não altera revisões nem tabelas internas ou públicas.
- [ ] Nenhuma requisição sem autorização acessa dados da prévia; URLs antigas deixam de funcionar após Salvar/Descartar.
- [ ] `pytest tests/` passa, inclusive os casos de campus preservado, ausência de publicação e falha de renderização.
