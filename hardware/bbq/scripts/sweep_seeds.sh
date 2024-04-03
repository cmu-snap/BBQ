#!/usr/bin/env bash
#
# Usage: ELEMENT_BITS=XXX BITMAP_WIDTH=YYY NUM_LEVELS=ZZZ \
#        ./sweep_seeds.sh [seed1] [seed2] ...
#
# Launches as many workers as seeds that you specify.
#
PROJECT_NAME="bbq"

CUR_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="${SCRIPT_DIR}/.."

if [ $# -eq 0 ]; then
  echo "Must specify seeds."
  exit 1
fi

SEEDS=$@

# Exit when error occurs.
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command exited with code $?."' EXIT

rm -rf ${PROJECT_DIR}/quartus/sweep_seeds
mkdir -p ${PROJECT_DIR}/quartus/sweep_seeds

tmp_dir="/tmp/${PROJECT_NAME}"
rm -rf ${tmp_dir}
cp -r ${PROJECT_DIR} ${tmp_dir}
rm -rf ${tmp_dir}/quartus/sweep_seeds

for seed in $SEEDS; do
    dst_dir=${PROJECT_DIR}/quartus/sweep_seeds/${seed}
    rm -rf ${dst_dir}
    cp -r ${tmp_dir} ${dst_dir}
done

rm -rf ${tmp_dir}

parallel "${PROJECT_DIR}/quartus/sweep_seeds/{}/scripts/synthesize.sh {}" ::: $SEEDS
