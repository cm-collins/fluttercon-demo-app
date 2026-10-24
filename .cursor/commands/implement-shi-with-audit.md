# implement-shi-with-audit

Automate planning for implementing a specific Linear **SHI** issue, **plus** perform a review-style audit of prerequisite SHI issue(s) to confirm prerequisites were implemented correctly.

This command is **planning-only**: you MUST NOT implement any code until the user explicitly approves the plan.

---

## Preconditions (MANDATORY)

- This command only runs for a specific Linear issue key like `SHI-123`.
- If the user did **not** provide an SHI key, STOP and ask: “Which SHI (e.g., `SHI-123`) do you want me to implement?”
- The user MAY optionally provide prerequisite SHI key(s) to audit in the same message (one or many), e.g.:
  - “implement SHI-109 with audit SHI-127”
  - “implement SHI-109 with audit SHI-127, SHI-128”
  - “implement SHI-109 with audit: SHI-127 SHI-128”

If the user provides prerequisite SHI key(s), you MUST audit **exactly those** (do not infer different prerequisites unless the user asks).

---

## Output rules (MANDATORY)

- The **full implementation plan** must be posted **only** as a Linear comment on the target SHI issue.
- Do **not** paste the full plan into chat (token-saving).
- For the prerequisite audit(s), follow the `/review` command behavior explicitly:
  - @.cursor/commands/review.md
  - and the shared audit framework: @.cursor/prompts/general-code-audit-review-prompt.md
- For each prerequisite SHI audit, you MUST produce audit artifacts (markdown + JSON). To avoid overwriting other reports, write them to SHI-scoped paths:
  - `Output/CodeReview/SHI-<PREREQ>/AUDIT_REPORT_<TIMESTAMP>.md`
  - `Output/CodeReview/SHI-<PREREQ>/AUDIT_REPORT_<TIMESTAMP>.json`
- Do **not** paste the audit markdown report or JSON into chat. Chat output must be a short pointer + summary only.
- Do **not** create any other plan files unless the user explicitly requests it.

---

## Step -1: Load repo standards (MANDATORY)

Before doing anything else (including calling Linear tools or starting prerequisite audit commands), you MUST load the repo’s engineering standards and change gates by reading these files:

- `AGENTS.md`
- `.cursor/skills/senior-software-engineer/SKILL.md`

Hard requirements:

- If you cannot access/read either file, STOP and ask the user to attach/share them (or provide relevant excerpts).
- You MUST apply those rules to all work produced by this command (planning + audit).

Output requirement (auditability):

- In the final chat response, include a short section titled **“Standards loaded”** with:
  - confirmation that you read both files, and
  - one short direct quote from each file (max 1 line each; keep each quote under 120 characters), and
  - 2–5 bullets of the most relevant constraints you applied while executing the audit and writing the plan.

---

## Step 0: Resolve target + prerequisite SHI(s) (MANDATORY)

Do NOT assume “preceding SHI” is `(N-1)`.

### If prerequisites were provided by the user

- Parse the user message for SHI keys after “audit”.
- Validate they look like `SHI-###`. If ambiguous/malformed, STOP and ask for the exact prerequisite SHI key(s).

### Otherwise: infer prerequisites from Linear

1. Retrieve the target SHI in Linear.
2. Identify prerequisite SHI(s) from the strongest available signals:
   - **Blocked-by / dependency relations** on the target issue (preferred)
   - Explicit mentions in the description like “depends on SHI-XXX”, “prerequisite: SHI-XXX”
   - Linked issues / related-to relations that are clearly prerequisites
   - Host project sequencing notes (if the project defines an order)
3. If you cannot confidently identify prerequisite SHI(s), STOP and ask:
   - “Which prerequisite SHI issue(s) should I audit before planning this one?”

Prerequisites may be **one or many** SHI issues.

### Confirmation gate for inferred prerequisites (MANDATORY)

If (and only if) prerequisites were **inferred** (not explicitly provided by the user):

1. Retrieve each inferred prerequisite issue from Linear and capture:
   - SHI key
   - Title
   - The reason it was inferred (e.g., “blocked-by relation”, “mentioned in description”, etc.)
2. In chat, present a short list like:
   - `SHI-127 — <title>` (reason: blocked-by)
   - `SHI-128 — <title>` (reason: mentioned in description)
3. Ask the user to confirm before you audit:
   - “Confirm I should audit these prerequisite issues before planning `SHI-<TARGET>`.”
4. STOP and do not audit until the user explicitly confirms.

If the user says “no” or provides different prerequisite SHI(s), use the user-provided list instead.

---

## Step 1: Load project + issue context in Linear (MANDATORY)

1. Retrieve the **target SHI** using Linear tools.
2. Retrieve each **prerequisite SHI** you identified (or the user provided).
3. If the target SHI belongs to a Linear project:
   - Load the host project description and enough context to understand goals/constraints.
4. Read existing comments on the target + prerequisite issues to avoid duplicating prior decisions.

In the final chat response, include:

- “What I learned from the project” (if applicable)
- “What I learned from the target issue”
- “What I learned from the prerequisite issue(s)”

---

## Step 1.5: Create (or switch to) a working branch for the target SHI (MANDATORY)

