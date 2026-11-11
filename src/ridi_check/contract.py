"""The results.csv contract: read, validate, write.

One row per question. Column names are fixed (see README). The reader follows the browser
prototype, with two differences that make it stricter: a row with no case_id is rejected
instead of skipped, and a run that has an answer but no correctness value in answer-key
mode is rejected instead of being counted as a disagreement.
"""

from __future__ import annotations

import csv
import re
import sys
from itertools import chain
from typing import Iterator
from dataclasses import dataclass, field

from .util import read_text

KEY = "key"
NOKEY = "nokey"

CONTEXT_SEPARATOR = " | "
RUN_COLUMN = re.compile(r"^(baseline|updated)(?:_repeat([0-9]*))?_(answer|correct)$")

LINE = re.compile(r"[^\r\n]*(?:\r\n?|\n)|[^\r\n]+")
FIRST_LINE_END = re.compile("[\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]")

csv.field_size_limit(64 * 1024 * 1024)

# A spreadsheet reads a cell that starts with one of these as a formula. `to_csv` puts an apostrophe in
# front of such a cell and `read_records` takes it off again, so the tool reads back what it wrote.
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _unguard(cell: str) -> str:
    return cell[1:] if len(cell) > 1 and cell[0] == "'" and cell[1] in FORMULA_START else cell


class ContractError(ValueError):
    """The file does not follow the results.csv contract."""


@dataclass(slots=True)     # a large file makes hundreds of thousands of these
class Run:
    answer: str = ""
    correct: int | None = None


@dataclass(slots=True)
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
    text = text.lstrip("\ufeff")
    end = FIRST_LINE_END.search(text)       # the first line as str.splitlines gives it, without splitting the whole text
    header = "" if not text or text.isspace() else (text[:end.start()] if end else text)
    if "," not in header:
        if "\t" in header:
            return "\t"
        if ";" in header:
            return ";"
    return ","


def iter_records(text: str) -> Iterator[tuple[int, list[str]]]:
    """(row number, cells) for every non-blank record, one at a time. The header is row 1, as a spreadsheet shows it.

    The lines go to the csv reader exactly as io.StringIO(text, newline="") would give them (ends kept, split
    at \\n, \\r and \\r\\n only) without the second copy of the whole text that it makes.
    """
    text = text.lstrip("\ufeff")
    lines = (m.group() for m in LINE.finditer(text))
    reader = csv.reader(lines, delimiter=sniff_delimiter(text), skipinitialspace=True)
    try:
        for i, r in enumerate(reader):
            if any(cell.strip() for cell in r):
                yield i + 1, [_unguard(cell) for cell in r]
    except csv.Error as exc:
        if "field limit" in str(exc):
            raise ContractError(
                f"Near line {reader.line_num}: one cell holds more than {csv.field_size_limit():,} characters, the most "
                "this tool reads in a cell. A quotation mark that is never closed has the same effect."
            ) from exc
        raise ContractError(f"Near line {reader.line_num}: the file could not be read as CSV ({exc}).") from exc


def read_records(text: str) -> list[tuple[int, list[str]]]:
    """Every record of `iter_records`, for the small files (questions, judgments) that are read whole."""
    return list(iter_records(text))


def run_column(side: str, run: int, kind: str) -> str:
    """Column name for the 1-based run of a side ('baseline' or 'updated')."""
    if run == 1:
        return f"{side}_{kind}"
    if run == 2:
        return f"{side}_repeat_{kind}"
    return f"{side}_repeat{run - 1}_{kind}"


def split_context(cell: str) -> list[str]:
    # The same passage names come back case after case: one copy of each is kept.
    return [sys.intern(part.strip()) for part in cell.split("|") if part.strip()]


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
    # One record at a time: the rows of a large file are not all held while its cases are built.
    records = iter_records(text)
    first, second = next(records, None), next(records, None)
    if first is None or second is None:
        raise ContractError("No rows found in the file.")

    header = [h.strip().lower() for h in first[1]]
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
    for row, record in chain([second], records):

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
        same_text: dict[str, str] = {}
        for side in ("baseline", "updated"):
            answers = runs.get((side, "answer"), {})
            corrects = runs.get((side, "correct"), {})
            scored = {i: binary(p) for i, p in corrects.items()}  # validates every _correct cell
            out: list[Run] = []
            for index in sorted(set(answers) | (set(corrects) if key else set())):
                answer = get(position=answers[index]) if index in answers else ""
                answer = same_text.setdefault(answer, answer)     # runs that repeat an answer share one copy of it
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
        text = read_text(path)
    except ValueError as exc:
        raise ContractError(str(exc)) from exc
    return parse_results(text, mode)


def to_csv(header: list[str], rows: list[list[str]]) -> str:
    """Comma-separated, \\n line ends; a cell is quoted when it holds a comma, a quote or a line break.

    A cell that a spreadsheet would read as a formula gets an apostrophe in front (see FORMULA_START).
    """
    def cell(value: object) -> str:
        text = "" if value is None else str(value).replace("\x00", "")   # a null character is never read back
        if text.startswith(FORMULA_START):
            text = "'" + text
        if any(ch in text for ch in ',"\r\n'):
            return '"' + text.replace('"', '""') + '"'
        return text

    return "".join(",".join(cell(v) for v in row) + "\n" for row in [header, *rows])
