Write a system prompt for an AI agent that reviews pull requests for code quality. The agent should check for common issues like TODO stubs, generic variable names, missing error handling, and inadequate tests. The prompt must define the agent's role, evaluation criteria, output format, and tone. It should be specific enough that two different runs on the same PR produce consistent feedback.

The system prompt will be used to configure a code review bot in a CI/CD pipeline. The bot receives PR diffs and must return structured feedback with line numbers and actionable suggestions.
