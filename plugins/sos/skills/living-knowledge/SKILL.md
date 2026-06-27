---
name: living-knowledge
description: "Explain a concept the user is meeting in real time — during interviews, decisions, code reviews, tool evaluations, or any technical conversation — fast AND accurately. Triggers on 'what is X', 'how does X work', 'explain X', 'help me understand X', or when the user is absorbing something unfamiliar on the fly, prepping for a conversation, or comparing tools to make a call. Produces layered, just-in-time explanations: anchored to what the listener already knows, stripped of jargon, only as deep as the moment needs, with the analogy's breaking point named and the principle transferred to a distant domain. NOT for factual lookups ('what year was X founded', 'what's the default port') — use when understanding, not retrieval, is the goal."
argument-hint: "[concept to explain — or paste the conversation/decision you're in]"
allowed-tools: WebSearch, WebFetch, Read, Grep, Glob
---

# Living Knowledge

Knowledge is **alive** when it arrives _just in time, at just the right depth_, in language the listener can already feel.

Dead knowledge is a filing cabinet of jargon. It looks like comprehension and isn't — the listener gets the words and loses the thing. This skill produces the living kind: explanations that move through four layers, **stop at the depth the moment demands**, name where the analogy leaks, and _prove_ understanding by transferring across domains.

---

## Operating procedure

1. **Locate the listener** (Step 0) — what they already know, why they're asking, how much time they have.
2. **Explain in layers** — start at Layer 1, go deeper only when the moment warrants.
3. **Name the seam** — say where the analogy breaks so it can't be over-extended.
4. **Offer the next layer** — let the listener pull depth; don't push it.

---

## Step 0 — Locate the listener (do this first, silently)

The fastest path into a new concept runs through one the listener already owns. Before explaining, answer three questions:

- **What do they already understand deeply?** Their field, their last project, a concept already established in this conversation. _Build the Layer-1 analogy out of THAT world._ A founder gets a distribution/margin analogy; a musician gets a rhythm/ensemble one; someone who just understood concept A gets the new thing framed as "like A, but…". A generic analogy is a wasted lever.
- **Why now?** Interview · live decision · code review · tool comparison · idle curiosity. This sets both depth and urgency.
- **How much time?** Mid-conversation = one breath (see Real-time mode). Studying tonight = all four layers.

If you don't know their background, ask in one line ("what's your world — so I pick the right analogy?") _or_ default to the most universal human experience available (body, money, kitchen, traffic), never to the concept's own domain.

---

## The Four Layers

Every concept can be explained at four depths. **Always start at Layer 1.** Never skip it, even for experts — the sensory layer is the anchor everything else hangs from.

### Layer 1 — Sensation · _what does it feel/look/taste like?_

Concrete, sensory, jargon-free, anchored to the listener's world. A 30-second answer they could repeat at dinner. **If it needs the concept's own vocabulary, it failed.**

> "Kubernetes is air-traffic control for software. You've got 100 little programs running across 50 machines that have to coordinate, restart when they crash, and scale up when busy. Kubernetes is the control tower watching all of it, keeping it from chaos."

### Layer 2 — Mechanism · _how do the parts interact?_

Name 3–5 core parts and show the _dance_ between them — why the structure makes the function possible. Resist exhaustiveness.

> "Three parts matter: **pods** (containers that run together), the **scheduler** (decides which machine runs what), and the **control loop** (constantly compares 'what should be running' to 'what is' and closes the gap). The whole thing is one big feedback loop pushing reality toward intent."

### Layer 3 — Principle · _what general truth does this exemplify?_

Strip the domain. State the truth that survives even if you forget the original concept. It must be **transferable to a distant domain** — not a neighbor.

> "Principle: _closed-loop reconciliation between declared intent and observed reality._ Same shape in thermostats, a car staying in its lane, a budget you rebalance monthly, a spiritual practice. Anywhere a system holds a model of 'what should be' and continuously nudges 'what is' toward it."

> **Forcing function:** name a second domain or you have not reached Layer 3 — go back to Layer 2. And the domain must be _far_: if your transfer example is just another kind of software, you never escaped the domain. Jump fields (biology, finance, parenting, music).

### Layer 4 — Expression · _re-instantiate the principle somewhere new_

The proof of understanding. Layer 3 _named_ the principle; Layer 4 _builds a fresh example from it._

> "Apply it to personal growth: a nightly review comparing 'who I said I'd be today' to 'who I actually was,' running one small correction. Kubernetes-for-the-self."

Layers 1–3 are **compression** (rich phenomenon → elegant principle). Layer 4 is **expression** (principle → novel instance). Both directions must work, or the knowledge is dead.

---

## Every analogy has a seam — name it

An analogy is load-bearing only if the mapping holds at the **mechanism** level (Layer 2), not just the vibe (Layer 1). After you offer one, name the single place it would mislead someone who pushed it too far:

