`ifndef PIEO_DATATYPES
`define PIEO_DATATYPES

package pieo_datatypes;

// Original parameters.
// localparam LIST_SIZE = (2**6);
// localparam ID_LOG = $clog2(LIST_SIZE);
// localparam RANK_LOG = 16;
// localparam TIME_LOG = 16;

// localparam NUM_OF_ELEMENTS_PER_SUBLIST = (2**3); //sqrt(LIST_SIZE)
// localparam NUM_OF_SUBLIST = (2**4); //2*NUM_OF_ELEMENTS_PER_SUBLIST

// localparam ID_LOG = `ID_LOG;  // Log of the number of elements.
// localparam RANK_LOG = `RANK_LOG;

// `ifndef ELEMENT_BITS
// `define ELEMENT_BITS 7
// `endif  // ELEMENT_BITS

// `ifndef PRIORITY_BITS
// `define PRIORITY_BITS 8
// `endif  // PRIORITY_BITS

localparam ID_LOG = `ELEMENT_BITS;  // Log of the number of elements.
localparam RANK_LOG = `PRIORITY_BITS;

localparam TIME_LOG = RANK_LOG;
localparam LIST_SIZE = 2**ID_LOG;

localparam NUM_OF_ELEMENTS_PER_SUBLIST = int'($sqrt(LIST_SIZE));
localparam NUM_OF_SUBLIST = 2 * NUM_OF_ELEMENTS_PER_SUBLIST;

typedef struct packed
{
    logic [ID_LOG-1:0] id;
    logic [RANK_LOG-1:0] rank; //init with infinity
    logic [TIME_LOG-1:0] send_time;
} SublistElement;

typedef struct packed
{
    logic [$clog2(NUM_OF_SUBLIST)-1:0] id;
    logic [RANK_LOG-1:0] smallest_rank; //init with infinity
    logic [TIME_LOG-1:0] smallest_send_time; //init with infinity
    logic full;
    logic [$clog2(NUM_OF_SUBLIST/2)-1:0] num;
} PointerElement;

endpackage
`endif
