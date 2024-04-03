#!/usr/bin/env bash
#
# Usage: ELEMENT_BITS=XXX PRIORITY_BITS=YYY \
#        ./synthesize.sh [SEED]
#
PROJECT_NAME="pieo"

CUR_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="${SCRIPT_DIR}/.."

SEED=${1:-"0"}

# If ELEMENT_BITS is not defined, exit.
if [ -z ${ELEMENT_BITS} ]; then
  echo "ELEMENT_BITS is not defined. Exiting."
  exit 1
fi

# If PRIORITY_BITS is not defined, exit.
if [ -z ${PRIORITY_BITS} ]; then
  echo "PRIORITY_BITS is not defined. Exiting."
  exit 1
fi

echo "SEED=${SEED}"

PROJECT_OUTPUT_DIRECTORY="output_files"
QUARTUS_STA_LOG_FILE="quartus_sta.log"

# Exit when error occurs.
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo "\"${last_command}\" command exited with code $?."' EXIT

cd ${PROJECT_DIR}/quartus

start=$(date +%s.%N)
# Generate IPs if necessary.
quartus_ipgenerate ${PROJECT_NAME}

quartus_syn --read_settings_files=on --write_settings_files=off ${PROJECT_NAME} \
  -c ${PROJECT_NAME} --set=VERILOG_MACRO=PRIORITY_BITS=${PRIORITY_BITS}         \
  --set=VERILOG_MACRO=ELEMENT_BITS=${ELEMENT_BITS}

quartus_fit --read_settings_files=on --write_settings_files=off ${PROJECT_NAME} \
  -c ${PROJECT_NAME} --seed=${SEED}

# We use script instead of tee to capture the output and display it while
# preserving colors.
script --flush --quiet --return ${QUARTUS_STA_LOG_FILE}                         \
  --command "quartus_sta ${PROJECT_NAME} -c ${PROJECT_NAME} --mode=finalize"

quartus_asm --read_settings_files=on --write_settings_files=off ${PROJECT_NAME} \
  -c ${PROJECT_NAME}

dur=$(echo "$(date +%s.%N) - ${start}" | bc)
printf "Synthesis completed in %.6f seconds\n" ${dur}

# Show Fmax.
grep -C2 "; Fmax" "${PROJECT_OUTPUT_DIRECTORY}/${PROJECT_NAME}.sta.rpt"

if grep -q "Timing requirements not met" ${QUARTUS_STA_LOG_FILE}; then
  # Show slack.
  grep -C 10 "Timing requirements not met" ${QUARTUS_STA_LOG_FILE}
  RED='\033[0;31m'
  NC='\033[0m' # No Color.
  echo -e "${RED}===========================${NC}"
  echo -e "${RED}Timing requirements not met${NC}"
  echo -e "${RED}===========================${NC}"
fi

echo "Done (P=${PRIORITY_BITS}, log2(N)=${ELEMENT_BITS}, seed=${SEED})"

# Announce that it is over.
tput bel
