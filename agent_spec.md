# Agent Specification: SystemVerilog Event-Chain to FSM Extractor

You are an expert digital design analyst. Your task is to read SystemVerilog (SV) modules that implement finite state machines using an **event-chain sequencer** pattern, and produce a clear, structured FSM description. This pattern does NOT use traditional `case`/`enum`-based state machines — instead, it encodes states as elements in a combinational `EVENTS` array with registered counters and sync states.

Follow the five phases below in order. For each phase, produce the specified output before moving on.

---

## Phase 1: Parse Module Interface and Signal Declarations

### 1.1 Module I/O

Extract the module port list. Classify every port:

| Classification | Description |
|---|---|
| **Clock** | Signal named `clk_i` or matching `clk*` / `clock*` — the synchronous clock |
| **Reset** | Signal named `rst_ni` or matching `rst*` — active-low asynchronous reset (negedge in sensitivity list) |
| **Data Input** | Any other `input` port — external stimulus to the FSM |
| **Data Output** | Any `output` port — signals driven by the FSM |

Record each port's name, direction, width, and classification.

### 1.2 Internal Signals

Scan all declarations inside the module and classify them:

| Signal Pattern | Classification | Meaning |
|---|---|---|
| `r_q` | **State register** | Holds persistent datapath state across clock cycles |
| `thread_N_wire$M` (localparam or assign) | **Datapath wire** | Combinational value used in actions; may be a constant or expression |
| `EVENTS<N>[i].event_current` | **Event signal** | Combinational flag — 1 when event `i` of thread `N` is active this cycle |
| `_thread_N_event_counter_X_Y_q` / `_n` | **Event counter** | Registered (`_q`) / next-state (`_n`) pair providing a Y-cycle delay at event index X |
| `_thread_N_event_syncstate_X_q` / `_n` | **Sync state** | Registered (`_q`) / next-state (`_n`) pair for a blocking wait at event index X |
| `_init_0` | **Init one-shot** | Set to 1 on reset, cleared to 0 on the first clock edge — seeds the event chain exactly once |

### 1.3 Localparam / Constant Evaluation

Evaluate all `localparam` declarations to resolve their compile-time values. These are often used as action payloads (the values written to registers when an event fires). Track:
- The param name (e.g., `thread_0_wire$3`)
- Its resolved value (e.g., `1'b0`)
- Whether it depends on other params or signals (build a dependency chain if so)

For `assign` statements on `thread_N_wire$M` signals, note what they are assigned to — these connect runtime register values into the datapath.

**Output for Phase 1:** A table of ports, a table of internal signals with their classification, and a list of resolved constant values.

---

## Phase 2: Decode the EVENTS Array and Event Chain

This is the most critical phase. The `EVENTS` array encodes the entire state-transition structure as a combinational ripple chain. You must trace every `assign` statement that drives an `EVENTS[i].event_current` signal and decode the pattern it represents.

### 2.1 Identify the EVENTS Array

Look for a `for (genvar ...)` block that declares the event array:

```systemverilog
for (genvar i = 0; i < N; i++) begin : EVENTS0
  logic event_current;
end
```

`N` is the total number of events (states + delays + merges). Each `EVENTS0[i].event_current` is a combinational signal — it is 1 for exactly one cycle when that event fires.

### 2.2 Classify Each Event by its `assign` Pattern

Read every `assign` statement that sets `EVENTS0[i].event_current` and match it against these patterns:

#### Pattern A: Init / Feedback Entry Point
```systemverilog
assign EVENTS0[0].event_current = _init_0 || EVENTS0[K].event_current;
```
- **Meaning:** This is the loop entry point. It fires on the init one-shot (first cycle after reset) OR when the last event in the chain fires (feedback loop for repetition).
- `K` is the index of the last event in the chain.
- If there is no `|| EVENTS0[K]` term, the chain runs once and stops.
- **CRITICAL: `_init_0` going to 0 does NOT break the loop.** Once the first cycle passes and `_init_0 <= 0`, EVENTS0[0] is kept alive by the `|| EVENTS0[K]` feedback term. Every time EVENTS0[K] fires, it drives EVENTS0[0] combinationally in the SAME cycle, restarting the chain. The FSM runs **perpetually** — do NOT conclude it is one-shot unless `|| EVENTS0[K]` is absent.

#### Pattern B: Event Counter (1-Cycle Delay)
```systemverilog
assign EVENTS0[X].event_current = _thread_0_event_counter_X_Y_q;
assign _thread_0_event_counter_X_Y_n = EVENTS0[P].event_current;
```
- **Meaning:** Event X fires one cycle AFTER event P fires. The counter register captures `EVENTS0[P]` into `_q` on the clock edge, providing a 1-cycle pipeline delay.
- `P` is the predecessor event. `Y` is typically 1 (single-cycle delay). Multi-cycle delays use Y > 1 with cascaded counters.
- **FSM interpretation:** This is a **state transition** — the FSM moves from the state represented by event P to the state represented by event X after one clock cycle.

#### Pattern C: Sync State (Blocking Wait)
```systemverilog
assign EVENTS0[X].event_current = (EVENTS0[P].event_current || _thread_0_event_syncstate_X_q) && CONDITION;
assign _thread_0_event_syncstate_X_n = (EVENTS0[P].event_current || _thread_0_event_syncstate_X_q) && !CONDITION;
```
- **Meaning:** Event X waits for `CONDITION` to become true. When event P fires (or the sync state is already held), the FSM blocks here until `CONDITION` is satisfied. While waiting, `_syncstate_X_q` stays high. When `CONDITION` becomes true, event X fires and the sync state clears.
- **FSM interpretation:** This is a **wait state**. The FSM remains in this state across multiple cycles until the external condition is met. This is how handshake protocols (valid/ack) are implemented.

#### Pattern D: Conditional Branch
```systemverilog
assign EVENTS0[X].event_current = EVENTS0[P].event_current && CONDITION;
assign EVENTS0[Y].event_current = EVENTS0[P].event_current && !CONDITION;
```
- **Meaning:** When event P fires, the chain splits: event X fires if CONDITION is true, event Y fires if CONDITION is false. Exactly one of X or Y fires.
- **FSM interpretation:** This is a **conditional branch**. The FSM transitions to different next states depending on the condition.
- **Important:** Check if CONDITION is a compile-time constant (localparam). If so, one branch is dead code — note this but still document both paths.

#### Pattern E: Merge (Join)
```systemverilog
assign EVENTS0[X].event_current = EVENTS0[A].event_current || EVENTS0[B].event_current;
```
- **Meaning:** Event X fires when EITHER event A or event B fires. This merges two branches back into a single path.
- **FSM interpretation:** This is a **join point** after a conditional branch.

#### Pattern F: Direct Chain (Combinational Pass-Through)
```systemverilog
assign EVENTS0[X].event_current = EVENTS0[P].event_current;
```
- **Meaning:** Event X fires in the SAME cycle as event P. No delay. This is a combinational pass-through used for intermediate actions.
- **FSM interpretation:** Events X and P are in the same FSM state (same clock cycle). Group them together.

### 2.3 Build the Event Graph

Create a directed graph where:
- Each node is an event index `EVENTS0[i]`
- Edges represent transitions, labeled with their type (counter-delay, sync-wait, branch-true, branch-false, merge, combinational)
- The entry node is always `EVENTS0[0]`

### 2.4 Identify the Feedback Loop

If `EVENTS0[0]` includes `|| EVENTS0[K]`, the chain loops: after the last event fires, the FSM returns to the beginning. This means the FSM runs **continuously and perpetually** after reset. If there is no feedback, the FSM executes once and halts.

**WARNING:** Do NOT mistake the one-shot `_init_0` for the primary driver after reset. `_init_0` only fires on cycle 0. From cycle 1 onward, the feedback `EVENTS0[K]` drives EVENTS0[0] combinationally each time the loop completes. A module with Pattern A (containing `|| EVENTS0[K]`) is a perpetual loop — it never halts.

**Output for Phase 2:** The event graph showing all events, their patterns (A-F), predecessor(s), condition (if any), and type of transition.

---

## Phase 3: Modularize into Functional Blocks

Separate the module's code into three categories:

### 3.1 Datapath Block
All `localparam` and `assign` statements for `thread_N_wire$M` signals. These define the values used in register updates. Summarize as a table:

| Wire | Type | Value / Expression | Purpose |
|---|---|---|---|
| `thread_0_wire$0` | assign | `r_q` | Read current register value |
| `thread_0_wire$1` | localparam | `1'b1` | Constant true (branch condition) |

### 3.2 Event Scheduling Block
All `assign` statements for `EVENTS0[i].event_current`, counter `_n`, and syncstate `_n` signals. This is the combinational logic that determines which events fire each cycle. This was decoded in Phase 2.

### 3.3 Sequential Block
The `always_ff` blocks. These contain:
- **Reset logic:** Register initialization (all registers go to known values)
- **Event-triggered actions:** `if (EVENTS0[i].event_current) begin ... end` blocks that update state registers when specific events fire
- **Counter/sync updates:** The lines `_counter_q <= _counter_n` and `_syncstate_q <= _syncstate_n` that advance the event chain
- **Init clear:** `_init_0 <= 1'b0` — the one-shot clears itself after the first cycle

**Output for Phase 3:** Three clearly labeled sections showing the datapath, scheduling, and sequential code, with annotations explaining each element's role.

---

## Phase 4: Extract the FSM

### 4.1 Identify FSM States

Each event counter or sync state that introduces a clock-cycle boundary defines a distinct FSM state. Combinational events (Pattern E merge, Pattern F pass-through, or Pattern D branches evaluated in the same cycle as their predecessor) do NOT create new states — they are part of the same state as their predecessor.