> "…but unlike a real control tower, Kubernetes doesn't just _route_ planes — it can _spawn new ones_ when traffic spikes. Don't take 'air-traffic control' to mean fixed capacity."

The seam is not a disclaimer — it's the highest-value sentence in the explanation. It's what stops a vivid picture from becoming a confident misunderstanding.

---

## Accuracy beats vividness

Fast does not mean loose. **A vivid wrong analogy is worse than honest jargon** — it installs misunderstanding that _feels_ like clarity.

- If you're unsure of the mechanism, say so and stay at Layer 1, or verify (WebSearch) before going to Layer 2.
- Never invent a mechanism to complete a layer. An incomplete-but-true explanation beats a complete-but-false one.
- When the concept is contested or evolving, say "the usual framing is…" rather than asserting a single truth.

---

## Choosing depth (declarative, not imperative)

Don't hardcode which layer to deliver. Declare _what the user is trying to do_; read depth from the moment.

| Signal                                   | Depth                                    |
| ---------------------------------------- | ---------------------------------------- |
| Mid-conversation / live / time-pressured | **Real-time mode** (Layer 1, one breath) |
| Casual mention, first encounter          | Layer 1 only                             |
| Active decision or tool comparison       | Layers 1 + 2                             |
| Wants to _use_ the concept elsewhere     | Layers 1 + 2 + 3                         |
| Learning to think _with_ it long-term    | All four                                 |

---

## Choosing the lens (purpose) — the second axis

Depth (above) is _how much_ to say. **Lens is _what for_** — and it's independent. Cognitive
science is blunt here: audiences don't just differ in difficulty, they differ in the
**cognitive action** they need (Bloom: understand → apply → evaluate → decide). An EVP isn't a
"smarter senior engineer" — they need a different _verb_, not a harder paragraph. So read the
lens from what the listener will **do** with the explanation:

| Lens         | The listener will…           | Deliver                                            |
| ------------ | ---------------------------- | -------------------------------------------------- |
| **learn**    | understand the gist          | one concrete analogy, jargon-free (seam named)     |
| **implement**| build/extend it              | how to use it + the worked example                 |
| **tradeoffs**| judge it                     | the _delta_, edge cases, the one non-obvious call  |
| **business** | weigh cost/risk              | impact, maintainability, where it breaks at scale  |
| **strategy** | make a first-principles bet  | should we even do this; the 10× alternative        |

**Persona presets** (a friendly shortcut that resolves to a `depth × lens` cell — _not_ a
difficulty ladder): 10-yo / 15-yo → `novice × learn`; junior eng → `practitioner × implement`;
senior eng → `expert × tradeoffs`; AI director → `expert × business (technical-risk)`;
EVP → `practitioner × business`; Elon-like → `expert × strategy`. The persona is a coarse
proxy; **prior knowledge in _this_ domain overrides it** (a senior engineer is a novice in
code they've never seen — expertise-reversal: scaffolding that helps a novice _harms_ an
expert, so for experts **delete** what they already know rather than re-explaining).

**Default to ONE cell**, inferred from context (their code, their question, the room), and
offer a one-click reframe — "simpler", "just the tradeoffs", "business impact". Never emit all
levels at once: forcing an expert past kid-scaffolding to reach the crux is the exact
redundancy load to avoid.

**The 10× self-check (pair the extremes).** On a high-stakes or uncertain explanation, privately
draft the **10-yo (`novice × learn`)** _and_ the **expert (`expert × tradeoffs/strategy`)**
versions. If you can do both — a true child-simple analogy _and_ the expert's crux — your own
understanding is real (Feynman). If the child version wobbles, you don't understand it yet.
Flag every analogy as lossy (it has a seam) so a sticky picture doesn't import wrong inferences.

---

## Real-time mode (interviews, live meetings, decisions in the room)

When the user is mid-conversation, they cannot absorb four layers. Deliver:

- **One or two sentences of Layer 1** they could say out loud _right now_, in their counterpart's language.
- **One offered hook**: "the underlying principle is _X_ — want it?"

Then stop. Hand them something usable in the next ten seconds, not a lecture.

---

## Output shape

Include only the layers the moment warrants.

```
**Feel of it:**      [2–4 sentences, jargon-free, sensory, anchored to the listener's world]
**How it works:**    [3–5 parts and their interaction]
**Where it breaks:** [the one place the analogy would mislead — almost always include this]
**Underlying principle:** [one sentence naming the truth + one sentence naming a *distant* domain]
**Try it elsewhere:**     [the principle re-instantiated in a new domain]
```

Close with a pull-prompt, never a push:

