# Examples

Everything in this folder is synthetic.

- `toy_assistant.py` is a toy assistant in two versions that answers questions about a made-up
  library handbook. `questions.csv` holds 30 made-up questions about it. None of the text, answers or
  numbers comes from a real assistant, dataset or study; they exist to show what a report looks like.
  `ridi-check demo` runs the same files.
- `ci/ridi-check.yml` is a GitHub Actions workflow to copy into your own repository.
- `adapters/` holds ready-made ways to connect a real assistant; see its README. They hold no key.
