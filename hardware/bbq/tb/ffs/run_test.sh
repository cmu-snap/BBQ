#!/bin/bash
source ../run_common.sh

run_testcase () {
  # Setup
  run_vlib
  run_vlog ../../src/ffs.sv
  run_vlog +define+TEST_CASE=\"$1\" tb_ffs.sv

  # Run simulation
  display_testcase_progress $1
  run_vsim tb_ffs
  run_report $1
}

declare -a testcases=(
  'TEST_ZERO'
  'TEST_LSB_SET'
  'TEST_MSB_SET'
  'TEST_ALL_SET'
  'TEST_RANDOM_BITMAP'
)

max_testcase_name_length ${testcases[@]}
for c in ${testcases[@]}; do
  run_testcase $c
done
