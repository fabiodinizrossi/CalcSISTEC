# Painel SISTEC (Dash) - Projeto completo (todas as páginas)

## Rodar local
```bash
pip install -r requirements.txt
python app.py
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
