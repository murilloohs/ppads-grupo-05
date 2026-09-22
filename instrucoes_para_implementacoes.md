# Implementação do Backend — ValidaHoras

Este documento descreve o estado atual da implementação do backend do **ValidaHoras**, explicando o que já existe, a responsabilidade de cada parte, os relacionamentos entre as entidades e o que ainda precisa ser desenvolvido.

> **Importante:** este arquivo deve ser atualizado sempre que uma implementação alterar a arquitetura, o banco de dados, os relacionamentos ou uma regra de negócio relevante.

---

## 1. Objetivo desta documentação

O `README.md` continua sendo a porta de entrada do projeto e explica como executar a aplicação.

Este documento tem outro objetivo: permitir que qualquer integrante da equipe entenda rapidamente:

- o que já foi criado;
- o que está apenas preparado para uso futuro;
- como a arquitetura foi organizada;
- como as entidades se relacionam;
- quais regras de negócio já foram definidas;
- o que ainda precisa ser implementado;
- qual padrão seguir ao criar novas funcionalidades.

---

## 2. Estado atual do backend

### Implementado

Atualmente a base do backend possui:

- Python 3.13;
- FastAPI;
- PostgreSQL 17;
- SQLAlchemy 2;
- Alembic;
- Docker e Docker Compose;
- configuração por `.env`;
- CORS configurado para o futuro frontend React;
- estrutura MVC adaptada para API REST;
- camada de `services`;
- camada de `repositories`;
- models iniciais do domínio;
- migration inicial do banco;
- estrutura inicial para autenticação JWT;
- estrutura inicial para upload de arquivos;
- health check da aplicação e do banco;
- CRUD inicial de instituições:
  - criar instituição;
  - listar instituições;
- teste básico da rota raiz.

### Preparado, mas ainda não implementado funcionalmente

As estruturas de banco/model já existem, porém ainda não existem fluxos completos, endpoints, services ou testes para:

- usuários;
- login;
- autorização por perfil;
- cursos;
- atividades complementares;
- documentos comprobatórios;
- submissões/protocolos;
- regras de validação;
- OCR;
- análise automática;
- revisão manual;
- histórico de status.

A existência de uma tabela ou model **não significa que a funcionalidade esteja pronta**.

---

## 3. Arquitetura adotada

O projeto utiliza uma separação MVC adaptada para API REST, complementada pelas camadas `Service` e `Repository`.

Fluxo esperado:

```text
Frontend React
      |
      v
Controller
      |
      v
Service
      |
      v
Repository
      |
      v
Model / SQLAlchemy
      |
      v
PostgreSQL
```

### `app/controllers`

Responsável pela camada HTTP.

Deve:

- receber requisições;
- declarar rotas;
- receber dados já validados pelos schemas;
- chamar a camada de serviço;
- devolver respostas HTTP.

Não deve conter consultas diretas ao banco nem regras de negócio complexas.

### `app/services`

Responsável pelas regras de negócio.

Exemplos:

- verificar se uma solicitação pode ser submetida;
- impedir submissão sem comprovante;
- selecionar a regra de validação aplicável;
- decidir quando enviar uma solicitação para revisão manual;
- validar permissões relacionadas ao fluxo.

### `app/repositories`

Responsável pelo acesso ao banco.

Deve centralizar operações SQLAlchemy, por exemplo:

- `select`;
- `insert`;
- `update`;
- `delete`;
- consultas específicas.

Controllers não devem acessar o ORM diretamente.

### `app/models`

Representa as entidades persistidas no PostgreSQL.

Os models utilizam SQLAlchemy e definem:

- tabelas;
- campos;
- chaves estrangeiras;
- relacionamentos.

### `app/schemas`

Representa os contratos de entrada e saída da API utilizando Pydantic.

Exemplos:

- dados necessários para criar uma instituição;
- resposta retornada ao frontend;
- payload futuro de login;
- payload futuro de atividade complementar.

### `app/core`

Configurações compartilhadas da aplicação.

Atualmente contém:

- leitura do `.env`;
- configurações gerais;
- chave JWT;
- tempo de expiração do token;
- hashing e verificação de senha;
- criação inicial de access token.

### `app/database`

Responsável pela conexão SQLAlchemy com o banco e pelo gerenciamento da sessão.

---

## 4. Docker

O ambiente local foi preparado para que todos os integrantes utilizem a mesma infraestrutura.

