# Validação da Iteração 2 — 04/11/2026

## Executado

| Verificação | Resultado |
|---|---|
| Alembic upgrade head em PostgreSQL isolado | Migrações 0001 e 0002 aplicadas |
| pytest -q | 15 testes aprovados |
| ruff check . | Aprovado |
| npm ci / instalação pelo lockfile | Concluída; lockfile atualizado por correções compatíveis |
| npm run lint | Aprovado |
| npm run build | Aprovado |
| npm audit | Zero vulnerabilidades após atualizações e override minimatch |
| Auditoria estática do contrato de UI | Zero achados |
| Submissão real via API com PDF digital | Aprovada automaticamente pela regra cadastrada |
| Interface no Chrome | Login, estado vazio, formulário e consulta de solicitação/histórico inspecionados |

O cenário de submissão utilizou dados sintéticos da conta Aluno Teste, certificado digital com campos estruturados e uma regra de Curso. A extração real de texto por PyMuPDF retornou os campos, e a solicitação ficou aprovada; a consulta no navegador exibiu resultado e histórico.

## Cobertura adicional

- Correção, edição autorizada e novo protocolo, preservando comprovante e retrato da submissão anterior.
- Versionamento imutável de regras e rejeição de edição desatualizada.
- Rejeição de arquivos vazios/corrompidos, duplicidade por SHA-256 e alteração do conteúdo após upload.
- Bloqueio de decisões posteriores; autorização por perfil e instituição.

## Limites

O ambiente local de verificação usa Python 3.12 e PostgreSQL 16 fornecido por pgserver; a distribuição Docker configura Python 3.13 e PostgreSQL 17. Docker não está instalado nesta máquina; o build das imagens e a subida pelo Compose não foram executados aqui. A configuração foi revisada e o caminho local equivalente foi exercitado.

Tesseract não está instalado localmente. A leitura digital de PDF foi executada, os testes do adaptador de OCR de imagem usam simulação, e a imagem Docker instala Tesseract e português. Não se declara OCR de imagem real testado nesta máquina.

O seletor de arquivo do navegador não concluiu o upload na automação. O envio de PDF foi validado pela API real e pelos testes; isso não equivale a teste manual completo de todas as interações da interface.

Não foram certificados desempenho, capacidade, segurança de produção, conformidade legal ou acessibilidade integral. Os testes emitem avisos de depreciação de bibliotecas, sem falhas.
