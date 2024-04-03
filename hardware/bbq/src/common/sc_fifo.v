// (C) 2001-2019 Intel Corporation. All rights reserved.
// Your use of Intel Corporation's design tools, logic functions and other 
// software and tools, and its AMPP partner logic functions, and any output 
// files from any of the foregoing (including device programming or simulation 
// files), and any associated documentation or information are expressly subject 
// to the terms and conditions of the Intel Program License Subscription 
// Agreement, Intel FPGA IP License Agreement, or other applicable 
// license agreement, including, without limitation, that your use is for the 
// sole purpose of programming logic devices manufactured by Intel and sold by 
// Intel or its authorized distributors.  Please refer to the applicable 
// agreement for further details.



// synopsys translate_off
`timescale 1 ps / 1 ps
// synopsys translate_on
module sc_fifo (
    clock,
    data,
    rdreq,
    wrreq,
    empty,
    full,
    q,
    usedw);

    parameter DWIDTH = 8;
    parameter DEPTH = 2048;
    parameter IS_SHOWAHEAD = 0;
    parameter IS_OUTDATA_REG = 0;

    localparam LOG_DEPTH = $clog2(DEPTH);
    localparam LPM_SHOWAHEAD = (
        (IS_SHOWAHEAD == 0) ? "OFF" : "ON");

    localparam ADD_RAM_OUTPUT_REGISTER = (
        (IS_OUTDATA_REG == 0) ? "OFF" : "ON");

    input    clock;
    input  [DWIDTH-1:0]  data;
    input    rdreq;
    input    wrreq;
    output   empty;
    output   full;
    output [DWIDTH-1:0]  q;
    output [LOG_DEPTH-1:0]  usedw;

    wire  sub_wire0;
    wire  sub_wire1;
    wire [DWIDTH-1:0] sub_wire2;
    wire [LOG_DEPTH-1:0] sub_wire3;
    wire  empty = sub_wire0;
    wire  full = sub_wire1;
    wire [DWIDTH-1:0] q = sub_wire2[DWIDTH-1:0];
    wire [LOG_DEPTH-1:0] usedw = sub_wire3[LOG_DEPTH-1:0];

    scfifo  scfifo_component (
                .clock (clock),
                .data (data),
                .rdreq (rdreq),
                .wrreq (wrreq),
                .empty (sub_wire0),
                .full (sub_wire1),
                .q (sub_wire2),
                .usedw (sub_wire3),
                .aclr (1'b0),
                .almost_empty (),
                .almost_full (),
                .eccstatus (),
                .sclr (1'b0));
    defparam
        scfifo_component.add_ram_output_register  = ADD_RAM_OUTPUT_REGISTER,
        scfifo_component.enable_ecc  = "FALSE",
        scfifo_component.intended_device_family  = "Stratix 10",
        scfifo_component.lpm_numwords  = DEPTH,
        scfifo_component.lpm_showahead  = LPM_SHOWAHEAD,
        scfifo_component.lpm_type  = "scfifo",
        scfifo_component.lpm_width  = DWIDTH,
        scfifo_component.lpm_widthu  = LOG_DEPTH,
        scfifo_component.overflow_checking  = "ON",
        scfifo_component.underflow_checking  = "ON",
        scfifo_component.use_eab  = "ON";

endmodule