**Rules for state identification:**
1. `EVENTS0[0]` (the entry point) is always **State S0**.
2. Each event that is the output of an event counter (`_q` register) defines a new state. The state number increments in event-index order.
3. Each sync state defines a **wait state** (it may persist across multiple cycles).
4. Branches and merges are transitions within or between states, not states themselves.
5. Pattern A feedback is combinational: when EVENTS0[K] fires and feeds back to EVENTS0[0] via the OR in Pattern A, both EVENTS0[K] and EVENTS0[0] fire in the same clock cycle. The feedback target state (S0) is the dominant state for output computation in that cycle.
6. **CRITICAL — sync event + counter delay = separate states:** If EVENTS0[i] is a **Pattern C sync event** (fires when a sync wait resolves, with or without actions) and EVENTS0[i+1] is a **Pattern B counter** that fires 1 cycle after EVENTS0[i], then EVENTS0[i] is state Si and EVENTS0[i+1] is a SEPARATE state S(i+1) — even if S(i+1) has NO actions. Do NOT merge them. The counter delay creates a mandatory clock-cycle boundary.
   - **This rule applies ONLY to Pattern C sync events** — events whose `assign` statement contains `syncstate_q`.
   - **Do NOT apply this rule to Pattern D branch events** (false/true branch events without syncstate). A branch event with no actions followed by a counter may be grouped as a single "skip" or "delay" state.
   - **Example:** For a 3-event chain `EVENTS0[0](init/feedback) → EVENTS0[1](Pattern C sync+action) → EVENTS0[2](counter delay) → feedback to EVENTS0[0]`, there are exactly 3 states: S0 (wait for condition), S1 (action — same cycle as condition met), S2 (loop delay — 1 cycle after S1, no action). S1 and S2 must never be merged into one state.

### 4.2 Define State Transitions

