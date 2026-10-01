# ValidaHoras

Projeto de Prática Profissional em ADS — Grupo 05.

Sistema para registrar, validar e acompanhar horas de atividades acadêmicas e profissionais.

## Backend

Base inicial do backend do **ValidaHoras**, API em Python para cadastro e validação de atividades complementares.

## Documentação e protótipo

- [Documento inicial (Aplicando conhecimento 1)](docs/A1_ValidaHoras_final.pdf)
- [Casos de uso revisados (Aplicando conhecimento 2)](docs/ValidaHoras_casos_de_uso_revisados.pdf)
- [Casos de uso revisados em ABNT](docs/ValidaHoras_casos_de_uso_revisados_ABNT.pdf)
- [Diagramas](imgs/)
- [Protótipo no Figma](https://www.figma.com/design/7WHqp3AJq0AFlGsp2WrcxN/ValidaHoras---Prot%C3%B3tipo-UC-Revisados?node-id=0-1&p=f&t=9O4KOcbW62qE36mJ-0)

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
- **View**: respostas JSON documentadas por schemas Pydantic (`app/schemas`); o React é a camada visual do frontend.
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

## Testar API localmente

Para facilitar os testes no Swagger, a API possui urls temporárias para criar usuários de teste:

1. Acesse `http://localhost:8000/docs`.
2. Execute `POST /api/v1/auth/temp-create-admin` para criar o Administrador.
3. Execute `POST /api/v1/auth/temp-create-student` para criar o Aluno.

**Credenciais criadas para teste:**
* **Administrador:**
  * E-mail: `admin@validahoras.com`
  * Senha: `senha123`
* **Aluno:**
  * E-mail: `aluno@validahoras.com`
  * Senha: `senha123`
* **Avaliador:**
  * E-mail: `avaliador@validahoras.com`
  * Senha: `senha123`

4. Clique no botão "Authorize" no topo do Swagger, coloque o email em "username" e a senha em "password" e clique em "Authorize" para conseguir testar todas as urls protegidas.

## Frontend

O frontend foi desenvolvido em React. Para rodar a interface após subir os containers do backend, siga estes passos em um novo terminal:

1. Acesse o diretório do frontend:
```bash
cd frontend
```

2. Instale as dependências:
```bash
npm install
```

3. Inicie o servidor de desenvolvimento:
```bash
npm run dev
```

4. Acesse no navegador: `http://localhost:5173`

> **Aviso:** O frontend exige que a API (`localhost:8000`) esteja rodando simultaneamente para validar o login, armazenar os tokens JWT e exibir os dados reais vindos do banco de dados nos dashboards.

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

## Iteração 1 - preparação A3

Fluxo implementado e testado: login do aluno, atividade com instituição/datas/horas decimais, upload, revisão antes do envio, protocolo, histórico inicial no banco e lista de solicitações/status. A conta local de aluno é `aluno@validahoras.com / senha123`.

A interface possui `/login`, `/dashboard`, `/nova-atividade`, `/sucesso` e `/minhas-solicitacoes`. Use o inicializador `../A3/Preparacao_Gravacao/Iniciar_ValidaHoras.ps1`, ou siga os comandos anteriores. Se já existir `.env`, preserve-o.

Não há pipeline OCR, decisão automática, revisão humana funcional, administração de regras, detalhes/download ou linha do tempo no frontend. As telas de avaliador e administrador permanecem placeholders.

A migration inicial recebeu uma correção de bootstrap para evitar criação duplicada de enums PostgreSQL. Não houve mudança do schema. Os testes de integração exigem PostgreSQL migrado e usam rollback para preservar os dados existentes.

Entrega e guia em `../A3`; nenhum vídeo foi produzido nem publicado.
