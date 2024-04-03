#!/bin/bash
source ../run_common.sh

run_testcase () {
  # Setup
  run_vlib
  run_vlog ../../src/common/bram_simple2port.v
  run_vlog ../../src/common/sc_fifo.v
  run_vlog ../../src/ffs.sv
  run_vlog ../../src/heap_ops.sv
  run_vlog ../../src/bbq.sv
  run_vlog +define+TEST_CASE=\"$1\" tb_bbq.sv

  # Run simulation
  display_testcase_progress $1
  run_vsim tb_bbq
  run_report $1
}

declare -a testcases=(
  'TEST_BASIC_ENQUE'
  'TEST_BASIC_DEQUE_MIN'
  'TEST_BASIC_DEQUE_MAX'
  'TEST_HEAP_PROPERTY'
  'TEST_CAPACITY_LIMITS'
  'TEST_PIPELINING_ENQUE_ENQUE'
  'TEST_PIPELINING_ENQUE_DEQUE'
  'TEST_PIPELINING_DEQUE_DEQUE_MIN'
  'TEST_PIPELINING_DEQUE_DEQUE_MAX'
  # TODO(natre): Mixed pipelining
  'TEST_DEQUE_FIFO'
  'TEST_RESET'
)

max_testcase_name_length ${testcases[@]}
for c in ${testcases[@]}; do
  run_testcase $c
done
