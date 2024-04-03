`timescale 1 ns/10 ps

import heap_ops::*;

module tb_bbq;

// Simulation parameters. Some testcases implicitly depend
// on the values being set here, so they musn't be changed!
localparam PERIOD = 10;
localparam HEAP_BITMAP_WIDTH = 32;
localparam HEAP_ENTRY_DWIDTH = 64;
localparam N = 127; // Maximum heap entries
localparam HEAP_ENTRY_AWIDTH = ($clog2(N));
localparam P = (bbq_inst.NUM_PIPELINE_STAGES + 1);
localparam HEAP_NUM_LEVELS = (bbq_inst.HEAP_NUM_LEVELS);
localparam HEAP_NUM_PRIORITIES = (HEAP_BITMAP_WIDTH ** HEAP_NUM_LEVELS);

localparam HEAP_PRIORITY_AWIDTH = ($clog2(HEAP_NUM_PRIORITIES));

localparam HEAP_INIT_CYCLES = (
    (N > HEAP_NUM_PRIORITIES) ?
    N : HEAP_NUM_PRIORITIES);

localparam HEAP_MIN_NUM_PRIORITIES_AND_ENTRIES = (
    (N < HEAP_NUM_PRIORITIES) ?
    N : HEAP_NUM_PRIORITIES);

localparam MAX_HEAP_INIT_CYCLES = (HEAP_INIT_CYCLES << 1);

// Local typedefs
typedef logic [HEAP_ENTRY_DWIDTH-1:0] heap_entry_data_t;
typedef logic [HEAP_PRIORITY_AWIDTH-1:0] heap_priority_t;

/**
 * List of tests:
 * ---------------------
 * TEST_BASIC_ENQUE
 * TEST_BASIC_DEQUE_MIN
 * TEST_BASIC_DEQUE_MAX
 * TEST_HEAP_PROPERTY
 * TEST_CAPACITY_LIMITS
 * TEST_PIPELINING_ENQUE_ENQUE
 * TEST_PIPELINING_ENQUE_DEQUE
 * TEST_PIPELINING_DEQUE_DEQUE_MIN
 * TEST_PIPELINING_DEQUE_DEQUE_MAX
 * TEST_PIPELINING_DEQUE_DEQUE_MIXED
 * TEST_DEQUE_FIFO
 * TEST_RESET
 */

// Global state
logic clk;
logic rst;
logic init_done;
logic [31:0] counter;
logic [31:0] test_timer;

initial clk = 0;
initial rst = 1;
initial counter = 0;
initial init_done = 0;
initial test_timer = 0;
always #(PERIOD) clk = ~clk;

// Heap signals
logic heap_ready;
logic heap_in_valid;
logic heap_out_valid;
heap_op_t heap_in_op_type;
heap_op_t heap_out_op_type;
heap_entry_data_t heap_in_data;
heap_entry_data_t heap_out_data;
heap_priority_t heap_in_priority;
heap_priority_t heap_out_priority;
logic [HEAP_ENTRY_AWIDTH-1:0] heap_size;

integer i;

`ifndef TEST_CASE
    $error("FAIL: No test case specified");