O `docker-compose.yml` possui dois serviços principais.

### `db`

Container PostgreSQL:

```text
Imagem: postgres:17-alpine
Container: validahoras-db
Porta local: 5432
```

Existe um volume persistente:

```text
validahoras_postgres_data
```

Assim, os dados permanecem mesmo após parar ou recriar os containers, desde que o volume não seja removido.

### `api`

Container do backend:

```text
Container: validahoras-api
Porta local: 8000
```

O código local é montado em `/app`, permitindo desenvolvimento com reload automático.

O backend depende do health check do PostgreSQL antes de iniciar.

---

## 5. Inicialização e migrations

Ao iniciar o container da API, o script:

```text
docker/entrypoint.sh
```

executa:

```bash
alembic upgrade head
```

Depois inicia o comando configurado no Docker Compose:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Isso significa que um integrante novo não precisa criar manualmente as tabelas.

Fluxo:

```text
docker compose up
       |
       v
PostgreSQL inicia
       |
       v
Health check confirma disponibilidade
       |
       v
API inicia
       |
       v
Alembic aplica migrations
       |
       v
FastAPI sobe na porta 8000
```

---

## 6. Configuração por ambiente

As configurações são lidas do `.env`.

O projeto disponibiliza:

```text
.env.example
```

Principais variáveis:

```text
APP_NAME
APP_ENV
APP_DEBUG
API_V1_PREFIX
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES

POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
DATABASE_URL

CORS_ORIGINS
UPLOAD_DIR
MAX_UPLOAD_SIZE_MB
```

As credenciais presentes no exemplo são exclusivamente para desenvolvimento local.

---

## 7. Entidades atuais

### 7.1 Institution

Tabela:

```text
institutions
```

Representa uma instituição de ensino.

Campos principais:

```text
id
name
code
active
created_at
updated_at
```

Relacionamentos:

```text
Institution 1 ---- N Course
Institution 1 ---- N User
Institution 1 ---- N ValidationRule
```

Já existe implementação funcional inicial para:

- criar instituição;
- listar instituições.

---

### 7.2 Course

Tabela:

```text
courses
```

Representa um curso pertencente a uma instituição.

Campos principais:

```text
id
institution_id
name
code
required_complementary_hours
active
created_at
updated_at
```

Relacionamentos:

```text
Institution 1 ---- N Course

Course 1 ---- N User
Course 1 ---- N ValidationRule
```

Existe uma restrição para impedir dois cursos com o mesmo nome dentro da mesma instituição:

```text
institution_id + name
```

O CRUD de cursos ainda precisa ser implementado.

---

### 7.3 User

Tabela:

```text
users
```

Representa os usuários da plataforma.

Perfis atualmente previstos:

```text
STUDENT
EVALUATOR
COORDINATOR
ADMIN
```

Campos principais:

```text
id
institution_id
course_id
name
email
password_hash
role
registration_number
active
created_at
updated_at
```

Relacionamentos principais:

```text
Institution 1 ---- N User

Course 1 ---- N User

User (aluno) 1 ---- N ComplementaryActivity

User (aluno) 1 ---- N Submission
```

Observação:

- `course_id` é opcional no banco porque nem todo perfil necessariamente precisa representar um aluno;
- regras de obrigatoriedade por perfil deverão ser implementadas na camada de negócio.

Ainda falta:

- cadastro de usuário;
- login;
- refresh token, caso seja adotado;
- dependências de autenticação;
- autorização por perfil;
- endpoints administrativos.

---

### 7.4 ComplementaryActivity

Tabela:

```text
complementary_activities
```

Representa a atividade complementar informada pelo aluno.

Campos principais:

```text
id
student_id
title
category
provider_name
start_date
end_date
declared_hours
description
created_at
updated_at
```

Relacionamentos:

```text
User (aluno) 1 ---- N ComplementaryActivity

ComplementaryActivity 1 ---- N CertificateDocument

ComplementaryActivity 1 ---- N Submission
```

Ainda falta:

- CRUD;
- validação de propriedade da atividade;
- validações de datas;
- validações de carga horária;
- regras relacionadas à categoria.

---

## 8. Documento comprobatório

Atualmente o model existente chama-se:

```text
CertificateDocument
```

e a tabela:

```text
certificate_documents
```

Campos atuais:

```text
id
activity_id
original_name
stored_name
mime_type
size_bytes
storage_path
sha256
ocr_text
extracted_data
created_at
updated_at
```

