// U4 DRAM controller for one 72-pin 5 V EDO/FPM SIMM -- ATF1508AS-7JX84 (PLCC-84), JTAG enabled.
// Spec: ../../spec.md section 5 (and 3.2 timing, 4.3 pins).
//
// Derived from Mackerel-30 pld/mackerel-30/dram_controller/dram_controller.v (Colin Maykish, MIT licence,
// https://github.com/crmaykish/mackerel-68k): same 50 MHz asynchronous-FSM idea, 2-flop AS synchroniser,
// CBR refresh, 72-pin SIMM side select on A26 and the SIZ1/SIZ0/A1/A0 -> CAS byte-lane table
// (Mackerel lines 89-122, MC68030 UM Table 7-4).  Changes vs Mackerel (spec 5.7):
//   * column = low address bits (A2..A11, A23, A25), row = A12..A22, A24  -> page/burst possible later
//   * RAS->COL->CAS/DSACK in 2 ticks after the start edge (Mackerel ~6); write CAS does not wait for DS
//   * RAS/CAS/WE/DSACK and the column select are cleared ASYNCHRONOUSLY by AS_n negation (macrocell AR
//     product term), so the SIMM and DSACK release ~one array pass after AS_n rises (EC #28), and a quickly
//     re-asserted AS for the next (possibly foreign) cycle can never re-open them.
//   * DRAM_SEL_n from the glue CPLD is NOT synchronised: only the CPU's AS_n is (2 flops).  A cycle starts only
//     on the synchronised AS_n falling edge (as2 low, as3 high); DRAM_SEL_n is sampled at that clock, which is
//     >= ~46 ns after AS_n fell (AS_n capture needs 6 ns setup at the pin, then two more clocks), while the glue's
//     decode settles <= AS+11 ns incl. board (spec 3.2).  The fitted DRAM_SEL_n -> RAS-register setup is 11.5 ns,
//     so the margin is >= ~23 ns and the glue's decode glitch (address path 13-18.5 ns vs AS path 7.5 ns) never
//     reaches the FSM.  Edge (not level) detection matters: after a short AS_n-high gap, as2 can still show the
//     previous cycle's AS for up to 40 ns (bug found in the post-fit simulation and fixed).
//   * CBR refresh every 375 clocks (7.5 us) alternating sides (each side every 15 us); tRAS 80 ns.
//   * power-up: >= 100 us wait (14 refresh ticks = 105 us) then 16 CBR cycles (8 per side), then ready.
//   * reset only by PWR_RST_n (warm reset keeps refresh running).
//   * Rev A.1 (2026-09-27): DSACK1/0 = k ? ~(k & AS) : Z with one ack register k per pin (fit1508 fails on a
//     shared enable).  AS_n rising drives the pin high combinationally (one array pass) and clears k
//     asynchronously, which releases the pin ~one pass later.  Rev A kept the enables on until the 2nd DRAM_CLK
//     edge after AS_n rose (<= 57 ns), which overlapped a following MC68882 cycle whose DSACK may come at
//     START + 0 (FPU UM 12.6 #19, no minimum) -> spec risk 23.
//   * Rev A.1: the first AS synchroniser flop is asynchronously SET by AS_n high and only cleared after the
//     second flop has seen it (as1 <= as1 & ~as2), so an AS_n-high gap of any length is always seen by the
//     FSM.  Rev A sampled AS_n directly: at 33 MHz (EC #15 min 23 ns) a gap can fall between two 20 ns
//     DRAM_CLK edges with less than the 6 ns setup, leaving the DSACK enables on (driving high) into the
//     next cycle, the FSM stuck in sAck and a pending dreq carried into a foreign cycle.  The FSM now ends a
//     cycle on as3 (two flops after the asynchronous set), never on a first-stage flop.
//
//PIN: CHIP "dram" ASSIGNED TO AN PLCC84
//PIN: PWR_RST_n      : 1
//PIN: DRAM_CLK       : 83
//PIN: AS_n           : 84
//PIN: MA10           : 4
//PIN: MA11           : 5
//PIN: RAS0_n         : 6
//PIN: RAS1_n         : 8
//PIN: RAS2_n         : 9
//PIN: RAS3_n         : 10
//PIN: CAS0_n         : 11
//PIN: DSACK0_n       : 12
//PIN: DSACK1_n       : 15
//PIN: MA0            : 20
//PIN: MA1            : 21
//PIN: MA2            : 22
//PIN: MA3            : 24
//PIN: MA4            : 25
//PIN: MA5            : 27
//PIN: MA6            : 28
//PIN: MA7            : 29
//PIN: MA8            : 30
//PIN: MA9            : 31
//PIN: A10            : 33
//PIN: A9             : 34
//PIN: A8             : 35
//PIN: A7             : 36
//PIN: A6             : 37
//PIN: A5             : 39
//PIN: A4             : 40
//PIN: A3             : 41
//PIN: A2             : 44
//PIN: A1             : 45
//PIN: A0             : 46
//PIN: SIZ1           : 48
//PIN: SIZ0           : 49
//PIN: R_W            : 51
//PIN: DRAM_SEL_n     : 52
//PIN: A26            : 54
//PIN: A25            : 55
//PIN: A24            : 56
//PIN: A23            : 57
//PIN: A22            : 58
//PIN: A21            : 60
//PIN: A20            : 61
//PIN: A19            : 63
//PIN: A18            : 64
//PIN: A17            : 65
//PIN: A16            : 67
//PIN: A15            : 68
//PIN: A14            : 69
//PIN: A13            : 70
//PIN: A12            : 73
//PIN: A11            : 74
//PIN: CAS1_n         : 75
//PIN: CAS2_n         : 76
//PIN: CAS3_n         : 77
//PIN: WE_n           : 79
//PIN: MUX_SEL        : 80
// Not logic ports (pins wired on the board but unused in Rev A; reached through open solder jumpers):
//   16 STERM_n, 17 CBREQ_n, 18 CBACK_n (future burst, spec 3.4), 50 DS_n (optional WRITE_CAS_WAITS_DS).
//   2 = GCLK2 carries CLK_DRAMC (CPU clock) for a future synchronous mode; 81 = spare (test point).
module dram (
    input  DRAM_CLK,       // 50 MHz, GCLK1
    input  PWR_RST_n,      // power-on reset from TPS3808 (GCLR pin)
    input  AS_n,           // CPU address strobe (OE1 pin used as input)
    input  DRAM_SEL_n,     // from glue: AS & DRAM region & ~overlay & ~CPU space
    input  R_W,
    input  SIZ0,
    input  SIZ1,
    input  A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13,
    input  A14, A15, A16, A17, A18, A19, A20, A21, A22, A23, A24, A25, A26,
    output MA0, MA1, MA2, MA3, MA4, MA5, MA6, MA7, MA8, MA9, MA10, MA11,
    output RAS0_n, RAS1_n, RAS2_n, RAS3_n,
    output CAS0_n, CAS1_n, CAS2_n, CAS3_n,
    output WE_n,
    output MUX_SEL,        // = column phase; drives the optional 74ACT257 fallback muxes (spec 4.3)
    output DSACK0_n,
    output DSACK1_n
);
parameter REF_DIV   = 375;   // 7.5 us at 50 MHz (one side per tick -> each side every 15 us)
parameter INIT_TICKS = 14;   // 14 x 7.5 us = 105 us >= 100 us power-up pause

