// VS Code Extension for Anti-Slop Kit
// Provides linting functionality for markdown and text files

const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let diagnosticCollection;
let outputChannel;

/**
 * Activate the extension
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    outputChannel = vscode.window.createOutputChannel('Anti-Slop Kit');
    diagnosticCollection = vscode.languages.createDiagnosticCollection('anti-slop-kit');
    
    outputChannel.appendLine('Anti-Slop Kit extension activated');
    
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('antiSlopKit.lintDocument', lintDocument),
        vscode.commands.registerCommand('antiSlopKit.lintSelection', lintSelection),
        vscode.commands.registerCommand('antiSlopKit.showReport', showReport)
    );
    
    // Register save event listener for auto-linting
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            const config = vscode.workspace.getConfiguration('antiSlopKit');
            if (config.get('enabled') && config.get('autoLint')) {
                lintDocument();
            }
        })
    );
    
    // Register document change listener for real-time feedback
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
            const config = vscode.workspace.getConfiguration('antiSlopKit');
            if (config.get('enabled')) {
                // Debounce linting to avoid excessive calls
                clearTimeout(context.debounceTimer);
                context.debounceTimer = setTimeout(() => {
                    lintDocument();
                }, 1000);
            }
        })
    );
    
    context.subscriptions.push(diagnosticCollection);
    context.subscriptions.push(outputChannel);
}

/**
 * Deactivate the extension
 */
function deactivate() {
    if (outputChannel) {
        outputChannel.appendLine('Anti-Slop Kit extension deactivated');
        outputChannel.dispose();
    }
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
    }
}

/**
 * Lint the current document
 */
async function lintDocument() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }
    
    const document = editor.document;
    const config = vscode.workspace.getConfiguration('antiSlopKit');
    
    if (!config.get('enabled')) {
        outputChannel.appendLine('Anti-Slop Kit is disabled');
        return;
    }
    
    const text = document.getText();
    const language = config.get('language');
    const customRulesPath = config.get('customRulesPath');
    
    outputChannel.appendLine(`Linting document: ${document.fileName}`);
    outputChannel.appendLine(`Language: ${language}`);
    
    try {
        const result = await runLinter(text, language, customRulesPath);
        
        if (config.get('showDiagnostics')) {
            updateDiagnostics(document, result);
        }
        
        showLintResult(result);
    } catch (error) {
        outputChannel.appendLine(`Error: ${error.message}`);
        vscode.window.showErrorMessage(`Anti-Slop Kit error: ${error.message}`);
    }
}

/**
 * Lint the selected text
 */
async function lintSelection() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }
    
    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('No text selected');
        return;
    }
    
    const text = editor.document.getText(selection);
    const config = vscode.workspace.getConfiguration('antiSlopKit');
    const language = config.get('language');
    const customRulesPath = config.get('customRulesPath');
    
    outputChannel.appendLine(`Linting selection (${text.length} chars)`);
    
    try {
        const result = await runLinter(text, language, customRulesPath);
        showLintResult(result);
    } catch (error) {
        outputChannel.appendLine(`Error: ${error.message}`);
        vscode.window.showErrorMessage(`Anti-Slop Kit error: ${error.message}`);
    }
}

/**
 * Show quality report
 */
async function showReport() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }
    
    const document = editor.document;
    const config = vscode.workspace.getConfiguration('antiSlopKit');
    const language = config.get('language');
    const customRulesPath = config.get('customRulesPath');
    const text = document.getText();
    
    try {
        const result = await runLinter(text, language, customRulesPath);
        
        // Create report
        let report = `# Anti-Slop Kit Report\n\n`;
        report += `**File:** ${document.fileName}\n`;
        report += `**Language:** ${result.language || 'auto-detected'}\n`;
        report += `**Words:** ${result.words || 0}\n`;
        report += `**Violations:** ${result.violations || 0}\n`;
        report += `**Score:** ${result.score || 0} per 100 words\n\n`;
        
        if (result.findings && result.findings.length > 0) {
            report += `## Findings\n\n`;
            result.findings.forEach((finding, index) => {
                report += `${index + 1}. **${finding.type}**: ${finding.word}\n`;
                report += `   - Position: ${finding.position}\n`;
                if (finding.message) {
                    report += `   - Message: ${finding.message}\n`;
                }
                report += `\n`;
            });
        } else {
            report += `No violations found! 🎉\n`;
        }
        
        // Show report in new document
        const reportDoc = await vscode.workspace.openTextDocument({
            content: report,
            language: 'markdown'
        });
        await vscode.window.showTextDocument(reportDoc, { preview: true });
    } catch (error) {
        outputChannel.appendLine(`Error: ${error.message}`);
        vscode.window.showErrorMessage(`Anti-Slop Kit error: ${error.message}`);
    }
}

