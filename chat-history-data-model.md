# Unified Chat History Data Model — Security Analysis

> Analysis of local conversation storage formats and exported chat logs from 6 different AI coding-assistant sources. This document outlines the raw data schemas and proposes a normalized data model to enable analysis for leaked secrets, slopquatting, and company/customer information.
> Generated 2026-04-08.

---

## Part 1: Unified Data Model Proposal

### Sources Analyzed

| # | Source | Format | Storage Location / Files | Key Characteristics |
|---|--------|--------|-----------------|---------------------|
| 1 | **Claude Code** — Prompt History | JSONL | `~/.claude/history.jsonl` | Flat append-only user prompts |
| 2 | **Claude Code** — Conversations | JSONL | `~/.claude/projects/<slug>/<session>.jsonl` | Full transcripts with tool calls, thinking, file snapshots |
| 3 | **Claude Code** — Session Registry | JSON | `~/.claude/sessions/<pid>.json` | Lightweight PID ↔ session mapping |
| 4 | **Pi Agent** — Sessions | JSONL | `~/.pi/agent/sessions/.../<timestamp>_<id>.jsonl` | Compaction summaries, model changes, tool calls |
| 5 | **Antigravity** — Conversations | Protobuf (`.pb`) | `~/.gemini/antigravity/conversations/<id>.pb` | Binary, opaque without proto schema |
| 6 | **Antigravity** — Artifacts / Exports | MD + JSON | `~/.gemini/antigravity/brain/<id>/` & MD Exports | Implementation plans, tasks, raw markdown exports |
| 7 | **ChatGPT** — Browser Export | JSON | User-exported `.json` files | Simple `{title, messages[{id, author, content}]}` |
| 8 | **Gemini** — Browser Export | JSON | User-exported `.json` files | Same schema as ChatGPT exports (via same exporter) |

---

### Design Goals

1. **Normalize** all sources into one queryable structure
2. **Preserve provenance** — always know which source/file/line produced a finding
3. **Enable pattern matching** for:
   - **Secrets**: API keys, tokens, passwords, connection strings, certificates
   - **Slopquatting**: Hallucinated package names, fabricated CLI tools, invented APIs/roles
   - **Company/Customer PII**: Names, emails, domains, internal project names, portfolio numbers, client identifiers

---

### Unified Data Model

#### Core Entity: `Conversation`

```typescript
interface Conversation {
  id: string;                          // Normalized UUID or provider-specific ID
  provider: Provider;                  // Source system
  title: string | null;                // Human-readable title (if available)
  slug: string | null;                 // Machine-readable name (Claude Code slugs)
  
  // Time range
  startedAt: string;                   // ISO 8601
  endedAt: string | null;             // ISO 8601 (null if still active)
  
  // Context
  project: ProjectContext | null;      // What codebase/directory was active
  
  // Content
  messages: Message[];                 // Ordered conversation turns
  toolInvocations: ToolInvocation[];   // Extracted tool calls (flattened for analysis)
  artifacts: Artifact[];               // Plans, tasks, generated files
  
  // Ingestion metadata
  source: SourceInfo;                  // Where this data came from
}

enum Provider {
  CLAUDE_CODE    = "claude_code",
  PI_AGENT       = "pi_agent",
  ANTIGRAVITY    = "antigravity",
  CHATGPT        = "chatgpt",
  GEMINI         = "gemini",
}
```

#### `Message` — The core unit of analysis

```typescript
interface Message {
  id: string;                          // Unique message ID
  conversationId: string;              // Back-reference
  parentId: string | null;             // Conversation tree linking
  
  role: Role;                          // Who produced this message
  timestamp: string;                   // ISO 8601
  
  // Content (the text that gets scanned)
  textContent: string;                 // Plain text (thinking + response merged)
  thinkingContent: string | null;      // Extended thinking / chain-of-thought (separate for analysis)
  rawContent: any;                     // Original provider-specific content blocks
  
  // Metadata for context-aware analysis
  model: string | null;                // e.g. "claude-opus-4-6", "gpt-4o"
  stopReason: string | null;           // "end_turn", "tool_use", "max_tokens"
  tokenUsage: TokenUsage | null;       // Cost/usage tracking
  
  // Pre-extracted signals (populated during ingestion)
  containsCode: boolean;               // Whether message contains code blocks
  codeBlocks: CodeBlock[];             // Extracted code snippets
  mentionedFiles: string[];            // File paths mentioned or accessed
  mentionedUrls: string[];             // URLs mentioned
  mentionedPackages: string[];         // Package/library names mentioned
}

enum Role {
  USER      = "user",
  ASSISTANT = "assistant",
  SYSTEM    = "system",
  TOOL      = "tool",                  // Tool results / outputs
}
```

