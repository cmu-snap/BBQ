<div align="justify">

## FPGA Synthesis

This directory contains the required SystemVerilog code, Quartus project files, and bash scripts required to synthesize the encompassed designs (`bbq`, `bmw`, `pieo`, and `pifo`) to an Intel Stratix 10MX FPGA. If you wish to target a different FPGA device or family, you will need to modify the ".qsf" file and IP-generation tcl script in each of the subdirectories (to find all offending files, run `grep -Rn "DEVICE" --include=*.{qsf,template}` in this directory). We provide scripts for three different FPGA synthesis flows.

### (A) Single-configuration synthesis with a predefined target frequency

Each design has a set of parameters that are configurable at compile-time: for instance, we can synthesize PIFO with a specific number of queue elements (e.g., 1024) and priority bits (e.g., 9). This flow allows us to synthesize _one_ such configuration with a _predefined_ target frequency (or "fmax"). To use this flow, do the following steps:

1. First, we need to instantiate a PLL (clock circuit) IP operating at a fixed frequency to drive the design. For the design you want to synthesize (say, `DESIGN`, which can be either `bbq`, `bmw`, `pieo`, or `pifo`), choose the clock frequency in MHz you wish to target (say, `TARGET_FMAX_MHz`), then run the following command from this directory: ```${DESIGN}/setup.sh ${TARGET_FMAX_MHz}```. For instance, to setup PIFO to operate with a 200 MHz clock, run: ```pifo/setup.sh 200```

2. Finally, run the synthesis script as follows: ```${CONFIG_OPTION_1}=${CONFIG_VALUE_1} ... ${DESIGN}/scripts/synthesize.sh [SEED]```. You will need to set all the required configuration options in order to perform synthesis. The (optional) SEED value is used to seed the synthesis tool's random-number generator. To find the relevant options for a given design, refer to the docstring of the corresponding synthesis script. For instance, to synthesize PIFO with 2^10 elements and 9-bit priorities, run: ```ELEMENT_BITS=10 PRIORITY_BITS=9 pifo/scripts/synthesize.sh```.

Once synthesis completes, you can find the corresponding compiler reports (placement, timing, etc.) and bitstream (if successfully generated) in the ```${DESIGN}/quartus/output_files``` subdirectory.

### (B) Single-configuration synthesis with fmax bisection search

Often, the maximum achievable clock frequency (fmax) is not known ahead of time. This flow allows us to automatically find the close-to-best possible fmax (and the corresponding seed value) for a single design configuration using a bisection search over a range of clock frequencies. To use this flow for a given design (say, `DESIGN`), run the following command from this directory: ```${CONFIG_OPTION_1}=${CONFIG_VALUE_1} ... [MIN_FREQ=AAA] [MAX_FREQ=BBB] [PRECISION=CCC] ${DESIGN}/scripts/bisect_fmax.sh ${SEED_1} ${SEED_2} ...```. The configuration options have the same semantics as described in Step 2 of [(A)](#a-single-configuration-synthesis-with-a-predefined-target-frequency). Optionally, you can set the limits (in MHz) of the frequency range (`MIN_FREQ`, `MAX_FREQ`), and the precision (also in MHz) of the bisection search (`PRECISION`). You must also specify (an arbitrary number of) SEEDs to use. For instance, to find the best fmax for a PIFO with 2^10 elements and 9-bit priorities using 5 seeds, run: ```ELEMENT_BITS=10 PRIORITY_BITS=9 MIN_FREQ=50 MAX_FREQ=250 pifo/scripts/bisect_fmax.sh 1 2 3 4 5```

The script iteratively synthesizes the design (using the specified set of seeds) at various fmax targets informed by bisection search. The process completes once either: (a) the lower- and upper-bounds of the search are within `PRECISION` MHz of each other, or (b) the script fails to synthesize a design that meets the timing requirements corresponding to `MIN_FREQ`. A summary of the results (best fmax, and the corresponding seed) are written to `${DESIGN}/quartus/bisect_fmax/fmax.txt`.

### (C) Multi-configuration sweep with fmax bisection search

This flow extends [(B)](#b-single-configuration-synthesis-with-fmax-bisection-search) to automatically find the best fmax for _multiple_ design configurations (queue size, number of priority bits, and so on). To use this flow for a given design (say, `DESIGN`), first modify the `for` loops in `${DESIGN}/scripts/sweep_bisect_fmax.sh` to correspond to the design configurations you would like to sweep. Finally, run the following command from this directory: ```[MIN_FREQ=AAA] [MAX_FREQ=BBB] [PRECISION=CCC] [NUM_PROCS=DDD] ./sweep_bisect_fmax.sh ${SEED_1} ${SEED_2} ...```. `MIN_FREQ`, `MAX_FREQ`, and `PRECISION` have the same semantics as described earlier. `NUM_PROCS` is an optional parameter that parallelizes the design-space exploration using the specified number of cores.

The results for each configuration are written to the newly-created `${DESIGN}/quartus/sweep_bisect_fmax` directory. Note that you will need [GNU parallel](https://www.gnu.org/software/parallel/) to use this flow.

</div>
