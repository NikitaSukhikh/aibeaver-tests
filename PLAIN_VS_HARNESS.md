# Plain Source vs Harnessed Plain

This note explains why `plain_source` performed better than `harnessed_plain` in:

`results/multihiertt_mini_original/run_20260606_111454/comparison.md`

## Short version

`plain_source` is effective because it gives the model a small, already-scoped source package: only the selected MultiHierTT example's raw paragraphs and raw HTML tables.

`harnessed_plain` is less effective in this run because it gives the model the full raw markdown/CSV corpus in one prompt: `main.md` plus all prebuilt CSV files. That changes the task from "answer from this example" into "first find the right example and tables inside a very large corpus, then answer."

NB: harnessed_plain had much more irrelevant context and more lookup burden. The model had to identify the right example boundary, table filename, table index, row labels, and year columns inside a huge flattened corpus. plain_source already isolated the correct example.

So the observed difference is not just `json` versus `md+csv`. It is primarily a context scope and retrieval-burden difference.

## What the run actually compared

The run config describes the two modes as:

- `plain_source`: single model call over raw original paragraphs and raw HTML tables only, without record metadata.
- `harnessed_plain`: single model call over full raw `original_md_csv/main.md` and all raw CSV files, without source metadata.

The comparison file also states:

- `plain_source` supplies only the selected original record's raw paragraphs and raw HTML tables.
- `harnessed_plain` supplies only the full raw `main.md` file and all raw prebuilt table CSVs.

That is a major experimental difference. The source format changed, but the amount of source material changed much more.

## Token evidence

For OpenAI in this run:

| Mode | Input tokens | Passed | Total | Pass rate |
| --- | ---: | ---: | ---: | ---: |
| `plain_source` | 40,542 | 6 | 7 | 85.7% |
| `harnessed_plain` | 1,249,835 | 4 | 7 | 57.1% |

`harnessed_plain` used about 31x more input tokens than `plain_source`.

For Anthropic, `harnessed_plain` did not really run successfully. All 7 calls errored because the prompt was over the model context limit:

`prompt is too long: ~203,780 tokens > 200000 maximum`

This is the clearest sign that `harnessed_plain` was not just a different serialization. It was a much larger prompt.

## Why `plain_source` works well

`plain_source` has several advantages:

1. The relevant example is already selected.

   The model does not need to search for `MHDEV-0002` or infer where one example ends and the next begins. All provided paragraphs and tables belong to the target question.

2. The table universe is small.

   The model only has to inspect the tables for one example. This reduces wrong-table and wrong-row mistakes.

3. Raw HTML preserves local table structure.

   MultiHierTT questions often depend on header hierarchy, year columns, row groups, and local table labels. The original raw table representation keeps that structure close to the source record.

4. Less irrelevant text means less distraction.

   Financial reports repeat similar phrases, years, row labels, and metric names across many examples. In a full corpus prompt, many plausible but wrong matches compete with the right one.

5. Arithmetic is easier after retrieval is solved.

   Most failures are not because the arithmetic itself is hard. They come from selecting the wrong numbers or rounding too aggressively. `plain_source` reduces the chance of selecting wrong numbers.

## Why `harnessed_plain` struggles

`harnessed_plain` is weaker in this run for practical reasons:

1. It overloads the prompt.

   Each OpenAI question used roughly 178k input tokens. At that size, the model must attend across a large amount of irrelevant material.

2. It makes retrieval implicit.

   The model receives the whole corpus but has no actual search/read tools in `harnessed_plain`. It must locate the right example, table links, CSV contents, row labels, and columns inside one huge prompt.

3. The markdown and CSV split adds navigation work.

   `main.md` references files such as `mhdev_0002_table_2.csv`, but the values live in separate CSV blocks. The model must connect narrative context to the correct CSV file and row.

4. Repeated labels create false matches.

   MultiHierTT examples often include common labels like "Total", "2007", "2008", "net sales", "revenues", "securities", and "investment grade". In full-corpus mode, those labels appear many times.

5. Precision suffers.

   In this run, `harnessed_plain` failed one arithmetic case by returning `0.669` instead of the expected `0.66977`, while `plain_source` returned `0.6698` and passed.

## Concrete failures from the run

For OpenAI:

| Question | Expected | `plain_source` | `harnessed_plain` | Notes |
| --- | --- | --- | --- | --- |
| `multihiertt_mini_0002` | `1570.75785` | `1571` PASS | `1579` FAIL | Harnessed plain likely selected or applied the growth numbers incorrectly. |
| `multihiertt_mini_0005` | `0.66977` | `0.6698` PASS | `0.669` FAIL | Harnessed plain lost required precision. |
| `multihiertt_mini_0006` | `1` | `2` FAIL | `10` FAIL | Both struggled, but harnessed plain made a larger counting/selection error. |

These failures are consistent with retrieval and source-navigation issues, not with JSON being inherently better than markdown/CSV.

## Better interpretation

The result supports this conclusion:

`plain_source` is effective because it is a clean, scoped, low-noise prompt over the target example.

It does not prove:

`json` is inherently better than `md+csv`.

The fairer comparison would be:

- `plain_source`: selected example only, raw paragraphs plus raw tables.
- scoped `harnessed_plain`: selected example only, markdown excerpt plus that example's CSV files.

The current workspace script already contains a scoped md+csv payload path, so a rerun using scoped `harnessed_plain` would better isolate the true format effect.

