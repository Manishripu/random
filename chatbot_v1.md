# LLM Output Safety & Clarification-First Design Plan
### Chatbot Integration — Spring Boot + Angular Portal (Bedrock Converse)

---

## 1. Goal

Ensure the chatbot's tool-calling behavior (especially `update_filters`) never:
- Produces output outside the expected schema
- Invents field names, operators, or values not present in the domain
- Silently guesses when user intent is ambiguous
- Applies a change to the UI without an explicit validation + confirmation gate

And instead:
- Prefers asking a clarifying question over guessing
- Fails closed, with model self-correction via feedback, when validation fails
- Never lets a raw model output directly mutate application state

---

## 2. Layered Defense Overview

| Layer | Mechanism | Catches |
|---|---|---|
| 1 | Bedrock tool-use (structured JSON Schema, `enum` constraints) | Malformed structure, invented field/operator names |
| 2 | Explicit `ask_clarifying_question` tool + system prompt rule | Ambiguous/missing user intent |
| 3 | Server-side JSON Schema validation (defense in depth) | Schema drift despite Bedrock's constraint |
| 4 | Domain/business-rule validation | Semantically invalid but schema-valid values |
| 5 | Bounded retry + feedback loop | Model self-correction without infinite loops |
| 6 | Propose-then-confirm UI pattern | Anything that slips through layers 1–5 |
| 7 | Bedrock Guardrails (optional) | Off-topic content, PII, prompt-injection via tool results |

No single layer is sufficient alone — implement all seven.

---

## 3. Tool Schema Design

### 3.1 `update_filters` tool
- `fieldName`: **enum** — restricted to actual filterable fields in `FilterStateService`. Never free string.
- `operator`: **enum** — restricted per field type (e.g. text fields get `contains`/`equals`; date fields get `before`/`after`/`between`).
- `value`: 
  - **enum** where the underlying data is a closed set (status, category, etc.)
  - free-text only where genuinely free-text (e.g. search term)
  - typed correctly (date, number) with format constraints in the schema
- Mark only truly required fields as `required`. Do not default optional fields — force explicit values or a clarifying question.

### 3.2 `ask_clarifying_question` tool
- `question`: string (required)
- `options`: string[] (optional — enables quick-reply buttons in Angular)
- Lightweight, always available alongside `update_filters` in the same `toolConfig`.

### 3.3 System prompt rule (explicit, with few-shot examples)
> When required filter information is missing, ambiguous, or not clearly and explicitly stated by the user, do NOT guess or default a value. Call `ask_clarifying_question` instead of `update_filters`. Only call `update_filters` when all required field values are explicitly stated or unambiguously implied.

