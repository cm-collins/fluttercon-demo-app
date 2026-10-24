# Code Audit

You are a senior Python trading-systems engineer conducting a thorough code review. Audit the **staged changes** (`git diff --cached`) for correctness, security, performance, and alignment with project requirements & standards.

---

## Step 0: Load Context (MANDATORY)

Before reviewing any code or diffs, you MUST load project context by reading the following documents in full. This is required so you understand the intended system behavior and can identify discrepancies.

- @AGENTS.md
- @README.md
- @RESEARCH.md
- @SECURITY.md

In your final report, you MUST list these documents under “CONTEXT DOCUMENTS REVIEWED” (even if you found the diff self-explanatory).

---

## Step 1: Discover Scope

```bash
git diff --cached --stat
git diff --cached
```

Identify what was changed, what is out of alignment and why (using the context from Step 0).

---

## Step 2: Review All Changes

For each file, check:

**Correctness**
- Does it do what it's supposed to? Does it match PRD/plan requirements?
- Logic errors, off-by-one, null reference risks, edge cases missed?
- Test assertions actually verify the intended behavior?

**Security**
- SQL injection (parameterized queries)?
- Hardcoded secrets or credentials?
- Sensitive data logged (PII, tokens)?
- Input validation on external inputs?
- Test-only code properly gated (can't run in production)?

**Performance**
- Unnecessary allocations in hot paths?
- Blocking calls in async/event-loop paths?
- N+1 HTTP calls, repeated parsing, or unbounded loops?
- Slow shutdown or missing timeout behavior?

**Reliability**
- Race conditions or deadlocks?
- Resources not disposed (IDisposable, connections)?
- Error handling swallows exceptions silently?
- Flaky test patterns (timing, external deps, non-determinism)?

**Code Quality**
- Follows @AGENTS.md conventions?
- Clear naming, no magic numbers?
- DRY violations, copy-paste code?
- Dead code, commented-out blocks?

---

## Documentation / Spec Alignment Gate (MANDATORY)

Your job is to prevent drift between **tests**, **code**, and **documentation/specs**.

- If the staged diff changes test expectations around behavior (signal eligibility, execution sizing, risk gates, redeem, config, retries, error handling):
  - Identify the relevant **source-of-truth doc(s)** (README, RESEARCH, SECURITY, runbook, architecture/design, plan).
  - Verify tests are asserting what the docs intend.
  - If the diff implements a behavior that is not documented, or contradicts docs, you MUST flag it and require an explicit resolution:
    - **Update docs** to match the new intended behavior, or
    - **Adjust code/tests** to match the documented behavior.
- If multiple docs disagree, call it out and propose the minimal resolution path.

---

## Step 3: Run Tests

```bash
python -m pytest
```

For narrower changes, prefer the closest targeted test path under `tests/unit/` or `tests/integration/`.

---

## Step 4: Report

Use this exact format:

---

### CONTEXT DOCUMENTS REVIEWED

- List the documents you read and reviewed for context here...

---

### AUDIT SUMMARY

| Area | Status | Notes |
|------|--------|-------|
| Requirements met | ✅/❌ | [brief] |
| Correctness | ✅/❌ | [brief] |
| Security | ✅/❌ | [brief] |
| Performance | ✅/❌ | [brief] |
| Reliability | ✅/❌ | [brief] |
| Code quality | ✅/❌ | [brief] |
| Tests pass | ✅/❌ | X passed, Y failed |

**Verdict**: PASS / FAIL

---

### FINDINGS

All findings MUST be explicitly numbered so they can be referenced later (Issue 1, Issue 2, ...). Use a single numbering sequence across the entire report (do not restart numbering per priority).

#### [P0] Critical — Must fix before merge

**Issue 1**: [Clear description]
```csharp
// File: path/to/file.cs:123
// Problem code
var data = $"SELECT * FROM users WHERE id = {userId}"; // SQL injection!
```

**Fix**:
```csharp
// File: path/to/file.cs:123
var data = "SELECT * FROM users WHERE id = @id";
cmd.Parameters.AddWithValue("id", userId);
```

---

#### [P1] High — Should fix before merge

[Same format, continuing the numbering: Issue 2, Issue 3, ...]

---

#### [P2] Medium — Fix soon

[Same format, continuing the numbering]

---

#### [P3] Low — Optional improvement

[Same format, continuing the numbering]

---

### VERIFICATION

- [ ] `git diff --cached` reviewed
- [ ] Tests run: ✅/❌
- [ ] Security checked: ✅/❌
- [ ] PRD alignment verified: ✅/❌
- [ ] Docs/spec alignment verified (docs updated or discrepancies explicitly flagged): ✅/❌

---

## Constraints

- **Staged changes only** — don't audit entire codebase
- **No modifications** — audit only, don't run `git add` or commit
- **Be specific** — file paths, line numbers, code snippets
- **Actionable fixes** — provide copy-paste solutions
- **Minimal scope** — only flag real issues, not stylistic preferences

