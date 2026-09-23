# Orientações do CalcSISTEC

- Para SDD, use `tlc-spec-driven` (instalada em `.claude/skills/tlc-spec-driven/`).
- Antes de planejar ou implementar uma feature, leia `.specs/PROJECT_RULES.md` e
  `.specs/STATE.md`.
- Registre requisitos, decisões, tarefas e validação em `.specs/`, conforme a
  complexidade da feature e o fluxo da skill.
- O Spec Kit foi arquivado em `APAGAR/` para revisão local; não crie novos
  artefatos em `.specify/`.
- Após testes internos, remova os diretórios temporários que criou. Use o
  diretório temporário do sistema sempre que possível; nunca deixe `.test-*`,
  `.pytest_cache/` ou `.verifier-scratch-*` no repositório.
