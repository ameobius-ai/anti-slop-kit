# Hermes Tool Schema Specification

This document describes the JSON schema expected by NousResearch hermes-agent.

## Tool Definition Schema

Tools are defined using JSON Schema format compatible with OpenAI function calling.

### Required fields
- **name**: Unique identifier (snake_case)
- **description**: Human-readable explanation
- **parameters**: JSON Schema object defining inputs

### Optional fields
- **required**: Array of required parameter names
- **enum**: Array of allowed values
- **default**: Default value

## Anti-Slop Kit Tools

### 1. lint_file
Analyzes a markdown file for anti-slop patterns.

Parameters:
- `file_path` (string, required): Path to markdown file
- `language` (string, optional): en/ru/es (default: en)
- `format` (string, optional): text/json/github (default: text)

### 2. lint_text
Analyzes text content directly without requiring a file.

Parameters:
- `text` (string, required): Text to analyze
- `language` (string, optional): en/ru/es (default: en)

### 3. rewrite_section
Rewrites text to improve clarity and remove slop.

Parameters:
- `text` (string, required): Original text
- `language` (string, required): en/ru/es
- `instructions` (string, optional): Specific rewrite instructions

### 4. transmit_check
Validates fidelity during agent-to-agent transmission.

Parameters:
- `original` (string, required): Original text
- `transmitted` (string, required): Transmitted text
- `strict` (boolean, optional): Enable strict checking

## Tool Call Format

Hermes agents use the OpenAI function calling format:

**Request:**
- `id`: Unique call identifier
- `type`: Always "function"
- `function.name`: Tool to invoke
- `function.arguments`: Parameter values (JSON object)

**Response:**
- `id`: Call identifier
- `result.success`: Boolean success flag
- `result.data`: Tool output (on success)
- `result.error`: Error details (on failure)

## Version Information

- **Hermes Agent**: 1.0.0 (pinned)
- **Schema**: OpenAI function calling v1

## References

- [NousResearch hermes-agent](https://github.com/NousResearch/hermes-agent)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [JSON Schema](https://json-schema.org/)

Replaces closed PR #47 (recreated from fresh main).