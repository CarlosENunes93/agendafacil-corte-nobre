# AgendaFácil — Barbearia Corte Nobre

**Projeto acadêmico de Análise e Desenvolvimento de Sistemas | Disciplina: Projeto de Software**

**Estado atual:** MVP em desenvolvimento na branch `feature/estrutura-inicial-flask`. O código inclui autenticação, consulta da agenda, novos agendamentos e encaixes, cadastro de clientes, cancelamento e reagendamento. A comprovação dos testes automatizados consta nas execuções do GitHub Actions; a validação externa e a revisão final ainda estão pendentes.

O **AgendaFácil** é uma proposta de aplicação web responsiva para organizar os agendamentos e encaixes presenciais da **Barbearia Corte Nobre**, situada em Sorocaba/SP. O projeto dá continuidade às **Experiências Práticas I e II** e orienta a execução e a coleta de evidências técnicas na **Experiência Prática III**.

> **Transparência:** as telas e os exemplos descritos são demonstrativos. Funcionalidades, critérios de segurança, desempenho e acessibilidade mencionados como *previstos* deverão ser implementados e testados antes de serem declarados concluídos. Este repositório não representa, neste momento, uma aplicação pronta para produção.

## 1. Contexto e problema

Na investigação inicial, foram identificadas duas formas de atendimento: **agendamentos recebidos por WhatsApp** e **atendimentos presenciais por ordem de chegada**. A coexistência desses fluxos exige uma visão organizada dos horários de cada profissional. Conflitos de agenda, atrasos e retrabalho são **riscos a prevenir**, não ocorrências comprovadas na entrevista.

**Usuários diretos:** proprietário/administrador e barbeiros autorizados.  
**Beneficiários indiretos:** clientes atendidos pela barbearia.

**Objetivo do MVP:** centralizar a agenda por profissional e permitir registrar, consultar, reagendar e cancelar atendimentos, distinguindo reservas de encaixes e prevenindo sobreposições.

## 2. Escopo funcional previsto

| Código | Funcionalidade | Resultado esperado |
| --- | --- | --- |
| RF01 | Cadastro e seleção de clientes | Identificar o cliente de um atendimento com os dados mínimos necessários. |
| RF02 | Consulta da agenda diária | Visualizar atendimentos por data e profissional, com horários e estados identificáveis. |
| RF03 | Registro de agendamentos | Validar serviço, duração e disponibilidade antes da confirmação. |
| RF04 | Cancelamento | Cancelar um atendimento autorizado e liberar seu horário conforme a regra de negócio. |
| RF05 | Reagendamento | Alterar o horário com nova verificação de disponibilidade. |
| RF06 | Registro de encaixes | Identificar atendimentos presenciais por ordem de chegada na mesma agenda. |

Acesso autenticado, autorização por operação e mensagens claras integram o fluxo essencial.

### Fora do escopo inicial

- Pagamentos e gestão financeira;
- Envio automático de mensagens ou integração direta com a API do WhatsApp;
- Aplicativo móvel nativo;
- Relatórios gerenciais avançados e recursos administrativos não essenciais.

O WhatsApp é um **canal atual de recebimento dos pedidos**, não uma integração automática prevista para esta primeira versão.

## 3. Arquitetura e tecnologias planejadas

**Padrão:** monólito modular em três camadas, proporcional ao desenvolvimento individual do MVP.

1. **Apresentação:** HTML5, CSS3 e JavaScript; interface responsiva no navegador, com comunicação HTTP/JSON.
2. **Aplicação e negócio:** **Python 3.12 + Flask 3.1.x (versão planejada)**; rotas, autenticação, autorização e validação das regras de agendamento.
3. **Persistência:** **SQLite**, integrado pela biblioteca padrão `sqlite3` do Python, com consultas parametrizadas, chaves estrangeiras e transações.

**Qualidade:** `pytest` (linha 8.x planejada) para testes unitários e de integração; **Git/GitHub**, revisão por **Pull Request** e **GitHub Actions** para execução automatizada dos testes.

