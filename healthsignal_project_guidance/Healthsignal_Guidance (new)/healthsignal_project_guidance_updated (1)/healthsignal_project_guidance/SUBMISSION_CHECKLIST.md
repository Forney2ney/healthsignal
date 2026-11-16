# HealthSignal — submission checklist

## Required submission items

- [ ] Public GitHub repository or accessible Google Colab notebook
- [ ] One-page write-up
- [ ] Team members' names, emails and schools
- [ ] One person submits for the whole team
- [ ] Dataset, pretrained model, tutorial, library and AI-tool credits with links
- [ ] Exact sentence in write-up: **"This project is a prototype and is not medical advice."**

## Write-up structure

1. **Project name / track / team**
2. **The problem:** Who is the one specific user? At what moment would they use it? Why does this matter?
3. **What we built:** What goes in, what comes out, and how does the user use it?
4. **What we added:** What suggested project/tutorial is the work based on? What is the team's original contribution? If it is an original idea, say so.
5. **How it works:** Dataset and source, verified sample count, cleaning/preprocessing, target label, model and rationale.
6. **Results:** Baseline vs model on held-out test data; relevant metrics; false positives and false negatives; at least one failure case.
7. **What we'd do next:** Honest limitations and realistic next steps.
8. **Sources:** Dataset, pretrained model, libraries, tutorials and AI tools, with links.

## Evaluation checks

- [ ] Test set is held out and not used for tuning
- [ ] No data leakage (including preprocessing/feature selection)
- [ ] Patient-level split used when required by dataset structure
- [ ] Baseline is appropriate and described
- [ ] Report metrics suited to the task, not accuracy alone
- [ ] False positives and false negatives separately counted/reported
- [ ] At least one genuine failure case included
- [ ] Weak results are reported honestly
- [ ] No unsupported clinical or diagnostic claims

## Demo checks

- [ ] Real input triggers real model inference
- [ ] Demo profile is clearly labelled synthetic if applicable
- [ ] No hard-coded output is presented as a model prediction
- [ ] Implemented / partial / simulated / planned features are distinguished
- [ ] App starts reliably from documented instructions
- [ ] Demo video, if used, is no longer than two minutes

## Final link and integrity checks

- [ ] Repository/notebook is accessible to anyone with the link
- [ ] Notebook outputs are saved and visible if using Colab
- [ ] Write-up link opens
- [ ] All links tested in a private/incognito window
- [ ] Team members listed actually contributed
- [ ] Code, demo and write-up describe the same version
- [ ] Latest submission is checked after any resubmission
