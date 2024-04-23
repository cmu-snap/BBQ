
set lib_path "asap7sc7p5t_28/LIB/NLDM/"
set db_dst "asap7_db/"

set libs [glob -directory $lib_path -- "*.lib"]
foreach lib $libs {
   puts "$lib"
   read_lib $lib
#    set lib_name [file rootname [file tail $lib]]
#    set db_name "${db_dst}${lib_name}.db"
#    write_lib -output $db_name -format db $lib_name
}

# Some file names are different than the library names, therefore I manually
# listed them all below. If they fix this in the future this will not longer be
# needed. And the above lines inside the loop can be uncommented.

write_lib asap7sc7p5t_INVBUF_RVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_RVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_AO_SLVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_SLVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_OA_RVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_RVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_SRAM_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_SRAM_TT_nldm_211120.db"
write_lib asap7sc7p5t_AO_SRAM_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_SRAM_SS_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_LVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_LVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_AO_LVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_LVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_LVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_LVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_SRAM_TT_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_SRAM_TT_nldm_220123.db"
write_lib asap7sc7p5t_AO_RVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_RVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_SLVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_SLVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_OA_SLVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_SLVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_RVT_SS_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_RVT_SS_nldm_220123.db"
write_lib asap7sc7p5t_SIMPLE_SLVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_SLVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_LVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_LVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_OA_SLVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_SLVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_OA_LVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_LVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_OA_RVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_RVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_AO_RVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_RVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_SRAM_SS_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_SRAM_SS_nldm_220123.db"
write_lib asap7sc7p5t_OA_SRAM_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_SRAM_SS_nldm_211120.db"
write_lib asap7sc7p5t_AO_SRAM_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_SRAM_FF_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_SLVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_SLVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_LVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_LVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_AO_LVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_LVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_SLVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_SLVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_SLVT_FF_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_SLVT_FF_nldm_220123.db"
write_lib asap7sc7p5t_INVBUF_RVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_RVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_RVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_RVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_SLVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_SLVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_LVT_TT_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_LVT_TT_nldm_220123.db"
write_lib asap7sc7p5t_AO_SLVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_SLVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_SLVT_SS_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_SLVT_SS_nldm_220123.db"
write_lib asap7sc7p5t_SIMPLE_SRAM_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_SRAM_SS_nldm_211120.db"
write_lib asap7sc7p5t_OA_SLVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_SLVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_RVT_TT_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_RVT_TT_nldm_220123.db"
write_lib asap7sc7p5t_INVBUF_LVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_LVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_RVT_FF_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_RVT_FF_nldm_220123.db"
write_lib asap7sc7p5t_OA_SRAM_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_SRAM_TT_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_SLVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_SLVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_SRAM_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_SRAM_FF_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_SRAM_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_SRAM_SS_nldm_211120.db"
write_lib asap7sc7p5t_AO_LVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_LVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_OA_SRAM_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_SRAM_FF_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_SRAM_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_SRAM_FF_nldm_211120.db"
write_lib asap7sc7p5t_SIMPLE_LVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_LVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_OA_LVT_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_LVT_TT_nldm_211120.db"
write_lib asap7sc7p5t_INVBUF_RVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_INVBUF_RVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_AO_SRAM_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_SRAM_TT_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_SRAM_FF_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_SRAM_FF_nldm_220123.db"
write_lib asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_AO_RVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_RVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_AO_SLVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_AO_SLVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_OA_RVT_FF_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_RVT_FF_nldm_211120.db"
write_lib asap7sc7p5t_OA_LVT_SS_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_OA_LVT_SS_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_SLVT_TT_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_SLVT_TT_nldm_220123.db"
write_lib asap7sc7p5t_SEQ_LVT_FF_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_LVT_FF_nldm_220123.db"
write_lib asap7sc7p5t_SIMPLE_SRAM_TT_nldm_211120 -format db -output "${db_dst}asap7sc7p5t_SIMPLE_SRAM_TT_nldm_211120.db"
write_lib asap7sc7p5t_SEQ_LVT_SS_nldm_220123 -format db -output "${db_dst}asap7sc7p5t_SEQ_LVT_SS_nldm_220123.db"

quit
