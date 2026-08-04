# Task: System Prompt Engineering

Write a system prompt for an AI code review agent. The agent should:

1. Review pull requests for code quality
2. Check for common issues (TODO stubs, generic names, missing tests)
3. Provide actionable feedback with specific line references
4. Maintain a professional but constructive tone

The system prompt must define:
- The agent's role and expertise
- Specific evaluation criteria
- Output format requirements
- Tone and communication style
- How to handle edge cases

Target: The prompt should be specific enough that two different model runs produce consistent, high-quality reviews on the same PR.

Success criteria:
- Clear role definition (one sentence, not a paragraph)
- Specific evaluation criteria (not "check for issues")
- Exact output format (not "provide feedback")
- Imperative voice throughout
- No hedging language
