# ValidaHoras — Iteração 2

Sistema acadêmico do Grupo 05 para submeter certificados, analisar dados por OCR e regras institucionais, revisar solicitações e acompanhar horas complementares.

Repositório de entrega: https://github.com/murilloohs/ppads-grupo-05

Histórico e autoria originais do Grupo 05 preservados.

## Integrantes

João Victor Santos Pinto Sotonyi (10720147), Bruno Moreira da Silva (10723746), Rafael Silva de Barros (10721409), Murillo Henrique Santos (10720644) e Guilherme Pedrotti Perossi (10443090).

## Requisitos

- Docker Desktop com Docker Compose v2, em execução; no Linux, Docker Engine e plugin Compose.
- Git para clonar o repositório privado com uma conta autorizada, ou o ZIP da versão v2.
- Portas 5432, 8000 e 5173 disponíveis.
- Para rodar apenas a interface fora do Docker: Node.js 22.13+ da série 22 ou Node.js 24 e npm.
- Internet na primeira instalação para baixar imagens e dependências.

Python 3.13, PostgreSQL 17 e Tesseract em português são instalados pelas imagens Docker. O usuário não precisa instalá-los separadamente.

## Instalação completa com Docker

```bash
git clone https://github.com/murilloohs/ppads-grupo-05.git ValidaHoras
cd ValidaHoras
git switch master
cp .env.example .env
docker compose up --build -d
```

No PowerShell, substitua a cópia por `Copy-Item .env.example .env`. Se usar ZIP, extraia e abra um terminal na pasta que contém `docker-compose.yml`; os comandos Git não são necessários. Preserve um `.env` já configurado. Para reproduzir a entrega exata, use `git switch --detach v2` após clonar.

O Compose inicia banco, API e frontend. A API aguarda o banco e executa `alembic upgrade head` automaticamente. Aguarde a instalação e confira:

```bash
docker compose ps
docker compose logs --tail=50 api
```

- Interface: http://localhost:5173
- Swagger: http://localhost:8000/docs
- Saúde: http://localhost:8000/api/v1/health

Use `localhost` na interface. O hostname `db` do `.env` identifica o banco dentro da rede Docker. As variáveis POSTGRES_* e DATABASE_URL devem manter credenciais coerentes. Os volumes persistem dados e comprovantes.

## Criar as contas de demonstração

O `.env.example` habilita explicitamente `DEMO_ACCOUNTS_ENABLED=true`. No Swagger, execute os três endpoints, sem parâmetros:

1. `POST /api/v1/auth/temp-create-admin`
2. `POST /api/v1/auth/temp-create-student`
3. `POST /api/v1/auth/temp-create-evaluator`

| Perfil | E-mail | Senha local |
|---|---|---|
| Administrador | admin@validahoras.com | senha123 |
| Aluno | aluno@validahoras.com | senha123 |
| Avaliador | avaliador@validahoras.com | senha123 |

São contas locais para demonstração acadêmica. Fora desse ambiente, configure `DEMO_ACCOUNTS_ENABLED=false`, uma SECRET_KEY própria e desative debug. Os endpoints de criação retornam 404 com a opção desativada.

Para testar rotas protegidas pelo Swagger, use Authorize: e-mail no campo username e a senha local no campo password. Na interface, basta efetuar login.

## Roteiro funcional

1. Entre como administrador e cadastre a categoria `Curso`, vigência que inclua setembro de 2026, limite de 40 horas, PDF/JPG/PNG e aprovação automática habilitada. Salvar uma edição cria nova versão; avaliações existentes mantêm a anterior.
2. Saia e entre como aluno. Em Nova atividade, preencha os dados que aparecem no certificado, anexe arquivo real, revise o resumo e confirme.
3. A análise usa nome, atividade, instituição, período e carga horária. Dados coincidentes com a regra podem ser aprovados automaticamente. Falta de regra, leitura insuficiente e divergências seguem para revisão manual.
4. Entre como avaliador, abra a fila, confira documento/comparações/regra e escolha aprovar, reprovar ou solicitar correção. Informe a justificativa e confirme a decisão.
5. Como aluno, abra Minhas solicitações: pesquise, filtre por status, consulte histórico e baixe o comprovante. Se houver correção, use Corrigir e reenviar. O novo envio recebe novo protocolo, e o histórico mantém os eventos anteriores.

A pasta `examples` contém um certificado sintético para demonstração, identificado como tal. Ele não comprova uma atividade acadêmica real. A submissão dele deve usar os mesmos campos impressos e a conta Aluno Teste.

