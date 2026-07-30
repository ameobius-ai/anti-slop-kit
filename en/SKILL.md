---
name: ste-writing
description: Rewrites English prose (documentation, README files, pull request descriptions, error messages, release notes, comments - but not code) into Simplified Technical English based on ASD-STE100. Removes marketing language, passive voice, nominalizations, and LLM slop markers. Two modes, strict and flavored.
---

# ste-writing

Write prose with the rules of Simplified Technical English. Apply these rules to documentation, README files, pull request descriptions, error messages, release notes, and comments. Do not apply them to code, variable names, or command syntax. Do not apply them to marketing copy, essays, or fiction. Controlled language removes voice on purpose.

## Rules

WORDS

- Give one thing one name. Do not call the same object a "job", a "task", and a "run" in one document.
- Give one word one meaning. Do not use "monitor" as both a verb and a screen.
- Choose the short word: start (not commence), use (not utilize), help (not facilitate), make sure (not ensure), before (not prior to), after (not subsequent to), about (not with regard to), get (not obtain), show (not demonstrate), also (not additionally).
- Do not write marketing adjectives: seamless, robust, powerful, cutting-edge, state-of-the-art, effortless, world-class, next-generation, revolutionary, best-in-class.
- Do not write filler openers: it should be noted that, it is important to note, needless to say, at the end of the day.

VERBS

- Use the active voice. Write "the parser reads the file", not "the file is read by the parser".
- Use a verb, not a nominalization. Write "configure the cache", not "perform configuration of the cache".
- Use the imperative for instructions. Put the verb first. Write "Open the file".
- Do not stack auxiliaries. Write "the job fails", not "the job will have been failing".
- Use the simple present for descriptions and states.

SENTENCES

- One idea, one sentence. Maximum 20 words for an instruction, 25 for a description.
- Put the condition before the command. Write "If the server returns 429, send the request again".
- Do not use semicolons. Write two sentences.
- Do not use contractions. Write "do not", not "don't".
- Keep the em dash if it carries real structure. It is not banned by ASD-STE100. Do not use it as a rhythm crutch in every paragraph.

STRUCTURE

- One topic per paragraph. Maximum six sentences.
- Write steps as a numbered vertical list. One action per item.
- Write warnings before the step they apply to, never after.

ANTI-SLOP

- Delete empty openers: "In today's fast-paced world", "Let's dive in", "In the ever-evolving landscape of".
- Delete service replies: "Great question", "I hope this helps".
- Delete self-praise about being concise.
- Delete the false antithesis "not just X, but Y" when nobody claimed X.
- Delete hedges with no data behind them: might, arguably, generally speaking, in most cases.

Write only the requested text. No preamble, no summary, no closing remark.

## Modes

- **strict** - instructions, runbooks, safety text, error messages. Apply every rule and both length limits.
- **flavored** - README files, pull request descriptions, ordinary documentation. Keep sentence length, active voice, plain words, and the anti-slop rules. Allow a mild authorial register.

## Self-check before you return text

1. Is any sentence longer than 20 words? Split it.
2. Is there a semicolon? Replace it with a full stop.
3. Is there a passive clause with a known actor? Make it active.
4. Is there a nominalization? Replace it with a verb.
5. Is there a marketing adjective or a banned word? Delete it or replace it with a fact.
6. Is one thing called by two names? Keep one.
7. Is there an empty opener or a service reply? Delete it.

The linter `ste-lint.py` checks these rules. They fix the FORM of slop. They do not make an empty paragraph true.

## Notes

- ASD-STE100 is a real international standard, Issue 9, dated 15 January 2025. It is owned by ASD and maintained by STEMG. The full specification includes a dictionary of approved words. Request the free copy from asd-ste100.org. The specification text is copyrighted and is not reproduced in this skill.
- Different models produce different slop. Passive voice and nominalization dominate in some, marketing adjectives in others. Check your own baseline with the linter before you trust a rewrite.
- On reference material such as API documentation, a strict rewrite can score worse than the original. Reference text is already terse. Use flavored mode there.
