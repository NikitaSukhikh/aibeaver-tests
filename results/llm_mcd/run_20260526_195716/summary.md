# LLM MCD Evaluation

- Created at: `2026-05-26T19:57:16`
- MCD package: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\auto-manufacturer-tech-spec.mcd`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`
- MCD MCP: `C:\Users\Nikita\.cargo\bin\mcd-mcp.exe`
- MCD MCP available: `True`
- MCD CLI: `mcd`
- MCD CLI available: `True`
- MCD tool reference: MCP-first read-only MCD tools with persistent state
- Scoring mode: `llm_judge`
- Judge provider: `same`
- Judge model override: `n/a`
- Token usage includes judge calls: `True`
- Max tool steps: `20`
- OpenAI stateful responses: `False`

| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | `gpt-5.4` | 0 | 0 | 0 | 1 | 0.0% | 0 |

| Provider | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai | 0 | 0 | 0 | 0.0 sec | 0.0 sec |

| Provider | Total tool calls | Avg per question |
| --- | ---: | ---: |
| openai | 0 | 0.00 |

## openai Answers

| # | Status | Seconds | Calls | Question | Answer |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | DRY | 0.0 sec | 0 | Join chassis_brake_validation_specs to vehicle_variant_configuration_specs. Which validation test has the shortest stop_distance_100_0_m? Return test_id, vehicle_variant, stop distance, body_style, trim_level, and curb_mass_kg. |  |
