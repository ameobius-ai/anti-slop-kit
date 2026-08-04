# Release notes: v2.4

This release changes the configuration format and makes queries faster.

## Before you update

Version 2.4 does not read v1 configuration files. Convert your file first:

```
asdk config migrate config.yaml
```

The command writes `config.yaml.v2` and keeps the old file.

## Changes

- Queries on tables of more than 1 million rows are 40 percent faster.
- The `--strict` flag stops the run at the first error. Before, it stopped at the end of the file.
- The `legacy_mode` option is removed. Use `compat_level: 1`.

## If the update fails

1. Read the log in `/var/log/asdk/update.log`.
2. Find the first line that starts with `ERROR`.
3. Send that line and your `config.yaml` to support@example.com.