// ------------------------------------------------------------------ synchronisers (DRAM_CLK domain)
reg as1, as2, as3;                  // AS_n synchroniser (active low); as3 = as2 delayed
// as1: set asynchronously while AS_n is high (a gap of any width is caught); cleared at a DRAM_CLK edge only
// once as2 has taken the 1 (AS_n falling is then seen at the first edge after it, as in Rev A).
always @(posedge DRAM_CLK or posedge AS_n) if (AS_n) as1 <= 1'b1; else as1 <= as1 & ~as2;
always @(posedge DRAM_CLK) begin as2 <= as1; as3 <= as2; end
// A cycle is recognised only on the synchronised AS_n falling edge (as2 low, as3 high).  A level test is
// not enough: as2 lags AS_n by 20-40 ns, so right after a short AS_n-high gap it can still show the
// previous cycle's AS as asserted while DRAM_SEL_n already reflects the new cycle (found in post-fit sim).
// as1 rises asynchronously, so as2 may be metastable right after AS_n rises; every "AS has risen" decision
// uses as3.  (as_new cannot fire then: as3 is still low from the long AS-low period.)
wire as_new = ~as2 & as3;

// ------------------------------------------------------------------ refresh timer + init sequencer
reg [8:0] tdiv;
reg       tick;
always @(posedge DRAM_CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) begin tdiv <= 9'd0; tick <= 1'b0; end
    else begin
        tick <= (tdiv == REF_DIV-1);
        tdiv <= (tdiv == REF_DIV-1) ? 9'd0 : tdiv + 9'd1;
    end

