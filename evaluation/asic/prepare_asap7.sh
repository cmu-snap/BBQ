#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $SCRIPT_DIR

ASAP7_LIB_PATH="$SCRIPT_DIR/asap7sc7p5t_28/LIB/NLDM/"

# Uncompress all the libs with extension .lib.7z if they are not already
# uncompressed.
cd $ASAP7_LIB_PATH
for file in *.lib.7z; do
    if [ ! -f "${file%.7z}" ]; then
        7z x $file
    fi
done
cd -


./lc_shell -f convert_asap7.tcl
