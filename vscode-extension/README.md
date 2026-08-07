# Anti-Slop Kit VS Code Extension

VS Code extension for detecting and removing AI slop from technical prose using deterministic linters.

## Features

- **Real-time Linting**: Automatically lint markdown and text files as you write
- **Multi-language Support**: English, Russian, Spanish, French, and German with auto-detection
- **Diagnostics Panel**: See violations in the Problems panel with severity levels
- **Command Palette**: Quick access to lint commands
- **Custom Rules**: Support for project-specific pattern rules via YAML
- **Quality Reports**: Generate detailed quality reports
- **Configurable**: Customize behavior through settings

## Installation

### From Source (Development)

1. Clone the repository
2. Navigate to vscode-extension directory
3. Run: npm install
4. Press F5 in VS Code to launch Extension Development Host

### From VSIX (Production)

1. Build: cd vscode-extension && npm install && npx vsce package
2. Install: code --install-extension anti-slop-kit-1.0.0.vsix

## Usage

### Automatic Linting

By default, the extension automatically lints documents on save. You'll see:
- Diagnostics in the Problems panel
- Status bar indicator showing current score
- Notifications for violations

### Manual Linting

Open the Command Palette (Ctrl+Shift+P / Cmd+Shift+P) and use:

- **Anti-Slop Kit: Lint Current Document** - Lint the entire document
- **Anti-Slop Kit: Lint Selection** - Lint only selected text
- **Anti-Slop Kit: Show Quality Report** - Generate detailed report

### Configuration

Open Settings (Ctrl+, / Cmd+,) and search for "Anti-Slop Kit":

- **Enabled**: Enable/disable the extension
- **Auto Lint**: Automatically lint on save
- **Language**: Language for linting (auto, en, ru, es, fr, de)
- **Max Score**: Maximum acceptable slop score per 100 words (default: 5.0)
- **Custom Rules Path**: Path to custom rules YAML file
- **Show Diagnostics**: Show diagnostics in Problems panel
- **Severity Level**: Severity level for diagnostics (error, warning, information)

### Custom Rules

Create a custom rules file (.anti-slop/rules.yaml) in your project and set the path in settings.

## Requirements

- VS Code 1.74.0 or higher
- Python 3.8 or higher
- Anti-slop-kit tools installed in the repository

## Language Support

The extension supports 5 languages with automatic detection:

- **English (en)**: ASD-STE100 mechanics
- **Russian (ru)**: GOST R 58049-2017
- **Spanish (es)**: Plain Language patterns
- **French (fr)**: Plain Language patterns
- **German (de)**: Leichte Sprache principles

Language detection is automatic based on character sets.

## Troubleshooting

### Extension Not Working

1. Check if Python is installed: python3 --version
2. Check the Output channel for errors
3. Verify anti-slop-kit is properly installed
4. Check extension settings are enabled

### Linter Not Found

Ensure the repository structure is correct with tools/aslint/lint_tool.py present.

### Custom Rules Not Loading

1. Verify the path is correct in settings
2. Check the YAML file syntax
3. View the Output channel for error messages

## Development

### Project Structure

- package.json: Extension manifest
- extension.js: Main extension logic
- README.md: This file

### Building

Run: npm install && npm run compile

### Testing

Press F5 to launch Extension Development Host, open a markdown file, and test linting commands.

### Packaging

Run: npm install -g @vscode/vsce && vsce package

## License

MIT License - see LICENSE file for details

## Related

- Anti-Slop Kit Repository: https://github.com/ameoblius-ai/anti-slop-kit
- Custom Rules Documentation: ../docs/CUSTOM_RULES.md
- CI/CD Integration Guide: ../docs/CICD_INTEGRATION.md
- Usage Guide: ../docs/USAGE.md

## Support

- Issues: https://github.com/ameoblius-ai/anti-slop-kit/issues
- Discussions: https://github.com/ameoblius-ai/anti-slop-kit/discussions
