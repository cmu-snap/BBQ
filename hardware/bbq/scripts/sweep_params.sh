#!/usr/bin/env bash
#
# Usage: ./sweep_params.sh [SEED]
#
PROJECT_NAME="bbq"

CUR_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="${SCRIPT_DIR}/.."

SEED=${1:-"0"}

# Exit when error occurs.
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command exited with code $?."' EXIT

rm -rf ${PROJECT_DIR}/quartus/sweep_params
mkdir -p ${PROJECT_DIR}/quartus/sweep_params

tmp_dir="/tmp/${PROJECT_NAME}"
rm -rf ${tmp_dir}
cp -r ${PROJECT_DIR} ${tmp_dir}
rm -rf ${tmp_dir}/quartus/sweep_params

jobs="sweep_params_jobs.txt"
rm -f ${jobs}

max_num_priorities=32768
# Number of element bits
for n in 12 15 17
do
    # Bitmap widths
    for b in 2 4 8 16 32
    do
        # Number of levels
        for l in 3 4 5 6 8 12 15
        do
            num_priorities=$((${b}**${l}))
            if [[ ${num_priorities} -le ${max_num_priorities} ]]
            then
                midfix="l${l}_b${b}_n${n}"

                dst_dir=${PROJECT_DIR}/quartus/sweep_params/${midfix}
                rm -rf ${dst_dir}
                cp -r ${tmp_dir} ${dst_dir}

                echo "ELEMENT_BITS=${n} BITMAP_WIDTH=${b} NUM_LEVELS=${l} \
                    ${dst_dir}/scripts/synthesize.sh ${SEED}" >> ${jobs}
            else
                break
            fi
        done
    done
done

rm -rf ${tmp_dir}
parallel -j4 < ${jobs}
rm -f ${jobs}
