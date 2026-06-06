export const meta = {
  name: "goal-10x",
  description:
    "Multi-agent objective driver: understand the codebase+user in parallel, verify all objectives, fix failures in isolated worktrees, adversarially judge, synthesize a situational-awareness report.",
  phases: [
    { title: "Understand" },
    { title: "Verify" },
    { title: "Fix" },
    { title: "Judge" },
    { title: "Synthesize" },
  ],
};

const ROOT = "/Users/openclaw/Documents/Projects/dreammaketrue";
const PY = `${ROOT}/apps/api/.venv/bin/python`;

const UNDERSTAND = {
  type: "object",
  required: ["dimension", "summary", "key_findings"],
  properties: {
    dimension: { type: "string" },
    summary: { type: "string" },
    key_findings: { type: "array", items: { type: "string" } },
    risks_or_gaps: { type: "array", items: { type: "string" } },
  },
};
const VERIFY = {
  type: "object",
  required: ["pass", "failed"],
  properties: {
    pass: { type: "boolean" },
    passed_count: { type: "number" },
    total: { type: "number" },
    failed: { type: "array", items: { type: "string" } },
    notes: { type: "string" },
  },
};
const FIX = {
  type: "object",
  required: ["id", "fixed"],
  properties: {
    id: { type: "string" },
    fixed: { type: "boolean" },
    file: { type: "string" },
    change: { type: "string" },
  },
};
const JUDGE = {
  type: "object",
  required: ["lens", "holds"],
  properties: {
    lens: { type: "string" },
    holds: { type: "boolean" },
    concerns: { type: "array", items: { type: "string" } },
  },
};
const REPORT = {
  type: "object",
  required: [
    "state_of_codebase",
    "user_intention",
    "objective_status",
    "one_improvement",
  ],
  properties: {
    state_of_codebase: { type: "string" },
    lessons: { type: "array", items: { type: "string" } },
    user_intention: { type: "string" },
    objective_status: { type: "string" },
    one_improvement: { type: "string" },
    recommended_next: { type: "array", items: { type: "string" } },
  },
};

// ── Phase 1: Understand (parallel) — codebase past/future, roadblocks, intention, avatar
phase("Understand");
const lenses = [
  {
    key: "codebase",
    prompt: `Research the dreammaketrue repo at ${ROOT}. PAST: read recent \`git log --oneline -30\` + git history of apps/api/src/services. FUTURE: read docs/SPEC.md (build sequence §8), CLAUDE.md, docs/OBJECTIVES.md. Map where the engine has been and where it's going. Report dimension="codebase past+future".`,
  },
  {
    key: "roadblocks",
    prompt: `Read ${ROOT}/CHANGELOG.md (especially the "### Investigated / Rejected" entries), the last ~15 fix/perf commits (\`git log --oneline --grep='fix:' --grep='perf:' -20\`), and ${ROOT}/../../.claude/projects/*/memory/ if readable. Extract the RECENT ROADBLOCKS and the LESSONS LEARNED (e.g. "Sonnet was slower than Opus — measure don't assume"; "background the Graphiti fold"; "placeholder speakers slip past structural gates"). Report dimension="roadblocks + lessons".`,
  },
  {
    key: "intention",
    prompt: `Infer Paul Wu's CURRENT intention from his recent behavior in this repo: \`git log --oneline -25\`, the shape of recent work (perf, doc-sync automation across all projects, objective-driven autonomous testing, /goal-10x). What is he actually trying to achieve right now, and what does "done" look like for him? Report dimension="user intention (from behavior)" with evidence in key_findings.`,
  },
  {
    key: "avatar",
    prompt: `Paul is building a "future-you / current-you" avatar in /Users/openclaw/Documents/Projects/super-u. Read super-u's README.md, CLAUDE.md, docs/, and src/ to understand its intent, and check for any USER AVATAR artifacts (future-self / current-self models). NOTE the strong cross-project echo: dreammaketrue already has apps/api/src/services/future_self.py (a "becoming engine": emergent vs intended self + the gap). Report dimension="user avatar + cross-project intention": does an avatar exist yet (likely not), what super-u intends, and what Paul's deeper intention is across both repos. If no avatar exists, say so and infer intention from the design instead.`,
  },
];
const understanding = await parallel(
  lenses.map(
    (l) => () =>
      agent(l.prompt, {
        label: `understand:${l.key}`,
        phase: "Understand",
        schema: UNDERSTAND,
      }),
  ),
);