#### `ToolInvocation` — Flattened for security scanning

```typescript
interface ToolInvocation {
  id: string;                          // Tool use ID
  messageId: string;                   // Which message triggered this
  conversationId: string;              // Back-reference
  timestamp: string;                   // ISO 8601
  
  toolName: string;                    // Normalized: "bash", "file_edit", "file_read", 
                                       // "file_write", "web_search", "browser", etc.
  rawToolName: string;                 // Provider-specific: "Bash", "Edit", "Read", 
                                       // "Write", "toolCall", etc.
  
  // Input (what was requested)
  input: Record<string, any>;          // Tool-specific parameters
  inputText: string;                   // Flattened text representation for scanning
  
  // Output (what was returned)  
  output: string | null;               // Tool result text
  isError: boolean;                    // Whether the tool errored
  
  // Security-relevant extracted fields
  commandsRun: string[];               // Shell commands (from bash/terminal tools)
  filesAccessed: string[];             // File paths read/written/edited
  urlsAccessed: string[];              // URLs fetched
  packagesReferenced: string[];        // npm/pip/cargo packages mentioned
}
```

#### Auxiliary Entities

```typescript
interface ProjectContext {
  workingDirectory: string;            // Absolute path (e.g. "/home/lars/Developer/PAI")
  gitBranch: string | null;            // Current git branch
  projectSlug: string | null;          // Claude Code style slug
  repositoryName: string | null;       // Inferred repo name
}

interface CodeBlock {
  language: string | null;             // "python", "powershell", "rust", "bash", etc.
  content: string;                     // The actual code
  messageId: string;                   // Which message contains this
  role: Role;                          // Who wrote this code (user or assistant)
}

interface Artifact {
  conversationId: string;
  fileName: string;                    // e.g. "implementation_plan.md"
  artifactType: string;                // "implementation_plan", "task", "walkthrough", "other"
  content: string;                     // Full text content
  summary: string | null;              // From metadata.json
  updatedAt: string;                   // ISO 8601
  versions: number;                    // Number of resolved versions
}

interface SourceInfo {
  filePath: string;                    // Absolute path to source file
  fileFormat: "jsonl" | "json" | "protobuf" | "markdown";
  exporterVersion: string | null;      // e.g. "3.1.0" for ChatGPT exporter
  ingestedAt: string;                  // ISO 8601 — when we processed this
  lineRange: [number, number] | null;  // Line range in source file (for JSONL)
}

interface TokenUsage {
  inputTokens: number;
  outputTokens: number;
  cacheCreationTokens: number | null;
  cacheReadTokens: number | null;
}
```

---

### Analysis-Oriented Views

#### View 1: `SecretCandidate` — For leaked secrets detection

```typescript
interface SecretCandidate {
  conversationId: string;
  messageId: string;
  role: Role;                          // USER = user leaked it; ASSISTANT = AI hallucinated/echoed it
  provider: Provider;
  timestamp: string;
  
  matchType: SecretType;
  matchValue: string;                  // The actual matched string
  matchContext: string;                // Surrounding text (±200 chars)
  confidence: number;                  // 0.0–1.0
  
  // Where in the conversation
  sourceField: string;                 // "textContent", "thinkingContent", "toolInput", "toolOutput", "codeBlock"
  codeLanguage: string | null;         // If found in a code block
}

enum SecretType {
  API_KEY              = "api_key",
  ACCESS_TOKEN         = "access_token",
  PASSWORD             = "password",
  CONNECTION_STRING    = "connection_string",
  PRIVATE_KEY          = "private_key",
  CERTIFICATE          = "certificate",
  WEBHOOK_URL          = "webhook_url",
  CLIENT_SECRET        = "client_secret",
  TENANT_ID            = "tenant_id",
  ENVIRONMENT_VARIABLE = "env_variable",
}
```

#### View 2: `SlopquatCandidate` — For slopquatting detection

