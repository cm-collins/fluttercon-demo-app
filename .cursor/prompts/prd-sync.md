# PRD Sync Issue Investigation

I've been assigned a task to resolve all issues under the Linear project named **PRDSync1**. You will be the agent assisting me to resolve these issues.

I now want us to work on **SHI-XX**.

---

## Your Task

### Step 1: Investigate

First, answer these questions:

1. **Does this issue exist?** — Verify whether the issue is real and valid in this codebase. If not, explain why.
2. **PRD vs. Reality** — What does the PRD say should happen? What is the code actually doing? Where's the gap?

Then, explicitly enumerate the gaps you found as a numbered list so they can be referenced later in the write-up:

## Issues (numbered)

1. **Issue 1** — <short title>
2. **Issue 2** — <short title>
   - Only include additional issues if they are truly distinct; don't over-split.

### Step 2: Produce an Explainer

If the issue is valid, produce an **explainer** that helps someone — even someone completely new to the codebase — quickly understand and act on this issue.

Your explainer must enable a reader to quickly understand:

1. **How the system works** — Enough context about the relevant part of the system to understand the issue
2. **What the issue is** — A clear explanation of what's going wrong or what's missing
3. **Why it's actually an issue** — The real-world impact, who's affected, and which requirements are violated
4. **The options for resolving it** — At least two approaches, with pros and cons of each
5. **Your recommended option** — Which approach you'd choose and why

---

## Format Guidelines

You have flexibility in how you structure the explainer — adapt it to what makes sense for the specific issue. Some issues need state diagrams; others need code snippets; others need before/after comparisons.

**What matters most:**
- Someone new to the codebase can understand it in one read
- Use plain English, not jargon
- Show concrete examples (actual file paths, status values, code paths)
- Include a summary table for quick reference
- List the key files involved so the reader knows where to look
- Keep issue numbering consistent (e.g., if you refer to "Issue 2" in one section, it must refer to the same issue everywhere)

**Useful techniques (use when appropriate):**
- State diagrams for workflow issues
- "Happy path vs failure scenario" comparisons for bugs
- Tables for comparing options or summarizing states
- Code snippets when the root cause is in specific logic
- Mermaid diagrams for complex flows

---

## Checklist Before Finishing

- [ ] Could someone new to the codebase understand this in one read?
- [ ] Is the root cause clearly identified?
- [ ] Are at least two resolution options presented with pros/cons?
- [ ] Is there a clear recommendation?
- [ ] Are the key files listed so the reader knows where to look?
- [ ] If database tables are involved, have you verified the actual schema?

---

## Example Outline

Use a repo-specific example when helpful. For this codebase, useful explainers often involve one of:

- a runtime trading safety issue, such as stale oracle data not blocking an entry
- a backtest/runtime parity issue, such as signal eligibility differing between live and historical paths
- a Safe/security issue, such as a module permission or allowance path being broader than intended
- an operations issue, such as a deployment config value drifting from `.env.example` or Key Vault defaults

Keep examples grounded in actual files such as `src/oracle_lag_sniper/config.py`, `src/oracle_lag_sniper/signal.py`, `src/oracle_lag_sniper/execution.py`, `tests/integration/test_signal_parity.py`, `security/safev2/`, or `infrastructure/`.
