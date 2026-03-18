#!/bin/bash

# Script de instalação do Timetracker
# Adiciona automaticamente a pasta bin ao PATH do sistema

# Obtém o diretório do projeto
PROJECT_DIR=$(dirname "$(readlink -f "$0")")
BIN_DIR="$PROJECT_DIR/bin"

# Verifica se o diretório bin existe
if [ ! -d "$BIN_DIR" ]; then
    echo "Erro: Diretório bin não encontrado em $BIN_DIR"
    exit 1
fi

# Detecta o shell do usuário
SHELL_NAME=$(basename "$SHELL")
SHELL_RC=""

case "$SHELL_NAME" in
    bash)
        SHELL_RC="$HOME/.bashrc"
        ;;
    zsh)
        SHELL_RC="$HOME/.zshrc"
        ;;
    fish)
        SHELL_RC="$HOME/.config/fish/config.fish"
        ;;
    *)
        echo "Shell não detectado ou não suportado. Usando .bashrc como padrão."
        SHELL_RC="$HOME/.bashrc"
        ;;
esac

# Verifica se o PATH já está configurado
if grep -q "# Timetracker PATH" "$SHELL_RC" 2>/dev/null; then
    echo "O Timetracker já está configurado no PATH em $SHELL_RC"
    exit 0
fi

# Adiciona o diretório bin ao PATH
echo "" >> "$SHELL_RC"
echo "# Timetracker PATH" >> "$SHELL_RC"
echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"

echo "✓ Timetracker instalado com sucesso!"
echo ""
echo "O diretório $BIN_DIR foi adicionado ao PATH em:"
echo "  $SHELL_RC"
echo ""
echo "Para aplicar as mudanças, execute:"
echo "  source $SHELL_RC"
echo ""
echo "Ou abra um novo terminal."
echo ""
echo "Após isso, você poderá usar o comando 'timetracker' de qualquer diretório."
