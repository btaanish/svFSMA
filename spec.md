# Project Specification

## What do you want to build?

Need to create an agen’t spec.md, such that the agent is able to take in, read and understand system verilog code, modularise it and then create FSMs for it. Then actually test that the description works by creating an agent with that description and test if it is actually able to convert the SV code to its corresponding modular FSMs

## How do you consider the project is success?

The goal is succesful only if the agent created from the description is able to create FSMs for the following System Verilog Codes:
Code 1:
/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
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

Code 2:
/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
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
