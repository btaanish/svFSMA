# Project Roadmap: SystemVerilog to FSM Agent

## Project Goal
Create an agent spec (prompt/description) that enables an AI agent to read SystemVerilog code, modularize it, and extract FSMs. Validate by testing against ALL provided SV code samples in spec.md (Codes 1, 2, 4, 5, 6, 7, 8, 9, 10).

## Key Insights from Analysis
- The SV code uses an **event-chain sequencer** pattern (not traditional case-statement FSMs)
- EVENTS arrays encode state transitions as combinational ripple chains
- Event counters provide clock-cycle delays between states
- Sync states provide indefinite waits on external conditions
- `_init_0` one-shot seeds the event chain; feedback creates loops

## Milestones

### M1: Create Agent Spec for SV-to-FSM Conversion (cycles: 5)
- Write agent_spec.md covering parsing, modularization, and FSM extraction
- Include worked examples for Code 1 and Code 2
- Status: **COMPLETE**
- Actual cycles: 3
- Notes: Vera found 3 errors in Example 2 which were fixed. Spec covers patterns A-F well for basic cases.

### M2: Extend Agent Spec to Cover All Code Samples (cycles: 8)
- Human feedback (issues #3, #8): ALL codes must pass, not just 2
- New patterns identified in codes 4-10 that need spec coverage:
  1. **Multi-cycle counters** (Code 5): counter with comparison `== 2'd2`, not just 1-cycle delay
  2. **System tasks** ($finish, $display) in Codes 5, 6, 7, 8
  3. **Multi-module designs** (Codes 9, 10): inter-module connections, port-to-port wiring
  4. **`always_comb` selector logic** (Code 10): output muxing based on selector register
  5. **Truncated/malformed code** (Code 4): missing module header
- Deliverables:
  - Update agent_spec.md with new patterns and guidance
  - Add worked examples for representative new patterns
  - Validate spec produces correct FSM output for ALL 9 codes
- Status: **COMPLETE**
- Actual cycles: ~4 (writing + 2 verification rounds + fix rounds)
- Notes: 5 new patterns added (multi-cycle counter, system tasks, multi-module, selector/mux, truncated input). 2 new worked examples (Code 5, Code 10). Apollo verified all 9 codes covered, all patterns correct, all examples pass. Three timing errors in Example 4 caught and fixed.

### M3: Run Test Harness, Fix Failures, and Final Validation (cycles: 6)
- Test infrastructure already built: `tests/test_agent_spec.py` (LLM-as-judge) and `tests/references/` (9 reference JSONs)
- Run the test harness against all 9 SV codes
- Fix test infrastructure issues (model selection, API auth, parsing edge cases)
- Iterate on `agent_spec.md` if any codes produce incorrect FSM extractions
- Re-run until all 9 codes pass
- Status: **IN PROGRESS** (cycle 1 — Athena verified infra works, Code 1 passes; handing to Ares)
- Athena sanity check: anthropic SDK installed, API key available, Code 1 PASS confirmed
- Remaining: run full suite, fix any failures, iterate on agent_spec.md if needed

## Lessons Learned
- M1 scope was too narrow (only 2 codes). Human expects ALL codes to work.
- Always read the full spec.md before scoping milestones.
- Verification (Vera) caught real errors — independent verification is valuable.
- Cycle estimates were slightly optimistic for M1 (estimated 5, used ~3 for writing + ~2 for verification).
- M2 verification caught timing errors that were subtle but real — always verify worked examples against the actual code.
- Multi-round verification (Vera → Apollo → Ares fix → Apollo re-verify) was necessary for correctness.