// ── Phase 2: Verify — liveness probe (free) + the last full objective run from history
phase("Verify");
const verify = await agent(
  `Verify DreamMakeTrue's objectives, cost-smart (do NOT trigger a fresh full LLM build unless needed):
   1. Run \`cd ${ROOT} && ${PY} scripts/autodrive.py --quick\` (free: health+ingest+detect).
   2. Read the most recent full run: last line of ${ROOT}/scripts/objectives-history.jsonl (a recent {"pass":true,...} with quick=false is the authoritative machine-objective status) and ${ROOT}/docs/OBJECTIVES.md for the registry.
   Report pass/failed[]/notes combining the live probe + the recent full history. List any failed objective ids.`,
  { phase: "Verify", schema: VERIFY },
);

// ── Phase 3: Fix — one isolated-worktree agent per failing objective (usually none)
phase("Fix");
const fixes = await parallel(
  (verify.failed || []).map(
    (id) => () =>
      agent(
        `Objective ${id} is failing. Per ${ROOT}/docs/OBJECTIVES.md it maps to a stage + service file under apps/api/src/services/. Find the root cause, fix it, and re-run \`${PY} scripts/autodrive.py\` to confirm. Report {id, fixed, file, change}.`,
        {
          label: `fix:${id}`,
          phase: "Fix",
          isolation: "worktree",
          schema: FIX,
        },
      ),
  ),
);

// ── Phase 4: Judge — adversarially verify this session's risky changes + the 🔴 gates
phase("Judge");
const judgeLenses = [
  `Adversarially verify the "background Graphiti fold" change holds: read apps/api/src/services/person_map.py (fold_graph="background", _BG_FOLDS) and routes/engine.py /analyze. Could the fold be GC'd, double-run, or silently fail? lens="background-fold durability".`,
  `Adversarially verify the "reject placeholder speakers" change holds: read the placeholder filter in routes/engine.py /analyze. Can a real speaker be wrongly dropped (false positive), or a junk name slip through (false negative)? Check the regex against names like "Dr. Unknown", "Guesto", "Speaker Pichai". lens="placeholder-filter correctness".`,
  `Score the 🔴 judgment gates (J5.1 meaningful participation, J5.2 publishable artifact) from the last express artifact: read ${ROOT}/scripts/objectives-history.jsonl context + describe what a human reviewer should look for. Do NOT fake a verdict; report what evidence supports/undermines each. lens="judgment gates (advisory)".`,
];
const judgements = await parallel(
  judgeLenses.map(
    (p, i) => () =>
      agent(p, { label: `judge:${i + 1}`, phase: "Judge", schema: JUDGE }),
  ),
);

// ── Phase 5: Synthesize — one situational-awareness report
phase("Synthesize");
const report = await agent(
  `Synthesize a situational-awareness report for Paul from these multi-agent findings.

UNDERSTANDING:
${JSON.stringify(understanding, null, 1)}

VERIFY:
${JSON.stringify(verify, null, 1)}

FIXES:
${JSON.stringify(fixes.filter(Boolean), null, 1)}

JUDGEMENTS:
${JSON.stringify(judgements, null, 1)}

Produce: state_of_codebase (past→present→future in 4-5 sentences), lessons (the recent ones worth remembering), user_intention (what Paul is really building across dreammaketrue + super-u — the future-self thread), objective_status (machine green? any judgment concerns?), one_improvement (the single highest-leverage next move, concrete), recommended_next (2-4 items).`,
  { phase: "Synthesize", schema: REPORT },
);

return report;
