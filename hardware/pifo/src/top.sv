`timescale 1 ps / 1 ps

module top (
  input  in_clk100,
  input  cpu_resetn,
  output logic pifo_out
);

wire rst, user_clk;
assign rst = ~cpu_resetn;

my_pll user_pll (
  .rst      (~cpu_resetn),
  .refclk   (in_clk100),
  .locked   (),
  .outclk_0 (user_clk)
);

// Default values.
// localparam NUMPIFO = 1024;  // PIFO capacity.
// localparam BITPORT = 8;  // Number of bits to represent a logical PIFO.
// localparam BITPRIO = 16;  // Number of bits to represent priorities.
// localparam BITDATA = 32;  // Number of bits to represent data.
// localparam PIFO_ID = 0;

// Values from PANIC.
// localparam NUMPIFO = 128;
// localparam BITPORT = 1;
// localparam BITPRIO = 8;
// localparam BITDATA = $clog2(NUMPIFO);  // PANIC uses an extra array to store
//                                        // the actual data.
// localparam PIFO_ID = 0;

// Using PANIC values by default as they are quicker to synthesize.
`ifndef ELEMENT_BITS
`define ELEMENT_BITS 7
`endif  // ELEMENT_BITS

`ifndef PRIORITY_BITS
`define PRIORITY_BITS 8
`endif  // PRIORITY_BITS

localparam NUMPIFO = 2**(`ELEMENT_BITS);
localparam BITPORT = 1;
localparam BITPRIO = `PRIORITY_BITS;
localparam BITDATA = $clog2(NUMPIFO);
localparam PIFO_ID = 0;

logic               pop_0;
logic [BITPORT-1:0] oprt_0;
logic               ovld_0;
logic [BITPRIO-1:0] opri_0;
logic [BITDATA-1:0] odout_0;

logic               push_1;
logic [BITPORT-1:0] uprt_1;
logic [BITPRIO-1:0] upri_1;
logic [BITDATA-1:0] udin_1;
logic               push_1_drop;

logic               odrop_vld_0;
logic [BITPRIO-1:0] odrop_pri_0;
logic [BITDATA-1:0] odrop_dout_0;

always_ff @(posedge user_clk) begin
  if (rst) begin
    pop_0 <= 0;
    oprt_0 <= 0;
    push_1 <= 0;
    uprt_1 <= 0;
    upri_1 <= 0;
    udin_1 <= 0;
    push_1_drop <= 0;
  end else begin
    pop_0 <= !pop_0;
    oprt_0 <= oprt_0 + 1;
    push_1 <= !push_1;
    uprt_1 <= uprt_1 + 1;
    upri_1 <= upri_1 + 1;
    udin_1 <= udin_1 + 1;
    push_1_drop <= !push_1_drop;
  end
end

logic [31:0] out_placeholder;
logic pifo_out_r;

// Make sure we use all the outputs
always_comb begin
  out_placeholder = 0;
  out_placeholder ^= opri_0;
  out_placeholder ^= odout_0;
  out_placeholder ^= odrop_pri_0;
  out_placeholder ^= odrop_dout_0;

  pifo_out_r = ^out_placeholder ^ ovld_0 ^ odrop_vld_0;
end

always_ff @(posedge user_clk) begin
  pifo_out <= pifo_out_r;
end

pifo #(
  .NUMPIFO(NUMPIFO),
  .BITPORT(BITPORT),
  .BITPRIO(BITPRIO),
  .BITDATA(BITDATA)
) pifo_inst (
  .clk          (user_clk),
  .rst          (rst),

  .pop_0        (pop_0),
  .oprt_0       (oprt_0),
  .ovld_0       (ovld_0),
  .opri_0       (opri_0),
  .odout_0      (odout_0),

  .push_1       (push_1),
  .uprt_1       (uprt_1),
  .upri_1       (upri_1),
  .udin_1       (udin_1),

  .push_2       (1'b0),
  .uprt_2       (),
  .upri_2       (),
  .udin_2       ()
);

// panic_pifo #(
//   .NUMPIFO(NUMPIFO),
//   .BITPORT(BITPORT),
//   .BITPRIO(BITPRIO),
//   .BITDATA(BITDATA),
//   .PIFO_ID(PIFO_ID)
// ) pifo_inst (
//   .clk          (user_clk),
//   .rst          (rst),

//   .pop_0        (pop_0),
//   .oprt_0       (oprt_0),
//   .ovld_0       (ovld_0),
//   .opri_0       (opri_0),
//   .odout_0      (odout_0),

//   .push_1       (push_1),
//   .uprt_1       (uprt_1),
//   .upri_1       (upri_1),
//   .udin_1       (udin_1),
//   .push_1_drop  (push_1_drop),

//   .push_2       (1'b0),
//   .uprt_2       (),
//   .upri_2       (),
//   .udin_2       (),
//   .push_2_drop  (1'b0),

//   .odrop_vld_0  (odrop_vld_0),
//   .odrop_pri_0  (odrop_pri_0),
//   .odrop_dout_0 (odrop_dout_0)
// );

endmodule
