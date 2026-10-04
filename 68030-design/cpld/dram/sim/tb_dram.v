`timescale 1ns/1ps
// Testbench for U4 dram.v (RTL) or the fitted netlist dram.vo (+ SDF-derived delays): 68030 asynchronous
// bus model at 25 MHz (EC timing ranges), glue DRAM_SEL_n model with the FITTED glue delays (AS path 7.5 ns,
// address/FC path 13 ns -> a real decode glitch when a non-DRAM cycle follows a DRAM cycle), a foreign
// 8-bit device, and a 60 ns EDO SIMM model (simm_edo.v) that checks the DRAM timing.
// Rev A.1 (2026-09-27): +cpu33 selects a 33.33 MHz CPU with the EC 33.33 MHz ranges; half of the cycles use the
// worst case AS-high gap (AS negated at #12 max, next AS asserted exactly #15 min later: 30 ns @25, 23 ns @33);
// CPU-space (FPU) foreign cycles answer with DSACK1+0 at AS + 7.5 (glue FPU_CS) + 0..25 ns (68882 #19, no minimum)
// and the tb measures the gap between U4 releasing DSACK and the next driver turning on (must be > 0).
// Primitive models: ../../glue/sim/prims_timed.v style (transport delays, +derate/+dmin, +seed, DFF checks).
`ifndef OUT_DLY
`define OUT_DLY 10.0      // RTL only: approximate fitted clock-to-pad (registered outputs)
`endif
`ifndef MA_DLY
`define MA_DLY 12.0       // RTL only: approximate col-register / address to MA pad
`endif
module tb;
integer n_setup = 0, n_hold = 0;           // incremented by prims_timed.v DFFEARS
integer sd = 1;                            // RNG seed (+seed=<n>) for the bus model and +derate
real dmin = 0.5; integer dpct;
initial begin if ($value$plusargs("seed=%d", sd)) $display("seed %0d", sd); if ($value$plusargs("dmin=%d", dpct)) dmin = dpct / 100.0; end
`define RND ($unsigned($random(sd)))
reg cpu33 = 0; initial cpu33 = $test$plusargs("cpu33");
real TCPU = 40.0;                          // 25 MHz CPU clock (30.0 with +cpu33)
// MC68030 EC AC table, 25 MHz / 33.33 MHz columns: #6 addr valid 0-20/0-14, #9 AS asserted 3-18/2-10,
// #12 AS negated 0-18/0-10, #15 AS negated width 30/23, #9B AS->DS (write) 27/22, #11 addr->AS 7/5, #13 AS->addr 7/5,
// #23 clock high -> data-out valid max 20/14, #31 DSACK asserted -> data-in valid (async) max 28/20
real E6, E9a, E9b, E12, E15, E9B, E11, E13, E23, E31;
initial begin
  if ($test$plusargs("cpu33")) begin TCPU = 30.0; E6 = 14; E9a = 2; E9b = 10; E12 = 10; E15 = 23; E9B = 22; E11 = 5; E13 = 5; E23 = 14; E31 = 20; end
  else begin E6 = 20; E9a = 3; E9b = 18; E12 = 18; E15 = 30; E9B = 27; E11 = 7; E13 = 7; E23 = 20; E31 = 28; end
end
real TDRAM = 20.0 * (1.0 + 1.0/997.0);     // 50 MHz DRAM clock, slightly off so the phase sweeps
real TBRD = 3.0;                           // series-R + SIMM load delay on MA/RAS/CAS/WE [EST]
reg CPUCLK = 0, DCLK = 0;
initial begin #0.01; forever #(TCPU/2) CPUCLK = ~CPUCLK; end
initial begin #7.3; forever #(TDRAM/2) DCLK = ~DCLK; end

reg PWR_RST_n = 0;
reg [31:0] A = 32'hE000_0000; reg [2:0] FC = 3'd6; reg [1:0] SIZ = 2'b00; reg R_W = 1; reg AS_n = 1, DS_n = 1;
tri [31:0] D;
reg [31:0] cpu_dout = 0; reg cpu_den = 0;
assign D = cpu_den ? cpu_dout : 32'hzzzz_zzzz;
tri1 DSACK0_n, DSACK1_n;

