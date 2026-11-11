# ridi-check use cases

Thirteen situations where ridi-check helps, and how to set each one up. In every case the rule is the
same: the "current" and the "proposed" version should differ in the one thing you want to learn
about, and in nothing else. Arabic version: [USE_CASES.ar.md](USE_CASES.ar.md).

| # | You are about to… | Current | Proposed |
|---|---|---|---|
| 1 | move to a new model | today's model | the new model, same prompt and documents |
| 2 | edit the system prompt | old prompt | new prompt |
| 3 | change retrieval (retriever, embeddings, chunking, top-k, reranker) | old retrieval | new retrieval |
| 4 | refresh the documents | old document set | new document set |
| 5 | change settings (temperature, max tokens, a library upgrade) | old settings | new settings |
| 6 | learn how much your assistant varies by itself | the assistant | the same assistant |
| 7 | block a deploy on regressions | live version | release candidate |
| 8 | check a provider that updates silently | answers you saved earlier | answers today |
| 9 | choose between two candidates | candidate A | candidate B |
| 10 | review an update with no reference answers | live version | update |
| 11 | check an assistant that answers in Arabic or several languages | live version | update |
| 12 | teach or demonstrate why averages hide change | toy assistant v1 | toy assistant v2 |
| 13 | update an agent that uses tools or keeps state | live agent | updated agent |

## 1. A new model

*Situation.* Your provider retires a model, or a cheaper or newer one is available.
*Set up.* In `ask()`, pick the model by `version`; keep the prompt and the documents equal.
*Read.* Stable regressions first. A new model often fixes some answers and breaks others; the
"cancel out" line tells you how many changes the accuracy figure hides.

## 2. A prompt edit

*Situation.* You tightened or reworded the system prompt.
*Read.* Without reference answers, expect many changes that are only rewording. Use
`--similarity 0.9`, or add `expected` answers and a scoring function, so that wording changes do not
bury the real ones.

## 3. A retrieval change

*Situation.* A new retriever, embedding model, chunk size, top-k or reranker.
*Set up.* Return the passage ids or titles as `context`.
*Read.* Each changed case lists the passages only one version used. That is where to look first.
The passages are shown, not graded: a passage without a relevance grade can still carry the evidence.

## 4. New or updated documents

*Situation.* You re-indexed the knowledge base.
*Read.* Changes are expected where the documents changed. Look for changes on questions whose
documents did **not** change.

## 5. Settings and upgrades

*Situation.* Temperature, token limit, a framework upgrade, a new guardrail.
*Read.* Compare the re-run variation of the two versions. A setting can leave the answers alone and
still make the assistant less consistent.

## 6. How consistent is my assistant? (no update at all)

*Set up.* Give the same definition as `--current` and `--proposed`.
*Read.* Every difference is the assistant disagreeing with itself. This is the floor that any later
update has to be read against. Do this once before your first real check.

## 7. A gate before deploy

```bash
ridi-check run --config ridi-check.json --out "out-$BUILD_ID"
```

```bash
ridi-check gate "out-$BUILD_ID/results.csv" --max-stable-regressions 0
```

The gate exits 1 when a limit is exceeded, so the pipeline stops. Keep `report.html` as a build
artifact. A workflow to copy: [examples/ci/ridi-check.yml](../examples/ci/ridi-check.yml).

## 8. A provider that changes without telling you

*Set up.* Keep the `results.csv` of a run from last month. Run again today with the same questions.
Build one file by hand: last month's answers in the `baseline_` columns, today's in the `updated_`
columns (two runs of each), and run `ridi-check report`. No code is needed for this step.

## 9. Two candidates

*Set up.* Candidate A as current, candidate B as proposed. "Regression" then means "A right, B
wrong". Run it both ways only if you want both labels; the counts mirror each other.

## 10. Review with no reference answers

*Situation.* The most common one: you have questions but no answer key.
*Do.* Run, open the report, read only the stable changes, give your call on each, download
`judgments.csv`, and run `gate --judgments judgments.csv`. Ten stable changes take minutes to read;
five hundred answers do not.

## 11. Arabic and multilingual assistants

Questions, answers and case ids can be in any language; files are UTF-8. The report switches between
English and Arabic (right-to-left). Exact matching ignores case and punctuation. It does not
normalise spelling variants or diacritics, so use a scoring function if your reference answers need
that.

## 12. Teaching and demos

`ridi-check demo` gives a complete example in under a minute. Students can edit `toy_assistant.py`
(for example `WINDOW_WORDS`), run again into a new folder and watch regressions and improvements move
while accuracy barely does.

## 13. An agent with tools or memory

*Set up.* Wrap the agent as one function that starts a fresh session, plays the case and returns the final
answer, with the tool calls, numbered, as `context`. A multi-turn conversation is one case: put its turns in
the `question` cell as a JSON list.
*Read.* Under each changed case the report lists the tool calls only one version made, which is usually
where the cause is: a tool no longer called, a different argument, a lost earlier turn.
*Note.* [examples/adapters/agent_adapter.py](../examples/adapters/agent_adapter.py) shows this on a stand-in
agent. It has not been tried on a production agent yet.

## When it is not the right tool

- Agents whose runs cannot be started fresh, or whose answer is an action in the world, not text.
- Deciding whether an answer is *correct* without reference answers or your judgment.
- Proving a system is safe or compliant. It reports counts of changed answers.
- Very long free-text answers compared by exact match. Add a scoring function first.
- Explaining *why* an answer changed. It shows the passages that differ and stops there.
