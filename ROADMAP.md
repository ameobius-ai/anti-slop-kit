# Roadmap

This document outlines the planned development direction for anti-slop-kit.

## Current Status (2026-08-05)

### Completed Features
- ✅ English and Russian linters with comprehensive rule sets
- ✅ Markdown structure analysis
- ✅ Code comment analysis  
- ✅ Technical register allowlist (reduces false positives)
- ✅ Enhanced JSON output with line-number findings
- ✅ Eval harness with 6 tasks per language
- ✅ Pre-commit hooks for automated checking
- ✅ Comprehensive usage documentation
- ✅ 51+ unit tests with full coverage

### In Progress
- 🔄 PR #13: Technical register allowlist for EN linter (issue #12)
- 🔄 PR #19: Enhanced JSON output with findings (issue #17)

## Q3 2026: Foundation & Polish

### High Priority

**Spanish Language Support (Issue #16)**
- Create `es/SKILL.md` with Spanish writing guidelines
- Implement `es/ste-lint.py` with Spanish-specific rules
- Add Spanish samples and tests
- Impact: 400M+ Spanish speakers

**Editor Integration**
- VS Code extension for inline diagnostics
- Neovim plugin with LSP support
- Emacs integration
- Impact: Real-time feedback during writing

**SARIF Output Format**
- Add `--format sarif` for Static Analysis Results Interchange Format
- Enables integration with GitHub Security tab, SonarQube, etc.
- Impact: Enterprise tool compatibility

### Medium Priority

**Eval Harness Improvements**
- Add 6 more tasks per language (technical writing, error messages, changelogs)
- Statistical analysis (confidence intervals, effect sizes)
- Model comparison dashboard
- Impact: Better measurement of skill effectiveness

**Performance Optimization**
- Profile and optimize linter for large documents (>10k words)
- Parallel processing for batch linting
- Streaming mode for real-time checking
- Impact: 10x faster on large codebases

## Q4 2026: Ecosystem & Scale

### High Priority

**Package Distribution**
- Publish to PyPI: `pip install anti-slop-kit`
- Publish to npm: `npm install @anti-slop/lint`
- Homebrew formula for macOS
- Impact: Easier installation

**GitHub Action Marketplace**
- Official GitHub Action: `uses: ameobius-ai/anti-slop-kit@v1`
- Configurable thresholds and languages
- PR comment with findings
- Impact: One-click CI integration

**Multi-File Reporting**
- Generate HTML report across entire documentation set
- Track quality trends over time
- Identify worst offenders
- Impact: Team-wide quality visibility

### Medium Priority

**Additional Languages**
- French (`fr/`)
- German (`de/`)
- Portuguese (`pt/`)
- Impact: Global coverage

**Custom Rule System**
- User-defined rules via YAML/JSON config
- Project-specific banned words
- Severity levels (error/warning/info)
- Impact: Customization without forking

## 2027: Intelligence & Automation

### Vision

**AI-Assisted Rewriting**
- Suggest fixes for violations (not just detect)
- Context-aware rewrites (understand document structure)
- Batch rewrite mode with preview
- Impact: 10x faster remediation

**Learning from Corrections**
- Track user acceptances/rejections of suggestions
- Improve suggestion quality over time
- Project-specific style learning
- Impact: Personalized linting

**Integration Ecosystem**
- Slack/Discord bots for documentation quality
- Jira/Linear integration for tracking violations
- Grafana dashboards for quality metrics
- Impact: Quality as continuous process

## Backlog (Unscheduled)

These ideas are valuable but not yet prioritized:

### Technical
- **Incremental linting**: Only re-check changed portions
- **Language detection**: Auto-detect document language
- **Semantic analysis**: Understand context, not just patterns
- **Grammar integration**: Work with grammar checkers (LanguageTool, etc.)

### User Experience
- **Web interface**: Online demo without installation
- **Browser extension**: Check documentation while browsing
- **Mobile app**: Quick checks on the go
- **IDE plugins**: JetBrains, Xcode, Visual Studio

### Research
- **Effectiveness studies**: Measure impact on documentation quality
- **User surveys**: Understand pain points and workflows
- **Benchmark dataset**: Standard corpus for comparing tools
- **Academic papers**: Publish research on technical writing patterns

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to help with these items.

High-impact areas where help is especially welcome:
- Spanish language support (native speakers)
- Editor extensions (VS Code, Neovim maintainers)
- Eval harness improvements (statistics, visualization)
- Documentation and examples

## Principles

These guide our development:

1. **Standalone**: No external dependencies (stdlib only)
2. **Deterministic**: Same input always produces same output
3. **Fast**: Sub-second for typical documents
4. **Accurate**: Minimize false positives
5. **Actionable**: Every violation has a clear fix
6. **Portable**: Works on any platform with Python 3.9+

## Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes to output format or API
- **MINOR**: New rules, languages, or features (backward compatible)
- **PATCH**: Bug fixes and performance improvements

Current version: 1.0.0 (planned after merging PRs #13, #19)

## Questions?

- Open an issue for feature requests
- Start a discussion for brainstorming
- Submit a PR for implementations

Last updated: 2026-08-05
