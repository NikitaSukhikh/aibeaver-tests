Let's create new test for testing models against reasoning questions: datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_10.jsonl

It shall include three modes:
1. LLM model uses .mcd file and corresponding MCP commands (like in tests\llm_mcd\run_mcd_eval.py )
2. 3. LLM model uses unpacked (2 mode) and discnnected (3 mode) folder and all tools (CLI,Python tools) needed as in tests\llm_unpacked_vs_disconnected\run_unpacked_vs_disconnected.py

PROPMTS:
1. For 