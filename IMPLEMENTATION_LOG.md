# AI Council - Implementation Log

## Date: 2026-03-21
## Author: Basil Suhail (basilsuhailkhan@proton.me)
## Constraint: NO PUSHES TODAY — all changes are local only. Push scheduled for 2026-03-22.

---

## Issues Found (Full Inventory)

### CRITICAL (C1-C5)
| ID | Issue | File(s) | Status |
|----|-------|---------|--------|
| C1 | Gemini API key leaked in URL query string | `agents/gemini_agent.py` | ✅ DONE |
| C2 | Empty Claude agent — no implementation | `agents/claude_agent.py` | ✅ DONE |
| C3 | Empty OpenAI agent — no implementation | `agents/openai_agent.py` | ✅ DONE |
| C4 | Bare `except:` clauses silently swallow all errors | Multiple files | ✅ DONE |
| C5 | Broken package entry point (relative imports) | `setup.py` | ✅ DONE |

### HIGH (H1-H8)
| ID | Issue | File(s) | Status |
|----|-------|---------|--------|
| H1 | API keys stored unencrypted on disk | `storage/config.py` | ✅ DONE |
| H2 | Agent status uses strings instead of enum | Multiple files | ✅ DONE |
| H3 | Dead code: source_validator.py never imported | `utils/source_validator.py` | ✅ DONE |
| H4 | `asyncio` listed in requirements.txt (stdlib) | `requirements.txt` | ✅ DONE |
| H5 | Relative session path breaks from other dirs | `storage/sessions.py`, `storage/rag.py` | ✅ DONE |
| H6 | Hardcoded magic numbers everywhere | Multiple files | ✅ DONE |
| H7 | `import re` inside method bodies | `agents/*.py` | ✅ DONE |
| H8 | No dependency version pinning | `requirements.txt` | ✅ DONE |

### MEDIUM (M1-M7)
| ID | Issue | File(s) | Status |
|----|-------|---------|--------|
| M1 | Stub commands (export, vote, eliminate) | `cli/commands.py` | ✅ DONE |
| M2 | Duplicated `get_resource_path()` logic | `cli/interface.py`, `storage/config.py` | ✅ DONE |
| M3 | No retry logic for APIs | `agents/*.py` | ✅ DONE |
| M4 | RAG uses O(n) linear search | `storage/rag.py` | ⬜ DEFERRED (future PR) |
| M5 | Inconsistent API timeouts, not configurable | `agents/*.py` | ✅ DONE |
| M6 | No input validation on commands/config | `cli/commands.py` | ✅ DONE |
| M7 | `clear_sessions()` has no confirmation prompt | `cli/commands.py` | ✅ DONE |

---

## Execution Plan (Completed)

### Phase 1: Critical Security & Crash Fixes ✅
### Phase 2: High-Priority Fixes ✅
### Phase 3: Medium-Priority Improvements ✅ (except M4 deferred)

---

## Change Log

