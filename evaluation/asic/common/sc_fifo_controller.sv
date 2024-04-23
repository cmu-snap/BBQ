
module sc_fifo_controller #(
    parameter DWIDTH = 8,
    parameter DEPTH = 2048,
    parameter IS_SHOWAHEAD = 0,
    parameter IS_OUTDATA_REG = 0,

    localparam AWIDTH = $clog2(DEPTH)
)(
    input  logic                 clock,
    input  logic  [DWIDTH-1:0]   data,
    input  logic                 rdreq,
    input  logic                 wrreq,
    output logic                 empty,
    output logic                 full,
    output logic [DWIDTH-1:0]    q,

    // External BRAM interface.
    output logic [DWIDTH-1:0]    bram_data,
    output logic [AWIDTH-1:0]    bram_rdaddress,
    output logic [AWIDTH-1:0]    bram_wraddress,
    output logic                 bram_wren,
    input  logic [DWIDTH-1:0]    bram_q
);

localparam FIFO_MAX_WIDTH = 2048;
localparam FIFO_MAX_DEPTH = 2**24;

logic              push_req_n;
logic              pop_req_n;
logic [DWIDTH-1:0] data_in;
logic              _empty;
logic              _full;

generate
    if (IS_SHOWAHEAD) begin
        $error("IS_SHOWAHEAD not supported.");
    end

    if (DWIDTH > FIFO_MAX_WIDTH) begin
        $error("DWIDTH must be at most %d", FIFO_MAX_WIDTH);
    end

    if (DEPTH > FIFO_MAX_DEPTH) begin
        $error("DEPTH must be at most %d", FIFO_MAX_DEPTH);
    end

    if (IS_OUTDATA_REG) begin
        // Adding extra cycle for read.
        always_ff @(posedge clock) begin
            empty <= _empty;
        end
    end else begin
        assign empty = _empty;
    end
endgenerate

logic we_n;

logic [AWIDTH-1:0] rdaddress;
logic [AWIDTH-1:0] wraddress;

always_comb begin
    push_req_n = ~wrreq;
    pop_req_n = ~rdreq;
    data_in = data;
    full = _full;

    // External BRAM interface.
    bram_data = data;
    bram_rdaddress = rdaddress;
    bram_wraddress = wraddress;
    bram_wren = ~we_n;
    q = bram_q;
end

DW_fifoctl_s1_sf #(
    .depth(DEPTH),
    .rst_mode(1)  // Synchonous reset.
) DW_fifoctl_s1_sf_inst (
    .clk          (clock),
    .rst_n        (1'b1),  // Disable reset.
    .push_req_n   (push_req_n),
    .pop_req_n    (pop_req_n),
    .diag_n       (1'b1),  // Disable diagnostic.
    .we_n         (we_n),
    .empty        (_empty),
    .almost_empty (),
    .half_full    (),
    .almost_full  (),
    .full         (_full),
    .error        (),
    .wr_addr      (wraddress),
    .rd_addr      (rdaddress)
);

endmodule  // sc_fifo
