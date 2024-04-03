#!/usr/bin/python3
from bbq_level import BBQLevel
from codegen import CodeGen


class BBQLevelSteering(BBQLevel):
    """Represents a steering level in BBQ."""
    def __init__(self, start_cycle: int, num_bitmap_levels: int) -> None:
        super().__init__(start_cycle, num_bitmap_levels)


    def name(self) -> str:
        """Canonical level name."""
        return "steering"


    def latency(self) -> int:
        """Latency in cycles."""
        return 0


    def emit_stage_defs(self, cg: CodeGen) -> None:
        """Emit per-stage definitions."""
        cycle = self.start_cycle

        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("logic", "valid_s{};".format(cycle)),
        ])
        cg.emit()
        cycle += 1


    def emit_state_dependent_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-dependent combinational logic."""
        pass


    def emit_combinational_default_assigns(self, cg: CodeGen) -> None:
        """Emit default assignments."""
        cycle = self.start_cycle
        cg.emit("valid_s{} = 0;".format(cycle))
        cycle += 1


    def emit_state_agnostic_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-agnostic combinational logic."""
        seq_cycle = self.start_cycle - 1

        cg.comment([
            "Stage {}: Determine operation validity. Disables the pipeline".format(seq_cycle + 1),
            "stage if the BBQ is empty (deques) or FL is empty (enqueues).",
        ], True)
        cg.start_conditional("if", "reg_valid_s[{}]".format(seq_cycle))
        cg.align_assignment("valid_s{}".format(seq_cycle + 1), [
            "(",
            "(reg_is_enque_s[{}] && !fl_empty) ||".format(seq_cycle),
            ("(!reg_is_enque_s[{0}] && (bbq_occupancy[0] |".format(seq_cycle)),
            ("                        bbq_occupancy[WATERLEVEL_IDX])));")
        ], "=", True)
        cg.end_conditional("if")

        cg.comment("Update the occupancy counter")
        cg.start_conditional("if", "valid_s{}".format(seq_cycle + 1))
        cg.align_ternary(
            "int_bbq_occupancy[WATERLEVEL_IDX-1:0]",
            ["reg_is_enque_s[{}]".format(seq_cycle)],
            ["(bbq_occupancy[WATERLEVEL_IDX-1:0] + 1)",
             "(bbq_occupancy[WATERLEVEL_IDX-1:0] - 1)"],
            "=", True, False)

        cg.emit()
        cg.align_assignment(
            "int_bbq_occupancy[WATERLEVEL_IDX]",
            ["(reg_is_enque_s[{}] ?".format(seq_cycle),
             "({0}[WATERLEVEL_IDX] | {0}[0]) :".format("bbq_occupancy"),
             "((|{0}[WATERLEVEL_IDX-1:2]) | (&{0}[1:0])));".format("bbq_occupancy"),
            ],
            "=", True)

        cg.end_conditional("if")

        cg.comment("If enqueing, also deque the free list")
        cg.start_conditional("if", ("valid_s{} && reg_is_enque_s[{}]"
                                    .format(seq_cycle + 1, seq_cycle)))

        cg.emit("fl_rdreq = 1;")
        cg.end_conditional("if")
        cg.emit()


    def emit_sequential_pipeline_logic(self, cg: CodeGen) -> None:
        """Emit sequential logic for this level."""
        cycle = self.end_cycle
        cg.comment([
            "Stage {}: Determine operation validity. Disables the pipeline".format(cycle),
            "stage if the BBQ is empty (deques) or FL is empty (enqueues).",
        ], True)

        signals = ["reg_valid_s",
                   "reg_he_data_s",
                   "reg_op_type_s",
                   "reg_is_enque_s",
                   "reg_priority_s",
                   "reg_is_deque_max_s",
                   "reg_is_deque_min_s"]

        value_override = {"reg_valid_s": "valid_s{}".format(cycle)}
        for signal in signals:
            v = value_override.get(signal)
            if not v: v = "{}[{}]".format(signal, cycle - 1)
            cg.emit("{}[{}] <= {};".format(signal, cycle, v))

        cg.emit()

        cg.emit("bbq_occupancy <= int_bbq_occupancy;")
        cg.emit()

        cg.start_ifdef("DEBUG")
        cg.start_conditional("if", ("reg_valid_s[{}] && !valid_s{}"
                                    .format(cycle - 1, cycle)))
        cg.emit("$display(")
        cg.emit([
            ("\"[BBQ] At S{0}, %s rejected at Stage {1}->{0}\","
             .format(cycle, cycle - 1)),

            "reg_op_type_s[{0}].name);".format(cycle - 1),
        ], True, 4)
        cg.end_conditional("if")

        cg.start_conditional("if", "valid_s{}".format(cycle))
        cg.emit("$display(")
        cg.emit([
            ("\"[BBQ] At S{} (op: %s), updating occupancy\", reg_op_type_s[{}].name,"
                .format(cycle, cycle - 1)),

            "\" from %0d to %0d\", bbq_occupancy[WATERLEVEL_IDX-1:0],",
            "int_bbq_occupancy[WATERLEVEL_IDX-1:0]);",
        ], True, 4)
        cg.end_conditional("if")
        cg.end_ifdef()
        cg.emit()