/**
 * Run the linter
 * @param {string} text - Text to lint
 * @param {string} language - Language code
 * @param {string} customRulesPath - Path to custom rules
 * @returns {Promise<object>} Lint result
 */
function runLinter(text, language, customRulesPath) {
    return new Promise((resolve, reject) => {
        // Find linter path
        const extensionPath = path.dirname(__dirname);
        const linterPath = path.join(extensionPath, '..', 'tools', 'aslint', 'lint_tool.py');
        
        if (!fs.existsSync(linterPath)) {
            reject(new Error(`Linter not found at ${linterPath}`));
            return;
        }
        
        // Build command arguments
        const args = [linterPath, '--json'];
        
        if (language && language !== 'auto') {
            args.push('--lang', language);
        }
        
        if (customRulesPath && customRulesPath.trim()) {
            args.push('--rules', customRulesPath);
        }
        
        // Spawn Python process
        const python = spawn('python3', args);
        let stdout = '';
        let stderr = '';
        
        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        python.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Linter exited with code ${code}: ${stderr}`));
                return;
            }
            
            try {
                const result = JSON.parse(stdout);
                resolve(result);
            } catch (error) {
                reject(new Error(`Failed to parse linter output: ${error.message}`));
            }
        });
        
        // Send text to stdin
        python.stdin.write(text);
        python.stdin.end();
    });
}

/**
 * Update diagnostics in Problems panel
 * @param {vscode.TextDocument} document - Document to update
 * @param {object} result - Lint result
 */
function updateDiagnostics(document, result) {
    diagnosticCollection.clear();
    
    if (!result.findings || result.findings.length === 0) {
        return;
    }
    
    const config = vscode.workspace.getConfiguration('antiSlopKit');
    const severityLevel = config.get('severityLevel');
    
    const severityMap = {
        'error': vscode.DiagnosticSeverity.Error,
        'warning': vscode.DiagnosticSeverity.Warning,
        'information': vscode.DiagnosticSeverity.Information
    };
    
    const severity = severityMap[severityLevel] || vscode.DiagnosticSeverity.Warning;
    
    const diagnostics = result.findings.map(finding => {
        // Convert position to line and character
        const position = document.positionAt(finding.position);
        const range = new vscode.Range(position, position);
        
        const message = `${finding.type}: ${finding.word}`;
        const diagnostic = new vscode.Diagnostic(range, message, severity);
        diagnostic.source = 'Anti-Slop Kit';
        
        return diagnostic;
    });
    
    diagnosticCollection.set(document.uri, diagnostics);
}

/**
 * Show lint result in output channel
 * @param {object} result - Lint result
 */
function showLintResult(result) {
    outputChannel.appendLine(`Lint result:`);
    outputChannel.appendLine(`  Words: ${result.words || 0}`);
    outputChannel.appendLine(`  Violations: ${result.violations || 0}`);
    outputChannel.appendLine(`  Score: ${result.score || 0} per 100 words`);
    
    if (result.findings && result.findings.length > 0) {
        outputChannel.appendLine(`  Findings:`);
        result.findings.forEach(finding => {
            outputChannel.appendLine(`    - ${finding.type}: ${finding.word} at position ${finding.position}`);
        });
    }
    
    // Show notification
    if (result.violations === 0) {
        vscode.window.showInformationMessage('Anti-Slop Kit: No violations found! 🎉');
    } else {
        vscode.window.showWarningMessage(
            `Anti-Slop Kit: Found ${result.violations} violation(s) (score: ${result.score})`
        );
    }
}

module.exports = {
    activate,
    deactivate
};
