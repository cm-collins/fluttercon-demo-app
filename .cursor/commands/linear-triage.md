Create Linear issues for implementing this repo's current PRD/TRD or source-of-truth plan. Use small, dependency-aware issues that fit `oracle-lag-sniper` work: Python runtime changes, backtests/research, data pipeline, Safe/security operations, and deployment reliability.

Structure the work using dependency-driven sequencing at two levels:
	1.	across phases, and
	2.	within tasks inside each phase.

Do not create issues just to increase issue count. I want a small set of well-scoped, reasonable units of work. Each issue should represent a chunk that can be executed independently by an AI agent from start to finish, once its dependencies are satisfied.

Each issue should:
	•	have a clear objective and completion criteria
	•	be self-contained enough for one agent to own end-to-end
	•	explicitly note any prerequisite issue(s)
	•	fit logically into the dependency order of the overall project

Prioritize clarity, execution flow, and minimal coordination overhead over exhaustive decomposition.