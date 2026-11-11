"""The results.csv contract: read, validate, write.

One row per question. Column names are fixed (see README). The reader follows the browser
prototype, with two differences that make it stricter: a row with no case_id is rejected
instead of skipped, and a run that has an answer but no correctness value in answer-key
mode is rejected instead of being counted as a disagreement.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

KEY = "key"
NOKEY = "nokey"

CONTEXT_SEPARATOR = " | "
RUN_COLUMN = re.compile(r"^(baseline|updated)(?:_repeat([0-9]*))?_(answer|correct)$")

csv.field_size_limit(64 * 1024 * 1024)


class ContractError(ValueError):
    """The file does not follow the results.csv contract."""


@dataclass
class Run:
    answer: str = ""
    correct: int | None = None


@dataclass
class Case:
    case_id: str
    row: int
    question: str = ""
    expected: str = ""
    baseline: list[Run] = field(default_factory=list)
    updated: list[Run] = field(default_factory=list)
    baseline_context: list[str] = field(default_factory=list)
    updated_context: list[str] = field(default_factory=list)
    run_errors: str = ""
    incomplete: bool = False


def sniff_delimiter(text: str) -> str:
    """Comma, unless the header line has none and uses tabs (cells pasted from a spreadsheet) or semicolons."""
    header = text.lstrip("\ufeff").splitlines()[0] if text.strip() else ""
    if "," not in header:
        if "\t" in header:
            return "\t"
        if ";" in header:
            return ";"
    return ","


def read_records(text: str) -> list[tuple[int, list[str]]]:
    """(row number, cells) for every non-blank record. The header is row 1, as a spreadsheet shows it."""
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=sniff_delimiter(text), skipinitialspace=True)
    return [(i + 1, r) for i, r in enumerate(reader) if any(cell.strip() for cell in r)]


def run_column(side: str, run: int, kind: str) -> str:
    """Column name for the 1-based run of a side ('baseline' or 'updated')."""
    if run == 1:
        return f"{side}_{kind}"
    if run == 2:
        return f"{side}_repeat_{kind}"
    return f"{side}_repeat{run - 1}_{kind}"


def split_context(cell: str) -> list[str]:
    return [part.strip() for part in cell.split("|") if part.strip()]


def _run_columns(header: list[str]) -> dict[tuple[str, str], dict[int, int]]:
    """{(side, kind): {run index from 0: column position}}."""
    found: dict[tuple[str, str], dict[int, int]] = {}
    for position, name in enumerate(header):
        m = RUN_COLUMN.match(name)
        if not m:
            continue
        side, digits, kind = m.group(1), m.group(2), m.group(3)
        if digits is None:
            index = 0
        elif digits == "":
            index = 1
        else:
            index = int(digits)
            if index < 1:
                raise ContractError(f"Column {name!r}: repeat numbers start at 1.")
        slot = found.setdefault((side, kind), {})
        if index in slot:
            raise ContractError(f"Columns {header[slot[index]]!r} and {name!r} name the same run.")
        slot[index] = position
    return found


def parse_results(text: str, mode: str = "auto") -> tuple[list[Case], str]:
    """Parse results.csv text. Returns (cases, mode) with mode 'key' or 'nokey'."""
    if mode not in ("auto", KEY, NOKEY):
        raise ValueError(f"unknown mode {mode!r}")
    records = read_records(text)
    if len(records) < 2:
        raise ContractError("No rows found in the file.")

    header = [h.strip().lower() for h in records[0][1]]
    seen_columns: set[str] = set()
    for name in header:
        if name and name in seen_columns:
            raise ContractError(f"Column {name!r} appears more than once.")
        seen_columns.add(name)
    col = {name: i for i, name in enumerate(header)}
    if "case_id" not in col:
        raise ContractError("The file needs a case_id column.")

    runs = _run_columns(header)
    has_key = "baseline_correct" in col and "updated_correct" in col
    has_answers = "baseline_answer" in col and "updated_answer" in col
    if not has_key and not has_answers:
        raise ContractError(
            "The file needs baseline_correct and updated_correct (0 or 1), "
            "or baseline_answer and updated_answer."
        )
    if mode == KEY and not has_key:
        raise ContractError("Answer-key mode needs baseline_correct and updated_correct.")
    if mode == NOKEY and not has_answers:
        raise ContractError("No-key mode needs baseline_answer and updated_answer.")
    resolved = mode if mode != "auto" else (KEY if has_key else NOKEY)
    key = resolved == KEY

    cases: list[Case] = []
    first_row_of: dict[str, int] = {}
    for row, record in records[1:]:

        def get(name: str | None = None, position: int | None = None) -> str:
            i = col.get(name, -1) if position is None else position
            return record[i].strip() if 0 <= i < len(record) else ""

        case_id = get("case_id")
        if not case_id:
            raise ContractError(f"Row {row}: case_id is missing.")
        if case_id in first_row_of:
            raise ContractError(
                f"Row {row}: case_id {case_id!r} appears more than once (first in row {first_row_of[case_id]})."
            )
        first_row_of[case_id] = row
        where = f"Row {row} (case {case_id})"

        def binary(position: int) -> int | None:
            value = get(position=position)
            if value == "":
                return None
            if value not in ("0", "1"):
                raise ContractError(f"{where}: {header[position]} must be 0 or 1, got {value!r}.")
            return int(value)

        case = Case(
            case_id=case_id,
            row=row,
            question=get("question"),
            expected=get("expected"),
            baseline_context=split_context(get("baseline_context")),
            updated_context=split_context(get("updated_context")),
            run_errors=get("run_errors"),
        )
        for side in ("baseline", "updated"):
            answers = runs.get((side, "answer"), {})
            corrects = runs.get((side, "correct"), {})
            scored = {i: binary(p) for i, p in corrects.items()}  # validates every _correct cell
            out: list[Run] = []
            for index in sorted(set(answers) | (set(corrects) if key else set())):
                answer = get(position=answers[index]) if index in answers else ""
                correct = scored.get(index) if key else None
                missing = correct is None if key else answer == ""
                if index == 0:
                    if missing:
                        if not case.run_errors:
                            name = run_column(side, 1, "correct" if key else "answer")
                            raise ContractError(
                                f"{where}: {name} is empty."
                                + (" It must be 0 or 1." if key else " Every row needs a first-run answer.")
                            )
                        case.incomplete = True
                        continue
                elif answer == "" and correct is None:
                    continue  # no such run for this case
                elif key and correct is None:
                    raise ContractError(
                        f"{where}: {run_column(side, index + 1, 'answer')} has a value but "
                        f"{run_column(side, index + 1, 'correct')} is empty or absent."
                    )
                out.append(Run(answer=answer, correct=correct))
            setattr(case, side, out)
        cases.append(case)
    return cases, resolved


def read_results(path: str, mode: str = "auto") -> tuple[list[Case], str]:
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            text = f.read()
    except OSError as exc:
        raise ContractError(f"The file could not be read: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ContractError(f"The file is not UTF-8 text: {exc}") from exc
    return parse_results(text, mode)


def to_csv(header: list[str], rows: list[list[str]]) -> str:
    """Comma-separated, \\n line ends; a cell is quoted when it holds a comma, a quote or a line break."""
    def cell(value: object) -> str:
        text = "" if value is None else str(value)
        if any(ch in text for ch in ',"\r\n'):
            return '"' + text.replace('"', '""') + '"'
        return text

    return "".join(",".join(cell(v) for v in row) + "\n" for row in [header, *rows])
