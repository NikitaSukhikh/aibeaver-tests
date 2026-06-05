# MultiHiertt Mini Original Disconnected Source

This directory contains the same 50 selected examples as `../multihiertt-mini.mcd`, but in the original MultiHiertt JSON record shape instead of the normalized MCD package.

- `dev_50.json` is a direct JSON array of the selected upstream dev records.
- `selection_map.csv` maps local `MHDEV-000x` IDs to upstream `uid` values and source record indexes.
- `../answers.json` is the evaluator-only gold-label file for these examples.

Use this directory for original-source or disconnected-source benchmark modes. When prompting a model, strip evaluator fields from each record's `qa` object and provide only the source paragraphs, tables, table descriptions, and question text.

The full upstream dataset is not vendored here.
