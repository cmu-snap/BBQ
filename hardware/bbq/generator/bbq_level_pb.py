#!/usr/bin/python3
from bbq_level import BBQLevel
from codegen import CodeGen


class BBQLevelPB(BBQLevel):
    """Represents the PB BBQ level."""
    def __init__(self, start_cycle: int, num_bitmap_levels: int) -> None:
        super().__init__(start_cycle, num_bitmap_levels)


    def name(self) -> str:
        """Canonical level name."""
        return "pb"


    def latency(self) -> int:
        """Latency in cycles."""
        return 3


    def emit_stage_defs(self, cg: CodeGen) -> None:
        """Emit per-stage definitions."""
        cycle = self.start_cycle

        # Read delay for PB
        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("op_color_t", "op_color_s{};".format(cycle)),
            ("logic", "reg_pb_update_s{};".format(cycle)),
            ("logic", "reg_pb_data_conflict_s{};".format(cycle)),
            ("logic", "reg_pb_state_changes_s{};".format(cycle)),
            ("logic", "reg_pb_tail_pp_changes_s{};".format(cycle)),
        ])
        for offset in range(1, 3):
            cg.align_defs([
                ("logic", "reg_pb_addr_conflict_s{}_s{};"
                 .format((cycle + offset), cycle)),
            ])
        cg.emit()
        cycle += 1

        # Read data and pointers
        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("logic", "pp_changes_s{}_s{};".format(cycle + 1, cycle)),
            ("logic", "pp_changes_s{}_s{};".format(cycle + 2, cycle)),
            ("list_t", "reg_pb_q_s{};".format(cycle)),
            ("heap_entry_ptr_t", "reg_pp_data_s{};".format(cycle)),
            ("logic", "reg_pp_data_valid_s{};".format(cycle)),
            ("logic", "reg_pb_data_conflict_s{};".format(cycle)),
            ("logic", "reg_pb_state_changes_s{};".format(cycle)),
            ("logic", "reg_pb_tail_pp_changes_s{};".format(cycle)),
        ])
        for offset in range(1, 3):
            cg.align_defs([
                ("logic", "reg_pb_addr_conflict_s{}_s{};"
                 .format((cycle + offset), cycle)),
            ])
        cg.emit()
        cycle += 1

        # Read delay for data, pointers
        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("heap_entry_data_t", "he_q_s{};".format(cycle)),
            ("heap_entry_ptr_t", "np_q_s{};".format(cycle)),
            ("heap_entry_ptr_t", "pp_q_s{};".format(cycle)),
            ("heap_entry_data_t", "reg_he_q_s{};".format(cycle)),
            ("heap_entry_ptr_t", "reg_np_q_s{};".format(cycle)),
            ("heap_entry_ptr_t", "reg_pp_q_s{};".format(cycle)),
            ("list_t", "reg_pb_q_s{};".format(cycle)),
            ("list_t", "reg_pb_new_s{};".format(cycle)),
            ("logic", "reg_pb_data_conflict_s{};".format(cycle)),
            ("logic", "reg_pb_state_changes_s{};".format(cycle)),
            ("logic", "reg_pb_tail_pp_changes_s{};".format(cycle)),
        ])
        cg.emit()
        cycle += 1

        # Commit writes
        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("heap_entry_data_t", "he_data_s{};".format(cycle)),
            ("heap_entry_data_t", "reg_he_data_s{};".format(cycle)),
            ("heap_entry_ptr_t", "reg_np_data_s{};".format(cycle)),
            ("heap_entry_ptr_t", "reg_pp_data_s{};".format(cycle)),
            ("list_t", "reg_pb_data_s{};".format(cycle)),
        ])
        cg.emit()
        cycle += 1

        # Spillover stage
        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([("list_t", "reg_pb_data_s{};".format(cycle))])
        cg.emit()


    def emit_state_dependent_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-dependent combinational logic."""
        # Commit writes
        seq_cycle = self.end_cycle - 1
        cg.comment([
            ("Stage {}: Perform writes: update the priority bucket,"
             .format(seq_cycle + 1)),
            "the free list, heap entries, next and prev pointers.",
        ], True)
        cg.align_assignment("fl_data", [
            "(",
            "(reg_op_color_s[{}] == OP_COLOR_BLUE) ?".format(seq_cycle),
            "reg_pb_q_s{0}.head : reg_pb_q_s{0}.tail);".format(seq_cycle),
        ], "=", True)
        cg.emit()

        cg.comment("Perform deque")
        cg.start_conditional("if", "!reg_is_enque_s[{}]".format(seq_cycle))
        cg.comment("Update the free list")
        cg.emit([
            "fl_wrreq = reg_valid_s[{}];".format(seq_cycle),
        ])
        cg.end_conditional("if")


    def emit_combinational_default_assigns(self, cg: CodeGen) -> None:
        """Emit default assignments."""
        cycle = self.start_cycle

        # Read delay for PB
        cg.emit([
            ("op_color_s{} = reg_is_enque_s[{}] ? "
             "OP_COLOR_BLUE : OP_COLOR_RED;".format(cycle, (cycle - 1))),
        ])
        cycle += 2

        # Read data and pointers
        # Read delay for data, pointers
        cg.emit([
            "he_q_s{} = he_q;".format(cycle),
            "np_q_s{} = np_q;".format(cycle),
            "pp_q_s{} = pp_q;".format(cycle),
        ])
        cycle += 1


    def emit_state_agnostic_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-agnostic combinational logic."""

        # Commit writes
        seq_cycle = self.end_cycle - 1
        cg.comment([
            "Stage {}: Perform writes: update the priority bucket,".format(seq_cycle + 1),
            "the free list, heap entries, next and prev pointers.",
        ], True)
        cg.emit("pb_wren = reg_valid_s[{}];".format(seq_cycle))
        cg.emit()

        cg.comment("Perform enque")
        cg.start_conditional("if", "reg_is_enque_s[{}]".format(seq_cycle))
        cg.start_conditional("if", "reg_valid_s[{}]".format(seq_cycle))
        cg.emit([
            "he_wren = 1; // Update the heap entry",
            "np_wren = 1; // Update the next pointer",
        ])
        cg.emit()

        cg.comment([
            "Update the entry's previous pointer. The",
            "pointer address is only valid if the PB",
            "was not previously empty, so write must",
            "be predicated on no change of state.",
        ])
        cg.start_conditional(
            "if", "!reg_pb_state_changes_s{}".format(seq_cycle))

        cg.emit("pp_wren = 1;")
        cg.end_conditional("if")
        cg.emit()

        cg.comment("Update the heap size")
        cg.emit("int_size = size + 1'b1;")
        cg.end_conditional("if")
        cg.emit()

        cg.comment("Update the data")
        cg.emit("he_data_s{} = reg_he_data_s[{}];"
                .format((seq_cycle + 1), seq_cycle))
        cg.end_conditional("if")

        cg.comment("Perform deque")
        cg.start_conditional("else", None)
        cg.start_conditional("if", "reg_valid_s[{}]".format(seq_cycle))
        cg.comment("Update the heap size")
        cg.emit("int_size = size - 1'b1;")
        cg.end_conditional("if")
        cg.emit()

        cg.start_conditional("if", ("reg_op_color_s[{}] == OP_COLOR_BLUE"
                                    .format(seq_cycle)))
        cg.comment("BLUE-colored dequeue (from HEAD)")
        cg.emit("int_pb_data.head = reg_np_q_s{};".format(seq_cycle))
        cg.end_conditional("if")
        cg.start_conditional("else", None)
        cg.comment("RED-colored dequeue (from TAIL)")
        cg.emit("int_pb_data.tail = reg_pp_q_s{};".format(seq_cycle))
        cg.end_conditional("else")
        cg.emit()

        cg.comment("Update the data")
        cg.align_assignment("he_data_s{}".format(seq_cycle + 1), [
            "(",
            "reg_pb_data_conflict_s{} ?".format(seq_cycle),
            "reg_he_data_s[{}] : reg_he_q_s{});".format(
                        (seq_cycle + 1), seq_cycle),
        ], "=", True)

        cg.end_conditional("else")
        seq_cycle -= 1

        # Read delay for data, pointers
        cg.comment("Stage {}: Read delay for HE and pointers."
                   .format(seq_cycle + 1), True)

        cg.comment("This HE was updated on the last cycle, so the output is stale")
        cg.start_conditional("if", "he_wren_r && (he_wraddress_r == he_rdaddress_r)")
        cg.emit("he_q_s{} = reg_he_data_s{};".format(seq_cycle + 1, seq_cycle + 2))
        cg.end_conditional("if")
        cg.comment("Fallthrough: default to he_q")
        cg.emit()

        cg.comment("This NP was updated on the last cycle, so the output is stale")
        cg.start_conditional("if", "np_wren_r && (np_wraddress_r == np_rdaddress_r)")
        cg.emit("np_q_s{} = reg_np_data_s{};".format(seq_cycle + 1, seq_cycle + 2))
        cg.end_conditional("if")
        cg.comment("Fallthrough: default to np_q")
        cg.emit()

        cg.comment("This PP was updated in the last 2 cycles")
        cg.start_conditional("if", "reg_pp_data_valid_s{}".format(seq_cycle))
        cg.emit("pp_q_s{} = reg_pp_data_s{};".format(seq_cycle + 1, seq_cycle))
        cg.end_conditional("if")
        cg.comment("Fallthrough: default to pp_q")

        cg.emit()
        seq_cycle -= 1

        # Read data and pointers
        cg.comment([
            "Stage {}: Read the heap entry and prev/next pointer".format(seq_cycle + 1),
            "corresponding to the priority bucket to deque.",
        ], True)
        cg.comment("The PB is being updated on this cycle")
        cg.start_conditional("if", "reg_pb_addr_conflict_s{}_s{}"
                             .format(seq_cycle + 2, seq_cycle))

        cg.emit("int_pb_q = int_pb_data;")
        cg.end_conditional("if")

        cg.comment("The PB was updated last cycle, so output is stale")
        cg.start_conditional("else if", "reg_pb_update_s{}".format(seq_cycle))
        cg.emit("int_pb_q = reg_pb_data_s{};".format(seq_cycle + 3))
        cg.end_conditional("else if")

        cg.comment("The PB was updated 2 cycles ago (and thus never read)")
        cg.start_conditional("else if", "reg_pb_rdwr_conflict_r2")
        cg.emit("int_pb_q = reg_pb_data_s{};".format(seq_cycle + 4))
        cg.end_conditional("else if")

        cg.comment("Fallthrough: default to pb_q_r")
        cg.emit()

        cg.comment("Read next and prev pointers")
        cg.emit([
            "np_rdaddress = int_pb_q.head;",
            "pp_rdaddress = int_pb_q.tail;",
        ])
        cg.emit()

        cg.comment("Compute tail PP updates")
        cg.align_assignment(
            "pp_changes_s{}_s{}".format(seq_cycle + 2, seq_cycle + 1),
            ["(reg_pb_tail_pp_changes_s{} &&".format(seq_cycle + 1),
             "reg_pb_addr_conflict_s{}_s{});".format(seq_cycle + 1, seq_cycle)
            ],
        "=")
        cg.emit()
        cg.align_assignment(
            "pp_changes_s{}_s{}".format(seq_cycle + 3, seq_cycle + 1),
            ["(reg_pb_tail_pp_changes_s{} &&".format(seq_cycle + 2),
             "reg_pb_addr_conflict_s{}_s{});".format(seq_cycle + 2, seq_cycle)
            ],
        "=")
        cg.emit()

        cg.comment("Read HE data")
        cg.align_assignment("he_rdaddress", [
            "(",
            "(reg_op_color_s[{}] == OP_COLOR_BLUE) ?".format(seq_cycle),
            "int_pb_q.head : int_pb_q.tail);",
        ], "=", True)
        cg.emit()

        cg.start_conditional("if", "reg_valid_s[{}]".format(seq_cycle))
        cg.start_conditional("if", "!reg_is_enque_s[{}]".format(seq_cycle))
        cg.emit("he_rden = 1; // Dequeing, read HE and PP/NP")
        cg.start_conditional("if", ("reg_op_color_s[{}] == OP_COLOR_BLUE"
                                    .format(seq_cycle)))
        cg.emit([
            "np_rden = 1; // BLUE-colored dequeue (from HEAD)",
        ])
        cg.end_conditional("if")
        cg.start_conditional("else", None)
        cg.emit([
            "pp_rden = 1; // RED-colored dequeue (from TAIL)",
        ])
        cg.end_conditional("else")
        cg.end_conditional("if")
        cg.end_conditional("if")
        seq_cycle -= 1

        # Read delay for PB
        cg.comment("Stage {}: Compute op color, read delay for PB."
                   .format(seq_cycle + 1), True)

        cg.start_conditional("if", "!reg_is_enque_s[{0}]".format(seq_cycle))
        cg.comment("Dequeing, recolor this op if required")
        cg.start_conditional("if", "reg_pb_addr_conflict_s{}_s{}"
                             .format(seq_cycle + 1, seq_cycle))

        cg.align_assignment("op_color_s{}".format(seq_cycle + 1), [
            "(",
            "(reg_op_color_s[{}] == OP_COLOR_BLUE)".format(seq_cycle + 1),
            "{}? OP_COLOR_RED : OP_COLOR_BLUE);".format(cg.tab())
        ], "=", True)
        cg.end_conditional("if")
        cg.end_conditional("if")
        seq_cycle -= 1


    def emit_sequential_pipeline_logic(self, cg: CodeGen) -> None:
        """Emit sequential logic for this level."""

        # Spillover stage
        cycle = self.end_cycle + 1
        cg.comment("Stage {}: Spillover stage.".format(cycle), True)
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format("reg_valid_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_he_data_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_op_type_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_enque_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_priority_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_max_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_min_s", cycle, cycle - 1),
        ])
        cg.emit()
        cg.emit([
            "{0}{1} <= {0}{2};".format("reg_pb_data_s", cycle, cycle - 1),
        ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_addr_s[{1}] <= reg_l{0}_addr_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format(
                "reg_op_color_s", cycle, cycle - 1),
        ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_bitmap_s[{1}] <= reg_l{0}_bitmap_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit()
        cycle -= 1

        # Commit writes
        cg.comment([
            "Stage {}: Perform writes: update the priority bucket,".format(cycle),
            "the free list, heap entries, next and prev pointers."
        ], True)
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format("reg_valid_s", cycle, cycle - 1),
            "{0}[{1}] <= he_data_s{1};".format("reg_he_data_s", cycle),
            "{0}[{1}] <= {0}[{2}];".format("reg_op_type_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_enque_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_priority_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_max_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_min_s", cycle, cycle - 1),
        ])
        cg.emit()
        cg.emit([
            "reg_he_data_s{} <= he_data;".format(cycle),
            "reg_np_data_s{} <= np_data;".format(cycle),
            "reg_pp_data_s{} <= pp_data;".format(cycle),
            "reg_pb_data_s{} <= int_pb_data;".format(cycle),
        ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_addr_s[{1}] <= reg_l{0}_addr_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format(
                "reg_op_color_s", cycle, cycle - 1),
        ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_bitmap_s[{1}] <= reg_l{0}_bitmap_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])

        cg.emit()
        cg.comment("Update the heap size")
        cg.emit(["size <= int_size;"])
        cg.emit()

        cg.start_ifdef("DEBUG")
        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.start_conditional("if", "!reg_pb_state_changes_s{}".format(cycle - 1))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (op: %s, color: %s) updating priority = %0d,\",".format(cycle),
            "reg_op_type_s[{0}].name, reg_op_color_s[{0}].name,".format(cycle - 1),
            "reg_priority_s[{}], \" pb (head, tail) changes from \",".format(cycle - 1),
            "\"(%b, %b) to (%b, %b)\", reg_pb_q_s{}.head,".format(cycle - 1),
            "reg_pb_q_s{0}.tail, int_pb_data.head, int_pb_data.tail);".format(cycle - 1),
        ], True, 4)
        cg.end_conditional("if")

        cg.start_conditional("else if", "reg_is_enque_s[{}]".format(cycle - 1))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (op: %s, color: %s) updating priority = %0d,\",".format(cycle),
            "reg_op_type_s[{0}].name, reg_op_color_s[{0}].name,".format(cycle - 1),
            "reg_priority_s[{}], \" pb (head, tail) changes from \",".format(cycle - 1),
            "\"(INVALID_PTR, INVALID_PTR) to (%b, %b)\",",
            "int_pb_data.head, int_pb_data.tail);",
        ], True, 4)
        cg.end_conditional("else if")

        cg.start_conditional("else", None)
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (op: %s, color: %s) updating priority = %0d,\",".format(cycle),
            "reg_op_type_s[{0}].name, reg_op_color_s[{0}].name,".format(cycle - 1),
            "reg_priority_s[{}], \" pb (head, tail) changes from \",".format(cycle - 1),
            "\"(%b, %b) to (INVALID_PTR, INVALID_PTR)\",",
            "reg_pb_q_s{0}.head, reg_pb_q_s{0}.tail);".format(cycle - 1),
        ], True, 4)
        cg.end_conditional("else")
        cg.end_conditional("if")
        cg.end_ifdef()
        cg.emit()
        cycle -= 1

        # Read delay for data, pointers
        cg.comment("Stage {}: Read delay for HE and pointers.".format(cycle), True)
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format("reg_valid_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_he_data_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_op_type_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_enque_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_priority_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_max_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_min_s", cycle, cycle - 1),
        ])
        cg.emit()
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_addr_s[{1}] <= reg_l{0}_addr_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format(
                "reg_op_color_s", cycle, cycle - 1),
        ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_bitmap_s[{1}] <= reg_l{0}_bitmap_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit([
            "{0}{1} <= {0}{2};".format("reg_pb_data_conflict_s", cycle, cycle - 1),
            "{0}{1} <= {0}{2};".format("reg_pb_state_changes_s", cycle, cycle - 1),
            "{0}{1} <= {0}{2};".format("reg_pb_tail_pp_changes_s", cycle, cycle - 1),
            "",
            "reg_he_q_s{0} <= he_q_s{0};".format(cycle),
            "reg_np_q_s{0} <= np_q_s{0};".format(cycle),
            "reg_pp_q_s{0} <= pp_q_s{0};".format(cycle),
        ])
        cg.emit()
        cg.align_assignment("reg_pb_q_s{}".format(cycle), [
            "(",
            "reg_pb_addr_conflict_s{}_s{} ?".format(cycle, cycle - 1),
            "   int_pb_data : reg_pb_q_s{});".format(cycle - 1)
        ],
        "<=", True)
        cg.emit()

        cg.align_assignment("reg_pb_new_s{}".format(cycle), [
            "(",
            "reg_pb_addr_conflict_s{}_s{} ?".format(cycle, cycle - 1),
            "   int_pb_data : reg_pb_q_s{});".format(cycle - 1)
        ],
        "<=", True)
        cg.emit()

        cg.start_conditional("if", "reg_is_enque_s[{}]".format(cycle - 1))
        cg.comment("PB becomes non-empty, update tail")
        cg.start_conditional("if", "reg_pb_state_changes_s{}".format(cycle - 1))
        cg.emit("reg_pb_new_s{}.tail <= fl_q_r[{}];"
                .format(cycle, self.fl_rd_delay - 2))

        cg.end_conditional("if")
        cg.emit("reg_pb_new_s{}.head <= fl_q_r[{}];"
                .format(cycle, self.fl_rd_delay - 2))

        cg.end_conditional("if")
        cg.emit()

        cg.start_ifdef("SIM")
        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.start_conditional("if", [
            "(he_wren && he_rden_r && (he_wraddress == he_rdaddress_r)) ||",
            "(np_wren && np_rden_r && (np_wraddress == np_rdaddress_r))"
        ])
        cg.emit([
            "$display(\"[BBQ] Error: Unexpected conflict in R/W access\");",
            "$finish;"
        ])
        cg.end_conditional("if")
        cg.end_conditional("if")
        cg.end_ifdef()

        cg.start_ifdef("DEBUG")
        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (op: %s) for PB (priority = %0d)\",".format(cycle),
            "reg_op_type_s[{0}].name, reg_priority_s[{0}]);".format(cycle - 1),
        ], True, 4)
        cg.end_conditional("if")
        cg.end_ifdef()
        cg.emit()
        cycle -= 1

        # Read data and pointers
        cg.comment([
            "Stage {}: Read the heap entry and prev/next pointer".format(cycle),
            "corresponding to the priority bucket to deque."
        ], True)
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format("reg_valid_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_he_data_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_op_type_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_enque_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_priority_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_max_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_min_s", cycle, cycle - 1),
        ])
        cg.emit()
        cg.emit("reg_pb_q_s{} <= int_pb_q;".format(cycle))
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_addr_s[{1}] <= reg_l{0}_addr_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format(
                "reg_op_color_s", cycle, cycle - 1),
        ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_bitmap_s[{1}] <= reg_l{0}_bitmap_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit([
            "{0}{1} <= {0}{2};".format("reg_pb_data_conflict_s", cycle, cycle - 1),
            "{0}{1} <= {0}{2};".format("reg_pb_state_changes_s", cycle, cycle - 1),
            "{0}{1} <= {0}{2};".format("reg_pb_tail_pp_changes_s", cycle, cycle - 1),
        ])
        for offset in range(1, 3):
            cg.emit([
                "{0}_s{1}_s{2} <= {0}_s{3}_s{4};".format(
                    "reg_pb_addr_conflict", cycle + offset,
                    cycle, cycle + offset - 1, cycle - 1)
            ])
        cg.emit()

        cg.emit([
            ("reg_pp_data_s{0} <= pp_changes_s{1}_s{0} ? fl_q_r[{2}] : fl_q_r[{3}];"
             .format(cycle, cycle + 1, self.fl_rd_delay - 3, self.fl_rd_delay - 2)),

            ("reg_pp_data_valid_s{0} <= (pp_changes_s{1}_s{0} || pp_changes_s{2}_s{0});"
             .format(cycle, cycle + 1, cycle + 2)),
        ])
        cg.emit()

        cg.start_ifdef("DEBUG")
        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (op: %s) for PB (priority = %0d)\",".format(cycle),
            "reg_op_type_s[{0}].name, reg_priority_s[{0}]);".format(cycle - 1),
        ], True, 4)
        cg.end_conditional("if")
        cg.end_ifdef()
        cg.emit()
        cycle -= 1

        # Read delay for PB
        cg.comment(("Stage {}: Compute op color, read delay for PB."
                    .format(cycle)), True)
        cg.emit([
            "{0}[{1}] <= {0}[{2}];".format("reg_valid_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_he_data_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_op_type_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_enque_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_priority_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_max_s", cycle, cycle - 1),
            "{0}[{1}] <= {0}[{2}];".format("reg_is_deque_min_s", cycle, cycle - 1),
        ])
        cg.emit()
        cg.emit("reg_{0}[{1}] <= {0}{1};".format("op_color_s", cycle))
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_addr_s[{1}] <= reg_l{0}_addr_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        for i in range(1, self.num_bitmap_levels):
            cg.emit([
                ("reg_l{0}_bitmap_s[{1}] <= reg_l{0}_bitmap_s[{2}];"
                 .format(i + 1, cycle, cycle - 1))
            ])
        cg.emit("reg_pb_update_s{} <= reg_pb_addr_conflict_s{}_s{};"
                .format(cycle, cycle + 2, cycle - 1))

        for offset in range(1, 3):
            cg.emit([
                "{0}_s{1}_s{2} <= {0}_s{3}_s{4};".format(
                    "reg_pb_addr_conflict", cycle + offset,
                    cycle, cycle + offset - 1, cycle - 1)
            ])
        cg.emit()
        cg.comment([
            "Determine if this op is going to result in PB data",
            "conflict (dequeing a PB immediately after an enque",
            "operation that causes it to become non-empty).",
        ])
        cg.align_assignment("reg_pb_data_conflict_s{}".format(cycle), [
            "(reg_is_enque_s[{}] &&".format(cycle),
            ("!reg_l{0}_counter_non_zero_s{1} && reg_pb_addr_conflict_s{2}_s{1});"
             .format(self.prev_level.level_id, cycle - 1, cycle))
        ],
        "<=", True)
        cg.emit()

        cg.comment([
            "Determine if this op causes the PB state to change.",
            "Change of state is defined differently based on op:",
            "for enques, corresponds to a PB becoming non-empty,",
            "and for deques, corresponds to a PB becoming empty.",
        ])
        cg.align_assignment("reg_pb_state_changes_s{}".format(cycle), [
            "(",
            "reg_is_enque_s[{}] ?".format(cycle - 1),
            ("(!reg_l{0}_counter_s{1}[WATERLEVEL_IDX] && reg_l{0}_counter_s{1}[0]) :"
             .format(self.prev_level.level_id, cycle - 1)),

            ("(!reg_l{0}_counter_s{1}[WATERLEVEL_IDX] && !reg_l{0}_counter_s{1}[0]));"
             .format(self.prev_level.level_id, cycle - 1)),
        ],
        "<=", True)
        cg.emit()

        cg.comment([
            "Determine if this op causes the previous pointer",
            "corresponding to the PB tail to change. High iff",
            "enqueing into a PB containing a single element.",
        ])
        cg.align_assignment("reg_pb_tail_pp_changes_s{}".format(cycle), [
            "(reg_is_enque_s[{}] &&".format(cycle - 1),
            ("!reg_old_l{0}_counter_s{1}[WATERLEVEL_IDX] && reg_old_l{0}_counter_s{1}[0]);"
             .format(self.prev_level.level_id, cycle - 1)),
        ],
        "<=", True)
        cg.emit()

        cg.start_ifdef("DEBUG")
        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (op: %s) for PB (priority = %0d)\",".format(cycle),
            "reg_op_type_s[{0}].name, reg_priority_s[{0}],".format(cycle - 1),
            "\" assigned color %s\", op_color_s{}.name);".format(cycle)
        ], True, 4)
        cg.end_conditional("if")
        cg.end_ifdef()
        cg.emit()
        cycle -= 1
