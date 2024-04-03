#!/usr/bin/env bash
#
# Usage: ./setup.sh FREQ_MHZ
#
# Generates the required IPs for the project. FREQ_MHZ is the frequency of the
# PLL in MHz. It must be an integer.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ $# -eq 0 ]; then
  echo "Must specify frequency in MHz."
  exit 1
fi

FREQ=$1

# Check if FREQ is an integer.
if ! [[ $FREQ =~ ^[0-9]+$ ]]; then
  echo "Frequency must be an integer."
  exit 1
fi

cd $SCRIPT_DIR/ip
rm -rf my_pll
rm -f my_pll.tcl
sed "s/{{{out_freq}}}/${FREQ}.0/g" my_pll.tcl.template > my_pll.tcl
qsys-script --script=my_pll.tcl --quartus-project=../quartus/bbq.qsf
