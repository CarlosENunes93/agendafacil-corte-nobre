# Evidências técnicas verificáveis — Experiência Prática III

**Projeto:** AgendaFácil — Barbearia Corte Nobre (Sorocaba/SP)
**Status:** compilação e testes automatizados documentados; testes manuais e validações externas **pendentes**.

## Versionamento e integração de código

- Repositório público: https://github.com/CarlosENunes93/agendafacil-corte-nobre
- Pull Request de implementação: https://github.com/CarlosENunes93/agendafacil-corte-nobre/pull/1
- Pull Request **integrado** à branch `main` pelo commit `53c66b5f513f1c16c2a96746cd54ae7cc0d39b21`.
- Revisão técnica comentada no PR, realizada com assistência do ChatGPT pela conta do autor. **Não é revisão independente por outro desenvolvedor.**

## Testes automatizados

- Workflow: `.github/workflows/testes.yml`.
- Linguagem/ambiente: Python 3.12, Flask, SQLite e pytest.
- Execução verificada: https://github.com/CarlosENunes93/agendafacil-corte-nobre/actions/runs/41453485477
- Resultado observado nos logs do job `pytest`: **69 passed in 12.25s** (69 testes aprovados).
- Abrangência: autenticação, hash de senha, CSRF, consulta e filtros, registros, sobreposição, clientes, cancelamento, reagendamento, semeadura fictícia idempotente e concorrência com conexões SQLite independentes.

**Limites da evidência:** a aprovação do pytest não demonstra automaticamente segurança de produção, acessibilidade em dispositivo real, desempenho sob carga, nem satisfação de participantes externos. Qualquer mudança posterior à execução indicada deve ser verificada por nova execução da CI. Atualizações de configuração da própria CI também exigem confirmação específica.

## Validação externa — ainda não executada

Planejamento e campos para duas rodadas reais: [PLANO_VALIDACAO.md](PLANO_VALIDACAO.md).

**Não preencher como concluídos** os campos de participação externa, satisfação, tempo das tarefas, feedback ou melhorias por usuário até que existam evidências autorizadas e verificáveis.

## Evidência visual da entrega — ainda não capturada

Após revisão da branch `main`, capturar realmente a aba **Code** do repositório no navegador, mostrando:
- Proprietário e nome do repositório;
- Indicador `Public`;
- Branch `main`;
- Arquivos do MVP e README.

A captura não deve ser fabricada, nem produzida por edição artificial que simule o GitHub.
