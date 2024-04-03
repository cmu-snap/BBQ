`timescale 1 ps / 1 ps

module top (
  input        in_clk100,
  input        cpu_resetn,
  output logic bmw_out
);

wire rst, user_clk;
assign rst = ~cpu_resetn;

my_pll user_pll (
  .rst      (rst),
  .refclk   (in_clk100),
  .locked   (),
  .outclk_0 (user_clk)
);

`ifndef LEVELS
`define LEVELS 8
`endif  // LEVELS

`ifndef PRIORITY_BITS
`define PRIORITY_BITS 16
`endif  // PRIORITY_BITS

localparam ORDER = 4;  // Hardcoded in the design.

localparam NB_ELEMENTS = ORDER * (1 - ORDER ** `LEVELS) / (1 - ORDER);
localparam PTW = `PRIORITY_BITS;         // Payload data width (weight)
localparam MTW = $clog2(NB_ELEMENTS);    // Metadata width.
localparam CTW = $clog2(NB_ELEMENTS);    // Counter width.
localparam ADW = $clog2(ORDER**`LEVELS); // Address width (used to index nodes
                                         // in a given tree level).

logic i_push;
logic i_pop;

logic [(MTW+PTW)-1:0] i_push_data;
logic [(MTW+PTW)-1:0] o_pop_data;

always_ff @(posedge user_clk) begin
  if (rst) begin
    i_push <= 0;
    i_pop <= 1;
    i_push_data <= 0;
  end else begin
    i_push <= !i_push;
    i_pop <= !i_pop;
    i_push_data <= i_push_data + 1;
  end
end

always_ff @(posedge user_clk) begin
  bmw_out <= ^o_pop_data;
end

bmw_sram_top #(
  .PTW   (PTW),
  .MTW   (MTW),
  .CTW   (CTW),
  .ADW   (ADW),
  .LEVEL (`LEVELS)
) bmw_sram_top_inst (
  .i_clk       (user_clk),
  .i_arst_n    (~rst),
  .i_push      (i_push),
  .i_push_data (i_push_data),
  .i_pop       (i_pop),
  .o_pop_data  (o_pop_data)
);

endmodule
