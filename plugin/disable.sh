#!/bin/bash
# anti-slop-kit plugin disable script

set -e

echo "Disabling anti-slop-kit plugin..."

CONFIG_DIR="${HOME}/.config/anti-slop-kit"

# Check if plugin is enabled
if [ ! -f "$CONFIG_DIR/enabled" ]; then
    echo "Plugin is not enabled"
    exit 0
fi

# Remove enabled flag
rm -f "$CONFIG_DIR/enabled"
echo "✓ Removed enabled flag"

# Disable git hooks in current repository if .git exists
if [ -d ".git/hooks" ]; then
    echo "Disabling git hooks in current repository..."
    
    # Disable pre-commit hook
    if [ -f ".git/hooks/pre-commit" ]; then
        if grep -q "anti-slop" ".git/hooks/pre-commit" 2>/dev/null; then
            rm -f ".git/hooks/pre-commit"
            echo "  ✓ Disabled pre-commit hook"
        fi
    fi
    
    # Disable pre-push hook
    if [ -f ".git/hooks/pre-push" ]; then
        if grep -q "anti-slop" ".git/hooks/pre-push" 2>/dev/null; then
            rm -f ".git/hooks/pre-push"
            echo "  ✓ Disabled pre-push hook"
        fi
    fi
fi

echo ""
echo "✓ Plugin disabled successfully!"
echo ""
echo "The anti-slop command is still installed but not active."
echo "To completely remove: bash plugin/uninstall.sh"
echo "To re-enable: bash plugin/enable.sh"
