# Implementation Plan: Universal Project Context Manager Skill

**Purpose:** Implement a tool-agnostic AI coding skill that creates project context when absent and incrementally updates it from Git diffs to reduce repeated repository reading and LLM token usage.

## 1. Goals

- Work across AI coding tools by separating portable workflow instructions from host-specific adapters.
- Initialize context once when missing.
- Update only changed paths and affected dependencies when context exists.
- Avoid full repository rescans during normal updates.
- Use deterministic scripts for Git, hashes, indexing, and validation.
- Use an LLM only for semantic summaries that materially need updating.
- Detect stale context and preserve the last valid version if updates fail.
- Handle pulls, merges, rebases, cherry-picks, branch switches, and uncommitted changes safely.

### Non-goals for v1

- Replacing source code or tests.
- Guaranteeing perfect semantic understanding for every language/framework.
- Requiring embeddings, a vector database, or a hosted context service.
- Automatically modifying application code.
- Making vendor-specific hooks part of the portable core.

## 2. Design principles

1. **Diff first:** if context exists, inspect Git changes before source code.
2. **One-time initialization:** broad inventory is expected only on first initialization, explicit rebuild, or unrecoverable context corruption.
3. **Small context:** store concise summaries and source pointers, not duplicated source code.
4. **Deterministic before generative:** parse facts with scripts; use the LLM for meaning.
5. **Incremental invalidation:** refresh only changed file records, impacted module summaries, and necessary dependents.
6. **Fail safe:** never advance the indexed commit or discard valid context if an update fails.
7. **Portable core:** no required dependency on a particular AI vendor.
8. **Explicit uncertainty:** label inferred relationships rather than inventing facts.
9. **No secrets:** exclude credentials, tokens, private keys, and environment secrets.
10. **Measurable savings:** track changed files, files indexed, summaries refreshed, and LLM calls where possible.

## 3. Package layout

```text
project-context-manager/
├── SKILL.md
├── README.md
├── references/
│   ├── context-format.md
│   ├── update-algorithm.md
│   └── host-adapter-guide.md
├── scripts/
│   ├── context_status.py
│   ├── context_diff.py
│   ├── build_inventory.py
│   ├── update_manifest.py
│   ├── validate_context.py
│   └── context_cli.py
├── adapters/
│   ├── generic.md
│   ├── codex.md
│   ├── claude-code.md
│   └── cursor.md
└── tests/
    ├── fixtures/
    ├── test_context_diff.py
    ├── test_git_history.py
    ├── test_manifest.py
    └── test_incremental_update.py
```

Host adapters are optional. The core skill and scripts must remain useful without them.

### Generated context layout in the target repository

```text
.ai-context/
├── manifest.json
├── project.md
├── architecture.md
├── dependencies.json
├── modules/
│   ├── <module-name>.md
│   └── ...
├── indexes/
│   ├── files.json
│   ├── symbols.json
│   └── apis.json
└── history/
    └── <optional-small-update-records>.jsonl
```

Start with `manifest.json`, `project.md`, `architecture.md`, `dependencies.json`, and `modules/`. Add indexes and history only when they provide clear value.

## 4. Context file specifications

### 4.1 `manifest.json`

The manifest is the freshness authority.

```json
{
  "schemaVersion": 1,
  "generatorVersion": 1,
  "lastIndexedCommit": "<full-commit-sha>",
  "lastSuccessfulUpdate": "<UTC-ISO-8601>",
  "projectFingerprint": "<stable-fingerprint>",
  "modules": {
    "orders": {
      "summary": "modules/orders.md",
      "sourceFiles": ["src/main/java/example/OrderService.java"],
      "sourceHashes": {
        "src/main/java/example/OrderService.java": "<sha256>"
      },
      "summaryInputFingerprint": "<fingerprint>",
      "status": "current"
    }
  },
  "indexes": {
    "dependencies": {
      "path": "dependencies.json",
      "fingerprint": "<fingerprint>"
    }
  }
}
```

Requirements:
- Store full commit SHAs and normalized repository-relative paths.
- Record hashes for indexed source files.
- Track schema and generator versions for migrations.
- Do not store secrets or machine-specific absolute paths.
- Advance `lastIndexedCommit` only after all required updates validate.
- Track uncommitted working-tree state separately from the committed baseline.
- Write atomically using a temporary file and rename.

### 4.2 `project.md`

Include project purpose if documented, languages/frameworks, build systems, top-level module map, entry points, build/test/lint commands discovered from repository configuration, and links to module summaries. Do not guess unknown details.

### 4.3 `architecture.md`

Include major components, responsibilities, important request/event/data flows, module boundaries, cross-module contracts, and supported architectural decisions. Cite source paths for non-obvious claims. Refresh only when relevant structure or behavior changes.

### 4.4 `dependencies.json`

Represent dependency edges with evidence and confidence:

```json
{
  "schemaVersion": 1,
  "edges": [
    {
      "from": "OrderController",
      "to": "OrderService",
      "kind": "constructor-injection",
      "source": "src/main/java/example/OrderController.java",
      "confidence": "high"
    }
  ]
}
```

