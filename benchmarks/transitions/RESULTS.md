# Results on the transition set

Measured with ridi-check 0.9.1 on `transitions.csv`: 1131 constructed pairs, 935 in English and 196 in Arabic. This file is written by `measure.py`; a test fails when it is out of date.

Read it for what it is. The pairs are made from fragments put into sentence frames, and each label
follows from the fragment: nobody independent has judged them. The numbers say how the comparison
rules behave on each kind of change. They do not say how often such changes happen in real use, and
they are not a comparison with any other tool.

## Pairs that say something else

Right means: seen as a change.

| Kind of change | Pairs | exact match | overlap 0.9 | overlap 0.75 |
|---|---|---|---|---|
| comparison sign | 80 | 80/80 | 80/80 | 80/80 |
| plus or minus sign | 69 | 69/69 | 69/69 | 69/69 |
| percent, per, times | 69 | 69/69 | 69/69 | 69/69 |
| other symbol | 69 | 69/69 | 69/69 | 69/69 |
| number | 80 | 80/80 | 80/80 | 80/80 |
| unit | 69 | 69/69 | 69/69 | 69/69 |
| negation | 69 | 69/69 | 69/69 | 69/69 |
| opposite word | 80 | 80/80 | 80/80 | 80/80 |
| who and what swapped | 51 | 51/51 | 51/51 | 51/51 |
| added condition | 69 | 69/69 | 53/69 | 30/69 |
| letter case that matters | 44 | 0/44 | 0/44 | 0/44 |
| decimal or thousands mark | 33 | 33/33 | 33/33 | 33/33 |
| **all** | 782 | **738/782** | **722/782** | **699/782** |

## Pairs that say the same thing in another form

Right means: seen as the same.

| Kind of change | Pairs | exact match | overlap 0.9 | overlap 0.75 |
|---|---|---|---|---|
| case and punctuation | 69 | 69/69 | 69/69 | 69/69 |
| markup and spacing | 69 | 69/69 | 69/69 | 69/69 |
| hyphen inside a word | 44 | 44/44 | 44/44 | 44/44 |
| added courtesy | 58 | 0/58 | 24/58 | 52/58 |
| list in another order | 40 | 0/40 | 0/40 | 0/40 |
| another word for the same thing | 69 | 0/69 | 0/69 | 0/69 |
| **all** | 349 | **182/349** | **206/349** | **234/349** |

## What this shows

- Exact match sees every change of a sign, a number, a unit, a negation or a word. It does not see a
  change that lower-casing hides: a letter case that matters, as in `mg` and `Mg`. Those pairs are not
  counted as a change, and the report names them: all 44 of them, together with 44 pairs
  where the case does not matter, such as a capital at the start. It cannot tell the two kinds apart.
- Exact match also calls a change what a reader would not: a courtesy added to the answer, a list in
  another order, another word for the same thing. Those are the cases the owner judges.
- Word overlap accepts an added courtesy. It also accepts an added condition ("allowed" against
  "allowed only under supervision") once the rest of the answer is long enough, which is why it must
  not be used where one word or one clause decides.
