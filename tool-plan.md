# 🚀 Portal Release Sanity Automation Tool
## Chrome-Attached, Workflow-Driven, Zero-Auth Automation

---

## 1. OBJECTIVE

Build a **production-grade release sanity automation tool** that:
- Attaches to an **already logged-in Chrome browser**
- Automatically validates **critical workflows**
- Verifies **UI rendering, API behavior, and business logic**
- Produces a **deterministic PASS / FAIL report**
- Works reliably after every release

This tool must simulate **real human usage** of the portal and must **not** automate authentication.

---

## 2. NON-GOALS

- ❌ No unit tests
- ❌ No mocked APIs
- ❌ No fake users
- ❌ No login automation
- ❌ No flaky selectors or timing-based hacks

---

## 3. HIGH-LEVEL DESIGN PRINCIPLES

1. **Human-first validation**  
   If a human can complete workflows, the release is sane.

2. **Attach, don’t launch**  
   The tool must connect to an existing Chrome session.

3. **Workflow-based sanity**  
   Each check represents a real business flow.

4. **Fail fast, fail loud**  
   Any workflow failure, rendering issue, or console error = FAIL.

5. **Evidence-driven debugging**  
   Every failure must include screenshots, traces, and logs.

---

## 4. TECHNOLOGY STACK (MANDATORY)

- Node.js ≥ 18
- Playwright
- TypeScript
- Google Chrome (manual launch)
- Chrome DevTools Protocol (CDP)
- Optional: Slack / Email for reporting

---

## 5. EXECUTION FLOW (END-TO-END)

```text
1. Engineer starts Chrome with debugging enabled
2. Engineer logs into the portal manually
3. Sanity tool attaches to the running Chrome instance
4. Tool detects active authenticated tab
5. Tool executes sanity workflows sequentially
6. Tool validates UI, workflows, rendering, and console logs
7. Tool generates PASS / FAIL report with evidence
8. Tool exits with proper exit code


Project structure
portal-sanity/
│
├── runner/
│   └── attach.ts
│
├── workflows/
│   ├── dashboard.workflow.ts
│   ├── content.lifecycle.workflow.ts
│   ├── content.rendering.workflow.ts
│   ├── permissions.workflow.ts
│   ├── search.workflow.ts
│
├── checks/
│   ├── console.check.ts
│   ├── rendering.check.ts
│   ├── network.check.ts
│
├── cleanup/
│   └── cleanup.testdata.ts
│
├── report/
│   ├── reporter.ts
│   └── summary.json
│
├── config/
│   ├── sanity.config.ts
│   ├── routes.ts
│   └── selectors.ts
│
├── playwright.config.ts
└── README.md

8. BROWSER ATTACHMENT LOGIC (NON-NEGOTIABLE)

Mandatory Behavior
	•	Attach to existing Chrome
	•	Reuse browser context
	•	Reuse cookies, 10. WORKFLOW DESIGN RULES

Each workflow MUST:
	•	Represent a real business use case
	•	Start from a known route
	•	End in a verifiable success state
	•	Be deterministic
	•	Clean up created data