// One-hot state flops, so every strobe register's D is a single sum of products of pins and flops
// (one array pass: DRAM_SEL_n, A26 and the synchronised AS reach the RAS registers with ~6 ns setup).
(* keep *) reg sI, sRow, sCol, sAck;                     // idle, RAS issued, column phase, acknowledged
(* keep *) reg sR0, sR1, sR2, sR3, sR4, sR5, sR6, sR7, sR8; // CBR refresh sequence
reg       pa;        // init phase A (power-up pause) in progress
reg       ready;     // init done: CPU accesses are served
reg [3:0] icnt;      // init counter: pause ticks, then 16 CBR cycles
reg       ref_pend;  // a refresh tick is pending
reg       refq;      // registered "refresh wanted" (0 during the pause)
reg       rside;     // side refreshed next (0: RAS0/2, 1: RAS1/3)
reg       refm;      // refresh owns RAS/CAS (disables the AS_n asynchronous clear)

reg  dreq;          // DRAM request seen at the AS edge while busy (refresh); served when idle
wire go_now = as_new & ~DRAM_SEL_n;   // DRAM_SEL_n is sampled only here (and latched into dreq)
wire go_ref = sI & refq;
wire go_cpu = sI & ~refq & ready & (go_now | dreq);
wire start  = go_cpu;

always @(posedge DRAM_CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) begin
        sI <= 1'b1; {sRow, sCol, sAck} <= 3'b000; {sR0, sR1, sR2, sR3, sR4, sR5, sR6, sR7, sR8} <= 9'd0;
        pa <= 1'b1; ready <= 1'b0; icnt <= 4'd0; ref_pend <= 1'b0; refq <= 1'b0; rside <= 1'b0; refm <= 1'b0;
        dreq <= 1'b0;
    end else begin
        dreq <= ~as2 & ~go_cpu & (go_now | dreq);   // as2 (not as3): as3 is high while go_now fires
        // state flops
        sI   <= (sI & ~go_ref & ~go_cpu) | (sAck & as3) | sR8;
        sRow <= go_cpu;
        sCol <= sRow;
        sAck <= sCol | (sAck & ~as3);          // leave when AS_n negation is seen (strobes already cleared async)
        sR0 <= go_ref; sR1 <= sR0; sR2 <= sR1; sR3 <= sR2; sR4 <= sR3; sR5 <= sR4; sR6 <= sR5; sR7 <= sR6; sR8 <= sR7;
        // R0: refm set; R1: CAS low; R2: RAS low; R3-R5 hold (RAS 80 ns); R6: RAS/CAS high; R7: refm off;
        // R8: precharge (>= 3 ticks from RAS high to the next RAS)
        if (go_ref) refm <= 1'b1; else if (sR7) refm <= 1'b0;
        if (sR8) rside <= ~rside;
        // refresh request: every tick once the pause is over; forced during the init burst
        if (tick & ~pa)            ref_pend <= 1'b1;   // a tick coinciding with R0 is kept
        else if (sR0)              ref_pend <= 1'b0;
        refq <= ~pa & ~sR0 & ~go_ref & (ref_pend | ~ready);
        // init: count pause ticks, then count 16 refresh cycles
        if (pa) begin
            if (tick) begin
                if (icnt == INIT_TICKS-1) begin pa <= 1'b0; icnt <= 4'd0; end
                else icnt <= icnt + 4'd1;
            end
        end else if (~ready & sR8) begin
            icnt <= icnt + 4'd1;
            if (icnt == 4'd15) ready <= 1'b1;
        end
    end

// ------------------------------------------------------------------ CPU-cycle strobes (async clear on AS_n)
// cpu_clr is a product term into each macrocell's asynchronous reset: AS_n high (and no refresh in
// progress), or power-on reset.
wire cpu_clr = (AS_n & ~refm) | ~PWR_RST_n;
wire acl     = AS_n | ~PWR_RST_n;

// CAS byte lanes for writes (spec 5.5; Mackerel lines 89-122).  Reads assert all four lanes.
wire [3:0] ct = {SIZ1, SIZ0, A1, A0};
reg  [3:0] tbl;   // {CAS3 (D31:24), CAS2, CAS1, CAS0 (D7:0)}, 1 = assert
always @* case (ct)
    4'b0100: tbl = 4'b1000;  4'b0101: tbl = 4'b0100;  4'b0110: tbl = 4'b0010;  4'b0111: tbl = 4'b0001;
    4'b1000: tbl = 4'b1100;  4'b1001: tbl = 4'b0110;  4'b1010: tbl = 4'b0011;  4'b1011: tbl = 4'b0001;
    4'b1100: tbl = 4'b1110;  4'b1101: tbl = 4'b0111;  4'b1110: tbl = 4'b0011;  4'b1111: tbl = 4'b0001;
    4'b0000: tbl = 4'b1111;  4'b0001: tbl = 4'b0111;  4'b0010: tbl = 4'b0011;  default: tbl = 4'b0001;
endcase

wire ras_end = (sAck & as3) | sR6;
wire ras_s0  = (start & ~A26) | (sR2 & ~rside);
wire ras_s1  = (start &  A26) | (sR2 &  rside);

// One register per pin, holding the active-low pin value so the fitter puts each flop in its pin macrocell
// (registered output, ~4.5 ns clock-to-pad instead of flop + combinational output).  (* keep *) stops
// Yosys merging RAS0/RAS2 etc. into one flop.  cpu_clr/acl drive the macrocell asynchronous PRESET.
(* keep *) reg r0n, r1n, r2n, r3n;
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) r0n <= 1'b1; else r0n <= ~(ras_s0 | (~r0n & ~ras_end));
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) r2n <= 1'b1; else r2n <= ~(ras_s0 | (~r2n & ~ras_end));
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) r1n <= 1'b1; else r1n <= ~(ras_s1 | (~r1n & ~ras_end));
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) r3n <= 1'b1; else r3n <= ~(ras_s1 | (~r3n & ~ras_end));

