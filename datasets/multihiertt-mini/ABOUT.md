# MultiHiertt Mini

This directory contains a 50-example MCD package derived from the public MultiHiertt dev split.

The package is designed to test MCD usage on acknowledged benchmark data: financial-report prose, multiple source tables per example, cell-level evidence refs, and arithmetic reasoning programs.

The full upstream dataset is not vendored here. Rebuild with:

```powershell
python datasets\multihiertt-mini\scripts\build_multihiertt_mini.py
mcd pack datasets\multihiertt-mini\unpacked --output datasets\multihiertt-mini\multihiertt-mini.mcd
```

`original_disconnected/` contains the same 50 examples in the original MultiHiertt JSON shape for MCD-vs-original benchmark comparisons.

Upstream source: https://huggingface.co/datasets/yilunzhao/MultiHiertt

Paper/repo: https://arxiv.org/abs/2206.01347 and https://github.com/psunlpgroup/MultiHiertt

License: MIT, as declared by the upstream Hugging Face dataset and GitHub repository.
