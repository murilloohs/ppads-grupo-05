# Estado técnico - ValidaHoras / A3

Atualizado em 30/09/2026 após inspeção do código e execução local.

## Funcional nesta iteração

- Login JWT e autorização por perfil; aluno só lista/manipula atividades próprias.
- Cadastro de atividade, instituição promotora, período estruturado, validação de datas e horas decimais.
- Upload PDF/JPG/PNG com MIME, tamanho máximo e SHA-256 (integridade completa ainda pendente).
- Revisão no frontend antes de iniciar criação/upload/submissão.
- Submissão obrigatoriamente com documento; bloqueio de repetição e lock da atividade.
- Protocolo único e primeiro StatusHistory gravados na mesma transação.
- Resumo e listagem de atividades com protocolo/status; distinção entre reprovação e correção.

## Arquitetura

Submissão: controller activities -> SubmissionService -> SubmissionRepository -> models/SQLAlchemy -> PostgreSQL.
O restante de auth/activities ainda contém acesso ORM legado. Não ampliar esse padrão para novas features.

## Banco

Sem novas tabelas/colunas. Corrigido bootstrap dos enums na migration inicial: postgresql.ENUM(create_type=False), preservando criação explícita checkfirst. Esse reparo permite instalação nova sem alterar schema nem apagar dados. A API aplica Alembic no entrypoint.

## Pendências reais

CRUD de cursos/usuários; integridade completa e download autorizado de arquivos; detalhes e histórico no frontend; seleção/versionamento funcional de regras; OCR/análise automática; fila/decisão do avaliador; administração funcional. A existência dos models não equivale a implementação.

## Testes

`docker compose exec api pytest -q`: testes básicos e integração PostgreSQL com rollback.
`docker compose exec api ruff check .`: lint.
`cd frontend; npm run lint; npm run build`: frontend.

Arquivos de evidência e material acadêmico em ../A3. Consulte AGENTS.md para regras completas e sua seção de atualização A3.
