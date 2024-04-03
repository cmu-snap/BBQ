#!/usr/bin/env bash
#
# Usage: [MIN_FREQ=AAA] [MAX_FREQ=BBB] [PRECISION=CCC]              \
#        [NUM_PROCS=DDD] ./sweep_bisect_fmax.sh [seed1] [seed2] ...
#
PROJECT_NAME="bbq"

CUR_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="${SCRIPT_DIR}/.."

if [ $# -eq 0 ]; then
  echo "Must specify seeds."
  exit 1
fi

# If NUM_PROCS is not defined, use the default.
if [ -z ${NUM_PROCS} ]; then
    NUM_PROCS=8
    echo "NUM_PROCS is not defined, using ${NUM_PROCS}."
fi

# Exit when error occurs.
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command exited with code $?."' EXIT

rm -rf ${PROJECT_DIR}/quartus/sweep_bisect_fmax
mkdir -p ${PROJECT_DIR}/quartus/sweep_bisect_fmax

tmp_dir="/tmp/${PROJECT_NAME}"
rm -rf ${tmp_dir}
cp -r ${PROJECT_DIR} ${tmp_dir}
rm -rf ${tmp_dir}/quartus/sweep_bisect_fmax

jobs="sweep_bisect_fmax_jobs.txt"
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

                dst_dir=${PROJECT_DIR}/quartus/sweep_bisect_fmax/${midfix}
                rm -rf ${dst_dir}
                cp -r ${tmp_dir} ${dst_dir}

                echo "ELEMENT_BITS=${n} BITMAP_WIDTH=${b} NUM_LEVELS=${l}"\
                    "${dst_dir}/scripts/bisect_fmax.sh $@ | tee"\
                    "${dst_dir}/bisect_fmax_log.txt" >> ${jobs}
            else
                break
            fi
        done
    done
done

rm -rf ${tmp_dir}
parallel -j${NUM_PROCS} < ${jobs}
rm -f ${jobs}
