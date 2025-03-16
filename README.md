# Timetracker

Ferramenta de linha de comando para rastrear horas de trabalho.

## Instalação

Para usar o gerenciador de qualquer diretório, adicione a pasta bin ao PATH do seu sistema.

## Comandos

- `start <empresa>`: Inicia o rastreamento de tempo para uma empresa
- `stop`: Finaliza o rastreamento atual
- `show`: Exibe registros de tempo
  - `-e, --empresa`: Filtra por empresa
  - `-i, --inicio`: Data inicial (YYYY-MM-DD)
  - `-f, --fim`: Data final (YYYY-MM-DD)
- `status`: Verifica o status atual de rastreamento
- `watch`: Exibe o tempo em execução em tempo real
- `calendar [offset]`: Mostra calendário visual do mês
  - `offset`: Deslocamento do mês (0=atual, -1=anterior, 1=próximo)
