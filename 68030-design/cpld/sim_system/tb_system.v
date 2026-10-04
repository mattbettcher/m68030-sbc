// WHOLE-SYSTEM timed post-fit simulation (2026-09-27): glue CPLD U3 (glue_timed.v, Rev A.1) + DRAM CPLD U4
// (dram_timed.v, Rev A.1) + 60 ns EDO SIMM model (../dram/sim/simm_edo.v) + MC68882 model + expansion-card model,
// all on the same DSACK/BERR/AVEC nets.  Both netlists are the fitter's gate models back-annotated from their SDF
// files by sdf2v.py; primitives from ../glue/sim/prims_timed.v (TRANSPORT delays, +derate/+dmin/+seed, DFF checks).
// Derived from ../glue/sim/tb_timed.v (which uses a behavioural U4); this version replaces that with the U4 netlist.
// Bus model: MC68030 asynchronous bus at 25 MHz with the EC timing extremes (MC68030EC, 25 MHz column):
//   #9  CLK low -> AS/DS asserted 3..18      #12 CLK low -> AS/DS negated 0..18    #15 AS negated width >= 30
//   #11 address/FC valid -> AS asserted >= 7 #13 AS negated -> address invalid >= 7
//   #9B AS -> DS asserted (write) >= 27      #47A async input (DSACK/BERR/AVEC) setup 2 ns before the falling edge
//   #23 clock high -> data-out valid <= 20   #25 AS negated -> data-out invalid >= 7   #27 data-in setup 2
// About half of the cycles use the worst case for glitches and missed gaps: address changes exactly 7 ns before AS
// falls, AS rises 18 ns after the falling edge and falls again 30 ns later.
// MC68882: START = CS.AS.(R/W + DS) [FPU UM 12.6 note 8]; DSACK after 0..25 ns (#19, no minimum given), negated
// within 30 ns and three-stated within 40 ns of START false (#21/#22), random inside those limits.
// DRAM data integrity: every DRAM read is compared with a reference memory (long words and single bytes).
`timescale 1ns/1ps
`define IDEW 13
module tb;
integer n_setup = 0, n_hold = 0;          // incremented by prims_timed.v DFFEARS
integer sd = 1;                            // RNG seed (+seed=<n>) for the bus model and +derate
initial if ($value$plusargs("seed=%d", sd)) $display("seed %0d", sd);
`define RND ($unsigned($random(sd)))
reg CLK = 0, PWR_RST_n = 0, AS_n = 1, DS_n = 1, R_W = 1, STATUS_n = 1;
reg [2:0] FC = 3'b101; reg [31:0] A = 0; reg [1:0] SIZ = 2'b00;
tri [31:0] D; reg [31:0] cpu_dout = 0; reg cpu_den = 0; assign D = cpu_den ? cpu_dout : 32'hzzzz_zzzz;
reg DUART_INT_n = 1, NIC_INT_n = 1, EXP_INT_n = 1, IDE_INTRQ = 0, IDE_IORDY = 1, NMI_BTN_n = 1, WARM_RST_BTN_n = 1;
wire g_DSACK0, g_DSACK1, g_BERR, g_AVEC;
wire DSACK0_n, DSACK1_n, BERR_n, AVEC_n, RESET_n, HALT_n;
pullup(DSACK0_n); pullup(DSACK1_n); pullup(BERR_n); pullup(AVEC_n); pullup(RESET_n); pullup(HALT_n);
assign DSACK0_n = g_DSACK0; assign DSACK1_n = g_DSACK1; assign BERR_n = g_BERR; assign AVEC_n = g_AVEC;
wire CIIN_n, IPL2_n, IPL1_n, IPL0_n, DRAM_SEL_n, FPU_CS_n, ROM_CE_n, BUS_RD_n, BUS_WR_n, DUART_CS_n,
     IDE_CS0_n, IDE_CS1_n, IDE_DIOR_n, IDE_DIOW_n, IDE_BUF_EN_n, EXP_SEL_n, EXP_BUF_EN_n,
     PERIPH_RST_n, DUART_RST, LED_n, HALT_LED_n, IDE_DA0, IDE_DA1, IDE_DA2;
glue dut(.CLK(CLK), .PWR_RST_n(PWR_RST_n), .AS_n(AS_n), .DS_n(DS_n), .FC2(FC[2]), .FC1(FC[1]), .FC0(FC[0]),
 .R_W(R_W), .A31(A[31]), .A30(A[30]), .A29(A[29]), .A28(A[28]), .A27(A[27]), .A19(A[19]), .A18(A[18]),
 .A17(A[17]), .A16(A[16]), .A15(A[15]), .A14(A[14]), .A13(A[13]), .A3(A[3]), .A2(A[2]), .A1(A[1]),
 .STATUS_n(STATUS_n), .DSACK0_n(g_DSACK0), .DSACK1_n(g_DSACK1), .BERR_n(g_BERR), .AVEC_n(g_AVEC),
 .CIIN_n(CIIN_n), .IPL2_n(IPL2_n), .IPL1_n(IPL1_n), .IPL0_n(IPL0_n), .RESET_n(RESET_n), .HALT_n(HALT_n),
 .DRAM_SEL_n(DRAM_SEL_n), .FPU_CS_n(FPU_CS_n), .ROM_CE_n(ROM_CE_n), .BUS_RD_n(BUS_RD_n), .BUS_WR_n(BUS_WR_n),
 .DUART_CS_n(DUART_CS_n), .IDE_CS0_n(IDE_CS0_n), .IDE_CS1_n(IDE_CS1_n), .IDE_DIOR_n(IDE_DIOR_n),
 .IDE_DIOW_n(IDE_DIOW_n), .IDE_BUF_EN_n(IDE_BUF_EN_n), .EXP_SEL_n(EXP_SEL_n), .EXP_BUF_EN_n(EXP_BUF_EN_n),
 .DUART_INT_n(DUART_INT_n), .NIC_INT_n(NIC_INT_n), .EXP_INT_n(EXP_INT_n), .IDE_INTRQ(IDE_INTRQ),
 .IDE_IORDY(IDE_IORDY), .NMI_BTN_n(NMI_BTN_n), .WARM_RST_BTN_n(WARM_RST_BTN_n), .PERIPH_RST_n(PERIPH_RST_n),
 .DUART_RST(DUART_RST), .LED_n(LED_n), .HALT_LED_n(HALT_LED_n)
 , .IDE_DA0(IDE_DA0), .IDE_DA1(IDE_DA1), .IDE_DA2(IDE_DA2)
 );
// ------------------------------------------------------------------ U4 DRAM CPLD netlist + SIMM
reg DCLK = 0; real TDRAM = 20.0 * (1.0 + 1.0/997.0);   // 50 MHz, slightly off so the phase to the CPU clock sweeps
initial begin #7.3; forever #(TDRAM/2) DCLK = ~DCLK; end
wire #(1.0) SEL_U4 = DRAM_SEL_n;                     // board
wire [11:0] MAd; wire [3:0] RASd, CASd; wire WEd, MUXd, u_DSACK0, u_DSACK1;
dram u4(.DRAM_CLK(DCLK), .PWR_RST_n(PWR_RST_n), .AS_n(AS_n), .DRAM_SEL_n(SEL_U4), .R_W(R_W), .SIZ0(SIZ[0]), .SIZ1(SIZ[1]),
 .A0(A[0]), .A1(A[1]), .A2(A[2]), .A3(A[3]), .A4(A[4]), .A5(A[5]), .A6(A[6]), .A7(A[7]), .A8(A[8]), .A9(A[9]),
 .A10(A[10]), .A11(A[11]), .A12(A[12]), .A13(A[13]), .A14(A[14]), .A15(A[15]), .A16(A[16]), .A17(A[17]),
 .A18(A[18]), .A19(A[19]), .A20(A[20]), .A21(A[21]), .A22(A[22]), .A23(A[23]), .A24(A[24]), .A25(A[25]), .A26(A[26]),
 .MA0(MAd[0]), .MA1(MAd[1]), .MA2(MAd[2]), .MA3(MAd[3]), .MA4(MAd[4]), .MA5(MAd[5]), .MA6(MAd[6]), .MA7(MAd[7]),
 .MA8(MAd[8]), .MA9(MAd[9]), .MA10(MAd[10]), .MA11(MAd[11]),
 .RAS0_n(RASd[0]), .RAS1_n(RASd[1]), .RAS2_n(RASd[2]), .RAS3_n(RASd[3]),
 .CAS0_n(CASd[0]), .CAS1_n(CASd[1]), .CAS2_n(CASd[2]), .CAS3_n(CASd[3]),
 .WE_n(WEd), .MUX_SEL(MUXd), .DSACK0_n(u_DSACK0), .DSACK1_n(u_DSACK1));
assign DSACK0_n = u_DSACK0; assign DSACK1_n = u_DSACK1;
reg pwr_ok = 0; initial #50 pwr_ok = 1;             // SIMM inputs held high for the first 50 ns (power-up artefact)
real TBRD = 3.0;                                     // series R + SIMM load [EST], as in ../dram/sim/tb_dram.v
wire [11:0] MAs; wire [3:0] RASs, CASs; wire WEs;
assign #(TBRD) MAs = MAd;
assign #(TBRD) RASs = pwr_ok ? RASd : 4'hf; assign #(TBRD) CASs = pwr_ok ? CASd : 4'hf; assign #(TBRD) WEs = pwr_ok ? WEd : 1'b1;
simm_edo simm(.MA(MAs), .RAS0_n(RASs[0]), .RAS1_n(RASs[1]), .RAS2_n(RASs[2]), .RAS3_n(RASs[3]),
              .CAS0_n(CASs[0]), .CAS1_n(CASs[1]), .CAS2_n(CASs[2]), .CAS3_n(CASs[3]), .WE_n(WEs), .DQ(D));
real dmin = 0.5; integer dpct; initial if ($value$plusargs("dmin=%d", dpct)) dmin = dpct / 100.0;
always #20 CLK = ~CLK;                    // 25 MHz

localparam K_ROM=1, K_DUART=2, K_REG=3, K_IDE0=4, K_IDE1=5, K_IACK=6, K_BERR=7, K_DRAM=8, K_FPU=9, K_EXP=10;
integer kind = 0, errors = 0, ncyc = 0;
realtime t_as_f = -1e9, t_as_r = -1e9;
integer maxerr = 40; initial if ($value$plusargs("maxerr=%d", maxerr)) ;
task err(input [8*72-1:0] msg); begin errors = errors + 1; if (errors <= maxerr) $display("%t ERR %0s", $realtime, msg); end endtask

// ------------------------------------------------------------------ other DSACK drivers
reg [1:0] f_st = 2, e_st = 2;   // 0 = drive low, 1 = drive high, 2 = three-state
wire f_d = (f_st == 0) ? 1'b0 : (f_st == 1) ? 1'b1 : 1'bz;
wire e_d = (e_st == 0) ? 1'b0 : (e_st == 1) ? 1'b1 : 1'bz;
assign DSACK0_n = f_d; assign DSACK1_n = f_d;
assign DSACK0_n = e_d; assign DSACK1_n = e_d;
// MC68882
wire fpu_start = ~FPU_CS_n & ~AS_n & (R_W | ~DS_n);
integer fseq = 0; real fd;
always @(posedge fpu_start) begin : fpu
  integer my; fseq = fseq + 1; my = fseq;
  if (kind != K_FPU) err("MC68882 START (CS.AS) in a non-FPU cycle");
  fd = (`RND % 2501) / 100.0; #(fd);            // #19: 0..25 ns
  if (fpu_start && my == fseq) f_st = 0;
