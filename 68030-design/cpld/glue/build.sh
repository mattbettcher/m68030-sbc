#!/bin/bash
# Synthesize + fit glue.v for ATF1508AS-7JX84 (PLCC-84), JTAG enabled.
# Flow: Yosys (hoglet67/atf15xx_yosys scripts) -> EDIF -> Microchip/Atmel fit1508.exe under Wine.
# Needs: yosys, wine (32-bit), and a checkout of https://github.com/hoglet67/atf15xx_yosys with
# fit1508.exe/aprim.lib/atmel.std copied into its vendor/ dir from ProChip 5.0.1 (see README.md).
set -e
cd "$(dirname "$0")"
ATF=${ATF15XX_YOSYS:-/opt/atf15xx_yosys}
export WINEDEBUG=-all
"$ATF/run_yosys.sh" glue > yosys.log 2>&1
# -optimize off: with the fitter's logic optimiser ON every attempt ends in "Grouping/Placement
# fail" (fan-in); OFF, the Yosys-mapped nodes are placed as-is and the design fits.
# (-xor_synthesis on gives 107 MC but the report then shows LAB G at "17/16 (106%)", which is
# not credible, so the plain option set is used: Rev A 111 MC, Rev A.1 121 MC, every LAB <= 100%.)
# -preassign keep: honour the //PIN: locks in glue.v (they are the schematic pinout).
# -pin_keep on: pin keepers on unused/reserved pins (Rev A.1; the Rev A fit ran with Pin-Keeper = OFF).
"$ATF/run_fitter.sh" -d ATF1508AS -p PLCC84 -s 7 glue \
    -preassign keep -optimize off -tdi_pullup on -tms_pullup on -pin_keep on -verilog_sim sdf 2>&1 | tee fit_run.log
grep -q "fits" glue.fit || { echo "FIT FAILED"; exit 1; }
grep -q "Pin-Keeper = ON" glue.fit || { echo "PIN KEEPER NOT ON"; exit 1; }
# Yosys-flow trap: a net that only feeds a TRI enable is deleted (see glue.v); make sure no enable is constant 0
if grep -Eq "^(DSACK0_n|DSACK1_n|AVEC_n|BERR_n)\.OE = 0;" glue.fit; then echo "OE REMOVED BY YOSYS"; exit 1; fi
# Static timing from the fitter's SDF timing model (see sim/sta_glue.py)
python3 sim/sta_glue.py glue.vo glue.sdo > timing.txt
# Simulations: RTL and zero-delay post-fit netlist with the functional testbench; timed post-fit netlist
# (SDF back-annotated, transport delays, setup/hold checks) with the worst-case 68030 bus model.
if command -v iverilog >/dev/null; then
  (cd sim && iverilog -g2005 -o /tmp/tb_rtl.vvp tb_glue.v ../glue.v cells_rtl.v && vvp -n /tmp/tb_rtl.vvp > sim_rtl.log ;
   iverilog -g2005 -DPOSTFIT -o /tmp/tb_post.vvp tb_glue.v ../glue.vo prims.v && vvp -n /tmp/tb_post.vvp 2>/dev/null | grep -v "SDF" > sim_postfit.log ;
   python3 sdf2v.py ../glue.vo ../glue.sdo > glue_timed.v &&
   iverilog -g2012 -DNCYC=4000 -o /tmp/tb_timed.vvp tb_timed.v glue_timed.v prims_timed.v &&
   vvp -n /tmp/tb_timed.vvp > sim_timed.log &&
   vvp -n /tmp/tb_timed.vvp +derate +seed=22 > sim_timed_derate.log)
  grep -h "done," sim/sim_rtl.log sim/sim_postfit.log sim/sim_timed.log sim/sim_timed_derate.log
fi
