# Evidence and audit protocol

What a run leaves behind, what each check on it shows, and what no check in this tool can show. It is
written for the person who has to rely on a result they did not produce: a reviewer, an auditor, a second
team.

- [What a run records](#what-a-run-records)
- [What each check shows](#what-each-check-shows)
- [The protocol](#the-protocol)
- [An independent proof in CI](#an-independent-proof-in-ci)
- [What this does not show](#what-this-does-not-show)

## What a run records

`ridi-check run` writes four files into its output folder.

| File | Holds |
|---|---|
| `raw_outputs.jsonl` | every call, one line each: case, version, run, attempt, status, answer, passages, error, start and end time. It is only appended to. |
| `run_manifest.json` | what the run was made from: the SHA-256 of the questions file, both system definitions, the SHA-256 of a Python adapter's source file or of a definition file, the scorer and the SHA-256 of its source file, the tool version, and every invocation with its counts. |
| `results.csv` | the table built from the record: what `report` and `gate` read. |
| `evidence.json` | the SHA-256 of each of the three files above, with the fingerprints of the questions, the scorer and the adapters' source. Fingerprints only: no question, answer or definition is copied into it. |

When the run finishes it prints two lines:

```text
sha256 9c1f…  raw_outputs.jsonl
sha256 41be…  evidence.json
```

The second one stands for the whole folder, because `evidence.json` names every other file by its
fingerprint. A run that is resumed writes `evidence.json` again when it ends.

## What each check shows

| A change made after the run | Seen by |
|---|---|
| a cell of `results.csv` edited: a score, an answer, a passage | `verify`: the table is built again from the record and compared cell by cell |
| a case added to or removed from `results.csv` | `verify` |
| `raw_outputs.jsonl` and `results.csv` edited together, so that they still agree | `verify`: neither has the fingerprint in `evidence.json` any more |
| the questions file or the manifest changed | `verify`, against `evidence.json` |
| the scorer's code changed | `verify`, against the fingerprint in the manifest; the scores are made again with the code that is there now, so a changed score shows as a cell that differs |
| every file in the folder rewritten together, `evidence.json` included | only a fingerprint kept outside the folder: `verify --evidence-sha256 HEX` |
| scores given outside the tool that do not follow the answer key | `gate --check-scores`, with the scorer named |

`verify` exits 0 when everything agrees, 1 when anything differs, 2 when the folder is not one that `run`
wrote.

## The protocol

1. **Before the run**, fix what will be asked: the questions file, the scorer, the two versions, the number
   of runs. For a study, write them down with their fingerprints before any call is made.
2. **Run** with `ridi-check run`. Keep the `evidence.json` line it prints somewhere the folder's owner
   cannot edit: a CI log, a signed commit, a registered protocol, an attestation (below).
3. **Hand over** the output folder as it is, with the questions file and the scorer's source.
4. **The reader checks**, with nothing but the folder and the line that was kept:

   ```bash
   ridi-check verify ridi-out --evidence-sha256 41be…
   ridi-check gate ridi-out/results.csv --strict --min-runs 2
   ```

   The first command shows that the folder is the one the run left and that the table is what the recorded
   calls give. The second applies the release policy to that table. For a results file that was scored
   outside the tool there is no record to verify; use `gate --strict --check-scores --scorer …` instead,
   which scores every answer again and does not pass a score it could not check.

## An independent proof in CI

A fingerprint in a job log is kept by the same people who own the repository. On GitHub a workflow can
instead ask for an attestation: a statement, signed with the workflow's own identity and recorded in a
public transparency log, that this file with this SHA-256 was produced by this workflow at this commit.
[`examples/ci/ridi-check-evidence.yml`](../examples/ci/ridi-check-evidence.yml) does that for
`evidence.json`. Anyone can then check it without trusting the repository's owner:

```bash
gh attestation verify ridi-out/evidence.json --repo OWNER/REPO
ridi-check verify ridi-out
```

The first command shows that `evidence.json` is the file the workflow produced; the second that every
other file in the folder is the one it names. The example was checked for syntax and has not been run on a
live repository by the authors of this tool. Attestations need a public repository, or a plan that offers
them for private ones, and a workflow started from a fork cannot ask for one.

## What this does not show

- **That an answer is right.** The record holds what the assistant said. Whether it is correct is decided
  by the answer key and the scorer, or by the person who reads the cases.
- **That the assistant that was called is the one that is deployed.** The manifest records the definition
  and the fingerprint of the adapter's source. What stands behind an HTTP address is not visible from here.
- **That the answer key is right.** `--check-scores` shows that scores follow a scorer, not that the
  expected answers are true.
- **That the questions are the right ones.** A result holds for the questions that were asked. Whether they
  represent what users ask is a matter of how they were chosen.
- **That the run was not repeated until it looked good.** One folder shows one run. A study guards against
  this by fixing its questions and its analysis before the first call, and by keeping every folder.
