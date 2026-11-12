# Qwen2.5 local CPU model-substitution pilot (exploratory)

**Not a clinical benchmark. Not a same-weights model update. Not independently adjudicated.**

## Purpose
Demonstrate a complete RIDI analysis of actual, locally executed language-model answers with frozen identical policy evidence. Compare Qwen2.5 0.5B Instruct Q4_K_M (current) to Qwen2.5 1.5B Instruct Q4_K_M (proposed). Both are real open-weight models, but of different sizes; this is a model **substitution**, not a controlled release-to-release update.

## Windows CPU pilot (2026-11-12 UTC)

- 24 intentionally constructed library-policy YES/NO cases, 12 YES and 12 NO, with unambiguous statements taken/adapted from RIDI's fictitious handbook. Every question contains the same policy evidence for the two models. Human-blinded adjudication and naturally sampled production questions have **not** happened.
- 2 model sizes × 2 repeats × 24 cases = **96/96 successful calls** at temperature 0, seed 20261113, max_tokens 12, on localhost ports 18121 and 18122; no paid API.
- First-run exact-match accuracy: **20/24 to 21/24**. RIDI: **3 stable regressions** (p10, p16, p22); **4 stable improvements** (p02, p03, p15, p21); zero observed within-model repeat differences in this small set.
- Identical source passages for every case. Those results show an aggregate +1 gain that conceals some per-question regressions; they do not establish harm or statistical external validity.
- RIDI strict gate with `--check-scores` correctly rejects the proposed model (exit 1); `verify` succeeds.

## Frozen bytes and source

| Item | SHA-256 |
|---|---|
| questions.csv | `9a16f8ddaa542e0bf08e27a7b173d1512742e8ac36a7c2e0edde995a6ed7e69a` |
| local_models.py | `716ef2147ed703ce1952778bac9e41698194a0c6b2da495e853dfacd75bb333d` |
| ridi-check.json | `b413605e8859e893a4c3b4bb21f4cb1a12905b76ab3b6ed1f9c019f610b9842c` |
| Qwen2.5-0.5B Q4_K_M.gguf | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Qwen2.5-1.5B Q4_K_M.gguf | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |

Model binaries are unmodified official GGUF files from `Qwen/Qwen2.5-0.5B-Instruct-GGUF` and `Qwen/Qwen2.5-1.5B-Instruct-GGUF`. The inference engine is `ggml-org/llama.cpp` release `b12327`.

The original Windows run's `raw_outputs.jsonl` SHA-256 is `1c2e44ea457b3b6df540e7537431f5a70f432be963d3113a883795fc1a680e61`; `evidence.json` SHA-256 is `6e8dadb192da08a6448dc8bb8e0e63ff79f560cef01c895c6dc17817b954ee09`. This GitHub folder contains the original frozen input bytes; the full original output folder is also retained on the authorized desktop at `C:\Users\Public\Documents\RIDI_LOCAL_MODEL_PILOT_20261113\pilot\ridi-out`.

## Independent compute reproduction via GitHub Actions

See `.github/workflows/ridi-qwen-local-pilot.yml`. It obtains the same checksum-pinned public model files and a release-pinned Linux llama.cpp CPU executable, invokes the exact question and adapter files, and signs the Linux-produced `evidence.json`. The job itself must complete successfully before this is called an **independently executed reproduction**.

Hardware, OS, numeric kernels and parallelism can change generation details despite a fixed seed. Compare the Linux run's full case-level outputs with the Windows run; do not assert bit-for-bit answer equivalence in advance. A GitHub attestation certifies the job/file identity, **not** model truth or the correctness of the policy labels.

## What remains for an external scientific evaluation

Use preselected production-representative tasks, real update pairs, blinded independent adjudicators, confidence intervals with justified sampling, cross-framework comparison on the same inputs, and a preregistered analytic protocol. A strict gate failing on these three cases is an engineering detection result, not a safety clearance or evidence of patient harm.
