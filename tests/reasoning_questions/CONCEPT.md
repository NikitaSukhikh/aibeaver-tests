Let's create new test for testing models against reasoning questions: datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_10.jsonl

It shall include three modes:
1. LLM model uses .mcd file and uses corresponding MCP commands (like in tests\llm_mcd\run_mcd_eval.py )
2. and 3. - LLM model uses unpacked (2 mode) and disconnected (3 mode) folder and they both use all available CLI and Python tools, as shown in tests\llm_unpacked_vs_disconnected\run_unpacked_vs_disconnected.py

PROPMTS:
Align prompts to questions-specific nature (quastions require multi-step thinking, chain-of-thoughts, applying math formulas etc.).

LLM Judge:
for this test deterministic validation is not enough. Implement llm judge as default validator (you can copy existing llm judge for tests\llm_mcd\run_mcd_eval.py). It shall compare provided "expected_contains" and "reference answer" from datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_10.jsonl
with answers provided by the model. It might be tolerant to phrasing variability, but shall catch the essence (numbers, right conclusion etc.). 

Add flags:
--questions [N] - it takes only first N questions, instead of all 10.
--modes all(by default)/mcd/connected/disconnected/mcd,connected/mcd,disconnected/connected,disconnected