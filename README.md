# ValidaHoras - Backend

Base inicial do backend do **ValidaHoras**, API em Python para cadastro e validação de atividades complementares.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2
- PostgreSQL 17
- Alembic
- Docker + Docker Compose
- Pytest

## Arquitetura

O projeto segue uma separação MVC adaptada para API REST:

- **Model**: `app/models` — entidades e relacionamentos de banco.
- **Controller**: `app/controllers` — endpoints HTTP e orquestração da requisição.
- **View**: respostas JSON documentadas por schemas Pydantic (`app/schemas`); o React será a camada visual no frontend.
- **Service**: `app/services` — regras de negócio.
- **Repository**: `app/repositories` — acesso ao banco, evitando SQL/ORM dentro dos controllers.

## Subir o projeto

1. Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Suba os containers:

```bash
docker compose up --build -d
```

3. O container da API executa automaticamente:

```bash
alembic upgrade head
```

4. Acesse:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Banco

PostgreSQL local via Docker:

- host a partir da máquina: `localhost`
- porta: `5432`
- database: `validahoras`
- usuário: `validahoras`
- senha: `validahoras`

As credenciais são somente para desenvolvimento e podem ser alteradas no `.env`.

## Entidades iniciais

A migration inicial já cria:

- instituições
- cursos
- usuários e perfis
- atividades complementares
- documentos/certificados
- solicitações/protocolos
- regras de validação versionadas
- análises automáticas
- revisões manuais
- histórico de status

Essa estrutura cobre a fundação das issues 13–20 e deixa os pontos de extensão para OCR/análise automática das issues seguintes.

## Comandos úteis

```bash
make up
make logs
make migrate
make test
make lint
```

Sem `make`:

```bash
docker compose exec api pytest -q
docker compose exec api alembic upgrade head
docker compose exec api ruff check .
```

## Próxima sequência sugerida

1. autenticação JWT e autorização por perfil;
2. CRUD de instituições/cursos (admin);
3. cadastro de atividade complementar;
4. upload seguro de certificado;
5. protocolo e histórico;
6. regras de validação;
7. OCR;
8. análise automática;
9. fila e decisão manual.
