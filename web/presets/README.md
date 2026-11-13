# RIDI browser presets — source, attribution, and limits

These **are real model responses**, copied **byte-for-byte** from the official RIDI GitHub Actions workflow artifacts. They are **not** an independently adjudicated clinical or pharmacology benchmark. The repository's **Python and JavaScript code remains MIT licensed**; underlying third-party BoolQ passages and question data retain their **Creative Commons Attribution–ShareAlike 3.0 (CC BY-SA 3.0)** terms. Their original source is [BoolQ (Clark et al., 2019)](https://github.com/google-research-datasets/boolean-questions), a yes/no question-answering dataset over Wikipedia passages. See the dataset's source attribution and license before redistributing its passages or any adaptations.

| Browser selection | Signed GitHub Actions evidence | Exact source SHA-256 | What changed |
|---|---|---|---|
| `qwen_config` | [Run 43317397792](https://github.com/adeebnoor/ridi-check/actions/runs/43317397792) | `18286273cf15a062629eaa59a3dbe976ea658a72d82d2b1dad5248e9b2e8317d` | Qwen2.5-1.5B weights unchanged; only source-authority system prompt changed. Three actual runs per arm; 48 BoolQ questions |
| `qwen_swap` | [Run 43312668253](https://github.com/adeebnoor/ridi-check/actions/runs/43312668253) | `8d9d0b48b48a0802df239fb47bbfa2dc9a72cb3eece853514aefec9ad982c629` | Qwen2.5-0.5B → Qwen2.5-1.5B, two runs per arm; 48 BoolQ questions |

The preset CSV files are the **exact original `results.csv` files** from the GitHub runs, not reconstructed from a secondary report and not massaged to look more impressive. The browser downloads the selected **public static** CSV from the *same* GitHub Pages origin and checks its **SHA-256** against the expected source before analysing it. This is a user-initiated download, *not* an upload of private CSV data. The browser's synthetic examples can still run without any server.

### Important interpretation

* The published BoolQ answer labels are **not** newly adjudicated human ground truth for RIDI. Some are explicitly wrong relative to their passage (e.g. the known Hindi national-language label issue) or become outdated across years. A *regression against the published label* is not necessarily a harmful decision.
* No model-weight-update comparison has been performed here; the `qwen_config` contrast is an **instruction configuration** change and `qwen_swap` is a **different-sized model substitution**.
* The `qwen_config` Ubuntu run yields **4 stable published-label regressions**, **2 stable improvements**, **3 unstable cases**; the `qwen_swap` run yields **6 stable regressions**, **16 stable improvements**, and **0 unstable** under their own run definitions. Windows repeat measurements were not identical in all cases; see [the audit](../../docs/research/same_weights_prompt_update_20261113.md).
* There is **no verified real clinical DDI preset** distributed in RIDI Check. The legacy invented-drug data are **fictional**, and the browser labels them accordingly. Never rename them as 'real-world clinical pharmacology'.
* Sample passages are included for reproducibility under the above third-party terms. This file is an attribution and source notice, **not** a relicense of the whole GitHub repository. Cite original BoolQ and inspect third-party license specifics before reuse.

### Regeneration

Run the explicit, SHA-256 pinned copier from the signed GitHub artifacts:

```bash
python tools/build_browser_presets.py --config-zip signed-config.zip --swap-zip signed-boolq-swap.zip
```

On a successful rebuild, all preset SHA-256 hashes are byte-identical to the GitHub original, so both scientific and UI tests can detect tampering. There is no API token required to use the published static files.