end
always @(negedge fpu_start) if (f_st == 0) begin : fpu_end
  fd = 3 + (`RND % 2701) / 100.0; #(fd); f_st = 1;   // #21 negated <= 30
  fd = (`RND % 1001) / 100.0; #(fd); if (f_st == 1) f_st = 2;   // #22 Z <= 40
end
// expansion card
wire exp_start = ~EXP_SEL_n & ~AS_n;
integer eseq = 0;
always @(posedge exp_start) begin : expc
  integer my; eseq = eseq + 1; my = eseq;
  if (kind != K_EXP) err("EXP_SEL_n asserted in a non-expansion cycle");
  #100; if (exp_start && my == eseq) e_st = 0;
end
always @(negedge exp_start) if (e_st == 0) begin e_st = 1; #15 if (e_st == 1) e_st = 2; end

// ------------------------------------------------------------------ monitors
// wrong-cycle select assertions (falling edges)
integer runt_harmless = 0; realtime rs_t [0:15]; real runt_min_w = 1e9;
`define SELMON(sig, cond, name, fatal) \
  always @(negedge sig) if ($realtime > 1000 && !(cond)) begin \
    if (fatal) err({name, " asserted in a wrong cycle (runt/stale select)"}); else runt_harmless = runt_harmless + 1; end
`SELMON(FPU_CS_n,     kind == K_FPU, "FPU_CS_n", 1)
`SELMON(EXP_SEL_n,    kind == K_EXP, "EXP_SEL_n", 1)
`SELMON(EXP_BUF_EN_n, kind == K_EXP, "EXP_BUF_EN_n", 1)
`SELMON(IDE_CS0_n,    kind == K_IDE0, "IDE_CS0_n", 1)
`SELMON(IDE_CS1_n,    kind == K_IDE1, "IDE_CS1_n", 1)
`SELMON(IDE_BUF_EN_n, kind == K_IDE0 || kind == K_IDE1, "IDE_BUF_EN_n", 1)
`SELMON(IDE_DIOR_n,   kind == K_IDE0 || kind == K_IDE1, "IDE_DIOR_n", 1)
`SELMON(IDE_DIOW_n,   kind == K_IDE0 || kind == K_IDE1, "IDE_DIOW_n", 1)
`SELMON(BUS_RD_n,     kind == K_ROM || kind == K_DUART, "BUS_RD_n", 1)
`SELMON(BUS_WR_n,     kind == K_ROM || kind == K_DUART, "BUS_WR_n", 1)
`SELMON(ROM_CE_n,     kind == K_ROM, "ROM_CE_n", 0)
`SELMON(DUART_CS_n,   kind == K_DUART, "DUART_CS_n", 0)
`SELMON(DRAM_SEL_n,   kind == K_DRAM, "DRAM_SEL_n", 0)
// a DUART or flash access = chip select AND strobe, in a cycle for another device
wire duart_acc = ~DUART_CS_n & (~BUS_RD_n | ~BUS_WR_n);
wire flash_acc = ~ROM_CE_n & (~BUS_RD_n | ~BUS_WR_n);
always @(posedge duart_acc) if (kind != K_DUART && PWR_RST_n) err("DUART access (CS + RD/WR) in a non-DUART cycle");
always @(posedge flash_acc) if (kind != K_ROM) err("flash access (CE + RD/WR) in a non-ROM cycle");
// (the DUART check is gated by PWR_RST_n: with random derating the netlist registers start at 0 and the reset preset
// takes a few ns to act, as on a real ATF15xx at power-up; the DUART itself is held in reset then)
// U4 DSACK0/DSACK1 assertion skew vs EC #31A (max 7 ns at 25 MHz, 5 ns at 33 MHz)
real T31A = 7.0; realtime tu0, tu1; real skew_max = 0; integer nskew = 0;
always @(negedge AS_n) begin tu0 = 0; tu1 = 0; end
always @(u_DSACK0) if (u_DSACK0 === 1'b0 && !AS_n) begin tu0 = $realtime; if (tu1 > 0) begin nskew = nskew + 1; if (tu0 - tu1 > skew_max) skew_max = tu0 - tu1;
  if (tu0 - tu1 > T31A) err("U4 DSACK0/1 skew > #31A"); end end
always @(u_DSACK1) if (u_DSACK1 === 1'b0 && !AS_n) begin tu1 = $realtime; if (tu0 > 0) begin nskew = nskew + 1; if (tu1 - tu0 > skew_max) skew_max = tu1 - tu0;
  if (tu1 - tu0 > T31A) err("U4 DSACK0/1 skew > #31A"); end end
// false early termination (carried-over state): terminations within 45 ns of AS falling
always @(negedge g_DSACK0 or negedge g_DSACK1 or negedge g_BERR or negedge g_AVEC)
  if (!AS_n && $realtime - t_as_f < 45 && $realtime > 1000) err("glue termination < 45 ns after AS fell (carried-over cycle state)");
// DSACK contention (two drivers fighting = x on the net) and glue release time after AS rises
realtime tx0 = 0, tx1 = 0, cont_max = 0; integer ncont = 0;
always @(DSACK0_n) if (DSACK0_n === 1'bx) begin tx0 = $realtime;
  if (ncont < 6) $display("%t DSACK0 contention: glue %b U4 %b FPU %0d EXP %0d, kind %0d, %0.2f ns after AS fell / %0.2f after previous AS rose",
                          $realtime, g_DSACK0, u_DSACK0, f_st, e_st, kind, $realtime - t_as_f, $realtime - t_as_r); end else if (tx0 > 0) begin
  ncont = ncont + 1; if ($realtime - tx0 > cont_max) cont_max = $realtime - tx0; tx0 = 0; end
always @(DSACK1_n) if (DSACK1_n === 1'bx) tx1 = $realtime; else if (tx1 > 0) begin
  ncont = ncont + 1; if ($realtime - tx1 > cont_max) cont_max = $realtime - tx1; tx1 = 0; end
realtime rel_max = 0;
always @(g_DSACK0 or g_DSACK1 or g_BERR or g_AVEC)
  if (AS_n && g_DSACK0 === 1'bz && g_DSACK1 === 1'bz && g_BERR === 1'bz && g_AVEC === 1'bz && $realtime - t_as_r < 200)
    if ($realtime - t_as_r > rel_max) rel_max = $realtime - t_as_r;
// U4: DSACK asserted only in DRAM cycles; release after AS rises; still driving when the next AS falls;
// hand-over gap from U4 releasing DSACK to the next DSACK driver turning on (68882, glue, expansion card)
always @(u_DSACK0 or u_DSACK1) if ((u_DSACK0 === 1'b0 || u_DSACK1 === 1'b0) && kind != K_DRAM && $realtime > 1000) err("U4 DSACK asserted in a non-DRAM cycle");
realtime u_rel_max = 0, u_hi_max = 0, t_u4z = -1e9, u_gap_min = 1e9, u_hold_max = 0; integer u_hold_n = 0;
always @(u_DSACK0 or u_DSACK1) begin
  if (u_DSACK0 === 1'bz && u_DSACK1 === 1'bz) begin t_u4z = $realtime;
    if (AS_n && $realtime - t_as_r < 200 && $realtime - t_as_r > u_rel_max) u_rel_max = $realtime - t_as_r;
    if (!AS_n && $realtime - t_as_f < 200) begin u_hold_n = u_hold_n + 1; if ($realtime - t_as_f > u_hold_max) u_hold_max = $realtime - t_as_f; end end
  if (u_DSACK1 === 1'b1 && AS_n && $realtime - t_as_r < 200 && $realtime - t_as_r > u_hi_max) u_hi_max = $realtime - t_as_r;
end
task other_on; begin
  if (u_DSACK0 !== 1'bz || u_DSACK1 !== 1'bz) err("DSACK driver on while U4 still drives DSACK");
  else if ($realtime - t_u4z < 1000 && $realtime - t_u4z < u_gap_min) u_gap_min = $realtime - t_u4z; end endtask
always @(negedge f_d) if (f_d === 1'b0) other_on;
always @(negedge e_d) if (e_d === 1'b0) other_on;
always @(negedge g_DSACK0 or negedge g_DSACK1 or negedge g_BERR or negedge g_AVEC)
  if (g_DSACK0 === 1'b0 || g_DSACK1 === 1'b0 || g_BERR === 1'b0 || g_AVEC === 1'b0) other_on;
// SIMM data-bus release vs the CPU's write data turning on
realtime t_simm_off = -1e9, simm_gap = 1e9;
always @(simm.den) if (simm.den == 4'b0000) t_simm_off = $realtime;
always @(posedge cpu_den) if (simm.den == 4'b0000 && $realtime - t_simm_off < simm_gap) simm_gap = $realtime - t_simm_off;
always @(simm.den or cpu_den) if (simm.den != 4'b0000 && cpu_den) begin #0.5; if (simm.den != 4'b0000 && cpu_den) err("data bus contention SIMM vs CPU write data"); end
// DRAM reference memory (same sparse index as the SIMM model) and wait-state histogram
reg [7:0] refm [0:131071]; integer wsh [0:15]; integer n_rd = 0, n_bad = 0, n_cmp = 0;
function [16:0] ridx(input [31:0] a); ridx = {a[26], a[15:12], a[11:2], a[1:0]}; endfunction
function [11:0] erow(input [31:0] a); erow = {a[24], a[22], a[21:12]}; endfunction
function [11:0] ecol(input [31:0] a); ecol = {a[25], a[23], a[11:2]}; endfunction
// MC68882 CS timing (FPU UM 12.6): #8 CS negated before AS of a following non-FPCP access; #8B CS -> DS (write) >= 20;
// #9 AS negated -> CS negated >= 5
realtime t_fcs_f = -1e9, m8b = 1e9, m9 = 1e9; integer n8 = 0;
always @(negedge FPU_CS_n) t_fcs_f = $realtime;
always @(posedge FPU_CS_n) if ($realtime - t_as_r < 100 && $realtime - t_as_r < m9) m9 = $realtime - t_as_r;
always @(negedge DS_n) if (kind == K_FPU && !R_W && $realtime - t_fcs_f < m8b && !FPU_CS_n) m8b = $realtime - t_fcs_f;
always @(negedge AS_n) begin t_as_f = $realtime; if (kind != K_FPU && !FPU_CS_n) begin n8 = n8 + 1; err("#8: FPU_CS_n still asserted when a non-FPU AS falls"); end end
always @(posedge AS_n) t_as_r = $realtime;
// IDE (ATA/ATAPI-6 T13/1410D r3a, Table 66/67 PIO mode 0): t0 600, t1 70, t2 290 (8-bit) / 165, t4 30, t9 20
realtime t_ch = -1e9, t_str_r = -1e9, t_prev = -1e9, t_iow_r = -1e9;
realtime t0m = 1e9, t1m = 1e9, t2m = 1e9, t4m = 1e9, t9m = 1e9; realtime t_str_f; integer nstr = 0;
wire str_n = IDE_DIOR_n & IDE_DIOW_n;
wire [2:0] da = {IDE_DA2, IDE_DA1, IDE_DA0};
always @(IDE_CS0_n or IDE_CS1_n or da) if ($realtime > 1000) begin
  t_ch = $realtime; if (str_n && $realtime - t_str_r < t9m) t9m = $realtime - t_str_r;
  if (!str_n) err("IDE CS/DA changed during DIOR/DIOW");
end
always @(negedge str_n) if ($realtime > 1000) begin
  t_str_f = $realtime; if (nstr > 0 && t_str_f - t_prev < t0m) t0m = t_str_f - t_prev;
  if (t_str_f - t_ch < t1m) t1m = t_str_f - t_ch; t_prev = t_str_f; nstr = nstr + 1;
end
always @(posedge str_n) if ($realtime > 1000) begin t_str_r = $realtime; if (t_str_r - t_str_f < t2m) t2m = t_str_r - t_str_f; end
always @(posedge IDE_DIOW_n) t_iow_r = $realtime;
always @(posedge AS_n) if (!R_W && (kind == K_IDE0 || kind == K_IDE1) && $realtime + 7 - t_iow_r < t4m) t4m = $realtime + 7 - t_iow_r;

// ------------------------------------------------------------------ 68030 bus cycle
reg worst; real das, doff, dds, d23; realtime r0, tf, ta; reg [3:0] term; integer n; reg [31:0] rdat, d1;
task bus(input integer k, input [2:0] fc, input [31:0] addr, input rw, input [3:0] want, input integer minclk);
  bus2(k, fc, addr, 2'b00, rw, 32'h0, want, minclk);
endtask
task bus2(input integer k, input [2:0] fc, input [31:0] addr, input [1:0] siz, input rw, input [31:0] wd, input [3:0] want, input integer minclk);
begin
  @(posedge CLK); r0 = $realtime;                       // S0
  worst = (`RND % 2) == 0;
  das = worst ? 3.0 : 3.0 + (`RND % 1501) / 100.0;  // #9 3..18
  tf = r0 + 20 + das; if (tf < t_as_r + 30) tf = t_as_r + 30;   // #15
  ta = worst ? tf - 7 : r0 + (`RND % 2001) / 100.0; // #6 0..20 after S0, #11 >= 7 before AS
  if (ta > tf - 7) ta = tf - 7; if (ta < t_as_r + 7) ta = t_as_r + 7;   // #13
  #(ta - $realtime); FC = fc; A = addr; R_W = rw; SIZ = siz; kind = k;
  if (k == K_DRAM) begin simm.exp_row = erow(addr); simm.exp_col = ecol(addr); simm.exp_side = addr[26]; simm.exp_valid = 1; end
  else simm.exp_valid = 0;
  #(tf - $realtime); AS_n = 0; if (rw) DS_n = 0;
  if (!rw) begin dds = 27 + (`RND % 301) / 100.0; fork begin #(dds); if (!AS_n) DS_n = 0; end join_none
    d23 = 2 + (`RND % 1801) / 100.0; fork begin #(r0 + 40 + d23 - $realtime); if (!AS_n) begin cpu_dout = wd; cpu_den = 1; end end join_none end
  n = 0; term = 0;
  while (term == 0 && n < 200) begin @(posedge CLK); #18; n = n + 1;   // sample 2 ns before each falling edge (#47A)
    term = {BERR_n === 1'b0, AVEC_n === 1'b0, DSACK1_n === 1'b0, DSACK0_n === 1'b0}; end
  // EC #31A: DSACK0/DSACK1 may be skewed by up to 7 ns (25 MHz); the CPU accepts the second one within that window
  if (term[3:2] == 0 && (term[1:0] == 2'b01 || term[1:0] == 2'b10)) begin #(T31A);
    term = term | {BERR_n === 1'b0, AVEC_n === 1'b0, DSACK1_n === 1'b0, DSACK0_n === 1'b0}; end
  @(negedge CLK); #38; d1 = D; @(negedge CLK); rdat = D;   // data latched at the next falling edge (#27 setup 2 ns)
  if (rw && k == K_DRAM && d1 !== rdat) err("DRAM read data not stable in the latch window");
  doff = worst ? 18.0 : (`RND % 1801) / 100.0;       // #12 0..18
  #(doff); AS_n = 1; DS_n = 1;
  if (!rw) fork begin #7; cpu_den = 0; end join_none   // #25 data-out held >= 7 ns after AS negated
  ncyc = ncyc + 1;
  if (k == K_DRAM && term === want) wsh[n - 1 > 15 ? 15 : n - 1] = wsh[n - 1 > 15 ? 15 : n - 1] + 1;
  if (term !== want) begin err("wrong termination"); $display("    kind %0d addr %h: term %b want %b after %0d", k, addr, term, want, n); end
  else if (n < minclk) begin err("termination too early"); $display("    kind %0d: %0d < %0d clocks", k, n, minclk); end
end endtask
// DRAM operations: aligned long word or single byte (lane table), reference-checked on reads
reg [31:0] dad, dwv, dexp; integer bo, bb; reg [31:0] pool [0:63]; integer np = 0;
task dram_op;
begin
  dad = {5'b0, `RND % 2 == 0, 10'b0, 16'b0} | (`RND & 32'h0000_FFFF); if (`RND % 4 == 0) dad[25:16] = `RND;
  if (np > 0 && `RND % 4 != 0) dad = pool[`RND % (np < 64 ? np : 64)] | (`RND & 3);   // mostly revisit written words
  if (`RND % 2) begin                                 // write
    if (`RND % 3 == 0) begin bo = dad[1:0]; dwv = 32'hEEEE_EEEE; dwv[8*(3-bo) +: 8] = `RND;
      bus2(K_DRAM, 3'b101, dad, 2'b01, 0, dwv, 4'b0011, 2); if (term === 4'b0011) refm[ridx(dad)] = dwv[8*(3-bo) +: 8]; end
    else begin dad[1:0] = 0; dwv = `RND; bus2(K_DRAM, 3'b101, dad, 2'b00, 0, dwv, 4'b0011, 2);
      if (term === 4'b0011) begin for (bb = 0; bb < 4; bb = bb + 1) refm[ridx(dad + bb)] = dwv[8*(3-bb) +: 8]; pool[np % 64] = dad; np = np + 1; end end
  end else begin                                      // read (long word, all four lanes)
    dad[1:0] = 0; bus2(K_DRAM, 3'b101 + (`RND % 2), dad, 2'b00, 1, 0, 4'b0011, 2); n_rd = n_rd + 1;
    for (bb = 0; bb < 4; bb = bb + 1) if (refm[ridx(dad + bb)] !== 8'hxx) n_cmp = n_cmp + 1;
    for (bb = 0; bb < 4; bb = bb + 1) if (refm[ridx(dad + bb)] !== 8'hxx && rdat[8*(3-bb) +: 8] !== refm[ridx(dad + bb)]) begin
      n_bad = n_bad + 1; err("DRAM read data mismatch"); $display("    addr %h lane %0d got %h want %h", dad, bb, rdat[8*(3-bb) +: 8], refm[ridx(dad + bb)]); end
  end
end endtask

integer i, r, lvl; reg [31:0] ad;
initial begin
  for (i = 0; i < 131072; i = i + 1) refm[i] = 8'hxx; for (i = 0; i < 16; i = i + 1) wsh[i] = 0;
  #200 PWR_RST_n = 1; simm.t_rst_rel = $realtime; #300;
  bus(K_ROM, 3'b110, 32'hE000_0000, 1, 4'b0001, 1);      // clears the boot overlay: 0000_0000 is DRAM from now on
  #(112000 - $realtime); simm.ref_ok_check = 1;          // U4 power-up: 105 us pause + 16 CBR cycles
  for (i = 0; i < `NCYC; i = i + 1) begin
    r = `RND % 20;
    case (r)
      0, 1:   bus(K_ROM,   3'b110, 32'hE000_0000 | (`RND & 32'h7FFFF), 1, 4'b0001, 1);
      2:      bus(K_DUART, 3'b101, 32'hF000_0000 | (`RND & 32'hF), 1, 4'b0001, 2);
      3:      bus(K_DUART, 3'b101, 32'hF000_0000 | (`RND & 32'hF), 0, 4'b0001, 2);
      4:      bus(K_REG,   3'b101, 32'hF003_0006 + ((`RND % 2) * 2), 0, 4'b0001, 1);   // LED on/off
      5, 6:   bus(K_IDE0,  3'b101, 32'hF001_0000 | (`RND & 32'hE), 1, 4'b0010, `IDEW);
      7:      bus(K_IDE0,  3'b101, 32'hF001_0000 | (`RND & 32'hE), 0, 4'b0010, `IDEW);
      8:      bus(K_IDE1,  3'b101, 32'hF002_0000 | (`RND & 32'hE), `RND % 2, 4'b0010, `IDEW);
      9:      begin lvl = 1 + `RND % 7; bus(K_IACK, 3'b111, 32'h000F_0000 | (lvl << 1), 1, 4'b0100, 1); end
      10:     bus(K_BERR,  3'b101, 32'h0800_0000, 1, 4'b1000, 1);
      11, 12, 13: dram_op;
      14, 15, 16: bus(K_FPU, 3'b111, 32'h0002_2000 | (`RND & 32'h1E), `RND % 2, 4'b0011, 0);
      17, 18: begin bus(K_IDE0, 3'b101, 32'hF001_0000, 1, 4'b0010, `IDEW); bus(K_IDE0, 3'b101, 32'hF001_0000, `RND % 2, 4'b0010, `IDEW); end
      default: bus(K_EXP,  3'b101, 32'hF800_0000 | (`RND & 32'h07FF_FFFC), `RND % 2, 4'b0011, 2);
    endcase
  end
  $display("cycles %0d; harmless wrong-cycle runts on ROM_CE/DUART_CS/DRAM_SEL (no strobe): %0d", ncyc, runt_harmless);
  $display("MC68882: #8 violations %0d; #8B CS->DS(write) min %0.2f ns (>= 20); #9 AS->CS negated min %0.2f ns (>= 5)", n8, m8b, m9);
  $display("DSACK: glue releases all termination pins <= %0.2f ns after AS rises; contention events %0d, longest %0.2f ns", rel_max, ncont, cont_max);
  $display("U4: DSACK driven high <= %0.2f ns and released <= %0.2f ns after AS rises; still driving after the next AS fell: %0d times (longest %0.2f ns)",
           u_hi_max, u_rel_max, u_hold_n, u_hold_max);
  $display("U4 -> next DSACK/BERR/AVEC driver (68882, glue, expansion) hand-over gap: min %0.2f ns", u_gap_min);
  simm.report;
  $display("DRAM: %0d long-word reads (%0d bytes compared), %0d mismatching bytes; SIMM data release -> CPU write data on: min %0.2f ns", n_rd, n_cmp, n_bad, simm_gap);
  $display("U4 DSACK0/DSACK1 assertion skew: max %0.2f ns over %0d cycles (EC #31A max %0.1f)", skew_max, nskew, T31A);
  $display("DRAM wait states: 2:%0d 3:%0d 4:%0d 5:%0d 6+:%0d", wsh[2], wsh[3], wsh[4], wsh[5], wsh[6]+wsh[7]+wsh[8]+wsh[9]+wsh[10]+wsh[11]+wsh[12]+wsh[13]+wsh[14]+wsh[15]);
  if (simm.errors) begin errors = errors + simm.errors; $display("SIMM model timing/protocol errors: %0d", simm.errors); end
  $display("IDE PIO-0: t0 min %0.2f (>=600), t1 min %0.2f (>=70), t2 min %0.2f (>=290), t4 min %0.2f (>=30), t9 min %0.2f (>=20) ns",
           t0m, t1m, t2m, t4m, t9m);
  if (t0m < 600) err("IDE t0 < 600"); if (t1m < 70) err("IDE t1 < 70"); if (t2m < 290) err("IDE t2 < 290");
  if (t4m < 30) err("IDE t4 < 30"); if (t9m < 20) err("IDE t9 < 20");
  $display("DFF timing-check hits (setup/recovery %0d, hold %0d): expected on the asynchronous AS_n/IORDY capture edges and AS-driven preset/clear releases", n_setup, n_hold);
  $display("done, errors=%0d", errors); $finish;
end
endmodule
