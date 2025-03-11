#!/bin/bash

# Obter o diretório atual
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Tornar o script executável
chmod +x "$DIR/timetracker.py"

# Criar link simbólico para o diretório em /usr/local/bin
ln -sf "$DIR/timetracker.py" "/usr/local/bin/timetracker"

echo "TimeTracker instalado com sucesso!"
echo "Você pode agora usar 'timetracker' de qualquer diretório."