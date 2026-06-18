# CLAUDE.md is Your AI's Operating System — Here's How to Configure It

**Day 10 of building an AI coaching agent in public.**

---

Every developer has a `.gitignore`.

Every developer knows what it does: tell the tool what to ignore.

Nobody reads the docs. Nobody thinks about it. It just works.

**Every AI team needs a `CLAUDE.md`.**

And almost nobody knows how to configure it.

After 9 days building a production coaching agent, the biggest gap I hadn't closed was this one: I was relying on the model to *remember* its rules. I wasn't *engineering* its constraints.

Today I close that gap. This is Domain 3 of the Claude Certified Architect exam — and it's 20% of the test.

---

## What is CLAUDE.md, Really?

Think of it as a compiler directive for Claude's behavior.

Your `.gitignore` tells Git what to skip. Your `CLAUDE.md` tells Claude how to behave — what tools it can use, what it must never do, what format outputs must take, and how to handle edge cases.

The difference between a `CLAUDE.md`-configured agent and one without is the same as the difference between a new employee with an onboarding manual and one who guesses their way through the first week.

Except the stakes are higher. The agent can write to your database.

---

## The Hierarchy: Three Levels, One Resolution Rule

Here's what most people get wrong: `CLAUDE.md` isn't a single file. It's a stack.

```
~/.claude/CLAUDE.md           ← user-level (your global defaults)
    ↓
your-project/CLAUDE.md        ← project-level (this repo's rules)
    ↓
your-project/coaching/CLAUDE.md  ← directory-level (most specific wins)
```

**The rule is simple: most specific wins.**

In my coaching agent, the project-level CLAUDE.md sets `MAX_TOOL_ROUNDS = 8`. But the `coaching/` subdirectory — where student memory is touched — overrides that to `MAX_TOOL_ROUNDS = 3`. Tighter blast radius where it matters most.

The Python starts with `MAX_TOOL_ROUNDS = 8`. But the config overrides it for the coaching context. No code change. Just config.

Here's what the resolution looks like at runtime:

```
[user-level]      max_tool_rounds: 10, style: formal
[project-level]   max_tool_rounds: 8  ← overrides 10
                  escalation_threshold: 0.6
[directory-level] max_tool_rounds: 3  ← overrides 8
                  halt_threshold: 0.4
                  compress_on_compliance_flag: False

RESOLVED: max_tool_rounds = 3 (coaching/ directory wins)
```

The directory with the highest risk gets the tightest constraint. That's not a code change — it's a config change. That's D3.

---

## @import: Modular CLAUDE.md

You can compose CLAUDE.md files the same way you'd import a module:

```markdown
# project-level CLAUDE.md

@import coaching/CLAUDE.md
```

When Claude works in the `coaching/` directory, both files load. The import pulls in context-specific rules without duplicating them in the root file.

This is the same principle as Python's `from module import config`. Modular. Versioned. Reviewable.

---

## .claude/rules/: Conditional Loading by File Type

Here's a feature that solves a real problem: your Python type hint rules shouldn't fire when Claude is editing a Markdown file.

```markdown
---
description: Python standards — applied to .py files only
paths:
  - "**/*.py"
---

# Python Standards

## Type Hints
All function signatures must include type hints.
Return types are mandatory: `def fn(...) -> ReturnType:`
...
```

The `paths:` frontmatter is how you tell Claude: *this rule only matters when you're touching Python*. Your CLAUDE.md doesn't become a 500-line wall of text that gets ignored at 400 tokens in.

Conditional loading. Same principle as webpack loaders. Different context → different rules.

---

## Custom Commands: /coaching-session

Here's a pattern I use every day: custom slash commands.

A command is just a Markdown file in `.claude/commands/`:

```markdown
---
description: Start a new coaching session for a student
argument-hint: <student_name> [topic]
allowed-tools:
  - Read
  - Write
  - Bash
---

# /coaching-session

Start a structured coaching session for $ARGUMENTS.

1. Load student profile from memory
2. Set session context (topic, level, gaps)
3. Run coaching loop with PreToolUse + PostToolUse hooks
4. Save session summary (validated against SessionSummary TypedDict)
```

Invoke it:

```bash
claude "/coaching-session Alice agentic-loops"
```

