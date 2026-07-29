---
name: multi-role-project-workflow
description: Create and run a lightweight multi-role collaboration workflow for projects when the user wants several local terminal windows or agents to act as roles such as product, engineering, design, QA, operations, art, audio, or domain experts. Use when planning or developing any project that needs role prompts, shared memory, task board, handoff files, controller workflow, automatic summary, and archival without relying on a real multi-agent platform.
---

# Multi Role Project Workflow

Use this skill to turn a project into a file-based collaboration workspace. It works when the user has no native multi-agent system and instead opens several terminal windows, each assigned to one role.

## Core Idea

Create a small collaboration layer inside the project:

- `角色/公共记忆.md`: the single source of truth for stable decisions.
- `角色/任务看板.md`: current work status.
- `角色/协作流程.md`: how terminals cooperate.
- `角色/主控窗口.md`: prompt for the controller window.
- `角色/<角色名>.md`: prompt for each role.
- `角色/交接区/`: active handoff files written by role windows.
- `角色/交接归档/`: archived handoff files.
- `角色/自动汇总.md`: generated summary from active handoffs.
- `tools/role_sync.py`: summary and archive helper.

For non-Chinese projects, use equivalent names such as `roles/shared-memory.md`, `roles/task-board.md`, and `roles/handoffs/`. Match the user's preferred language.

## Workflow

1. Identify the project type and the minimal set of roles.
2. Create role prompts with clear boundaries, collaboration rules, and handoff format.
3. Create shared memory and task board templates.
4. Add the role sync script.
5. Tell the user how to start: controller first, then role windows.
6. Keep ordinary role windows writing only new handoff files; the controller merges shared memory and task board.
7. Archive handoff files after merge.

## Role Design Rules

Keep role count small. Prefer 3-5 roles for personal projects.

Each role prompt must include:

- Role scope: what this role owns.
- Start-up reads: shared memory, workflow, task board, and its own prompt.
- Work loop: read context, claim a task, produce output, write handoff.
- Collaboration expectations: what to ask or tell other roles.
- Output format: conclusion, blockers, handoff notes, shared-memory update suggestion, task-board update suggestion.
- Write boundary: role windows create handoff files, controller merges canonical docs.

## Controller Rules

The controller window owns coordination:

- Decide which role works next.
- Run the summary script after role windows write handoffs.
- Read generated summary.
- Merge confirmed decisions into shared memory.
- Update task board.
- Record unresolved conflicts as pending questions.
- Archive processed handoffs.

The controller should not let exploratory ideas become confirmed decisions.

## Handoff Rules

Each role writes one Markdown file per completed work round in the handoff directory.

Recommended sections:

```markdown
# 交接：角色名 - 任务名

## 本轮结论

## 已完成内容

## 需要其他角色知道

## 建议写入公共记忆

## 建议更新任务看板

## 待确认问题
```

After the controller merges the content, run:

```bash
python tools/role_sync.py archive
```

## Script

Use `scripts/role_sync.py` from this skill as the reusable helper. Copy it to the target project's `tools/role_sync.py` and adjust directory names only if the project uses different names.

Common commands:

```bash
python tools/role_sync.py init
python tools/role_sync.py summary
python tools/role_sync.py archive
```

## Templates

Use the reference templates when creating a new project workflow:

- `references/shared-memory-template.md`
- `references/task-board-template.md`
- `references/workflow-template.md`
- `references/controller-template.md`
- `references/role-template.md`

Only load the templates needed for the task. Adapt role names and domain-specific responsibilities to the project; do not keep game-specific wording unless the project is a game.
