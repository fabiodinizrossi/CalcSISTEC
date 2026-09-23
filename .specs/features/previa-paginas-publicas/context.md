# Contexto da prévia das páginas públicas

**Gathered:** 2026-09-23
**Spec:** `.specs/features/previa-paginas-publicas/spec.md`
**Status:** Spec aprovada; design redigido e aguardando aprovação

## Feature Boundary

Após ler e consolidar as duas pastas de CSVs, a administradora confere as quatro páginas públicas completas antes de salvar a versão interna. A publicação permanece uma ação separada.

## Implementation Decisions

### Momento da conferência

- A prévia aparece logo após a leitura e consolidação dos CSVs, antes de **Salvar na versão interna**.
- A amostra de ciclos existente não substitui a prévia das páginas.

### Experiência da prévia

- As quatro páginas são completas e interativas, com filtros, indicadores e tabelas funcionando como no painel público.

### Arquitetura escolhida

- O conjunto candidato fica apenas em memória, vinculado à execução administrativa.
- A prévia compartilha as quatro páginas Dash e usa uma fonte de dados privada por execução.

### Agent's Discretion

- Nenhuma área foi delegada explicitamente pela usuária.

### Declined / Undiscussed Gray Areas → Assumptions

- O conjunto exibido, a navegação e a duração da prévia foram aprovados na tabela de premissas de `spec.md`.

## Specific References

- A usuária pediu a prévia das páginas que ficarão públicas, dentro da área administrativa, após os CSVs serem lidos.
- Escolhas confirmadas na conversa: antes de Salvar; quatro páginas completas e interativas.

## Deferred Ideas

- Prévia da coleta direta do Sistec e comparação visual entre versões ficam fora desta feature.
