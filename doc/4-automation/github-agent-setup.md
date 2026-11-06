# GitHub Agentic Automation Setup

This guide configures GitHub Issues and Projects as a provider-neutral control
plane for human developers and AI agents. Any AI provider can participate if it
can call GitHub through REST, GraphQL, the GitHub CLI, MCP, or an equivalent
integration.

## 1. Repository rules

The agent must read `CLAUDE.md` before selecting work. In particular:

- ClearPath work is divided into M1, M2, M3, and M4 ownership boundaries.
- Shared contracts, dependencies, `CLAUDE.md`, and `README.md` require team
  consensus.
- Contract schemas and samples are immutable without the documented procedure.
- English is used for code, documentation, commits, and agent communication.
- Browser, network, and subprocess operations need explicit timeouts.
- Agents must not commit or push unless explicitly instructed.

The official product and acceptance sources are `doc/PRD.md`,
`doc/SETUP.md`, `doc/1-foundation/`, and
`doc/3-integration/definition-of-done.md`.

## 2. Create the Project

Create a repository Project named **ClearPath Delivery** and add the repository
to it. Configure these fields:

| Field | Type | Values |
|---|---|---|
| Status | Single select | Backlog, Todo, Doing, Testing, Done |
| Track | Single select | M1, M2, M3, M4, Shared |
| Priority | Single select | P0, P1, P2, P3 |
| Assignee | People | The responsible human or agent identity |
| Iteration | Iteration | Your delivery cadence |
| Pull Request | Text or URL | The implementing PR |

Use **Status** as the source of truth. Labels such as `status:doing` are
searchable mirrors, not a second workflow database.

Recommended views:

1. **Backlog:** Status is Backlog, grouped by Priority.
2. **Ready:** Status is Todo, grouped by Track.
3. **Active:** Status is Doing or Testing, grouped by Assignee.
4. **Delivery:** Status is Done, sorted by Iteration.

## 3. Install labels

The complete declarative label list is `.github/labels.yml`. Apply it with
GitHub CLI after installing `yq`:

```bash
OWNER_REPO="Sergiu1809/Clearpath"
yq -r '.labels[] | [.name, .color, .description] | @tsv' .github/labels.yml |
while IFS=$'\t' read -r name color description; do
  gh label create "$name" --repo "$OWNER_REPO" \
    --color "$color" --description "$description" --force
done
```

If `yq` is unavailable, create the same labels through the repository
**Issues → Labels** page. Do not put tokens in the repository or shell history.

## 4. Configure issue creation

The **Agent task** issue form in `.github/ISSUE_TEMPLATE/agent-task.yml`
requires a goal, context, exact scope, acceptance criteria, validation
commands, dependencies, out-of-scope boundaries, priority, track, and a
working owner.

An agent should create issues with:

- one `type:*` label;
- one `track:*` label;
- one `priority:*` label;
- one `status:*` label, initially `status:backlog`;
- a Project item with Status `Backlog`;
- the responsible GitHub username or service identity as assignee.

Use linked prerequisite issues instead of hiding dependencies in prose.

## 5. Provider-neutral agent contract

Give each AI provider the following adapter contract. The provider may use
different tools, but the result must be identical:

| Operation | Required result |
|---|---|
| `list_ready_work` | Return assigned issues whose Project Status is Todo |
| `create_issue` | Create a fully populated issue from the template |
| `apply_labels` | Keep type, track, priority, and mirrored status labels accurate |
| `assign_issue` | Record the actual working owner |
| `add_issue_to_project` | Add the issue to ClearPath Delivery |
| `set_project_status` | Move the item through the lifecycle |
| `set_project_fields` | Set Track, Priority, Iteration, Assignee, and PR |
| `add_issue_comment` | Record decisions, progress, tests, and blockers |
| `create_branch` | Create a focused branch for the issue |
| `create_pull_request` | Link the PR with `Closes #<issue-number>` |
| `read_checks` | Verify required checks before completion |

This makes the workflow portable across OpenAI, Anthropic, Google, local
models, GitHub Copilot, or custom orchestration: only the adapter changes.

## 6. Agent lifecycle

### Backlog → Todo

An intake agent may create or enrich an issue. Move it to **Todo** only when
the acceptance criteria, validation commands, ownership, track, priority,
dependencies, and scope are complete.

### Todo → Doing

The implementation agent claims only assigned or explicitly delegated issues.
It moves the Project item to **Doing**, changes the mirrored label from
`status:todo` to `status:doing`, and comments with its branch and plan.

### Doing → Testing

The agent implements only the issue scope, follows the relevant track
ownership, and runs the smallest appropriate checks. It then moves the item to
**Testing**, applies `status:testing`, and comments with:

- files changed;
- exact commands executed;
- pass/fail results;
- remaining risks or blocked items.

### Testing → Done

Do not use **Done** when a branch or PR merely exists. The item becomes **Done**
only after the PR is merged and every acceptance criterion is verified. Then
the agent records a final comment, applies `status:done`, closes the issue, and
sets the PR URL and iteration fields.

If a decision or dependency is missing, apply `workflow:blocked`, move the item
back to **Backlog**, explain the blocker, and stop.

## 7. Recommended agent prompt

Use this as the provider-independent system/task instruction:

```text
You are a ClearPath repository agent.

1. Read CLAUDE.md, the issue, and the relevant official documentation.
2. Work only on issues assigned to you or explicitly delegated to you.
3. Verify Project fields: Status, Track, Priority, Assignee, Iteration.
4. Before coding, move the issue to Doing and comment with the branch and plan.
5. Respect track ownership, contract immutability, explicit timeouts, and the
   no-unprompted-commit rule.
6. Implement only the stated scope.
7. Run the exact validation commands from the issue and record their results.
8. Move to Testing only with evidence, then open a linked pull request.
9. Never mark Done or close the issue until the PR is merged and all acceptance
   criteria are verified.
10. If blocked, apply workflow:blocked, explain the missing dependency or
    decision, move the item to Backlog, and stop.
```

## 8. Permissions and approvals

Use a GitHub App or fine-grained token with the minimum permissions required:

- Issues: read/write
- Projects: read/write
- Pull requests: read/write
- Contents: read by default; write only when the agent must push branches
- Checks/actions: read

Keep tokens outside the repository. Require human approval for merging,
closing issues, changing shared contracts or dependencies, modifying agent
instructions, changing workflow permissions, or touching another track's
files.

## 9. ClearPath validation gates

For integration work, follow `doc/3-integration/integration.md` and progressively
disable `CP_STUBS`:

```text
events,audit,render,report
audit,render,report
render,report
report
empty
```

The final acceptance target is in
`doc/3-integration/definition-of-done.md`: local startup, analysis under three
minutes, synchronized video and timestamps, a 0–100 score, independent
shareable results, and an offline demo.

## 10. Manual setup checklist

- [ ] Create the **ClearPath Delivery** Project.
- [ ] Add the fields and values from this guide.
- [ ] Create the four recommended views.
- [ ] Apply `.github/labels.yml`.
- [ ] Enable the Agent task issue form.
- [ ] Configure the selected AI provider with the adapter contract.
- [ ] Give the provider only the required GitHub permissions.
- [ ] Create one test issue, move it through every status, and verify labels,
      assignee, comments, PR URL, and closure.
- [ ] Revoke or rotate any setup token after testing if it was temporary.
