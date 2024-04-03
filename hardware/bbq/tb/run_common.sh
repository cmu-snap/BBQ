RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

run_vlib () {
  rm -rf work
  rm -f vsim.wlf

  if [[ -n ${DEBUG} ]]; then
    vlib work
  else
    vlib work > /dev/null 2>&1
  fi
}

run_vlog () {
  if [[ -n ${DEBUG} ]]; then
    vlog +define+SIM +define+DEBUG "$@" -sv
  else
    vlog +define+SIM "$@" -sv > /dev/null 2>&1
  fi
}

run_vsim () {
  if [[ -n ${DEBUG} ]]; then
    OUTPUT=$(vsim -L altera_ver -L lpm_ver -L sgate_ver     \
             -L altera_mf_ver -L altera_lnsim_ver           \
             -c -do "run -all" $1)
  else
    OUTPUT=$(vsim -L altera_ver -L lpm_ver -L sgate_ver     \
             -L altera_mf_ver -L altera_lnsim_ver           \
             -c -do "run -all" $1 | grep -e "PASS" -e "FAIL")
  fi
}

run_report () {
  if grep -q "FAIL" <<< ${OUTPUT}
  then
    printf "${RED}${OUTPUT}${NC}\n"
  elif grep -q "PASS $1" <<< ${OUTPUT}
  then
    if [[ -n ${DEBUG} ]]; then
      printf "${GREEN}${OUTPUT}${NC}\n"
    else
      printf "${GREEN}PASS${NC}\n"
    fi
  else
    printf "${RED}Test not run\n${OUTPUT}${NC}\n"
  fi
}

max_testcase_name_length() {
  MAX_LENGTH=0
  local array=("$@")
  for testcase in ${array[@]}; do
    if ((${#testcase} > ${MAX_LENGTH}));
    then
      MAX_LENGTH=${#testcase}
    fi
  done
}

display_testcase_progress() {
  local testcase=$1
  local testcase_name_length=${#testcase}

  printf "Running ${testcase}... "
  padding=$((MAX_LENGTH - testcase_name_length))
  printf '%*s' ${padding} ""
}
