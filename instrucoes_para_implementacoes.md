# Estado técnico — Iteração 2

Fonte mantida: README.md, docs/Especificacao_ValidaHoras_Iteracao_2.pdf e docs/VALIDACAO.md.

Implementado: autenticação por perfil; submissão com arquivo validado e protocolo; OCR e comparação com regras; aprovação automática ou revisão; fila e decisões com justificativa; correção/reenvio com histórico; versões imutáveis de regras; consulta própria com busca, filtro e paginação local; download autorizado e integridade SHA-256.

A migração 20261104_0002 vincula cada submissão ao documento e ao retrato dos dados usados. O backfill usa os dados disponíveis no banco; não recupera versões históricas que já tenham sido sobrescritas antes da atualização. Reenvios futuros preservam os dados e documentos de cada rodada.

Futuro: integração acadêmica, cadastro administrativo completo de cursos/usuários, relatórios, processamento de OCR em fila, paginação de servidor, auditoria operacional e validação para produção. Esses itens não são apresentados como entregues nesta versão.