What makes this powerful isn't the command itself — it's the `allowed-tools` frontmatter.

Every tool I list is a tool Claude can use for this command. Everything else is blocked. Not by the model. Not by a prompt. By the config.

**Blast radius control at the config layer.**

---

## Iterative Refinement: How to Actually Get What You Want

Here's the gap most people have with Claude Code: they write a description, get mediocre output, and then describe it again — more words, more emphasis, same result.

The better approach has four techniques, and they compound.

**1. Concrete I/O examples beat prose descriptions.**

Don't describe what you want. Show it.

```markdown
# ❌ Vague description
Generate a session summary for the student.

# ✅ Concrete I/O example
Input:
  student: Alice
  topic: agentic loops
  duration: 45min
  issues_flagged: ["never_closes_loop", "no_stop_condition"]

Expected output:
{
  "student": "Alice",
  "topic": "agentic loops",
  "mastery_score": 0.62,
  "gaps": ["loop termination", "stop_reason handling"],
  "next_session_focus": "Day 3 material — stop_reason patterns"
}
```

When Claude produces inconsistent summaries from prose, a single concrete example fixes it. Every field. Every type. No ambiguity.

**2. Test-driven iteration.**

Write the test before you write the prompt. Share failures.

```python
# Write this first
def test_session_summary():
    result = generate_session_summary("Alice", "agentic loops")
    assert "mastery_score" in result
    assert 0.0 <= result["mastery_score"] <= 1.0
    assert isinstance(result["gaps"], list)
    assert len(result["gaps"]) > 0  # never empty

# Then share the failure output with Claude:
# "This test fails with: KeyError 'mastery_score'. Fix the schema."
```

The test failure is more precise than any description you could write. Claude gets exact signal on what broke, not a general complaint.

**3. The interview pattern.**

In unfamiliar domains, have Claude ask questions before implementing.

```bash
claude "Before writing the CLAUDE.md for my coaching agent,
ask me 5 questions to understand the safety constraints
and tool requirements. Do not implement yet."
```

This surfaces assumptions before they become bugs. The questions Claude asks reveal what it doesn't know — and what you forgot to specify.

**4. Sequential vs. batch issue fixing.**

When you have multiple problems:

```
Interacting problems (fixing A changes B)?
→ Single message with all issues listed

Independent problems (A and B don't touch each other)?
→ Sequential: fix A, verify, then fix B
```

Sending interacting fixes as separate messages causes Claude to fix A, then break A while fixing B, then re-introduce the original A problem. Name them in one shot.

---

## Plan Mode vs. Direct Execution: The Decision Tree

Domain 3 also covers one of the most-missed exam concepts: when to use `--plan` vs just running.

The decision tree is simpler than people make it:

```
Single file + reversible + unambiguous spec?
→ DIRECT EXECUTION
  claude "rename getCwd to getCurrentWorkingDirectory in utils.py"

Multi-file OR irreversible OR ambiguous spec?
→ PLAN MODE
  claude --plan "refactor auth module to use JWT"
  claude --plan "delete test fixtures older than 30 days"
  claude --plan "improve the API"  ← surface what "improve" means first
```

One exam trap: **`-p` is NOT `--plan`.**

- `--plan` = show me the plan before executing (interactive, human reviews)
- `-p` = non-interactive pipe mode (CI/CD, no human prompts)

These are orthogonal. You can use both:

```bash
# CI/CD: non-interactive, shows plan as JSON, exits
claude -p --plan "refactor auth module" --output-format json
```

---

## CI/CD: The Three-Stage Pattern

In CI/CD, there's no human to review the plan. You need a different safety layer.

```yaml
# .github/workflows/claude-review.yml

# STAGE 1: Generate
- name: Run Claude review
  run: |
    claude -p "Review this PR for agentic loop correctness,
    error handling, and schema validation. Output as JSON:
    {issues: [], severity: 'low|medium|high', approved: bool}" \
    --output-format json \
    --context "$(git diff origin/main...HEAD)" \
    > review_output.json

# STAGE 2: Verify (the circuit breaker)
- name: Validate review output
  run: |
    python3 -c "
    import json, sys
    data = json.load(open('review_output.json'))
    required = ['issues', 'severity', 'approved']
    missing = [k for k in required if k not in data]
    if missing:
        sys.exit(1)  # fail the pipeline, don't proceed
    print(f'Severity: {data[\"severity\"]}. Approved: {data[\"approved\"]}')
    "

# STAGE 3: Act (only after verification)
- name: Post review comment
  # ... post the verified JSON as a PR comment
```

