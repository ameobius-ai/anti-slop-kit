# Hermes Tool Schema Specification

This document describes the JSON schema expected by NousResearch hermes-agent.

## Tool Definition Schema

Tools are defined using JSON Schema format compatible with OpenAI function calling.

Required fields:
- name: Unique identifier (snake_case)
- description: Human-readable explanation
- parameters: JSON Schema object defining inputs

Optional fields:
- required: Array of required parameter names
- enum: Array of allowed values
- default: Default value

## Anti-Slop Kit Tools

### 1. lint_file

Analyzes a markdown file for anti-slop patterns.

Parameters:
- file_path (string, required): Path to markdown file
- language (string, optional): en/ru/es (default: en)
- format (string, optional): text/json/github (default: text)

### 2. lint_text

Analyzes text content directly without requiring a file.

Parameters:
- text (string, required): Text to analyze
- language (string, optional): en/ru/es (default: en)

### 3. rewrite_section

Rewrites text to improve clarity and remove slop.

Parameters:
- text (string, required): Original text
- language (string, required): en/ru/es
- instructions (string, optional): Specific rewrite instructions

### 4. transmit_check

Validates fidelity during agent-to-agent transmission.

Parameters:
- original (string, required): Original text
- transmitted (string, required): Transmitted text
- strict (boolean, optional): Enable strict checking

## Tool Call Format

Request:
{ id: call_id, type: function, function: { name, arguments } }

Response:
{ id: call_id, result: { success: bool, data/error } }

## Version Information

- Hermes Agent: 1.0.0 (pinned)
- Schema: OpenAI function calling v1
- Last updated: 2026-08-06

## References

- [NousResearch hermes-agent](https://github.com/NousResearch/hermes-agent)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [JSON Schema](https://json-schema.org/)

Refs #37