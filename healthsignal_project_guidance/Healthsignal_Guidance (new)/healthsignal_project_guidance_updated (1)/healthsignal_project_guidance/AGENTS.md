# HealthSignal repository instructions

Before planning or making significant changes, read `HEALTHSIGNAL_PROJECT.md` in full. It is the source of truth.

## Hackathon execution mode

The long-term product is a multimodal, multi-disease platform. The hackathon submission is deliberately narrower: one specific user, one health problem and one complete, genuinely working AI workflow.

1. Audit the actual repository before choosing a task or rewriting code.
2. Identify what genuinely works, what is partial, what is simulated and what is only planned.
3. Select the most defensible use case based on existing code, public dataset availability, model feasibility, baseline/test design and remaining time. Do not assume a disease task in advance.
4. Preserve useful existing work. Do not expand the scope until the submission-critical workflow is complete.
5. Make AI/ML central to the product's main function. AI-assisted coding alone is not sufficient.
6. Use public datasets only. Never use real patient records. Label synthetic demo data clearly.
7. Evaluate against a simple baseline on held-out test data. Prevent leakage. For health tasks, report false positives and false negatives separately and include at least one genuine failure case.
8. Include the exact sentence: **"This project is a prototype and is not medical advice."**
9. Credit datasets, pretrained models, tutorials, libraries and AI tools with links.
10. Never invent dataset sizes, metrics, sources, clinical validation, features or successful tests.

## Required working practice

- Start with an audit and a concise decision memo: current state, strongest feasible use case, blockers, risks and deadline-aware plan.
- Then implement without waiting for approval on routine reversible work. Ask before destructive or irreversible actions, paid services, external account creation or exposing private information.
- Keep `PROJECT_STATUS.md`, `DECISIONS.md` and a source/credits register current.
- Run tests and report only observed results.
- Ensure the application and write-up describe the same actual implementation.
- Prioritise the one-page write-up, public code link, sources and final link checks. Optional features must not jeopardise submission.

For this health-related project, do not diagnose, prescribe treatment or claim clinical validation. Model outputs are research predictions, not medical advice.
