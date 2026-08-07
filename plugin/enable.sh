#!/bin/bash
# anti-slop-kit plugin enable script

set -e

echo "Enabling anti-slop-kit plugin..."

INSTALL_DIR="${HOME}/.local/share/anti-slop-kit"
BIN_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.config/anti-slop-kit"

# Check if plugin is installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Error: anti-slop-kit is not installed"
    echo "Run 'bash plugin/install.sh' first"
    exit 1
fi

# Check if CLI command exists
if [ ! -f "$BIN_DIR/anti-slop" ]; then
    echo "Error: anti-slop command not found"
    echo "Run 'bash plugin/install.sh' first"
    exit 1
fi

# Create config directory
mkdir -p "$CONFIG_DIR"

# Create enabled flag
touch "$CONFIG_DIR/enabled"

# Enable git hooks in current repository if .git exists
if [ -d ".git" ]; then
    echo "Enabling git hooks in current repository..."
    
    # Create hooks directory if it doesn't exist
    mkdir -p .git/hooks
    
    # Enable pre-commit hook
    if [ -f "$INSTALL_DIR/hooks/pre-commit" ]; then
        cp "$INSTALL_DIR/hooks/pre-commit" .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        echo "  ✓ Enabled pre-commit hook"
    fi
    
    # Enable pre-push hook
    if [ -f "$INSTALL_DIR/hooks/pre-push" ]; then
        cp "$INSTALL_DIR/hooks/pre-push" .git/hooks/pre-push
        chmod +x .git/hooks/pre-push
        echo "  ✓ Enabled pre-push hook"
    fi
fi

# Update PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "Adding $BIN_DIR to PATH..."
    export PATH="$BIN_DIR:$PATH"
    echo "  ✓ Added to current session"
    echo ""
    echo "To make this permanent, add to your shell profile:"
    echo "  echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc"
fi

echo ""
echo "✓ Plugin enabled successfully!"
echo ""
echo "You can now use:"
echo "  anti-slop lint <file>"
echo "  anti-slop rewrite <original> <rewrite>"
echo "  anti-slop eval"
echo ""
echo "To disable: bash plugin/disable.sh"