```typescript
interface SlopquatCandidate {
  conversationId: string;
  messageId: string;
  provider: Provider;
  timestamp: string;
  
  packageName: string;                 // The hallucinated package name
  ecosystem: PackageEcosystem;         // npm, pypi, crates.io, etc.
  
  // Evidence
  suggestedByAI: boolean;             // Was this in an assistant message?
  existsInRegistry: boolean | null;    // Result of registry lookup (null = not checked)
  similarRealPackages: string[];       // Typosquat candidates
  
  context: string;                     // Surrounding text showing usage
  installCommand: string | null;       // e.g. "pip install fake-package"
  
  // Additional hallucination signals
  fabricatedApiEndpoint: string | null;   // Non-existent API URL
  fabricatedCliTool: string | null;       // Non-existent CLI command
  fabricatedRole: string | null;          // Non-existent RBAC role (e.g. "Mailbox.AccessAsApp")
}

enum PackageEcosystem {
  NPM        = "npm",
  PYPI       = "pypi",
  CRATES_IO  = "crates_io",
  NUGET      = "nuget",
  GO         = "go",
  MAVEN      = "maven",
}
```

> **Note on Slopquatting**: The exported ChatGPT conversation "App Zugriff auf Postfach" contains several examples of the AI fabricating PowerShell roles and parameters (e.g. `Mailbox.AccessAsApp`, `ApplicationMail.Read`, `-CustomRecipientScope`). This represents high-value training/verification data for detection heuristics.

#### View 3: `PIICandidate` — For company/customer information detection

```typescript
interface PIICandidate {
  conversationId: string;
  messageId: string;
  role: Role;
  provider: Provider;
  timestamp: string;
  
  piiType: PIIType;
  matchValue: string;
  matchContext: string;
  confidence: number;
  
  // Categorization
  isInternal: boolean;                 // Company-internal info vs customer data
  dataSubject: string | null;          // "employee", "customer", "advisor", "system"
}

enum PIIType {
  EMAIL_ADDRESS        = "email",
  PERSON_NAME          = "person_name",
  COMPANY_NAME         = "company_name",
  DOMAIN_NAME          = "domain",
  IP_ADDRESS           = "ip_address",
  PORTFOLIO_NUMBER     = "portfolio_number",
  CLIENT_IDENTIFIER    = "client_id",
  INTERNAL_PATH        = "internal_path",
  INTERNAL_URL         = "internal_url",
  PROJECT_NAME         = "project_name",
  PHONE_NUMBER         = "phone_number",
  ADDRESS              = "physical_address",
}
```

---

## Part 2: Raw Provider Schema Specifications & Ingestion Notes

### 1. Claude Code — `~/.claude/projects/<slug>/<session-id>.jsonl`

Full conversation transcripts. Each line is a typed event. The slug is the project path with `/` replaced by `-` (e.g. `-home-lars-Developer-PAI`).

#### Unified Model Mapping
| Claude Code Field | Maps To | Notes |
|---|---|---|
| `type: "user"` → `message.content` | `Message.textContent` | String or ContentBlock array |
| `type: "assistant"` → `message.content` | `Message.textContent` + `thinkingContent` | Split thinking blocks from text/tool_use blocks |
| `type: "assistant"` → tool_use blocks | `ToolInvocation` | Extract tool name, input, and link to result via `tool_use_id` |
| `type: "user"` with `toolUseResult` | `ToolInvocation.output` | Match via `tool_use_id` |
| `cwd`, `gitBranch` | `ProjectContext` | Available on every event |
| `type: "file-history-snapshot"` | `ToolInvocation` (type: file_snapshot) | Track which files were modified |
| `permissionMode: "bypassPermissions"` | `Message` metadata flag | ⚠️ Security-relevant: user disabled safety checks |

#### Event Types
| Type | Subtype | Description |
|---|---|---|
| `permission-mode` | — | Permission mode set/changed |
| `system` | `local_command` | Slash command invocation + output |
| `user` | — | User prompt or tool result |
| `attachment` | — | Companion/plugin attachment metadata |
| `assistant` | — | Model response (text, thinking, tool calls) |
| `file-history-snapshot` | — | File state checkpoint for undo |
| `queue-operation` | — | Message queue (enqueue/dequeue during interrupts) |
| `system` | `stop_hook_summary` | Post-response hook execution results |
| `system` | `turn_duration` | Turn timing metadata |
| `last-prompt` | — | Final prompt text (session footer) |

*The raw events form a linked list/tree via `parentUuid` → `uuid` fields.*

