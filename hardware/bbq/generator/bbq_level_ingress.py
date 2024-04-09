#!/usr/bin/python3
from __future__ import annotations

import typing

from bbq_level import BBQLevel
from codegen import CodeGen

# Hack for type hinting with circular imports
if typing.TYPE_CHECKING: from bbq import BBQ


class BBQLevelIngress(BBQLevel):
    """Represents the ingress level in BBQ."""
    def __init__(self, bbq: BBQ, start_cycle: int) -> None:
        super().__init__(bbq, start_cycle)


    def name(self) -> str:
        """Canonical level name."""
        return "ingress"


    def latency(self) -> int:
        """Latency in cycles."""
        return 0


    def emit_stage_defs(self, cg: CodeGen) -> None:
        """Emit per-stage definitions."""
        cycle = self.start_cycle

        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("logic", "valid_s{};".format(cycle)),
            ("counter_t", "old_occupancy_s{};".format(cycle)),
            ("counter_t", "new_occupancy_s{};".format(cycle)),
            ("counter_t", "reg_old_occupancy_s{};".format(cycle)),
            ("counter_t", "reg_new_occupancy_s{};".format(cycle)),
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

        if self.bbq.is_logically_partitioned:
            cg.emit("old_occupancy_s{} = occupancy[reg_bbq_id_s[{}]];"
                    .format(cycle, cycle - 1))
        else:
            cg.emit("old_occupancy_s{} = occupancy;".format(cycle))

        cycle += 1


    def emit_state_agnostic_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-agnostic combinational logic."""
        seq_cycle = self.start_cycle - 1

        old_occupancy = "old_occupancy_s{}".format(seq_cycle + 1)
        cg.comment([
            "Stage {}: Determine operation validity. Disables the pipeline".format(seq_cycle + 1),
            "stage if the BBQ is empty (deques), or FL is empty (enques).",
        ], True)
        cg.start_conditional("if", "reg_valid_s[{}]".format(seq_cycle))
        cg.align_assignment("valid_s{}".format(seq_cycle + 1), [
            "(",
            "(reg_is_enque_s[{}] && !fl_empty) ||".format(seq_cycle),
            ("(!reg_is_enque_s[{}] && ({}[0] |"
             .format(seq_cycle, old_occupancy)),

            ("                        {}[WATERLEVEL_IDX])));"
             .format(old_occupancy))
        ], "=", True)
        cg.end_conditional("if")

        cg.comment("Update the occupancy counter")
        cg.align_ternary(
            "new_occupancy_s{}[WATERLEVEL_IDX-1:0]".format(seq_cycle + 1),
            ["reg_is_enque_s[{}]".format(seq_cycle)],
            ["({}[WATERLEVEL_IDX-1:0] + 1)".format(old_occupancy),
             "({}[WATERLEVEL_IDX-1:0] - 1)".format(old_occupancy)],
            "=", True, False)

        cg.emit()
        cg.align_assignment(
            "new_occupancy_s{}[WATERLEVEL_IDX]".format(seq_cycle + 1),
            ["(reg_is_enque_s[{}] ?".format(seq_cycle),
             "({0}[WATERLEVEL_IDX] | {0}[0]) :".format(old_occupancy),
             "((|{0}[WATERLEVEL_IDX-1:2]) | (&{0}[1:0])));".format(old_occupancy),
            ],
            "=", True)

        cg.emit()
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

        value_override = {"reg_valid_s": "valid_s{}".format(cycle)}
        self.bbq.emit_sequential_primary_signals(cycle, value_override)

        cg.emit([
            "reg_old_occupancy_s{0} <= old_occupancy_s{0};".format(cycle),
            "reg_new_occupancy_s{0} <= new_occupancy_s{0};".format(cycle),
        ])
        cg.emit()

        cg.start_conditional("if", "valid_s{}".format(cycle))
        cg.emit("occupancy{} <= new_occupancy_s{};"
                .format("[reg_bbq_id_s[{}]]".format(cycle - 1) if
                        self.bbq.is_logically_partitioned else "", cycle))

        cg.end_conditional("if")
        cg.emit()

        cg.start_ifdef("DEBUG")
        id_str_prefix = ("logical ID: %0d, "
                         if self.bbq.is_logically_partitioned else "")

        id_val_prefix = ("reg_bbq_id_s[{}], ".format(cycle - 1)
                         if self.bbq.is_logically_partitioned else "")

        cg.start_conditional("if", ("reg_valid_s[{}] && !valid_s{}"
                                    .format(cycle - 1, cycle)))
        cg.emit("$display(")
        cg.emit([
            ("\"[BBQ] At S{0} ({1}op: %s), rejected at Stage {2}->{0}\","
             .format(cycle, id_str_prefix, cycle - 1)),

            "{}reg_op_type_s[{}].name);".format(id_val_prefix, cycle - 1),
        ], True, 4)
        cg.end_conditional("if")

        cg.start_conditional("if", "valid_s{}".format(cycle))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} ({}op: %s), updating occupancy\",".format(cycle, id_str_prefix),
            "{}reg_op_type_s[{}].name, \" from %0d to %0d\",".format(id_val_prefix, cycle - 1),
            "old_occupancy_s{}[WATERLEVEL_IDX-1:0],".format(cycle),
            "new_occupancy_s{}[WATERLEVEL_IDX-1:0]);".format(cycle),
        ], True, 4)
        cg.end_conditional("if")
        cg.end_ifdef()
        cg.emit()
