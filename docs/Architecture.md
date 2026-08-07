# Architecture

This document describes the high-level architecture of anti-slop-kit.

## Overview

anti-slop-kit is a text quality analysis toolkit that detects and measures 'slop' - low-quality, AI-generated, or poorly written content.

The system consists of three main components:
1. **Analysis Tools** (tools/aslint/) - Core analysis engine
2. **Evaluation Harness** (evals/) - Framework for running experiments
3. **Infrastructure** (.github/, scripts/) - CI/CD and automation

## Core Analysis Engine

The analysis tools follow a pipeline pattern with three main stages:
1. **Input Processing** - Read and normalize input text
2. **Analysis** - Apply detection rules and scoring
3. **Output Generation** - Format results for consumption

### CLI (cli.py)
Command-line interface that orchestrates the analysis pipeline.

### Lint Tool (lint_tool.py)
Detects low-quality patterns in text including:
- Vague language (very, really, basically)
- Filler words (actually, literally, honestly)
- Weasel words (some people say, it is said)
- Passive voice overuse
- Hedging language

### Rewrite Tool (rewrite_tool.py)
Validates that rewrites improve text quality by comparing original and rewrite.

### Transmit Check (transmit_check.py)
Checks information fidelity through transmission channels.

## Key Design Decisions

1. **Pattern-Based Analysis** - YAML files for pattern definitions
2. **JSON Output Format** - Machine-readable for integration
3. **Modular Tool Design** - Separate tools for different concerns
4. **Exit Codes** - Standard Unix convention for results
5. **Configuration-Driven** - YAML for configuration

## Technology Stack

- **Language:** Python 3.9+
- **Pattern Format:** YAML
- **Output Format:** JSON
- **Testing:** pytest
- **CI/CD:** GitHub Actions
- **Type Checking:** mypy

## Extensibility

### Adding New Patterns
Create new YAML file in pattern directory with regex patterns and suggestions.

### Adding New Tools
Create new tool file in tools/aslint/ and add to CLI dispatcher.

### Adding New Languages
Create new pattern directory and add language-specific patterns.
