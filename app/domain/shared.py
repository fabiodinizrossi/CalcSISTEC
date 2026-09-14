"""BC-02 (Núcleo de Matrículas, shared kernel): eh_evadido(), matricula_equivalente(), eixo dinâmico.

Contrato de domínio (filtros ativos, ordem de dependência entre módulos) definido na
Tarefa 04. Funções deste módulo implementadas na Tarefa 06, a partir de
`_reversa_sdd/migration/target_architecture.md` (seção BC-02),
`_reversa_sdd/migration/target_domain_model.md` e
`_reversa_sdd/migration/target_business_rules.md` (BR-MIGRAR-005, 014, 019, 020).

Paradigma alvo (`paradigm_decision.md`): procedural rico, estilo funcional leve —
cada função pura, recebendo os filtros ativos como parâmetro explícito, sem estado global.
"""