## Interface fora do Docker (opcional)

Suba banco e API: `docker compose up --build -d db api`. Em outro terminal:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

PowerShell: `Copy-Item .env.example .env`. O arquivo usa `VITE_API_URL=http://localhost:8000/api/v1`. Alterações na URL exigem reiniciar o Vite. Se a porta mudar, atualize CORS_ORIGINS no `.env` da API e recrie o container. Não é preciso executar a interface manualmente quando o serviço frontend do Compose já ocupa 5173.

## Verificação

```bash
docker compose exec api pytest -q
docker compose exec api ruff check .
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

São 15 testes, incluindo autenticação, isolamento por aluno/instituição, OCR, aprovação/revisão, correção/reenvio, versões de regras, duplicidade e integridade de arquivos. Os testes usam PostgreSQL migrado e rollback; não usam SQLite. Evidências e limitações: `docs/VALIDACAO.md`.

Para execução Python sem Docker, instale Python 3.13, PostgreSQL, Tesseract e o idioma português, crie um virtualenv e execute `pip install -r requirements.txt`. Ajuste DATABASE_URL para o banco acessível pela máquina, UPLOAD_DIR para uma pasta local e aplique `alembic upgrade head`; inicie com `uvicorn app.main:app --reload`. A execução completa com Docker é o caminho recomendado.

## Encerramento e problemas comuns

- Encerrar preservando dados: `docker compose down`.
- Reiniciar: `docker compose up -d`.
- Porta ocupada: encerre o outro processo ou ajuste o mapeamento e as URLs.
- Login falha: confirme API saudável e criação das três contas.
- Sem aprovação automática: confira categoria, vigência, dados extraídos e nome no certificado; a fila manual continua disponível.
- Mudança de credenciais do PostgreSQL: um volume já inicializado mantém as credenciais antigas; não apague volumes com dados para tentar corrigir login.

## Arquitetura e limites

API FastAPI; SQLAlchemy e Alembic; PostgreSQL; React/Vite. Controllers expõem HTTP, services implementam regras e repositories concentram as transações principais. JSON/Pydantic forma a apresentação da API; React é a interface visual.

OCR: texto digital com PyMuPDF e imagens com Tesseract. São lidas até três páginas de PDF e armazenados até 20 mil caracteres do texto. A extração de campos usa heurísticas; a confiança representa proporção de verificações coincidentes, não probabilidade de autenticidade do certificado. Documentos ilegíveis ou sem dados suficientes seguem para avaliação humana.

Uploads: PDF/JPG/PNG, até 10 MB por padrão; verificação de conteúdo, SHA-256 e acesso autorizado. Comprovantes idênticos em outra atividade do mesmo aluno são bloqueados. Formatos corrompidos/protegidos exigem substituição. Um envio fechado não aceita alteração de dados ou comprovantes sem solicitação de correção.

As listas usam paginação local no frontend sobre dados autorizados; paginação no servidor e processamento assíncrono de OCR são evoluções de escala. A versão acadêmica não inclui implantação pública, integração com sistema institucional, relatórios gerenciais nem comprovação de conformidade legal ou desempenho de produção.

## Documentação e entregas

- `docs/Especificacao_ValidaHoras_Iteracao_2.md`: texto da especificação revisada; PDF e DOCX de mesmo nome também disponíveis em docs, no modelo Mackenzie.
- `docs/Praticando_ValidaHoras_Controle_de_Versao.md`: identificação e evidências da atividade Praticando; PDF e DOCX de mesmo nome também disponíveis em docs.
- `docs/COMO_ENTREGAR.md`: instruções e textos para a plataforma.
- `docs/VALIDACAO.md`: verificações executadas.
- Os três PDFs anteriores em `docs` permanecem como referência histórica.
- `imgs`: diagramas originais; a especificação atual distingue a modelagem anterior das mudanças da Iteração 2.

### Referências Git

- `v1`: commit original da Iteração 1, equivalente à referência herdada `v1.0`.
- `iteracao2`: branch preservada com alteração em `frontend/README.md` e `frontend/src/pages/Success.jsx`.
- PR #30: merge do exercício em `master`.
- `v2`: código e documentação finais da Iteração 2; `master` contém a entrega atual.

A entrega está no repositório principal do Grupo 05. As branches master e main contêm a versão final; iteracao2 permanece disponível. A release v2 inclui os documentos e o ZIP executável. Não publique tokens, `.env` ou dados reais de alunos.
