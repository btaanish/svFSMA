# Project Roadmap: SystemVerilog to FSM Agent

## Project Goal
Create an agent spec (prompt/description) that enables an AI agent to read SystemVerilog code, modularize it, and extract FSMs. Validate by testing against two provided SV code samples.

## Key Insights from Analysis
- The SV code uses an **event-chain sequencer** pattern (not traditional case-statement FSMs)
- EVENTS arrays encode state transitions as combinational ripple chains
- Event counters provide clock-cycle delays between states
- Sync states provide indefinite waits on external conditions
- `_init_0` one-shot seeds the event chain; feedback creates loops
- Code 1: Trivial 2-state loop (always assigns r_q=0)
- Code 2: 4-state handshake requester with conditional branching (dead false branch)

## Milestones

### M1: Create Agent Spec for SV-to-FSM Conversion (cycles: 5)
- Write a detailed agent description/prompt that instructs an AI to:
  1. Parse and understand SystemVerilog event-chain sequencer patterns
  2. Identify modular components (datapath, event scheduling, sync states, counters)
  3. Extract FSM states, transitions, inputs/outputs
  4. Produce clear FSM descriptions with state diagrams
- Deliverable: `agent_spec.md` in repo root
- Status: **PENDING**

### M2: Build Test Harness and Validate (cycles: 5)
- Create a testing framework that:
  1. Feeds the two provided SV code samples to an agent using the spec
  2. Evaluates whether the agent correctly identifies states, transitions, outputs
  3. Compares against known-correct FSM descriptions
- Deliverable: Test scripts and expected outputs
- Status: **PENDING**

### M3: Iterate and Finalize (cycles: 3)
- Fix any issues found during validation
- Refine the agent spec based on test results
- Ensure both code samples produce correct FSM output
- Status: **PENDING**

## Lessons Learned
- (none yet - first cycle)
