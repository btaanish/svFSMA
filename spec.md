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

Code 4:
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
Code 5:
Copy
/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
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
Code 6:


Copy
/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
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
  for (genvar i = 0; i < 3; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_2_1_q, _thread_0_event_counter_2_1_n;
  assign EVENTS0[2].event_current = _thread_0_event_counter_2_1_q;
  assign _thread_0_event_counter_2_1_n = EVENTS0[0].event_current;
  assign EVENTS0[1].event_current = EVENTS0[0].event_current && !thread_0_wire$1;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[2].event_current;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      _thread_0_event_counter_2_1_q <= '0;
    end else begin
      if (EVENTS0[2].event_current) begin
        $finish;
      end
      if (EVENTS0[1].event_current) begin
        $display("Value is %d", thread_0_wire$0);
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_2_1_q <= _thread_0_event_counter_2_1_n;
    end
  end
endmodule
Code 7:




/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
module concurrent (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni
);
  logic[0:0] r_q;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  logic[0:0] thread_0_wire$2;
  localparam logic[0:0] thread_0_wire$0 = 1'b1;
  localparam logic[0:0] thread_0_wire$1 = 1'b0;
  assign thread_0_wire$2 = r_q;
  for (genvar i = 0; i < 3; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_2_1_q, _thread_0_event_counter_2_1_n;
  logic _thread_0_event_counter_1_1_q, _thread_0_event_counter_1_1_n;
  assign EVENTS0[2].event_current = _thread_0_event_counter_2_1_q;
  assign _thread_0_event_counter_2_1_n = EVENTS0[1].event_current;
  assign EVENTS0[1].event_current = _thread_0_event_counter_1_1_q;
  assign _thread_0_event_counter_1_1_n = EVENTS0[0].event_current;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[2].event_current;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      r_q <= '0;
      _thread_0_event_counter_2_1_q <= '0;
      _thread_0_event_counter_1_1_q <= '0;
    end else begin
      if (EVENTS0[2].event_current) begin
        $display("Value = %d", thread_0_wire$2);
      end
      if (EVENTS0[1].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$1;
      end
      if (EVENTS0[0].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$0;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_2_1_q <= _thread_0_event_counter_2_1_n;
      _thread_0_event_counter_1_1_q <= _thread_0_event_counter_1_1_n;
    end
  end
endmodule
Code 8:




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
  logic[0:0] thread_0_wire$2;
  localparam logic[0:0] thread_0_wire$0 = 1'b1;
  localparam logic[0:0] thread_0_wire$1 = 1'b1;
  assign thread_0_wire$2 = r_q;
  for (genvar i = 0; i < 6; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_4_1_q, _thread_0_event_counter_4_1_n;
  logic _thread_0_event_counter_2_1_q, _thread_0_event_counter_2_1_n;
  assign EVENTS0[5].event_current = EVENTS0[2].event_current || EVENTS0[4].event_current;
  assign EVENTS0[4].event_current = _thread_0_event_counter_4_1_q;
  assign _thread_0_event_counter_4_1_n = EVENTS0[3].event_current;
  assign EVENTS0[3].event_current = EVENTS0[0].event_current && !thread_0_wire$0;
  assign EVENTS0[2].event_current = _thread_0_event_counter_2_1_q;
  assign _thread_0_event_counter_2_1_n = EVENTS0[1].event_current;
  assign EVENTS0[1].event_current = EVENTS0[0].event_current && thread_0_wire$0;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[5].event_current;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      r_q <= '0;
      _thread_0_event_counter_4_1_q <= '0;
      _thread_0_event_counter_2_1_q <= '0;
    end else begin
      if (EVENTS0[4].event_current) begin
        $display("Value = %d", thread_0_wire$2);
      end
      if (EVENTS0[1].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$1;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_4_1_q <= _thread_0_event_counter_4_1_n;
      _thread_0_event_counter_2_1_q <= _thread_0_event_counter_2_1_n;
    end
  end
endmodule
Code 9:




/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
module reggg (
  input logic[0:0] clk_i,
  input logic[0:0] rst_ni,
  output logic[0:0] _e_req_ack,
  input logic[0:0] _e_req_valid,
  input logic[0:0] _e_req_0
);
  always_ff @(posedge clk_i or negedge rst_ni) begin : _proc_transition
    if (~rst_ni) begin
    end
  end
  logic[0:0] thread_0_wire$0;
  assign thread_0_wire$0 = _e_req_0;
  for (genvar i = 0; i < 3; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_2_1_q, _thread_0_event_counter_2_1_n;
  logic _thread_0_event_syncstate_1_q, _thread_0_event_syncstate_1_n;
  assign EVENTS0[2].event_current = _thread_0_event_counter_2_1_q;
  assign _thread_0_event_counter_2_1_n = EVENTS0[1].event_current;
  assign EVENTS0[1].event_current = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q) && _e_req_valid;
    assign _thread_0_event_syncstate_1_n = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q) && !_e_req_valid;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[2].event_current;
  assign _e_req_ack = (EVENTS0[0].event_current || _thread_0_event_syncstate_1_q);
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      _thread_0_event_counter_2_1_q <= '0;
      _thread_0_event_syncstate_1_q <= '0;
    end else begin
      if (EVENTS0[1].event_current) begin
        $display("Received %d", thread_0_wire$0);
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_2_1_q <= _thread_0_event_counter_2_1_n;
      _thread_0_event_syncstate_1_q <= _thread_0_event_syncstate_1_n;
    end
  end
endmodule
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
  logic[0:0] thread_0_wire$1;
  localparam logic[0:0] thread_0_wire$0 = 1'b0;
  assign thread_0_wire$1 = r_q;
  localparam logic[0:0] thread_0_wire$2 = 1'b1;
  for (genvar i = 0; i < 5; i ++) begin : EVENTS0
    logic event_current;
    end
  logic _init_0;
  logic _thread_0_event_counter_4_1_q, _thread_0_event_counter_4_1_n;
  logic _thread_0_event_counter_3_1_q, _thread_0_event_counter_3_1_n;
  logic _thread_0_event_syncstate_2_q, _thread_0_event_syncstate_2_n;
  logic _thread_0_event_counter_1_1_q, _thread_0_event_counter_1_1_n;
  assign EVENTS0[4].event_current = _thread_0_event_counter_4_1_q;
  assign _thread_0_event_counter_4_1_n = EVENTS0[3].event_current;
  assign EVENTS0[3].event_current = _thread_0_event_counter_3_1_q;
  assign _thread_0_event_counter_3_1_n = EVENTS0[2].event_current;
  assign EVENTS0[2].event_current = (EVENTS0[1].event_current || _thread_0_event_syncstate_2_q) && _e_req_ack;
    assign _thread_0_event_syncstate_2_n = (EVENTS0[1].event_current || _thread_0_event_syncstate_2_q) && !_e_req_ack;
  assign EVENTS0[1].event_current = _thread_0_event_counter_1_1_q;
  assign _thread_0_event_counter_1_1_n = EVENTS0[0].event_current;
  assign EVENTS0[0].event_current = _init_0 || EVENTS0[4].event_current;
  assign _e_req_valid = (EVENTS0[1].event_current || _thread_0_event_syncstate_2_q);
  assign _e_req_0 = thread_0_wire$1;
  always_ff @(posedge clk_i or negedge rst_ni) begin : _thread_0_st_transition
    if (~rst_ni) begin
      _init_0 <= 1'b1;
      r_q <= '0;
      _thread_0_event_counter_4_1_q <= '0;
      _thread_0_event_counter_3_1_q <= '0;
      _thread_0_event_syncstate_2_q <= '0;
      _thread_0_event_counter_1_1_q <= '0;
    end else begin
      if (EVENTS0[3].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$2;
      end
      if (EVENTS0[0].event_current) begin
        r_q[0 +: 1] <= thread_0_wire$0;
      end
      _init_0 <= 1'b0;
      _thread_0_event_counter_4_1_q <= _thread_0_event_counter_4_1_n;
      _thread_0_event_counter_3_1_q <= _thread_0_event_counter_3_1_n;
      _thread_0_event_syncstate_2_q <= _thread_0_event_syncstate_2_n;
      _thread_0_event_counter_1_1_q <= _thread_0_event_counter_1_1_n;
    end
  end
endmodule
Code 10:
Copy
/* verilator lint_off UNOPTFLAT */
/* verilator lint_off WIDTHTRUNC */
/* verilator lint_off WIDTHEXPAND */
/* verilator lint_off WIDTHCONCAT */
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

