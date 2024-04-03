/*
 * Find first-set bits (MSb, LSb).
 */
module ffs #(
    parameter WIDTH_LOG = 4,
    localparam WIDTH = (1 << WIDTH_LOG)
) (
    input  logic [WIDTH-1:0]        x,
    output logic [WIDTH_LOG-1:0]    msb,
    output logic [WIDTH_LOG-1:0]    lsb,
    output logic [WIDTH-1:0]        msb_onehot,
    output logic [WIDTH-1:0]        lsb_onehot,
    output logic                    zero
);

integer i, width;
logic [WIDTH-1:0] y;
logic [WIDTH-1:0] part_msb;
logic [WIDTH-1:0] part_lsb;

// Zero input?
assign zero = (x == 0);

// Leading one (MSb) detector
always @(*) begin
    msb = 0;
    part_msb = x;
    for (i = (WIDTH_LOG-1); i >= 0; i = i - 1) begin
        width = 1 << i;
        if (|(part_msb >> width)) begin
            msb[i] = 1;
        end
        part_msb = msb[i] ? (part_msb >> width) :
                            (part_msb & ((1'd1 << width) - 1'd1));
    end
    msb_onehot = (1 << msb);
    lsb_onehot = (((~x) + 1) & x);
end

// Reverse bit order for LSb detection
always @(*) begin
    for (i = (WIDTH-1); i >= 0; i = i - 1) begin
        y[i] = x[(WIDTH-1) - i];
    end
end

// Trailing one (LSb) detector
// TODO(natre): Optimize impl.
always @(*) begin
    lsb = 0;
    part_lsb = y;
    for (i = (WIDTH_LOG-1); i >= 0; i = i - 1) begin
        width = 1 << i;
        if (|(part_lsb >> width)) begin
            lsb[i] = 1;
        end
        part_lsb = lsb[i] ? (part_lsb >> width) :
                            (part_lsb & ((1'd1 << width) - 1'd1));
    end
    lsb = ~lsb;
end

endmodule