Include 2–3 concrete negative examples in the prompt (e.g. "recent orders" without a date range → ask, don't infer "last 7 days").

---

## 4. Backend Validation Pipeline

Order of operations inside `Tool.execute()` for any mutating tool:

1. **JSON Schema validation** (`networknt/json-schema-validator` or `everit-json-schema`) — even though Bedrock already constrains output, validate again server-side. Treat client/model output as untrusted input, same as any REST payload.
2. **Domain validation** — check enum values against the live list of valid fields/operators/values (not just what was hardcoded in the schema at prompt-build time, in case the domain model has since changed).
3. **Authorization check** — confirm the current user is allowed to filter/view the referenced fields/data (reuse existing Spring Security checks, don't bypass them because the caller is an LLM).
4. **On failure**: do not execute against `FilterStateService`. Return a structured `tool_result` error back to the model describing exactly what was invalid, so the model can self-correct or fall back to `ask_clarifying_question`.
5. **On success**: emit a `filter_update` SSE event with the **proposed** change — do not apply directly.

```java
ToolValidationResult result = schemaValidator.validate(toolName, arguments);
if (!result.isValid()) {
    return ToolResult.error(result.getErrorMessage()); // fed back to model
}
DomainValidationResult domainResult = domainValidator.validate(arguments, userContext);
if (!domainResult.isValid()) {
    return ToolResult.error(domainResult.getErrorMessage());
}
// success: emit proposal, do not mutate state directly
```

---

## 5. Retry & Loop Bounds

- Cap tool-call iterations per user turn (recommended: **5** total, **2** validation-failure retries specifically for a single tool).
- If the retry cap is hit, terminate the turn gracefully: return a user-facing message like "I wasn't able to build that filter — could you clarify [specific missing piece]?" rather than looping silently or applying a best-guess.
- Log capped/failed loops for prompt-tuning review — repeated failures on the same tool usually indicate a schema or prompt gap, not a one-off.

---

## 6. Confidence Handling for Near-Matches

If a model-proposed value is a near-match but not an exact enum match (e.g. `"active-ish"` vs `"Active"`):
- **Do not silently auto-correct** to the nearest valid value.
- Reject with a message fed back to the model: `"'active-ish' is not a valid status. Valid values: Active, Inactive, Pending. Ask the user to clarify."`
- This routes ambiguity through the ask-path rather than papering over it with fuzzy matching, which can silently apply the wrong filter.

---

## 7. UI-Level Safety Net (Angular)

- Every model-proposed filter change arrives as a `filter_update` SSE event — rendered as a **proposal card**, not applied to `FilterStateService` directly:
  - "Claude suggests: status = Active, date > 30 days — **Apply** / **Edit** / **Cancel**"
- Additive changes vs. destructive changes (e.g. clearing existing filters) should be visually distinguished; consider requiring explicit confirmation for destructive ones specifically.
- `ask_clarifying_question` events render as a chat message, optionally with quick-reply buttons from `options`.
- Only an explicit user action ("Apply") calls into `FilterStateService`'s existing public API — the model never has a direct write path.

---

## 8. Optional Hardening

- **Bedrock Guardrails**: apply if tool results ever pull in user-generated or external content (e.g. search results feeding back into context), to catch prompt-injection attempts or PII leakage before they reach the next model turn.
- **Structured logging**: log every tool call (input, validation result, applied/rejected) per conversation ID — needed for debugging prompt drift and for any audit requirements around automated filter changes.
- **Shadow-mode rollout**: for the first release, log what the model *would* have applied without actually emitting `filter_update` to the UI, to sanity-check behavior against real usage before enabling the write path.

---

## 9. Rollout Sequence

1. Read-only tools only (search, lookup) — validate the full pipeline (schema, domain, retry, UI proposal pattern) on the lowest-risk surface.
2. Add `ask_clarifying_question` + system prompt rules; test ambiguous-input handling in isolation.
3. Add `update_filters` as a **propose-only** tool (no Apply button yet — just verify proposals look correct).
4. Enable the Apply flow with explicit user confirmation.
5. Only after this is stable, consider any tool with direct mutation (create/update) beyond filters.

---

## 10. Pre-Implementation Checklist

- [ ] `update_filters` schema uses `enum` for `fieldName` and `operator`, not free string
- [ ] `ask_clarifying_question` tool defined and included in every `toolConfig` alongside mutating tools
- [ ] System prompt contains explicit ask-vs-guess rule with negative few-shot examples
- [ ] Server-side JSON Schema validator wired into `Tool.execute()` for every tool
- [ ] Domain validator checks against live field/operator/value lists, not stale schema snapshot
- [ ] Authorization check reuses existing Spring Security context, not bypassed for LLM calls
- [ ] Failed validation returns structured error back to model (not silently dropped)
- [ ] Retry loop capped (recommended 2 validation retries / 5 total tool calls per turn)
- [ ] Near-match values rejected, not auto-corrected
- [ ] All mutating tool calls emit a proposal event; none mutate `FilterStateService` directly
- [ ] Angular renders Apply/Edit/Cancel for proposals, with destructive changes visually distinct
- [ ] Tool calls logged (input, validation result, outcome) per conversation
- [ ] Shadow-mode or propose-only rollout precedes enabling direct Apply
