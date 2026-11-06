# Connecting Agentic AI to GitHub Projects & Issues (`setup-workflow-projects.md`)

This guide explains how to connect and operate AI coding agents (Claude, Antigravity, Cursor, etc.) with GitHub Projects (v2) and GitHub Issues for the ClearPath repository, implementing the protocol defined in [`.github/agentic-workflow.yml`](.github/agentic-workflow.yml).

---

## 1. Overview & Architecture

ClearPath uses a **provider-neutral agentic workflow** where GitHub Projects acts as the single source of truth for task status, while GitHub Issues and labels provide searchable context and guardrails.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AGENTIC AI INTEGRATION                          │
└──────┬─────────────────────────┬───────────────────────────────┬───────┘
       │                         │                               │
       ▼                         ▼                               ▼
 [Method 1: MCP]         [Method 2: CLI / Script]      [Method 3: GitHub Actions]
 Ideal for IDE Agents    Ideal for Terminal Agents     Ideal for Event-Driven
 (Cursor, Claude, AGY)   (Antigravity CLI, Claude)     Automations (CI/Webhooks)
```

### Core Configuration Files in [`.github/`](.github/)
- **[`.github/agentic-workflow.yml`](.github/agentic-workflow.yml):** Workflow contract specifying project fields, lifecycle states (`Backlog`, `Ready`, `In progress`, `In review`, `Done`), required adapter operations, completion gates, and human approval rules.
- **[`.github/labels.yml`](.github/labels.yml):** Declarative label manifest (`status:*`, `track:*`, `priority:*`, `type:*`, `workflow:*`).
- **[`.github/ISSUE_TEMPLATE/agent-task.yml`](.github/ISSUE_TEMPLATE/agent-task.yml):** Structured issue template enforcing Goal, Context, Scope, Acceptance Criteria, Validation commands, and Out-of-Scope boundaries.

---

## 2. One-Time Setup: GitHub Project Board & Labels

Before connecting an AI agent, complete this initial setup in the GitHub web interface:

### Step 2.1: Create the GitHub Project (v2)
1. Go to your GitHub profile or organization ➔ **Projects** ➔ **New project**.
2. Select the **Board** or **Table** template.
3. Set the project title: **`ClearPath Delivery`**.
4. In project settings, link the repository: `Sergiu1809/Clearpath`.

### Step 2.2: Configure Custom Project Fields
Ensure the following fields exist in your project settings:
* **`Status`** (Single select options):
  * `Backlog`
  * `Ready`
  * `In progress`
  * `In review`
  * `Done`
* **`Track`** (Single select options):
  * `M1` (Extraction and keyboard traversal)
  * `M2` (Announcement engine, audit, and reporting)
  * `M3` (TTS, recording, and media rendering)
  * `M4` (Pipeline, API, web UI, and demo)
  * `Shared` (Contracts, common utilities, repository rules)
* **`Priority`** (Single select options):
  * `P0` (Blocks delivery)
  * `P1` (Current milestone)
  * `P2` (Important)
  * `P3` (Nice to have)
* **`Pull Request`** (Linked Pull Request field)

### Step 2.3: Import Labels from [`.github/labels.yml`](.github/labels.yml)
Using the GitHub CLI (`gh`), create the required labels:
```bash
# Status mirror labels
gh label create "status:backlog" --color "6b7280" --description "Captured work that is not ready to start" --force
gh label create "status:ready" --color "2563eb" --description "Ready, scoped, assigned work" --force
gh label create "status:in-progress" --color "f59e0b" --description "Work currently being implemented" --force
gh label create "status:in-review" --color "8b5cf6" --description "Implementation is under validation or review" --force
gh label create "status:done" --color "16a34a" --description "Merged and acceptance criteria verified" --force

# Workflow labels
gh label create "workflow:ready" --color "22c55e" --description "Meets definition of ready" --force
gh label create "workflow:blocked" --color "b91c1c" --description "Cannot proceed without dependency or decision" --force
gh label create "workflow:needs-review" --color "7c3aed" --description "Human review required" --force

# Track labels
gh label create "track:m1" --color "f97316" --description "Extraction and keyboard traversal" --force
gh label create "track:m2" --color "e11d48" --description "Announcement engine, audit, and reporting" --force
gh label create "track:m3" --color "a855f7" --description "TTS, recording, and media rendering" --force
gh label create "track:m4" --color "0891b2" --description "Pipeline, API, web UI, and demo" --force
gh label create "track:shared" --color "475569" --description "Shared files requiring team consensus" --force

# Priority labels
gh label create "priority:p0" --color "991b1b" --description "Blocks delivery or causes data loss" --force
gh label create "priority:p1" --color "c2410c" --description "Important for current milestone" --force
gh label create "priority:p2" --color "ca8a04" --description "Valuable but not immediately blocking" --force
gh label create "priority:p3" --color "65a30d" --description "Nice to have" --force