Three stages. Generate → Verify → Act.

The verification loop (Stage 2) is the key. If Stage 1 produces malformed output and Stage 3 acts on it directly, downstream is garbage. The circuit breaker catches what the generator normalized away.

**This is Cascading Failure prevention. It's not glamorous. It's engineering.**

---

## The CLAUDE.md + Hooks Double Lock

Day 9 showed that PostToolUse hooks make compression deterministic — you can't forget to run it.

CLAUDE.md and hooks solve different layers of the same problem:

```
CLAUDE.md  → design-time spec precision (before the agent runs)
Hooks      → runtime enforcement     (while the agent runs)
```

Together:

```markdown
# CLAUDE.md
"Never run git push without user confirmation"
"Always use plan mode for multi-file refactors"
"MAX_TOOL_ROUNDS = 8 (3 in coaching/)"
```

```python
# hooks
@post_tool_use
def enforce_compression(tool_result):
    if tool_result.tool == "update_student_note":
        if not tool_result.compliance_flag:
            compress_session()  # deterministic — not a suggestion
```

CLAUDE.md is the spec. The hook enforces it. Neither alone is as safe as both together.

---

## What the Exam Tests (D3 — 20%)

After building all of this, here are the D3 exam traps that are worth naming explicitly:

**Trap 1: "Directory-level overrides user-level"**  
✅ True. Hierarchy: user < project < directory. Most specific wins.

**Trap 2: "-p enables plan mode in CI/CD"**  
❌ False. `-p` = non-interactive. `--plan` = plan mode. Different flags, different purposes.

**Trap 3: "Skills always inherit the project CLAUDE.md"**  
❌ False. Skills with `context: fork` get an isolated copy of context at invocation time. Use `fork` when the skill touches sensitive data (student files, credentials).

**Trap 4: "CLAUDE.md rules are prompts"**  
❌ False. CLAUDE.md rules are loaded into the system prompt, but they behave differently from inline prompts — they persist across sessions, they're version-controlled, and they fire for every tool use in the session. They're config, not conversation.

---

## What I Built Today

```
day10_claude_config_demo/
├── CLAUDE.md                         ← project-level (MAX_TOOL_ROUNDS=8, @import)
├── coaching/
│   └── CLAUDE.md                     ← directory-level (MAX_TOOL_ROUNDS=3, halt threshold)
└── .claude/
    ├── rules/
    │   └── python.md                 ← paths: ["**/*.py"] (conditional loading)
    ├── commands/
    │   ├── coaching-session.md       ← /coaching-session command
    │   └── generate-report.md        ← /generate-report command
    └── skills/
        └── coaching-mastery.md       ← context: fork (isolated execution)

day10_claude_config_demo.py           ← runs all 4 demos
day10_plan_mode_demo.md               ← decision tree + CI/CD 3-stage pattern
```

Run it:

```bash
python day10_claude_config_demo.py --demo all
```

---

## What Changes After You Configure This

Before CLAUDE.md: your agent's behavior is a function of the prompt in this session.

After CLAUDE.md: your agent's behavior is a function of version-controlled config that your whole team can review, modify, and audit.

The difference between "Claude should be careful with student data" and:

```markdown
## coaching/CLAUDE.md
MAX_MEMORY_WRITE_ROUNDS = 3
compress_on_compliance_flag: False  ← log verbatim if compliance flag set
halt_threshold: 0.4                 ← immediate escalation, not just flagging
```

The first is a hope. The second is a spec.

**Every developer has a `.gitignore`. Every AI team needs a `CLAUDE.md`.**

---

Day 11: how to cut your AI costs by 90% — the Batch API, TypedDict schema validation, and why multi-model routing is the most underused optimization in production agents.

Comment CONFIG or BATCH below for the article link.

#AIEngineering #Claude #ClaudeCode #AgentDesign #OmegaFounders #BuildInPublic #AIArchitect
