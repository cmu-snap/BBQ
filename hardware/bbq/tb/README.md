<div align="justify">

## BBQ Testbench

This simulation testbench contains two test suites: one for the `bbq` module, and another for the `ffs` (Find-First Set) module. To run them, first ensure that the `src` directory contains a `bbq.sv` source file (as described [here](../README.md#generating-bbqs-source-code)). Also ensure that `modelsim_ase/linux` and `modelsim_ase/linuxaloem` (or equivalent) are on your PATH. Finally, from this directory, run the following snippet:
```
for i in ffs bbq; do
  echo "Starting testbench for ${i}"
  cd ${i}; ./run_test.sh; cd ..;
  echo ""
done
```

</div>
