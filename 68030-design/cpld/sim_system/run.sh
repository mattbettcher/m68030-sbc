#!/bin/bash
# Whole-system timed post-fit simulation: glue U3 + DRAM U4 netlists (SDF back-annotated) + SIMM + 68882 + expansion.
# Run ../glue/build.sh and ../dram/build.sh first (they produce glue_timed.v / dram_timed.v).
set -e
cd "$(dirname "$0")"
NCYC=${NCYC:-4000}
iverilog -g2012 -DNCYC=$NCYC -o /tmp/tb_system.vvp tb_system.v ../glue/sim/glue_timed.v ../dram/sim/dram_timed.v \
    ../glue/sim/prims_timed.v ../dram/sim/simm_edo.v
vvp -n /tmp/tb_system.vvp > sim_system.log &
for s in 11 22 33 44 55; do vvp -n /tmp/tb_system.vvp +derate +seed=$s > sim_system_derate_s$s.log & done
wait
grep -H "done," sim_system*.log
