# AI Coding Principles (after Andrej Karpathy)

Guidelines for working with an AI coding assistant, based on Andrej Karpathy's observations about where LLMs commonly go wrong when writing code:

- They make wrong assumptions and keep going without checking.
- They don't manage their own confusion, don't ask clarifying questions, and don't point out inconsistencies or tradeoffs.
- They overcomplicate code and APIs, add abstractions nobody needs, and leave dead code behind.
- They change or delete code and comments they weren't asked to touch, sometimes as side effects.

The principles below address each of these. They favor caution over speed. For trivial tasks, use judgment.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If you're uncertain, ask.
- If the request can be read more than one way, lay out the readings. Don't pick one silently.
- If a simpler approach exists, say so. Push back when it's warranted.
- If something is unclear, stop. Name what's confusing and ask.

> Wrong assumptions that go unchecked turn into wasted work.

## 2. Simplicity First

**Write the minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for code that is used once.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for scenarios that can't happen.
- If you wrote 200 lines and it could be 50, rewrite it.

**Check:** Would a senior engineer call this overcomplicated? If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match the existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it. Don't delete it.

When your changes create orphans:

- Remove imports, variables, and functions that **your** changes made unused.
- Don't remove pre-existing dead code unless asked.

**Check:** Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until they're verified.**

Turn tasks into verifiable goals:

| Instead of…            | Do this…                                                     |
| ---------------------- | ------------------------------------------------------------ |
| "Add validation"       | Write tests for invalid inputs, then make them pass          |
| "Fix the bug"          | Write a test that reproduces it, then make it pass           |
| "Refactor X"           | Make sure tests pass before and after                        |

For multi-step tasks, write a short plan where each step has a check:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let the AI loop on its own. Weak criteria ("make it work") mean constant clarification.

> LLMs are very good at looping until they meet a specific goal. Don't tell them what to do; give them success criteria and let them work toward them.

---

## Signs These Principles Are Working

- Fewer unnecessary changes in diffs.
- Fewer rewrites caused by overcomplication.
- Clarifying questions come **before** implementation, not after mistakes.
- Clean, minimal PRs with no drive-by refactoring.