---

### 2. Pi Agent Sessions — `~/.pi/agent/sessions/--home-lars--/`

Pi uses a JSONL format with short IDs and a different event taxonomy. Filename template: `<iso-timestamp>_<session-uuid>.jsonl`.

#### Unified Model Mapping
| Pi Agent Field | Maps To | Notes |
|---|---|---|
| `type: "message"`, `role: "user"` | `Message` (role: USER) | |
| `type: "message"`, `role: "assistant"` | `Message` (role: ASSISTANT) | Split thinking/text/toolCall blocks |
| `type: "message"`, `role: "toolResult"` | `ToolInvocation.output` | May contain base64 images |
| `type: "compaction"` → `summary` | Separate `Message` (role: SYSTEM) | Contains summarized context — **may still reference secrets** |
| `type: "compaction"` → `details.readFiles` | `ToolInvocation.filesAccessed` | Track which files were in context |
| `type: "custom"`, `customType: "web-search-results"` | `ToolInvocation` (type: web_search) | |

#### Event Types
| Type | Description |
|---|---|
| `session` | Session initialization (version, cwd) |
| `model_change` | Model selection event |
| `thinking_level_change` | Thinking level configuration |
| `message` | All conversation messages (user, assistant, toolResult) |
| `compaction` | Context window compression events |
| `custom` | Extension-specific events (e.g. web search results) |

---

### 3. ChatGPT & Gemini Browser Exports 

Both use the same generic exporter (version 3.1.0 JSON format). 

#### Unified Model Mapping
| Export Field | Maps To | Notes |
|---|---|---|
| `title` | `Conversation.title` | |
| `author: "user"` / `author: "ai"` | `Message.role` | Map "ai" → ASSISTANT (and "gemini", "chatgpt" → ASSISTANT logically) |
| `content` | `Message.textContent` | Single string, no structured blocks |
| `url` | `Conversation.source` | Original conversation URL |
| `exporter` version | `SourceInfo.exporterVersion` | |

> **Note**: ChatGPT/Gemini exports contain **no tool call structure** — everything is flattened into text content. Code blocks must be extracted via regex/parsing from the markdown content within the `content` string.

---

### 4. Antigravity Conversations

Antigravity operates with local directories containing `.pb` (Protocol Buffer) logs and `.md`/`.json` artifact files.

#### Unified Model Mapping
| Antigravity Data | Maps To | Notes |
|---|---|---|
| `.pb` files in `conversations/` | `Conversation` | ⚠️ Binary protobuf — need proto schema to decode |
| `brain/<id>/*.md` | `Artifact` | Implementation plans, tasks |
| `brain/<id>/*.metadata.json` | `Artifact.summary`, `Artifact.updatedAt` | |
| `brain/<id>/*.resolved.*` | `Artifact` version history | Multiple resolved versions |
| Exported `.md` chat logs | `Conversation` + `Message[]` | Markdown format with "User Input" / "Planner Response" sections |

> **Note on Antigravity `.pb` Logs**: The `.pb` files track extensive telemetry but are opaque without the appropriate protobuf schema. Standard data recovery may need to rely on the exported `.md` log files which are often stripped of codebase snippets, making the `brain/` artifact files and any available original source files critical for a full contextual security scan.

---

### Cross-Reference: Key Differences between Engine APIs (Claude vs Pi vs Export)

| Aspect | Claude Code | Pi Agent | Raw Text Exports (ChatGPT/Gemini/Antigravity MD) |
|---|---|---|---|
| **ID format** | UUID v4 (36 chars) | Short hex (8 chars) | Usually sequential `user-1` / `ai-1` or implicit |
| **Event linking** | `parentUuid` → `uuid` | `parentId` → `id` | None/List Order |
| **Message typing** | Separate `type: "user"` / `assistant` | Single `type: "message"` with `role` | Flattened inside a single JSON `messages` array |
| **Tool calls** | `tool_use` in content blocks | `toolCall` in content blocks | Stripped or present only as descriptive text |
| **Tool results** | Separate `type: "user"` with `tool_result` | Separate `role: "toolResult"` | Usually omitted or folded into text context |
| **Thinking** | `signature` field (crypto) | `thinkingSignature` | Included directly in text or omitted entirely |
| **Session meta** | `sessions/<pid>.json` registry | Inline `type: "session"` event | In JSON root metadata |
