# OMP Embedded Documentation Reference Map

OMP embeds 131 authoritative Markdown documentation files directly inside the binary.
Read any document instantly using: `omp read omp://<path>`
Or search across all documents using: `~/.gemini/skills/investigate-omp/scripts/query_omp_docs.py <query>`

---

## CLI, Core Lifecycle & SDK (8 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://cli-reference.md` | **CLI reference** | `omp` is invoked as: |
| `omp://auth-broker-gateway.md` | **Auth Broker and Auth Gateway** | The auth broker and auth gateway are two cooperating HTTP services that move OAuth... |
| `omp://collab.md` | **Collab: Live Session Sharing** | `/collab` shares your running session with other omp instances in real time. Guest... |
| `omp://rpc.md` | **RPC Protocol Reference** | RPC mode runs the coding agent as a newline-delimited JSON protocol over stdio. |
| `omp://sdk.md` | **SDK** | The SDK is the in-process integration surface for `@oh-my-pi/pi-coding-agent`. |
| `omp://user-facing-packages.md` | **User-Facing Packages** | This page indexes README-only user-facing package CLIs and features that need root... |
| `omp://slash-command-internals.md` | **Slash command internals** | This document describes how slash commands are discovered, deduplicated, surfaced ... |
| `omp://install-id.md` | **Install ID** | A persistent per-install UUID shared across sessions and profiles. It supplies a s... |

## Configuration & Runtime Settings (7 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://settings.md` | **Settings** | `omp` resolves settings from built-in defaults, a persistent global config file, o... |
| `omp://config-usage.md` | **Configuration Discovery and Resolution** | This document describes how the coding-agent resolves configuration today: which r... |
| `omp://environment-variables.md` | **Environment Variables (Current Runtime Reference)** | This reference is derived from current code paths in: |
| `omp://keybindings.md` | **Keybindings** | Run `/hotkeys` inside an `omp` session to see the active chords for your current b... |
| `omp://theme.md` | **Theming Reference** | This document describes how theming works in the coding-agent today: schema, loadi... |
| `omp://context-files.md` | **Context files** | Context files are Markdown instruction files that `omp` discovers automatically be... |
| `omp://magic-keywords.md` | **Magic keywords** | Magic keywords are standalone prose words in a user prompt that can add hidden, us... |

## Tool Approvals, Sandboxing & Security (3 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://approval-mode.md` | **Tool approval mode** | Tool approval has three inputs: |
| `omp://bash-tool-runtime.md` | **Bash tool runtime** | This document describes the **`bash` tool** runtime path used by agent tool calls,... |
| `omp://secrets.md` | **Secret Obfuscation** | Prevents sensitive values (API keys, tokens, passwords) from being sent to LLM pro... |

