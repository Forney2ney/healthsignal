# HealthSignal — updated project guidance pack

This pack keeps the ambitious long-term HealthSignal vision while changing the immediate hackathon strategy to a focused, verifiable submission.

## What changed in this update

- Separated the long-term multi-disease platform vision from the narrow hackathon prototype.
- Added an evidence-led rule for choosing the use case only after auditing the actual repository.
- Added the four required project questions: target user, real input/output, baseline comparison and failure case.
- Made held-out evaluation and separate false-positive/false-negative reporting explicit.
- Added public-dataset-only and no-real-patient-record rules.
- Added the exact required health disclaimer.
- Added one-page write-up structure, source-credit requirements, deliverables and final link checks.
- Reprioritised work around the official deadline; extra modalities and interface features are deferred until the core is secure.

## Files

- `HEALTHSIGNAL_PROJECT.md` — full source-of-truth specification.
- `AGENTS.md` — repository-wide instructions for coding agents.
- `CLAUDE.md` — Claude Code entry point.
- `GEMINI.md` — Gemini CLI entry point.
- `HACKATHON_EXECUTION_PLAN.md` — short tactical plan and decision process.
- `SUBMISSION_CHECKLIST.md` — final deliverables and quality checks.
- `AGENT_UPDATE_PROMPT.md` — ready-to-paste prompt for the coding agent.

## Installation

Extract the ZIP and copy the files into the root of the HealthSignal repository. Keep the guidance files alongside the source folders and existing README. If the agent does not automatically read the right file, explicitly tell it to read `HEALTHSIGNAL_PROJECT.md` and `AGENTS.md` first.

## Important

The instructions do not prove that any feature exists. The coding agent must inspect the repository and report the actual state. Never present mock data, simulated screens or planned features as completed AI functionality.
