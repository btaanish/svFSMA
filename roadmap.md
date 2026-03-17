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
- Status: **PENDING**

### M3: Build Test Harness and Final Validation (cycles: 5)
- Create testing framework that feeds all SV codes to an agent using the spec
- Evaluate correctness of FSM extraction for each code
- Final iteration and polish
- Status: **PENDING**

## Lessons Learned
- M1 scope was too narrow (only 2 codes). Human expects ALL codes to work.
- Always read the full spec.md before scoping milestones.
- Verification (Vera) caught real errors — independent verification is valuable.
- Cycle estimates were slightly optimistic for M1 (estimated 5, used ~3 for writing + ~2 for verification).
