#!/usr/bin/python3
from abc import ABC, abstractmethod

from codegen import CodeGen


class BBQLevel(ABC):
    """Represents a generic BBQ level."""
    def __init__(self, start_cycle: int, num_levels: int) -> None:
        self.start_cycle = start_cycle      # Starting pipeline cycle
        self.num_bitmap_levels = num_levels # Number of bitmap levels

        # Housekeeping
        self.prev_level: BBQLevel = None    # Pointer to the prev level
        self.next_level: BBQLevel = None    # Pointer to the next level

        # Miscellaneous
        self.fl_rd_delay: int = None        # Free-list read delay


    @property
    def end_cycle(self) -> int:
        """Ending pipeline cycle."""
        return self.start_cycle + self.latency()


    @abstractmethod
    def name(self) -> str:
        """Canonical level name."""
        raise NotImplementedError()


    @abstractmethod
    def latency(self) -> int:
        """Latency in cycles."""
        raise NotImplementedError()


    @abstractmethod
    def emit_stage_defs(self, cg: CodeGen) -> None:
        """Emit per-stage definitions."""
        raise NotImplementedError()


    @abstractmethod
    def emit_state_dependent_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-dependent combinational logic."""
        raise NotImplementedError()


    @abstractmethod
    def emit_combinational_default_assigns(self, cg: CodeGen) -> None:
        """Emit state-agnostic default assigns."""
        raise NotImplementedError()


    @abstractmethod
    def emit_state_agnostic_combinational_logic(self, cg: CodeGen) -> None:
        """Emit state-agnostic combinational logic."""
        raise NotImplementedError()


    @abstractmethod
    def emit_sequential_pipeline_logic(self, cg: CodeGen) -> None:
        """Emit sequential logic for this level."""
        raise NotImplementedError()