Relacionamento:

```text
ComplementaryActivity 1 ---- N CertificateDocument
```

### Regra de negócio definida

O aluno deverá anexar **pelo menos um documento comprobatório** antes de enviar uma atividade para validação.

Uma atividade poderá existir como rascunho sem arquivo, porém:

```text
SEM DOCUMENTO COMPROBATÓRIO
          |
          v
NÃO PODE SER SUBMETIDA PARA VALIDAÇÃO
```

O comprovante não precisa ser obrigatoriamente um certificado.

Dependendo da instituição, curso, categoria e regra vigente, podem ser aceitos:

- certificado;
- declaração;
- comprovante de participação;
- atestado;
- outro documento definido pela instituição.

### Ajuste recomendado

Antes da implementação do upload, recomenda-se renomear:

```text
CertificateDocument
```

para um nome mais genérico, por exemplo:

```text
SupportingDocument
```

e a tabela para:

```text
supporting_documents
```

Também deve ser criado um campo para identificar o tipo do documento.

Exemplo:

```text
document_type
```

Possíveis valores iniciais:

```text
CERTIFICATE
DECLARATION
ATTENDANCE_PROOF
OTHER
```

A regra que exige ao menos um comprovante deve ficar no `Service` responsável por submeter uma solicitação, e não apenas no frontend.

---

## 9. Submission

Tabela:

```text
submissions
```

Representa a solicitação enviada pelo aluno para validação.

Campos principais:

```text
id
protocol
student_id
activity_id
validation_rule_id
status
submitted_at
created_at
updated_at
```

Status previstos:

```text
DRAFT
SUBMITTED
PROCESSING
PENDING_REVIEW
APPROVED
REJECTED
CORRECTION_REQUESTED
```

Relacionamentos:

```text
User 1 ---- N Submission

ComplementaryActivity 1 ---- N Submission

ValidationRule 1 ---- N Submission

Submission 1 ---- 0..1 AutomaticAnalysis

Submission 1 ---- N ManualReview

Submission 1 ---- N StatusHistory
```

### Regras que ainda precisam ser implementadas

Antes de uma submissão mudar para `SUBMITTED`, deve ser validado no mínimo:

- a atividade pertence ao aluno autenticado;
- existe pelo menos um documento comprobatório associado;
- os campos obrigatórios da atividade estão preenchidos;
- existe contexto suficiente para determinar a instituição e o curso;
- deve ser gerado protocolo único;
- deve ser criado um registro de histórico.

A migration/model atual não força a existência de documento por constraint de banco.

Essa validação deverá ser feita no fluxo de negócio.

---

## 10. ValidationRule

Tabela:

```text
validation_rules
```

Representa as regras utilizadas para avaliar atividades.

Campos principais:

```text
id
institution_id
course_id
category
version
valid_from
valid_until
max_hours
accepted_document_types
mandatory_criteria
confidence_threshold
allows_auto_approval
active
notes
created_by_id
created_at
updated_at
```

Relacionamentos:

```text
Institution 1 ---- N ValidationRule

Course 1 ---- N ValidationRule

ValidationRule 1 ---- N Submission
```

Existe uma restrição de versão por:

```text
institution_id
course_id
category
version
```

### Regra importante

Regras utilizadas em decisões anteriores não devem ser alteradas de forma retroativa.

Quando uma regra já utilizada precisar mudar, deve ser criada uma nova versão.

Exemplo:

```text
Curso extracurricular - versão 1
              |
              +---- solicitações antigas

Curso extracurricular - versão 2
              |
              +---- novas solicitações
```

Ainda falta implementar:

- CRUD;
- versionamento automático;
- validação de conflito de vigência;
- seleção da regra aplicável;
- bloqueio de alteração destrutiva de versões já utilizadas.

---

## 11. AutomaticAnalysis

Tabela:

```text
automatic_analyses
```

Estrutura preparada para guardar o resultado da futura análise automática.

Campos:

```text
id
submission_id
result
confidence
details
explanation
created_at
updated_at
```

Resultados previstos:

```text
APPROVED
MANUAL_REVIEW
FAILED
```

Relacionamento:

```text
Submission 1 ---- 0..1 AutomaticAnalysis
```

A relação foi modelada como uma única análise automática por submissão nesta primeira versão.

### Ainda não implementado

