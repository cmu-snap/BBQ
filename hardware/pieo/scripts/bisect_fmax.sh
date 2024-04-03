#!/usr/bin/env bash
#
# Usage: ELEMENT_BITS=XXX PRIORITY_BITS=YYY             \
#        [MIN_FREQ=AAA] [MAX_FREQ=BBB] [PRECISION=CCC]  \
#        ./bisect_fmax.sh [seed1] [seed2] ...
#
# Given a design configuration, performs a bisection search to
# find the target Fmax that closes timing. Tries as many seeds
# as specified, using a single process for synthesis.
#
PROJECT_NAME="pieo"

CUR_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="${SCRIPT_DIR}/.."

if [ $# -eq 0 ]; then
  echo "Must specify seeds."
  exit 1
fi

SEEDS=$@

# If MIN_FREQ is not defined, use the default.
if [ -z ${MIN_FREQ} ]; then
    MIN_FREQ=50
    echo "MIN_FREQ is not defined, using ${MIN_FREQ} MHz."
fi

# If MAX_FREQ is not defined, use the default.
if [ -z ${MAX_FREQ} ]; then
    MAX_FREQ=400
    echo "MAX_FREQ is not defined, using ${MAX_FREQ} MHz."
fi

# If PRECISION is not defined, use the default.
if [ -z ${PRECISION} ]; then
    PRECISION=3
    echo "PRECISION is not defined, using ${PRECISION} MHz."

elif [ ${PRECISION} -lt 1 ]; then
    echo "PRECISION must be greater than 0."
    exit 1
fi

# Outputs
best_fmax=0
best_seed=-1
output_dir="${PROJECT_DIR}/quartus/bisect_fmax"

# Report files
timing_report="${PROJECT_DIR}/quartus/output_files/${PROJECT_NAME}.sta.rpt"
fitter_report="${PROJECT_DIR}/quartus/output_files/${PROJECT_NAME}.fit.summary"

# Setup
rm -rf ${output_dir}
rm -f ${timing_report}
rm -f ${fitter_report}
mkdir -p ${output_dir}

# Housekeeping
fmax_lower=0
fmax_upper=${MAX_FREQ}
current_freq=$(( ${MAX_FREQ} / 2 ))

while true
do
    # Setup for the next iteration
    rm -rf ${PROJECT_DIR}/quartus/output_files

    # Print start message and run the setup script for the current fmax
    echo "Attempting synthesis with target fmax ${current_freq} MHz"
    ${PROJECT_DIR}/setup.sh ${current_freq}
    if [ $? -ne 0 ]; then
        echo "Setup script failed for ${current_freq} MHz, exiting."
        exit 1
    fi

    timing_success=0
    for seed in ${SEEDS[@]}; do

        # First, run synthesis for this seed (8-hour timeout)
        timeout -k 60 8h ${SCRIPT_DIR}/synthesize.sh ${seed}
        retcode=$?
        if [ ${retcode} -eq 124 ]; then
            echo "Synthesis script timed out for ${current_freq} MHz and seed ${seed}, skipping."
            continue
        elif [ ${retcode} -ne 0 ]; then
            echo "Synthesis script failed for ${current_freq} MHz and seed ${seed}, skipping."
            continue
        fi
        # If the timing report is clear, declare success
        if [ -f "${timing_report}" ]; then
            timing_success=1
            if grep -qcm1 "Timing requirements not met" ${timing_report}; then
                timing_success=0;
            fi
        fi
        # Found a seed that works, stop early
        if [ ${timing_success} -eq 1 ]; then
            best_fmax=${current_freq}
            best_seed=${seed}

            # Copy the reports to the output directory
            cp ${timing_report} ${output_dir}/
            cp ${fitter_report} ${output_dir}/
            break
        fi
    done

    if [ ${timing_success} -eq 1 ]; then
        # Found a new lower bound
        fmax_lower=${current_freq}
    else
        # Synthesis failed, found a new upper bound
        fmax_upper=${current_freq}
    fi
    # Update frequency estimate
    current_freq=$(( (${fmax_lower} + ${fmax_upper}) / 2 ))

    if (( ${current_freq} < ${MIN_FREQ} )); then
        echo "Warning: bisect_fmax reached MIN_FREQ, design may not be synthesizable."
        break

    elif (( ${fmax_upper} - ${fmax_lower} <= ${PRECISION} )); then
        break # Found the frequency
    fi
done

if [ ${best_fmax} -ne 0 ]; then
    echo "Best fmax: ${best_fmax}, seed: ${best_seed}" | tee ${output_dir}/fmax.txt
fi

# Announce that it is over.
tput bel