| # | Issue ID | What Changed | Files Modified |
|---|----------|--------------|----------------|
| 1 | C1 | Moved Gemini API key from URL query string to `x-goog-api-key` header (both generate and evaluate) | `agents/gemini_agent.py` |
| 2 | C4 | Replaced all bare `except:` with specific exceptions: `(ValueError, IndexError)` for parsing, `(json.JSONDecodeError, KeyError)` for JSON, `Exception` for UI fallbacks, `(httpx.HTTPError, httpx.TimeoutException)` for HTTP | `agents/gemini_agent.py`, `agents/ollama_agent.py`, `agents/deepseek_agent.py`, `cli/interface.py`, `cli/commands.py`, `utils/source_validator.py` |
| 3 | C5 | Added `py_modules=["main"]` to setup.py so root main.py is packaged; filtered blank lines from requirements | `setup.py` |
| 4 | C2 | Implemented full Claude agent with Anthropic Messages API, `x-api-key` auth, JSON eval parsing, retry support | `agents/claude_agent.py` (new) |
| 5 | C3 | Implemented full OpenAI agent with Bearer auth, `response_format` for JSON eval, retry support | `agents/openai_agent.py` (new) |
| 6 | C2+C3 | Registered claude and openai providers in council's `add_agent()` | `core/council.py` |
| 7 | H7 | Moved `import re` from method bodies to module top level | `agents/ollama_agent.py`, `agents/deepseek_agent.py`, `agents/gemini_agent.py` |
| 8 | H4+H8 | Removed `asyncio` (stdlib); pinned minimum versions for all deps | `requirements.txt` |
| 9 | H2 | Changed all `"active"`/`"eliminated"` string literals to `AgentStatus.ACTIVE`/`AgentStatus.ELIMINATED`; imported `AgentStatus` in `base_agent.py`, `council.py`, `voting.py`, `interface.py`, `commands.py` | `agents/base_agent.py`, `core/council.py`, `consensus/voting.py`, `cli/interface.py`, `cli/commands.py` |
| 10 | H5 | Changed session dir from `Path("storage/sessions")` to `~/.council/sessions`; RAG index from `Path("storage/rag_index.json")` to `~/.council/rag_index.json` | `storage/sessions.py`, `storage/rag.py` |
| 11 | H6 | Added `max_rounds`, `min_agents`, `rag_top_k`, `max_history`, `generate_timeout`, `evaluate_timeout` to `AppConfig`; replaced hardcoded `5`, `2`, `2`, `10` in council.py and commands.py | `storage/config.py`, `core/council.py`, `cli/commands.py` |
| 12 | H3 | Integrated `validate_sources()` into research pipeline — validates output source URLs between generation and voting phases | `core/council.py` |
| 13 | H1 | Added `chmod 0o600` on config file after save (owner-only read/write); moved config to `~/.council/config.yaml` | `storage/config.py` |
| 14 | M2 | Created shared `utils/paths.py` with `get_resource_path()`; replaced duplicate definitions in `cli/interface.py` and `storage/config.py` | `utils/paths.py` (new), `cli/interface.py`, `storage/config.py` |
| 15 | M5 | Added `generate_timeout`/`evaluate_timeout` params to `BaseAgent` and all subclasses; wired through from `AppConfig` via `council.add_agent()`; replaced all hardcoded timeout values | `agents/base_agent.py`, `agents/ollama_agent.py`, `agents/gemini_agent.py`, `agents/deepseek_agent.py`, `agents/claude_agent.py`, `agents/openai_agent.py`, `core/council.py` |
| 16 | M6 | Added threshold range validation (0-100), timeout validation (>0), provider validation against supported list, valid config key hints | `cli/commands.py` |
| 17 | M7 | `/council clear` now requires `/council clear confirm`; shows session count before deletion | `cli/commands.py` |
| 18 | M1 | Implemented `/council vote` (shows scores), `/council eliminate <id>` (manual elimination), `/council export [json|text]` (session export); registered in command map; updated help text | `cli/commands.py` |
| 19 | M3 | Created `utils/retry.py` with `retry_async()` — exponential backoff, retries on 429/5xx/connection errors; integrated into all cloud agents (Gemini, DeepSeek, Claude, OpenAI) | `utils/retry.py` (new), `agents/gemini_agent.py`, `agents/deepseek_agent.py`, `agents/claude_agent.py`, `agents/openai_agent.py` |

---

## Files Created
- `agents/claude_agent.py` — Full Claude/Anthropic agent implementation
- `agents/openai_agent.py` — Full OpenAI agent implementation
- `utils/paths.py` — Shared `get_resource_path()` utility
- `utils/retry.py` — Async retry with exponential backoff

## Files Modified (19 existing)
- `agents/base_agent.py` — AgentStatus enum, timeout params
- `agents/gemini_agent.py` — Security fix, imports, retry, timeouts, exceptions
- `agents/ollama_agent.py` — Imports, timeouts, exceptions
- `agents/deepseek_agent.py` — Imports, retry, timeouts, exceptions
- `cli/interface.py` — Shared paths import, AgentStatus, exceptions
- `cli/commands.py` — New commands, validation, AgentStatus, history limit, clear confirm
- `core/council.py` — New providers, enum usage, config-driven limits, source validation
- `consensus/voting.py` — AgentStatus enum
- `storage/config.py` — New config fields, shared paths import, chmod, ~/.council path
- `storage/sessions.py` — ~/.council path
- `storage/rag.py` — ~/.council path
- `utils/source_validator.py` — Specific exception types
- `requirements.txt` — Removed asyncio, pinned versions
- `setup.py` — py_modules, filtered requirements

## Deferred
- **M4**: RAG vector indexing (FAISS/ANN) — larger architectural change, deferred to separate PR

---

## Summary
- **19/20 issues fixed** (1 deferred)
- **4 new files created**
- **14 existing files modified**
- **0 pushes made** (per constraint)