- OCR;
- integração com IA;
- cálculo de confiança;
- comparação com regras;
- aprovação automática;
- encaminhamento automático para avaliação humana.

---

## 12. ManualReview

Tabela:

```text
manual_reviews
```

Representa uma decisão de um avaliador humano.

Campos:

```text
id
submission_id
evaluator_id
decision
justification
created_at
updated_at
```

Decisões previstas:

```text
APPROVED
REJECTED
CORRECTION_REQUESTED
```

Relacionamentos:

```text
Submission 1 ---- N ManualReview

User (avaliador) 1 ---- N ManualReview
```

Ainda falta:

- fila de solicitações pendentes;
- permissões do avaliador;
- endpoint de decisão;
- validação obrigatória da justificativa;
- alteração de status;
- registro automático no histórico.

---

## 13. StatusHistory

Tabela:

```text
status_history
```

Mantém a rastreabilidade das alterações de status de uma submissão.

Campos:

```text
id
submission_id
status
changed_by_id
note
created_at
updated_at
```

Relacionamentos:

```text
Submission 1 ---- N StatusHistory

User 1 ---- N StatusHistory
```

Objetivo:

```text
SUBMITTED
    |
    v
PROCESSING
    |
    v
PENDING_REVIEW
    |
    v
APPROVED
```

Cada alteração relevante deverá gerar um novo registro no histórico.

Ainda falta automatizar essa gravação na camada de serviço.

---

## 14. Visão geral dos relacionamentos

```text
Institution
├── 1:N Course
├── 1:N User
└── 1:N ValidationRule

Course
├── N:1 Institution
├── 1:N User
└── 1:N ValidationRule

User
├── N:1 Institution
├── N:1 Course (opcional)
├── 1:N ComplementaryActivity
└── 1:N Submission

ComplementaryActivity
├── N:1 User
├── 1:N SupportingDocument*
└── 1:N Submission

SupportingDocument*
└── N:1 ComplementaryActivity

ValidationRule
├── N:1 Institution
├── N:1 Course (opcional)
└── 1:N Submission

Submission
├── N:1 User
├── N:1 ComplementaryActivity
├── N:1 ValidationRule (opcional antes da análise)
├── 1:0..1 AutomaticAnalysis
├── 1:N ManualReview
└── 1:N StatusHistory

AutomaticAnalysis
└── 1:1 Submission

ManualReview
├── N:1 Submission
└── N:1 User (avaliador)

StatusHistory
├── N:1 Submission
└── N:1 User (responsável pela mudança, quando aplicável)
```

`*` Atualmente chamado `CertificateDocument` no código. Renomeação recomendada antes da implementação do upload.

---

## 15. Endpoints existentes

### Raiz

```http
GET /
```

Retorna o status básico da API.

### Health

```http
GET /api/v1/health
```

Executa também:

```sql
SELECT 1
```

para confirmar que o banco está acessível.

### Instituições

Criar:

```http
POST /api/v1/institutions
```

Listar:

```http
GET /api/v1/institutions
```

Essa implementação foi criada como referência do padrão:

```text
Controller
   |
Service
   |
Repository
   |
Model
   |
Database
```

---

## 16. Segurança

O arquivo:

```text
app/core/security.py
```

já possui funções base para:

- gerar hash de senha;
- verificar senha;
- gerar access token JWT.

Algoritmo JWT atual:

```text
HS256
```

### Ainda falta

- schema de login;
- endpoint de login;
- busca do usuário por e-mail;
- validação de senha;
- dependency para usuário autenticado;
- controle de acesso por perfil;
- estratégia de refresh token, se adotada;
- tratamento de usuários inativos.

---

## 17. Upload

Existe:

```text
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10
```

Também existe volume Docker:

```text
validahoras_uploads
```

Porém o upload **ainda não está implementado**.

Será necessário criar:

- validação de tamanho;
- validação de MIME type;
- geração de nome interno;
- hash SHA-256;
- gravação física;
- registro no banco;
- vínculo com atividade;
- remoção controlada;
- proteção contra arquivos inválidos;
- regra de documentos permitidos;
- endpoint de download/visualização com autorização.

---

## 18. Testes

Atualmente existe apenas um teste básico:

```text
tests/test_root.py
```

Ele verifica se:

```http
GET /
```

retorna HTTP `200` e informa que a aplicação está executando.

Ainda devem ser criados testes para cada funcionalidade.

Estrutura sugerida:

