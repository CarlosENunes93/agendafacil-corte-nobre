# Plano de validação externa — AgendaFácil

**Estado:** PLANEJADO. Nenhuma rodada, observação ou nota de participante foi preenchida artificialmente.

## Objetivo

Avaliar com um representante externo a compreensão do fluxo de autenticação, o registro de encaixe e a consulta da confirmação, usando a aplicação **executável**, não apenas capturas estáticas. Depois do primeiro contato, registrar dificuldades, implementar ajustes justificáveis e repetir a avaliação para verificar os resultados.

**Representante previsto:** proprietário ou profissional autorizado da Barbearia Corte Nobre. A participação de Cláudio é uma possibilidade a confirmar; não se presume que aceitou participar.

**Cuidados:** solicitar consentimento, não registrar senhas reais, utilizar base de demonstração sem clientes reais, informar que o protótipo é acadêmico, evitar mostrar contatos pessoais nas evidências e não divulgar conversas privadas. Registrar somente as evidências autorizadas.

## Pré-condições e preparação

1. Verificar funcionamento local da versão implementada e login de usuário autorizado.
2. Usar banco local descartável e comando `preparar-demo --confirmar` com flag de ambiente, conforme README.
3. Confirmar que a agenda de Rafael Costa em 10/11/2026 contém Pedro Almeida às 09h e Bruno Martins às 10h, mas **não** o encaixe de Lucas às 14h antes da tarefa.
4. Dispor de navegador móvel ou emulação controlada de 360 pixels CSS. Registrar dispositivo, navegador, versão e condições.
5. Garantir que a segunda rodada possa ser comparada à primeira, com os mesmos objetivos e condições.
6. Medir as tarefas com cronômetro, a partir do fim da leitura da instrução.

## Tarefas de avaliação

| ID | Instrução ao participante | Critério esperado |
| --- | --- | --- |
| T01 | Identificar a área de login, entrar com credenciais de demonstração fornecidas de modo seguro e localizar a agenda. | Acesso e localização sem ajuda. |
| T02 | Registrar um **Encaixe** para Lucas Ferreira com Rafael Costa, Corte masculino, em **10/11/2026, 14:00–14:30**. | Registro correto, sem sobreposição, em até **180 segundos**. |
| T03 | Localizar a confirmação na agenda, reconhecer horário, profissional, origem e estado por texto (não só pela cor) e apontar as ações de reagendar e cancelar. | Interpretação correta, sem ajuda. |

Os valores são **metas estabelecidas anteriormente**, não resultados registrados.

## Métricas e aprovação

- **Usabilidade:** 3 de 3 tarefas concluídas de maneira independente (100%). Sucessos com ajuda devem ser identificados separadamente, sem serem contabilizados como independentes.
- **Eficiência:** T02 concluída em até 180 segundos, incluindo conferência do resultado.
- **Satisfação:** nota mínima **4/5**, perguntando ao fim: “Em uma escala de 1 a 5, em que 1 significa muito difícil e 5 significa muito fácil, como você avalia a facilidade de utilização do protótipo AgendaFácil nas tarefas apresentadas?”
- **Defeito crítico:** qualquer perda de dados, erro de acesso, duplicação indevida, impossibilidade de registrar o encaixe ou erro que inviabilize a tarefa impede aceitação, independentemente da nota.

## Modelo de registro — Rodada 1 (NÃO EXECUTADA)

- Data/hora: **a preencher após execução**
- Local e condições: **a preencher**
- Participante, papel e consentimento: **a preencher**
- Versão/commit testado: **a preencher**
- Dispositivo/navegador: **a preencher**

| Tarefa | Concluída sem ajuda? | Tempo (s) | Erros/hesitações observados | Ajuda fornecida? |
| --- | --- | --- | --- | --- |
| T01 | — | — | — | — |
| T02 | — | — | — | — |
| T03 | — | — | — | — |

- Satisfação (1–5): **—**
- Comentário espontâneo do participante: **—**
- Problemas encontrados, severidade e evidência: **—**
- Decisão: **pendente**
- Ajustes a implementar e commits correspondentes: **—**

## Modelo de registro — Rodada 2 (NÃO EXECUTADA)

- Data/hora: **a preencher após execução**
- Local e condições: **a preencher**
- Participante, papel e consentimento: **a preencher**
- Versão/commit testado: **a preencher**
- Alterações da rodada 1 verificadas: **—**

| Tarefa | Concluída sem ajuda? | Tempo (s) | Erros/hesitações observados | Ajuda fornecida? |
| --- | --- | --- | --- | --- |
| T01 | — | — | — | — |
| T02 | — | — | — | — |
| T03 | — | — | — | — |

- Satisfação (1–5): **—**
- Comparação com a rodada 1: **—**
- Novos problemas, evidências e correções: **—**
- Decisão: **pendente**

## Evidências mínimas a preservar

- Link do repositório público e captura **real** de sua página principal com arquivos e visibilidade pública.
- Link do Pull Request, histórico de commits e execução aprovada do GitHub Actions.
- Saídas reais dos testes, com versão/commit identificado.
- Registro autorizado e verificável das duas rodadas externas; separar execução real de protótipos e dados demonstrativos.
- Alterações corretivas associadas ao feedback e evidência de reteste.

**Resultado final:** não preenchido até a execução efetiva das duas rodadas.
