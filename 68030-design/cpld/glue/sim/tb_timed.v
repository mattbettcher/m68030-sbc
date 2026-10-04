// Timed post-fit simulation of the glue CPLD (U3): glue_timed.v = glue.vo back-annotated from glue.sdo by sdf2v.py,
// primitives from prims_timed.v (TRANSPORT delays, so runts reach the pins; DFF setup/hold/recovery checks).
// Bus model: MC68030 asynchronous bus at 25 MHz with the EC timing extremes (MC68030EC, 25 MHz column):
//   #9  CLK low -> AS/DS asserted 3..18      #12 CLK low -> AS/DS negated 0..18    #15 AS negated width >= 30
//   #11 address/FC valid -> AS asserted >= 7 #13 AS negated -> address invalid >= 7
//   #9B AS -> DS asserted (write) >= 27      #47A async input (DSACK/BERR/AVEC) setup 2 ns before the falling edge
// About half of the cycles use the worst case for glitches and missed gaps: address changes exactly 7 ns before AS
// falls, AS rises 18 ns after the falling edge and falls again 30 ns later.
// Other bus agents: U4 (DRAM, DSACK1+0 ~100 ns after AS, driven high then released 57 ns after AS rises),
// MC68882 (START = CS.AS.(R/W + DS) [FPU UM 12.6 note 8]; DSACK after 0..25 ns (#19, no minimum given), negated
// within 30 ns and three-stated within 40 ns of START false (#21/#22), random inside those limits), expansion card.
// -DOLD: run against the Rev A netlist (no IDE_DA pins). +derate: random per-instance delay scaling [dmin..1].
`timescale 1ns/1ps
`ifdef OLD
`define IDEW 11
`else
`define IDEW 13
`endif
module tb;
integer n_setup = 0, n_hold = 0;          // incremented by prims_timed.v DFFEARS
integer sd = 1;                            // RNG seed (+seed=<n>) for the bus model and +derate
initial if ($value$plusargs("seed=%d", sd)) $display("seed %0d", sd);
`define RND ($unsigned($random(sd)))
reg CLK = 0, PWR_RST_n = 0, AS_n = 1, DS_n = 1, R_W = 1, STATUS_n = 1;
reg [2:0] FC = 3'b101; reg [31:0] A = 0;
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
`ifndef OLD
 , .IDE_DA0(IDE_DA0), .IDE_DA1(IDE_DA1), .IDE_DA2(IDE_DA2)