# Type labels
gh label create "type:feature" --color "0ea5e9" --description "New behavior or capability" --force
gh label create "type:bug" --color "dc2626" --description "Incorrect or broken behavior" --force
gh label create "type:chore" --color "64748b" --description "Maintenance or tooling work" --force
gh label create "type:documentation" --color "14b8a6" --description "Documentation-only work" --force
```

---

## 3. Connecting Your AI Agent (3 Methods)

### Method 1: Model Context Protocol (MCP) — Best for IDE Agents (Cursor, Claude, Antigravity)
The Model Context Protocol allows AI coding assistants to invoke GitHub tools directly within the IDE.

1. **Create a GitHub Personal Access Token (PAT):**
   * Go to **GitHub Settings** ➔ **Developer settings** ➔ **Personal access tokens** (classic or fine-grained).
   * Required Scopes: `repo` (all), `project` (read/write), `read:org`.
2. **Add GitHub MCP Server to your IDE Config:**
   * **In Claude Desktop** (`claude_desktop_config.json`):
     ```json
     {
       "mcpServers": {
         "github": {
           "command": "npx",
           "args": ["-y", "@modelcontextprotocol/server-github"],
           "env": {
             "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_yourTokenHere"
           }
         }
       }
     }
     ```
   * **In Cursor:** Settings ➔ Features ➔ MCP ➔ Add new MCP server:
     * Name: `github`
     * Type: `command`
     * Command: `npx -y @modelcontextprotocol/server-github` (with `GITHUB_PERSONAL_ACCESS_TOKEN` set in environment).
3. **Capabilities Unlocked:**
   * The AI can directly call `search_issues`, `get_issue`, `create_issue`, `create_pull_request`, and query the project board via GraphQL.

---

### Method 2: GitHub CLI (`gh` + `gh project`) — Best for Terminal Agents
If you use terminal-based AI agents (such as Antigravity CLI, Claude Code, or Aider), the agent can execute standard `gh` CLI commands to perform all 12 adapter operations.

1. **Install and Authenticate `gh`:**
   ```bash
   # Linux / WSL:
   sudo apt install gh
   # macOS:
   brew install gh
   # Windows:
   winget install GitHub.cli

   gh auth login
   gh auth refresh -s project   # Grants permission to read/write project boards
   ```
2. **Standard CLI Commands for Agent Operations:**

| Operation in `agentic-workflow.yml` | Command |
|---|---|
| `list_ready_work` | `gh issue list --label "status:ready" --label "workflow:ready"` |
| `assign_issue` | `gh issue edit <id> --add-assignee "@me"` |
| `set_project_status` (In progress) | `gh issue edit <id> --add-label "status:in-progress" --remove-label "status:ready"` |
| `add_issue_comment` | `gh issue comment <id> --body "Starting implementation on branch mX-..."` |
| `create_branch` | `git checkout -b m1-task-<id>` |
| `create_pull_request` | `gh pr create --title "[M1] <Title>" --body "Closes #<id>" --base main` |
| `set_project_status` (In review) | `gh issue edit <id> --add-label "status:in-review" --remove-label "status:in-progress"` |

---

### Method 3: GitHub Actions Event-Driven Workflow
You can trigger agent executions automatically when issues are labeled or assigned on the board.

Create `.github/workflows/agent-dispatcher.yml`:
```yaml
name: Agent Task Dispatcher

on:
  issues:
    types: [labeled, assigned]
  issue_comment:
    types: [created]

jobs:
  dispatch-agent:
    runs-on: ubuntu-latest
    if: >
      contains(github.event.issue.labels.*.name, 'workflow:ready') ||
      startsWith(github.event.comment.body, '/run-agent')
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Agent Task Runner
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: |
          echo "Agent received issue #${ISSUE_NUMBER}"
          # Invoke agent CLI or script to analyze issue, run tests, and open PR
```

---

## 4. The 5-Stage Task Lifecycle

AI agents and human developers must follow the sequential lifecycle defined in `agentic-workflow.yml`:

```
 1. BACKLOG             2. READY                3. IN PROGRESS          4. IN REVIEW            5. DONE
┌──────────────┐       ┌──────────────┐        ┌─────────────┐        ┌─────────────┐         ┌───────────┐
│ Issue filled │ ────► │ AC, scope &  │ ─────► │ Agent claims│ ─────► │ PR opened   │ ──────► │ Human     │
│ with template│       │ validation ok│        │ branch cut  │        │ tests run   │         │ merges PR │
└──────────────┘       └──────────────┘        └─────────────┘        └─────────────┘         └───────────┘
```

1. **Backlog:**
   * An issue is created using [`.github/ISSUE_TEMPLATE/agent-task.yml`](.github/ISSUE_TEMPLATE/agent-task.yml).
   * Must define: Track, Priority, Goal, Context, Scope, Acceptance Criteria, Validation commands, and Out-of-Scope boundaries.
2. **Ready:**
   * Human or lead verifies that Acceptance Criteria and Validation commands are unambiguous.
   * Add label `workflow:ready` and set status to `Ready` (`status:ready`).
3. **In progress:**
   * The agent claims the issue, sets status to `In progress` (`status:in-progress`), and cuts a track branch (e.g., `m2-audit-fixes`).
   * **Strict Boundary Rule:** The agent modifies **only** files listed in the issue's Scope section.
4. **In review:**
   * The agent runs the exact test commands specified in the issue's Validation section (e.g. `python -m worker.engine.audit http://localhost:8080/bad-checkout.html contracts/samples/nodes.json`).
   * The agent pushes the branch, opens a Pull Request (`Closes #<id>`), comments test results as evidence, and sets status to `In review` (`status:in-review`).
5. **Done:**
   * Human reviews the Pull Request and runs completion checks.
   * Pull Request is merged into `main`. The issue transitions to `Done` (`status:done`).

---

## 5. Human Approval Safeguards (Guardrails)

As enforced in `agentic-workflow.yml`, the AI agent is **never permitted** to perform the following actions autonomously without explicit human confirmation:

1. **Merging Pull Requests into `main`**
2. **Closing GitHub Issues**
3. **Modifying Shared Data Contracts** (`doc/1-foundation/data-contracts.md`, `contracts/selector.js`, `contracts/samples/`)
4. **Modifying Shared Dependencies** (`requirements.txt`)
5. **Editing files owned by another track** (violating file ownership in `doc/rules/repo-rules.md`)
6. **Altering workflow permissions or agent guardrails**