// ---- glue model: DRAM_SEL_n = ~(AS & A31:27==0 & FC!=7 & ~overlay), fitted delays (cpld/glue/timing.txt)
wire dec = (A[31:27] == 5'd0) && (FC != 3'd7);
wire #(13.0) dec_d = dec;
wire #(7.5)  as_d  = ~AS_n;
wire #(1.0)  DRAM_SEL_n = ~(as_d & dec_d);

// ---- foreign 8-bit device (ROM/IO/FPU stand-in): DSACK0 after 3 CPU clocks, data 5A, active negation
reg f_dsack = 0, f_oe = 0, f_den = 0;
assign DSACK0_n = f_oe ? ~f_dsack : 1'bz;
assign D = f_den ? 32'h5A5A5A5A : 32'hzzzz_zzzz;
reg foreign = 0;
// 68882-like agent in CPU-space cycles: DSACK1+0 at AS + 7.5 (glue FPU_CS_n, single PT) + 0..25 ns (#19)
reg p_dsack = 0, p_oe = 0; real pd;
assign DSACK0_n = p_oe ? ~p_dsack : 1'bz;
assign DSACK1_n = p_oe ? ~p_dsack : 1'bz;
real t_oth_on = -1.0e9;
always @(negedge AS_n) if (!dec) begin : fdev
    foreign = 1;
    if (FC == 3'd7) begin
        pd = 7.5 + (`RND % 2501) / 100.0; #(pd);
        if (!AS_n) begin p_dsack = 1; p_oe = 1; t_oth_on = $realtime; end
    end else fork
      begin repeat (3) @(posedge CPUCLK); #10; if (!AS_n) begin f_dsack = 1; f_oe = 1; t_oth_on = $realtime; end end
      begin #30; if (!AS_n && R_W) f_den = 1; end
    join
end
always @(posedge AS_n) begin
    if (p_oe) begin pd = 3 + (`RND % 2701) / 100.0; #(pd) p_dsack = 0; pd = (`RND % 1001) / 100.0; #(pd) p_oe = 0; end  // #21/#22
    if (f_oe) begin f_dsack = 0; #25 f_oe = 0; end
    #8 f_den = 0; foreign = 0;
end

// ---- DUT
wire [11:0] MAd; wire [3:0] RASd, CASd; wire WEd, MUXd, DS0d, DS1d;
`ifdef POSTFIT
dram dut(
`else
dram dut(
`endif
    .DRAM_CLK(DCLK), .PWR_RST_n(PWR_RST_n), .AS_n(AS_n), .DRAM_SEL_n(DRAM_SEL_n), .R_W(R_W), .SIZ0(SIZ[0]), .SIZ1(SIZ[1]),
    .A0(A[0]), .A1(A[1]), .A2(A[2]), .A3(A[3]), .A4(A[4]), .A5(A[5]), .A6(A[6]), .A7(A[7]), .A8(A[8]), .A9(A[9]),
    .A10(A[10]), .A11(A[11]), .A12(A[12]), .A13(A[13]), .A14(A[14]), .A15(A[15]), .A16(A[16]), .A17(A[17]),
    .A18(A[18]), .A19(A[19]), .A20(A[20]), .A21(A[21]), .A22(A[22]), .A23(A[23]), .A24(A[24]), .A25(A[25]), .A26(A[26]),
    .MA0(MAd[0]), .MA1(MAd[1]), .MA2(MAd[2]), .MA3(MAd[3]), .MA4(MAd[4]), .MA5(MAd[5]), .MA6(MAd[6]), .MA7(MAd[7]),
    .MA8(MAd[8]), .MA9(MAd[9]), .MA10(MAd[10]), .MA11(MAd[11]),
    .RAS0_n(RASd[0]), .RAS1_n(RASd[1]), .RAS2_n(RASd[2]), .RAS3_n(RASd[3]),
    .CAS0_n(CASd[0]), .CAS1_n(CASd[1]), .CAS2_n(CASd[2]), .CAS3_n(CASd[3]),
    .WE_n(WEd), .MUX_SEL(MUXd), .DSACK0_n(DS0d), .DSACK1_n(DS1d));
`ifdef POSTFIT
real OD = 0.0, MD = 0.0;                 // the netlist carries the fitter's SDF delays
`else
real OD = `OUT_DLY, MD = `MA_DLY;
`endif
wire [11:0] MAp; wire [3:0] RASp, CASp; wire WEp;
assign #(MD)  MAp = MAd;
assign #(OD)  RASp = RASd;
assign #(OD)  CASp = CASd;
assign #(OD)  WEp = WEd;
assign #(OD)  DSACK0_n = DS0d;
assign #(OD)  DSACK1_n = DS1d;
wire [11:0] MAs; wire [3:0] RASs, CASs; wire WEs;
// Power-up: the ATF15xx clears every register at power-up, so the active-low strobe registers read 0 for the
// few ns until the AS_n/PWR_RST_n asynchronous preset takes effect.  The netlist sim reproduces that at t=0;
// the SIMM is not powered/initialised at that instant, so its inputs are held high for the first 50 ns.
reg pwr_ok = 0; initial #50 pwr_ok = 1;
assign #(TBRD) MAs = MAp;
assign #(TBRD) RASs = pwr_ok ? RASp : 4'hf;  assign #(TBRD) CASs = pwr_ok ? CASp : 4'hf;  assign #(TBRD) WEs = pwr_ok ? WEp : 1'b1;

simm_edo simm(.MA(MAs), .RAS0_n(RASs[0]), .RAS1_n(RASs[1]), .RAS2_n(RASs[2]), .RAS3_n(RASs[3]),
              .CAS0_n(CASs[0]), .CAS1_n(CASs[1]), .CAS2_n(CASs[2]), .CAS3_n(CASs[3]), .WE_n(WEs), .DQ(D));

// ---- reference memory (same sparse index as the SIMM model)
reg [7:0] refm [0:131071];   // {side,row[3:0],col[9:0],lane}
integer i, errors = 0, n_cyc = 0, n_dram = 0, n_for = 0, n_to = 0;
integer wsh[0:15];
integer ws_max = -1;
real t_ds_assert = 0, t_dchg = 0, min31 = 1e9; integer n31 = 0;
real t_asr = 0, max_rel_hi = 0, max_rel_z = 0;
always @(negedge DSACK1_n) t_ds_assert = $realtime;
always @(negedge DSACK0_n) if (DSACK1_n !== 1'b0) t_ds_assert = $realtime;
always @(D) t_dchg = $realtime;
// EC #28: AS negated -> DSACK negated (driven high) <= 40 ns @25 MHz; also measure release to Z
reg in_dram = 0;
always @(posedge AS_n) t_asr = $realtime;
always @(posedge DS1d) if (DS1d === 1'b1 && AS_n && ($realtime - t_asr) < 100) begin if ($realtime + OD - t_asr > max_rel_hi) max_rel_hi = $realtime + OD - t_asr; end
always @(DS1d) if (DS1d === 1'bz && ($realtime - t_asr) < 200) begin if ($realtime + OD - t_asr > max_rel_z) max_rel_z = $realtime + OD - t_asr; end
// U4 DSACK release (both pins Z) -> next DSACK driver on (foreign/68882): must be > 0 (no overlap)
real t_u4_z = -1.0e9, min_rel_gap = 1.0e9; integer n_ovl = 0;
always @(DS0d or DS1d) if (DS0d === 1'bz && DS1d === 1'bz) t_u4_z = $realtime + OD;
always @(posedge p_oe or posedge f_oe) begin
    if (DS0d !== 1'bz || DS1d !== 1'bz || $realtime < t_u4_z) begin n_ovl = n_ovl + 1; errors = errors + 1;
        $display("%t ERROR: another DSACK driver on while U4 still drives DSACK", $realtime);
        if ($realtime - t_u4_z < min_rel_gap && DS0d === 1'bz && DS1d === 1'bz) min_rel_gap = $realtime - t_u4_z; end
    else if ($realtime - t_u4_z < min_rel_gap && $realtime - t_u4_z < 1000) min_rel_gap = $realtime - t_u4_z;
end
// contention / protocol monitors
always @(DSACK0_n or DSACK1_n) if ((DSACK0_n === 1'bx) || (DSACK1_n === 1'bx)) begin errors = errors + 1; $display("%t ERROR: DSACK contention (X)", $realtime); end
always @(DS1d or DS0d) if (foreign && (DS1d === 1'b0 || DS0d === 1'b0)) begin errors = errors + 1; $display("%t ERROR: DRAM DSACK asserted during a foreign cycle", $realtime); end
// U4 still driving DSACK (high) after the NEXT cycle's AS fell: the risk-23 hold-over (report the longest)
real t_asf = -1.0e9, max_hold = 0; integer n_hold_over = 0;
always @(negedge AS_n) begin t_asf = $realtime; if (DS0d !== 1'bz || DS1d !== 1'bz) n_hold_over = n_hold_over + 1; end
always @(DS0d or DS1d) if (DS0d === 1'bz && DS1d === 1'bz && !AS_n && $realtime + OD - t_asf < 200 && $realtime + OD - t_asf > max_hold) max_hold = $realtime + OD - t_asf;
always @(negedge RASs[0] or negedge RASs[1]) if (foreign && CASs == 4'hf) begin errors = errors + 1; $display("%t ERROR: DRAM RAS cycle during a foreign cycle", $realtime); end
// data-bus driver overlap: SIMM lanes vs the CPU (writes) or the foreign device; also record the smallest
// gap between the SIMM releasing the bus and another driver turning on
real t_simm_off = -1.0e9, min_gap = 1.0e9;
always @(simm.den) if (simm.den == 4'b0000) t_simm_off = $realtime;
always @(posedge cpu_den or posedge f_den) if (simm.den == 4'b0000 && $realtime - t_simm_off < min_gap) min_gap = $realtime - t_simm_off;
always @(simm.den or cpu_den or f_den) if ((simm.den != 4'b0000) && (cpu_den || f_den)) begin
    #0.5; if ((simm.den != 4'b0000) && (cpu_den || f_den)) begin errors = errors + 1;
        $display("%t ERROR: data bus contention: SIMM lanes %b driving while cpu_den=%b f_den=%b", $realtime, simm.den, cpu_den, f_den); end
end

function [16:0] ridx(input [31:0] a); ridx = {a[26], a[15:12], a[11:2], a[1:0]}; endfunction
function [11:0] erow(input [31:0] a); erow = {a[24], a[22], a[21:12]}; endfunction
function [11:0] ecol(input [31:0] a); ecol = {a[25], a[23], a[11:2]}; endfunction

// one CPU bus cycle. rw=1 read. siz = SIZ1:0 code. lanes = bytes this 32-bit port transfers (for the check)
task bus(input [31:0] addr, input [2:0] fc, input [1:0] siz, input rw, input [31:0] wd, output [31:0] rd, output integer ws, output to);
    real t0, t9, t12, t23, ts, r0, tf, ta; integer k; reg done, worst; reg [31:0] d1, d2;
    begin
    worst = (`RND % 2) == 0;
    t9 = worst ? E9a : E9a + (`RND % 1000) / 999.0 * (E9b - E9a);
    t12 = worst ? E12 : (`RND % 1000) / 999.0 * E12;
    t23 = 2 + (`RND % 1000) / 999.0 * (E23 - 2);
    @(posedge CPUCLK); r0 = $realtime;
    t0 = r0 + TCPU/2;                                   // falling edge that starts S1
    tf = t0 + t9; if (tf < t_asr + E15) tf = t_asr + E15;   // #9, #15
    ta = worst ? tf - E11 : r0 + (`RND % 1000) / 999.0 * E6; if (ta > tf - E11) ta = tf - E11; if (ta < t_asr + E13) ta = t_asr + E13;
    #(ta - $realtime);
    A = addr; FC = fc; SIZ = siz; R_W = rw;
    in_dram = (addr[31:27] == 0) && (fc != 7);
    if (in_dram) begin simm.exp_row = erow(addr); simm.exp_col = ecol(addr); simm.exp_side = addr[26]; simm.exp_valid = 1; end
    else simm.exp_valid = 0;
    #(tf - $realtime); AS_n = 0; if (rw) DS_n = 0;
    if (!rw) begin ts = t0 + TCPU/2 + t23; if ($realtime < ts) #(ts - $realtime); cpu_dout = wd; cpu_den = 1; end   // #23: R1 + 0..max
    k = 1; done = 0; to = 0;
    while (!done) begin
        ts = t0 + k*TCPU - 2.0; if ($realtime < ts) #(ts - $realtime);
        if (DSACK0_n === 1'b0 || DSACK1_n === 1'b0) done = 1;
        else if (!rw && k == 1) begin if ($realtime < tf + E9B) #(tf + E9B - $realtime); DS_n = 0; end
        if (!done) begin k = k + 1; if (k > 150) begin done = 1; to = 1; end end
    end
    ws = k - 1;
    if (!to) begin
        // data latched at F(k+1) with 2 ns setup: must be valid and stable over [F-2, F]
        ts = t0 + (k+1)*TCPU - 2.0; if ($realtime < ts) #(ts - $realtime);
        d1 = D; #2.0; d2 = D; rd = d2;
        if (rw && in_dram) begin
            if (d1 !== d2) begin errors = errors + 1; $display("%t ERROR: read data not stable in setup window", $realtime); end
            if (t_dchg - t_ds_assert > E31) n31 = n31 + 1;
            if (t_ds_assert + E31 - t_dchg < min31) min31 = t_ds_assert + E31 - t_dchg;
        end
        ts = t0 + (k+1)*TCPU + t12; if ($realtime < ts) #(ts - $realtime);
    end else #(t12);
    AS_n = 1; DS_n = 1; #2 cpu_den = 0;
    n_cyc = n_cyc + 1;
    end
endtask

// operand access with 68030 dynamic bus sizing against a 32-bit port (splits misaligned operands)
task op(input [31:0] addr, input integer size, input rw, input [31:0] wdata, output [31:0] rdata);
    integer rem, o, n, ws, b; reg to; reg [31:0] a, lanes_d, rd; reg [1:0] sz;
    begin
    a = addr; rem = size; rdata = 0;
    while (rem > 0) begin
        o = a[1:0]; n = (rem < 4 - o) ? rem : 4 - o; sz = rem[1:0];
        lanes_d = 32'hEEEE_EEEE;             // unused lanes carry garbage (checks the CAS table)
        for (b = 0; b < n; b = b + 1) lanes_d[8*(3-(o+b)) +: 8] = wdata[8*(rem-1-b) +: 8];
        bus(a, 3'd5, sz, rw, lanes_d, rd, ws, to);
        if (to) begin errors = errors + 1; $display("%t ERROR: DRAM access timed out at %h", $realtime, a); end
        else begin
            wsh[ws > 15 ? 15 : ws] = wsh[ws > 15 ? 15 : ws] + 1; n_dram = n_dram + 1;
            for (b = 0; b < n; b = b + 1) begin
                if (!rw) refm[ridx(a + b)] = wdata[8*(rem-1-b) +: 8];
                else rdata[8*(rem-1-b) +: 8] = rd[8*(3-(o+b)) +: 8];
            end
        end
        a = a + n; rem = rem - n;
    end
    end
endtask
task chk(input [31:0] addr, input integer size);
    reg [31:0] r, e; integer b; begin
    op(addr, size, 1, 0, r);
    e = 0; for (b = 0; b < size; b = b + 1) e[8*(size-1-b) +: 8] = refm[ridx(addr + b)];
    if (r !== e) begin errors = errors + 1; $display("%t ERROR: read %h size %0d = %h, expected %h", $realtime, addr, size, r, e); end
    end
endtask
task foreign_cycle(input [31:0] addr, input [2:0] fc, input rw);
    reg [31:0] r; integer ws; reg to; begin bus(addr, fc, 2'b01, rw, 32'h12345678, r, ws, to); n_for = n_for + 1;
    if (to) begin errors = errors + 1; $display("%t ERROR: foreign cycle timed out", $realtime); end end
endtask
function [31:0] rnd_addr(input integer full);
    reg [31:0] a; begin
    a = {5'b0, 1'b0, 26'b0};
    a[26] = `RND % 2; a[15:12] = `RND; a[11:0] = `RND;
    if (full) a[25:16] = `RND;      // exercise all MA bits (aliases in the sparse model, same in ref)
    rnd_addr = a; end
endfunction

integer n, sz, rw, t, b; reg [31:0] a, r, wv; reg to; integer ws;
initial begin
    for (i = 0; i < 16; i = i + 1) wsh[i] = 0;
    for (i = 0; i < 131072; i = i + 1) refm[i] = 8'hxx;
    #1000 PWR_RST_n = 1; simm.t_rst_rel = $realtime;
    // --- accesses during the power-up pause must not be answered (glue BERR timeout ends them)
    #40000;
    bus(32'h0000_1000, 3'd5, 2'b00, 1, 0, r, ws, to);
    if (!to) begin errors = errors + 1; $display("ERROR: DRAM answered during the power-up pause"); end else n_to = n_to + 1;
    foreign_cycle(32'hE000_0000, 3'd6, 1);
    // --- wait for init (105 us pause + 16 CBR)
    #(112000 - $realtime);
    simm.ref_ok_check = 1;
    // --- 1. every SIZ/A1/A0 combination as a raw single cycle (write), then long read-back of the word
    for (t = 0; t < 16; t = t + 1) begin
        a = rnd_addr(0) & 32'hFFFF_FFFC;
        op(a, 4, 0, 32'h11223344, r);                        // known background
        wv = 32'hA0B0C0D0 ^ (t << 4);
        bus(a | t[1:0], 3'd5, t[3:2], 0, wv, r, ws, to);     // raw cycle: SIZ=t[3:2], A1:A0=t[1:0]
        // expected lanes written: offsets t[1:0] .. min(3, t[1:0]+size-1), size = SIZ (0 -> 4)
        begin : exp_lanes integer o2, nb, bb; o2 = t[1:0]; nb = (t[3:2] == 0) ? 4 : t[3:2]; if (o2 + nb > 4) nb = 4 - o2;
            for (bb = 0; bb < nb; bb = bb + 1) refm[ridx(a + o2 + bb)] = wv[8*(3-(o2+bb)) +: 8]; end
        if (to) begin errors = errors + 1; $display("ERROR: raw cycle timeout"); end
        else begin wsh[ws > 15 ? 15 : ws] = wsh[ws > 15 ? 15 : ws] + 1; n_dram = n_dram + 1; end
        chk(a, 4);
    end
    $display("%t lane test done, errors so far %0d", $realtime, errors + simm.errors);
    // --- 2. operands of 1/2/4 bytes at every offset (misaligned words/longs are split by the CPU model)
    for (t = 0; t < 12; t = t + 1) begin
        sz = (t < 4) ? 1 : (t < 8) ? 2 : 4;
        a = (rnd_addr(0) & 32'hFFFF_FFF0) | (t % 4) + 4;
        wv = `RND;
        op(a, sz, 0, wv, r);
        chk(a, sz); chk(a & 32'hFFFF_FFFC, 4); chk((a & 32'hFFFF_FFFC) + 4, 4);
    end
    $display("%t misaligned test done, errors so far %0d", $realtime, errors + simm.errors);
    // --- 3. random traffic with foreign cycles (incl. FPU CPU-space cycles with A31:27 = 0) interleaved
    for (n = 0; n < 500; n = n + 1) begin
        t = `RND % 10;
        if (t < 2) foreign_cycle((`RND % 2) ? 32'hE000_0000 | (`RND & 32'hFFFF) : 32'hF000_0003, 3'd5, `RND % 2);
        else if (t < 3) foreign_cycle(32'h0002_2000 | (`RND & 32'h1E), 3'd7, `RND % 2);   // FPU CIR (CPU space)
        else begin
            sz = (`RND % 3); sz = (sz == 0) ? 1 : (sz == 1) ? 2 : 4;
            a = rnd_addr(n % 4 == 0);
            if (`RND % 2) begin wv = `RND; op(a, sz, 0, wv, r); end
            else chk(a, sz);
        end
        repeat (`RND % 3) @(posedge CPUCLK);
    end
    // hold off the bus for > 2 refresh periods to check refresh continues alone
    #20000;
    for (n = 0; n < 50; n = n + 1) begin a = rnd_addr(0); chk(a, 4); end
    $display("---- summary (%s)", `ifdef POSTFIT "POST-FIT netlist + SDF delays" `else "RTL + nominal delays" `endif);
    simm.report;
    $display("cycles %0d (DRAM %0d, foreign %0d, early-timeout %0d)", n_cyc, n_dram, n_for, n_to);
    $display("DRAM wait states @%s MHz:", cpu33 ? "33.33" : "25"); $display("   0:%0d 1:%0d 2:%0d 3:%0d 4:%0d 5:%0d 6+:%0d", wsh[0], wsh[1], wsh[2], wsh[3], wsh[4], wsh[5],
             wsh[6]+wsh[7]+wsh[8]+wsh[9]+wsh[10]+wsh[11]+wsh[12]+wsh[13]+wsh[14]+wsh[15]);
    for (i = 15; i >= 0; i = i - 1) if (wsh[i] != 0 && ws_max < 0) ws_max = i;
    $display("  max wait states observed: %0d%s", ws_max, ws_max == 15 ? "+" : "");
    $display("SIMM bus release -> next driver on (CPU write data / foreign device): min %.1f ns", min_gap);
    $display("EC #31 (DSACK -> data valid <= %0.0f ns): min margin %.1f ns, violations %0d%s", E31, min31, n31, `ifdef POSTFIT "" `else " (informational in RTL: assumed output delays)" `endif);
    $display("EC #28 (AS negated -> DSACK negated <= %0d ns): max %.1f ns to driven-high, max %.1f ns to released (Z)", cpu33 ? 30 : 40, max_rel_hi, max_rel_z);
    $display("DSACK hand-over: U4 released -> next driver (68882-like agent at AS+7.5+0..25 / 8-bit device) on: min %.1f ns, overlaps %0d", min_rel_gap, n_ovl);
    $display("U4 DSACK drive still on when the next AS falls: %0d times, longest %.1f ns into the next cycle", n_hold_over, max_hold);
    $display("DFF timing-check hits (setup/recovery %0d, hold %0d): expected on the asynchronous AS_n synchroniser", n_setup, n_hold);
    // #31 counts as an error only for the fitted netlist; the RTL run uses an assumed +10/+12 ns output model
    // (CAS 12 ns vs 4.5 ns fitted), which is pessimistic for DSACK -> data by about 8.5 ns
    $display("done, %0d errors", errors + simm.errors `ifdef POSTFIT + n31 `endif);
    $finish;
end
// debug trace: +dbgt=<ns> prints bus/strobe activity in [dbgt-600, dbgt+100]
real dbgt = -1.0;
initial if ($value$plusargs("dbgt=%f", dbgt)) begin
    #(dbgt - 600.0);
    $display("---- trace from %t", $realtime);
    repeat (1) begin end
end
always @(AS_n or DRAM_SEL_n or RASs or CASs or WEs or DSACK0_n or DSACK1_n or D or foreign or f_den or cpu_den or R_W or A)
    if (dbgt > 0 && $realtime > dbgt - 600.0 && $realtime < dbgt + 100.0)
        $display("%t AS=%b SEL=%b RW=%b A=%h SIZ=%b RAS=%b CAS=%b WE=%b DS=%b%b D=%h fr=%b fden=%b cden=%b",
                 $realtime, AS_n, DRAM_SEL_n, R_W, A, SIZ, RASs, CASs, WEs, DSACK1_n, DSACK0_n, D, foreign, f_den, cpu_den);
endmodule
