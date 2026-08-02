# Codex CLI Essentials Cheat Sheet

A practical reference of the most important Codex CLI commands for daily development.

---

# Table of Contents

1. Starting Codex
2. Core CLI Commands
3. Slash Commands
4. Approval Modes
5. Sandbox Modes
6. Keyboard Shortcuts
7. Typical Workflow
8. Commands to Memorize

---

# 1. Starting Codex

Start an interactive Codex session in the current project.

```bash
codex
```

Start Codex with an initial prompt.

```bash
codex "Explain this repository"
```

Run Codex non-interactively (ideal for CI/CD or scripts).

```bash
codex exec "Fix lint errors"
```

Resume a previous Codex session.

```bash
codex resume
```

Fork an existing session into a new conversation.

```bash
codex fork
```

Review changes or commits.

```bash
codex review
```

Apply the latest generated patch.

```bash
codex apply
```

Login.

```bash
codex login
```

Logout.

```bash
codex logout
```

Manage MCP servers.

```bash
codex mcp
```

Upgrade Codex.

```bash
codex --upgrade
```

---

# 2. Core CLI Commands

| Command | Description |
|----------|-------------|
| `codex` | Start interactive mode |
| `codex "task"` | Start with an initial prompt |
| `codex exec` | Non-interactive execution |
| `codex review` | Review code changes |
| `codex apply` | Apply generated patch |
| `codex resume` | Resume previous session |
| `codex fork` | Fork existing session |
| `codex login` | Login |
| `codex logout` | Logout |
| `codex mcp` | Manage MCP servers |
| `codex --upgrade` | Upgrade CLI |

---

# 3. Slash Commands

These commands are available inside an interactive Codex session.

---

## Help

Display every available command.

```text
/help
```

---

## Status

Display current session information.

```text
/status
```

Shows:

- Active model
- Approval mode
- Sandbox mode
- Active skills
- Session information

---

## Clear Conversation

Clear chat history without leaving the current project.

```text
/clear
```

Alias:

```text
/c
```

---

## Reset Session

Start a completely fresh session.

```text
/reset
```

---

## Change Model

Switch models.

```text
/model gpt-5
```

Example:

```text
/model gpt-5-mini
```

---

## Approval Mode

Safest mode.

```text
/approval suggest
```

Automatically edit files but ask before executing commands.

```text
/approval auto-edit
```

Allow Codex to edit files and execute commands autonomously.

```text
/approval full-auto
```

---

## Sandbox Mode

Read-only access.

```text
/sandbox read-only
```

Workspace write access.

```text
/sandbox workspace-write
```

Maximum access.

```text
/sandbox danger-full-access
```

---

## Review

Review the current changes.

```text
/review
```

Alias:

```text
/r
```

---

## Load Skills

Load an installed skill.

```text
/use
```

Example:

```text
/use java
```

---

## Connected Apps

Manage connected applications.

```text
/apps
```

---

# 4. Approval Modes

## Suggest

```
Read files        ✅
Edit files        ❌ (asks first)
Run commands      ❌ (asks first)
```

Recommended when learning a new project.

---

## Auto Edit

```
Read files        ✅
Edit files        ✅
Run commands      ❌ (asks first)
```

Recommended for daily development.

---

## Full Auto

```
Read files        ✅
Edit files        ✅
Run commands      ✅
```

Recommended for repetitive tasks such as:

- Refactoring
- Running tests
- Fixing lint errors
- Code formatting
- Boilerplate generation

---

# 5. Sandbox Modes

## Read Only

- Can inspect files
- Cannot modify anything

Best for audits and code review.

---

## Workspace Write

- Can modify project files
- Cannot access outside workspace

Recommended for normal development.

---

## Danger Full Access

- Full filesystem access
- Can execute unrestricted commands

Use only when necessary.

---

# 6. Keyboard Shortcuts

| Shortcut | Action |
|-----------|--------|
| Ctrl + C | Cancel current task |
| Tab | Auto-complete commands |
| ↑ | Previous prompt |
| ↓ | Next prompt |

---

# 7. Typical Daily Workflow

```bash
cd my-project

codex

/status

/model gpt-5

/approval auto-edit

Explain this repository.

Find dead code.

Refactor authentication module.

Run unit tests.

Review my changes.

/review
```

---

# 8. Commands to Memorize

## CLI

```text
codex
codex exec
codex review
codex apply
codex resume
codex fork
codex login
codex logout
codex mcp
codex --upgrade
```

---

## Slash Commands

```text
/help
/status
/clear
/c
/reset
/model
/approval
/sandbox
/review
/r
/use
/apps
```

---

# 9. Recommended Daily Setup

Start your workday with:

```bash
codex
```

Then configure your session:

```text
/status

/model gpt-5

/approval auto-edit

/sandbox workspace-write
```

You're now ready to:

- Understand unfamiliar code
- Generate new features
- Refactor modules
- Fix bugs
- Run tests
- Review changes
- Generate documentation

---

# 10. Quick Reference

## Most Frequently Used

| Command | Usage |
|----------|------|
| `/help` | Show available commands |
| `/status` | View session information |
| `/model` | Change the AI model |
| `/approval auto-edit` | Enable automatic file edits |
| `/clear` | Clear conversation |
| `/review` | Review generated changes |

---

## Recommended Commands to Memorize

```
codex
codex exec
codex resume

/help
/status
/model
/approval auto-edit
/sandbox workspace-write
/review
/clear
```

Mastering these commands is sufficient for the vast majority of everyday development tasks with Codex.