```text
tests/
├── test_auth.py
├── test_institutions.py
├── test_courses.py
├── test_activities.py
├── test_documents.py
├── test_submissions.py
├── test_rules.py
├── test_analysis.py
├── test_reviews.py
└── test_history.py
```

---

## 19. Padrão para implementar uma nova funcionalidade

Ao criar uma funcionalidade nova, seguir preferencialmente esta sequência:

```text
1. Model / alteração do model
2. Migration Alembic
3. Schema
4. Repository
5. Service
6. Controller
7. Inclusão da rota
8. Testes
9. Atualização desta documentação
```

Nem toda funcionalidade precisará obrigatoriamente criar todos esses arquivos, mas a separação de responsabilidades deve ser mantida.

---

## 20. Regras de negócio já definidas

### BR01 — Instituição e curso

Um aluno deve estar associado à instituição e ao curso necessários para determinar as regras acadêmicas aplicáveis.

### BR02 — Atividade em rascunho

Uma atividade pode ser cadastrada antes de possuir documento comprobatório.

### BR03 — Comprovante obrigatório para submissão

Uma atividade **não pode ser enviada para validação sem pelo menos um documento comprobatório**.

A validação deve existir no backend.

### BR04 — Tipo de comprovante

O comprovante aceito pode variar conforme instituição, curso, categoria e versão da regra.

### BR05 — Protocolo

Toda submissão efetivamente enviada deve receber um protocolo único.

### BR06 — Histórico

Mudanças relevantes no status de uma submissão devem gerar histórico.

### BR07 — Versionamento de regra

Alterações em regras que já tenham sido utilizadas devem gerar nova versão.

### BR08 — Não retroatividade

Uma alteração de regra não pode modificar retroativamente uma solicitação já processada com uma versão anterior.

### BR09 — Revisão manual

Solicitações não conclusivas pela análise automática deverão ser encaminhadas para revisão manual.

### BR10 — Decisão humana

A revisão manual deve registrar avaliador, decisão e justificativa.

---

## 21. Pendências recomendadas antes de continuar

### Prioridade imediata

1. Decidir e executar a renomeação de `CertificateDocument` para `SupportingDocument`;
2. adicionar o tipo do documento comprobatório;
3. criar migration correspondente;
4. implementar autenticação e autorização por perfil;
5. implementar CRUD de cursos;
6. implementar CRUD de atividades;
7. implementar upload de documentos;
8. implementar submissão com protocolo;
9. aplicar a regra de comprovante obrigatório;
10. implementar histórico inicial da submissão.

### Depois

11. regras de validação;
12. OCR;
13. análise automática;
14. fila do avaliador;
15. decisão manual;
16. fluxo de correção;
17. testes de integração do MVP.

---

## 22. Relação com as issues do projeto

Estado aproximado da base atual:

```text
#13 Estrutura base MVC
Status: base implementada

#14 Configuração do banco
Status: base implementada com PostgreSQL, SQLAlchemy, Alembic e Docker

#15 Models e relacionamentos
Status: primeira versão implementada; ainda sujeita a ajustes de domínio

#16 Login e perfis
Status: infraestrutura de segurança preparada; fluxo funcional pendente

#17 Cadastro de atividade complementar
Status: model existente; funcionalidade pendente

#18 Upload de certificado/documento
Status: model e armazenamento preparados; funcionalidade pendente

#19 Protocolo/solicitação
Status: model existente; geração e fluxo pendentes

#20 Regras de validação
Status: model existente; CRUD, seleção e versionamento funcional pendentes

#21 OCR
Status: campos reservados; implementação pendente

#22 Análise automática
Status: model existente; implementação pendente

#23 Fila do avaliador
Status: pendente

#24 Decisão manual
Status: model existente; fluxo pendente

#25 Status e histórico
Status: model existente; automação do fluxo pendente
```

---

## 23. Regra de manutenção desta documentação

Sempre que um PR alterar uma das áreas abaixo, este arquivo deve ser revisado:

- arquitetura;
- models;
- migrations;
- relacionamentos;
- autenticação;
- upload;
- regras de negócio;
- status;
- fluxo de submissão;
- OCR;
- análise automática;
- revisão manual.

A documentação deve refletir o **estado real do código**, diferenciando claramente:

```text
IMPLEMENTADO
PREPARADO
PENDENTE
```

Isso evita que uma estrutura criada para o futuro seja confundida com uma funcionalidade já pronta.
