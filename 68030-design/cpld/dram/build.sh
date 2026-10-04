#!/bin/bash
# Synthesize + fit dram.v for ATF1508AS-7JX84 (PLCC-84), JTAG enabled. Same flow as ../glue/build.sh:
# Yosys (hoglet67/atf15xx_yosys scripts) -> EDIF -> Microchip fit1508.exe (ProChip 5.0.1) under Wine.
set -e
cd "$(dirname "$0")"
ATF=${ATF15XX_YOSYS:-/opt/atf15xx_yosys}
export WINEDEBUG=-all
"$ATF/run_yosys.sh" dram > yosys.log 2>&1
"$ATF/run_fitter.sh" -d ATF1508AS -p PLCC84 -s 7 dram \
    -preassign keep -optimize on -tdi_pullup on -tms_pullup on -pin_keep on -verilog_sim sdf 2>&1 | tee fit_run.log
grep -q "fits" dram.fit || { echo "FIT FAILED"; exit 1; }
grep -q "Pin-Keeper = ON" dram.fit || { echo "PIN KEEPER NOT ON"; exit 1; }
# Yosys-flow trap (see ../glue/README.md): a register that only feeds a TRI enable is deleted -> OE = 0
if grep -Eq "^(DSACK0_n|DSACK1_n)\.OE = 0;" dram.fit; then echo "OE REMOVED BY YOSYS"; exit 1; fi
python3 sim/sta_dram.py dram.vo dram.sdo > timing.txt
python3 pinout.py > /dev/null
python3 sim/sdf2v.py dram.vo dram.sdo > sim/dram_timed.v
# Simulations (sim/tb_dram.v + 60 ns EDO SIMM model): RTL and SDF-timed post-fit netlist, 25 MHz and 33.33 MHz
# CPU (+cpu33), and the timed netlist with 50 % random derating (+derate, 5 seeds).
if command -v iverilog >/dev/null; then
  (cd sim && iverilog -g2012 -o /tmp/tb_dram_rtl.vvp tb_dram.v simm_edo.v ../dram.v &&
   iverilog -g2012 -DPOSTFIT -o /tmp/tb_dram_post.vvp tb_dram.v simm_edo.v dram_timed.v prims_timed.v &&
   vvp -n /tmp/tb_dram_rtl.vvp > sim_rtl.log && vvp -n /tmp/tb_dram_rtl.vvp +cpu33 > sim_rtl_33.log &&
   vvp -n /tmp/tb_dram_post.vvp > sim_postfit.log && vvp -n /tmp/tb_dram_post.vvp +cpu33 > sim_postfit_33.log &&
   for s in 11 22 33 44 55; do vvp -n /tmp/tb_dram_post.vvp +derate +seed=$s; done > sim_postfit_derate.log &&
   for s in 11 22 33 44 55; do vvp -n /tmp/tb_dram_post.vvp +cpu33 +derate +seed=$s; done > sim_postfit_33_derate.log)
  grep -H "^done," sim/sim_*.log
fi
