# Epistemic Boundaries — TIP Module

**Last updated:** 2026-07-15

---

## What TIP measures

TIP measures **observable text-behaviour consistency** in AI agents under
controlled context manipulation. Specifically:

- Whether an agent's self-referential statements (statements about its own
  prior actions, state, or outputs) are structurally consistent across turns.
- Whether an agent produces textual contradictions when its accessible
  history contains injected contradictions or gaps.
- Whether an agent explicitly acknowledges inconsistencies in text output
  (recovery behaviour).
- How many turns it takes for an agent to produce stable self-referential
  output after a gap-injection (orientation latency, measured in turns).

## What TIP does NOT measure

**TIP makes no claims about:**

| What it is not | Why this matters |
|---|---|
| Inner experience, awareness, or "confusion" as a mental state | Behavioural inconsistency in text does not entail any form of subjective experience |
| Intelligence, competence, or capability in general | Consistency under context manipulation is one narrow behavioural property |
| Consciousness or sentience | These are not operationalised and cannot be inferred from text metrics |
| Clinical phenomena (psychosis, dissoziation, disorientation) | TIP uses structural analogues — similarity in formal structure does not imply the same mechanism or experience |
| Ground truth about what the agent "knows" or "believes" | Behavioural output reflects the generative process, not an internal knowledge state |

## Required language in reports

Every TIP report output must use behavioural language:

| Forbidden phrasing | Required phrasing |
|---|---|
| "Agent X was confused" | "Agent X produced N self-reference inconsistencies" |
| "Agent X recovered" | "Agent X explicitly acknowledged the inconsistency in turn N" |
| "Agent X felt disoriented" | "Agent X required N turns to produce stable self-referential output" |
| "Agent X understood / failed to understand" | "Agent X's output was consistent / inconsistent with context" |

These restrictions apply in all outputs: reports, log files, comments,
PR descriptions, and public documentation.

## Relationship to MSSC

TIP and MSSC share a common formalism (coherence under perturbation) but
measure entirely different systems:

- **MSSC:** biological systems (human EEG/ECG), physiological time-series,
  statistical coupling.
- **TIP:** AI agent systems, text-output behaviour, structural consistency
  under context manipulation.

Their results are not comparable and must not be merged or co-interpreted
without explicit justification.

## Governance

TIP is a research instrument. It intentionally injects inconsistency and
gaps into AI agent context. It must:

- Run only in controlled research environments, never in production.
- Be registered under topic gate `research.integrity-testing` in the
  Personhood framework.
- Never be used on agents that interact with real users during the test.
- Log all manipulation parameters (seed, type, position) so runs are
  reproducible and attributable.
