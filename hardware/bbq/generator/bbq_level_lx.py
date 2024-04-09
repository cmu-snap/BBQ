#!/usr/bin/python3
from __future__ import annotations

import typing

from bbq_level import BBQLevel
from bbq_level_pb import BBQLevelPB
from codegen import CodeGen

# Hack for type hinting with circular imports
if typing.TYPE_CHECKING: from bbq import BBQ


class BBQLevelLX(BBQLevel):
    """Represents an LX BBQ level."""
    def __init__(self, bbq: BBQ, start_cycle: int, level_id: int,
                 sram_bitmap: bool, sram_counters: bool) -> None:

        super().__init__(bbq, start_cycle)

        self.level_id = level_id            # BBQ Level (>= 1)
        self.sram_bitmap = sram_bitmap      # Store bitmap in SRAM?
        self.sram_counters = sram_counters  # Store counters in SRAM?


    @property
    def is_leaf(self) -> bool:
        """Returns whether this is a leaf bitmap."""
        return isinstance(self.next_level, BBQLevelPB)


    @property
    def id(self) -> int:
        """Alias for the level ID."""
        return self.level_id


    def name(self) -> str:
        """Canonical level name."""
        return "l{}".format(self.level_id)


    def latency(self) -> int:
        """Latency in cycles."""
        return 1 + int(self.sram_bitmap) + int(self.sram_counters)


    def emit_stage_defs(self, cg: CodeGen) -> None:
        """Emit per-stage definitions."""
        cycle = self.start_cycle

        # Read delay for SRAM-based bitmaps
        if self.sram_bitmap:
            cg.comment("Stage {} metadata".format(cycle))
            cg.align_defs([
                ("bitmap_t", "{}_bitmap_s{};".format(self.name(), cycle))
            ])
            for offset in range(1, 5):
                cg.align_defs([
                    ("logic", "reg_{}_addr_conflict_s{}_s{};"
                     .format(self.name(), (cycle + offset), cycle))
                ])
            cg.emit()
            cycle += 1

        # Bitmap index computation
        cg.comment("Stage {} metadata".format(cycle))
        cg.align_defs([
            ("read_carry_direction_t", "rcd_s{};".format(cycle)),

            ("logic [HEAP_LOG_BITMAP_WIDTH-1:0]",
             "{}_bitmap_idx_s{};".format(self.name(), cycle)),

            ("logic", "{}_bitmap_empty_s{};".format(self.name(), cycle)),
            ("bitmap_t", "{}_bitmap_postop_s{};".format(self.name(), cycle)),
            ("bitmap_t", "{}_bitmap_idx_onehot_s{};".format(self.name(), cycle)),
        ])
        cg.align_defs([
            ("logic", "{}_bitmap_changes_s{}_s{};".format(
                self.name(), cycle + 1 + int(self.sram_counters), cycle))
        ])
        if not self.sram_counters:
            cg.align_defs([
                ("counter_t", "reg_{}_counter_s{};".format(self.name(), cycle))
            ])
        cg.align_defs([
            ("logic [HEAP_LOG_BITMAP_WIDTH-1:0]",
             "reg_{}_bitmap_idx_s{};".format(self.name(), cycle)),

            ("logic", "reg_{}_bitmap_empty_s{};".format(self.name(), cycle)),
            ("bitmap_t", "reg_{}_bitmap_postop_s{};".format(self.name(), cycle)),
            ("bitmap_t", "reg_{}_bitmap_idx_onehot_s{};".format(self.name(), cycle)),
        ])
        if self.sram_counters:
            cg.align_defs([
                ("logic", "reg_{}_counter_rdvalid_r1_s{};".format(self.name(), cycle))
            ])
        if self.level_id > 1:
            for offset in range(1, 5):
                cg.align_defs([
                    ("logic", "reg_{}_addr_conflict_s{}_s{};"
                     .format(self.name(), (cycle + offset), cycle))
                ])
        cg.emit()
        cycle += 1

        # Read delay for SRAM-based counters
        if self.sram_counters:
            cg.comment("Stage {} metadata".format(cycle))
            cg.align_defs([
                ("read_carry_direction_t", "rcd_s{};".format(cycle)),
                ("counter_t", "{}_counter_s{};".format(self.name(), cycle)),
                ("counter_t", "{}_counter_q_s{};".format(self.name(), cycle)),
                ("counter_t", "reg_{}_counter_s{};".format(self.name(), cycle)),
                ("counter_t", "reg_{}_counter_rc_s{};".format(self.name(), cycle)),

                ("logic [HEAP_LOG_BITMAP_WIDTH-1:0]",
                 "reg_{}_bitmap_idx_s{};".format(self.name(), cycle)),

                ("bitmap_t", "reg_{}_bitmap_postop_s{};".format(self.name(), cycle)),
                ("bitmap_t", "reg_{}_bitmap_idx_onehot_s{};".format(self.name(), cycle)),
            ])
            for offset in range(1, 5):
                cg.align_defs([
                    ("logic", "reg_{}_addr_conflict_s{}_s{};"
                     .format(self.name(), (cycle + offset), cycle))
                ])
            cg.emit()
            cycle += 1

        # Write-back counter, bitmap
        cg.comment("Stage {} metadata".format(cycle))
        if self.is_leaf:
            cg.align_defs([
                ("heap_priority_t", "priority_s{};".format(cycle)),
            ])
        if not self.sram_bitmap:
            cg.align_defs([
                ("bitmap_t", "{}_bitmap_s{};".format(self.name(), cycle))
            ])
        cg.align_defs([
            ("counter_t", "{}_counter_s{};".format(self.name(), cycle)),
            ("logic", "{}_counter_non_zero_s{};".format(self.name(), cycle)),
        ])
        for offset in range(1, 5):
            cg.align_defs([
                ("logic", "{}_addr_conflict_s{}_s{};".format(
                    self.next_level.name(), (cycle + offset), cycle))
            ])
        cg.align_defs([
            ("counter_t", "reg_{}_counter_s{};".format(self.name(), cycle))
        ])
        if self.sram_counters:
            cg.align_defs([
                ("logic [HEAP_LOG_BITMAP_WIDTH-1:0]",
                 "reg_{}_bitmap_idx_s{};".format(self.name(), cycle))
            ])
        if self.is_leaf:
            cg.align_defs([
                ("counter_t", "reg_old_{}_counter_s{};".format(self.name(), cycle)),
                ("logic", "reg_{}_counter_non_zero_s{};".format(self.name(), cycle)),
            ])
        for offset in range(1, 5):
            cg.align_defs([
                ("logic", "reg_{}_addr_conflict_s{}_s{};".format(
                    self.next_level.name(), (cycle + offset), cycle))
            ])
        cg.emit()
        cycle += 1


    def emit_state_dependent_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-dependent combinational logic."""
        # Write-back counter, bitmap
        seq_cycle = self.end_cycle - 1
        if self.sram_counters or self.sram_bitmap:
            cg.comment([
                ("Stage {}: Write-back the L{} counter and bitmap,"
                .format(seq_cycle + 1, self.level_id)),
                ("and read the corresponding {}.".format(
                    "PB (head and tail)" if self.is_leaf else
                        "L{} bitmap".format(self.level_id + 1))),
            ], True)

        if self.sram_counters:
            cg.comment("Write L{} counter".format(self.level_id))
            cg.emit([
                ("counter_{}_wren = reg_valid_s[{}];"
                 .format(self.name(), seq_cycle)),

                ("counter_{0}_data = {0}_counter_s{1};"
                 .format(self.name(), seq_cycle + 1)),
            ])
            cg.align_assignment("counter_{}_wraddress".format(self.name()), [
                "{{reg_{}_addr_s[{}],".format(self.name(), seq_cycle),
                "reg_{}_bitmap_idx_s{}}};".format(self.name(), seq_cycle)
            ], "=")

        if self.sram_bitmap:
            cg.comment("Write L{} bitmap".format(self.level_id))
            cg.emit([
                ("bm_{}_wren = reg_valid_s[{}];"
                 .format(self.name(), seq_cycle)),

                ("bm_{0}_wraddress = reg_{0}_addr_s[{1}];"
                 .format(self.name(), seq_cycle)),
            ])
            bm_lhs = "bm_{}_data".format(self.name())
            bm_rhs_term = "reg_{}_bitmap_s[{}]".format(self.name(), seq_cycle)

            cg.start_conditional("if", "reg_is_enque_s[{}]".format(seq_cycle))
            cg.align_assignment(bm_lhs, [
                "({} |".format(bm_rhs_term),
                "reg_{}_bitmap_idx_onehot_s{});".format(self.name(), seq_cycle)
            ], "=")
            cg.end_conditional("if")
            cg.start_conditional("else", None)
            cg.align_assignment(bm_lhs, [
                "(",
                ("{}_counter_non_zero_s{} ? {} :".format(
                 self.name(), (seq_cycle + 1), bm_rhs_term)),

                ("({} & ~reg_{}_bitmap_idx_onehot_s{}));".format(
                            bm_rhs_term, self.name(), seq_cycle)),
            ], "=", True)
            cg.end_conditional("else")


    def emit_combinational_default_assigns(self, cg: CodeGen) -> None:
        """Emit default assignments."""
        cycle = self.start_cycle

        # Read delay for SRAM-based bitmaps
        if self.sram_bitmap:
            cg.emit("{0}_bitmap_s{1} = bm_{0}_q;".format(self.name(), cycle))
            cycle += 1

        # Bitmap index computation
        cg.emit("rcd_s{} = READ_CARRY_DOWN;".format(cycle))
        cycle += 1

        # Read delay for SRAM-based counters
        if self.sram_counters:
            cg.emit([
                "rcd_s{} = READ_CARRY_DOWN;".format(cycle),
                "{0}_counter_s{1} = reg_{0}_counter_s{1};".format(self.name(), cycle),
                "{0}_counter_q_s{1} = counter_{0}_q;".format(self.name(), cycle),
            ])
            cycle += 1

        # Write-back counter, bitmap
        if self.is_leaf:
            if self.level_id == 1:
                cg.emit("priority_s{} = reg_{}_bitmap_idx_s{};"
                        .format(cycle, self.name(), cycle - 1))
            else:
                cg.emit("priority_s{0} = {{reg_{1}_addr_s[{2}], reg_{1}_bitmap_idx_s{2}}};"
                        .format(cycle, self.name(), cycle - 1))
        cycle += 1


    def emit_state_agnostic_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-agnostic combinational logic."""

        # Write-back counter, bitmap
        seq_cycle = self.end_cycle - 1
        cg.comment([
            ("Stage {}: Write-back the L{} counter and bitmap,"
             .format(seq_cycle + 1, self.level_id)),
            ("and read the corresponding {}.".format(
                "PB (head and tail)" if self.is_leaf else
                    "L{} bitmap".format(self.level_id + 1))),
        ], True)

        reg_bitmap = ("reg_{}_counter_rc_s{}".format(self.name(), seq_cycle)
                      if self.sram_counters else
                      "reg_{}_counter_s{}".format(self.name(), seq_cycle))

        cg.align_ternary(
            "{}_counter_s{}[WATERLEVEL_IDX-1:0]".format(self.name(), seq_cycle + 1),
            ["reg_is_enque_s[{}]".format(seq_cycle)],
            ["({}[WATERLEVEL_IDX-1:0] + 1)".format(reg_bitmap),
             "({}[WATERLEVEL_IDX-1:0] - 1)".format(reg_bitmap),],
            "=", True, False)

        cg.emit()
        cg.align_assignment(
            "{}_counter_s{}[WATERLEVEL_IDX]".format(self.name(), seq_cycle + 1),
            ["(reg_is_enque_s[{}] ?".format(seq_cycle),
             "({0}[WATERLEVEL_IDX] | {0}[0]) :".format(reg_bitmap),
             "((|{0}[WATERLEVEL_IDX-1:2]) | (&{0}[1:0])));".format(reg_bitmap),
            ],
            "=", True)

        cg.emit()
        cg.align_assignment(
            "{}_counter_non_zero_s{}".format(self.name(), seq_cycle + 1), [
            "(reg_is_enque_s[{}] |".format(seq_cycle),
            "{}[WATERLEVEL_IDX]);".format(reg_bitmap),
            ], "=", False
        )

        if not self.sram_bitmap:
            cg.comment("Write L{} bitmap".format(self.level_id))
            bm_lhs = "{}_bitmap_s{}".format(self.name(), seq_cycle + 1)

            bm_rhs_term = ("l1_bitmap" if (self.level_id == 1) else
                           "reg_{}_bitmap_s[{}]".format(self.name(), seq_cycle))

            cg.start_conditional("if", "reg_is_enque_s[{}]".format(seq_cycle))
            cg.align_assignment(bm_lhs, [
                "({} |".format(bm_rhs_term),
                "reg_{}_bitmap_idx_onehot_s{});".format(self.name(), seq_cycle)
            ], "=")
            cg.end_conditional("if")
            cg.start_conditional("else", None)
            cg.align_assignment(bm_lhs, [
                "(",
                ("{}_counter_non_zero_s{} ? {} :".format(
                    self.name(), (seq_cycle + 1), bm_rhs_term)),
                ("({} & ~reg_{}_bitmap_idx_onehot_s{}));".format(
                            bm_rhs_term, self.name(), seq_cycle)),
            ], "=", True)
            cg.end_conditional("else")

        if self.is_leaf:
            cg.comment("Read PB contents")
            cg.emit("pb_rden = reg_valid_s[{}];".format(seq_cycle))
            cg.emit()

        elif self.next_level.sram_bitmap:
            cg.comment("Read L{} bitmap".format(self.level_id + 1))
            cg.emit("bm_{}_rden = reg_valid_s[{}];".format(
                self.next_level.name(), seq_cycle))

            rdaddress_lhs = "bm_{}_rdaddress".format(self.next_level.name())
            rdaddress_rhs_idx_term = ("reg_{}_bitmap_idx_s{}".format(
                                      self.name(), seq_cycle))

            if self.level_id == 1:
                cg.emit("{} = {};".format(rdaddress_lhs, rdaddress_rhs_idx_term))
            else:
                cg.align_assignment(rdaddress_lhs, [
                    "{{reg_{}_addr_s[{}],".format(self.name(), seq_cycle),
                    "{}}};".format(rdaddress_rhs_idx_term),
                ], "=")
            cg.emit()

        if self.level_id == 1:
            cg.comment("Compute conflicts")
            for offset in range(1, 5):
                rhs_addr_midfix = (
                    "priority" if (self.num_bitmap_levels == 1)
                    else "{}_addr".format(self.next_level.name()))

                cg.align_assignment(
                    ("{}_addr_conflict_s{}_s{}"
                     .format(self.next_level.name(),
                             seq_cycle + 1 + offset,
                             seq_cycle + 1)),
                    ["(",
                    ("reg_valid_s[{}] && reg_valid_s[{}] &&"
                    .format(seq_cycle, seq_cycle + offset)),

                    ("(reg_l1_bitmap_idx_s{} == reg_{}_s[{}]));"
                    .format(seq_cycle, rhs_addr_midfix, seq_cycle + offset))
                    ],
                "=", True)
                cg.emit()

        else:
            cg.comment("Compute conflicts")
            for offset in range(1, 5):
                rhs_priority = (
                    "reg_priority_s" if self.is_leaf else
                    "reg_{}_addr_s".format(self.next_level.name())
                )
                cg.align_assignment("{}_addr_conflict_s{}_s{}"
                                    .format(self.next_level.name(),
                                            seq_cycle + 1 + offset,
                                            seq_cycle + 1), [
                    "(",
                    ("reg_{}_addr_conflict_s{}_s{}"
                    .format(self.name(), seq_cycle + offset, seq_cycle)),

                    ("{}&& (reg_{}_bitmap_idx_s{} =="
                     .format(cg.tab(), self.name(), seq_cycle)),

                    ("{}{}[{}][HEAP_LOG_BITMAP_WIDTH-1:0]));"
                     .format(cg.tab(2), rhs_priority, seq_cycle + offset)),
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

        seq_cycle -= 1

        # Read delay for SRAM-based counters
        if self.sram_counters:
            cg.comment("Stage {}: NOOP, read delay for L{} counter."
                       .format(seq_cycle + 1, self.level_id), True)

            cg.comment([
                "Compute the read carry direction. If the",
                "active op in Stage {} is of the same type".format(seq_cycle + 2),
                "or the bitmap is empty, carry right.",
            ])
            align_to_str = ("(reg_{}_bitmap_empty_s{} || ("
                            .format(self.name(), seq_cycle))

            cg.start_conditional("if", [
                "!reg_is_enque_s[{}] &&".format(seq_cycle),
                "{}_counter_non_zero_s{} &&".format(self.name(), seq_cycle + 2),
                "reg_{}_addr_conflict_s{}_s{} &&".format(self.name(), seq_cycle + 1, seq_cycle),

                "{}reg_op_type_s[{}] ==".format(align_to_str, seq_cycle),
                "{}reg_op_type_s[{}]))".format(" " * len(align_to_str), seq_cycle + 1)
            ])
            cg.emit("rcd_s{} = READ_CARRY_RIGHT;".format(seq_cycle + 1))
            cg.end_conditional("if")
            cg.comment("Fallthrough: default to carry down")
            cg.emit()

            cg.comment("Counter is updating this cycle, so output is stale")
            cg.start_conditional("if", [
                ("(reg_{0}_bitmap_idx_s{1} == reg_{0}_bitmap_idx_s{2})"
                 .format(self.name(), seq_cycle, seq_cycle + 1)),

                ("&& reg_{}_addr_conflict_s{}_s{}".format(
                 self.name(), seq_cycle + 1, seq_cycle)),
            ])
            cg.emit([
                "{0}_counter_q_s{1} = {0}_counter_s{2};".format(
                    self.name(), seq_cycle + 1, seq_cycle + 2),

                "{0}_counter_s{1} = {0}_counter_s{2};".format(
                    self.name(), seq_cycle + 1, seq_cycle + 2),
            ])
            cg.end_conditional("if")

            cg.comment("Counter was updated last cycle (there was R/W conflict)")
            cg.start_conditional("else if", [
                ("(reg_{0}_bitmap_idx_s{1} == reg_{0}_bitmap_idx_s{2})"
                 .format(self.name(), seq_cycle, seq_cycle + 2)),

                ("&& reg_{}_addr_conflict_s{}_s{}".format(
                 self.name(), seq_cycle + 2, seq_cycle)),
            ])
            cg.emit([
                "{0}_counter_q_s{1} = reg_{0}_counter_s{2};".format(
                    self.name(), seq_cycle + 1, seq_cycle + 2),

                "{0}_counter_s{1} = reg_{0}_counter_s{2};".format(
                    self.name(), seq_cycle + 1, seq_cycle + 2),
            ])
            cg.end_conditional("else if")
            cg.comment([
                "Fallthrough, defaults to:",
                ("counter_{0}_q for {0}_counter_q_s{1}"
                 .format(self.name(), seq_cycle + 1)),

                ("reg_{0}_counter_s{1} for {0}_counter_s{1}"
                 .format(self.name(), seq_cycle + 1)),
            ])
            cg.emit()
            seq_cycle -= 1

        # Bitmap index computation
        cg.comment([
            ("Stage {}: Compute the L{} bitmap index and postop"
             .format(seq_cycle + 1, self.level_id)),
            ("bitmap, and read the corresponding L{} counter."
             .format(self.level_id)),
        ], True)

        cg.comment("L{} bitmap changes?".format(self.level_id))
        bitmap_changes_lhs = "{}_bitmap_changes_s{}_s{}".format(self.name(),
            (seq_cycle + 2 + int(self.sram_counters)), (seq_cycle + 1))

        if self.level_id == 1:
            cg.align_assignment(bitmap_changes_lhs, [
                "(",
                ("reg_valid_s[{0}] && (reg_is_enque_s[{0}] ||"
                 .format(seq_cycle + 1)),

                ("                   !{}_counter_non_zero_s{}));"
                 .format(self.name(), seq_cycle + 2))
            ], "=", True)

        else:
            cg.align_assignment(bitmap_changes_lhs, [
                "(",
                "reg_{}_addr_conflict_s{}_s{} &&".format(self.name(),
                    (seq_cycle + 1 + int(self.sram_counters)), seq_cycle),

                ("(reg_is_enque_s[{}] || !{}_counter_non_zero_s{}));"
                 .format((seq_cycle + 1 + int(self.sram_counters)),
                         self.name(), (seq_cycle + 2 + int(self.sram_counters))))
            ], "=", True)

        cg.emit()

        cg.comment("Compute L{} bitmap idx and postop".format(self.level_id))
        bm_rhs_term = ("l1_bitmap" if (self.level_id == 1) else
                       "reg_{}_bitmap_s[{}]".format(self.name(), seq_cycle))

        bitmap_idx_lhs = ("{}_bitmap_idx_s{}".format(
                          self.name(), seq_cycle + 1))

        bitmap_empty_lhs = ("{}_bitmap_empty_s{}".format(
                            self.name(), seq_cycle + 1))

        bitmap_idx_onehot_lhs = ("{}_bitmap_idx_onehot_s{}".format(
                                 self.name(), seq_cycle + 1))

        bitmap_postop_lhs = ("{}_bitmap_postop_s{}".format(
                             self.name(), seq_cycle + 1))

        cg.start_switch("reg_op_type_s[{}]".format(seq_cycle))
        conditionals = [bitmap_changes_lhs]
        if self.sram_counters:
            conditionals.insert(0, "reg_{}_addr_conflict_s{}_s{}".format(
                                    self.name(), seq_cycle + 1, seq_cycle))

        for case, midfix in [("MAX", "msb"), ("MIN", "lsb")]:
            cg.start_case("HEAP_OP_DEQUE_{}".format(case))
            # Bitmap idx
            values = [
                "ffs_{}_inst_{}[{}]".format(
                    self.name(), midfix,
                    1 + int(self.sram_counters)),

                "ffs_{}_inst_{}[0]".format(
                    self.name(), midfix)
            ]
            if self.sram_counters:
                values.insert(0, "ffs_{}_inst_{}[1]"
                              .format(self.name(), midfix))

            cg.align_ternary(bitmap_idx_lhs, conditionals, values, "=")

            # Bitmap empty
            cg.emit()
            values = [
                "ffs_{}_inst_zero[{}]".format(
                    self.name(), 1 + int(self.sram_counters)),

                "ffs_{}_inst_zero[0]".format(self.name())
            ]
            if self.sram_counters:
                values.insert(0, "ffs_{}_inst_zero[1]".format(self.name()))

            cg.align_ternary(bitmap_empty_lhs, conditionals, values, "=")

            # Onehot idx
            cg.emit()
            values = [
                "ffs_{}_inst_{}_onehot[{}]".format(
                    self.name(), midfix,
                    1 + int(self.sram_counters)),

                "ffs_{}_inst_{}_onehot[0]".format(
                    self.name(), midfix)
            ]
            if self.sram_counters:
                values.insert(0, "ffs_{}_inst_{}_onehot[1]"
                              .format(self.name(), midfix))

            cg.align_ternary(bitmap_idx_onehot_lhs, conditionals, values, "=")

            # Postop
            cg.emit()
            values = [
                ["{} ^".format(bitmap_idx_onehot_lhs),
                 "reg_{}_bitmap_postop_s{}".format(self.name(),
                    seq_cycle + 1 + int(self.sram_counters))
                ],
                ["{} ^".format(bitmap_idx_onehot_lhs), bm_rhs_term]
            ]
            if self.sram_counters:
                values.insert(0, [
                    "{} ^".format(bitmap_idx_onehot_lhs),
                    "reg_{}_bitmap_postop_s{}".format(self.name(), seq_cycle + 1)
                ])

            cg.align_ternary(bitmap_postop_lhs, conditionals, values, "=")
            cg.end_case() # HEAP_OP_DEQUE_*

        cg.comment("HEAP_OP_ENQUE")
        cg.start_case("default")
        bitmap_idx_ub = ("({} * HEAP_LOG_BITMAP_WIDTH) - 1".format(
                         (self.num_bitmap_levels - self.level_id) + 1))

        bitmap_idx_lb = ("0" if self.is_leaf else
                         "({} * HEAP_LOG_BITMAP_WIDTH)".format(
                            self.num_bitmap_levels - self.level_id))
        cg.emit([
            "{} = 0;".format(bitmap_empty_lhs),

            "{} = (reg_priority_s[{}][(".format(bitmap_idx_lhs,
                                                seq_cycle),
            "{}{})".format(cg.tab(2), bitmap_idx_ub),
            "{}: {}]);".format(cg.tab(2), bitmap_idx_lb),
        ])
        cg.emit()
        cg.emit([
            "{} = (1 << {});".format(bitmap_idx_onehot_lhs, bitmap_idx_lhs)
        ])
        values = [
            ["{} |".format(bitmap_idx_onehot_lhs),
             "reg_{}_bitmap_postop_s{}".format(self.name(),
                seq_cycle + 1 + int(self.sram_counters))
            ],
            ["{} |".format(bitmap_idx_onehot_lhs),
             "{}".format(bm_rhs_term)]
        ]
        if self.sram_counters:
            values.insert(0, [
                "{} |".format(bitmap_idx_onehot_lhs),
                "reg_{}_bitmap_postop_s{}".format(self.name(), seq_cycle + 1)
            ])
        cg.align_ternary(bitmap_postop_lhs, conditionals, values, "=")
        cg.end_case() # HEAP_OP_ENQUE

        cg.end_switch()

        valid_and = ("reg_valid_s[{}] && ".format(seq_cycle + 1)
                     if (self.level_id == 1) else "")
        if self.sram_counters:
            cg.comment([
                "Compute the read carry direction. If the active",
                ("op in Stage {} is of the same type, carry up."
                 .format(seq_cycle + 3)),
            ])
            cg.start_conditional("if", [
                "!reg_is_enque_s[{}] &&".format(seq_cycle),
                ("{}{}_counter_non_zero_s{} &&"
                 .format(valid_and, self.name(), seq_cycle + 3)),

                "reg_{}_addr_conflict_s{}_s{} &&".format(self.name(),
                                                         seq_cycle + 2, seq_cycle),
                ("(reg_op_type_s[{}] == reg_op_type_s[{}])"
                 .format(seq_cycle, seq_cycle + 2))
            ])
            cg.emit("rcd_s{} = READ_CARRY_UP;".format(seq_cycle + 1))
            cg.emit()

            cg.comment([
                ("Special case: The active op in Stage {} is also"
                 .format(seq_cycle + 2)),
                "of the same type, which means that it's bound",
                "to carry right; here, we do the same.",
            ])
            cg.start_conditional("if", [
                ("(reg_op_type_s[{}] == reg_op_type_s[{}]) &&"
                 .format(seq_cycle, seq_cycle + 1)),
                conditionals[0]
            ])
            cg.emit("rcd_s{} = READ_CARRY_RIGHT;".format(seq_cycle + 1))
            cg.end_conditional("if")
            cg.end_conditional("if")
            cg.comment("Fallthrough: default to carry down")
            cg.emit()

            cg.comment("Read the L{} counter".format(self.level_id))
            cg.emit("counter_{}_rden = reg_valid_s[{}];".format(self.name(), seq_cycle))

            cg.align_assignment("counter_{}_rdaddress".format(self.name()), [
                "{{reg_{}_addr_s[{}],".format(self.name(), seq_cycle),
                "{}}};".format(bitmap_idx_lhs)
            ], "=")
        else:
            cg.comment([
                "Compute the read carry direction. If the",
                ("active op in Stage {} is of the same type"
                 .format(seq_cycle + 2)),
                "or the bitmap is empty, carry right.",
            ])
            alignto_lhs = "({} || (".format(bitmap_empty_lhs)
            cg.start_conditional("if", [
                "!reg_is_enque_s[{}] &&".format(seq_cycle),
                ("{}{}_counter_non_zero_s{} &&"
                 .format(valid_and, self.name(), seq_cycle + 2)),

                "{}reg_op_type_s[{}] ==".format(alignto_lhs, seq_cycle),
                "{}reg_op_type_s[{}]))".format(" " * len(alignto_lhs), seq_cycle + 1)
            ])
            cg.emit("rcd_s{} = READ_CARRY_RIGHT;".format(seq_cycle + 1))
            cg.end_conditional("if")
            cg.comment("Fallthrough: default to carry down")
            cg.emit()

        seq_cycle -= 1

        # Read delay for SRAM-based bitmaps
        if self.sram_bitmap:
            cg.comment("Stage {}: NOOP, read delay for L{} bitmap."
                       .format(seq_cycle + 1, self.level_id), True)

            cg.comment("L{} bitmap updated this cycle, so output is stale"
                       .format(self.level_id))

            cg.start_conditional("if", ("reg_{}_addr_conflict_s{}_s{}".format(
                                        self.name(), self.end_cycle - 1, seq_cycle)))
            cg.emit(
                "{0}_bitmap_s{1} = bm_{0}_data;".format(self.name(), seq_cycle + 1)
            )
            cg.end_conditional("if")
            cg.comment("L{} bitmap was updated last cycle (R/W conflict)"
                       .format(self.level_id))

            cg.start_conditional("else if", ("reg_{}_addr_conflict_s{}_s{}".format(
                                             self.name(), self.end_cycle, seq_cycle)))
            cg.emit(
                "{0}_bitmap_s{1} = bm_{0}_data_r;".format(self.name(), seq_cycle + 1)
            )
            cg.end_conditional("else if")
            cg.comment("Fallthrough: default to bm_{}_q".format(self.name()))
            cg.emit()
            seq_cycle -= 1


    def emit_sequential_pipeline_logic(self, cg: CodeGen) -> None:
        """Emit sequential logic for this level."""

        # Fetch configuration
        reg_bitmap = not self.sram_bitmap
        reg_counters = not self.sram_counters

        # Write-back counter, bitmap
        cycle = self.end_cycle
        cg.comment([
            ("Stage {}: Write-back the L{} counter and bitmap,"
             .format(cycle, self.level_id)),
            ("and read the corresponding {}.".format(
                "PB (head and tail)" if self.is_leaf else
                    "L{} bitmap".format(self.level_id + 1))),
        ], True)

        value_override = {}
        if self.is_leaf: value_override[
            "reg_priority_s"] = "priority_s{}".format(cycle)
        self.bbq.emit_sequential_primary_signals(cycle, value_override)

        reg_bitmap_idx = ("reg_{}_bitmap_idx_s{}".format(self.name(), cycle - 1))
        emit_newline = False
        if self.level_id > 1:
            cg.emit(
                "reg_{}_bitmap_s[{}] <= {};"
                .format(self.name(), cycle,
                        ("bm_{}_data".format(self.name())
                         if self.sram_bitmap else
                         "{}_bitmap_s{}".format(self.name(), cycle))))

            for level in self.bbq.bitmap_levels:
                if level.id < 2: continue
                elif level.id > self.level_id: break
                cg.emit("{0}[{1}] <= {0}[{2}];".format(
                    "reg_{}_addr_s".format(level.name()), cycle, cycle - 1))

            for level in self.bbq.bitmap_levels:
                if level.id < 2: continue
                elif level.id >= self.level_id: break
                cg.emit("{0}[{1}] <= {0}[{2}];".format(
                    "reg_{}_bitmap_s".format(level.name()), cycle, cycle - 1))

            emit_newline = True

        if not self.is_leaf:
            next_addr_lhs = ("reg_{}_addr_s[{}]"
                             .format(self.next_level.name(), cycle))

            if self.level_id > 1:
                cg.emit(
                    ("{} <= {{reg_{}_addr_s[{}], {}}};"
                     .format(next_addr_lhs, self.name(),
                             cycle - 1, reg_bitmap_idx)))
            else:
                cg.emit("{} <= {};".format(
                    next_addr_lhs, reg_bitmap_idx))

            emit_newline = True

        if emit_newline: cg.emit()
        cg.emit([
            ("reg_{0}_counter_s{1} <= {0}_counter_s{1};"
             .format(self.name(), cycle)),
        ])
        emit_newline = False
        if self.sram_counters:
            cg.emit([
                ("reg_{}_bitmap_idx_s{} <= {};"
                 .format(self.name(), cycle, reg_bitmap_idx)),
            ])
            emit_newline = True

        if self.is_leaf:
            rhs_counter_midfix = "rc_" if self.sram_counters else ""
            cg.emit([
                ("reg_old_{0}_counter_s{1} <= reg_{0}_counter_{3}s{2};"
                 .format(self.name(), cycle, cycle - 1, rhs_counter_midfix)),

                ("reg_{0}_counter_non_zero_s{1} <= {0}_counter_non_zero_s{1};"
                .format(self.name(), cycle)),
            ])
            emit_newline = True

        if emit_newline: cg.emit()
        for offset in range(1, 5):
            cg.emit(
                "reg_{0}_addr_conflict_s{1}_s{2} <= "
                "{0}_addr_conflict_s{1}_s{2};".format(
                self.next_level.name(), cycle + offset, cycle)
            )
        cg.emit()

        if reg_counters or reg_bitmap:
            if reg_counters and reg_bitmap:
                cg.comment("Write-back L{} bitmap and counter"
                           .format(self.level_id))
            else:
                cg.comment("Write-back L{} {}".format(
                    self.level_id, "bitmap" if reg_bitmap
                    else "counter"))

            cg.start_conditional("if", "{}".format(
                "reg_valid_s[{}]".format(cycle - 1)
            ))
            if reg_bitmap:
                lhs = ("l1_bitmap" if (self.level_id == 1) else
                       ("{0}_bitmaps[reg_{0}_addr_s[{1}]]"
                        .format(self.name(), cycle - 1)))

                cg.emit("{} <= {}_bitmap_s{};"
                        .format(lhs, self.name(), cycle))

            if reg_counters:
                cg.emit("{0}_counters[{1}] <= {0}_counter_s{2};"
                        .format(self.name(), reg_bitmap_idx, cycle))

            cg.end_conditional("if")
            cg.emit()

        if (not self.is_leaf) and (not self.next_level.sram_bitmap):
            cg.comment("Forward L{} bitmap updates".format(self.level_id + 1))
            cg.align_ternary(
                "reg_{}_bitmap_s[{}]".format(
                    self.next_level.name(), cycle),

                ["{}_addr_conflict_s{}_s{}"
                 .format(self.next_level.name(),
                         self.next_level.end_cycle, cycle)],

                ["{}_bitmap_s{}".format(self.next_level.name(),
                                        self.next_level.end_cycle),

                 "{}_bitmaps[{}]".format(self.next_level.name(),
                                         reg_bitmap_idx)],
                "<=", True, True)

            cg.emit()

        cg.start_ifdef("DEBUG")
        id_str_prefix = ("logical ID: %0d, "
                         if self.bbq.is_logically_partitioned else "")

        id_val_prefix = ("reg_bbq_id_s[{}], ".format(cycle - 1)
                         if self.bbq.is_logically_partitioned else "")

        if self.level_id == 1:
            cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
            cg.emit("$display(")
            cg.emit([
                ("\"[BBQ] At S{} ({}op: %s), updating L1 counter (L1_idx = %0d) to %0d\","
                 .format(cycle, id_str_prefix)),

                ("{}reg_op_type_s[{}].name, {}, {}_counter_s{}[WATERLEVEL_IDX-1:0]);"
                 .format(id_val_prefix, cycle - 1, reg_bitmap_idx, self.name(), cycle)),
            ], True, 4)
            cg.end_conditional("if")

        else:
            cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
            cg.emit("$display(")
            cg.emit([
                ("\"[BBQ] At S{0} ({1}op: %s), updating L{2} counter "
                 "(L{2}_addr, L{2}_idx) \",".format(cycle, id_str_prefix, self.level_id)),

                ("{0}reg_op_type_s[{1}].name, \"= (%0d, %0d) to %0d\", "
                 "reg_{2}_addr_s[{1}],".format(id_val_prefix, cycle - 1, self.name())),

                ("{}, {}_counter_s{}[WATERLEVEL_IDX-1:0]);"
                 .format(reg_bitmap_idx, self.name(), cycle))
            ], True, 4)
            cg.end_conditional("if")
        cg.end_ifdef()

        cg.emit()
        cycle -= 1

        # Read delay for SRAM-based counters
        if self.sram_counters:
            cg.comment("Stage {}: NOOP, read delay for L{} counter."
                       .format(cycle, self.level_id), True)

            self.bbq.emit_sequential_primary_signals(cycle)

            for level in self.bbq.bitmap_levels:
                if level.id < 2: continue
                elif level.id > self.level_id: break
                cg.emit("{0}[{1}] <= {0}[{2}];".format(
                    "reg_{}_addr_s".format(level.name()), cycle, cycle - 1))

            for level in self.bbq.bitmap_levels:
                if level.id < 2: continue
                elif level.id >= self.level_id: break
                cg.emit("{0}[{1}] <= {0}[{2}];".format(
                    "reg_{}_bitmap_s".format(level.name()), cycle, cycle - 1))

            for offset in range(1, 5):
                cg.emit(
                    "reg_{0}_addr_conflict_s{1}_s{2} <= "
                    "reg_{0}_addr_conflict_s{3}_s{4};".format(
                        self.name(), cycle + offset, cycle,
                        cycle + offset - 1, cycle - 1)
                )
            cg.emit()

            conditional = ("reg_{}_counter_rdvalid_r1_s{}"
                           .format(self.name(), cycle - 1))

            counter_lhs = ("reg_{}_counter_rc_s{}"
                           .format(self.name(), cycle))

            cg.align_ternary("reg_{}_counter_s{}".format(self.name(), cycle),
                             [conditional],
                             ["{}_counter_q_s{}".format(self.name(), cycle),
                              "{}_counter_s{}".format(self.name(), cycle),
                             ],
                             "<=", False, True)

            cg.start_switch("rcd_s{}".format(cycle))
            cg.start_case("READ_CARRY_DOWN")
            cg.emit([
                "{0}{1} <= {0}{2};".format("reg_{}_bitmap_idx_s".format(
                                           self.name()), cycle, cycle - 1),

                "{0}{1} <= {0}{2};".format("reg_{}_bitmap_postop_s".format(
                                           self.name()), cycle, cycle - 1),

                "{0}{1} <= {0}{2};".format("reg_{}_bitmap_idx_onehot_s".format(
                                           self.name()), cycle, cycle - 1),
            ])
            cg.emit()
            cg.align_ternary(counter_lhs, [conditional],
                             ["{}_counter_q_s{}".format(self.name(), cycle),
                              "{}_counter_s{}".format(self.name(), cycle),
                             ],
                             "<=", False, True)
            cg.end_case() # READ_CARRY_DOWN

            cg.start_case("READ_CARRY_RIGHT")
            cg.emit("{} <= {}_counter_s{};".format(
                counter_lhs, self.name(), cycle + 1))
            cg.end_case() # READ_CARRY_RIGHT

            cg.emit("default: ;")
            cg.end_switch()
            cg.emit()

            if self.level_id > 1:
                bitmap_data = ("bm_{}_data".format(self.name())
                               if self.sram_bitmap else
                               "{}_bitmap_s{}".format(self.name(), cycle + 1))

                cg.comment("Forward L{} bitmap updates".format(self.level_id))
                cg.align_ternary(
                    "reg_{}_bitmap_s[{}]".format(self.name(), cycle),

                    ["reg_{}_addr_conflict_s{}_s{}"
                     .format(self.name(), cycle, cycle - 1)],

                    [bitmap_data,
                     "reg_{}_bitmap_s[{}]".format(self.name(), cycle - 1)
                    ],
                "<=", True, True)
                cg.emit()

            cg.start_ifdef("DEBUG")
            id_str_prefix = ("logical ID: %0d, "
                             if self.bbq.is_logically_partitioned else "")

            id_val_prefix = ("reg_bbq_id_s[{}], ".format(cycle - 1)
                             if self.bbq.is_logically_partitioned else "")

            cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
            cg.emit("$display(")
            cg.emit([
                ("\"[BBQ] At S{} ({}op: %s) for (L{} addr = %0d),\","
                 .format(cycle, id_str_prefix, self.level_id)),

                ("{0}reg_op_type_s[{1}].name, reg_{2}_addr_s[{1}],"
                 .format(id_val_prefix, cycle - 1, self.name())),

                "\" RCD is %s\", rcd_s{}.name);".format(cycle)
            ], True, 4)
            cg.end_conditional("if")
            cg.end_ifdef()

            cg.emit()
            cycle -= 1

        # Bitmap index computation
        cg.comment([
            ("Stage {}: Compute the L{} bitmap index and postop"
            .format(cycle, self.level_id)),
            ("bitmap, and read the corresponding L{} counter."
            .format(self.level_id))
        ], True)

        self.bbq.emit_sequential_primary_signals(cycle)

        for level in self.bbq.bitmap_levels:
            if level.id < 2: continue
            elif level.id > self.level_id: break
            cg.emit("{0}[{1}] <= {0}[{2}];".format(
                "reg_{}_addr_s".format(level.name()), cycle, cycle - 1))

        for level in self.bbq.bitmap_levels:
            if level.id < 2: continue
            elif level.id >= self.level_id: break
            cg.emit("{0}[{1}] <= {0}[{2}];".format(
                "reg_{}_bitmap_s".format(level.name()), cycle, cycle - 1))

        if self.level_id > 1:
            for offset in range(1, 5):
                cg.emit(
                    "reg_{0}_addr_conflict_s{1}_s{2} <= "
                    "reg_{0}_addr_conflict_s{3}_s{4};".format(
                        self.name(), cycle + offset, cycle,
                        cycle + offset - 1, cycle - 1)
                )
            cg.emit()

        counter_rdvalid = ("reg_{}_counter_rdvalid_r1_s{}"
                           .format(self.name(), cycle))

        reg_counter_lhs = ("reg_{}_counter_s{}"
                           .format(self.name(), cycle))

        if self.sram_counters:
            cg.emit("{} <= 0;".format(counter_rdvalid))

        else:
            cg.emit("reg_{}_bitmap_empty_s{} <= 0;"
                    .format(self.name(), cycle))
        cg.emit()
        cg.start_switch("rcd_s{}".format(cycle))

        cg.start_case("READ_CARRY_DOWN")
        midfixes = ["bitmap_idx_s", "bitmap_empty_s",
                    "bitmap_postop_s", "bitmap_idx_onehot_s"]

        for midfix in midfixes:
            cg.emit(
                "reg_{0}_{1}{2} <= {0}_{1}{2};"
                .format(self.name(), midfix, cycle))

        cg.emit()
        if self.sram_counters:
            cg.emit("{} <= (!{}_bitmap_empty_s{});"
                    .format(counter_rdvalid, self.name(), cycle))
        else:
            if self.level_id == 1:
                cg.align_assignment(reg_counter_lhs, [
                    "(",
                    "(reg_valid_s[{}] &&".format(cycle),

                    ("{0}({1}_{2}{3} == reg_{1}_{2}{3})) ?"
                     .format(cg.tab(), self.name(), "bitmap_idx_s", cycle)),

                    ("{0}{1}_counter_s{2} : {1}_counters[{1}_bitmap_idx_s{3}]);"
                     .format(cg.tab(), self.name(), cycle + 1, cycle))
                ],
                "<=", True)
            else:
                cg.align_assignment(reg_counter_lhs, [
                    "(",
                    ("reg_valid_s[{0}] && reg_{1}_addr_conflict_s{0}_s{2} &&"
                     .format(cycle, self.name(), cycle - 1)),

                    ("{0}({1}_{2}{3} == reg_{1}_{2}{3})) ?"
                     .format(cg.tab(), self.name(), "bitmap_idx_s", cycle)),

                    ("{0}{1}_counter_s{2} : {1}_counters[{1}_bitmap_idx_s{3}]);"
                     .format(cg.tab(), self.name(), cycle + 1, cycle))
                ],
                "<=", True)
        cg.end_case() # READ_CARRY_DOWN

        if self.sram_counters:
            cg.start_case("READ_CARRY_UP")
            cg.emit([
                ("reg_{0}_bitmap_empty_s{1} <= 0;"
                 .format(self.name(), cycle)),

                ("reg_{0}_bitmap_idx_s{1} <= reg_{0}_bitmap_idx_s{2};"
                 .format(self.name(), cycle, cycle + 1)),

                ("reg_{0}_bitmap_idx_onehot_s{1} <= reg_{0}_bitmap_idx_onehot_s{2};"
                 .format(self.name(), cycle, cycle + 1)),
            ])
            cg.emit()
            cg.start_conditional("if", ("!reg_{}_addr_conflict_s{}_s{}"
                                        .format(self.name(), cycle, cycle - 1)))
            cg.emit([
                "reg_{}_bitmap_postop_s{} <= (".format(self.name(), cycle),
                "{}reg_{}_bitmap_postop_s{});".format(cg.tab(), self.name(), cycle + 1)
            ])
            cg.end_conditional("if")
            cg.end_case() # READ_CARRY_UP

        else:
            cg.start_case("READ_CARRY_RIGHT")
            cg.emit("reg_{0}_counter_s{1} <= {0}_counter_s{2};"
                    .format(self.name(), cycle, cycle + 1))

            cg.end_case() # READ_CARRY_RIGHT

        cg.emit("default: ;")
        cg.end_switch()
        cg.emit()

        if self.level_id > 1:
            bitmap_data = ("bm_{}_data".format(self.name())
                           if self.sram_bitmap else
                           "{}_bitmap_s{}".format(self.name(),
                                                  self.end_cycle))

            cg.comment("Forward L{} bitmap updates".format(self.level_id))
            cg.align_ternary(
                "reg_{}_bitmap_s[{}]".format(self.name(), cycle),

                ["reg_{}_addr_conflict_s{}_s{}".format(
                    self.name(), self.end_cycle - 1, cycle - 1)],

                [bitmap_data,
                 "reg_{}_bitmap_s[{}]".format(self.name(), cycle - 1)
                ],
            "<=", True, True)
            cg.emit()

        cg.start_ifdef("DEBUG")
        id_str_prefix = ("logical ID: %0d, "
                         if self.bbq.is_logically_partitioned else "")

        id_val_prefix = ("reg_bbq_id_s[{}], ".format(cycle - 1)
                         if self.bbq.is_logically_partitioned else "")

        cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
        cg.emit("$display(")
        if self.level_id > 1:
            cg.emit([
                ("\"[BBQ] At S{} ({}op: %s) for (L{} addr = %0d),\","
                 .format(cycle, id_str_prefix, self.level_id)),

                ("{0}reg_op_type_s[{1}].name, reg_{2}_addr_s[{1}],"
                 .format(id_val_prefix, cycle - 1, self.name())),

                "\" RCD is %s\", rcd_s{}.name);".format(cycle)
            ], True, 4)

        else:
            cg.emit([
                "\"[BBQ] At S{} ({}op: %s),\",".format(cycle, id_str_prefix),
                "{}reg_op_type_s[{}].name,".format(id_val_prefix, cycle - 1),
                "\" RCD is %s\", rcd_s{}.name);".format(cycle)
            ], True, 4)

        cg.end_conditional("if")
        cg.end_ifdef()

        cg.emit()
        cycle -= 1

        # Read delay for SRAM-based bitmaps
        if self.sram_bitmap:
            cg.comment("Stage {}: NOOP, read delay for L{} bitmap."
                       .format(cycle, self.level_id), True)

            self.bbq.emit_sequential_primary_signals(cycle)
            cg.emit("reg_{0}[{1}] <= {0}{1};".format(
                    "{}_bitmap_s".format(self.name()), cycle))

            for level in self.bbq.bitmap_levels:
                if level.id < 2: continue
                elif level.id > self.level_id: break
                cg.emit("{0}[{1}] <= {0}[{2}];".format(
                    "reg_{}_addr_s".format(level.name()), cycle, cycle - 1))

            for level in self.bbq.bitmap_levels:
                if level.id < 2: continue
                elif level.id >= self.level_id: break
                cg.emit("{0}[{1}] <= {0}[{2}];".format(
                    "reg_{}_bitmap_s".format(level.name()), cycle, cycle - 1))

            if self.level_id > 1:
                for offset in range(1, 5):
                    cg.emit(
                        "reg_{0}_addr_conflict_s{1}_s{2} <= "
                        "reg_{0}_addr_conflict_s{3}_s{4};".format(
                            self.name(), cycle + offset, cycle,
                            cycle + offset - 1, cycle - 1)
                    )
                cg.emit()

            cg.start_ifdef("DEBUG")
            id_str_prefix = ("logical ID: %0d, "
                             if self.bbq.is_logically_partitioned else "")

            id_val_prefix = ("reg_bbq_id_s[{}], ".format(cycle - 1)
                             if self.bbq.is_logically_partitioned else "")

            cg.start_conditional("if", "reg_valid_s[{}]".format(cycle - 1))
            cg.emit("$display(")
            cg.emit([
                ("\"[BBQ] At S{} ({}op: %s) for (L{} addr = %0d)\","
                 .format(cycle, id_str_prefix, self.level_id)),

                ("{0}reg_op_type_s[{1}].name, reg_{2}_addr_s[{1}]);"
                 .format(id_val_prefix, cycle - 1, self.name())),
            ], True, 4)

            cg.end_conditional("if")
            cg.end_ifdef()

            cg.emit()
            cycle -= 1
