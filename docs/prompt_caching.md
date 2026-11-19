# Prompt caching in CURA

CURA relies on provider caching through OpenRouter. It keeps no application level prompt cache and stores no prompt, answer, report or conversation for reuse.

## Layout of a request
1. System message, static part: identity, fact rules, how to read a result, answer shape, language rule, JSON contract, voice. Identical for every member and question of the same shape. A narrow question (one result, a general question, a follow up) leaves out the whole report layouts. A report wide question keeps the original order, so only the text before the report layouts is shared.
2. System message, dynamic part: the answer plan and optional modules. No personal values.
3. User message: fixed instructions, then the member's evidence, history and the question.

`app/llm/prompt_cache.py` records where the static part ends (a length and a hash called the prompt version). It never stores the text.

## Providers
| Provider | Behavior | CURA setting |
|---|---|---|
| OpenAI (GPT-5 mini, GPT-5.6 luna) | Automatic for prompts of 1,024 tokens or more. Reads are cheaper. | Nothing needed. `LLM_PROMPT_CACHE_KEY=true` adds a shared, non identifying key (off until measured). |
| Google Gemini | Implicit caching where supported, otherwise explicit `cache_control` on a content block. Only the last breakpoint counts. | `LLM_GEMINI_CACHE_CONTROL=true` (off until measured). |
| Anthropic | Needs explicit breakpoints. Not in the routing. | Not implemented. |

Limits: cache lifetimes are minutes (about 5 for Gemini, 30 minutes or more for OpenAI), so savings need requests close together. Below the provider minimum nothing is cached. A cache write can cost more than a plain read on some models.

## Measuring
Every call logs `prompt_cache {...}`: model, provider, prompt version, input, cached and cache write tokens, hit rate, estimated input cost (an estimate from `LLM_CACHE_READ_FACTOR`), the provider cost, and latency. Run `python scripts/measure_prompt_cache.py --live` with each flag combination and compare round 2 against round 1.