A escolha inicial do SQLite reduz a complexidade de instalação, mas requer **armazenamento persistente, backups e tratamento cuidadoso da concorrência**. Um eventual crescimento para múltiplas instâncias ou maior concorrência poderá justificar migração para PostgreSQL. Isso é uma possibilidade futura, não parte do escopo inicial.

### Fluxo central planejado

1. Um profissional autorizado acessa a agenda e solicita um novo atendimento.
2. Seleciona cliente, profissional, serviço, data, horário e origem (**Agendado** ou **Encaixe**).
3. A camada de negócio valida os dados, a duração, as permissões e a ausência de sobreposição para o profissional.
4. A gravação é efetuada em transação; se existir conflito, o registro não é confirmado.
5. A interface apresenta **confirmação ou erro compreensível**, e a agenda exibe o estado atualizado.

A proteção contra agendamentos simultâneos deve ser verificada em testes específicos de concorrência, e não apenas presumida pela interface.

## 4. Modelo de dados previsto

Entidades principais, relacionadas por identificadores e chaves estrangeiras:

| Entidade | Papel |
| --- | --- |
| `usuarios` | Contas autorizadas, papéis e hash seguro de senha. |
| `profissionais` | Identificação dos barbeiros e filtragem da agenda. |
| `clientes` | Dados mínimos necessários à identificação de clientes. |
| `servicos` | Nome e duração prevista do atendimento. |
| `agendamentos` | Referências a cliente, profissional e serviço; início, fim, origem e situação. |

As restrições de integridade, os valores permitidos e a prevenção transacional de conflitos serão especificados e exercitados na implementação. Não serão utilizados dados pessoais reais nos exemplos ou nos testes acadêmicos.

## 5. Requisitos não funcionais e segurança

- **RNF01 — Autenticação e autorização:** login restrito; senhas nunca armazenadas em texto simples, MD5 ou SHA-1. Utilizar mecanismo robusto de hash de senha (por exemplo, `scrypt`, com salt e parâmetros adequados), sessões protegidas e verificação de permissão no servidor.
- **RNF02 — Proteção de entradas e dados:** validação obrigatória no servidor, SQL parametrizado, saída textual codificada, tratamento adequado de erros, proteção de segredos e dependências atualizadas, considerando riscos pertinentes do **OWASP Top 10**.
- **RNF03 — Desempenho e portabilidade:** aplicação web em ambiente Python documentado, com armazenamento persistente do SQLite. Meta planejada para a agenda: **mediana de até 3,0 segundos em cinco medições**, após aquecimento, nas condições móveis e com volume de dados definidos no plano de teste. Essa meta ainda precisa ser verificada.
- **RNF04 — Acessibilidade:** rótulos permanentes, contraste planejado de **4,5:1 para texto** e **3:1 para componentes**, foco visível, navegação por teclado, mensagens não dependentes somente de cor, alvos de toque de pelo menos **44 × 44 pixels CSS** e ampliação a **200%** sem perda das ações essenciais. Sua conformidade dependerá de avaliação prática e testes.

**Não publicar:** senhas, tokens, chaves, arquivos `.env`, bancos com dados pessoais, informações privadas de terceiros ou backups sensíveis. Conferir o `.gitignore` antes de qualquer commit.

## 6. Protótipo e fluxo de telas

As três telas de referência foram planejadas na Experiência Prática II:

1. **Tela 1 — Acesso ao sistema:** identidade do AgendaFácil, usuário, senha e entrada para a área autorizada.
2. **Tela 2 — Novo agendamento:** formulário com dados obrigatórios e indicação demonstrativa de disponibilidade.
3. **Tela 3 — Agenda diária e resultados:** mensagem de confirmação, filtros, lista de atendimentos e ações de continuidade.

**Cenário inteiramente fictício e consistente entre as telas:**

- Cliente: **Lucas Ferreira**
- Profissional: **Rafael Costa**
- Serviço: **Corte masculino** (30 minutos)
- Data: **10/11/2026**
- Intervalo: **14:00–14:30**
- Origem: **Encaixe**
- Resultado demonstrado: **Confirmado**