Problem this prevents:
- Agents sometimes perform later implementation work on `dev` because branch creation is deferred until “after approval” and can be forgotten. Creating the **local** SHI branch now makes the working state deterministic without implementing code.

Rules:
- You MUST create (or switch to) a **local** `shi-<id>/...` branch for the target SHI while still in planning-only mode.
- You MUST NOT change code.
- You MUST NOT push the branch remote until the plan is explicitly approved.

Minimum workflow (commands):

```bash
git status --porcelain
git fetch origin --prune

BASE_BRANCH="dev"
git show-ref --verify --quiet "refs/remotes/origin/$BASE_BRANCH" || BASE_BRANCH="$(git symbolic-ref -q --short refs/remotes/origin/HEAD | sed 's#^origin/##')"

# Example: SHI_KEY="SHI-172", ISSUE_TITLE="Fix oracle staleness gate"
SHI_KEY="SHI-<NNN>"
ISSUE_TITLE="<issue title>"
SHI_NUMBER="${SHI_KEY#SHI-}"
ISSUE_SLUG="$(printf '%s' "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g; s/-+/-/g' | cut -c1-40)"
[ -n "$ISSUE_SLUG" ] || ISSUE_SLUG="wip"
BRANCH="shi-${SHI_NUMBER}/${ISSUE_SLUG}"
git show-ref --verify --quiet "refs/heads/$BRANCH" && git switch "$BRANCH" || git switch -c "$BRANCH" "origin/$BASE_BRANCH"

git rev-parse --abbrev-ref HEAD
```

Hard stop:
- If `git status --porcelain` is non-empty, STOP and ask the user to clean/stash/commit before you proceed (do not guess what to do with their local changes).

---

## Step 2: Audit prerequisite SHI(s) (MANDATORY)

Goal: validate prerequisites were implemented correctly, using the same audit workflow as `/review`:

- @.cursor/commands/review.md
- @.cursor/prompts/general-code-audit-review-prompt.md

For each prerequisite SHI key `SHI-<PREREQ>`:

### 2.1 Choose audit scope (MANDATORY)

You MUST audit the code associated with the prerequisite SHI. Prefer the strongest evidence source, in this order:

1. **Merged PR** for that SHI:
   - If the SHI links to a PR, use that PR.
   - Otherwise, search merged PRs targeting `dev` containing `SHI-<PREREQ>` in title/body/branch.
2. **Commit history** on `origin/dev` (fallback):
   - Search commit messages for `SHI-<PREREQ>` and use the relevant commit(s)/range.
3. If neither PR nor commits can be identified, STOP and report what link/info is missing.

Minimum commands (examples; adapt as needed):

```bash
git fetch origin --prune
STARTING_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
git switch dev
git pull --ff-only
```

After the prerequisite audit is complete (MANDATORY):

```bash
git switch "$STARTING_BRANCH"
git rev-parse --abbrev-ref HEAD
```

PR-based (preferred):

```bash
gh pr list --base dev --state merged --search "SHI-<PREREQ>" --limit 5
gh pr view <PR_NUMBER> --json url,mergedAt,baseRefName,headRefName,mergeCommit,statusCheckRollup
gh pr diff <PR_NUMBER>
```

Commit-based (fallback):

```bash
git log --oneline --decorate origin/dev --grep "SHI-<PREREQ>"
git show <SHA>
```

### 2.2 Produce audit artifacts (MANDATORY)

- Apply the framework in @.cursor/prompts/general-code-audit-review-prompt.md.
- Write:
  - `Output/CodeReview/SHI-<PREREQ>/AUDIT_REPORT_<TIMESTAMP>.md`
  - `Output/CodeReview/SHI-<PREREQ>/AUDIT_REPORT_<TIMESTAMP>.json`
- Do not stage/commit these artifacts (they are ignored by git).
- Chat output for each prerequisite audit must be short: verdict + P0/P1 titles/locations + artifact paths.

If any prerequisite audit **fails**, you MUST:

- Clearly state prerequisites are not satisfied.
- Do NOT proceed to planning unless the user explicitly asks you to proceed anyway (and you restate the risk).

---

## Step 3: Produce an implementation plan for the target SHI (MANDATORY)

Create a detailed, emoji-styled plan in plain English (same style requirements as `/implement-shi`) and post it as a **new Linear comment** on the target SHI.

Constraints:

- Do NOT post the full plan in chat.
- Do NOT implement code.

---

## Step 4: Report back in chat (MANDATORY)

After posting the plan comment and writing the prerequisite audit artifacts, respond in chat with a short, skimmable summary:

- Target SHI: key + link
- Prerequisite SHI(s) audited: list keys + links
- Audit results (per prerequisite):
  - Verdict (PASS/FAIL)
  - Count of findings by priority (P0/P1/P2/P3)
  - Artifact paths
- Plan posted: confirm it was added as a Linear comment and provide the issue link
- Any blocking questions / confirmations

---

## Step 5: Do not implement until approved (MANDATORY)

After posting the plan and producing the audit artifacts, STOP.

- Do NOT change code.
- Do NOT push the branch remote.

When (and only when) the plan is approved, the next steps will be:

- Push the already-created SHI branch to remote:
  - `git push -u origin HEAD`
- Then proceed with implementation following the approved plan.