`endif
 );
real dmin = 0.5; integer dpct; initial if ($value$plusargs("dmin=%d", dpct)) dmin = dpct / 100.0;
always #20 CLK = ~CLK;                    // 25 MHz

localparam K_ROM=1, K_DUART=2, K_REG=3, K_IDE0=4, K_IDE1=5, K_IACK=6, K_BERR=7, K_DRAM=8, K_FPU=9, K_EXP=10;
integer kind = 0, errors = 0, ncyc = 0;
realtime t_as_f = -1e9, t_as_r = -1e9;
integer maxerr = 40; initial if ($value$plusargs("maxerr=%d", maxerr)) ;
task err(input [8*72-1:0] msg); begin errors = errors + 1; if (errors <= maxerr) $display("%t ERR %0s", $realtime, msg); end endtask

// ------------------------------------------------------------------ other DSACK drivers
reg [1:0] u_st = 2, f_st = 2, e_st = 2;   // 0 = drive low, 1 = drive high, 2 = three-state
wire u_d = (u_st == 0) ? 1'b0 : (u_st == 1) ? 1'b1 : 1'bz;
wire f_d = (f_st == 0) ? 1'b0 : (f_st == 1) ? 1'b1 : 1'bz;
wire e_d = (e_st == 0) ? 1'b0 : (e_st == 1) ? 1'b1 : 1'bz;
assign DSACK0_n = u_d; assign DSACK1_n = u_d;
assign DSACK0_n = f_d; assign DSACK1_n = f_d;
assign DSACK0_n = e_d; assign DSACK1_n = e_d;
// U4 DRAM controller: DSACK ~100 ns after AS (sim: 2..8 WS), high then Z 57 ns after AS rises (U4 post-fit sim)
// (this is the Rev A U4; Rev A.1 releases at 17.5 ns -- see ../../sim_system/ for the bench with the real U4 netlist)
integer useq = 0;
always @(negedge AS_n) begin : u4
  integer my; useq = useq + 1; my = useq;
  #60; if (!AS_n && !DRAM_SEL_n && my == useq) begin #40; if (!AS_n && my == useq) u_st = 0; end
end
always @(posedge AS_n) if (u_st == 0) begin u_st = 1; #57 if (u_st == 1) u_st = 2; end
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
always @(posedge duart_acc) if (kind != K_DUART) err("DUART access (CS + RD/WR) in a non-DUART cycle");
always @(posedge flash_acc) if (kind != K_ROM) err("flash access (CE + RD/WR) in a non-ROM cycle");
// false early termination (carried-over state): terminations within 45 ns of AS falling
always @(negedge g_DSACK0 or negedge g_DSACK1 or negedge g_BERR or negedge g_AVEC)
  if (!AS_n && $realtime - t_as_f < 45 && $realtime > 1000) err("glue termination < 45 ns after AS fell (carried-over cycle state)");
// DSACK contention (two drivers fighting = x on the net) and glue release time after AS rises
realtime tx0 = 0, tx1 = 0, cont_max = 0; integer ncont = 0;
always @(DSACK0_n) if (DSACK0_n === 1'bx) begin tx0 = $realtime;
  if (ncont < 6) $display("%t DSACK0 contention: glue %b U4 %0d FPU %0d EXP %0d, kind %0d, %0.2f ns after AS fell / %0.2f after previous AS rose",
                          $realtime, g_DSACK0, u_st, f_st, e_st, kind, $realtime - t_as_f, $realtime - t_as_r); end else if (tx0 > 0) begin
  ncont = ncont + 1; if ($realtime - tx0 > cont_max) cont_max = $realtime - tx0; tx0 = 0; end
always @(DSACK1_n) if (DSACK1_n === 1'bx) tx1 = $realtime; else if (tx1 > 0) begin
  ncont = ncont + 1; if ($realtime - tx1 > cont_max) cont_max = $realtime - tx1; tx1 = 0; end
realtime rel_max = 0;
always @(g_DSACK0 or g_DSACK1 or g_BERR or g_AVEC)
  if (AS_n && g_DSACK0 === 1'bz && g_DSACK1 === 1'bz && g_BERR === 1'bz && g_AVEC === 1'bz && $realtime - t_as_r < 200)
    if ($realtime - t_as_r > rel_max) rel_max = $realtime - t_as_r;
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
`ifdef OLD
wire [2:0] da = A[3:1];
`else
wire [2:0] da = {IDE_DA2, IDE_DA1, IDE_DA0};
`endif
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
reg worst; real das, doff, dds; realtime r0, tf, ta; reg [3:0] term; integer n;
task bus(input integer k, input [2:0] fc, input [31:0] addr, input rw, input [3:0] want, input integer minclk);
begin
  @(posedge CLK); r0 = $realtime;                       // S0
  worst = (`RND % 2) == 0;
  das = worst ? 3.0 : 3.0 + (`RND % 1501) / 100.0;  // #9 3..18
  tf = r0 + 20 + das; if (tf < t_as_r + 30) tf = t_as_r + 30;   // #15
  ta = worst ? tf - 7 : r0 + (`RND % 2001) / 100.0; // #6 0..20 after S0, #11 >= 7 before AS
  if (ta > tf - 7) ta = tf - 7; if (ta < t_as_r + 7) ta = t_as_r + 7;   // #13
  #(ta - $realtime); FC = fc; A = addr; R_W = rw; kind = k;
  #(tf - $realtime); AS_n = 0; if (rw) DS_n = 0;
  if (!rw) begin dds = 27 + (`RND % 301) / 100.0; fork begin #(dds); if (!AS_n) DS_n = 0; end join_none end
  n = 0; term = 0;
  while (term == 0 && n < 200) begin @(posedge CLK); #18; n = n + 1;   // sample 2 ns before each falling edge (#47A)
    term = {BERR_n === 1'b0, AVEC_n === 1'b0, DSACK1_n === 1'b0, DSACK0_n === 1'b0}; end
  @(negedge CLK); @(negedge CLK);                        // data latched at the next falling edge; S5
  doff = worst ? 18.0 : (`RND % 1801) / 100.0;       // #12 0..18
  #(doff); AS_n = 1; DS_n = 1;
  ncyc = ncyc + 1;
  if (term !== want) begin err("wrong termination"); $display("    kind %0d addr %h: term %b want %b after %0d", k, addr, term, want, n); end
  else if (n < minclk) begin err("termination too early"); $display("    kind %0d: %0d < %0d clocks", k, n, minclk); end
end endtask

integer i, r, lvl; reg [31:0] ad;
initial begin
  #200 PWR_RST_n = 1; #300;
  bus(K_ROM, 3'b110, 32'hE000_0000, 1, 4'b0001, 1);      // clears the boot overlay: 0000_0000 is DRAM from now on
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
      11, 12, 13: bus(K_DRAM, 3'b101 + (`RND % 2), `RND & 32'h07FF_FFFC, `RND % 2, 4'b0011, 2);
      14, 15, 16: bus(K_FPU, 3'b111, 32'h0002_2000 | (`RND & 32'h1E), `RND % 2, 4'b0011, 0);
      17, 18: begin bus(K_IDE0, 3'b101, 32'hF001_0000, 1, 4'b0010, `IDEW); bus(K_IDE0, 3'b101, 32'hF001_0000, `RND % 2, 4'b0010, `IDEW); end
      default: bus(K_EXP,  3'b101, 32'hF800_0000 | (`RND & 32'h07FF_FFFC), `RND % 2, 4'b0011, 2);
    endcase
  end
  $display("cycles %0d; harmless wrong-cycle runts on ROM_CE/DUART_CS/DRAM_SEL (no strobe): %0d", ncyc, runt_harmless);
  $display("MC68882: #8 violations %0d; #8B CS->DS(write) min %0.2f ns (>= 20); #9 AS->CS negated min %0.2f ns (>= 5)", n8, m8b, m9);
  $display("DSACK: glue releases all termination pins <= %0.2f ns after AS rises; contention events %0d, longest %0.2f ns", rel_max, ncont, cont_max);
  $display("IDE PIO-0: t0 min %0.2f (>=600), t1 min %0.2f (>=70), t2 min %0.2f (>=290), t4 min %0.2f (>=30), t9 min %0.2f (>=20) ns",
           t0m, t1m, t2m, t4m, t9m);
`ifndef OLD
  if (t0m < 600) err("IDE t0 < 600"); if (t1m < 70) err("IDE t1 < 70"); if (t2m < 290) err("IDE t2 < 290");
  if (t4m < 30) err("IDE t4 < 30"); if (t9m < 20) err("IDE t9 < 20");
`endif
  $display("DFF timing-check hits (setup/recovery %0d, hold %0d): expected on the asynchronous AS_n/IORDY capture edges", n_setup, n_hold);
  $display("done, errors=%0d", errors); $finish;
end
endmodule