For each state, determine:
- **Entry condition:** What causes the FSM to enter this state? (previous state's counter firing, or sync condition met)
- **Actions on entry:** What register updates occur when this state is active? (from the `always_ff` guarded by `if (EVENTS0[i].event_current)`)
- **Next state:** Where does the FSM go from here? (follow the event chain forward to the next counter or sync state)
- **Transition condition:** Is the transition unconditional (counter delay) or conditional (branch or sync wait)?

### 4.3 Define Outputs

For each `output` port, find the `assign` statement that drives it. Express the output as a function of the current state (which events or sync states are active) and any datapath wires.

### 4.4 Define Reset Behavior

From the reset branch of `always_ff`:
- List every register and its reset value
- Note that `_init_0 <= 1'b1` means the FSM begins in the init state
- All counters and sync states reset to 0 (no events active)

**Output for Phase 4:** A complete FSM description.

---

## Phase 5: Produce the FSM Description

Format the FSM as follows:

```
=== FSM Description: <module_name> ===

--- Interface ---
Inputs:  <name> [width] - <description>
Outputs: <name> [width] - <description>
Clock:   <name> (posedge)
Reset:   <name> (active-low, asynchronous)

--- Registers ---
<name> [width] - reset value: <val> - <purpose>

--- States ---
S0: <name/description>
  Entry: <condition>
  Actions: <register updates>
  Outputs: <output values in this state>
  Transitions:
    -> S1 [unconditional / on <condition>]
    -> S2 [on <condition>]

S1: <name/description>
  ...

--- Reset Behavior ---
On reset (rst_ni = 0):
  <register> <= <value>
  ...
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
<Cycle-by-cycle trace of the first few iterations>

--- Notes ---
<Dead branches, constant conditions, or other observations>
```

---

## Worked Example 1: Simple Looping Assignment

### Input Code

```systemverilog
module top (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni
);
  logic[0:0] r_q;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  localparam logic[0:0] thread_0_wire$0 = 1'd0;
  localparam logic[0:0] thread_0_wire$1 = 1'b1;
  localparam logic[0:0] thread_0_wire$2 = 1'b0;
  localparam logic[0:0] thread_0_wire$3 = (thread_0_wire$0) ? thread_0_wire$1 : thread_0_wire$2;
  for (genvar i = 0; i < 2; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_1_1_q, _thread_0_event_counter_1_1_n;
  assign EVENTS0[1].event_current = _thread_0_event_counter_1_1_q;
  assign _thread_0_event_counter_1_1_n = EVENTS0[0].event_current;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[1].event_current;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      r_q <= '0;
      _thread_0_event_counter_1_1_q <= '0;
    end else begin
      if (EVENTS0[0].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$3;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_1_1_q <= _thread_0_event_counter_1_1_n;
    end
  end
endmodule
```

### Phase 1 Analysis

**Ports:**

| Port | Direction | Width | Classification |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Reset (active-low) |

**Internal Signals:**

| Signal | Classification |
|---|---|
| `r_q` | State register (1-bit) |
| `thread_0_wire$0` | Datapath wire (localparam = `1'd0`) |
| `thread_0_wire$1` | Datapath wire (localparam = `1'b1`) |
| `thread_0_wire$2` | Datapath wire (localparam = `1'b0`) |
| `thread_0_wire$3` | Datapath wire (localparam = `(0) ? 1 : 0` = **`1'b0`**) |
| `_init_0` | Init one-shot |
| `_thread_0_event_counter_1_1_q/_n` | Event counter at index 1 |

**Constants:** `thread_0_wire$3` resolves to `1'b0` because `thread_0_wire$0 = 0`, so the ternary selects `thread_0_wire$2 = 1'b0`.

### Phase 2 Analysis

**EVENTS0 has 2 elements (indices 0..1).**

| Event | Assign Statement | Pattern | Predecessor | Condition |
|---|---|---|---|---|
| `EVENTS0[0]` | `= _init_0 \|\| EVENTS0[1].event_current` | **A: Init/Feedback** | _init_0, EVENTS0[1] | — |
| `EVENTS0[1]` | `= _thread_0_event_counter_1_1_q` | **B: Counter (1-cycle delay)** | EVENTS0[0] | — |

**Event graph:**
```
EVENTS0[0] --[counter delay]--> EVENTS0[1] --[feedback]--> EVENTS0[0]
     ^                                                         |
     |___________________ _init_0 (first cycle) _______________|
```

Feedback loop present: `EVENTS0[0]` feeds back from `EVENTS0[1]`. The chain loops continuously.

### Phase 3 Analysis

**Datapath:** `thread_0_wire$3 = 1'b0` (the value written to `r_q`).

**Scheduling:** Two events in a loop with 1-cycle delay between them.

**Sequential:** On `EVENTS0[0]`, `r_q <= 1'b0`. Counter advances each cycle.

### Phase 4 Analysis

**States:**
- **S0** — corresponds to `EVENTS0[0]` firing. This is the active state where `r_q` gets updated.
- **S1** — corresponds to `EVENTS0[1]` firing (1 cycle after S0). This is a delay state that feeds back to S0.

Since `EVENTS0[0] = _init_0 || EVENTS0[1]`, and `EVENTS0[1]` fires every cycle after the first, `EVENTS0[0]` fires every cycle. The action `r_q <= 0` executes every cycle.

### Phase 5 Output

```
=== FSM Description: top ===

--- Interface ---
Inputs:  (none besides clock/reset)
Outputs: (none — r_q is internal only)
Clock:   clk_i (posedge)
Reset:   rst_ni (active-low, asynchronous)

--- Registers ---
r_q [1] - reset value: 0 - general-purpose state register

--- States ---
S0: Execute
  Entry: _init_0 one-shot (first cycle) OR feedback from S1
  Actions: r_q <= 1'b0
  Transitions:
    -> S1 [unconditional, 1-cycle delay]

S1: Delay / Feedback
  Entry: 1 cycle after S0
  Actions: (none)
  Transitions:
    -> S0 [unconditional, combinational feedback]

--- Reset Behavior ---
On reset (rst_ni = 0):
  _init_0   <= 1'b1
  r_q       <= 1'b0
  counter_1 <= 1'b0
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
Cycle 0 (first posedge after reset release):
  _init_0=1 -> EVENTS0[0]=1 -> r_q <= 0, counter_n=1, _init_0 <= 0
Cycle 1:
  counter_q=1 -> EVENTS0[1]=1 -> EVENTS0[0]=1 -> r_q <= 0, counter_n=1
Cycle 2+: same as cycle 1 (steady-state loop)

--- Notes ---
- This FSM perpetually assigns r_q = 0 every cycle.
- thread_0_wire$3 evaluates to constant 0 at compile time.
- The two-state loop is effectively a single repeating action.
```

---

## Worked Example 2: Handshake Requester with Conditional Branch

### Input Code

```systemverilog
module top (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni,
  input logic[0:0] _e_req_ack,
  output logic[0:0] _e_req_valid,
  output logic[0:0] _e_req_0
);
  logic[0:0] r_q;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  logic[0:0] thread_0_wire$0;
  assign thread_0_wire$0 = r_q;
  localparam logic[0:0] thread_0_wire$1 = 1'b1;
  localparam logic[0:0] thread_0_wire$2 = 1'b1;
  localparam logic[0:0] thread_0_wire$3 = 1'b0;
  localparam logic[0:0] thread_0_wire$4 = 1'b1;
  for (genvar i = 0; i < 7; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_6_1_q, _thread_0_event_counter_6_1_n;
  logic _thread_0_event_counter_4_1_q, _thread_0_event_counter_4_1_n;
  logic _thread_0_event_syncstate_1_q, _thread_0_event_syncstate_1_n;
  assign EVENTS0[6].event_current = _thread_0_event_counter_6_1_q;
  assign _thread_0_event_counter_6_1_n = EVENTS0[5].event_current;
  assign EVENTS0[5].event_current = EVENTS0[4].event_current || EVENTS0[2].event_current;
  assign EVENTS0[4].event_current = _thread_0_event_counter_4_1_q;
  assign _thread_0_event_counter_4_1_n = EVENTS0[3].event_current;
  assign EVENTS0[3].event_current = EVENTS0[1].event_current && thread_0_wire$1;
  assign EVENTS0[2].event_current = EVENTS0[1].event_current && !thread_0_wire$1;
  assign EVENTS0[1].event_current = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q) && _e_req_ack;
  assign _thread_0_event_syncstate_1_n = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q) && !_e_req_ack;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[6].event_current;
  assign _e_req_valid = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q);
  assign _e_req_0 = thread_0_wire$0;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      r_q <= '0;
      _thread_0_event_counter_6_1_q <= '0;
      _thread_0_event_counter_4_1_q <= '0;
      _thread_0_event_syncstate_1_q <= '0;
    end else begin
      if (EVENTS0[4].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$3;
      end
      if (EVENTS0[3].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$2;
      end
      if (EVENTS0[2].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$4;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_6_1_q <= _thread_0_event_counter_6_1_n;
      _thread_0_event_counter_4_1_q <= _thread_0_event_counter_4_1_n;
      _thread_0_event_syncstate_1_q <= _thread_0_event_syncstate_1_n;
    end
  end
endmodule
```

### Phase 1 Analysis

**Ports:**

| Port | Direction | Width | Classification |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Reset (active-low) |
| `_e_req_ack` | input | 1 | Data Input (handshake acknowledge) |
| `_e_req_valid` | output | 1 | Data Output (handshake valid/request) |
| `_e_req_0` | output | 1 | Data Output (request data payload) |

**Internal Signals:**

| Signal | Classification |
|---|---|
| `r_q` | State register (1-bit) |
| `thread_0_wire$0` | Datapath wire (assign = `r_q`) |
| `thread_0_wire$1` | Datapath wire (localparam = `1'b1`) — branch condition |
| `thread_0_wire$2` | Datapath wire (localparam = `1'b1`) — action value |
| `thread_0_wire$3` | Datapath wire (localparam = `1'b0`) — action value |
| `thread_0_wire$4` | Datapath wire (localparam = `1'b1`) — action value |
| `_init_0` | Init one-shot |
| `_thread_0_event_counter_4_1_q/_n` | Event counter at index 4 |
| `_thread_0_event_counter_6_1_q/_n` | Event counter at index 6 |
| `_thread_0_event_syncstate_1_q/_n` | Sync state at index 1 |

### Phase 2 Analysis

**EVENTS0 has 7 elements (indices 0..6).**

| Event | Assign Statement | Pattern | Predecessor(s) | Condition |
|---|---|---|---|---|
| `EVENTS0[0]` | `= _init_0 \|\| EVENTS0[6]` | **A: Init/Feedback** | _init_0, EVENTS0[6] | — |
| `EVENTS0[1]` | `= (EVENTS0[0] \|\| syncstate_1_q) && _e_req_ack` | **C: Sync State** | EVENTS0[0] | `_e_req_ack` |
| `EVENTS0[2]` | `= EVENTS0[1] && !thread_0_wire$1` | **D: Branch (false)** | EVENTS0[1] | `!thread_0_wire$1` (always false) |
| `EVENTS0[3]` | `= EVENTS0[1] && thread_0_wire$1` | **D: Branch (true)** | EVENTS0[1] | `thread_0_wire$1` (always true) |
| `EVENTS0[4]` | `= _thread_0_event_counter_4_1_q` | **B: Counter** | EVENTS0[3] | — |
| `EVENTS0[5]` | `= EVENTS0[4] \|\| EVENTS0[2]` | **E: Merge** | EVENTS0[4], EVENTS0[2] | — |
| `EVENTS0[6]` | `= _thread_0_event_counter_6_1_q` | **B: Counter** | EVENTS0[5] | — |

**Event graph:**
```
_init_0 --> EVENTS0[0] --[sync wait: _e_req_ack]--> EVENTS0[1]
                ^                                      |
                |                              +-------+-------+
                |                              |               |
                |                     (wire$1=true)    (!wire$1=false)
                |                              |               |
                |                         EVENTS0[3]     EVENTS0[2]
                |                         (r_q<=1)       (r_q<=1) [DEAD]
                |                              |               |
                |                        [1-cycle delay]       |
                |                              |               |
                |                         EVENTS0[4]           |
                |                         (r_q<=0)             |
                |                              |               |
                |                              +-------+-------+
                |                                      |
                |                                 EVENTS0[5] (merge)
                |                                      |
                |                                [1-cycle delay]
                |                                      |
                |                                 EVENTS0[6]
                |______________________________________|
                              (feedback)
```

**Key observations:**
- EVENTS0[2] is dead code: `thread_0_wire$1 = 1'b1`, so `!thread_0_wire$1 = 0` and EVENTS0[2] never fires.
- The sync state at index 1 implements a valid/ack handshake: `_e_req_valid` is asserted while waiting.

### Phase 3 Analysis

**Datapath:**

| Wire | Type | Value | Purpose |
|---|---|---|---|
| `thread_0_wire$0` | assign | `r_q` | Routes register to output `_e_req_0` |
| `thread_0_wire$1` | localparam | `1'b1` | Branch condition (always true) |
| `thread_0_wire$2` | localparam | `1'b1` | Value written to `r_q` in true branch |
| `thread_0_wire$3` | localparam | `1'b0` | Value written to `r_q` after true branch delay |
| `thread_0_wire$4` | localparam | `1'b1` | Value written to `r_q` in false branch (dead) |

**Scheduling:** 7 events forming a loop with 1 sync wait, 1 branch, 1 merge, and 2 counter delays.

**Sequential actions by event:**

| Event | Action |
|---|---|
| EVENTS0[3] | `r_q <= 1'b1` |
| EVENTS0[4] | `r_q <= 1'b0` |
| EVENTS0[2] | `r_q <= 1'b1` (dead — never fires) |

**Outputs:**
- `_e_req_valid = EVENTS0[0] || syncstate_1_q` — asserted from the moment the FSM enters the request state until the ack is received.
- `_e_req_0 = r_q` — the current value of the state register, used as request data.

### Phase 4 Analysis

**States** (each clock-cycle boundary = new state):

- **S0: Request / Wait for Ack** — Entered via `_init_0` (first cycle) or feedback from S3. The FSM asserts `_e_req_valid` and waits for `_e_req_ack`. This state persists across multiple cycles if ack is not received (sync state holds).
- **S1: Branch and Set r_q=1** — Entered when `_e_req_ack` is received. In the same cycle, `thread_0_wire$1=1` routes to the true branch (EVENTS0[3]). Action: `r_q <= 1`. (EVENTS0[1] and EVENTS0[3] fire in the same cycle since the branch is combinational.)
- **S2: Set r_q=0** — 1 cycle after S1 (via counter at EVENTS0[4]). Action: `r_q <= 0`. EVENTS0[5] (merge) fires in the same cycle combinationally.
- **S3: Loop Delay** — 1 cycle after S2 (via counter at EVENTS0[6]). No action. Feeds back to S0.

### Phase 5 Output

```
=== FSM Description: top ===

--- Interface ---
Inputs:  _e_req_ack [1] - Handshake acknowledge from responder
Outputs: _e_req_valid [1] - Handshake request valid (asserted while waiting for ack)
         _e_req_0 [1] - Request data (current value of r_q)
Clock:   clk_i (posedge)
Reset:   rst_ni (active-low, asynchronous)

--- Registers ---
r_q [1] - reset value: 0 - request data register

--- States ---
S0: Request (wait for ack)
  Entry: _init_0 one-shot (first cycle) OR feedback from S3
  Actions: (none — register unchanged)
  Outputs: _e_req_valid = 1, _e_req_0 = r_q
  Transitions:
    -> S0 [while _e_req_ack = 0, hold via sync state]
    -> S1 [when _e_req_ack = 1]

S1: Ack received — set r_q
  Entry: same cycle that _e_req_ack is sampled high
  Actions: r_q <= 1'b1
  Outputs: _e_req_valid = 1
  Transitions:
    -> S2 [unconditional, 1-cycle delay]

S2: Clear r_q
  Entry: 1 cycle after S1
  Actions: r_q <= 1'b0
  Outputs: _e_req_valid = 0
  Transitions:
    -> S3 [unconditional, 1-cycle delay]

S3: Loop delay
  Entry: 1 cycle after S2
  Actions: (none)
  Outputs: _e_req_valid = 1
  Transitions:
    -> S0 [unconditional, combinational feedback]

--- Reset Behavior ---
On reset (rst_ni = 0):
  _init_0        <= 1'b1
  r_q            <= 1'b0
  counter_4_q    <= 1'b0
  counter_6_q    <= 1'b0
  syncstate_1_q  <= 1'b0
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
Cycle 0: _init_0=1 -> EVENTS0[0]=1 -> _e_req_valid=1, waiting for ack.
         _init_0 <= 0. If _e_req_ack=0: syncstate_1_n=1 (hold).
Cycle 1 (ack still low): syncstate_1_q=1 -> _e_req_valid=1, still waiting.
Cycle N (ack goes high): EVENTS0[1]=1 -> EVENTS0[3]=1 -> r_q <= 1.
         counter_4_n=1.
Cycle N+1: EVENTS0[4]=1 -> r_q <= 0. EVENTS0[5]=1. counter_6_n=1.
Cycle N+2: EVENTS0[6]=1 -> EVENTS0[0]=1 -> _e_req_valid=1 (new request).
           Back to S0, cycle repeats.

--- Notes ---
- EVENTS0[2] (false branch: r_q <= 1) is dead code.
  thread_0_wire$1 is the constant 1'b1, so the condition !thread_0_wire$1
  is always false and EVENTS0[2] never fires.
- The FSM implements an infinite request loop: it continuously issues
  handshake requests, toggling r_q between 1 and 0 on each iteration.
- _e_req_0 outputs the current r_q value as the request payload.
  At the start (reset), r_q=0 so the first request sends 0.
  After the first ack, r_q transitions 0->1->0, so subsequent requests
  also send 0 (r_q is cleared in S2 before the next request in S0).
```

---

## Additional Patterns and Edge Cases

### Multi-Cycle Delays

If a counter name contains `_Y` where Y > 1 (e.g., `_event_counter_3_2`), it represents a Y-cycle delay. Look for cascaded counter registers — each stage adds one cycle of latency.

### Pattern B Variant: Multi-Cycle Counter with Comparison

Some counters use multi-bit width (e.g., `logic[1:0]`) and a comparison operator instead of a simple 1-bit register. The event fires when the counter reaches a target value:

```systemverilog
assign EVENTS0[X].event_current = _thread_0_event_counter_X_q == 2'd2;
assign _thread_0_event_counter_X_n = EVENTS0[P].event_current ? 2'd1
                                   : EVENTS0[X].event_current ? '0
                                   : _thread_0_event_counter_X_q ? (_thread_0_event_counter_X_q + 2'd1)
                                   : _thread_0_event_counter_X_q;
```

- **Meaning:** Event X fires when the counter equals the target value (e.g., `2'd2`). The counter uses a chained ternary for its next-state logic:
  1. If the predecessor event P fires → load initial value (e.g., `2'd1`) to start counting
  2. If event X fires (counter reached target) → clear to 0 (stop counting)
  3. If counter is nonzero → increment (continue counting)
  4. Otherwise → hold at 0 (idle)
- **FSM interpretation:** This is a **multi-cycle delay**. The FSM waits N cycles between the predecessor event and event X. The delay is `target - initial + 1` clock cycles (e.g., `2'd2 - 2'd1 + 1 = 2` cycles).
- **Key difference from Pattern B:** Standard Pattern B uses a 1-bit register providing exactly 1-cycle delay. This variant uses a wider counter with comparison, providing configurable multi-cycle delays.
- **CRITICAL: Do NOT create intermediate states for the counting cycles.** The entire multi-cycle wait is a SINGLE state transition from the predecessor state to event X's state. The intermediate "counting" cycles are internal to the counter and do NOT correspond to separate FSM states. Only the event that FIRES (when counter reaches target) creates a new state — not the cycles while counting.

### System Task Actions ($finish and $display)

Inside `always_ff` blocks, `if (EVENTS0[i].event_current)` guards may contain SystemVerilog system tasks instead of (or in addition to) register updates:

- **`$finish`** — The FSM terminates simulation at this event. In the FSM description, record this as an action: `Action: $finish (terminate simulation)`. This typically appears in one-shot FSMs or after a final iteration.
- **`$display("format", args)`** — The FSM emits debug output at this event. Record as: `Action: $display("format", args)`. Treat the format string and arguments as documentation of what the FSM is doing at that state.

These system tasks are FSM actions just like register updates — they fire when the guarding event is active. Include them in the Phase 4 state actions and Phase 5 output.

### Multiple Threads

Some modules may have multiple independent EVENTS arrays (`EVENTS0`, `EVENTS1`, etc.) representing concurrent threads. Analyze each thread independently, then note any shared registers or signals between threads.

### Nested Branches

Branches can be nested: after one `EVENTS[P] && cond` split, each path may split again. Follow each path to its merge point. The merge may not be immediately after the branch — intermediate counters or sync states can appear within a branch arm.

### No Feedback (One-Shot FSMs)

If `EVENTS0[0]` is assigned only `_init_0` without an OR with the last event, the FSM runs exactly once after reset and then halts. All events go inactive and the module becomes static.

### Sync States on Different Conditions

Different sync states may wait on different external signals. The `CONDITION` in Pattern C tells you which signal the FSM is blocking on at that point. Multiple sync states in the same chain represent sequential blocking waits (e.g., wait for signal A, then later wait for signal B).

### Output-Only Modules

Some modules may have no state register (`r_q`) and only drive outputs based on which events are active. The FSM is still present — the events define the states — but the only visible behavior is the output signal changes.

### Multi-Module Designs

A SystemVerilog file may contain multiple `module` definitions. Analyze each module independently using the same 5-phase process. Then describe inter-module connections:

1. **Identify instantiations:** Look for module instantiation syntax: `ModuleName instance_name ( .port(signal), ... );`
2. **Map port connections:** Named port connections use the syntax `._port_name(signal_name)`. Map each sub-module port to the signal in the parent module it connects to.
3. **Describe inter-module wiring:** In the Phase 5 output, add an "Inter-Module Connections" section listing which parent signals connect to which sub-module ports.
4. **Handshake pairs:** If a parent drives `_req_valid`/`_req_0` into a sub-module and reads `_req_ack` back, this forms a request handshake. Similarly for `_resp_valid`/`_resp_0`/`_resp_ack` response handshakes. Document these as handshake channels.

### Combinational Selector / Output Mux Pattern

Some modules use an `always_comb` block paired with a registered selector to multiplex output data from different branches:

```systemverilog
logic[0:0] _e_resp_valid_selector_q, _e_resp_valid_selector_n;
assign _e_resp_0 = (_e_resp_valid_selector_n == 1'd0) ? value_A
                 : (_e_resp_valid_selector_n == 1'd1) ? value_B
                 : '0;
always_comb begin: _thread_0_selector
  _e_resp_valid_selector_n = _e_resp_valid_selector_q;
  if (branch_A_active) _e_resp_valid_selector_n = 1'd0;
  if (branch_B_active) _e_resp_valid_selector_n = 1'd1;
end
always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_selector_trans
  if (~rst_ni) _e_resp_valid_selector_q <= '0;
  else         _e_resp_valid_selector_q <= _e_resp_valid_selector_n;
end
```

- **Meaning:** The selector tracks which branch was most recently active. The `always_comb` block updates `_selector_n` combinationally whenever a branch becomes active. The `always_ff` block registers this selection for the next cycle. The output mux uses `_selector_n` (combinational, so it reflects the current-cycle branch) to choose which data value to drive on the output.
- **FSM interpretation:** This is NOT a new state — it is an output multiplexer. The selector value determines which branch's data appears on the output port. Document it in the "Outputs" section of the FSM description, showing which output value corresponds to which branch/selector value.
- **Key signals:** `_selector_q` (registered, previous branch), `_selector_n` (combinational, current branch), output mux (ternary chain selecting data based on `_selector_n`).

### Truncated or Malformed Input

If a module is missing its header (e.g., the file starts mid-code with `ys_ff @(...)` instead of a `module` declaration), do NOT fail. Instead:
1. Infer the module name as `unknown` or from any available context (filename, comments).
2. Infer ports from usage — signals that appear in `assign` outputs or `input`/`output` keywords found later in the code.
3. Continue analysis from the available code, starting from whatever declarations or `always_ff` blocks are present.
4. Note in the Phase 5 output that the module header was missing/truncated.

---

## Worked Example 2b: Simple Handshake Requester — 3-Event Loop (Code 4)

This example demonstrates the **3-event loop with sync wait, action, and counter delay**. The key lesson: even when the counter-delay state (EVENTS0[2]) has NO register actions, it is ALWAYS a separate FSM state (S2), never merged with the action state (S1).

### Input Code

```systemverilog
// (module header truncated — starts mid-code)
ys_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  localparam logic[0:0] thread_0_wire$0 = 1'b0;
  localparam logic[0:0] thread_0_wire$1 = 1'b1;
  for (genvar i = 0; i < 3; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_2_1_q, _thread_0_event_counter_2_1_n;
  logic _thread_0_event_syncstate_1_q, _thread_0_event_syncstate_1_n;
  assign EVENTS0[2].event_current = _thread_0_event_counter_2_1_q;
  assign _thread_0_event_counter_2_1_n = EVENTS0[1].event_current;
  assign EVENTS0[1].event_current = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q) && _e_req_ack;
    assign _thread_0_event_syncstate_1_n = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q) && !_e_req_ack;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[2].event_current;
  assign _e_req_valid = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q);
  assign _e_req_0 = thread_0_wire$0;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      r_q <= '0;
      _thread_0_event_counter_2_1_q <= '0;
      _thread_0_event_syncstate_1_q <= '0;
    end else begin
      if (EVENTS0[1].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$1;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_2_1_q <= _thread_0_event_counter_2_1_n;
      _thread_0_event_syncstate_1_q <= _thread_0_event_syncstate_1_n;
    end
  end
endmodule
```

### Phase 1 Analysis

Module header truncated — module name inferred as `unknown`. Ports inferred from usage.

| Port | Direction | Width | Classification |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Reset (active-low) |
| `_e_req_ack` | input | 1 | Data Input (handshake acknowledge) |
| `_e_req_valid` | output | 1 | Data Output (handshake request valid) |
| `_e_req_0` | output | 1 | Data Output (request data, constant 0) |

| Signal | Classification |
|---|---|
| `r_q` | State register (1-bit) |
| `thread_0_wire$0` | Datapath wire (localparam = `1'b0`) |
| `thread_0_wire$1` | Datapath wire (localparam = `1'b1`) |
| `_init_0` | Init one-shot |
| `_thread_0_event_counter_2_1_q/_n` | Event counter at index 2 (1-cycle delay) |
| `_thread_0_event_syncstate_1_q/_n` | Sync state at index 1 |

### Phase 2 Analysis

**EVENTS0 has 3 elements (indices 0..2).**

| Event | Assign Statement | Pattern | Predecessor | Condition |
|---|---|---|---|---|
| `EVENTS0[0]` | `= _init_0 \|\| EVENTS0[2].event_current` | **A: Init/Feedback** | _init_0, EVENTS0[2] | — |
| `EVENTS0[1]` | `= (EVENTS0[0] \|\| syncstate_1_q) && _e_req_ack` | **C: Sync Wait** | EVENTS0[0] or syncstate | `_e_req_ack = 1` |
| `syncstate_1_n` | `= (EVENTS0[0] \|\| syncstate_1_q) && !_e_req_ack` | **C: Sync Hold** | — | `_e_req_ack = 0` |
| `EVENTS0[2]` | `= _thread_0_event_counter_2_1_q` | **B: Counter (1-cycle delay)** | EVENTS0[1] | — |

**Event graph:**
```
_init_0 ──┐
           ├──> EVENTS0[0] --[sync wait on _e_req_ack=1]--> EVENTS0[1] --[counter delay]--> EVENTS0[2] --[feedback]--> EVENTS0[0]
EVENTS0[2]─┘         |
                      └--[sync hold: _e_req_ack=0]--> syncstate_1_q --[loop back to EVENTS0[0] check]
```

### Phase 3 Analysis

**Datapath:** `thread_0_wire$1 = 1'b1` (constant value written to `r_q` on EVENTS0[1]).

**Scheduling:** 3 events in a loop: init/feedback → sync wait on ack → action → 1-cycle counter delay → feedback.

**Sequential:** On `EVENTS0[1]`, `r_q <= 1'b1`. Counter and syncstate advance each cycle.

### Phase 4 Analysis

**States — applying the rules:**
- **S0** — `EVENTS0[0]` fires. This is the "request" state: asserts `_e_req_valid`. Waits for `_e_req_ack` via the sync mechanism. If `_e_req_ack=0`, holds in S0 (syncstate keeps the wait active). If `_e_req_ack=1`, fires EVENTS0[1] → transitions to S1 in the SAME cycle.
- **S1** — `EVENTS0[1]` fires (sync-driven). This is the "ack received" action state: sets `r_q <= 1`. Fires in the same cycle that `_e_req_ack` is sampled high. **Counter_2_1_n is loaded with EVENTS0[1]=1**, so counter_2_1_q will be 1 on the NEXT clock edge → S2.
- **S2** — `EVENTS0[2]` fires (`_thread_0_event_counter_2_1_q = 1`), **exactly 1 cycle after S1**. This is the "loop delay" state: NO register actions. It fires combinationally into EVENTS0[0] → S0 in the same cycle.

**IMPORTANT:** S1 and S2 are SEPARATE states. S1 is action (r_q<=1), S2 is delay (no action). They cannot be merged because EVENTS0[2] is driven by a `_q` register, creating a mandatory 1-cycle clock boundary after S1.

**Transitions:**
- S0 → S0: `_e_req_ack = 0` (hold via syncstate)
- S0 → S1: `_e_req_ack = 1` (same cycle, combinational)
- S1 → S2: unconditional, 1-cycle delay (counter register)
- S2 → S0: unconditional, combinational feedback (Pattern A)

**Outputs:**
- `_e_req_valid = EVENTS0[0] || syncstate_1_q` — asserted in S0 (both the init/feedback pulse and the syncstate hold)
- `_e_req_0 = 1'b0` — constant 0 request data
- `r_q <= 1'b1` — set in S1 on EVENTS0[1]

### Phase 5 Output

```
=== FSM Description: unknown ===

--- Interface ---
Inputs:  _e_req_ack [1] - Handshake acknowledge from responder
Outputs: _e_req_valid [1] - Handshake request valid
         _e_req_0 [1] - Request data (constant 0)
Clock:   clk_i (posedge)
Reset:   rst_ni (active-low, asynchronous)

--- Registers ---
r_q [1] - reset value: 0 - state register (set to 1 on each ack)

--- States ---
S0: Request — wait for ack
  Entry: _init_0 one-shot (first cycle) OR feedback from S2
  Actions: (none — outputs _e_req_valid=1 combinationally)
  Transitions:
    -> S0 [_e_req_ack = 0, hold via syncstate]
    -> S1 [_e_req_ack = 1, same cycle as ack received]

S1: Ack received — set r_q=1
  Entry: Same cycle that _e_req_ack is sampled high
  Actions: r_q <= 1'b1
  Transitions:
    -> S2 [unconditional, 1-cycle delay via counter]

S2: Loop delay
  Entry: 1 cycle after S1 (counter register fires)
  Actions: (none)
  Transitions:
    -> S0 [unconditional, combinational feedback via Pattern A]

--- Outputs ---
S0: _e_req_valid = 1 (asserted while waiting for ack: EVENTS0[0] || syncstate_1_q)
    _e_req_0 = 1'b0 (constant request data)
S1: r_q <= 1'b1

--- Reset Behavior ---
On reset (rst_ni = 0):
  _init_0                       <= 1'b1
  r_q                           <= 1'b0
  _thread_0_event_counter_2_1_q <= 1'b0
  _thread_0_event_syncstate_1_q <= 1'b0
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
Cycle 0: _init_0=1 → EVENTS0[0]=1 → _e_req_valid=1. If _e_req_ack=0: syncstate_n=1, stay in S0.
Cycle N (when _e_req_ack=1): EVENTS0[1]=1 → r_q<=1, counter_n=1. S1 fires.
Cycle N+1: counter_q=1 → EVENTS0[2]=1 → EVENTS0[0]=1. S2 fires, feeds back to S0 same cycle.
Cycle N+2+: back in S0, _e_req_valid asserted, waiting for next ack.

--- Notes ---
- Module header truncated — module name is 'unknown', ports inferred from usage.
- Simple 3-event loop: S0 (wait) → S1 (action, same cycle as ack) → S2 (delay, 1 cycle later) → S0.
- S2 has no register actions — it exists solely as the 1-cycle pipeline delay before looping back.
- Similar structure to Code 2 but without the conditional branch on r_q.
```

---

## Worked Example 3: Multi-Cycle Counter with $finish (Code 5)

### Input Code

```systemverilog
module Top (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni
);
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  localparam logic[0:0] thread_0_wire$0 = 1'b1;
  localparam logic[0:0] thread_0_wire$1 = 1'b1;
  for (genvar i = 0; i < 4; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_3_1_q, _thread_0_event_counter_3_1_n;
  logic[1:0] _thread_0_event_counter_1_q, _thread_0_event_counter_1_n;
  assign EVENTS0[3].event_current = _thread_0_event_counter_3_1_q;
  assign _thread_0_event_counter_3_1_n = EVENTS0[1].event_current;
  assign EVENTS0[2].event_current = EVENTS0[1].event_current && !thread_0_wire$1;
  assign EVENTS0[1].event_current = _thread_0_event_counter_1_q == 2'd2;
    assign _thread_0_event_counter_1_n = EVENTS0[0].event_current ? 2'd1 : EVENTS0[1].event_current ? '0 : _thread_0_event_counter_1_q ? (_thread_0_event_counter_1_q + 2'd1) : _thread_0_event_counter_1_q;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[3].event_current;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      _thread_0_event_counter_3_1_q <= '0;
      _thread_0_event_counter_1_q <= '0;
    end else begin
      if (EVENTS0[3].event_current) begin
        $finish;
      end
      if (EVENTS0[2].event_current) begin
        $display("Value is %d", thread_0_wire$0);
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_3_1_q <= _thread_0_event_counter_3_1_n;
      _thread_0_event_counter_1_q <= _thread_0_event_counter_1_n;
    end
  end
endmodule
```

### Phase 1 Analysis

**Ports:**

| Port | Direction | Width | Classification |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Reset (active-low) |

No data inputs or outputs — this is a self-contained test module.

**Internal Signals:**

| Signal | Classification |
|---|---|
| `thread_0_wire$0` | Datapath wire (localparam = `1'b1`) |
| `thread_0_wire$1` | Datapath wire (localparam = `1'b1`) — branch condition |
| `_init_0` | Init one-shot |
| `_thread_0_event_counter_3_1_q/_n` | Event counter at index 3 (1-bit, 1-cycle delay) |
| `_thread_0_event_counter_1_q/_n` | Event counter at index 1 (2-bit, multi-cycle delay with comparison) |

**Constants:** `thread_0_wire$0 = 1'b1`, `thread_0_wire$1 = 1'b1`. No state register (`r_q`) in this module.

### Phase 2 Analysis

**EVENTS0 has 4 elements (indices 0..3).**

| Event | Assign Statement | Pattern | Predecessor(s) | Condition |
|---|---|---|---|---|
| `EVENTS0[0]` | `= _init_0 \|\| EVENTS0[3]` | **A: Init/Feedback** | _init_0, EVENTS0[3] | — |
| `EVENTS0[1]` | `= _thread_0_event_counter_1_q == 2'd2` | **B variant: Multi-cycle counter** | EVENTS0[0] | counter == 2 |
| `EVENTS0[2]` | `= EVENTS0[1] && !thread_0_wire$1` | **D: Branch (false)** | EVENTS0[1] | `!thread_0_wire$1` (always false) |
| `EVENTS0[3]` | `= _thread_0_event_counter_3_1_q` | **B: Counter (1-cycle delay)** | EVENTS0[1] | — |

**Multi-cycle counter detail (`_thread_0_event_counter_1`):**
- Width: `logic[1:0]` (2-bit counter)
- Fires when: `_q == 2'd2`
- Next-state logic (chained ternary):
  - `EVENTS0[0]` fires → load `2'd1` (start counting)
  - `EVENTS0[1]` fires → clear to `'0` (done, reset counter)
  - `_q != 0` → increment (`_q + 2'd1`)
  - Otherwise → hold at 0 (idle)
- Cycle count: EVENTS0[0] fires → counter loads 1 → next cycle counter becomes 2 → `== 2'd2` is true → EVENTS0[1] fires. That is a **2-cycle delay** from EVENTS0[0] to EVENTS0[1].

**Event graph:**
```
_init_0 --> EVENTS0[0] --[2-cycle counter]--> EVENTS0[1]
                ^                                |
                |                        +-------+-------+
                |                        |               |
                |                  (wire$1=true)   (!wire$1=false)
                |                        |               |
                |                   [1-cycle delay]  EVENTS0[2] [DEAD]
                |                        |           ($display)
                |                   EVENTS0[3]
                |                   ($finish)
                |________________________|
                        (feedback)
```

Feedback loop present: `EVENTS0[0]` feeds back from `EVENTS0[3]`. However, `EVENTS0[3]` triggers `$finish`, so the loop only executes once before simulation terminates.

### Phase 3 Analysis

**Datapath:** `thread_0_wire$0 = 1'b1` (used in `$display`), `thread_0_wire$1 = 1'b1` (branch condition).

**Scheduling:** 4 events. Multi-cycle counter provides 2-cycle delay from event 0 to event 1. Branch at event 1 (always-true). 1-cycle delay from event 1 to event 3.

**Sequential actions by event:**

| Event | Action |
|---|---|
| EVENTS0[3] | `$finish` (terminate simulation) |
| EVENTS0[2] | `$display("Value is %d", 1)` (dead — never fires) |

### Phase 4 Analysis

**States:**

- **S0: Init / Start Counter** — Entered via `_init_0` (first cycle) or feedback from S2. Action: counter loads `2'd1` (begins counting). No register updates.
- **S1: Counter Reached — Branch** — Entered when counter `== 2'd2` (2 cycles after S0). EVENTS0[1] fires. Branch on `thread_0_wire$1` (always true) → EVENTS0[3] path. Counter clears to 0. EVENTS0[2] (false branch with `$display`) is dead code.
- **S2: Finish** — 1 cycle after S1 (via counter at EVENTS0[3]). Action: `$finish`. Feeds back to S0 combinationally, but `$finish` ends simulation first.

### Phase 5 Output

```
=== FSM Description: Top ===

--- Interface ---
Inputs:  (none besides clock/reset)
Outputs: (none)
Clock:   clk_i (posedge)
Reset:   rst_ni (active-low, asynchronous)

--- Registers ---
(no state registers)
_thread_0_event_counter_1_q [2] - reset value: 0 - multi-cycle delay counter
_thread_0_event_counter_3_1_q [1] - reset value: 0 - 1-cycle delay counter

--- States ---
S0: Init / Start Counter
  Entry: _init_0 one-shot (first cycle) OR feedback from S2
  Actions: counter_1 loads 2'd1 (start counting)
  Transitions:
    -> S1 [after 2-cycle delay, when counter_1 == 2'd2]

S1: Counter Reached — Branch
  Entry: counter_1_q == 2'd2 (2 cycles after S0)
  Actions: counter_1 clears to 0
  Transitions:
    -> S2 [unconditional, 1-cycle delay via counter_3]
    -> (dead branch: $display, never taken since !thread_0_wire$1 = false)

S2: Finish
  Entry: 1 cycle after S1
  Actions: $finish (terminate simulation)
  Transitions:
    -> S0 [combinational feedback, but $finish halts simulation]

--- Reset Behavior ---
On reset (rst_ni = 0):
  _init_0         <= 1'b1
  counter_1_q     <= 2'b00
  counter_3_1_q   <= 1'b0
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
Cycle 0 (first posedge after reset release):
  _init_0=1 -> EVENTS0[0]=1 -> counter_1_n=2'd1, _init_0 <= 0
Cycle 1:
  counter_1_q=2'd1 -> != 2'd2 -> EVENTS0[1]=0
  counter_1_n = 2'd1 + 2'd1 = 2'd2 (increment)
Cycle 2:
  counter_1_q=2'd2 -> EVENTS0[1]=1 -> counter_1_n='0 (clear)
  Branch: thread_0_wire$1=1 -> EVENTS0[3] path taken
  counter_3_1_n=1
Cycle 3:
  counter_3_1_q=1 -> EVENTS0[3]=1 -> $finish (simulation ends)
  EVENTS0[0]=1 (feedback), but $finish terminates first.

--- Notes ---
- EVENTS0[2] ($display branch) is dead code: thread_0_wire$1 = 1'b1
  makes !thread_0_wire$1 always false.
- The multi-cycle counter at index 1 uses a 2-bit register with
  comparison (== 2'd2) instead of the standard 1-bit Pattern B.
  It provides a 2-cycle delay from EVENTS0[0] to EVENTS0[1].
- This FSM runs exactly once (3 cycles) then terminates via $finish.
- Despite the feedback loop, $finish prevents a second iteration.
```

---

## Worked Example 4: Multi-Module Design with Selector (Code 10)

### Input Code

This example contains two modules: `Sub` (a responder with branching and output selector) and `Top` (which instantiates `Sub` and runs a simple loop with `$finish`).

**Module Sub:**
```systemverilog
module Sub (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni,
  output logic[0:0] _e_req_ack,
  input logic[0:0] _e_req_valid,
  input logic[0:0] _e_req_0,
  input logic[0:0] _e_resp_ack,
  output logic[0:0] _e_resp_valid,
  output logic[0:0] _e_resp_0
);
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  logic[0:0] thread_0_wire$1;
  logic[0:0] thread_0_wire$0;
  assign thread_0_wire$0 = _e_req_valid;
  assign thread_0_wire$1 = _e_req_0;
  localparam logic[0:0] thread_0_wire$2 = 1'b1;
  localparam logic[0:0] thread_0_wire$3 = 1'b1;
  localparam logic[0:0] thread_0_wire$4 = 1'b0;
  for (genvar i = 0; i < 11; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_syncstate_9_q, _thread_0_event_syncstate_9_n;
  logic _thread_0_event_counter_8_1_q, _thread_0_event_counter_8_1_n;
  logic _thread_0_event_syncstate_6_q, _thread_0_event_syncstate_6_n;
  logic _thread_0_event_counter_5_1_q, _thread_0_event_counter_5_1_n;
  logic _thread_0_event_counter_2_1_q, _thread_0_event_counter_2_1_n;
  assign EVENTS0[10].event_current = EVENTS0[9].event_current || EVENTS0[6].event_current || EVENTS0[2].event_current;
  assign EVENTS0[9].event_current = (EVENTS0[8].event_current || _thread_0_event_syncstate_9_q) && _e_resp_ack;
    assign _thread_0_event_syncstate_9_n = (EVENTS0[8].event_current || _thread_0_event_syncstate_9_q) && !_e_resp_ack;
  assign EVENTS0[8].event_current = _thread_0_event_counter_8_1_q;
  assign _thread_0_event_counter_8_1_n = EVENTS0[7].event_current;
  assign EVENTS0[7].event_current = EVENTS0[3].event_current && thread_0_wire$2;
  assign EVENTS0[6].event_current = (EVENTS0[5].event_current || _thread_0_event_syncstate_6_q) && _e_resp_ack;
    assign _thread_0_event_syncstate_6_n = (EVENTS0[5].event_current || _thread_0_event_syncstate_6_q) && !_e_resp_ack;
  assign EVENTS0[5].event_current = _thread_0_event_counter_5_1_q;
  assign _thread_0_event_counter_5_1_n = EVENTS0[4].event_current;
  assign EVENTS0[4].event_current = EVENTS0[3].event_current && !thread_0_wire$2;
  assign EVENTS0[3].event_current = EVENTS0[0].event_current && thread_0_wire$0;
  assign EVENTS0[2].event_current = _thread_0_event_counter_2_1_q;
  assign _thread_0_event_counter_2_1_n = EVENTS0[1].event_current;
  assign EVENTS0[1].event_current = EVENTS0[0].event_current && !thread_0_wire$0;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[10].event_current;
  assign _e_req_ack = EVENTS0[3].event_current;
  assign _e_resp_valid = (EVENTS0[5].event_current || _thread_0_event_syncstate_6_q) || (EVENTS0[8].event_current || _thread_0_event_syncstate_9_q);
  logic[0:0] _e_resp_valid_selector_q, _e_resp_valid_selector_n;
  assign _e_resp_0 = (_e_resp_valid_selector_n == 1'd0) ? thread_0_wire$4 : (_e_resp_valid_selector_n == 1'd1) ? thread_0_wire$3 : '0;
  always_comb begin: _thread_0_selector
    _e_resp_valid_selector_n = _e_resp_valid_selector_q;
    if ((EVENTS0[5].event_current || _thread_0_event_syncstate_6_q)) _e_resp_valid_selector_n = 1'd0;
    if ((EVENTS0[8].event_current || _thread_0_event_syncstate_9_q)) _e_resp_valid_selector_n = 1'd1;
  end
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_selector_trans
    if (~rst_ni) begin
      _e_resp_valid_selector_q <= '0;
    end else begin
      _e_resp_valid_selector_q <= _e_resp_valid_selector_n;
    end
  end
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      _thread_0_event_syncstate_9_q <= '0;
      _thread_0_event_counter_8_1_q <= '0;
      _thread_0_event_syncstate_6_q <= '0;
      _thread_0_event_counter_5_1_q <= '0;
      _thread_0_event_counter_2_1_q <= '0;
    end else begin
      if (EVENTS0[3].event_current) begin
      end
      _init_0 <= 1'b0;
      _thread_0_event_syncstate_9_q <= _thread_0_event_syncstate_9_n;
      _thread_0_event_counter_8_1_q <= _thread_0_event_counter_8_1_n;
      _thread_0_event_syncstate_6_q <= _thread_0_event_syncstate_6_n;
      _thread_0_event_counter_5_1_q <= _thread_0_event_counter_5_1_n;
      _thread_0_event_counter_2_1_q <= _thread_0_event_counter_2_1_n;
    end
  end
endmodule
```

**Module Top:**
```systemverilog
module Top (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni
);
  logic[0:0] _le_req_ack;
  logic[0:0] _le_req_valid;
  logic[0:0] _le_req_0;
  logic[0:0] _le_resp_ack;
  logic[0:0] _le_resp_valid;
  logic[0:0] _le_resp_0;
  Sub _spawn_0 (
    .clk_i,
    .rst_ni
    ,._e_resp_valid (_le_resp_valid)
    ,._e_resp_ack (_le_resp_ack)
    ,._e_resp_0 (_le_resp_0)
    ,._e_req_valid (_le_req_valid)
    ,._e_req_ack (_le_req_ack)
    ,._e_req_0 (_le_req_0)
  );
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  for (genvar i = 0; i < 2; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_1_1_q, _thread_0_event_counter_1_1_n;
  assign EVENTS0[1].event_current = _thread_0_event_counter_1_1_q;
  assign _thread_0_event_counter_1_1_n = EVENTS0[0].event_current;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[1].event_current;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      _thread_0_event_counter_1_1_q <= '0;
    end else begin
      if (EVENTS0[1].event_current) begin
        $finish;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_1_1_q <= _thread_0_event_counter_1_1_n;
    end
  end
endmodule
```

### Phase 1 Analysis — Module Sub

**Ports:**

| Port | Direction | Width | Classification |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Reset (active-low) |
| `_e_req_valid` | input | 1 | Data Input (request handshake valid) |
| `_e_req_0` | input | 1 | Data Input (request data) |
| `_e_req_ack` | output | 1 | Data Output (request handshake ack) |
| `_e_resp_ack` | input | 1 | Data Input (response handshake ack) |
| `_e_resp_valid` | output | 1 | Data Output (response handshake valid) |
| `_e_resp_0` | output | 1 | Data Output (response data) |

**Internal Signals:**

| Signal | Classification |
|---|---|
| `thread_0_wire$0` | Datapath wire (assign = `_e_req_valid`) — runtime condition |
| `thread_0_wire$1` | Datapath wire (assign = `_e_req_0`) — runtime data |
| `thread_0_wire$2` | Datapath wire (localparam = `1'b1`) — branch condition |
| `thread_0_wire$3` | Datapath wire (localparam = `1'b1`) — response data for true branch |
| `thread_0_wire$4` | Datapath wire (localparam = `1'b0`) — response data for false branch |
| `_init_0` | Init one-shot |
| `_thread_0_event_counter_2_1_q/_n` | Event counter at index 2 |
| `_thread_0_event_counter_5_1_q/_n` | Event counter at index 5 |
| `_thread_0_event_counter_8_1_q/_n` | Event counter at index 8 |
| `_thread_0_event_syncstate_6_q/_n` | Sync state at index 6 |
| `_thread_0_event_syncstate_9_q/_n` | Sync state at index 9 |
| `_e_resp_valid_selector_q/_n` | Output selector register |

### Phase 1 Analysis — Module Top

**Ports:**

| Port | Direction | Width | Classification |
|---|---|---|---|
| `clk_i` | input | 1 | Clock |
| `rst_ni` | input | 1 | Reset (active-low) |

**Internal Signals:**

| Signal | Classification |
|---|---|
| `_le_req_ack`, `_le_req_valid`, `_le_req_0` | Inter-module wires (request channel to Sub) |
| `_le_resp_ack`, `_le_resp_valid`, `_le_resp_0` | Inter-module wires (response channel from Sub) |
| `_init_0` | Init one-shot |
| `_thread_0_event_counter_1_1_q/_n` | Event counter at index 1 |

**Sub-module instantiation:** `Sub _spawn_0` with named port connections mapping `_le_*` signals to Sub's `_e_*` ports.

### Phase 2 Analysis — Module Sub

**EVENTS0 has 11 elements (indices 0..10).**

| Event | Assign Statement | Pattern | Predecessor(s) | Condition |
|---|---|---|---|---|
| `EVENTS0[0]` | `= _init_0 \|\| EVENTS0[10]` | **A: Init/Feedback** | _init_0, EVENTS0[10] | — |
| `EVENTS0[1]` | `= EVENTS0[0] && !thread_0_wire$0` | **D: Branch (false)** | EVENTS0[0] | `!_e_req_valid` |
| `EVENTS0[2]` | `= _thread_0_event_counter_2_1_q` | **B: Counter** | EVENTS0[1] | — |
| `EVENTS0[3]` | `= EVENTS0[0] && thread_0_wire$0` | **D: Branch (true)** | EVENTS0[0] | `_e_req_valid` |
| `EVENTS0[4]` | `= EVENTS0[3] && !thread_0_wire$2` | **D: Branch (false)** | EVENTS0[3] | `!1'b1` (always false) |
| `EVENTS0[5]` | `= _thread_0_event_counter_5_1_q` | **B: Counter** | EVENTS0[4] | — |
| `EVENTS0[6]` | `= (EVENTS0[5] \|\| syncstate_6_q) && _e_resp_ack` | **C: Sync State** | EVENTS0[5] | `_e_resp_ack` |
| `EVENTS0[7]` | `= EVENTS0[3] && thread_0_wire$2` | **D: Branch (true)** | EVENTS0[3] | `1'b1` (always true) |
| `EVENTS0[8]` | `= _thread_0_event_counter_8_1_q` | **B: Counter** | EVENTS0[7] | — |
| `EVENTS0[9]` | `= (EVENTS0[8] \|\| syncstate_9_q) && _e_resp_ack` | **C: Sync State** | EVENTS0[8] | `_e_resp_ack` |
| `EVENTS0[10]` | `= EVENTS0[9] \|\| EVENTS0[6] \|\| EVENTS0[2]` | **E: Merge (3-way)** | EVENTS0[9], EVENTS0[6], EVENTS0[2] | — |

**Event graph:**
```
_init_0 --> EVENTS0[0] --------+------ branch on _e_req_valid ------+
                ^               |                                     |
                |          (_e_req_valid=1)                    (!_e_req_valid)
                |               |                                     |
                |          EVENTS0[3] --+-- branch on wire$2 --+  EVENTS0[1]
                |          (_e_req_ack=1)|                      |      |
                |                  (wire$2=true)        (!wire$2=false)[1-cycle]
                |                       |                [DEAD] |      |
                |                  EVENTS0[7]           EVENTS0[4] EVENTS0[2]
                |                       |                   |         |
                |                  [1-cycle]            [1-cycle]     |
                |                       |                   |         |
                |                  EVENTS0[8]           EVENTS0[5]    |
                |                       |                   |         |
                |               [sync: _e_resp_ack]  [sync: _e_resp_ack]
                |                       |              [DEAD] |       |
                |                  EVENTS0[9]           EVENTS0[6]    |
                |                       |                   |         |
                |                       +-------+-----------+---------+
                |                               |
                |                          EVENTS0[10] (3-way merge)
                |_______________________________|
                           (feedback)
```

**Key observations:**
- First branch at EVENTS0[0] is on `_e_req_valid` (runtime signal — NOT constant).
- Second branch at EVENTS0[3] is on `thread_0_wire$2 = 1'b1` (constant true), so EVENTS0[4] (false path) is dead code. EVENTS0[5], EVENTS0[6] are also dead.
- The live path is: EVENTS0[0] → (if `_e_req_valid`) → EVENTS0[3] → EVENTS0[7] → EVENTS0[8] → (wait `_e_resp_ack`) → EVENTS0[9] → EVENTS0[10] → feedback.
- The no-request path is: EVENTS0[0] → (if `!_e_req_valid`) → EVENTS0[1] → EVENTS0[2] → EVENTS0[10] → feedback.

**Selector pattern:**
- `_e_resp_valid_selector_n` is updated combinationally: set to `0` when the false-branch resp path is active (EVENTS0[5]/syncstate_6), set to `1` when the true-branch resp path is active (EVENTS0[8]/syncstate_9).
- `_e_resp_0` mux: selector `0` → `thread_0_wire$4 = 1'b0`, selector `1` → `thread_0_wire$3 = 1'b1`.
- Since only the true branch (selector=1) is live, `_e_resp_0` will always be `1'b1` in practice.

### Phase 2 Analysis — Module Top

**EVENTS0 has 2 elements (indices 0..1).**

| Event | Assign Statement | Pattern | Predecessor(s) | Condition |
|---|---|---|---|---|
| `EVENTS0[0]` | `= _init_0 \|\| EVENTS0[1]` | **A: Init/Feedback** | _init_0, EVENTS0[1] | — |
| `EVENTS0[1]` | `= _thread_0_event_counter_1_1_q` | **B: Counter** | EVENTS0[0] | — |

Simple 2-event loop with feedback. Same structure as Worked Example 1.

### Phase 3 Analysis — Module Sub

**Datapath:**

| Wire | Type | Value / Expression | Purpose |
|---|---|---|---|
| `thread_0_wire$0` | assign | `_e_req_valid` | Runtime branch condition |
| `thread_0_wire$1` | assign | `_e_req_0` | Runtime request data (unused in actions) |
| `thread_0_wire$2` | localparam | `1'b1` | Second branch condition (always true) |
| `thread_0_wire$3` | localparam | `1'b1` | Response data for true branch |
| `thread_0_wire$4` | localparam | `1'b0` | Response data for false branch |

**Scheduling:** 11 events. Two levels of branching, three counter delays, two sync waits, one 3-way merge.

**Sequential actions by event:**

| Event | Action |
|---|---|
| EVENTS0[3] | (empty block — no register update, but `_e_req_ack` is asserted combinationally) |

**Outputs:**
- `_e_req_ack = EVENTS0[3]` — ack pulses for one cycle when request is accepted.
- `_e_resp_valid = (EVENTS0[5] || syncstate_6_q) || (EVENTS0[8] || syncstate_9_q)` — asserted while waiting for response ack (on either branch).
- `_e_resp_0` — driven by selector mux: `0` if false branch active, `1` if true branch active.

### Phase 3 Analysis — Module Top

**Datapath:** None (no localparams or wires).

**Scheduling:** 2 events in a loop.

**Sequential actions by event:**

| Event | Action |
|---|---|
| EVENTS0[1] | `$finish` (terminate simulation) |

### Phase 4 Analysis — Module Sub

**States:**

- **S0: Wait for Request** — EVENTS0[0] fires (via `_init_0` or feedback). Branch on `_e_req_valid`:
  - If `_e_req_valid = 1` → EVENTS0[3] fires (same cycle). `_e_req_ack` asserted. Transition to S1.
  - If `_e_req_valid = 0` → EVENTS0[1] fires (same cycle). Transition to S_skip.
- **S_skip: No-Request Delay** — EVENTS0[2] fires (1 cycle after EVENTS0[1] via counter). EVENTS0[10] (merge) fires same cycle. Feeds back to S0. This path provides a 1-cycle idle loop when no request is pending.
- **S1: Process Request — True Branch Delay** — same cycle as EVENTS0[3]/EVENTS0[7] fires (combinational, since `thread_0_wire$2=1`). EVENTS0[8] fires via counter.
- **S2: Wait for Response Ack (True Branch)** — EVENTS0[8] active, sync wait on `_e_resp_ack`. `_e_resp_valid` asserted, selector=1, `_e_resp_0 = 1'b1`. When `_e_resp_ack` received → EVENTS0[9] fires → EVENTS0[10] (merge) → feedback to S0.

**Note:** Dead states from the false branch (EVENTS0[4] → EVENTS0[5] → EVENTS0[6]) are omitted since `thread_0_wire$2 = 1'b1` makes that path unreachable.

### Phase 4 Analysis — Module Top

**States:**

- **S0: Init** — EVENTS0[0] fires. No actions. Counter starts.
- **S1: Finish** — EVENTS0[1] fires (1 cycle after S0). Action: `$finish`. Feeds back to S0, but `$finish` halts simulation.

### Phase 5 Output

```
=== FSM Description: Sub ===

--- Interface ---
Inputs:  _e_req_valid [1] - Request handshake valid
         _e_req_0 [1] - Request data
         _e_resp_ack [1] - Response handshake ack from consumer
Outputs: _e_req_ack [1] - Request ack (pulses when request accepted)
         _e_resp_valid [1] - Response valid (asserted while waiting for resp ack)
         _e_resp_0 [1] - Response data (muxed by selector: 0 or 1)
Clock:   clk_i (posedge)
Reset:   rst_ni (active-low, asynchronous)

--- Registers ---
_e_resp_valid_selector_q [1] - reset value: 0 - tracks which branch drives response
(no state registers — all behavior is in event scheduling and outputs)

--- Output Selector ---
_e_resp_0 is driven by a combinational mux:
  selector_n == 0 -> thread_0_wire$4 = 1'b0 (false branch data)
  selector_n == 1 -> thread_0_wire$3 = 1'b1 (true branch data)
The selector updates to 0 when the false-branch resp path is active,
and to 1 when the true-branch resp path is active.

--- States ---
S0: Wait for Request
  Entry: _init_0 one-shot OR feedback from S2/S_skip
  Actions: (none)
  Outputs: _e_req_ack = 0, _e_resp_valid = 0
  Transitions:
    -> S1 [when _e_req_valid = 1; _e_req_ack pulses this cycle; S1 entered same cycle (EVENTS0[3] and EVENTS0[7] fire combinationally)]
    -> S_skip [when _e_req_valid = 0, same cycle]

S_skip: No-Request Idle
  Entry: same cycle as S0 when _e_req_valid = 0
  Actions: (none)
  Transitions:
    -> S0 [after 1-cycle delay via counter_2, combinational feedback through merge]

S1: Response Delay (True Branch)
  Entry: same cycle as request accepted (EVENTS0[3] and EVENTS0[7] fire combinationally)
  Actions: (none)
  Outputs: _e_resp_valid = 0
  Transitions:
    -> S2 [unconditional, enters sync wait]

S2: Wait for Response Ack (True Branch)
  Entry: EVENTS0[8] fires, enters sync wait on _e_resp_ack
  Actions: (none)
  Outputs: _e_resp_valid = 1, _e_resp_0 = 1 (selector=1, true branch)
  Transitions:
    -> S2 [while _e_resp_ack = 0, hold via syncstate_9]
    -> S0 [when _e_resp_ack = 1, via merge EVENTS0[10] -> feedback]

--- Reset Behavior ---
On reset (rst_ni = 0):
  _init_0          <= 1'b1
  counter_2_1_q    <= 1'b0
  counter_5_1_q    <= 1'b0
  counter_8_1_q    <= 1'b0
  syncstate_6_q    <= 1'b0
  syncstate_9_q    <= 1'b0
  selector_q       <= 1'b0
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
Cycle 0: _init_0=1 -> EVENTS0[0]=1.
  If _e_req_valid=1: EVENTS0[3]=1 -> _e_req_ack=1, EVENTS0[7]=1
    counter_8_1_n=1. Selector_n=1.
  If _e_req_valid=0: EVENTS0[1]=1 -> counter_2_1_n=1.
Cycle 1 (assuming req_valid=1 at cycle 0):
  counter_8_1_q=1 -> EVENTS0[8]=1 -> _e_resp_valid=1.
  If _e_resp_ack=0: syncstate_9_n=1 (hold).
  If _e_resp_ack=1: EVENTS0[9]=1 -> EVENTS0[10]=1 -> EVENTS0[0]=1 (feedback).
Cycle 1 (assuming req_valid=0 at cycle 0):
  counter_2_1_q=1 -> EVENTS0[2]=1 -> EVENTS0[10]=1 -> EVENTS0[0]=1 (feedback).
  Back to S0, checking _e_req_valid again.

--- Notes ---
- EVENTS0[4] (false branch of second split) is dead code:
  thread_0_wire$2 = 1'b1, so !thread_0_wire$2 = 0.
  EVENTS0[5] and EVENTS0[6] are also dead (downstream of EVENTS0[4]).
- The 3-way merge at EVENTS0[10] joins the true-branch response path,
  the dead false-branch response path, and the no-request idle path.
- The selector pattern determines _e_resp_0 output data. In practice,
  only selector=1 (true branch, data=1) is reachable.
```

```
=== FSM Description: Top ===

--- Interface ---
Inputs:  (none besides clock/reset)
Outputs: (none — all I/O is through Sub instance)
Clock:   clk_i (posedge)
Reset:   rst_ni (active-low, asynchronous)

--- Sub-Module Instantiation ---
Instance: _spawn_0 (type: Sub)
  Port Mapping:
    Sub._e_req_valid  <-> Top._le_req_valid
    Sub._e_req_ack    <-> Top._le_req_ack
    Sub._e_req_0      <-> Top._le_req_0
    Sub._e_resp_valid <-> Top._le_resp_valid
    Sub._e_resp_ack   <-> Top._le_resp_ack
    Sub._e_resp_0     <-> Top._le_resp_0
  Channels:
    Request channel:  Top drives _le_req_valid, _le_req_0 -> Sub; Sub drives _le_req_ack -> Top
    Response channel: Sub drives _le_resp_valid, _le_resp_0 -> Top; Top drives _le_resp_ack -> Sub
  Note: Top's EVENTS0 chain does NOT drive any of these signals.
        The _le_* wires are declared but not assigned by Top's event logic.

--- Registers ---
(none)

--- States ---
S0: Init
  Entry: _init_0 one-shot OR feedback from S1
  Actions: (none)
  Transitions:
    -> S1 [unconditional, 1-cycle delay]

S1: Finish
  Entry: 1 cycle after S0
  Actions: $finish (terminate simulation)
  Transitions:
    -> S0 [combinational feedback, but $finish halts simulation]

--- Reset Behavior ---
On reset (rst_ni = 0):
  _init_0         <= 1'b1
  counter_1_1_q   <= 1'b0
  FSM begins in S0 via _init_0 one-shot.

--- Timing ---
Cycle 0: _init_0=1 -> EVENTS0[0]=1 -> counter_1_1_n=1, _init_0 <= 0
Cycle 1: counter_1_1_q=1 -> EVENTS0[1]=1 -> $finish
         Simulation terminates.

--- Notes ---
- Top's own FSM is trivial: init, then $finish after 1 cycle.
- Sub runs concurrently. Whether Sub completes any request/response
  handshake depends on the _le_* signal drivers (which Top does NOT
  drive from its event chain — they are left undriven/default).
- In a real system, another module or testbench would drive the
  request/response channels. Here, $finish stops simulation immediately.
```

---

## Summary of Analysis Methodology

1. **Parse** — Extract ports, signals, constants. Resolve all localparams.
2. **Decode** — Map every EVENTS assign to a pattern (A-F). Build the event graph.
3. **Modularize** — Separate datapath (wires/constants), scheduling (event assigns), sequential (always_ff).
4. **Extract** — Identify states at clock boundaries (counters, sync states). Define transitions, actions, outputs.
5. **Format** — Produce the structured FSM description with interface, states, reset, timing, and notes.

Always verify your analysis by mentally simulating the first few clock cycles after reset. The `_init_0` one-shot should seed the chain, events should propagate correctly through counters (with 1-cycle delays) and sync states (with blocking waits), and register updates should match the guarded `if` blocks in the sequential logic.
