set DESIGN_TOPLEVEL "bbq"
set BITMAP_WIDTH $env(BITMAP_WIDTH)
set NUM_LEVELS $env(NUM_LEVELS)
set ELEMENT_BITS $env(ELEMENT_BITS)

# Using 1 GHz clock (period in ps).
# set clock_period    1000.0

# Using 3.1 GHz clock (period in ps).
# set clock_period    320.0

set clock_period $env(CLOCK_PERIOD)

set REPORT_DIR "report3/bbq_no_sram_${ELEMENT_BITS}_${NUM_LEVELS}_${BITMAP_WIDTH}_7nm_${clock_period}"
exec mkdir -p $REPORT_DIR

set VCS_OPTS "+define+BITMAP_WIDTH=${BITMAP_WIDTH} +define+ELEMENT_BITS=${ELEMENT_BITS}"

set SRC_FILES [list \
    /src/evaluation/asic/common/sc_fifo_controller.sv \
    /src/hardware/bbq/src/heap_ops.sv \
    /src/hardware/bbq/src/ffs.sv \
    /src/hardware/bbq/src/bbq_no_sram_${NUM_LEVELS}.sv \
]

source asap_synth.tcl

quit
