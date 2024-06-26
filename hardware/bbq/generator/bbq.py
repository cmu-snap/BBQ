#!/usr/bin/python3
import argparse
import math
from typing import List

from bbq_level import BBQLevel
from bbq_level_ingress import BBQLevelIngress
from bbq_level_lx import BBQLevelLX
from bbq_level_pb import BBQLevelPB
from bbq_level_steering import BBQLevelSteering
from codegen import CodeGen
from toolz.itertoolz import partition


class BBQ:
    """Class for generating configurable BBQs."""
    def __init__(self, num_bitmap_levels: int, num_lps: int=1,
                 bitmap_width: int=0) -> None:

        # BBQ configuration
        self.num_lps = num_lps
        self.bitmap_width = bitmap_width
        self.num_bitmap_levels = num_bitmap_levels
        self.validate_configuration() # Perform validation

        # Generate ingress level
        start_cycle = 1
        self.levels : List[BBQLevel] = [
            BBQLevelIngress(self, start_cycle)
        ]
        start_cycle = self.levels[-1].end_cycle + 1

        # Generate steering level
        start_level_id = 1
        if self.is_logically_partitioned:
            start_level_id = int(math.log(num_lps, bitmap_width))
            level = BBQLevelSteering(self, start_cycle,
                                     num_lps, start_level_id)

            self.levels.append(level)
            start_cycle = level.end_cycle + 1
            start_level_id += 1 # Skip corresponding LX levels

        # Populate the list with all LX levels
        for level_id in range(start_level_id, self.num_bitmap_levels + 1):
            level = BBQLevelLX(self, start_cycle, level_id,
                               (level_id >= 3), (level_id >= 2))

            self.levels.append(level)
            start_cycle = level.end_cycle + 1

        # Finally, append the PB level into the list
        self.levels.append(BBQLevelPB(self, start_cycle))
        self.num_pipeline_stages = self.levels[-1].end_cycle + 1

        # Update next and prev pointers
        for i in range(len(self.levels) - 1):
            self.levels[i].next_level = self.levels[i + 1]

        for i in range (1, len(self.levels)):
            self.levels[i].prev_level = self.levels[i - 1]

        # Compute the free list read delay
        self.fl_rd_delay = (self.levels[-1].end_cycle -
                            self.levels[0].end_cycle - 1)

        # Finally, instantiate backend
        self.codegen = CodeGen()


    @property
    def bitmap_levels(self) -> List[BBQLevelLX]:
        """Returns levels of the bitmap tree."""
        bitmap_levels = []
        for level in self.levels:
            if isinstance(level, BBQLevelLX):
                bitmap_levels.append(level)

        return bitmap_levels


    @property
    def is_logically_partitioned(self) -> bool:
        """Uses logical paritioning?"""
        return self.num_lps > 1


    def validate_configuration(self) -> None:
        """Validate the BBQ configuration."""
        if self.num_bitmap_levels < 1:
            raise ValueError("Number of bitmap levels must be GEQ 1.")

        if self.is_logically_partitioned:
            if not self.bitmap_width:
                raise ValueError("Bitmap width must be specified if "
                                 "logical partitioning is enabled.")

            # TODO(natre): Remove after implementing intra-level partitioning
            if not math.log(self.num_lps, self.bitmap_width).is_integer():
                raise ValueError("Number of logical partitions must be a "
                                 "power of the bitmap width.")


    def emit_prologue(self) -> None:
        """Emit the module definition."""
        self.codegen.emit("import heap_ops::*;")
        self.codegen.comment("`define DEBUG")
        self.codegen.emit()

        self.codegen.comment([
            "Implements an integer priority queue in hardware using a configurable",
            "Hierarchical Find First Set (HFFS) Queue. The implementation is fully",
            "pipelined, capable of performing one operation (enqueue, dequeue-*,",
            "or peek) every cycle.",
        ], True)

        self.codegen.emit("module bbq #(")
        self.codegen.inc_level()
        self.codegen.emit([
            (None if self.is_logically_partitioned
             else "parameter HEAP_BITMAP_WIDTH = 4,"),

            "parameter HEAP_ENTRY_DWIDTH = 17,",
            "parameter HEAP_MAX_NUM_ENTRIES = ((1 << 17) - 1),",
        ])
        if self.is_logically_partitioned:
            self.codegen.emit([
                ("localparam HEAP_BITMAP_WIDTH = {}, {}".format(
                    self.bitmap_width, "// Bitmap bit-width")),

                ("localparam HEAP_NUM_LPS = {}, {}".format(
                    self.num_lps, "// Number of logical BBQs")),

                "localparam HEAP_LOGICAL_BBQ_AWIDTH = ($clog2(HEAP_NUM_LPS)),",
            ])
        self.codegen.emit([
            "localparam HEAP_ENTRY_AWIDTH = ($clog2(HEAP_MAX_NUM_ENTRIES)),",
            ("localparam HEAP_NUM_LEVELS = {}, {}".format(
                self.num_bitmap_levels, "// Number of bitmap tree levels")),

            "localparam HEAP_NUM_PRIORITIES = (HEAP_BITMAP_WIDTH ** HEAP_NUM_LEVELS),",
        ])
        self.codegen.emit([
            "localparam HEAP_PRIORITY_BUCKETS_AWIDTH = ($clog2(HEAP_NUM_PRIORITIES)){}"
            .format("," if self.is_logically_partitioned else ""),
        ])
        if self.is_logically_partitioned:
            self.codegen.emit([
                "localparam HEAP_NUM_PRIORITIES_PER_LP = (HEAP_NUM_PRIORITIES / HEAP_NUM_LPS),",
                "localparam HEAP_PRIORITY_BUCKETS_LP_AWIDTH = ($clog2(HEAP_NUM_PRIORITIES_PER_LP))",
            ])

        self.codegen.dec_level()
        self.codegen.emit(") (")
        self.codegen.inc_level()

        self.codegen.comment("General I/O")
        self.codegen.emit([
            "input   logic                                       clk,",
            "input   logic                                       rst,",
            "output  logic                                       ready,",
        ])
        self.codegen.emit()

        self.codegen.comment("Operation input")
        self.codegen.emit([
            "input   logic                                       in_valid,",
            "input   heap_op_t                                   in_op_type,",
            "input   logic [HEAP_ENTRY_DWIDTH-1:0]               in_he_data,",
            "input   logic [HEAP_PRIORITY_BUCKETS_AWIDTH-1:0]    in_he_priority,",
        ])
        self.codegen.emit()

        self.codegen.comment("Operation output")
        self.codegen.emit([
            "output  logic                                       out_valid,",
            "output  heap_op_t                                   out_op_type,",
            "output  logic [HEAP_ENTRY_DWIDTH-1:0]               out_he_data,",
            "output  logic [HEAP_PRIORITY_BUCKETS_AWIDTH-1:0]    out_he_priority",
        ])

        self.codegen.dec_level()
        self.codegen.emit(");")
        self.codegen.emit()


    def emit_typedefs(self) -> None:
        """Emit param and type definitions."""
        self.codegen.comment([
            "Optimization: Subtree occupancy counters (StOCs) must represent",
            "values in the range [0, HEAP_MAX_NUM_ENTRIES]. Consequently, to",
            "support 2^k entries, every StOC must be (k + 1)-bits wide; this",
            "is wasteful because the MSb is only ever used to encode maximum",
            "occupancy (2^k). Instead, by supporting one less entry (2^k - 1)",
            "we can reduce memory usage by using 1 fewer bit per StOC.",
        ])
        self.codegen.emit([
            "localparam ROUNDED_MAX_NUM_ENTRIES = (1 << HEAP_ENTRY_AWIDTH);",
        ])
        self.codegen.start_conditional(
            "if", "HEAP_MAX_NUM_ENTRIES != (ROUNDED_MAX_NUM_ENTRIES - 1)")

        self.codegen.emit([
            "$error(\"HEAP_MAX_NUM_ENTRIES must be of the form (2^k - 1)\");",
        ])
        self.codegen.end_conditional("if")
        self.codegen.emit()

        self.codegen.emit([
            "integer i;",
            "integer j;"
        ])
        self.codegen.emit()

        self.codegen.comment("Derived parameters.", True)
        self.codegen.align_defs([
            ("localparam NUM_PIPELINE_STAGES", "= {};"
             .format(self.num_pipeline_stages))
        ])

        self.codegen.emit()
        # Emit the bitmap counts
        for i in range(1, (self.num_bitmap_levels + 1)):
            lhs = "localparam NUM_BITMAPS_L{}".format(i)
            rhs = "= {};".format(1 if (i == 1) else
                                 "(HEAP_BITMAP_WIDTH ** {})".format(i - 1))

            self.codegen.align_defs([(lhs, rhs)])

        # Emit the bitmap address widths
        for i in range(2, (self.num_bitmap_levels + 1)):
            lhs = "localparam BITMAP_L{}_AWIDTH".format(i)
            rhs = "= ($clog2(NUM_BITMAPS_L{}));".format(i)

            self.codegen.align_defs([(lhs, rhs)])

        self.codegen.emit()
        # Emit the StOC counts
        for i in range(1, (self.num_bitmap_levels + 1)):
            lhs = "localparam NUM_COUNTERS_L{}".format(i)
            rhs = "= {};".format("(HEAP_NUM_PRIORITIES)"
                                 if (i == self.num_bitmap_levels)
                                 else "(NUM_BITMAPS_L{})".format(i + 1))

            self.codegen.align_defs([(lhs, rhs)])

        # Emit counter width
        self.codegen.align_defs([(
            "localparam COUNTER_T_WIDTH",
            "= (HEAP_ENTRY_AWIDTH + 1);"
        )])

        # Emit the StOC address widths
        for i in range(1, (self.num_bitmap_levels + 1)):
            lhs = "localparam COUNTER_L{}_AWIDTH".format(i)
            rhs = "= ($clog2(NUM_COUNTERS_L{}));".format(i)

            self.codegen.align_defs([(lhs, rhs)])

        self.codegen.emit()
        self.codegen.align_defs([
            ("localparam WATERLEVEL_IDX",           "= (COUNTER_T_WIDTH - 1);"),
            ("localparam LIST_T_WIDTH",             "= (HEAP_ENTRY_AWIDTH * 2);"),
            ("localparam BITMAP_IDX_MASK",          "= (HEAP_BITMAP_WIDTH - 1);"),
            ("localparam HEAP_LOG_BITMAP_WIDTH",    "= ($clog2(HEAP_BITMAP_WIDTH));"),
        ])

        self.codegen.emit()
        self.codegen.comment("Local typedefs.", True)
        self.codegen.emit([
            "typedef logic [COUNTER_T_WIDTH-1:0] counter_t;",
            "typedef logic [HEAP_BITMAP_WIDTH-1:0] bitmap_t;",
        ])
        if self.is_logically_partitioned:
            self.codegen.emit([
                "typedef logic [HEAP_LOGICAL_BBQ_AWIDTH-1:0] bbq_id_t;"
            ])
        self.codegen.emit([
            "typedef logic [HEAP_ENTRY_AWIDTH-1:0] heap_entry_ptr_t;",
            "typedef logic [HEAP_ENTRY_DWIDTH-1:0] heap_entry_data_t;",
            "typedef logic [HEAP_PRIORITY_BUCKETS_AWIDTH-1:0] heap_priority_t;",
            "typedef struct packed { heap_entry_ptr_t head; heap_entry_ptr_t tail; } list_t;",
        ])

        self.codegen.emit()
        self.codegen.enum("fsm_state_t",
                          ["FSM_STATE_IDLE", "FSM_STATE_INIT", "FSM_STATE_READY"])

        self.codegen.emit()
        self.codegen.enum("op_color_t",
                          ["OP_COLOR_BLUE", "OP_COLOR_RED"])

        self.codegen.emit()
        self.codegen.enum("read_carry_direction_t",
                          ["READ_CARRY_RIGHT", "READ_CARRY_DOWN", "READ_CARRY_UP"])

        self.codegen.emit()


    def emit_defs(self):
        """Emit common state logic."""
        self.codegen.comment("Heap state")

        # Emit register-based bitmaps
        for level in self.bitmap_levels:
            if not level.sram_bitmap:
                var = ("l1_bitmap; // L1 bitmap" if (level.id == 1)
                       else ("{0}_bitmaps[NUM_BITMAPS_L{1}-1:0"
                             "]; // L{1} bitmaps".format(level.name(), level.id)))

                self.codegen.emit("bitmap_t " + var)

        # Emit register-based counters
        for level in self.bitmap_levels:
            if not level.sram_counters:
                var = ("{0}_counters[NUM_COUNTERS_L{1}-1:0"
                       "]; // L{1} counters".format(level.name(), level.id))

                self.codegen.emit("counter_t " + var)

        self.codegen.emit()

        # Emit free list signals
        self.codegen.comment("Free list")
        self.codegen.emit([
            "logic fl_empty;",
            "logic fl_rdreq;",
            "logic fl_wrreq;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] fl_q;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] fl_data;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] fl_q_r[{}:0];".format(self.fl_rd_delay - 1),
            "logic [HEAP_ENTRY_AWIDTH-1:0] fl_wraddress_counter_r;",
        ])
        self.codegen.emit()

        # Emit heap entries
        self.codegen.comment("Heap entries")
        self.codegen.emit([
            "logic he_rden;",
            "logic he_wren;",
            "logic he_rden_r;",
            "logic he_wren_r;",
            "logic [HEAP_ENTRY_DWIDTH-1:0] he_q;",
            "logic [HEAP_ENTRY_DWIDTH-1:0] he_data;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] he_rdaddress;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] he_wraddress;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] he_rdaddress_r;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] he_wraddress_r;",
        ])
        self.codegen.emit()

        # Emit next pointers
        self.codegen.comment("Next pointers")
        self.codegen.emit([
            "logic np_rden;",
            "logic np_wren;",
            "logic np_rden_r;",
            "logic np_wren_r;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] np_q;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] np_data;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] np_rdaddress;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] np_wraddress;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] np_rdaddress_r;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] np_wraddress_r;",
        ])
        self.codegen.emit()

        # Emit previous pointers
        self.codegen.comment("Previous pointers")
        self.codegen.emit([
            "logic pp_rden;",
            "logic pp_wren;",
            "logic pp_rden_r;",
            "logic pp_wren_r;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] pp_q;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] pp_data;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] pp_rdaddress;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] pp_wraddress;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] pp_rdaddress_r;",
            "logic [HEAP_ENTRY_AWIDTH-1:0] pp_wraddress_r;",
        ])
        self.codegen.emit()

        # Emit priority buckets
        self.codegen.comment("Priority buckets")
        self.codegen.emit([
            "logic pb_rden;",
            "logic pb_wren;",
            "logic pb_rdwr_conflict;",
            "logic reg_pb_rdwr_conflict_r1;",
            "logic reg_pb_rdwr_conflict_r2;",
            "logic [LIST_T_WIDTH-1:0] pb_q;",
            "logic [LIST_T_WIDTH-1:0] pb_q_r;",
            "logic [LIST_T_WIDTH-1:0] pb_data;",
            "logic [HEAP_PRIORITY_BUCKETS_AWIDTH-1:0] pb_rdaddress;",
            "logic [HEAP_PRIORITY_BUCKETS_AWIDTH-1:0] pb_wraddress;",
        ])
        self.codegen.emit()

        # Emit SRAM-based bitmaps and counters
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.comment("L{} bitmaps".format(level.id))
                self.codegen.emit([
                    "logic bm_{}_rden;".format(level.name()),
                    "logic bm_{}_wren;".format(level.name()),
                    "logic [HEAP_BITMAP_WIDTH-1:0] bm_{}_q;".format(level.name()),
                    "logic [HEAP_BITMAP_WIDTH-1:0] bm_{}_data;".format(level.name()),
                    "logic [HEAP_BITMAP_WIDTH-1:0] bm_{}_data_r;".format(level.name()),
                    "logic [BITMAP_L{}_AWIDTH-1:0] bm_{}_rdaddress;".format(level.id, level.name()),
                    "logic [BITMAP_L{}_AWIDTH-1:0] bm_{}_wraddress;".format(level.id, level.name()),
                    "logic [BITMAP_L{}_AWIDTH-1:0] bm_{}_wraddress_counter_r;".format(level.id, level.name()),
                ])
                self.codegen.emit()

            if level.sram_counters:
                self.codegen.comment("L{} counters".format(level.id))
                self.codegen.emit([
                    "logic counter_{}_rden;".format(level.name()),
                    "logic counter_{}_wren;".format(level.name()),
                    "logic [COUNTER_T_WIDTH-1:0] counter_{}_q;".format(level.name()),
                    "logic [COUNTER_T_WIDTH-1:0] counter_{}_data;".format(level.name()),
                    "logic [COUNTER_L{}_AWIDTH-1:0] counter_{}_rdaddress;".format(level.id, level.name()),
                    "logic [COUNTER_L{}_AWIDTH-1:0] counter_{}_wraddress;".format(level.id, level.name()),
                    "logic [COUNTER_L{}_AWIDTH-1:0] counter_{}_wraddress_counter_r;".format(level.id, level.name()),
                ])
                self.codegen.emit()

        if self.is_logically_partitioned:
            self.codegen.comment("Heap occupancy per logical BBQ")
            self.codegen.emit("counter_t occupancy[HEAP_NUM_LPS-1:0];")
        else:
            self.codegen.comment("Heap occupancy")
            self.codegen.emit("counter_t occupancy;")

        self.codegen.emit()

        # Emit common pipeline stage data
        self.codegen.comment("Housekeeping.", True)
        self.codegen.comment("Common pipeline metadata")
        self.codegen.align_defs([
            ("logic", "reg_valid_s[NUM_PIPELINE_STAGES:0];"),
            ("bbq_id_t", ("reg_bbq_id_s[NUM_PIPELINE_STAGES:0];"
                          if self.is_logically_partitioned else None)),

            ("heap_op_t", "reg_op_type_s[NUM_PIPELINE_STAGES:0];"),
            ("heap_entry_data_t", "reg_he_data_s[NUM_PIPELINE_STAGES:0];"),
        ])
        for level in self.bitmap_levels:
            if level.id > 1:
                self.codegen.align_defs([
                    ("logic [BITMAP_L{}_AWIDTH-1:0]".format(level.id),
                    "reg_{}_addr_s[NUM_PIPELINE_STAGES:0];".format(level.name()))
                ])
        self.codegen.align_defs([
            ("op_color_t", "reg_op_color_s[NUM_PIPELINE_STAGES:0];"),
            ("logic", "reg_is_enque_s[NUM_PIPELINE_STAGES:0];"),
            ("heap_priority_t", "reg_priority_s[NUM_PIPELINE_STAGES:0];"),
        ])
        for level in self.bitmap_levels:
            if level.id > 1:
                self.codegen.align_defs([
                    ("bitmap_t",
                    "reg_{}_bitmap_s[NUM_PIPELINE_STAGES:0];".format(level.name()))
                ])
        self.codegen.align_defs([
            ("logic", "reg_is_deque_min_s[NUM_PIPELINE_STAGES:0];"),
            ("logic", "reg_is_deque_max_s[NUM_PIPELINE_STAGES:0];"),
        ])
        self.codegen.emit()

        # Emit per-stage defs
        if self.is_logically_partitioned:
            self.codegen.comment("Stage 0 metadata")
            self.codegen.align_defs([
                ("bbq_id_t", "bbq_id_s0;")
            ])
            self.codegen.emit()

        for level in self.levels:
            level.emit_stage_defs(self.codegen)

        # Init signals
        self.codegen.comment("Init signals")
        self.codegen.align_defs([
            ("fsm_state_t", "state = FSM_STATE_IDLE;"),
        ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.align_defs([
                    ("logic", "counter_{}_init_done_r;".format(level.name())),
                ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.align_defs([
                    ("logic", "bm_{}_init_done_r;".format(level.name())),
                ])
        self.codegen.align_defs([
            ("logic", "fl_init_done_r;"),
        ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.align_defs([
                    ("logic", "counter_{}_init_done;".format(level.name())),
                ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.align_defs([
                    ("logic", "bm_{}_init_done;".format(level.name())),
                ])
        self.codegen.align_defs([
            ("logic", "fl_init_done;"),
            ("fsm_state_t", "state_next;"),
        ])
        self.codegen.emit()

        self.codegen.comment("Intermediate signals")
        self.codegen.align_defs([
            ("list_t", "int_pb_data;"),
            ("list_t", "int_pb_q;"),
        ])
        self.codegen.emit()

        self.codegen.comment("Miscellaneous signals")
        for level in self.bitmap_levels:
            num_ffs_insts = 2 + int(
                level.sram_counters)

            self.codegen.align_defs([
                ("logic [HEAP_LOG_BITMAP_WIDTH-1:0]",
                 "ffs_{}_inst_msb[{}:0];".format(
                    level.name(), (num_ffs_insts - 1))),

                ("logic [HEAP_LOG_BITMAP_WIDTH-1:0]",
                 "ffs_{}_inst_lsb[{}:0];".format(
                    level.name(), (num_ffs_insts - 1))),

                ("logic", ("ffs_{}_inst_zero[{}:0];".
                           format(level.name(), (num_ffs_insts - 1)))),

                ("bitmap_t", ("ffs_{}_inst_msb_onehot[{}:0];".
                              format(level.name(), (num_ffs_insts - 1)))),

                ("bitmap_t", ("ffs_{}_inst_lsb_onehot[{}:0];".
                              format(level.name(), (num_ffs_insts - 1)))),
            ])
            self.codegen.emit()

        self.codegen.start_ifdef("DEBUG")
        self.codegen.align_defs([("logic", "debug_newline;")])
        self.codegen.end_ifdef()
        self.codegen.emit()


    def emit_initial(self):
        """Emit initial and global output assignments."""

        # Global output assignments
        self.codegen.emit("assign pb_data = int_pb_data;")
        self.codegen.emit()

        self.codegen.comment("Output assignments")
        self.codegen.emit([
            "assign ready = !rst & (state == FSM_STATE_READY);",
            "assign out_valid = reg_valid_s[NUM_PIPELINE_STAGES-1];",
            "assign out_op_type = reg_op_type_s[NUM_PIPELINE_STAGES-1];",
            "assign out_he_data = reg_he_data_s[NUM_PIPELINE_STAGES-1];",
            "assign out_he_priority = reg_priority_s[NUM_PIPELINE_STAGES-1];",
        ])
        self.codegen.emit()


    def emit_combinational_default_assigns(self) -> None:
        """Emit default assignments."""
        # Per-level defaults
        if self.is_logically_partitioned:
            self.codegen.align_assignment("bbq_id_s0",
                ["in_he_priority[HEAP_PRIORITY_BUCKETS_AWIDTH-1:",
                 "              HEAP_PRIORITY_BUCKETS_LP_AWIDTH];"
            ], "=")

        for level in self.levels:
            level.emit_combinational_default_assigns(self.codegen)

        # Global defaults
        self.codegen.emit()
        pb_end_cycle = self.levels[-1].end_cycle
        self.codegen.emit([
            "int_pb_q = pb_q_r;",
        ])
        self.codegen.emit()

        self.codegen.emit([
            "fl_rdreq = 0;",
        ])
        self.codegen.emit()

        self.codegen.emit([
            "he_rden = 0;",
            "he_wren = 0;",
            "he_data = reg_he_data_s[{}];".format(pb_end_cycle - 1),
            "he_wraddress = fl_q_r[{}];".format(self.fl_rd_delay - 1),
        ])
        self.codegen.emit()
        self.codegen.emit([
            "np_rden = 0;",
            "np_wren = 0;",
            ("np_data = reg_pb_q_s{}.head;"
             .format(pb_end_cycle - 1)),
            "np_wraddress = fl_q_r[{}];".format(self.fl_rd_delay - 1),
        ])
        self.codegen.emit()
        self.codegen.emit([
            "pp_rden = 0;",
            "pp_wren = 0;",
            "pp_data = fl_q_r[{}];".format(self.fl_rd_delay - 1),
            ("pp_wraddress = reg_pb_q_s{}.head;"
             .format(pb_end_cycle - 1)),
        ])
        self.codegen.emit()
        self.codegen.emit([
            "pb_rdwr_conflict = 0;",
            "pb_rdaddress = priority_s{};".format(self.levels[-2].end_cycle),
            "int_pb_data = reg_pb_new_s{};".format(pb_end_cycle - 1),
            "pb_wraddress = reg_priority_s[{}];".format(pb_end_cycle - 1),
        ])
        self.codegen.emit()

        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.emit([
                    "bm_{}_rden = 0;".format(level.name()),
                ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.emit([
                    "counter_{}_rden = 0;".format(level.name()),
                ])
        if self.num_bitmap_levels > 1:
            self.codegen.emit()


    def emit_init_state(self) -> None:
        """Emit init state definition."""
        self.codegen.comment("Free list")
        self.codegen.emit([
            "fl_data = fl_wraddress_counter_r;"
        ])
        self.codegen.start_conditional("if", "!fl_init_done_r")
        done_condition_list = ["fl_init_done_r"]
        self.codegen.emit([
            "fl_wrreq = 1;",
        ])
        self.codegen.align_assignment("fl_init_done", [
            "(fl_wraddress_counter_r ==",
            "(HEAP_MAX_NUM_ENTRIES - 1));"
        ], "=")
        self.codegen.end_conditional("if")

        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.comment("L{} bitmaps".format(level.id))
                self.codegen.emit([
                    "bm_{}_data = 0;".format(level.name()),
                    ("bm_{0}_wraddress = "
                     "bm_{0}_wraddress_counter_r;".format(level.name())),
                ])
                self.codegen.start_conditional("if",
                    "!bm_{}_init_done_r".format(level.name()))

                done_condition_list[-1] += " & "
                done_condition_list.append("bm_{}_init_done_r".format(level.name()))

                self.codegen.emit([
                    "bm_{}_wren = 1;".format(level.name()),
                ])
                self.codegen.align_assignment(
                    "bm_{}_init_done".format(level.name()),
                    ["(bm_{}_wraddress_counter_r ==".format(level.name()),
                     "(NUM_BITMAPS_L{} - 1));".format(level.id)], "=")

                self.codegen.end_conditional("if")

            if level.sram_counters:
                self.codegen.comment("L{} counters".format(level.id))
                self.codegen.emit([
                    "counter_{}_data = 0;".format(level.name()),
                    ("counter_{0}_wraddress = "
                     "counter_{0}_wraddress_counter_r;".format(level.name())),
                ])
                self.codegen.start_conditional("if",
                    "!counter_{}_init_done_r".format(level.name()))

                done_condition_list[-1] += " & "
                done_condition_list.append("counter_{}_init_done_r".format(level.name()))

                self.codegen.emit([
                    "counter_{}_wren = 1;".format(level.name()),
                ])
                self.codegen.align_assignment(
                    "counter_{}_init_done".format(level.name()),
                    ["(counter_{}_wraddress_counter_r ==".format(level.name()),
                     "(NUM_COUNTERS_L{} - 1));".format(level.id)], "=")

                self.codegen.end_conditional("if")

        self.codegen.comment([
            "Finished initializing the queue (including priority buckets,",
            "free list, and the LX bitmaps). Proceed to the ready state."
        ])
        done_condition = [("".join(v)).strip() for v in list(
            partition(3, done_condition_list, ""))]

        self.codegen.start_conditional("if", done_condition)
        self.codegen.emit("state_next = FSM_STATE_READY;")
        self.codegen.end_conditional("if")


    def emit_state_dependent_combinational_logic(self) -> None:
        """Emit the state-dependent combinational block."""
        self.codegen.comment([
            "State-dependent signals (data, wraddress, and wren) for the",
            "FL, priority buckets and SRAM-based LX bitmaps and counters.",
        ], True)
        self.codegen.start_block("always_comb")
        self.codegen.emit([
            "state_next = state;",
            "fl_init_done = fl_init_done_r;",
        ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.emit([
                    "bm_{0}_init_done = "
                    "bm_{0}_init_done_r;".format(level.name()),
                ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.emit([
                    "counter_{0}_init_done = "
                    "counter_{0}_init_done_r;".format(level.name()),
                ])
        self.codegen.emit()

        self.codegen.emit([
            "fl_wrreq = 0;",
        ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.emit([
                    "bm_{}_wren = 0;".format(level.name()),
                ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.emit([
                    "counter_{}_wren = 0;".format(level.name()),
                ])
        self.codegen.emit()

        self.codegen.comment("Initialization state")
        self.codegen.start_conditional("if", "state == FSM_STATE_INIT")
        self.emit_init_state()
        self.codegen.end_conditional("if")

        self.codegen.start_conditional("else", None)
        for level in reversed(self.levels):
            level.emit_state_dependent_combinational_logic(self.codegen)

        self.codegen.end_conditional("else")
        self.codegen.end_block("always_comb")
        self.codegen.emit()


    def emit_state_agnostic_combinational_logic(self) -> None:
        """Emit the state-agnostic combinational block."""
        self.codegen.comment("State-independent logic.", True)
        self.codegen.start_block("always_comb")
        self.emit_combinational_default_assigns()

        for level in reversed(self.levels):
            level.emit_state_agnostic_combinational_logic(self.codegen)

        self.codegen.start_ifdef("DEBUG")
        self.codegen.comment([
            "Print a newline between pipeline output across timesteps."
        ], True)
        self.codegen.emit("debug_newline = in_valid;")
        self.codegen.start_for("j", "j < (NUM_PIPELINE_STAGES - 1)")
        self.codegen.emit("debug_newline |= reg_valid_s[j];")
        self.codegen.end_for()
        self.codegen.end_ifdef()

        self.codegen.end_block("always_comb")
        self.codegen.emit()


    def emit_sequential_rst_state(self) -> None:
        """Emits the reset state logic."""
        self.codegen.comment("Reset occupancy")
        if self.is_logically_partitioned:
            self.codegen.start_for(
                "i", "i < HEAP_NUM_LPS"
            )
            self.codegen.emit("occupancy[i] <= 0;")
            self.codegen.end_for()
        else:
            self.codegen.emit("occupancy <= 0;")

        self.codegen.emit()

        self.codegen.comment("Reset bitmaps")
        for level in self.bitmap_levels:
            if not level.sram_bitmap:
                if level.id == 1:
                    self.codegen.emit("l1_bitmap <= 0;")
                else:
                    self.codegen.start_for(
                        "i", "i < NUM_BITMAPS_L{}".format(level.id))

                    self.codegen.emit("{}_bitmaps[i] <= 0;".format(level.name()))
                    self.codegen.end_for()

            if not level.sram_counters:
                self.codegen.start_for(
                    "i", "i < NUM_COUNTERS_L{}".format(level.id))

                self.codegen.emit("{}_counters[i] <= 0;".format(level.name()))
                self.codegen.end_for()

        self.codegen.emit()
        self.codegen.comment("Reset pipeline stages")
        self.codegen.start_for("i", "i <= NUM_PIPELINE_STAGES")
        self.codegen.emit("reg_valid_s[i] <= 0;")
        self.codegen.end_for()

        self.codegen.emit()
        self.codegen.comment("Reset init signals")
        self.codegen.emit([
            "fl_init_done_r <= 0;",
        ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.emit([
                    "bm_{}_init_done_r <= 0;".format(level.name()),
                ])
        self.codegen.emit([
            "fl_wraddress_counter_r <= 0;",
        ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.emit([
                    "counter_{}_init_done_r <= 0;".format(level.name()),
                ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.emit([
                    "bm_{}_wraddress_counter_r <= 0;".format(level.name()),
                ])
        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.emit([
                    "counter_{}_wraddress_counter_r <= 0;".format(level.name()),
                ])

        self.codegen.emit()
        self.codegen.comment("Reset FSM state")
        self.codegen.emit([
            "state <= FSM_STATE_INIT;",
        ])


    def emit_sequential_common_logic(self) -> None:
        """Emit misc assigns and global logic."""
        self.codegen.comment("Stage 0: Register inputs.", True)

        if self.is_logically_partitioned:
            self.codegen.emit("reg_bbq_id_s[0] <= bbq_id_s0;")

        self.codegen.emit([
            "reg_op_type_s[0] <= in_op_type;",
            "reg_he_data_s[0] <= in_he_data;",
            "reg_priority_s[0] <= in_he_priority;",
            "reg_valid_s[0] <= (ready & in_valid);",
            "reg_is_enque_s[0] <= (in_op_type == HEAP_OP_ENQUE);",
            "reg_is_deque_max_s[0] <= (in_op_type == HEAP_OP_DEQUE_MAX);",
            "reg_is_deque_min_s[0] <= (in_op_type == HEAP_OP_DEQUE_MIN);",
        ])
        self.codegen.emit()

        self.codegen.start_ifdef("DEBUG")
        id_str = (" (logical ID: %0d)"
                  if self.is_logically_partitioned else "")

        id_val = ("bbq_id_s0, "
                  if self.is_logically_partitioned else "")

        priority_str_prefix = ("relative "
                               if self.is_logically_partitioned else "")

        priority_val_suffix = (" & (HEAP_NUM_PRIORITIES_PER_LP - 1)"
                               if self.is_logically_partitioned else "")

        self.codegen.start_conditional("if", "in_valid")
        self.codegen.start_conditional("if", "in_op_type == HEAP_OP_ENQUE")
        self.codegen.emit([
            ("$display(\"[BBQ] At S0{}, enqueing %0d with {}priority %0d\","
             .format(id_str, priority_str_prefix)),

            ("         {}in_he_data, in_he_priority{});"
             .format(id_val, priority_val_suffix)),
        ])
        self.codegen.end_conditional("if")
        self.codegen.start_conditional("else", None)

        self.codegen.emit([
            "$display(\"[BBQ] At S0{}, performing %s\",".format(id_str),
            "         {}in_op_type.name);".format(id_val),
        ])
        self.codegen.end_conditional("else")
        self.codegen.end_conditional("if")
        self.codegen.emit()

        self.codegen.start_conditional("if", "debug_newline")
        self.codegen.emit("$display(\"\");")
        self.codegen.end_conditional("if")

        self.codegen.start_conditional("if", [
            "(state == FSM_STATE_INIT) &&",
            "(state_next == FSM_STATE_READY)"
        ])
        self.codegen.emit("$display(\"[BBQ] Heap initialization complete!\");")
        self.codegen.end_conditional("if")
        self.codegen.end_ifdef()
        self.codegen.emit()

        self.codegen.comment("Register init signals")
        done_signals = ["fl_init_done"]
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                done_signals.append("bm_{}_init_done".format(level.name()))

            if level.sram_counters:
                done_signals.append("counter_{}_init_done".format(level.name()))

        for signal in sorted(done_signals, key=lambda x: len(x)):
            self.codegen.emit("{0}_r <= {0};".format(signal))

        self.codegen.emit()
        counter_signals = ["fl_wraddress_counter_r"]

        for level in self.bitmap_levels:
            if level.sram_bitmap:
                counter_signals.append(
                    "bm_{}_wraddress_counter_r".format(level.name()))

            if level.sram_counters:
                counter_signals.append(
                    "counter_{}_wraddress_counter_r".format(level.name()))

        for signal in sorted(counter_signals, key=lambda x: len(x)):
            self.codegen.emit("{0} <= {0} + 1;".format(signal))

        self.codegen.emit()
        self.codegen.comment("Register read signals")
        self.codegen.emit([
            "pb_q_r <= pb_q;",
            "he_rden_r <= he_rden;",
            "np_rden_r <= np_rden;",
            "pp_rden_r <= pp_rden;",
            "he_rdaddress_r <= he_rdaddress;",
            "np_rdaddress_r <= np_rdaddress;",
            "pp_rdaddress_r <= pp_rdaddress;",
        ])
        self.codegen.emit()
        self.codegen.comment("Register write signals")
        self.codegen.emit([
            "he_wren_r <= he_wren;",
            "np_wren_r <= np_wren;",
            "pp_wren_r <= pp_wren;",
        ])
        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.emit("bm_{0}_data_r <= bm_{0}_data;"
                                  .format(level.name()))
        self.codegen.emit([
            "he_wraddress_r <= he_wraddress;",
            "np_wraddress_r <= np_wraddress;",
            "pp_wraddress_r <= pp_wraddress;",
        ])
        self.codegen.emit()

        self.codegen.emit("fl_q_r[0] <= fl_q;")
        self.codegen.start_for("i", "i < {}".format(self.fl_rd_delay - 1))
        self.codegen.emit("fl_q_r[i + 1] <= fl_q_r[i];")
        self.codegen.end_for()
        self.codegen.emit()

        self.codegen.comment("Register R/W conflict signals")
        self.codegen.emit([
            "reg_pb_rdwr_conflict_r1 <= pb_rdwr_conflict;",
            "reg_pb_rdwr_conflict_r2 <= reg_pb_rdwr_conflict_r1;",
        ])
        self.codegen.emit()

        self.codegen.comment("Update FSM state")
        self.codegen.emit("state <= state_next;")


    def emit_sequential_primary_signals(self, cycle: int,
                      value_override: dict=None) -> None:
        """Emits the primary pipeline signals."""
        if value_override is None:
            value_override = dict()

        signals = ["reg_valid_s",
                   "reg_he_data_s",
                   "reg_op_type_s",
                   "reg_is_enque_s",
                   "reg_priority_s",
                   "reg_is_deque_max_s",
                   "reg_is_deque_min_s"]

        if self.is_logically_partitioned:
            signals.insert(1, "reg_bbq_id_s")

        for signal in signals:
            v = value_override.get(signal)
            if not v: v = "{}[{}]".format(signal, cycle - 1)
            self.codegen.emit("{}[{}] <= {};".format(signal, cycle, v))

        self.codegen.emit()


    def emit_sequential_pipeline_logic(self) -> None:
        """Emit the sequential logic block."""
        self.codegen.start_block("always @(posedge clk)")
        self.codegen.start_conditional("if", "rst")
        self.emit_sequential_rst_state()
        self.codegen.end_conditional("if")

        self.codegen.start_conditional("else", None)
        for level in reversed(self.levels):
            level.emit_sequential_pipeline_logic(self.codegen)

        self.emit_sequential_common_logic()
        self.codegen.end_conditional("else")
        self.codegen.end_block("always @(posedge clk)")
        self.codegen.emit()


    def emit_module_instantiations(self) -> None:
        """Emit submodule instantiation code."""
        self.codegen.comment("Free list")
        self.codegen.emit([
            "sc_fifo #(",
            "    .DWIDTH(HEAP_ENTRY_AWIDTH),",
            "    .DEPTH(HEAP_MAX_NUM_ENTRIES),",
            "    .IS_SHOWAHEAD(0),",
            "    .IS_OUTDATA_REG(1)",
            ")",
            "free_list (",
            "    .clock(clk),",
            "    .data(fl_data),",
            "    .rdreq(fl_rdreq),",
            "    .wrreq(fl_wrreq),",
            "    .empty(fl_empty),",
            "    .full(),",
            "    .q(fl_q),",
            "    .usedw()",
            ");",
        ])
        self.codegen.emit()

        self.codegen.comment("Heap entries")
        self.codegen.emit([
            "bram_simple2port #(",
            "    .DWIDTH(HEAP_ENTRY_DWIDTH),",
            "    .AWIDTH(HEAP_ENTRY_AWIDTH),",
            "    .DEPTH(HEAP_MAX_NUM_ENTRIES),",
            "    .IS_OUTDATA_REG(0)",
            ")",
            "heap_entries (",
            "    .clock(clk),",
            "    .data(he_data),",
            "    .rden(he_rden),",
            "    .wren(he_wren),",
            "    .rdaddress(he_rdaddress),",
            "    .wraddress(he_wraddress),",
            "    .q(he_q)",
            ");",
        ])
        self.codegen.emit()

        self.codegen.comment("Next pointers")
        self.codegen.emit([
            "bram_simple2port #(",
            "    .DWIDTH(HEAP_ENTRY_AWIDTH),",
            "    .AWIDTH(HEAP_ENTRY_AWIDTH),",
            "    .DEPTH(HEAP_MAX_NUM_ENTRIES),",
            "    .IS_OUTDATA_REG(0)",
            ")",
            "next_pointers (",
            "    .clock(clk),",
            "    .data(np_data),",
            "    .rden(np_rden),",
            "    .wren(np_wren),",
            "    .rdaddress(np_rdaddress),",
            "    .wraddress(np_wraddress),",
            "    .q(np_q)",
            ");",
        ])
        self.codegen.emit()

        self.codegen.comment("Previous pointers")
        self.codegen.emit([
            "bram_simple2port #(",
            "    .DWIDTH(HEAP_ENTRY_AWIDTH),",
            "    .AWIDTH(HEAP_ENTRY_AWIDTH),",
            "    .DEPTH(HEAP_MAX_NUM_ENTRIES),",
            "    .IS_OUTDATA_REG(0)",
            ")",
            "previous_pointers (",
            "    .clock(clk),",
            "    .data(pp_data),",
            "    .rden(pp_rden),",
            "    .wren(pp_wren),",
            "    .rdaddress(pp_rdaddress),",
            "    .wraddress(pp_wraddress),",
            "    .q(pp_q)",
            ");",
        ])
        self.codegen.emit()

        self.codegen.comment("Priority buckets")
        self.codegen.emit([
            "bram_simple2port #(",
            "    .DWIDTH(LIST_T_WIDTH),",
            "    .AWIDTH(HEAP_PRIORITY_BUCKETS_AWIDTH),",
            "    .DEPTH(HEAP_NUM_PRIORITIES),",
            "    .IS_OUTDATA_REG(0)",
            ")",
            "priority_buckets (",
            "    .clock(clk),",
            "    .data(pb_data),",
            "    .rden(pb_rden),",
            "    .wren(pb_wren),",
            "    .rdaddress(pb_rdaddress),",
            "    .wraddress(pb_wraddress),",
            "    .q(pb_q)",
            ");",
        ])
        self.codegen.emit()

        for level in self.bitmap_levels:
            if level.sram_bitmap:
                self.codegen.comment("L{} bitmaps".format(level.id))
                self.codegen.emit([
                    "bram_simple2port #(",
                    "    .DWIDTH(HEAP_BITMAP_WIDTH),",
                    "    .AWIDTH(BITMAP_L{}_AWIDTH),".format(level.id),
                    "    .DEPTH(NUM_BITMAPS_L{}),".format(level.id),
                    "    .IS_OUTDATA_REG(0)",
                    ")",
                    "bm_{} (".format(level.name()),
                    "    .clock(clk),",
                    "    .data(bm_{}_data),".format(level.name()),
                    "    .rden(bm_{}_rden),".format(level.name()),
                    "    .wren(bm_{}_wren),".format(level.name()),
                    "    .rdaddress(bm_{}_rdaddress),".format(level.name()),
                    "    .wraddress(bm_{}_wraddress),".format(level.name()),
                    "    .q(bm_{}_q)".format(level.name()),
                    ");",
                ])
                self.codegen.emit()

        for level in self.bitmap_levels:
            if level.sram_counters:
                self.codegen.comment("L{} counters".format(level.id))
                self.codegen.emit([
                    "bram_simple2port #(",
                    "    .DWIDTH(COUNTER_T_WIDTH),",
                    "    .AWIDTH(COUNTER_L{}_AWIDTH),".format(level.id),
                    "    .DEPTH(NUM_COUNTERS_L{}),".format(level.id),
                    "    .IS_OUTDATA_REG(0)",
                    ")",
                    "counters_{} (".format(level.name()),
                    "    .clock(clk),",
                    "    .data(counter_{}_data),".format(level.name()),
                    "    .rden(counter_{}_rden),".format(level.name()),
                    "    .wren(counter_{}_wren),".format(level.name()),
                    "    .rdaddress(counter_{}_rdaddress),".format(level.name()),
                    "    .wraddress(counter_{}_wraddress),".format(level.name()),
                    "    .q(counter_{}_q)".format(level.name()),
                    ");",
                ])
                self.codegen.emit()

        for level in self.bitmap_levels:
            self.codegen.comment("L{} FFSs".format(level.id))
            num_ffs_insts = 2 + int(level.sram_counters)

            for j in range(num_ffs_insts):
                cycle = (level.start_cycle +
                         int(level.sram_bitmap) + j - 1)

                bitmap = ("reg_{}_bitmap_postop_s{}"
                          .format(level.name(), cycle))
                if j == 0:
                    bitmap = ("l1_bitmap" if (level.id == 1) else
                              "reg_{}_bitmap_s[{}]".format(level.name(), cycle))

                self.codegen.emit([
                    "ffs #(",
                    "    .WIDTH_LOG(HEAP_LOG_BITMAP_WIDTH)",
                    ")",
                    "ffs_{}_inst{} (".format(level.name(), j),
                    "    .x({}),".format(bitmap),
                    "    .msb(ffs_{}_inst_msb[{}]),".format(level.name(), j),
                    "    .lsb(ffs_{}_inst_lsb[{}]),".format(level.name(), j),
                    "    .msb_onehot(ffs_{}_inst_msb_onehot[{}]),".format(level.name(), j),
                    "    .lsb_onehot(ffs_{}_inst_lsb_onehot[{}]),".format(level.name(), j),
                    "    .zero(ffs_{}_inst_zero[{}])".format(level.name(), j),
                    ");",
                ])
                self.codegen.emit()


    def emit_epilogue(self) -> None:
        """Emit module trailer."""
        self.codegen.emit("endmodule", indent_first=False,
                          offset=0, trailing_newline=False)


    def generate(self) -> None:
        """Generates the BBQ."""
        self.emit_prologue()
        self.emit_typedefs()
        self.emit_defs()
        self.emit_initial()
        self.emit_state_dependent_combinational_logic()
        self.emit_state_agnostic_combinational_logic()
        self.emit_sequential_pipeline_logic()
        self.emit_module_instantiations()
        self.emit_epilogue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="bbq", description=("Generates a SystemVerilog implementation of BBQ "
                                 "for the specified number of bitmap tree levels."))

    parser.add_argument("num_bitmap_levels", type=int)
    parser.add_argument("--num_lps", type=int, default=1)
    parser.add_argument("--bitmap_width", type=int, default=0)
    args = parser.parse_args()

    bbq = BBQ(args.num_bitmap_levels, args.num_lps, args.bitmap_width)
    bbq.generate()
    print(bbq.codegen.out)