wire cas_set = sCol;
wire cas_ref = sR1;
(* keep *) reg c0n, c1n, c2n, c3n;
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) c0n <= 1'b1;
    else c0n <= ~((cas_set & (R_W | tbl[0])) | cas_ref | (~c0n & ~ras_end));
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) c1n <= 1'b1;
    else c1n <= ~((cas_set & (R_W | tbl[1])) | cas_ref | (~c1n & ~ras_end));
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) c2n <= 1'b1;
    else c2n <= ~((cas_set & (R_W | tbl[2])) | cas_ref | (~c2n & ~ras_end));
always @(posedge DRAM_CLK or posedge cpu_clr) if (cpu_clr) c3n <= 1'b1;
    else c3n <= ~((cas_set & (R_W | tbl[3])) | cas_ref | (~c3n & ~ras_end));

// column select (MA mux, buried) and its copy on the MUX_SEL pin; WE_n (early write: low one tick before CAS)
wire cyc_end = sAck & as3;
(* keep *) reg col, colp, wen;
always @(posedge DRAM_CLK or posedge acl) if (acl) col  <= 1'b0; else col  <= sRow | (col  & ~cyc_end);
always @(posedge DRAM_CLK or posedge acl) if (acl) colp <= 1'b0; else colp <= sRow | (colp & ~cyc_end);
always @(posedge DRAM_CLK or posedge acl) if (acl) wen  <= 1'b1; else wen  <= ~((sRow & ~R_W) | (~wen & ~cyc_end));

// DSACK (Rev A.1): one ack register per pin, set with CAS, cleared asynchronously by AS_n high.  The pin
// is driven while k is set: low while AS_n is low, high as soon as AS_n rises (combinational), and released
// when the asynchronous clear of k propagates (~one array pass later).  k also feeds the data term, so
// Yosys cannot treat it as a TRI-enable-only net (see ../glue/README.md, EN/ENA trap).
(* keep *) reg k0, k1;
always @(posedge DRAM_CLK or posedge acl) if (acl) k0 <= 1'b0; else k0 <= cas_set | k0;
always @(posedge DRAM_CLK or posedge acl) if (acl) k1 <= 1'b0; else k1 <= cas_set | k1;
wire as_l = ~AS_n;

// ------------------------------------------------------------------ pins
assign RAS0_n = r0n;  assign RAS2_n = r2n;  assign RAS1_n = r1n;  assign RAS3_n = r3n;
assign CAS0_n = c0n;  assign CAS1_n = c1n;  assign CAS2_n = c2n;  assign CAS3_n = c3n;
assign WE_n   = wen;
assign MUX_SEL = colp;
assign DSACK0_n = k0 ? ~(k0 & as_l) : 1'bz;
assign DSACK1_n = k1 ? ~(k1 & as_l) : 1'bz;

// MA: row = A12..A21, A22, A24 ; column = A2..A11, A23, A25 (spec 5.2)
assign MA0  = col ? A2  : A12;
assign MA1  = col ? A3  : A13;
assign MA2  = col ? A4  : A14;
assign MA3  = col ? A5  : A15;
assign MA4  = col ? A6  : A16;
assign MA5  = col ? A7  : A17;
assign MA6  = col ? A8  : A18;
assign MA7  = col ? A9  : A19;
assign MA8  = col ? A10 : A20;
assign MA9  = col ? A11 : A21;
assign MA10 = col ? A23 : A22;
assign MA11 = col ? A25 : A24;
endmodule
