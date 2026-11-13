# Reproducibility

Commands, seeds, environment pins, and checksums copied from this repository. A number that is not in these files is not claimed here. The commercial replication figures on the [science page](https://adeebnoor.github.io/ridi-check/research.html) are the reported preregistered result. This repository does not contain those runs, so they cannot be rebuilt from these commands.

## Package

Runtime dependencies: none (`dependencies = []` in `pyproject.toml`). Python `>=3.10`.

The test workflow (`.github/workflows/tests.yml`) installs `.[test]` plus `anthropic` (used only by the adapter example) and runs:

```bash
pip install ".[test]" anthropic
pytest -q
```

On Ubuntu with Python 3.13 it also runs `pytest -q --cov=ridi_check --cov-branch --cov-fail-under=95`. The matrix is Python 3.10, 3.13, and 3.14 on Ubuntu, Windows, and macOS.

`pytest` itself is pinned only as `pytest>=7` and `pytest-cov>=4`. There is no lockfile of transitive test packages in the repository.

## Offline demo

The toy assistant seeds its tie-break with `SEED = 7` in `src/ridi_check/demo/toy_assistant.py` (`random.Random(f"{SEED}|{question}|{nth}")`). The current version does not use that generator. From a fresh process:

```bash
pip install ridi-check
ridi-check demo
```

Development checkout:

```bash
pip install -e ".[test]"
ridi-check demo
```

The questions are the constructed library handbook in `src/ridi_check/demo/questions.csv`. The demo config runs each version twice (`src/ridi_check/demo/ridi-check.json`). Data are synthetic.

## Same weights, prompt update

Frozen before the run: `experiments/same_weights_prompt/PRE_RUN_FROZEN.json`.

| Pin | Value |
|---|---|
| Model | `Qwen2.5-1.5B-Instruct` GGUF `q4_k_m`, both arms |
| Model SHA-256 | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |
| llama.cpp | release `b12327` |
| Linux binary archive SHA-256 | `a78e768c62bebc3e8de5e8a04d32b5d6ef3727efcc5f042efc271d03d893bd94` |
| Decoding | `temperature=0`, `seed=20261113` (`SEED` in `experiments/same_weights_prompt/same_model.py`) |
| Items | 48 seeded BoolQ dev cases, 24 YES and 24 NO |
| Repeated runs | 3 per version, 288 calls |
| Questions SHA-256 | `3fa33a0e7e968c99056ffe17a430a555a9678f717d6fdcc78e1c352dfa4eb462` |
| Adapter SHA-256 | `d91234a6400aa92e6b3ed61dc69c4642d668228d7a76cf0db02f518e49ca04b4` |
| Config SHA-256 | `b79a464d492e8d87f384a36651f44562811a5de095de034f4eb5e021c1ece083` |
| BoolQ `dev.jsonl` SHA-256 | `ebc29ea3808c5c611672384b3de56e83349fe38fc1fe876fd29b674d81d0a80a` |
| Workflow runner | `ubuntu-24.04`, Python 3.13 |
| GitHub evidence SHA-256 | `cf5359da1222170064d95905470aa163b107f4ee55f4c2405a67e23598ffe64e` |

The sample is rebuilt only from that `dev.jsonl` checksum (`experiments/qwen_cpu_pilot/boolq_builder.py`, `SEED = 20261113`). The workflow then runs:

```bash
python -m pip install -e .
# checksums in .github/workflows/ridi-same-weights-prompt.yml
ridi-check run --config ridi-check.json
ridi-check verify ridi-out
ridi-check gate ridi-out/results.csv --strict --check-scores
```

The signed run is GitHub Actions [43317397792](https://github.com/adeebnoor/ridi-check/actions/runs/43317397792). Findings and the cross-platform difference are in [the audit](research/same_weights_prompt_update_20261113.md). A fixed seed did not make every repeated answer identical across Windows and Ubuntu.

## Qwen size substitution

Frozen file: `experiments/qwen_cpu_pilot/PRE_RUN_FROZEN.json`. This is a different experiment: two model sizes, not one set of weights.

| Pin | Value |
|---|---|
| Current model SHA-256 | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` |
| Proposed model SHA-256 | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |
| llama.cpp Linux archive SHA-256 | `a78e768c62bebc3e8de5e8a04d32b5d6ef3727efcc5f042efc271d03d893bd94` |
| Decoding | `temperature=0`, `seed=20261113`, `max_tokens=12` |
| Policy questions SHA-256 | `9a16f8ddaa542e0bf08e27a7b173d1512742e8ac36a7c2e0edde995a6ed7e69a` |
| Adapter SHA-256 | `716ef2147ed703ce1952778bac9e41698194a0c6b2da495e853dfacd75bb333d` |
| Config SHA-256 | `b413605e8859e893a4c3b4bb21f4cb1a12905b76ab3b6ed1f9c019f610b9842c` |

Commands and checksums are in `.github/workflows/ridi-qwen-local-pilot.yml`. The signed BoolQ run is GitHub Actions [43312668253](https://github.com/adeebnoor/ridi-check/actions/runs/43312668253). Read [the scientific audit](../experiments/qwen_cpu_pilot/SCIENTIFIC_AUDIT.md) before quoting a count: one later GitHub run did not reproduce every baseline answer, and BoolQ labels are not adjudicated.

## What is not reproduced here

- The commercial replication (Gemini 3.8 Flash, GPT-5.4 mini, Claude Sonnet 5.5) is not in this repository. The science page reports the preregistered outcome; it does not rebuild it.
- No Zenodo deposit has been made. `.zenodo.json` is metadata for a later archive.
