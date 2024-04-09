`timescale 1 ps / 1 ps

import heap_ops::*;

`ifndef ELEMENT_BITS
`define ELEMENT_BITS 17
`endif  // ELEMENT_BITS

`ifndef BITMAP_WIDTH
`define BITMAP_WIDTH 32
`endif // BITMAP_WIDTH

`ifndef NUM_LEVELS
`define NUM_LEVELS 3
`endif // NUM_LEVELS

module top (
    input               in_clk100,
    input               cpu_resetn,
    output logic        bbq_out
);

/////////////////////////
// dev_clr sync-reset
/////////////////////////
wire arst, user_clk;
assign arst = ~cpu_resetn;

my_pll user_pll (
    .rst      (~cpu_resetn),
    .refclk   (in_clk100),
    .locked   (),
    .outclk_0 (user_clk)
);

/**
 * BBQ.
 */
// Heap parameters
localparam NB_LEVELS = `NUM_LEVELS;
localparam HEAP_BITMAP_WIDTH = `BITMAP_WIDTH;
localparam HEAP_ENTRY_DWIDTH = `ELEMENT_BITS;
localparam HEAP_MAX_NUM_ENTRIES = ((1 << `ELEMENT_BITS) - 1);
localparam HEAP_NUM_PRIORITIES = (HEAP_BITMAP_WIDTH ** NB_LEVELS);
localparam HEAP_ENTRY_AWIDTH = ($clog2(HEAP_MAX_NUM_ENTRIES));
localparam HEAP_PRIORITY_AWIDTH = ($clog2(HEAP_NUM_PRIORITIES));

// Local typedefs
typedef logic [HEAP_ENTRY_DWIDTH-1:0] heap_entry_data_t;
typedef logic [HEAP_PRIORITY_AWIDTH-1:0] heap_priority_t;

// Global state
logic init_done;
logic [63:0] counter;

// Heap signals
logic heap_ready;
logic heap_in_valid;
heap_op_t heap_in_op_type;
heap_entry_data_t heap_in_data;
heap_priority_t heap_in_priority;

always @(posedge user_clk) begin
    if (arst) begin
        counter <= 0;
        init_done <= 0;
    end
    else begin
        heap_in_data <= 0;
        heap_in_valid <= 0;
        heap_in_priority <= 0;
        heap_in_op_type <= HEAP_OP_ENQUE;

        init_done <= (init_done | heap_ready);
        if (init_done) begin
            counter <= counter + 1;

            heap_in_valid <= 1;
            heap_in_data <= counter[HEAP_ENTRY_DWIDTH-1:0];
            heap_in_priority <= counter[HEAP_PRIORITY_AWIDTH-1:0];
            heap_in_op_type <= (counter[0] == 0) ? HEAP_OP_ENQUE : HEAP_OP_DEQUE_MIN;
        end
    end
end

localparam HEAP_PRIORITY_BUCKETS_AWIDTH = ($clog2(HEAP_NUM_PRIORITIES));

logic                                    heap_out_valid;
heap_op_t                                heap_out_op_type;
logic [HEAP_ENTRY_DWIDTH-1:0]            heap_out_he_data;
logic [HEAP_PRIORITY_BUCKETS_AWIDTH-1:0] heap_out_he_priority;

logic [31:0] out_placeholder;
logic bbq_out_r;

// Make sure we use all the outputs.
always_comb begin
    out_placeholder = 0;
    out_placeholder ^= heap_out_op_type;
    out_placeholder ^= heap_out_he_data;
    out_placeholder ^= heap_out_he_priority;

    bbq_out_r = ^out_placeholder ^ heap_out_valid;
end

always_ff @(posedge user_clk) begin
    bbq_out <= bbq_out_r;
end

// BBQ instance
bbq #(
    .HEAP_BITMAP_WIDTH(HEAP_BITMAP_WIDTH),
    .HEAP_ENTRY_DWIDTH(HEAP_ENTRY_DWIDTH),
    .HEAP_MAX_NUM_ENTRIES(HEAP_MAX_NUM_ENTRIES)
)
bbq_inst (
    .clk(user_clk),
    .rst(arst),
    .ready(heap_ready),
    .in_valid(heap_in_valid),
    .in_op_type(heap_in_op_type),
    .in_he_data(heap_in_data),
    .in_he_priority(heap_in_priority),
    .out_valid(heap_out_valid),
    .out_op_type(heap_out_op_type),
    .out_he_data(heap_out_he_data),
    .out_he_priority(heap_out_he_priority)
);

endmodule
