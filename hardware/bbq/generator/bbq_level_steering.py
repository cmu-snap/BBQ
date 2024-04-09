#!/usr/bin/python3
from __future__ import annotations

import typing

from bbq_level import BBQLevel
from bbq_level_pb import BBQLevelPB
from codegen import CodeGen

# Hack for type hinting with circular imports
if typing.TYPE_CHECKING: from bbq import BBQ


class BBQLevelSteering(BBQLevel):
    """Represents the steering level in BBQ."""
    def __init__(self, bbq: BBQ, start_cycle: int,
                 num_lps: int, level_id: int) -> None:

        super().__init__(bbq, start_cycle)

        self.num_lps = num_lps      # Number of logical partitions
        self.level_id = level_id    # ID of the maximum level replaced


    @property
    def is_leaf(self) -> bool:
        """Returns whether this is a leaf level."""
        return isinstance(self.next_level, BBQLevelPB)


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
        if self.is_leaf:
            cg.align_defs([
                ("heap_priority_t", "priority_s{};".format(cycle)),
            ])
        for offset in range(1, 5):
            cg.align_defs([
                ("logic", "{}_addr_conflict_s{}_s{};".format(
                    self.next_level.name(), (cycle + offset), cycle))
            ])
        if self.is_leaf:
            cg.align_defs([
                ("counter_t", "reg_{}_counter_s{};".format(self.name(), cycle)),
            ])
        for offset in range(1, 5):
            cg.align_defs([
                ("logic", "reg_{}_addr_conflict_s{}_s{};".format(
                    self.next_level.name(), (cycle + offset), cycle))
            ])
        if self.is_leaf:
            cg.align_defs([
                ("counter_t", "reg_old_{}_counter_s{};".format(self.name(), cycle)),
                ("logic", "reg_{}_counter_non_zero_s{};".format(self.name(), cycle)),
            ])
        cg.emit()
        cycle += 1


    def emit_state_dependent_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-dependent combinational logic."""
        pass


    def emit_combinational_default_assigns(self, cg: CodeGen) -> None:
        """Emit state-agnostic default assigns."""
        cycle = self.start_cycle

        # If this (steering) level is also the leaf level, then
        # the priority simply corresponds to the logical BBQ ID.
        if self.is_leaf:
            cg.emit("priority_s{} = reg_priority_s[{}];"
                    .format(cycle, cycle - 1))

        cycle += 1


    def emit_state_agnostic_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-agnostic combinational logic."""
        seq_cycle = self.end_cycle - 1

        cg.comment([
            ("Stage {}: Steer op to the appropriate logical BBQ."
             .format(seq_cycle + 1))
        ], True)

        if self.is_leaf:
            cg.comment("Read PB contents")
            cg.emit("pb_rden = reg_valid_s[{}];".format(seq_cycle))
            cg.emit()

        elif self.next_level.sram_bitmap:
            cg.comment("Read L{} bitmap".format(self.level_id + 1))
            cg.emit("bm_{}_rden = reg_valid_s[{}];".format(
                self.next_level.name(), seq_cycle))

            cg.emit("bm_{}_rdaddress = reg_bbq_id_s[{}];".format(
                self.next_level.name(), seq_cycle))

            cg.emit()

        cg.comment("Compute conflicts")
        for offset in range(1, 5):
            cg.align_assignment(
                ("{}_addr_conflict_s{}_s{}"
                    .format(self.next_level.name(),
                            seq_cycle + 1 + offset,
                            seq_cycle + 1)),
                ["(",
                ("reg_valid_s[{}] && reg_valid_s[{}] &&"
                .format(seq_cycle, seq_cycle + offset)),

                ("(reg_bbq_id_s[{}] == reg_bbq_id_s[{}]));"
                .format(seq_cycle, seq_cycle + offset))
                ],
            "=", True)
            cg.emit()

        if self.is_leaf:
            cg.comment("Disable conflicting reads during writes")
            cg.start_conditional("if",
                ("pb_addr_conflict_s{}_s{}".format(
                    self.next_level.end_cycle, seq_cycle + 1))
            )
            cg.emit([
                "pb_rdwr_conflict = 1;",
                "pb_rden = 0;",
            ])
            cg.end_conditional("if")

        seq_cycle += 1


    def emit_sequential_pipeline_logic(self, cg: CodeGen) -> None:
        """Emit sequential logic for this level."""
        cycle = self.start_cycle

        cg.comment([
            "Stage {}: Steer op to the appropriate logical BBQ.".format(cycle)
        ], True)

        self.bbq.emit_sequential_primary_signals(cycle)
        if not self.is_leaf:
            cg.emit("reg_{}_addr_s[{}] <= reg_bbq_id_s[{}];"
                    .format(self.next_level.name(), cycle, cycle - 1))

            cg.emit()

        for offset in range(1, 5):
            cg.emit(
                "reg_{0}_addr_conflict_s{1}_s{2} <= "
                "{0}_addr_conflict_s{1}_s{2};".format(
                self.next_level.name(), cycle + offset, cycle)
            )
        cg.emit()

        if self.is_leaf:
            cg.comment([
                "With a steering level that replaces the leaf-level",
                "bitmaps, we can effectively substitute StOC values",
                "(used in Stage {}) with logical occupancy counters.".format(cycle + 1)
            ])
            cg.emit([
                ("reg_{}_counter_s{} <= reg_new_occupancy_s{};"
                 .format(self.name(), cycle, cycle - 1)),

                ("reg_old_{}_counter_s{} <= reg_old_occupancy_s{};"
                 .format(self.name(), cycle, cycle - 1)),
            ])
            cg.align_assignment(
                "reg_{}_counter_non_zero_s{}".format(self.name(), cycle),
                ["(reg_is_enque_s[{}] |".format(cycle - 1),
                 "reg_new_occupancy_s{}[WATERLEVEL_IDX]);".format(cycle - 1)],
            "<=", False)
            cg.emit()

        elif (not self.is_leaf) and (not self.next_level.sram_bitmap):
            cg.comment("Forward L{} bitmap updates".format(self.level_id + 1))
            cg.align_ternary(
                "reg_{}_bitmap_s[{}]".format(
                    self.next_level.name(), cycle),

                ["{}_addr_conflict_s{}_s{}"
                 .format(self.next_level.name(),
                         self.next_level.end_cycle, cycle)],

                ["{}_bitmap_s{}".format(self.next_level.name(),
                                        self.next_level.end_cycle),

                 "{}_bitmaps[reg_bbq_id_s[{}]]".format(
                     self.next_level.name(), cycle - 1)],
                "<=", True, True)
            cg.emit()

        cg.start_ifdef("DEBUG")
        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.emit("$display(")
        cg.emit([
            "\"[BBQ] At S{} (logical ID: %0d, op: %s),\",".format(cycle),
            "reg_bbq_id_s[{0}], reg_op_type_s[{0}].name,".format(cycle - 1),

            ("\" steering op to the corresponding {}\");"
             .format("PB" if self.is_leaf else
                     "L{} bitmap".format(self.level_id + 1))),
        ], True, 4)
        cg.end_conditional("if")
        cg.end_ifdef()

        cycle += 1
