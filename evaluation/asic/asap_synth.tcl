
# TODO(sadok): Remove duplicated code with the other synthesis scripts.

# 16 seems to be the maximum allowed.
set_host_options -max_cores 16

set SynopsysInstall [getenv "STROOT"]
set SAED14 [getenv "SAED14"]
set SAED14_SRAM [getenv "SAED14_SRAM"]

set search_path [list \
    "." \
    [format "%s%s" $SynopsysInstall /libraries/syn] \
    [format "%s%s" $SynopsysInstall /dw/sim_ver] \
    [format "%s%s" $SynopsysInstall /dw] \
]

set lib_path "asap7_db"
set std_cell_lib [glob -directory $lib_path -- "*.db"]

set std_sram_cell_lib [list \
]

set synthetic_library "dw_foundation.sldb"
set target_library [concat $std_sram_cell_lib $std_cell_lib]
set link_library [concat $target_library [list $synthetic_library]]
set symbol_library [list generic.sdb]

set hdlin_sverilog_std 2009
set hdlin_ff_always_async_set_reset true
set hdlin_ff_always_sync_set_reset true
set hdlin_auto_save_templates true
set verilogout_show_unconnected_pins true
set compile_fix_multiple_port_ets true
set fsm_auto_inferring true
set fsm_enable_state_minimization true
set fsm_export_formality_state_info true
set synlib_wait_for_design_license "DesignWare"

analyze -format sverilog $SRC_FILES -vcs $VCS_OPTS
elaborate $DESIGN_TOPLEVEL
check_design

source synth.sdc

link

# compile -map_effort low
compile_ultra

report_timing -loops

write -format verilog -hierarchy -output \
    [format "%s/%s.gate.v.rpt" ${REPORT_DIR} ${DESIGN_TOPLEVEL}]

write_sdf [format "%s/%s.gate.sdf.rpt" ${REPORT_DIR} ${DESIGN_TOPLEVEL}]  
write_sdc [format "%s/%s.gate.sdc.rpt" ${REPORT_DIR} ${DESIGN_TOPLEVEL}]

report_timing > [format "%s/%s.timing.rpt" ${REPORT_DIR} ${DESIGN_TOPLEVEL}]
report_area -hierarchy > \
    [format "%s/%s.area.rpt" ${REPORT_DIR} ${DESIGN_TOPLEVEL}]
report_power > [format "%s/%s.power.rpt" ${REPORT_DIR} ${DESIGN_TOPLEVEL}]