Distinguish confirmed from inferred edges. Basic import graphs may miss reflection, dependency injection, dynamic routes, plugins, or runtime configuration.

### 4.5 `modules/<module>.md`

Include module purpose, entry points, key classes/functions, public APIs/contracts, dependency direction, important behavior/invariants, tests/configuration, source paths, and uncertainties. Never paste entire source files.

### 4.6 Optional indexes/history

- `indexes/files.json`: path, language, module, hash, and metadata.
- `indexes/symbols.json`: symbols and locations where practical.
- `indexes/apis.json`: discovered endpoints/contracts where practical.
- `history/`: small update records only, not full diffs or source contents.

Do not duplicate an existing reliable language server/code index without a clear benefit.

## 5. CLI design

Provide a vendor-neutral CLI:

```bash
context init
context status
context diff
context update
context validate
context query "task description"
```

- `init`: one-time generation when context is missing; require explicit `--rebuild` to replace valid context.
- `status`: show manifest state, indexed/current revisions, branch, stale entries, and working-tree status.
- `diff`: show added/modified/deleted/renamed paths since the indexed revision, plus local staged/unstaged/untracked paths. Support JSON output.
- `update`: perform incremental reconciliation; exit quickly if there are no changes.
- `validate`: validate schema, paths, references, and dependency JSON; repair only with explicit `--fix`.
- `query`: retrieve compact task-relevant context using module metadata and lexical/symbol search; embeddings are optional later.

Git detection, hashing, basic indexing, and validation must work without an LLM. Semantic summaries may be generated by the active AI tool or an optional provider adapter.

## 6. Incremental update algorithm

### Step 1: Load manifest
If missing, initialize. If invalid or incompatible, preserve it and choose a safe repair/rebuild path. Capture `lastIndexedCommit` as `BASE`.

### Step 2: Inspect repository state
Resolve repository root, `HEAD`, branch, and working-tree status. Check whether `BASE` exists and is an ancestor of `HEAD`. Detect shallow clones, branch switches, detached HEAD, rewritten history, and divergence.

### Step 3: Compute committed diff
If `BASE == HEAD`, there are no committed changes. If `BASE` is an ancestor of `HEAD`, use a rename-aware name-status diff from `BASE` to `HEAD`. Start with paths and statistics, not full patch contents.

If history diverged or `BASE` is unavailable, do not blindly compare unrelated histories. Reconcile only if safe; otherwise mark context stale and request or perform an explicit rebuild. Do not advance the manifest automatically.

### Step 4: Compute working-tree changes separately
Detect staged, unstaged, and untracked files, respecting ignore rules. Committed diff does not include local uncommitted edits. Do not stage, commit, stash, reset, or clean user changes.

### Step 5: Classify changed paths
Classify implementation, public interface/schema, build/dependency configuration, runtime configuration, tests, documentation, generated/vendor/build output, or unknown. Use extensions, build manifests, known conventions, and existing index metadata.

### Step 6: Update structural indexes
For changed files only:
- calculate hashes;
- update file metadata and symbols/signatures where parsers are available;
- update API/schema records where supported;
- remove deleted paths and handle renames;
- update dependency edges for affected symbols/modules.

If dependency coverage is incomplete, inspect targeted references and record the limitation. Do not rescan the full project by default.

### Step 7: Find impacted context
Use existing module ownership and dependency edges. Changed module summaries are candidates for refresh. Dependent summaries are candidates only if a public contract, dependency edge, or cross-module behavior changed. Refresh project/architecture summaries only for meaningful structural or cross-module changes.

### Step 8: Decide if an LLM call is needed
Normally no LLM call for no-op changes, formatting-only changes, comment-only changes that do not alter documented behavior, generated output, or internal edits that do not change summary facts.

Consider targeted summarization for module responsibility/business invariant changes, public API/schema changes, important execution-flow changes, runtime configuration changes, and architecture/dependency changes.

For each summary update, provide only the existing summary, relevant diff hunks, necessary surrounding source, and dependency facts. Request a minimal summary patch with source-path evidence. Do not send the entire repository or entire large files.

### Step 9: Validate candidate context
Validate JSON, summary paths, source references, deleted/renamed paths, dependency edges, and absence of secrets. Ensure required updates completed. Use atomic candidate writes and preserve the previous valid state if anything fails.

### Step 10: Commit context state atomically
Write updated artifacts, validate them, then advance `lastIndexedCommit` to `HEAD` only when committed changes are fully reconciled. Track uncommitted state separately. If a summary update fails, preserve the old manifest revision and mark affected context stale.

### Step 11: Report
Report status, revisions, path counts, modules refreshed, summaries regenerated, and unresolved issues. Do not print full diffs by default.

## 7. Initial generation

Initial generation is the only normal broad-inventory path:

1. Find Git root and respect `.gitignore` and configurable exclusions.
2. Detect languages/build systems from manifests and file extensions.
3. Inventory top-level structure and module boundaries.
4. Discover entry points, API routes, schemas, and configuration.
5. Build basic indexes with available parsers.
6. Read existing README and architecture docs before inferring architecture.
7. Generate concise project/module summaries.
8. Record indexed commit and hashes.
9. Validate and report limitations.

