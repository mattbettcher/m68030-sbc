// Functional testbench for glue.v (iverilog), used for the RTL (glue.v + cells_rtl.v) and the zero-delay
// post-fit netlist (glue.vo + prims.v, compiled with -DPOSTFIT). Not a timing sim: see tb_timed.v.
// -DOLD: build against the Rev A netlist/RTL (no IDE_DA pins; old IDE timing), to show the old failures.
`timescale 1ns/1ps
module tb;
reg CLK=0, PWR_RST_n=0, AS_n=1, DS_n=1, R_W=1, STATUS_n=1;
reg [2:0] FC=3'b101; reg [31:0] A=0;
reg DUART_INT_n=1, NIC_INT_n=1, EXP_INT_n=1, IDE_INTRQ=0, IDE_IORDY=1, NMI_BTN_n=1, WARM_RST_BTN_n=1;
wire DSACK0_n, DSACK1_n, BERR_n, AVEC_n, RESET_n, HALT_n;
pullup(DSACK0_n); pullup(DSACK1_n); pullup(BERR_n); pullup(AVEC_n); pullup(RESET_n); pullup(HALT_n);
wire CIIN_n, IPL2_n, IPL1_n, IPL0_n, DRAM_SEL_n, FPU_CS_n, ROM_CE_n, BUS_RD_n, BUS_WR_n, DUART_CS_n,
     IDE_CS0_n, IDE_CS1_n, IDE_DIOR_n, IDE_DIOW_n, IDE_BUF_EN_n, EXP_SEL_n, EXP_BUF_EN_n,
     PERIPH_RST_n, DUART_RST, LED_n, HALT_LED_n, IDE_DA0, IDE_DA1, IDE_DA2;
glue dut(.CLK(CLK), .PWR_RST_n(PWR_RST_n), .AS_n(AS_n), .DS_n(DS_n), .FC2(FC[2]), .FC1(FC[1]), .FC0(FC[0]),
 .R_W(R_W), .A31(A[31]), .A30(A[30]), .A29(A[29]), .A28(A[28]), .A27(A[27]), .A19(A[19]), .A18(A[18]),
 .A17(A[17]), .A16(A[16]), .A15(A[15]), .A14(A[14]), .A13(A[13]), .A3(A[3]), .A2(A[2]), .A1(A[1]),
 .STATUS_n(STATUS_n), .DSACK0_n(DSACK0_n), .DSACK1_n(DSACK1_n), .BERR_n(BERR_n), .AVEC_n(AVEC_n),
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
always #20 CLK = ~CLK;              // 25 MHz
integer errors=0, clocks;
// 68030-style bus cycle: AS/DS asserted after falling edge; ends when a termination is seen at a falling edge.
task cycle(input [2:0] fc, input [31:0] addr, input rw, input integer maxclk, output [3:0] term, output integer n);
begin
  @(posedge CLK); #5 FC=fc; A=addr; R_W=rw;
  @(negedge CLK); #3 AS_n=0; if (rw) DS_n=0;
  n=0; term=4'b0000;
  @(negedge CLK); if (!rw) #3 DS_n=0;
  while (term==0 && n<maxclk) begin
    @(negedge CLK); n=n+1;
    term = {~BERR_n, ~AVEC_n, ~DSACK1_n, ~DSACK0_n};
  end
  @(negedge CLK); #3 AS_n=1; DS_n=1;
  @(posedge CLK); #1;
  if (DSACK0_n!==1'b1 || BERR_n!==1'b1) begin $display("ERR: termination not negated/released"); errors=errors+1; end
  @(posedge CLK); #1;
  if (DSACK0_n!==1'bz && DSACK0_n!==1'b1) begin $display("ERR: DSACK0 stuck"); errors=errors+1; end
end endtask
task expect(input [3:0] got, input [3:0] want, input [8*24-1:0] what, input integer n);
begin
  if (got!==want) begin $display("ERR %0s: term=%b want %b after %0d clk", what, got, want, n); errors=errors+1; end
  else $display("ok  %0s: term=%b after %0d clk", what, got, n);
end endtask
reg [3:0] t; integer n; reg saw;
// ---- IDE timing monitor (ATA/ATAPI-6 Tables 66/67, PIO mode 0), zero-delay: clock-quantised check of the logic
realtime t_cs=-1e9, t_da=-1e9, t_ior_f=-1e9, t_ior_r=-1e9, t_iow_f=-1e9, t_iow_r=-1e9, t_as_r=-1e9, t_prev_strobe=-1e9;
realtime t0min=1e9, t1min=1e9, t2min=1e9, t9min=1e9, t4min=1e9;
integer nstrobe=0;
wire ide_cs_any = ~IDE_CS0_n | ~IDE_CS1_n;
always @(IDE_CS0_n or IDE_CS1_n) begin
  t_cs = $realtime; if ($realtime > 100)
  if ((t_ior_r > t_ior_f || t_iow_r > t_iow_f) && $realtime - (t_ior_r > t_iow_r ? t_ior_r : t_iow_r) < t9min)
     begin t9min = $realtime - (t_ior_r > t_iow_r ? t_ior_r : t_iow_r); end
end
always @(IDE_DA0 or IDE_DA1 or IDE_DA2) begin
  t_da = $realtime; if ($realtime > 100)
  if ($realtime - (t_ior_r > t_iow_r ? t_ior_r : t_iow_r) < t9min) begin t9min = $realtime - (t_ior_r > t_iow_r ? t_ior_r : t_iow_r); end
end
task strobe_start; begin
  if (nstrobe > 0 && $realtime - t_prev_strobe < t0min) t0min = $realtime - t_prev_strobe;
  if ($realtime - (t_cs > t_da ? t_cs : t_da) < t1min) t1min = $realtime - (t_cs > t_da ? t_cs : t_da);
  t_prev_strobe = $realtime; nstrobe = nstrobe + 1;
end endtask
always @(negedge IDE_DIOR_n) begin t_ior_f = $realtime; strobe_start; end
always @(negedge IDE_DIOW_n) begin t_iow_f = $realtime; strobe_start; end
always @(posedge IDE_DIOR_n) begin t_ior_r = $realtime; if (t_ior_r - t_ior_f < t2min) t2min = t_ior_r - t_ior_f; end
always @(posedge IDE_DIOW_n) begin t_iow_r = $realtime; if (t_iow_r - t_iow_f < t2min) t2min = t_iow_r - t_iow_f; end
// t4 (DIOW data hold 30): the 68030 holds write data only #25 = 7 ns after AS_n rises
always @(posedge AS_n) begin t_as_r = $realtime;
  if (!R_W && t_iow_r > t_iow_f && t_iow_r > t_as_r - 1000 && (t_as_r + 7 - t_iow_r) < t4min) t4min = t_as_r + 7 - t_iow_r; end
// ---- termination monitor: a DSACK/BERR/AVEC low within 45 ns of AS_n falling is a carried-over (false) termination
realtime t_as_f=-1e9; integer false_term=0;
always @(negedge AS_n) t_as_f = $realtime;
always @(negedge DSACK0_n or negedge DSACK1_n or negedge BERR_n or negedge AVEC_n or negedge BUS_RD_n)
  if (!AS_n && $realtime - t_as_f < 45 && $realtime > 1000) begin
    false_term = false_term + 1; $display("ERR: false termination/strobe %0.1f ns after AS_n fell (t=%0t)", $realtime - t_as_f, $time); end
initial begin
  #200 PWR_RST_n=1; #100;
  // boot overlay: read at 0 -> ROM, DSACK0
  saw=0; fork cycle(3'b110, 32'h0000_0000, 1, 200, t, n); begin #60; @(negedge CLK); saw = ~ROM_CE_n & DRAM_SEL_n; end join
  expect(t, 4'b0001, "overlay ROM read @0", n); if(!saw) begin $display("ERR: ROM_CE not asserted/DRAM_SEL asserted"); errors=errors+1; end
  // ROM native E000_0000 clears overlay
  cycle(3'b110, 32'hE000_0000, 1, 200, t, n); expect(t, 4'b0001, "ROM read @E0000000", n);
  // now 0 is DRAM: glue does not terminate; DRAM_SEL asserted; timeout BERR at 128
  saw=0; fork cycle(3'b101, 32'h0000_1000, 1, 200, t, n); begin #60; @(negedge CLK); saw = ~DRAM_SEL_n & ROM_CE_n; end join
  expect(t, 4'b1000, "DRAM unterminated -> timeout", n); if(!saw) begin $display("ERR: DRAM_SEL"); errors=errors+1; end
  if (n<120 || n>135) begin $display("ERR: timeout at %0d clocks", n); errors=errors+1; end
  // DUART read
  cycle(3'b101, 32'hF000_0003, 1, 200, t, n); expect(t, 4'b0001, "DUART read", n);
  // IDE read (DSACK1): W = IDE_SETUP + IDE_PULSE = 13 at 25 MHz (was 11)
  cycle(3'b101, 32'hF001_0000, 1, 200, t, n); expect(t, 4'b0010, "IDE CS0 read", n);
  $display("    IDE read: %0d clocks from S2 to DSACK1 sample", n);
  // back-to-back IDE accesses (16-bit data reads/writes, register read) for t0/t1/t2/t9/t4
  cycle(3'b101, 32'hF001_0000, 1, 200, t, n); expect(t, 4'b0010, "IDE data read #2", n);
  cycle(3'b101, 32'hF001_000E, 1, 200, t, n); expect(t, 4'b0010, "IDE status read (DA=7)", n);
`ifndef OLD
  if ({IDE_DA2,IDE_DA1,IDE_DA0} !== 3'd7) begin $display("ERR: IDE_DA=%0d want 7", {IDE_DA2,IDE_DA1,IDE_DA0}); errors=errors+1; end
`endif
  cycle(3'b101, 32'hF001_0000, 0, 200, t, n); expect(t, 4'b0010, "IDE data write", n);
  cycle(3'b101, 32'hF002_000C, 0, 200, t, n); expect(t, 4'b0010, "IDE CS1 write (DA=6)", n);
  cycle(3'b101, 32'hF001_0002, 1, 200, t, n); expect(t, 4'b0010, "IDE read after write", n);
  $display("    IDE (zero-delay, clock-quantised): t0 min %0.0f (>=600), t1 min %0.0f (>=70), t2 min %0.0f (>=290), t9 min %0.0f (>=20), t4 min %0.0f (>=30) ns",
           t0min, t1min, t2min, t9min, t4min);
  if (t0min < 600 || t1min < 70 || t2min < 290 || t9min < 20 || t4min < 30) begin $display("ERR: IDE PIO-0 timing"); errors=errors+1; end
  // Missed AS-high gap (EC #12 AS negated up to 18 ns after the falling edge, #15 re-asserted >= 30 ns later):
  // the only rising edge in the gap can miss AS_n high. Emulated here by an AS-high pulse between two rising
  // edges. ROM read (DSACK0), gap, then an IDE read: the IDE cycle must not be terminated by a stale DSACK0.
  @(posedge CLK); #5 FC=3'b101; A=32'hE000_0000; R_W=1;
  @(negedge CLK); #3 AS_n=0; DS_n=0;
  n=0; t=0; while (t==0 && n<50) begin @(negedge CLK); n=n+1; t={~BERR_n, ~AVEC_n, ~DSACK1_n, ~DSACK0_n}; end
  @(negedge CLK); @(posedge CLK); #1 AS_n=1; DS_n=1;
  #5 A=32'hF001_0000;
  #30 AS_n=0; DS_n=0;                           // AS high 31 ns, no rising edge inside
  n=0; t=0; while (t==0 && n<50) begin @(negedge CLK); n=n+1; t={~BERR_n, ~AVEC_n, ~DSACK1_n, ~DSACK0_n}; end
  @(negedge CLK); #3 AS_n=1; DS_n=1;
  if (t !== 4'b0010 || n < 10) begin $display("ERR missed-gap: IDE cycle after ROM read terminated with %b after %0d clk (stale cycle state)", t, n); errors=errors+1; end
  else $display("ok  missed AS gap: next cycle terminated correctly (%b after %0d clk)", t, n);
  repeat(3) @(posedge CLK);
  // unmapped memory 0800_0000 -> fast BERR
  cycle(3'b101, 32'h0800_0000, 1, 200, t, n); expect(t, 4'b1000, "unmapped 08000000", n);
  // bad I/O slot F004_0000 -> BERR
  cycle(3'b101, 32'hF004_0000, 1, 200, t, n); expect(t, 4'b1000, "I/O slot 4", n);
  // FPU CPU space: CpID1 (A15:13=001), type 2 -> FPU_CS, no glue termination (FPU drives DSACK); expect timeout-free if FPU answered
  saw=0; fork cycle(3'b111, 32'h0002_2000, 1, 6, t, n); begin #60; @(negedge CLK); saw = ~FPU_CS_n; end join
  expect(t, 4'b0000, "FPU cpu-space (no glue term)", n); if(!saw) begin $display("ERR: FPU_CS"); errors=errors+1; end
  // other coprocessor ID -> BERR
  cycle(3'b111, 32'h0002_4000, 1, 200, t, n); expect(t, 4'b1000, "CpID 2 -> BERR", n);
  // breakpoint ack (type 0) -> BERR
  cycle(3'b111, 32'h0000_0000, 1, 200, t, n); expect(t, 4'b1000, "BKPT ack -> BERR", n);
  // interrupt: DUART_INT (level 5?) -> IPL, IACK -> AVEC
  DUART_INT_n=0; repeat(4) @(posedge CLK); #1 $display("IPL with DUART_INT = %0d", ~{IPL2_n,IPL1_n,IPL0_n} & 3'b111);
  cycle(3'b111, 32'h000F_000A, 1, 200, t, n); expect(t, 4'b0100, "IACK level 5 -> AVEC", n);
  DUART_INT_n=1;
  // register write: LED on (reg 3 -> A3:1=3 -> offset 6)
  cycle(3'b101, 32'hF003_0006, 0, 200, t, n); expect(t, 4'b0001, "REG write LED on", n);
  if (LED_n!==1'b0) begin $display("ERR: LED not on"); errors=errors+1; end
  cycle(3'b101, 32'hF003_0008, 0, 200, t, n); if (LED_n!==1'b1) begin $display("ERR: LED not off"); errors=errors+1; end
  // flash write without flash_we: DSACK but no BUS_WR
  saw=0; fork cycle(3'b101, 32'hE000_0000, 0, 200, t, n); begin repeat(4) @(negedge CLK); saw = ~BUS_WR_n; end join
  if (saw) begin $display("ERR: BUS_WR asserted without flash_we"); errors=errors+1; end else $display("ok  flash write blocked");
  // 100 Hz timer: enable (reg 0), expect IPL 6 within ~10 ms, IACK 6 clears it
  cycle(3'b101, 32'hF003_0000, 0, 200, t, n); expect(t, 4'b0001, "REG write timer en", n);
  wait (~{IPL2_n,IPL1_n,IPL0_n} == 3'd6); $display("ok  timer IPL6 at %0t ns", $time/1000);
  cycle(3'b111, 32'h000F_000C, 1, 200, t, n); expect(t, 4'b0100, "IACK6 -> AVEC", n);
  repeat(3) @(posedge CLK); if (~{IPL2_n,IPL1_n,IPL0_n} != 3'd0) begin $display("ERR: timer IRQ not cleared by IACK6"); errors=errors+1; end
  // NMI button (debounced on 100 Hz tick): IPL 7
  NMI_BTN_n=0; wait (~{IPL2_n,IPL1_n,IPL0_n} == 3'd7); $display("ok  NMI IPL7 at %0t ns", $time/1000); NMI_BTN_n=1;
  cycle(3'b111, 32'h000F_000E, 1, 200, t, n); expect(t, 4'b0100, "IACK7 -> AVEC", n);
  cycle(3'b101, 32'hF003_0002, 0, 200, t, n);   // timer disable
  // warm reset button: RESET_n/HALT_n pulse
  WARM_RST_BTN_n=0; wait (RESET_n===1'b0); $display("ok  warm reset asserted at %0t ns", $time/1000);
  WARM_RST_BTN_n=1; wait (RESET_n!==1'b0); $display("ok  warm reset released at %0t ns", $time/1000);
  errors = errors + false_term;
  $display("done, errors=%0d", errors); $finish;
end
initial begin #200000000 $display("TIMEOUT"); $finish; end
endmodule