Na agenda fictícia do mesmo profissional também constam Pedro Almeida (09:00–09:30, corte masculino) e Bruno Martins (10:00–10:30, barba). Esses nomes e horários servem apenas para demonstração e testes.

## 7. Plano de validação e critérios de aceitação

A Experiência Prática II definiu três tarefas:

- **T01:** compreender o acesso e localizar a agenda;
- **T02:** registrar ou indicar corretamente o registro do encaixe fictício;
- **T03:** localizar e interpretar a confirmação e as próximas ações, inclusive informações acessíveis sem depender somente das cores.

**Critérios planejados:** sucesso independente em **3 de 3 tarefas (100%)**; **T02 em até 180 segundos**; facilidade percebida de **pelo menos 4/5**. São limites de aceitação, **não resultados coletados**. O teste deve registrar tempos, erros, ajuda, comentários e decisões de correção. Testar apenas imagens estáticas permite avaliar compreensão, mas não comprova autenticação, gravação ou segurança reais.

Na **Experiência Prática III**, deverão ser realizadas **ao menos duas rodadas reais de validação e testes de usabilidade com contato externo**, respeitando consentimento, privacidade, utilização de dados fictícios e registro de melhorias efetivamente implementadas.

## 8. Objetivo de Desenvolvimento Sustentável

**ODS 8 — Trabalho Decente e Crescimento Econômico**, com conexão à **Meta 8.3**. A contribuição pretendida é apoiar a organização e a produtividade de um pequeno negócio local, reduzindo barreiras no gerenciamento dos atendimentos. **Não se afirma que o software, por si só, produziu impacto econômico mensurado**.

## 9. Como executar a versão em desenvolvimento

> **Estado do código:** aplicação Flask com autenticação, consulta da agenda diária a partir do SQLite (filtros de data e profissional), **formulário autenticado de novos agendamentos e encaixes com proteção CSRF**, confirmação na agenda e verificação transacional de conflitos. Cadastro de clientes, cancelamento e reagendamento **já estão implementados e cobertos por testes automatizados**; o cadastro administrativo de profissionais e serviços ainda precisa ser disponibilizado de forma prática. O sistema não foi validado externamente nem preparado para produção. As instruções abaixo destinam-se a execução local, não à publicação em produção.

Pré-requisitos: **Python 3.12** e Git. No terminal, na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No PowerShell, configure um segredo **aleatório e exclusivo** antes de iniciar o projeto:

```powershell
$env:AGENDAFACIL_SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(48))")
```

**Não versionar nem compartilhar o segredo.** O SQLite de desenvolvimento é criado automaticamente em `instance/agenda.sqlite3`, ignorado pelo Git.

Crie uma conta inicial, informando a senha somente no prompt seguro:

```powershell
python -m flask --app run:app criar-usuario
```

Execute o servidor local:

```powershell
python -m flask --app run:app run
```

Abra `http://127.0.0.1:5000/login` e entre com o usuário criado. A agenda consulta registros efetivamente armazenados no SQLite, e o botão **Novo agendamento** abre o formulário autenticado. Para utilizá-lo, devem existir previamente registros de clientes, profissionais e serviços no banco. O cadastro de clientes já pode ser realizado na interface. Profissionais e serviços ainda precisam ser cadastrados no SQLite por procedimento administrativo; a interface para esses dois cadastros não faz parte da versão atual. Os dados fictícios do protótipo são usados nos testes, não criados automaticamente no banco normal. A rota `/health` permite verificar a resposta básica do servidor.

Execute os testes:

```powershell
python -m pytest -q
```

Os testes também são configurados no GitHub Actions. Seus resultados devem ser verificados na execução correspondente; a mera presença do workflow não comprova aprovação. Para uma implantação real serão necessários HTTPS, cookies seguros, gerenciamento de segredo, backup persistente, revisão de ameaças e restrições de acesso adicionais.

---

**Autor do repositório:** [CarlosENunes93](https://github.com/CarlosENunes93)  
**Projeto:** AgendaFácil — Barbearia Corte Nobre · Sorocaba/SP  
**Finalidade:** desenvolvimento acadêmico, com dados de demonstração e foco em engenharia de software responsável.
