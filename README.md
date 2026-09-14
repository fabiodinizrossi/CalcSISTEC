# Painel SISTEC (Dash) - Projeto completo (todas as páginas)

## Estrutura

```
app/
  data/        # BC-01: ingestão, validação e correção de status (Tarefa 05)
  domain/      # BC-02/BC-03: regras de negócio puras (Tarefas 04, 06, 07)
  pages/       # 1 arquivo por página (Tarefa 09)
  components/  # UI reutilizável (Tarefa 09)
  assets/      # CSS
  app.py       # app Dash + callbacks
run.py         # entry point
```

Ver `_reversa_sdd/migration/` e `_reversa_sdd/reconstruction-plan.md` (no repositório principal) para as specs completas desta migração.

## Rodar local
```bash
pip install -r requirements.txt
python run.py
```

## Rodar na EC2 (modo teste)
O `app.py` já está configurado para:
- host 0.0.0.0
- port 8050
- debug False

Libere a porta 8050 no Security Group (idealmente restrita ao seu IP).

## Upload
Envie um Excel com abas:
- matriculas
- ciclos

## Observação sobre métricas
Algumas métricas (ex.: Matrículas equivalentes) estão implementadas como *proxy*:
- `EQ_MATRICULA = NU_CARGA_HORARIA / CARGA_TOTAL` (quando disponível; senão 1.0)
- `MatEq = soma(EQ_MATRICULA)`

Isso pode ser ajustado depois conforme a regra oficial do seu Power BI.
