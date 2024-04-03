<div align="justify">

## FPGA Simulation

### Generating BBQ's Source Code

Unlike the other designs, BBQ's implementation file (`bbq.sv`) is not checked in to its `src` directory. Instead, we use a Python wrapper to generate BBQ's source code by stitching together modular blocks of hand-written SystemVerilog code. The reason is that the semantics of BBQ's pipeline depend heavily on the _number of levels_ in its bitmap tree, and encoding this configurability directly in SystemVerilog would yield highly complex and unwieldy source code. Instead, we choose to offload the complexity of handling this parameter to Python, resulting in simpler, cleaner, and more manageable SystemVerilog code.

Thus, as a first step in the simulation flow, we need to generate BBQ's source code for a chosen number of bitmap levels (say, `NUM_BITMAP_LEVELS`). To do this, run the following snippet from this directory:
```
python3 generator/bbq.py ${NUM_BITMAP_LEVELS} > src/bbq.sv
```

This generates source code for a `bbq` SystemVerilog module with the specified bitmap tree depth. At this point, the tree depth is fixed, and should not be changed! However, you may still tune the _width_ of each bitmap, the queue size, and the width of each queue entry by initializing the appropriate parameters while instantiating the module (`HEAP_BITMAP_WIDTH`, `HEAP_MAX_NUM_ENTRIES`, and `HEAP_ENTRY_DWIDTH`, respectively). For example usage, please refer to `src/top.sv`.

### Simulating BBQ

As a starting point for simulation, this repository contains a testbench with a regression test suite for BBQ and the Find-First Set (FFS) module underlying BBQ. Once you have generated the BBQ source code (as described above), you can exercise the simulation testbench by following the README in the [tb](tb) subdirectory.

</div>
