# Whole-system timed simulation (glue U3 + DRAM U4 + SIMM + MC68882 + expansion)

`run.sh` compiles `tb_system.v` with both SDF-back-annotated CPLD netlists (`../glue/sim/glue_timed.v`, `../dram/sim/dram_timed.v`, produced by the two `build.sh` scripts), the shared timed primitives (`../glue/sim/prims_timed.v`) and the 60 ns EDO SIMM model (`../dram/sim/simm_edo.v`). It runs 4000 random bus cycles (`NCYC`) once with nominal SDF delays and five times with 50 % random derating (seeds 11/22/33/44/55): `sim_system.log`, `sim_system_derate_s*.log`.

Bus model: MC68030 at 25 MHz, EC AC table extremes on half of the cycles (AS↑ at #12 max, next AS↓ exactly #15 = 30 ns later). Cycle mix: ROM, DUART, glue registers, IDE (PIO-0), 68882 (FC=7, answers at START + 0..25 ns, #19 has no minimum), expansion card, interrupt acknowledge, unmapped (BERR timeout), and DRAM (long-word/byte reads and writes, reference-checked). U4 is released from reset and the tb waits for its 105 µs init + 16 CBR cycles before DRAM traffic.

Monitors: DSACK/BERR/AVEC contention between all drivers (glue, U4, 68882, expansion); U4 DSACK asserted in a non-DRAM cycle; U4 drive-high/release times after AS↑ and drive still on at the next AS↓; U4 → next driver hand-over gap; DSACK0/1 skew vs EC #31A (the CPU model accepts the second DSACK within #31A, 7 ns); SIMM data vs CPU write data contention; SIMM timing (tRAS/tRP/tRCD/…/refresh gap); 68882 #8/#8B/#9; IDE t0/t1/t2/t4/t9; DRAM wait-state histogram.

Result 2026-09-27 (glue Rev A.1, U4 Rev A.1): **0 errors in all 6 runs**, 0 DSACK contention events, U4 DSACK high ≤ 7.5 ns / Z ≤ 17.5 ns after AS↑, hand-over gap ≥ 21.0 ns, U4 DSACK skew ≤ 0.9 ns, SIMM timing errors 0, refresh gap ≤ 15 235 ns, 0 DRAM data mismatches. With the Rev A U4 netlist in the same bench: 7–22 contention events per run (≤ 15.3 ns) and 33–39 false U4 DSACK assertions per derated run.

The DUART-access check is gated by PWR_RST_n: with random derating the netlist registers start at 0 and the reset preset takes a few ns to act (as in a real ATF15xx at power-up, when the DUART is held in reset anyway).