`else
if (`TEST_CASE == "TEST_BASIC_ENQUE") begin
// Test a single enque operation
always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter == 0) begin
            heap_in_valid <= 1;
            heap_in_data <= 23;
            heap_in_op_type <= HEAP_OP_ENQUE;
            heap_in_priority <= (HEAP_NUM_PRIORITIES - 1);
        end
        else if (counter > P) begin
            $display("FAIL %s: Test timed out", `TEST_CASE);
            $finish;
        end
        else if (heap_out_valid) begin
            if ((heap_out_data === 23) &&
                (heap_out_op_type === HEAP_OP_ENQUE) &&
                (heap_out_priority === (HEAP_NUM_PRIORITIES - 1))) begin
                $display("PASS %s", `TEST_CASE);
                $finish;
            end
            else begin
                $display("FAIL %s: Expected ", `TEST_CASE,
                         "(op: HEAP_OP_ENQUE, data: 23, priority: %d)",
                         (HEAP_NUM_PRIORITIES - 1), ", got (%s, %0d, %0d)",
                         heap_out_op_type.name, heap_out_data, heap_out_priority);
                $finish;
            end
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_BASIC_DEQUE_MIN") begin
// Test a single deque-min operation
localparam PRIORITY = (HEAP_NUM_PRIORITIES - 1);

always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter == 0) begin
            heap_in_valid <= 1;
            heap_in_data <= 42;
            heap_in_priority <= PRIORITY;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter == (2 * P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MIN;
        end
        else if ((counter > (2 * P)) && heap_out_valid) begin
            if ((heap_out_op_type === HEAP_OP_DEQUE_MIN) &&
                (heap_out_priority === PRIORITY) &&
                (heap_out_data === 42)) begin
                $display("PASS %s", `TEST_CASE);
                $finish;
            end
            else begin
                $display("FAIL %s: Expected ", `TEST_CASE,
                         "(op: HEAP_OP_DEQUE_MIN, data: 42, priority: %d), got",
                         PRIORITY, " (%s, %0d, %0d)", heap_out_op_type.name,
                         heap_out_data, heap_out_priority);
                $finish;
            end
        end
        else if (counter >= (4 * P)) begin
            $display("FAIL %s: Test timed out", `TEST_CASE);
            $finish;
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_BASIC_DEQUE_MAX") begin
// Test a single deque-max operation
always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter == 0) begin
            heap_in_valid <= 1;
            heap_in_data <= 13455345;
            heap_in_priority <= 7;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter == (2 * P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MAX;
        end
        else if ((counter > (2 * P)) && heap_out_valid) begin
            if ((heap_out_op_type === HEAP_OP_DEQUE_MAX) &&
                (heap_out_data === 13455345) &&
                (heap_out_priority === 7)) begin
                $display("PASS %s", `TEST_CASE);
                $finish;
            end
            else begin
                $display("FAIL %s: Expected ", `TEST_CASE,
                         "(op: HEAP_OP_DEQUE_MAX, data: 13455345, priority: 7), got",
                         " (%s, %0d, %0d)", heap_out_op_type.name, heap_out_data,
                         heap_out_priority);
                $finish;
            end
        end
        else if (counter >= (4 * P)) begin
            $display("FAIL %s: Test timed out", `TEST_CASE);
            $finish;
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_HEAP_PROPERTY") begin
// Ensures that the heap property is maintained
localparam PRIORITY_1 = ((3 * (HEAP_BITMAP_WIDTH ** (HEAP_NUM_LEVELS - 1))) + 21);
localparam PRIORITY_2 = ((2 * (HEAP_BITMAP_WIDTH ** (HEAP_NUM_LEVELS - 1))) + 17);
localparam PRIORITY_3 = ((1 * (HEAP_BITMAP_WIDTH ** (HEAP_NUM_LEVELS - 1))) + 12);
localparam PRIORITY_4 = ((7 * (HEAP_BITMAP_WIDTH ** (HEAP_NUM_LEVELS - 1))) + 18);

logic deque_min_done;
logic deque_max_done;

initial begin
    deque_min_done = 0;
    deque_max_done = 0;
end

always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter == 0) begin
            heap_in_valid <= 1;
            heap_in_data <= 1;
            heap_in_priority <= PRIORITY_1;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter == 1) begin
            heap_in_valid <= 1;
            heap_in_data <= 2;
            heap_in_priority <= PRIORITY_2;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter == 2) begin
            heap_in_valid <= 1;
            heap_in_data <= 3;
            heap_in_priority <= PRIORITY_3;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter == 3) begin
            heap_in_valid <= 1;
            heap_in_data <= 4;
            heap_in_priority <= PRIORITY_4;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter < (2 * P)) begin
            // NOOP
        end
        else if (counter == (2 * P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MIN;
        end
        else if (counter < (4 * P)) begin
            if (heap_out_valid) begin
                if ((heap_out_op_type === HEAP_OP_DEQUE_MIN) &&
                    (heap_out_priority === PRIORITY_3) &&
                    (heap_out_data === 3)) begin
                    deque_min_done <= 1;
                end
                else begin
                    $display("FAIL %s: Expected ", `TEST_CASE,
                             "(op: HEAP_OP_DEQUE_MIN, data: 3, priority: %d), got",
                             PRIORITY_3, " (%s, %0d, %0d)", heap_out_op_type.name,
                             heap_out_data, heap_out_priority);
                    $finish;
                end
            end
        end
        else if (counter == (4 * P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MAX;
        end
        else if (counter < (6 * P)) begin
            if (heap_out_valid) begin
                if ((heap_out_op_type === HEAP_OP_DEQUE_MAX) &&
                    (heap_out_priority === PRIORITY_4) &&
                    (heap_out_data === 4)) begin
                    deque_max_done <= 1;
                end
                else begin
                    $display("FAIL %s: Expected ", `TEST_CASE,
                             "(op: HEAP_OP_DEQUE_MAX, data: 4, priority: %d), got",
                             PRIORITY_4, " (%s, %0d, %0d)", heap_out_op_type.name,
                             heap_out_data, heap_out_priority);
                    $finish;
                end
            end
        end
        else begin
            if (deque_min_done && deque_max_done) begin
                $display("PASS %s", `TEST_CASE);
            end
            else begin
                $display("FAIL %s: Test timed out", `TEST_CASE);
            end
            $finish;
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_CAPACITY_LIMITS") begin
// Test heap capacity limits (i.e. enqueing into
// a full heap or dequeing from an empty heap).
// Also implicitly checks whether the free list
// works correctly going from an empty state to
// a non-empty one and back.
logic [31:0] num_enques_done_count;
logic deque_done;

initial begin
    num_enques_done_count = 0;
    deque_done = 0;
end

always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter < (2 * P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MIN;

            if (heap_out_valid) begin
                $display("FAIL %s: Deque'd empty heap", `TEST_CASE);
                $finish;
            end
        end
        else if (counter < ((4 * P) + N)) begin
            if (counter <= ((2 * P) + N)) begin
                heap_in_valid <= 1;
                heap_in_data <= counter;
                heap_in_priority <= (counter << 1);
                heap_in_op_type <= HEAP_OP_ENQUE;
            end
            if (heap_out_valid &&
                (heap_out_op_type == HEAP_OP_ENQUE)) begin
                num_enques_done_count <= num_enques_done_count + 1;
            end
        end
        else if (counter < ((6 * P) + N)) begin
            heap_in_valid <= 1;
            heap_in_data <= counter;
            heap_in_priority <= (counter << 1);
            heap_in_op_type <= HEAP_OP_ENQUE;

            if (heap_out_valid) begin
                $display("FAIL %s: Enque'd into a full heap", `TEST_CASE);
                $finish;
            end
        end
        else if (counter < ((8 * P) + N)) begin
            if (counter == ((6 * P) + N)) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MIN;
            end

            if (heap_out_valid) begin
                if (deque_done) begin
                    $display("FAIL %s: Expected 1 deque, saw many", `TEST_CASE);
                    $finish;
                end
                deque_done <= 1;
            end
        end
        else if (counter < ((10 * P) + N)) begin
            if (counter == ((8 * P) + N)) begin
                heap_in_valid <= 1;
                heap_in_data <= 42390;
                heap_in_priority <= 27;
                heap_in_op_type <= HEAP_OP_ENQUE;
            end
            if (num_enques_done_count !== N) begin
                $display("FAIL %s: Expected %0d enques, saw %0d",
                         `TEST_CASE, N, num_enques_done_count);
                $finish;
            end
            else if (!deque_done) begin
                $display("FAIL %s: Expected 1 deque, saw none", `TEST_CASE);
                $finish;
            end
            else if ((heap_out_op_type === HEAP_OP_ENQUE) &&
                     (heap_out_priority === 27) &&
                     (heap_out_data === 42390) &&
                     heap_out_valid) begin
                $display("PASS %s", `TEST_CASE);
                $finish;
            end
        end
        else begin
            $display("FAIL %s: Test timed out", `TEST_CASE);
            $finish;
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_PIPELINING_ENQUE_ENQUE") begin
// Make sure enque pipelining works as expected
logic [31:0] first_enque_done_count;
logic [31:0] num_enques_done_count;
logic first_enque_done;

initial begin
    first_enque_done = 0;
    num_enques_done_count = 0;
    first_enque_done_count = 0;
end

always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter < P) begin
            heap_in_valid <= 1;
            heap_in_data <= counter;
            heap_in_priority <= counter;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter >= (2 * P)) begin
            if (num_enques_done_count == P) begin
                $display("PASS %s", `TEST_CASE);
                $finish;
            end
            else begin
                $display("FAIL %s: Expected %0d enques, saw %0d",
                         `TEST_CASE, P, num_enques_done_count);
                $finish;
            end
        end
        if (heap_out_valid) begin
            if (!first_enque_done) begin
                first_enque_done <= 1;
                first_enque_done_count <= counter;

                if ((heap_out_priority !== 0) || (heap_out_data !== 0)) begin
                    $display("FAIL %s: Unexpected output data", `TEST_CASE);
                    $finish;
                end
            end
            else begin
                if ((heap_out_priority !== (counter - first_enque_done_count) ||
                    (heap_out_data !== (counter - first_enque_done_count)))) begin
                    $display("FAIL %s: Unexpected output data", `TEST_CASE);
                    $finish;
                end
            end
            num_enques_done_count <= num_enques_done_count + 1;
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_PIPELINING_ENQUE_DEQUE") begin
// Ensure back-to-back enques+deques are correctly handled
typedef enum {
    SUBTEST_A, // Staggered enques+deques targeting the same PB
    SUBTEST_B, // Staggered enques+deques targeting diff PBs
    SUBTEST_C, // Series of enques+deques 1 cycle(s) apart
    SUBTEST_D, // Series of enques+deques 2 cycle(s) apart
    SUBTEST_E, // Series of enques followed by 1 deque
    PASS
} subtest_t;
localparam NUM_SUBTESTS = 5;

logic [3:0] num_subtests_run;
logic [7:0] op_done[1:0];
logic is_out_enque;
subtest_t subtest;
integer j;

// For subtests A and B
logic [31:0] op_done_idx;
heap_op_t expected_out_op_type[3:0];
heap_entry_data_t expected_out_data[3:0];
heap_priority_t expected_out_priority[3:0];

initial begin
    op_done_idx = 0;

    expected_out_data[0] = 1;
    expected_out_data[1] = 3;
    expected_out_data[2] = 4;
    expected_out_data[3] = 2;

    expected_out_op_type[0] = HEAP_OP_DEQUE_MIN;
    expected_out_op_type[1] = HEAP_OP_DEQUE_MAX;
    expected_out_op_type[2] = HEAP_OP_DEQUE_MAX;
    expected_out_op_type[3] = HEAP_OP_DEQUE_MAX;

    for (i = 0; i < 2; i = i + 1) begin
        for (j = 0; j < 8; j = j + 1) begin
            op_done[i][j] = 0;
        end
    end
    subtest = SUBTEST_A;
    num_subtests_run = 0;
end

assign expected_out_priority[0] = 1;
assign expected_out_priority[1] = (HEAP_NUM_PRIORITIES - 1);
assign expected_out_priority[2] = ((subtest == SUBTEST_A) ? (HEAP_NUM_PRIORITIES - 1) :
                                                            (HEAP_NUM_PRIORITIES - 2));

assign expected_out_priority[3] = (subtest == SUBTEST_A) ? 1 : 2;

assign is_out_enque = (heap_out_op_type == HEAP_OP_ENQUE);
always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        case (subtest)
        // Staggered enques+deques targeting the same PB
        SUBTEST_A: begin
            counter <= counter + 1;
            if ((counter == 0) ||
                (counter == P)) begin
                heap_in_valid <= 1;
                heap_in_priority <= 1;
                heap_in_op_type <= HEAP_OP_ENQUE;
                heap_in_data <= (counter == 0) ? 1 : 2;
            end
            else if (counter == (P + 1)) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MIN;
            end
            else if ((counter == (P + 2)) ||
                     (counter == (P + 3))) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_ENQUE;
                heap_in_data <= (counter - P) + 1;
                heap_in_priority <= (HEAP_NUM_PRIORITIES - 1);
            end
            else if ((counter == (P + 4)) ||
                     (counter == ((2 * P) + 4)) ||
                     (counter == ((4 * P) + 4))) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MAX;
            end
            if (counter < ((6 * P) + 4)) begin
                if (heap_out_valid && !is_out_enque) begin
                    if (op_done_idx > 3) begin
                        $display("FAIL %s.A: Expected 4 deque ops, saw more",
                                 `TEST_CASE);
                        $finish;
                    end
                    else begin
                        if ((heap_out_priority !== expected_out_priority[op_done_idx]) ||
                            (heap_out_op_type !== expected_out_op_type[op_done_idx]) ||
                            (heap_out_data !== expected_out_data[op_done_idx])) begin
                            $display("FAIL %s.A: Expected ", `TEST_CASE,
                                     "(op: %s, data: %0d, priority: %0d) ",
                                     expected_out_op_type[op_done_idx].name,
                                     expected_out_data[op_done_idx],
                                     expected_out_priority[op_done_idx],
                                     "for op_done_idx %0d, ", op_done_idx,
                                     "got (%s, %0d, %0d)", heap_out_op_type.name,
                                     heap_out_data, heap_out_priority);
                            $finish;
                        end
                        op_done_idx <= op_done_idx + 1;
                    end
                end
            end
            else begin
                if (op_done_idx !== 4) begin
                    $display("FAIL %s.A: Expected 4 deques, saw fewer", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                counter <= 0;
                op_done_idx <= 0;
                subtest <= SUBTEST_B;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        // Staggered enques+deques targeting different PBs
        SUBTEST_B: begin
            counter <= counter + 1;
            if ((counter == 0) ||
                (counter == P)) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_ENQUE;
                heap_in_data <= (counter == 0) ? 1 : 2;
                heap_in_priority <= (counter == 0) ? 1 : 2;
            end
            else if (counter == (P + 1)) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MIN;
            end
            else if ((counter == (P + 2)) ||
                     (counter == (P + 3))) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_ENQUE;
                heap_in_data <= (counter - P) + 1;
                heap_in_priority <= ((HEAP_NUM_PRIORITIES - 1) -
                                     (counter - (P + 2)));
            end
            else if ((counter == (P + 4)) ||
                     (counter == ((2 * P) + 4)) ||
                     (counter == ((4 * P) + 4))) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MAX;
            end
            if (counter < ((6 * P) + 4)) begin
                if (heap_out_valid && !is_out_enque) begin
                    if (op_done_idx > 3) begin
                        $display("FAIL %s.B: Expected 4 deque ops, saw more",
                                 `TEST_CASE);
                        $finish;
                    end
                    else begin
                        if ((heap_out_priority !== expected_out_priority[op_done_idx]) ||
                            (heap_out_op_type !== expected_out_op_type[op_done_idx]) ||
                            (heap_out_data !== expected_out_data[op_done_idx])) begin
                            $display("FAIL %s.B: Expected ", `TEST_CASE,
                                     "(op: %s, data: %0d, priority: %0d) ",
                                     expected_out_op_type[op_done_idx].name,
                                     expected_out_data[op_done_idx],
                                     expected_out_priority[op_done_idx],
                                     "for op_done_idx %0d, ", op_done_idx,
                                     "got (%s, %0d, %0d)",
                                     heap_out_op_type.name,
                                     heap_out_data, heap_out_priority);
                            $finish;
                        end
                        op_done_idx <= op_done_idx + 1;
                    end
                end
            end
            else begin
                if (op_done_idx !== 4) begin
                    $display("FAIL %s.B: Expected 4 deques, saw fewer", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                counter <= 0;
                op_done_idx <= 0;
                subtest <= SUBTEST_C;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        // Series of enques+deques 1 cycle apart
        SUBTEST_C: begin
            counter <= counter + 1;
            if (counter < 16) begin
                heap_in_valid <= 1;
                heap_in_data <= counter;
                heap_in_priority <= counter;
                heap_in_op_type <= ((counter & 1'b1) ?
                    HEAP_OP_DEQUE_MIN : HEAP_OP_ENQUE);
            end
            else if (counter < 18) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MAX;
            end
            if (counter < (18 + (2 * P))) begin
                if (heap_out_valid) begin
                    if (!op_done[is_out_enque][0]) begin
                        if ((heap_out_priority !== 0) || (heap_out_data !== 0)) begin
                            $display("FAIL %s.C: Expected ", `TEST_CASE, "(op: *, ",
                                     "data: 0, priority: 0), got (%s, ",
                                     heap_out_op_type.name, "%0d, %0d)",
                                     heap_out_data, heap_out_priority);
                            $finish;
                        end
                        op_done[is_out_enque][0] <= 1;
                    end
                    for (i = 1; i < 8; i = i + 1) begin
                        if (op_done[is_out_enque][i - 1] && !op_done[is_out_enque][i]) begin
                            if (heap_out_priority !== (i * 2) || heap_out_data !== (i * 2))
                            begin
                                $display("FAIL %s.C: Expected ", `TEST_CASE, "(op: *, data: ",
                                         "%0d, ", (i * 2), "priority: %0d), ", (i * 2),
                                         "got (%s, %0d, %0d)", heap_out_op_type.name,
                                         heap_out_data, heap_out_priority);
                                $finish;
                            end
                            op_done[is_out_enque][i] <= 1;
                        end
                    end
                    if (op_done[is_out_enque][7]) begin
                        $display("FAIL %s.C: Expected 8 ops per type, saw more", `TEST_CASE);
                        $finish;
                    end
                end
            end
            else begin
                if (!op_done[0][7] || !op_done[1][7]) begin
                    $display("FAIL %s.C: Saw fewer than 8 deques and enques", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                for (i = 0; i < 2; i = i + 1) begin
                    for (j = 0; j < 8; j = j + 1) begin
                        op_done[i][j] <= 0;
                    end
                end
                counter <= 0;
                subtest <= SUBTEST_D;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        // Series of enques+deques 2 cycles apart
        SUBTEST_D: begin
            counter <= counter + 1;
            if (counter < 24) begin
                if (counter % 3 == 0) begin
                    heap_in_valid <= 1;
                    heap_in_data <= counter;
                    heap_in_priority <= counter;
                    heap_in_op_type <= HEAP_OP_ENQUE;
                end
                else if ((counter >= 2) &&
                         ((counter - 2) % 3 == 0)) begin
                    heap_in_valid <= 1;
                    heap_in_op_type <= HEAP_OP_DEQUE_MAX;
                end
            end
            if (counter < (24 + (2 * P))) begin
                if (heap_out_valid) begin
                    if (!op_done[is_out_enque][0]) begin
                        if ((heap_out_priority !== 0) || (heap_out_data !== 0)) begin
                            $display("FAIL %s.D: Expected ", `TEST_CASE, "(op: *, ",
                                     "data: 0, priority: 0), got (%s, ",
                                     heap_out_op_type.name, "%0d, %0d)",
                                     heap_out_data, heap_out_priority);
                            $finish;
                        end
                        op_done[is_out_enque][0] <= 1;
                    end
                    for (i = 1; i < 8; i = i + 1) begin
                        if (op_done[is_out_enque][i - 1] && !op_done[is_out_enque][i]) begin
                            if (heap_out_priority !== (i * 3) || heap_out_data !== (i * 3))
                            begin
                                $display("FAIL %s.D: Expected ", `TEST_CASE, "(op: *, data: ",
                                         "%0d, ", (i * 3), "priority: %0d), ", (i * 3),
                                         "got (%s, %0d, %0d)", heap_out_op_type.name,
                                         heap_out_data, heap_out_priority);
                                $finish;
                            end
                            op_done[is_out_enque][i] <= 1;
                        end
                    end
                    if (op_done[is_out_enque][7]) begin
                        $display("FAIL %s.D: Expected 8 ops per type, saw more", `TEST_CASE);
                        $finish;
                    end
                end
            end
            else begin
                if (!op_done[0][7] || !op_done[1][7]) begin
                    $display("FAIL %s.D: Saw fewer than 8 deques and enques", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                for (i = 0; i < 2; i = i + 1) begin
                    for (j = 0; j < 8; j = j + 1) begin
                        op_done[i][j] <= 0;
                    end
                end
                counter <= 0;
                subtest <= SUBTEST_E;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        // Series of enques followed by a single deque.
        // Also ensures the heap property is satisfied.
        SUBTEST_E: begin
            counter <= counter + 1;
            if (counter <= 8) begin
                heap_in_valid <= 1;
                if (counter < 4) begin
                    heap_in_data <= (3 - counter);
                    heap_in_op_type <= HEAP_OP_ENQUE;
                    heap_in_priority <= (HEAP_NUM_PRIORITIES - 1);
                end
                else if (counter < 8) begin
                    heap_in_data <= counter;
                    heap_in_priority <= counter;
                    heap_in_op_type <= HEAP_OP_ENQUE;
                end
                else begin
                    heap_in_op_type <= HEAP_OP_DEQUE_MAX;
                end
            end
            if (counter < (8 + (2 * P))) begin
                if (heap_out_valid) begin
                    if (!is_out_enque) begin
                        if (op_done[0][0]) begin
                            $display("FAIL %s.E: Expected 1 deque, saw many",
                                     `TEST_CASE);
                            $finish;
                        end
                        else if ((heap_out_priority !== (HEAP_NUM_PRIORITIES - 1)) ||
                                 (heap_out_op_type !== HEAP_OP_DEQUE_MAX) ||
                                 (heap_out_data !== 3)) begin
                            $display("FAIL %s.E: Expected ", `TEST_CASE, "(op: ",
                                     "HEAP_OP_DEQUE_MAX, data: 3, priority: %0d) ",
                                     (HEAP_NUM_PRIORITIES - 1), "got (%s, %0d, %0d)",
                                     heap_out_op_type.name, heap_out_data, heap_out_priority);
                            $finish;
                        end
                        op_done[0][0] <= 1;
                    end
                end
            end
            else begin
                if (!op_done[0][0]) begin
                    $display("FAIL %s.E: Expected 1 deque, saw none", `TEST_CASE);
                    $finish;
                end

                // Reset state
                counter <= 0;
                subtest <= PASS;
                op_done[0][0] <= 0;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        PASS: begin
            if (num_subtests_run === NUM_SUBTESTS) begin
                $display("PASS %s", `TEST_CASE);
            end
            else begin
                $display("FAIL %s: Only ran %0d/%0d subtests",
                         `TEST_CASE, num_subtests_run, NUM_SUBTESTS);
            end
            $finish;
        end
        default: begin
            $display("FAIL %s: Invalid subtest", `TEST_CASE);
            $finish;
        end
        endcase
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_PIPELINING_DEQUE_DEQUE_MIN" ||
         `TEST_CASE == "TEST_PIPELINING_DEQUE_DEQUE_MAX") begin
// Ensure back-to-back same-typed deques are correctly handled
typedef enum {
    SUBTEST_A, // Deques 1 cycle(s) apart
    SUBTEST_B, // Deques 2 cycle(s) apart
    PASS
} subtest_t;
localparam NUM_SUBTESTS = 2;

localparam IS_TEST_MIN = (`TEST_CASE == "TEST_PIPELINING_DEQUE_DEQUE_MIN");
logic [3:0] num_subtests_run;
logic is_out_enque;
subtest_t subtest;

// Expected output
logic [31:0] op_done_idx;
heap_op_t expected_out_op_type;
heap_entry_data_t expected_out_data[7:0];
heap_priority_t expected_out_priority[7:0];

initial begin
    op_done_idx = 0;
    subtest = SUBTEST_A;
    num_subtests_run = 0;

    expected_out_op_type = (IS_TEST_MIN ? HEAP_OP_DEQUE_MIN :
                                          HEAP_OP_DEQUE_MAX);

    expected_out_priority[0] = IS_TEST_MIN ? 1 : (HEAP_NUM_PRIORITIES - 1);
    expected_out_priority[1] = IS_TEST_MIN ? 1 : (HEAP_NUM_PRIORITIES - 1);
    expected_out_priority[2] = IS_TEST_MIN ? 1 : (HEAP_NUM_PRIORITIES - 1);
    expected_out_priority[3] = IS_TEST_MIN ? 1 : (HEAP_NUM_PRIORITIES - 1);
    expected_out_priority[4] = IS_TEST_MIN ? 2 : (HEAP_NUM_PRIORITIES - 2);
    expected_out_priority[5] = IS_TEST_MIN ? 3 : (HEAP_NUM_PRIORITIES - 3);
    expected_out_priority[6] = IS_TEST_MIN ? 4 : (HEAP_NUM_PRIORITIES - 4);
    expected_out_priority[7] = IS_TEST_MIN ? (HEAP_NUM_PRIORITIES - 1) : 1;
end

// Non-FIFO due to op coloring
assign expected_out_data[0] = 1;
assign expected_out_data[1] = (subtest == SUBTEST_A) ? 4 : 2;
assign expected_out_data[2] = (subtest == SUBTEST_A) ? 2 : 3;
assign expected_out_data[3] = (subtest == SUBTEST_A) ? 3 : 4;
assign expected_out_data[4] = 5;
assign expected_out_data[5] = 6;
assign expected_out_data[6] = 7;
assign expected_out_data[7] = 8;

assign is_out_enque = (heap_out_op_type == HEAP_OP_ENQUE);
always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        case (subtest)
        // Deques 1 cycle(s) apart
        SUBTEST_A: begin
            counter <= counter + 1;
            if (counter < 8) begin
                heap_in_valid <= 1;
                heap_in_data <= counter + 1;
                heap_in_op_type <= HEAP_OP_ENQUE;

                if (IS_TEST_MIN) begin
                    heap_in_priority <= (
                        (counter == 7) ? (HEAP_NUM_PRIORITIES - 1) :
                                         (counter < 4) ? 1 :
                                         (counter - 2));
                end
                else begin
                    heap_in_priority <= (
                        (counter == 7) ? 1 : (counter < 4) ?
                                         (HEAP_NUM_PRIORITIES - 1) :
                                         (HEAP_NUM_PRIORITIES - (counter - 2)));
                end
            end
            else if (counter < (8 + P)) begin
                // NOOP
            end
            else if (counter < (16 + P)) begin
                heap_in_valid <= 1;
                heap_in_op_type <= (IS_TEST_MIN ? HEAP_OP_DEQUE_MIN :
                                                  HEAP_OP_DEQUE_MAX);
            end
            else if (counter < (18 + P)) begin
                heap_in_valid <= 1; // Invalid deque ops
                heap_in_op_type <= (IS_TEST_MIN ? HEAP_OP_DEQUE_MAX :
                                                  HEAP_OP_DEQUE_MIN);
            end
            if (counter < (18 + (3 * P))) begin
                if (heap_out_valid && !is_out_enque) begin
                    if (heap_out_op_type !== expected_out_op_type) begin
                        $display("FAIL %s.A: Expected op %s, got %s", `TEST_CASE,
                                 expected_out_op_type.name, heap_out_op_type.name);
                        $finish;
                    end
                    else if (op_done_idx > 7) begin
                        $display("FAIL %s.A: Expected 8 deque ops, saw more",
                                 `TEST_CASE);
                        $finish;
                    end
                    else begin
                        if ((heap_out_priority !== expected_out_priority[op_done_idx]) ||
                            (heap_out_data !== expected_out_data[op_done_idx])) begin
                            $display("FAIL %s.A: Expected ", `TEST_CASE,
                                     "(data: %0d, priority: %0d) ",
                                     expected_out_data[op_done_idx],
                                     expected_out_priority[op_done_idx],
                                     "for op_done_idx %0d, got ", op_done_idx,
                                     "(%0d, %0d)", heap_out_data, heap_out_priority);
                            $finish;
                        end
                    end
                    op_done_idx <= op_done_idx + 1;
                end
            end
            else begin
                if (op_done_idx !== 8) begin
                    $display("FAIL %s.A: Expected 8 deques, saw fewer", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                counter <= 0;
                op_done_idx <= 0;
                subtest <= SUBTEST_B;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        // Deques 2 cycle(s) apart
        SUBTEST_B: begin
            counter <= counter + 1;
            if (counter < 8) begin
                heap_in_valid <= 1;
                heap_in_data <= counter + 1;
                heap_in_op_type <= HEAP_OP_ENQUE;

                if (IS_TEST_MIN) begin
                    heap_in_priority <= (
                        (counter == 7) ? (HEAP_NUM_PRIORITIES - 1) :
                                         (counter < 4) ? 1 :
                                         (counter - 2));
                end
                else begin
                    heap_in_priority <= (
                        (counter == 7) ? 1 : (counter < 4) ?
                                         (HEAP_NUM_PRIORITIES - 1) :
                                         (HEAP_NUM_PRIORITIES - (counter - 2)));
                end
            end
            else if (counter < (8 + P)) begin
                // NOOP
            end
            else if (counter < (32 + P)) begin
                if (counter % 2 == 0) begin
                    heap_in_valid <= 1;
                    heap_in_op_type <= (IS_TEST_MIN ? HEAP_OP_DEQUE_MIN :
                                                      HEAP_OP_DEQUE_MAX);
                end
            end
            else if (counter < (34 + P)) begin
                heap_in_valid <= 1; // More invalid deque ops
                heap_in_op_type <= (IS_TEST_MIN ? HEAP_OP_DEQUE_MAX :
                                                  HEAP_OP_DEQUE_MIN);
            end
            if (counter < (34 + (3 * P))) begin
                if (heap_out_valid && !is_out_enque) begin
                    if (heap_out_op_type !== expected_out_op_type) begin
                        $display("FAIL %s.B: Expected op %s, got %s", `TEST_CASE,
                                 expected_out_op_type.name, heap_out_op_type.name);
                        $finish;
                    end
                    else if (op_done_idx > 7) begin
                        $display("FAIL %s.B: Expected 8 deque ops, saw more",
                                 `TEST_CASE);
                        $finish;
                    end
                    else begin
                        if ((heap_out_priority !== expected_out_priority[op_done_idx]) ||
                            (heap_out_data !== expected_out_data[op_done_idx])) begin
                            $display("FAIL %s.B: Expected ", `TEST_CASE,
                                     "(data: %0d, priority: %0d) ",
                                     expected_out_data[op_done_idx],
                                     expected_out_priority[op_done_idx],
                                     "for op_done_idx %0d, got ", op_done_idx,
                                     "(%0d, %0d)", heap_out_data, heap_out_priority);
                            $finish;
                        end
                    end
                    op_done_idx <= op_done_idx + 1;
                end
            end
            else begin
                if (op_done_idx !== 8) begin
                    $display("FAIL %s.B: Expected 8 deques, saw fewer", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                counter <= 0;
                subtest <= PASS;
                op_done_idx <= 0;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        PASS: begin
            if (num_subtests_run === NUM_SUBTESTS) begin
                $display("PASS %s", `TEST_CASE);
            end
            else begin
                $display("FAIL %s: Only ran %0d/%0d subtests",
                         `TEST_CASE, num_subtests_run, NUM_SUBTESTS);
            end
            $finish;
        end
        default: begin
            $display("FAIL %s: Invalid subtest", `TEST_CASE);
            $finish;
        end
        endcase
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_PIPELINING_DEQUE_DEQUE_MIXED") begin
// Ensure back-to-back diff-typed deques are correctly handled
typedef enum {
    SUBTEST_A, // Deques 1 cycle(s) apart
    SUBTEST_B, // Deques 2 cycle(s) apart
    PASS
} subtest_t;
localparam NUM_SUBTESTS = 2;

logic [3:0] num_subtests_run;
logic is_out_enque;
subtest_t subtest;

// Expected output
logic [31:0] op_done_idx;
heap_op_t expected_out_op_type[7:0];
heap_entry_data_t expected_out_data[7:0];
heap_priority_t expected_out_priority[7:0];

initial begin
    op_done_idx = 0;
    subtest = SUBTEST_A;
    num_subtests_run = 0;

    for (i = 0; i < 8; i = i + 1) begin
        expected_out_op_type[i] = (
            (i % 2 == 0) ? HEAP_OP_DEQUE_MIN :
                           HEAP_OP_DEQUE_MAX);
    end

    expected_out_priority[0] = 1;
    expected_out_priority[1] = (HEAP_NUM_PRIORITIES - 1);
    expected_out_priority[2] = 1;
    expected_out_priority[3] = 2;
    expected_out_priority[4] = 1;
    expected_out_priority[5] = 1;
    expected_out_priority[6] = 1;
    expected_out_priority[7] = 1;
end

// Non-FIFO due to op coloring
assign expected_out_data[0] = 1;
assign expected_out_data[1] = 2;
assign expected_out_data[2] = 3;
assign expected_out_data[3] = 4;
assign expected_out_data[4] = 5;
assign expected_out_data[5] = (subtest == SUBTEST_A) ? 8 : 6;
assign expected_out_data[6] = (subtest == SUBTEST_A) ? 6 : 7;
assign expected_out_data[7] = (subtest == SUBTEST_A) ? 7 : 8;

assign is_out_enque = (heap_out_op_type == HEAP_OP_ENQUE);
always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        case (subtest)
        // Deques 1 cycle(s) apart
        SUBTEST_A: begin
            counter <= counter + 1;
            if (counter < 8) begin
                heap_in_valid <= 1;
                heap_in_data <= counter + 1;
                heap_in_op_type <= HEAP_OP_ENQUE;
                heap_in_priority <= expected_out_priority[counter];
            end
            else if (counter < (8 + (2 * P))) begin
                // NOOP
            end
            else if (counter < (20 + (2 * P))) begin
                heap_in_valid <= 1;
                heap_in_op_type <= (
                    (counter % 2 == 0) ? HEAP_OP_DEQUE_MIN :
                                         HEAP_OP_DEQUE_MAX);
            end
            if (counter < (20 + (4 * P))) begin
                if (heap_out_valid && !is_out_enque) begin
                    if (heap_out_op_type !== expected_out_op_type[op_done_idx]) begin
                        $display("FAIL %s.A: Expected op %s for op_done_idx %0d, got %s",
                                 `TEST_CASE, expected_out_op_type[op_done_idx].name,
                                 op_done_idx, heap_out_op_type.name);
                        $finish;
                    end
                    else if (op_done_idx > 7) begin
                        $display("FAIL %s.A: Expected 8 deque ops, saw more",
                                 `TEST_CASE);
                        $finish;
                    end
                    else begin
                        if ((heap_out_priority !== expected_out_priority[op_done_idx]) ||
                            (heap_out_data !== expected_out_data[op_done_idx])) begin
                            $display("FAIL %s.A: Expected ", `TEST_CASE,
                                     "(data: %0d, priority: %0d) ",
                                     expected_out_data[op_done_idx],
                                     expected_out_priority[op_done_idx],
                                     "for op_done_idx %0d, got ", op_done_idx,
                                     "(%0d, %0d)", heap_out_data, heap_out_priority);
                            $finish;
                        end
                    end
                    op_done_idx <= op_done_idx + 1;
                end
            end
            else begin
                if (op_done_idx !== 8) begin
                    $display("FAIL %s.A: Expected 8 deques, saw fewer", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                counter <= 0;
                op_done_idx <= 0;
                subtest <= SUBTEST_B;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        // Deques 2 cycle(s) apart
        SUBTEST_B: begin
            counter <= counter + 1;
            if (counter < 8) begin
                heap_in_valid <= 1;
                heap_in_data <= counter + 1;
                heap_in_op_type <= HEAP_OP_ENQUE;
                heap_in_priority <= expected_out_priority[counter];
            end
            else if (counter < (8 + (4 * P))) begin
                // NOOP
            end
            else if (counter < (40 + (4 * P))) begin
                if (counter % 2 == 0) begin
                    heap_in_valid <= 1;
                    heap_in_op_type <= (
                        (counter % 4 == 0) ? HEAP_OP_DEQUE_MIN :
                                             HEAP_OP_DEQUE_MAX);
                end
            end
            if (counter < (40 + (6 * P))) begin
                if (heap_out_valid && !is_out_enque) begin
                    if (heap_out_op_type !== expected_out_op_type[op_done_idx]) begin
                        $display("FAIL %s.B: Expected op %s for op_done_idx %0d, got %s",
                                 `TEST_CASE, expected_out_op_type[op_done_idx].name,
                                 op_done_idx, heap_out_op_type.name);
                        $finish;
                    end
                    else if (op_done_idx > 7) begin
                        $display("FAIL %s.B: Expected 8 deque ops, saw more",
                                 `TEST_CASE);
                        $finish;
                    end
                    else begin
                        if ((heap_out_priority !== expected_out_priority[op_done_idx]) ||
                            (heap_out_data !== expected_out_data[op_done_idx])) begin
                            $display("FAIL %s.B: Expected ", `TEST_CASE,
                                     "(data: %0d, priority: %0d) ",
                                     expected_out_data[op_done_idx],
                                     expected_out_priority[op_done_idx],
                                     "for op_done_idx %0d, got ", op_done_idx,
                                     "(%0d, %0d)", heap_out_data, heap_out_priority);
                            $finish;
                        end
                    end
                    op_done_idx <= op_done_idx + 1;
                end
            end
            else begin
                if (op_done_idx !== 8) begin
                    $display("FAIL %s.B: Expected 8 deques, saw fewer", `TEST_CASE);
                    $finish;
                end

                // Reset state for the next subtest
                counter <= 0;
                subtest <= PASS;
                op_done_idx <= 0;
                num_subtests_run <= num_subtests_run + 1;
            end
        end
        PASS: begin
            if (num_subtests_run === NUM_SUBTESTS) begin
                $display("PASS %s", `TEST_CASE);
            end
            else begin
                $display("FAIL %s: Only ran %0d/%0d subtests",
                         `TEST_CASE, num_subtests_run, NUM_SUBTESTS);
            end
            $finish;
        end
        default: begin
            $display("FAIL %s: Invalid subtest", `TEST_CASE);
            $finish;
        end
        endcase
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_DEQUE_FIFO") begin
// Make sure multiple deque ops spaced two cycles
// apart and landing at the same priority bucket
// implement FIFO behavior.

localparam PRIORITY = ((HEAP_NUM_PRIORITIES / 2) + 3);
logic [31:0] last_deque_counter;
logic [5:0] num_deques_done;

initial begin
    num_deques_done = 0;
    last_deque_counter = 0;
end

always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (init_done) begin
        counter <= counter + 1;
        if (counter < 8) begin
            heap_in_valid <= 1;
            heap_in_data <= counter + 5;
            heap_in_priority <= PRIORITY;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter < (2 * P)) begin
            // NOOP
        end
        else if (counter < (2 * P) + 16) begin
            if ((counter & 1'b1) == 0) begin
                heap_in_valid <= 1;
                heap_in_op_type <= HEAP_OP_DEQUE_MIN;
            end
        end
        else if (counter >= ((4 * P) + 16)) begin
            if (num_deques_done == 0) begin
                $display("FAIL %s: Test timed out", `TEST_CASE);
            end
            else if (num_deques_done !== 8) begin
                $display("FAIL %s: Expected 8 deque completions, saw %0d",
                         `TEST_CASE, num_deques_done);
            end
            else begin
                $display("PASS %s", `TEST_CASE);
            end
            $finish;
        end

        if (heap_out_valid && (heap_out_op_type == HEAP_OP_DEQUE_MIN)) begin
            num_deques_done <= num_deques_done + 1;
            last_deque_counter <= counter;

            if (num_deques_done !== 0) begin
                if ((counter !== (last_deque_counter + 2)) ||
                    (heap_out_priority !== PRIORITY)) begin
                    $display("FAIL %s: Colliding deques were not pipelined", `TEST_CASE);
                    $finish;
                end
            end
            if (heap_out_data !== (5 + num_deques_done)) begin
                $display("FAIL %s: Deques violate FIFO ordering", `TEST_CASE);
                $finish;
            end
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else if (`TEST_CASE == "TEST_RESET") begin
// Make sure rst works as expected
logic [31:0] num_enques_done;
logic second_init_done;
logic deque_done;
logic rst_issued;

initial begin
    rst_issued = 0;
    deque_done = 0;
    num_enques_done = 0;
    second_init_done = 0;
end

always @(posedge clk) begin
    rst <= 0;
    heap_in_valid <= 0;
    heap_in_data <= 0;
    heap_in_priority <= 0;
    test_timer <= test_timer + 1;
    heap_in_op_type <= HEAP_OP_ENQUE;
    init_done <= init_done | heap_ready;

    if (second_init_done) begin
        counter <= counter + 1;
        if (counter < N) begin
            heap_in_valid <= 1;
            heap_in_data <= 42;
            heap_in_priority <= counter;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter < (N + P)) begin
            // NOOP
        end
        else if (counter == (N + P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MAX;
        end
        else if (counter > (N + (2 * P))) begin
            if ((num_enques_done === N) && deque_done) begin
                $display("PASS %s", `TEST_CASE);
            end
            else if (!deque_done) begin
                $display("FAIL %s: Expected 1 deque post reset, saw none",
                         `TEST_CASE);
            end
            else begin
                $display("FAIL %s: Expected %0d enques post reset, only saw %0d",
                         `TEST_CASE, N, num_enques_done);
            end
            $finish;
        end

        if (heap_out_valid) begin
            if (heap_out_op_type === HEAP_OP_ENQUE) begin
                if (heap_out_data === 42) begin
                    num_enques_done <= num_enques_done + 1;
                end
                else begin
                    $display("FAIL %s: Unexpected output data", `TEST_CASE);
                    $finish;
                end
            end
            else if (heap_out_op_type === HEAP_OP_DEQUE_MAX) begin
                if ((heap_out_priority === (HEAP_MIN_NUM_PRIORITIES_AND_ENTRIES - 1)) &&
                    (heap_out_data === 42)) begin
                    deque_done <= 1;
                end
                else begin
                    $display("FAIL %s: Deque-max post reset does not satisfy heap property",
                             `TEST_CASE);
                    $finish;
                end
            end
            else begin
            end
        end
    end
    else if (rst_issued && heap_ready) begin
        if (heap_size !== 0) begin
            $display("FAIL %s: Heap size is non-zero post reset", `TEST_CASE);
            $finish;
        end
        counter <= 0;
        second_init_done <= 1;
    end
    else if (init_done) begin
        counter <= counter + 1;
        if (counter < 8) begin
            heap_in_valid <= 1;
            heap_in_data <= counter + 5;
            heap_in_priority <= counter + 5;
            heap_in_op_type <= HEAP_OP_ENQUE;
        end
        else if (counter < (8 + P)) begin
            // NOOP
        end
        else if (counter < (12 + P)) begin
            heap_in_valid <= 1;
            heap_in_op_type <= HEAP_OP_DEQUE_MIN;
        end
        else if (counter == (12 + P)) begin
            rst <= 1;
            rst_issued <= 1;
        end
        else if (counter > (MAX_HEAP_INIT_CYCLES << 2)) begin
            $display("FAIL %s: Heap rst timed out", `TEST_CASE);
            $finish;
        end
    end
    else if (test_timer > MAX_HEAP_INIT_CYCLES) begin
        $display("FAIL %s: Heap init timed out", `TEST_CASE);
        $finish;
    end
end
end

else begin
    $error("FAIL: Unknown test %s", `TEST_CASE);
end
`endif

// BBQ instance
bbq #(
    .HEAP_BITMAP_WIDTH(HEAP_BITMAP_WIDTH),
    .HEAP_ENTRY_DWIDTH(HEAP_ENTRY_DWIDTH),
    .HEAP_MAX_NUM_ENTRIES(N)
)
bbq_inst (
    .clk(clk),
    .rst(rst),
    .ready(heap_ready),
    .in_valid(heap_in_valid),
    .in_op_type(heap_in_op_type),
    .in_he_data(heap_in_data),
    .in_he_priority(heap_in_priority),
    .out_valid(heap_out_valid),
    .out_op_type(heap_out_op_type),
    .out_he_data(heap_out_data),
    .out_he_priority(heap_out_priority),
    .size(heap_size)
);

endmodule
