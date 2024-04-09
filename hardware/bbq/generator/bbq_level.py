#!/usr/bin/python3
from __future__ import annotations

import typing
from abc import ABC, abstractmethod

from codegen import CodeGen

# Hack for type hinting with circular imports
if typing.TYPE_CHECKING: from bbq import BBQ


class BBQLevel(ABC):
    """Represents a generic BBQ level."""
    def __init__(self, bbq: BBQ, start_cycle: int) -> None:
        self.bbq = bbq                      # Pointer to BBQ instance
        self.start_cycle = start_cycle      # Starting pipeline cycle

        # Housekeeping
        self.prev_level: BBQLevel = None    # Pointer to the prev level
        self.next_level: BBQLevel = None    # Pointer to the next level


    @property
    def num_bitmap_levels(self) -> int:
        """Returns the bitmap level count."""
        return self.bbq.num_bitmap_levels


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
