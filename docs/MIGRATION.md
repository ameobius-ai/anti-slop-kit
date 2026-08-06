# Migration Guide

Guide for upgrading between major versions of anti-slop-kit.

## Version 1.x to 2.0

### Breaking Changes

**Configuration Format:**
- v1.x: Config values wrapped in `config:` key
- v2.0: Config values at root level
- Action: Remove `config:` wrapper from .anti-slop.yaml

**API Changes:**
- v1.x: `Analyzer().check(text)`
- v2.0: `analyze_text(text)`
- Action: Update imports and function calls

**CLI Changes:**
- v1.x: `anti-slop check` and `anti-slop batch`
- v2.0: `anti-slop analyze` for all operations
- Action: Update scripts and CI/CD pipelines

### Migration Steps

1. Update package: `pip install --upgrade anti-slop-kit`
2. Update configuration: Remove `config:` wrapper from YAML
3. Update code: Replace Analyzer class with analyze_text function
4. Update scripts: Use `analyze` command instead of `check` or `batch`
5. Test thoroughly before deploying to production

### Troubleshooting

**ImportError: cannot import name 'Analyzer'**
- Solution: Use `from anti_slop_kit import analyze_text`

**Configuration not loading**
- Solution: Remove `config:` wrapper from YAML file

**CLI commands not found**
- Solution: Use `anti-slop analyze` instead of old commands

### Need Help?

- Check TROUBLESHOOTING.md for common issues
- Open a GitHub issue for specific problems
- Review CHANGELOG.md for detailed changes

## Version 0.x to 1.0

First stable release with:
- Stabilized API
- Improved documentation
- Better error handling
- Performance optimizations

Review CHANGELOG.md for specific changes from beta versions.

## Future Versions

Migration guides for future versions will be added here.
Subscribe to GitHub releases to be notified of new versions.