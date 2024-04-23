# Synopsys

## Build Container

If the container is not yet built, run the following command from the `asic` directory:
```bash
docker build -t synopsys .
```

## Using ASAP7 PDK

ASAP7 is a submodule of this repository. To use it, run the following command to initialize the submodule:
```bash
git submodule init asap7sc7p5t_28
```

Then run the following to decompress the libraries and convert them to `.db` so that Synopsys can use them:
```bash
./prepare_asap7.sh
```

The converted libraries will be placed at `asap7_db/`.

## Running Synopsys

By default the script assumes that synopsys is installed at `$HOME/synopsys`. To use a different path, set the `SYNOPSYS_PATH` environment variable. We also assume that `license.dat` is located at the root of the synopsys installation directory.

Run `dc_shell` replacing:

- `<priority_bits>` with the number of bits used for priority
- `<element_bits>` with the number of bits used for elements
- `<clock_period>` with the clock period in ps (e.g., 1000.0 for 1GHz)
- `<design>` with the name of the design you want to synthesize in `{pifo, bbq}`:
```bash
PRIORITY_BITS=<priority_bits> ELEMENT_BITS=<element_bits> CLOCK_PERIOD=<clock_period> ./dc_shell -f <design>.tcl
```
