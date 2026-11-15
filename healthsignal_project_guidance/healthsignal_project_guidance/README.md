# HealthSignal project guidance files

Copy the files in this folder into the **root of your HealthSignal
repository**.

## Files

-   `HEALTHSIGNAL_PROJECT.md` --- the complete project operating
    specification and source of truth.
-   `AGENTS.md` --- concise repository instructions for agents that
    support AGENTS.md (including many Codex/OpenCode workflows).
-   `CLAUDE.md` --- project guidance entry point for Claude Code.
-   `GEMINI.md` --- project guidance entry point for Gemini CLI.

## How to use

1.  Copy all four files into the root of your project, beside your
    source folders and README.
2.  Start your AI coding agent from that project directory.
3.  Ask it to inspect the repository and follow its project
    instructions.
4.  Keep `HEALTHSIGNAL_PROJECT.md` as the central specification. Update
    it if the project's goals or constraints change.
5.  Ask the agent to maintain `PROJECT_STATUS.md` and `DECISIONS.md` as
    it works.

Not every AI coding tool automatically reads the same instruction
filename. `AGENTS.md`, `CLAUDE.md` and `GEMINI.md` cover several common
conventions. For another agent, configure its project-instructions
feature to read `HEALTHSIGNAL_PROJECT.md`, or tell it once to read that
file at the beginning of the session.

These files guide the agent; they do not grant it tools, permissions,
API access or automatic background execution.
