# Contrato de interação do ValidaHoras

Fontes: especificação da Iteração 2 em `../docs`, schemas e serviços da API. A identidade existente está em DESIGN.md; os tokens de runtime pertencem a src/index.css.

| Capacidade | Responsável canônico | Contrato |
|---|---|---|
| Select/Listbox | select nativo de Dashboard | Popup e teclado do sistema operacional; rótulos do produto em português |
| Date | input date nativo | Calendário do navegador/sistema; datas ISO no transporte e pt-BR na exibição |
| Form | páginas e schemas Pydantic | Validação textual da aplicação e servidor; valores preservados em falhas |
| Scrollbar | src/index.css | Padrão global e override de cores forçadas |
| CRUD | api.js e serviços do backend | Autorização no servidor; navegação de sucesso para lista ou protocolo |
| Confirmação | ConfirmDialog | dialog modal nativo, Escape, foco inicial seguro e restauração de foco |

Decisões acadêmicas requerem justificativa e confirmação explícita; os serviços preservam autor e histórico. As permissões vêm de app/api/deps.py. Correções só são abertas por decisão do avaliador. Cada reenvio registra nova solicitação e preserva os dados e o documento usados anteriormente. Regras editadas criam versões imutáveis. Datas sem horário são tratadas como datas de calendário. Tokens de acesso são mantidos pelo fluxo JWT existente e removidos quando a sessão expira.

Busca, status e página da lista do aluno persistem na URL; paginação de dez itens sobre os dados próprios carregados pela API. A listagem local foi mantida para o escopo acadêmico; paginação no servidor é evolução de escala. Falhas têm mensagens inline com role alert; carregamento tem role status. Formulários impedem envio repetido durante a gravação.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Dashboard select | UX-CONTRACT.md | native | browser keyboard |
| Date | Native date inputs | API schemas | native | browser |
| Form | Page handlers | Pydantic schemas | create / edit | pytest / browser |
| Scrollbar | src/index.css | DESIGN.md | global | browser |
| CRUD | api.js | API controllers | return / protocol | pytest / browser |
