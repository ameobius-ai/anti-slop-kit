# Troubleshooting & FAQ

Common issues and solutions for anti-slop-kit.

## Installation Issues

### Issue: ModuleNotFoundError

**Solution:** Reinstall the package with `pip install --upgrade anti-slop-kit`

### Issue: Permission denied

**Solution:** Use `pip install --user anti-slop-kit` or virtual environment

## Usage Issues

### Issue: Configuration file not found

**Solution:** Create `.anti-slop.yaml` in project root with strictness and threshold settings

### Issue: High false positive rate

**Solution:** Adjust strictness level, add custom exclusions, customize pattern matching

### Issue: Slow performance

**Solution:** Use batch processing, exclude unnecessary directories, analyze changed files only

## Configuration Issues

### Issue: Custom patterns not working

**Solution:** Check YAML syntax, verify regex, test with small sample, check logs

### Issue: Threshold too strict/lenient

**Solution:** Adjust threshold value (90+ for high, 70-89 for medium, below 70 for low)

## Integration Issues

### Issue: Pre-commit hook fails

**Solution:** Update pre-commit, reinstall hooks, test manually with `pre-commit run --all-files`

### Issue: GitHub Actions workflow fails

**Solution:** Check Python version (3.9+), verify installation, check threshold, review logs

## Performance Issues

### Issue: Analysis takes too long

**Solution:** Use parallel processing, exclude large directories, analyze specific file types only

### Issue: High memory usage

**Solution:** Process in smaller batches, use streaming mode, increase memory, close other apps

## Common Questions

### Q: What is the scoring system?

**A:** Scores 0-100: 90-100 Excellent, 70-89 Good, 50-69 Fair, 0-49 Poor

### Q: How do I customize patterns?

**A:** Add custom_patterns section to configuration file with name, regex, severity, message

### Q: Can I use with other languages?

**A:** Currently English only, other languages planned for future releases

### Q: How do I report bugs?

**A:** Open GitHub issue with description, reproduction steps, expected vs actual, environment

## Getting Help

1. Check documentation in docs/
2. Search existing GitHub issues
3. Open new issue with detailed information
4. Join community discussions

## Contributing

Found a solution? Contribute by forking repo, adding to this document, opening PR.
See CONTRIBUTING.md for details.