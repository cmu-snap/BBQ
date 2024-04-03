`timescale 1 ps / 1 ps

import pieo_datatypes::*;

module top (
  input  in_clk100,
  input  cpu_resetn,
  output logic pieo_out
);

wire rst, user_clk;
assign rst = ~cpu_resetn;

my_pll user_pll (
  .rst      (~cpu_resetn),
  .refclk   (in_clk100),
  .locked   (),
  .outclk_0 (user_clk)
);

logic pieo_reset_done_out;

logic start;

logic pieo_ready_for_nxt_op_out;

logic enqueue_f_in;
SublistElement f_in;
logic enq_valid_out;
logic [$clog2(NUM_OF_SUBLIST):0] f_enqueued_in_sublist_out;

logic dequeue_in;
logic [TIME_LOG-1:0] curr_time_in;

logic dequeue_f_in;
logic [ID_LOG-1:0] flow_id_in;
logic [$clog2(NUM_OF_SUBLIST)-1:0] sublist_id_in;

logic deq_valid_out;
SublistElement deq_element_out;

logic [ID_LOG:0] flow_id_moved_out;
logic [$clog2(NUM_OF_SUBLIST):0] flow_id_moved_to_sublist_out;

always_ff @(posedge user_clk) begin
  if (rst) begin
    start <= 0;
    enqueue_f_in <= 0;
    f_in <= 0;
    dequeue_in <= 0;
    curr_time_in <= 0;
    dequeue_f_in <= 0;
    flow_id_in <= 0;
    sublist_id_in <= 0;
  end else begin
    start <= !start;
    enqueue_f_in <= !enqueue_f_in;
    f_in <= f_in + 1;
    dequeue_in <= !dequeue_in;
    curr_time_in <= curr_time_in + 1;
    dequeue_f_in <= !dequeue_f_in;
    flow_id_in <= flow_id_in + 1;
    sublist_id_in <= sublist_id_in + 1;
  end
end

logic [31:0] out_placeholder;
logic pieo_out_r;

// Make sure we use all the outputs
always_comb begin
  out_placeholder = 0;
  out_placeholder ^= f_enqueued_in_sublist_out;
  out_placeholder ^= deq_element_out;
  out_placeholder ^= flow_id_moved_out;
  out_placeholder ^= flow_id_moved_to_sublist_out;

  pieo_out_r = ^out_placeholder;
  pieo_out_r ^= pieo_reset_done_out;
  pieo_out_r ^= pieo_ready_for_nxt_op_out;
  pieo_out_r ^= deq_valid_out;
end

always_ff @(posedge user_clk) begin
  pieo_out <= pieo_out_r;
end

pieo pieo_inst (
  .clk                          (user_clk),
  .rst                          (rst),
  .pieo_reset_done_out          (pieo_reset_done_out),
  .start                        (start),
  .pieo_ready_for_nxt_op_out    (pieo_ready_for_nxt_op_out),
  .enqueue_f_in                 (enqueue_f_in),
  .f_in                         (f_in),
  .enq_valid_out                (enq_valid_out),
  .f_enqueued_in_sublist_out    (f_enqueued_in_sublist_out),
  .dequeue_in                   (dequeue_in),
  .curr_time_in                 (curr_time_in),
  .dequeue_f_in                 (dequeue_f_in),
  .flow_id_in                   (flow_id_in),
  .sublist_id_in                (sublist_id_in),
  .deq_valid_out                (deq_valid_out),
  .deq_element_out              (deq_element_out),
  .flow_id_moved_out            (flow_id_moved_out),
  .flow_id_moved_to_sublist_out (flow_id_moved_to_sublist_out)
);

endmodule