## Built-in Tool Implementations (32 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://tools/ask.md` | **ask** | > Prompts the interactive user for one or more option-picker or free-form answers. |
| `omp://tools/ast-edit.md` | **ast_edit** | > Preview and apply structural rewrites over source files via native ast-grep. |
| `omp://tools/ast-grep.md` | **ast_grep** | > Structural code search over supported source files via native ast-grep. |
| `omp://tools/bash.md` | **bash** | > Execute a shell command in the session workspace, with optional PTY or backgroun... |
| `omp://tools/browser.md` | **Browser Eval prelude** | The Eval `browser` facade opens, reuses, scripts, and closes named Chromium, Elect... |
| `omp://tools/checkpoint.md` | **checkpoint** | > Mark the current top-level conversation state so later `rewind` can collapse exp... |
| `omp://tools/computer.md` | **computer Eval prelude** | > Drive the real host desktop from Eval through direct `computer` helpers and wind... |
| `omp://tools/context-notes.md` | **context_notes** | > Read or replace the current branch's persistent experimental context notebook. |
| `omp://tools/debug.md` | **debug** | > Drive one DAP debug session; adjacent debug UI code reuses the same subsystem fo... |
| `omp://tools/edit.md` | **edit** | > Applies source edits. The default `hashline` mode consumes one line-anchored pat... |
| `omp://tools/eval.md` | **eval** | > Execute one Python or JavaScript cell in a persistent language runtime. One tool... |
| `omp://tools/generate_image.md` | **generate_image** | > Generate or edit images and write generated image files to temporary paths. |
| `omp://tools/github.md` | **github** | > Dispatch GitHub CLI operations for repositories, repository files, pull requests... |
| `omp://tools/glob.md` | **glob** | > Find filesystem paths by glob; use `grep` when you need content matches instead ... |
| `omp://tools/grep.md` | **grep** | > Grep file contents with a regex across files, directories, globs, and internal U... |
| `omp://tools/hub.md` | **hub** | > The single agent-coordination surface: peer messaging over the process-global ma... |
| `omp://tools/learn.md` | **learn** | > Capture a reusable lesson into long-term memory and optionally create or update ... |
| `omp://tools/lsp.md` | **lsp** | > Query language servers for diagnostics, navigation, symbols, renames, code actio... |
| `omp://tools/manage_skill.md` | **manage_skill** | > Create, update, or delete an isolated managed skill. |
| `omp://tools/memory_edit.md` | **memory_edit** | > Update, forget, or invalidate Mnemopi long-term memories by id. |
| `omp://tools/new-context.md` | **new_context** | > Request a fresh experimental context window while preserving the current noteboo... |
| `omp://tools/read.md` | **read** | > Read files, directories, archives, SQLite databases, internal resources, images,... |
| `omp://tools/recall.md` | **recall** | > Search the active long-term memory backend and return matching memories. |
| `omp://tools/reflect.md` | **reflect** | > Synthesize an answer over the active long-term memory backend. |
| `omp://tools/retain.md` | **retain** | > Store durable facts through the active long-term memory backend. |
| `omp://tools/rewind.md` | **rewind** | > End an active checkpoint by pruning exploratory context and retaining a concise ... |
| `omp://tools/security_scan.md` | **security_scan** | > Plan and run OMP-native security reviews, validate stored findings, and explicit... |
| `omp://tools/task.md` | **task** | > Spawn subagents — one per call, or a `tasks[]` batch per call (`task.batch`, def... |
| `omp://tools/todo.md` | **todo** | > Applies one mutation to the session todo list and returns a text summary plus th... |
| `omp://tools/tts.md` | **tts** | > Generate a speech audio file from text and write it to `output_path`. |
| `omp://tools/web_search.md` | **web_search** | > Run one web query through the first available search provider and return LLM-for... |
| `omp://tools/write.md` | **write** | > Create or overwrite a file, writable internal resource, archive entry, SQLite ro... |

## Native Engine & Rust Layer (10 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://natives-architecture.md` | **Natives Architecture** | `@oh-my-pi/pi-natives` combines a JavaScript ESM loader with a Rust Node-API addon: |
| `omp://natives-addon-loader-runtime.md` | **Natives Addon Loader Runtime** | This page documents `packages/natives/native/loader-state.js`, the runtime between... |
| `omp://natives-binding-contract.md` | **Natives Binding Contract (JavaScript/TypeScript Side)** | This page defines the public JS/TS boundary between `@oh-my-pi/pi-natives` callers... |
| `omp://natives-build-release-debugging.md` | **Natives Build, Release, and Debugging Runbook** | This runbook describes how `@oh-my-pi/pi-natives` produces `.node` addons, generat... |
| `omp://natives-media-system-utils.md` | **Natives media + system utilities** | This document covers the media/system/conversion exports currently present in `@oh... |
| `omp://natives-rust-task-cancellation.md` | **Native Rust task execution and cancellation (`pi-natives`)** | This document describes how `crates/pi-natives` schedules native work and how canc... |
| `omp://natives-shell-pty-process.md` | **Natives Shell, PTY, Process, and Key Internals** | This document covers execution/process/terminal primitives in `@oh-my-pi/pi-native... |
| `omp://natives-text-search-pipeline.md` | **Natives Text/Search Pipeline** | This document maps the `@oh-my-pi/pi-natives` text/search/code surface from genera... |
| `omp://native-crates.md` | **Native Crates** | Contributor map for Rust workspace members under `crates/`. They are implementatio... |
| `omp://porting-to-natives.md` | **Porting Hot Paths to `pi-natives`** | This is the contributor path for moving a measured JS/TS hot path into `crates/pi-... |

## Agent Orchestration & Subagents (5 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://agent-hub.md` | **Agent Hub** | Agent Hub is the interactive TUI for watching and controlling subagents associated... |
| `omp://task-agent-discovery.md` | **Task Agent Discovery and Selection** | This document describes how the task subsystem discovers agent definitions, merges... |
| `omp://prewalk.md` | **Prewalk** | Prewalk is a one-shot handoff from the active model to a faster or cheaper model a... |
| `omp://advisor-watchdog.md` | **Advisor, WATCHDOG.md, and WATCHDOG.yml** | The advisor subsystem attaches one or more optional reviewer models to a session. ... |
| `omp://system-prompt-customization.md` | **System Prompt Customization** | How the coding agent assembles its system prompt and what users can control with `... |

## Extensions, Hooks & Plugins (13 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://extensions.md` | **Extensions** | Primary guide for authoring runtime extensions in `packages/coding-agent`. |
| `omp://extension-loading.md` | **Extension Loading (TypeScript/JavaScript Modules)** | This document covers how the coding agent discovers and loads extension modules at... |
| `omp://hooks.md` | **Hooks** | This document describes the **current hook subsystem code** in `packages/coding-ag... |
| `omp://skills.md` | **Skills** | Skills are file-backed capability packs discovered at startup and exposed to the m... |
| `omp://plugin-manager-installer-plumbing.md` | **Plugin manager and installer plumbing** | This document describes how `omp plugin` npm/git/link and marketplace operations m... |
| `omp://skills/authoring-extensions.md` | **Authoring Extensions** | name: authoring-extensions |
| `omp://skills/authoring-hooks.md` | **Authoring Hooks** | name: authoring-hooks |
| `omp://skills/authoring-marketplaces.md` | **Authoring Marketplaces** | name: authoring-marketplaces |
| `omp://skills/examples/hello-extension/README.md` | **hello-extension** | A minimal `oh-my-pi` extension that demonstrates the two most common authoring pat... |
| `omp://skills/examples/mini-marketplace/README.md` | **mini-marketplace** | A minimal `oh-my-pi` marketplace catalog that demonstrates the `marketplace.json` ... |
| `omp://skills/examples/safety-hook/README.md` | **safety-hook** | An `oh-my-pi` extension that demonstrates `tool_call` blocking. It intercepts `bas... |
| `omp://marketplace.md` | **Marketplace plugin system** | The marketplace system lets you discover, install, and manage plugins from Git, lo... |
| `omp://gemini-manifest-extensions.md` | **Gemini Manifest Extensions (`gemini-extension.json`)** | This document covers how the coding-agent discovers and parses Gemini-style manife... |

## Model Context Protocol (MCP) (4 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://mcp-config.md` | **MCP configuration in OMP** | This guide explains how to add, edit, and validate MCP servers for the OMP coding ... |
| `omp://mcp-protocol-transports.md` | **MCP Protocol and Transport Internals** | This document describes how coding-agent implements MCP JSON-RPC messaging and how... |
| `omp://mcp-runtime-lifecycle.md` | **MCP runtime lifecycle** | This document describes how MCP servers are discovered, connected, exposed as tool... |
| `omp://mcp-server-tool-authoring.md` | **MCP server and tool authoring** | This document explains how MCP server definitions become callable `mcp__*` tools i... |

## Providers, Models & Converters (20 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://models.md` | **Model and Provider Configuration (`models.yml` / `models.yaml`)** | This document describes how the coding-agent currently loads models, applies overr... |
| `omp://providers.md` | **Providers** | Providers are the model backends `omp` can route requests to: Anthropic, OpenAI, G... |
| `omp://adding-a-provider.md` | **Adding a provider** | A provider is described in two halves: |
| `omp://local-models.md` | **Embedded Local Tiny-Model Experiments** | This document summarizes the experiments behind the optional **local** tiny-model ... |
| `omp://provider-compat-reference.md` | **Provider compat reference: OpenAI compat flags, reasoning levels, and tool handling** | Reference for four subsystems of `packages/ai` (with type definitions in `packages... |
| `omp://provider-endpoint-constraints.md` | **Provider endpoint constraints** | Provider integrations are not interchangeable just because they speak an |
| `omp://provider-quirks.md` | **Provider quirks: special casings, streams, auth, and catalog handling** | Per-provider deep dive for `packages/ai` transports: what each provider special-ca... |
| `omp://provider-streaming-internals.md` | **Provider streaming internals** | This document explains how token/tool streaming is normalized in `@oh-my-pi/pi-ai`... |
| `omp://toolconv/anthropic.md` | **Anthropic Claude tool use (Messages API content blocks)** | Anthropic's Claude is a closed, hosted model family; there are no released weights... |
| `omp://toolconv/deepseek.md` | **DeepSeek tool-calling wire format** | DeepSeek's chat models (DeepSeek-V3, V3-0324, R1, R1-0528, and DeepSeek-V3.1) share a |
| `omp://toolconv/gemini.md` | **Gemini Pythonic tool-calling format (`tool_code` / `default_api`)** | Tool-calling convention of Google's hosted **Gemini** models (current generation, ... |
| `omp://toolconv/gemma.md` | **Gemma 4 tool-calling format (token-delimited `call:NAME{…}`)** | Tool-calling convention of Google's **Gemma 4** open-weights family (`google/gemma... |
| `omp://toolconv/glm-4.5.md` | **GLM-4.5 / GLM-4.6 tool-calling format** | Native tool-calling convention of Zhipu AI / Z.ai's **GLM-4.5** family (`zai-org/G... |
| `omp://toolconv/harmony.md` | **OpenAI Harmony response format** | Harmony is the response format OpenAI trained its open-weight `gpt-oss` models on ... |
| `omp://toolconv/hermes.md` | **Hermes tool-calling format** | Tool-calling convention originated by NousResearch's **Hermes 2 Pro** (Llama-3-bas... |
| `omp://toolconv/kimi-k2.md` | **Kimi K2 tool-calling format** | Native tool-calling convention of Moonshot AI's **Kimi K2** family (`moonshotai/Ki... |
| `omp://toolconv/minimax.md` | **MiniMax owned tool-calling format (`<minimax:tool_call>`)** | OMP's `minimax` dialect is the prompt-driven, in-band tool protocol for MiniMax-fa... |
| `omp://toolconv/pi-native.md` | **pi-native auth-gateway transport** | `pi-native` is the lossless transport between a pi-ai client and an |
| `omp://toolconv/qwen3.md` | **Qwen3 tool-calling format (Hermes convention)** | Tool-calling convention of Alibaba's **Qwen3** family (`Qwen/Qwen3-*`: dense `0.6B... |
| `omp://toolconv/xml.md` | **Generic XML owned tool-calling format (`<invoke>` / `<tool_response>`)** | OMP's `xml` dialect is a generic, prompt-driven in-band protocol. The model writes... |

## Memory & Session Lifecycle (9 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://memory.md` | **Autonomous Memory** | Oh My Pi supports five memory modes. Memory is disabled by default; select one bac... |
| `omp://mnemosyne-memory-backend.md` | **Mnemopi memory backend** | Oh My Pi can use `@oh-my-pi/pi-mnemopi` as a local long-term memory backend. |
| `omp://session.md` | **Session Storage and Entry Model** | This document is the source of truth for how coding-agent sessions are represented... |
| `omp://session-tree-plan.md` | **Session tree architecture (current)** | Reference: [session.md](./session.md) |
| `omp://session-operations-export-share-fork-resume.md` | **Session Operations: export, dump, share, fresh, clear, fork, resume/continue** | This document describes operator-visible behavior for session export, sharing, con... |
| `omp://session-switching-and-recent-listing.md` | **Session switching and recent session listing** | This document describes how coding-agent discovers recent sessions, resolves `--re... |
| `omp://tree.md` | **`/tree` Command Reference** | `/tree` opens the interactive **Session Tree** navigator. It lets you jump to any ... |
| `omp://compaction.md` | **Compaction and Branch Summaries** | Compaction and branch summaries are the two mechanisms that keep long sessions usa... |
| `omp://handoff-generation-pipeline.md` | **`/handoff` generation pipeline** | This document describes how the coding-agent implements `/handoff`: trigger path, ... |

## TUI & Terminal Graphics (3 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://tui.md` | **TUI integration for extensions and custom tools** | This document covers the **current** TUI contract used by `packages/coding-agent` ... |
| `omp://tui-core-renderer.md` | **TUI core renderer — explicit history and viewport contract** | This document describes the core renderer contract. The relevant implementation |
| `omp://tui-runtime-internals.md` | **TUI runtime internals** | This document maps terminal input and rendering ownership in interactive mode. See... |

## Advanced Internals & Architecture (17 files)

| Document URI | Title | Summary / Purpose |
| :--- | :--- | :--- |
| `omp://ERRATA-GPT5-HARMONY.md` | **ERRATA — GPT-5 Harmony-Header Leakage** | Historical research note, not a current runtime contract. The statistics below |
| `omp://ai-schema-normalize.md` | **AI tool-schema normalization** | `@oh-my-pi/pi-ai` exposes one unified schema normalizer that providers consume |
| `omp://blob-artifact-architecture.md` | **Blob and artifact storage architecture** | This document describes how coding-agent stores large/binary payloads outside sess... |
| `omp://computer-use.md` | **Scriptable computer use** | Eval's `computer` prelude controls the host desktop. It can enumerate windows and ... |
| `omp://custom-tools.md` | **Custom Tools** | Custom tools are model-callable functions that plug into the same tool execution p... |
| `omp://fs-scan-cache-architecture.md` | **Filesystem scan cache architecture contract** | This document defines the shared Rust filesystem scan cache implemented by `crates... |
| `omp://lsp-config.md` | **LSP configuration in OMP** | This guide explains how to configure language servers for the OMP coding agent. |
| `omp://macos-signing-notarization.md` | **macOS signing & notarization** | The compiled macOS `omp` binaries shipped on GitHub Releases can be signed with a |
| `omp://non-compaction-retry-policy.md` | **Non-compaction auto-retry policy** | This document describes the standard API-error retry path coordinated by `AgentSes... |
| `omp://notebook-tool-runtime.md` | **Notebook file runtime internals** | This document describes current `.ipynb` handling in `coding-agent` and its relati... |
| `omp://omptype-guide.md` | **omptype Guide (schema authoring in this repo)** | Internal schemas use **`@oh-my-pi/omptype`** — an ArkType-compatible validator |
| `omp://porting-from-pi-mono.md` | **Porting From pi-mono: A Practical Merge Guide** | This guide is a repeatable checklist for porting changes from pi-mono into this repo. |
| `omp://python-repl.md` | **Eval Tool Python Backend** | This document describes the Python execution stack in `packages/coding-agent`. |
| `omp://resolve-tool-runtime.md` | **Resolution devices runtime** | Pending previews and plan approval do not use a `resolve` tool. They finalize thro... |
| `omp://rulebook-matching-pipeline.md` | **Rulebook Matching Pipeline** | This document describes how coding-agent discovers rules from supported config for... |
| `omp://ttsr-injection-lifecycle.md` | **TTSR Injection Lifecycle** | This document covers the current Time Traveling Stream Rules (TTSR) runtime path f... |
| `omp://vibe-mode.md` | **Vibe mode** | Vibe mode turns the top-level interactive session into a **director** for persiste... |