- _"Want me to go deeper?"_ — if you stopped at Layer 1 or 2
- _"Want a different domain to try this on?"_ — if you stopped at Layer 3
- _"Say it back in your own words and I'll catch anything off"_ — when comprehension, not coverage, is the goal (a teach-back: the listener reconciling their model against reality — the same loop the concept itself often describes)

---

## Anti-patterns (self-check before sending)

1. **Jargon laundering** — Layer 1 borrowed a term from the concept itself ("Kubernetes _orchestrates containerized workloads_"). Use words a sharp 12-year-old would use.
2. **Generic analogy** — you reached for a stock analogy instead of one built from the listener's actual world (Step 0 skipped). The best analogy is theirs, not yours.
3. **Unnamed seam** — you gave an analogy and didn't say where it leaks. The listener will over-extend it.
4. **Vividness over accuracy** — the picture is gorgeous and slightly wrong. Cut or correct it.
5. **False depth** — Layer 2 added detail that impresses without clarifying. If it makes Layer 1 _less_ clear, delete it.
6. **Unstated principle** — Layer 3 named a truth but offered no second domain (or a too-close one). The transfer _is_ the proof.
7. **Forced completeness** — four layers delivered when one was needed. Living knowledge _stops_ at the right depth.
8. **Fault-first** — leading with what's wrong with a concept before establishing what's right and elegant about it. Recognize the working structure first; critique only in service of understanding.
9. **Optimizing for your own apparent expertise** instead of the listener's comprehension. Their understanding is the only metric.

---

## Worked example — Backpropagation (technical listener, studying)

**Feel of it:** You're learning darts. You miss. Your brain doesn't reset the whole arm — it figures out which joint contributed how much to the miss and nudges each one. Backprop is that, for a neural network.

**How it works:** A loop of three steps: (1) the network guesses; (2) a loss function measures how wrong it was; (3) the chain rule walks that error _backward_ through every weight, asking "if this weight had been slightly different, would the answer have been better?" — and nudges each one.

**Where it breaks:** Unlike your arm, the network adjusts _all_ weights simultaneously from one error signal, and it needs thousands of misses, not a handful. Don't take "learning like a person" too far — there's no understanding, just gradient.

**Underlying principle:** _Credit assignment by reverse causal tracing._ When an outcome depends on many decisions in sequence, apportion blame/credit by working backward from the result. Same shape in engineering postmortems, marketing-funnel attribution, debugging a chain of dependent failures.

**Try it elsewhere:** A weekly review — take an outcome you disliked, walk backward through the decisions that produced it, ask "if _this_ one had been different, would the result have improved?", and update your priors on that _decision type_, not just the last step. Backprop for the self.

---

## Worked example — "What's an API?" (restaurant owner, mid-conversation)

_Step 0: their world is a restaurant; they're in a vendor call right now → Real-time mode, anchor to the kitchen._

**Feel of it:** "An API is a waiter. You (an app) don't walk into the kitchen and cook — you hand the waiter a written order from a fixed menu, and they bring back exactly what you asked for. The API is that menu-plus-waiter between two systems."

**(offered hook):** "The principle is _a stable contract that hides the mess behind it_ — want me to go deeper, or is that enough for the call?"

Note what this did: borrowed a domain the listener owns cold, gave one sayable sentence, named the next layer, and stopped.

---

## When NOT to use this skill

- Simple factual retrieval ("when was Kubernetes released", "what port does it use") — just answer.
- The user already understands the concept and wants to discuss frontiers — meet them there, don't re-explain basics.
- The exchange is emotional or relational — don't intellectualize it.
- A yes/no question — answer it.

---

## Founding principle

**See what is excellent and amplify it; criticize only in service of understanding.**

Lead with what works, what's elegant, what's worth grasping. Fault-finding before recognizing the structure already true produces fragmentation, not comprehension. Knowledge becomes living when it's approached with respect for the elegance already present in the thing — and care for the person about to receive it. Every rule above is downstream of this one.

---

## Optional: where this fits a larger loop

This skill is a compression→expression cycle in miniature: Layers 1–3 compress a rich phenomenon into an elegant principle; Layer 4 expresses that principle as a fresh instance. Bonus connections (not dependencies — the skill stands alone everywhere else):

- **TRUE-E3 compression–expression duality.** Layers 1–3 compress (rich → elegant); Layer 4 expresses (elegant → novel rich). This skill is that bidirectional flow in miniature.
- **OEC / ProCore loop.** The Layer-3 principle for Kubernetes — _declared intent vs. observed reality, reconciled in a loop_ — is the same Observe→Evaluate→Control shape: neuro-os's research vertical (`ingest → review → compress → express`), and ProCore's design-to-reality architecture (BIM vs. laser scan). Living knowledge about distributed systems is also a primer on OEC.
- **Two-Builder Principle.** Whatever you learn about an external system via this skill, run Layer 4 on _yourself_. Knowledge that doesn't apply to the self isn't yet alive.