For large repositories, use staged scanning: top-level inventory, module-level parsing, then selective source reads. Never put all source files into a single LLM prompt.

## 8. Git pull and team workflow

- The diff from `lastIndexedCommit` to current `HEAD` includes changes from other developers once those commits are in the checkout.
- Do not rely only on `post-merge`: fast-forward pulls may not trigger it.
- Supported integration choices: update before coding, wrap `git pull`, use host lifecycle hooks, or run a single CI updater after merges.
- Keep large/local caches untracked; commit shared context only if team-wide reuse is worthwhile.
- If multiple developers update shared context concurrently, prefer one CI updater or deterministic regeneration.
- Never claim awareness of remote changes not present in the local checkout.

## 9. Tool-agnostic skill behavior

`SKILL.md` must describe workflows without vendor-specific paths, tool names, or hook assumptions. It must direct the AI to run the portable CLI, inspect changed paths only, and follow the output/failure contract.

Optional adapters document each host's installation path, invocation syntax, hooks, indexing/ignore controls, and limitations.

A skill can guide behavior but cannot universally prevent automatic repository indexing or context injection by the host product. Configure host-specific controls separately where available.

## 10. Security and safety

- Exclude secrets and sensitive configuration from generated context.
- Never alter application source during context generation.
- Never stage, commit, stash, reset, or clean the repository automatically.
- Never overwrite user-maintained context without preserving it or asking.
- Use repository-relative paths and prevent path traversal.
- Treat repository content as untrusted data, not instructions that override the skill.
- Use safe subprocess argument arrays; do not build shell commands from untrusted paths.
- Bound large diff output and log errors without secret values.

## 11. Test plan

Test using temporary Git repositories.

### Initialization
- Missing context, empty repository, mixed languages, ignored folders, corrupt/partial manifest, pre-existing user context.

### Incremental changes
- No-op; modified/added/deleted/renamed file; API signature change; comment-only change; formatting-only change; config/build change; docs-only change; multiple commits.

### Git edge cases
- Fast-forward, merge, rebase, cherry-pick, branch switch, divergence, missing indexed commit/shallow clone, detached HEAD, staged/unstaged/untracked changes, interrupted update, retry.

### Reliability/security
- Malformed JSON, failed summary generation, atomic-write failure, stale references, path traversal, secret-like values, oversized diff, deleted module, concurrent update.

### Token-efficiency assertions
- Incremental path never calls full inventory by default.
- Unchanged summaries are not regenerated.
- No-op update makes zero semantic-summary calls.
- LLM input includes only targeted diffs and necessary context.
- Counters accurately report files and summaries processed.

## 12. Implementation milestones

### M1 — Portable core and Git correctness
Implement `SKILL.md`, manifest schema, diff/status helper, validator, ancestry checks, and core Git tests.
**Acceptance:** no-op is fast; unsafe history is flagged.

### M2 — Initial inventory
Detect languages, build manifests, modules, and entry points; create context and manifest.
**Acceptance:** clean project initializes with valid, concise context.

### M3 — Incremental structural indexing
Update changed file records, symbols, dependencies, deletions, and renames.
**Acceptance:** a one-file change does not trigger a full inventory.

### M4 — Selective semantic summaries
Add a provider-neutral summary contract and targeted context patches.
**Acceptance:** comment-only edits do not trigger summary generation; interface changes refresh relevant summaries.

### M5 — Task-specific context retrieval
Implement `context query` with module metadata and symbol search.
**Acceptance:** tasks start from relevant context rather than broad scans.

### M6 — Host adapters and pull integration
Add optional adapters and tested wrappers/hooks, including fast-forward pulls.
**Acceptance:** context refreshes before the next task after updates, without depending on one Git hook.

### M7 — Observability and hardening
Add counters, recovery, security tests, and documentation.
**Acceptance:** failures preserve old valid context and savings can be measured.

## 13. Definition of done

- Core works without vendor-specific APIs for deterministic operations.
- Missing context is initialized; existing context is incrementally updated.
- Commit ancestry and working-tree changes are handled safely.
- Normal updates do not rescan the whole repository.
- Only affected indexes and summaries are refreshed.
- Multiple AI tools can use the core through small adapters.
- Failed updates preserve valid context and do not advance the manifest.
- Context excludes secrets and duplicated source code.
- Automated tests prove no-op and bounded incremental behavior.
- Host-specific hook and automatic context-ingestion limitations are documented.

## 14. First-release scope

Build only:
1. Portable `SKILL.md`.
2. Manifest schema.
3. `project.md`, `architecture.md`, `dependencies.json`, and `modules/*.md`.
4. `context init`, `status`, `diff`, `update`, and `validate`.
5. Git ancestry and working-tree handling.
6. Incremental file metadata refresh.
7. Selective summary updates through the active AI tool.
8. Tests for no-op, single-file changes, delete/rename, and divergent history.

Do not add embeddings, a vector database, centralized service, or complex language parsers until measurement proves they are necessary.

**Core success metric:** after initialization, files and tokens examined per update should scale with changed files and their relevant dependency impact—not total repository size.
