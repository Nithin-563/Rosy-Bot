# Rosy v5 fixes

- Added the missing `aiosqlite` runtime dependency required by the SQLite fallback and test suite.
- Fixed the OpenAI-compatible provider's broken `_post_status` call (`_handle_status` is now used).
- Fixed provider attribution so OpenRouter/OpenAI/Groq/Mistral usage is recorded under the real provider instead of `openai-compat`.
- Added first-class `openrouter/free` and `openrouter/auto` configuration values; the default is now `openrouter/free`.
- Preserved OpenRouter-specific headers and environment defaults when a guild credential is stored without a custom base URL/model.
- Fixed tool execution's default permission so registered tools can actually run with the default permission.
- Fixed conversation history ordering so turns are sent chronologically rather than newest-first.
- Fixed conversation context to carry the current user ID and respect the memory-enabled setting.
- Fixed plugin lifecycle loading to call `on_load()` instead of a nonexistent `connect()` method.
- Hardened the web-fetch tool against private/local/metadata-network SSRF targets and unsafe redirects, and bounded response sizes/redirects.
- Added regression tests for provider calls, OpenRouter defaults, tool execution, and history ordering.

## Verification

- Python compilation: passed.
- Non-database regression suite: **20 passed**.
- The 8 DB-backed tests could not be executed in the current isolated build environment because `aiosqlite` is not installed there; the project now declares `aiosqlite>=0.20.0` so a normal install recreates the required dependency.
