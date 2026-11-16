# HealthSignal — hackathon execution plan

## The strategic decision

Do not abandon the HealthSignal vision. Keep the full multimodal, multi-disease platform as the roadmap, but make the competition submission a single coherent proof that the core idea works.

**The submission should demonstrate:** one named user + one defined health problem + one public dataset + one real model + one baseline + held-out evaluation + one failure case + one working input-to-output demo.

## Step 1 — audit before choosing

The coding agent must inspect the actual repository and classify each relevant item:

- Working model and inference path
- Dataset availability, source and licence
- Preprocessing and labels
- Evaluation scripts and split strategy
- Backend/API status
- Frontend/demo status
- Tests and reproducibility
- Existing explanations/reporting
- Missing or simulated components

It must not infer implementation from filenames or UI appearance. It should run the code and inspect outputs where feasible.

## Step 2 — choose the smallest defensible use case

Score candidate tasks against:
1. Existing working implementation
2. Public data accessible now
3. Clear target label and useful baseline
4. Valid unseen test split without leakage
5. End-to-end demo feasibility
6. Ability of the team to explain it accurately

Choose one task. Do not add a second disease simply to make the product look broader.

## Step 3 — build the evidence

- Verify dataset URL, licence, sample count and feature/label definitions.
- Establish a simple baseline (for example, majority-class or a simple standard model, as appropriate).
- Train or load the selected model.
- Keep preprocessing inside the training pipeline.
- Use a held-out test set; do not tune against it.
- Report suitable metrics, confusion matrix, false positives and false negatives.
- Save at least one real failure example and explain possible causes.
- State whether external validation is unavailable.
- Avoid describing model scores as clinical probabilities unless calibration supports that.

## Step 4 — connect the demo

A judge should be able to provide a valid example input, run the model and see its actual output. Use a clearly labelled synthetic/demo profile only for interactive examples if necessary. Make the data provenance and limitations visible. Do not show a hard-coded result as if the model generated it.

## Step 5 — freeze scope and submit

Once the core flow works, stop adding features. Test from a clean start, capture evidence, finish the one-page write-up and credits, verify public access in a private browser window, and submit before the deadline.

## Definition of done

- [ ] One specific user and moment of use
- [ ] One specific health problem and prediction target
- [ ] Public dataset with verified source/licence and credits
- [ ] Real model inference demonstrated
- [ ] Baseline and model evaluated on held-out test data
- [ ] False positives and false negatives reported separately
- [ ] At least one genuine failure case discussed
- [ ] AI/ML is central to the product's main function
- [ ] Synthetic data, if used, is labelled
- [ ] Exact medical disclaimer included
- [ ] One-page write-up complete
- [ ] Public code link works
- [ ] Sources and AI tools credited
- [ ] Every visible feature's status is truthful
