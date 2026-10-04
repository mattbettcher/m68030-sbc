// ============================================================================
// U3 glue / system controller for the 68030 Linux SBC (Rev A)
// Target: Microchip ATF1508AS-7JX84 (PLCC-84), JTAG ISP enabled.
// Spec: ../../spec.md sections 2 (memory map), 3 (bus cycles), 4.2 (pins),
//       7.2 (reset).  Flow: Yosys + Microchip fit1508 (see build.sh / README.md).
//
// Clocking: everything runs on CLK (= CPU clock, GCLK1, rising edge).
// AS_n is captured by a single synchronizer stage (spec 3.2): wait-state
// counts assume the earliest capture, a late capture only adds one state.
// Rev A.1 (2026-09-27): every per-cycle register is ASYNCHRONOUSLY CLEARED
// while AS_n is high. At 25 MHz AS_n can be negated as late as 18 ns after a
// falling edge (EC #12) and re-asserted 30 ns later (EC #15), so the single
// rising edge inside the AS-high gap can miss it (setup 6 ns); with purely
// synchronous clearing the cycle state (act/cnt/dsack/rd) would then carry
// into the next bus cycle and terminate it falsely. See spec 3.2.
//
// Termination lines (DSACK1/0_n, BERR_n, AVEC_n) are three-state push-pull:
// driven while the assert flag x_q is set, low while AS_n is low. When AS_n
// rises the direct AS_n term drives the pin high within one array pass
// (7.5 ns SDF) and the asynchronous clear of x_q then releases the driver
// (AS_n -> AR -> Q -> OE, 19.5 ns SDF), leaving the 1k pull-up to hold it
// (spec 3.1, EC #28).
//
// Chip selects (Rev A.1): FPU_CS_n, EXP_SEL_n and EXP_BUF_EN_n are single
// product terms of the address/FC pins AND AS_n (MC68881/2 UM Fig. 10-5(a)
// "correct late chip select"; EC note 14): no decode node that can lag AS.
// IDE_CS0/1_n and IDE_DA2:0 are registered and held >= 20 ns after DIOR/DIOW
// negate (ATA t9); IDE_BUF_EN_n is registered and async-cleared by AS_n.
// ============================================================================
`ifndef CPU_CLK_HZ
 `define CPU_CLK_HZ 25000000
`endif

// ---- fitter pin locks (read by run_fitter.sh; SPI reserve 46/48/49; 50-52 = IDE_DA0-2 since Rev A.1)
//PIN: CHIP "glue" ASSIGNED TO AN PLCC84
//PIN: PWR_RST_n      : 1
//PIN: DS_n           : 2
//PIN: CLK            : 83
//PIN: AS_n           : 84
//PIN: FC2            : 4
//PIN: FC1            : 5
//PIN: FC0            : 6
//PIN: R_W            : 8
//PIN: DSACK0_n       : 9
//PIN: DSACK1_n       : 10
//PIN: BERR_n         : 11
//PIN: A31            : 12
//PIN: A30            : 15
//PIN: A29            : 16
//PIN: A28            : 17
//PIN: A27            : 18
//PIN: A19            : 20
//PIN: A18            : 21
//PIN: A17            : 22
//PIN: A16            : 24
//PIN: A15            : 25
//PIN: A14            : 27
//PIN: A13            : 28
//PIN: A3             : 29
//PIN: A2             : 30
//PIN: A1             : 31
//PIN: DUART_INT_n    : 33
//PIN: NIC_INT_n      : 34
//PIN: EXP_INT_n      : 35
//PIN: NMI_BTN_n      : 36
//PIN: PERIPH_RST_n   : 37
//PIN: DUART_RST      : 39
//PIN: LED_n          : 40
//PIN: WARM_RST_BTN_n : 41
//PIN: STATUS_n       : 44
//PIN: HALT_LED_n     : 45
//PIN: IDE_DA0        : 50
//PIN: IDE_DA1        : 51
//PIN: IDE_DA2        : 52
//PIN: HALT_n         : 54
//PIN: DRAM_SEL_n     : 55
//PIN: FPU_CS_n       : 56
//PIN: ROM_CE_n       : 57
//PIN: BUS_RD_n       : 58
//PIN: BUS_WR_n       : 60
//PIN: DUART_CS_n     : 61
//PIN: IDE_CS0_n      : 63
//PIN: IDE_CS1_n      : 64
//PIN: IDE_DIOR_n     : 65
//PIN: IDE_DIOW_n     : 67
//PIN: IDE_BUF_EN_n   : 68
//PIN: EXP_SEL_n      : 69
//PIN: EXP_BUF_EN_n   : 70
//PIN: IDE_INTRQ      : 73
//PIN: IDE_IORDY      : 74
//PIN: AVEC_n         : 75
//PIN: CIIN_n         : 76
//PIN: IPL0_n         : 77
//PIN: IPL1_n         : 79
//PIN: IPL2_n         : 80
//PIN: RESET_n        : 81

module glue (
    // dedicated inputs
    input        CLK,          // pin 83 GCLK1  : CPU clock (CLK_GLUE)
    input        PWR_RST_n,    // pin 1  GCLR   : supervisor reset
    input        AS_n,         // pin 84 OE1    : used as an array input
    input        DS_n,         // pin 2  OE2/GCLK2: used as an array input
    // CPU bus
    input        FC2, FC1, FC0,
    input        R_W,
    input        A31, A30, A29, A28, A27,
    input        A19, A18, A17, A16, A15, A14, A13,
    input        A3, A2, A1,
    input        STATUS_n,
    output       DSACK0_n,
    output       DSACK1_n,
    output       BERR_n,
    output       AVEC_n,
    output       CIIN_n,
    output       IPL2_n, IPL1_n, IPL0_n,
    inout        RESET_n,
    output       HALT_n,
    // chip selects / strobes
    output       DRAM_SEL_n,
    output       FPU_CS_n,
    output       ROM_CE_n,
    output       BUS_RD_n,
    output       BUS_WR_n,
    output       DUART_CS_n,
    output       IDE_CS0_n,
    output       IDE_CS1_n,
    output       IDE_DIOR_n,
    output       IDE_DIOW_n,
    output       IDE_BUF_EN_n,
    output       IDE_DA0, IDE_DA1, IDE_DA2,   // pins 50-52: registered IDE DA2:0 (= A1..A3), Rev A.1
    output       EXP_SEL_n,
    output       EXP_BUF_EN_n,
    // interrupts, buttons, misc
    input        DUART_INT_n,
    input        NIC_INT_n,
    input        EXP_INT_n,
    input        IDE_INTRQ,
    input        IDE_IORDY,
    input        NMI_BTN_n,
    input        WARM_RST_BTN_n,
    output       PERIPH_RST_n,
    output       DUART_RST,
    output       LED_n,
    output       HALT_LED_n
    // SPI_HW_SCK/MOSI/MISO: pins reserved (46/48/49), behind open solder
    // jumpers; not ports in Rev A logic, so the fitter leaves them unused.
);

// ---------------------------------------------------------------- parameters
localparam FAST      = (`CPU_CLK_HZ > 30000000);
localparam ROM_WS    = FAST ? 2 : 1;       // spec 3.2 boot flash
localparam DUART_WS  = FAST ? 3 : 2;       // spec 3.2 SC26C92
localparam DUART_DLY = FAST ? 1 : 0;       // extra idle clock before DUART strobe (tRWD)
localparam REG_WS    = 1;
localparam IACK_WS   = 1;
localparam BERR_WS   = 1;                  // fast BERR, 1 clock after decode
// IDE (ATA/ATAPI-6 T13/1410D r3a Tables 66/67, PIO mode 0: t0 >= 600, t1 >= 70, t2 >= 290 (8-bit) /
// 165 (16-bit), t2i: none, t4 >= 30, t9 >= 20 ns). Wait states W = IDE_SETUP + IDE_PULSE. Two back-to-back
// IDE cycles put DIOx-to-DIOx at (W+3) clocks (DSACK sampled at S2/S3, AS negated in S5, next S0 at once;
// a late AS capture only lengthens a cycle): 25 MHz 16 x 40 = 640 ns, 33 MHz 21 x 30 = 630 ns (t0 >= 600).
localparam IDE_SETUP = FAST ? 5 : 4;       // CS/DA (loaded at the 2nd edge) -> DIOx: t1 = (IDE_SETUP-1) clocks
localparam IDE_PULSE = FAST ? 13 : 9;      // DIOx asserted -> DSACK1 (DIOW ends here): t2 = IDE_PULSE clocks
localparam TIMER_DIV = `CPU_CLK_HZ / 100;  // 100 Hz tick
localparam TW        = (TIMER_DIV > 262144) ? 19 : 18;

// ---------------------------------------------------------------- decode
// scalar ports (fitter pin names match schematic nets); internal buses
wire [2:0]   FC = {FC2, FC1, FC0};
wire [31:27] AH = {A31, A30, A29, A28, A27};
wire [19:13] AM = {A19, A18, A17, A16, A15, A14, A13};
wire [3:1]   AL = {A3, A2, A1};

wire cpu_space = (FC == 3'b111);
wire mem       = ~cpu_space;

reg  overlay;                                   // boot overlay (spec 2.2)
wire low_128m  = mem & (AH == 5'b00000);        // 0000_0000-07FF_FFFF
wire rom_nat   = mem & (AH[31:28] == 4'b1110);  // E000_0000-EFFF_FFFF
wire io_sp     = mem & (AH == 5'b11110);        // F000_0000-F7FF_FFFF
wire exp_sp    = mem & (AH == 5'b11111);        // F800_0000-FFFF_FFFF
wire dram_sp   = low_128m & ~overlay;
wire rom_sp    = rom_nat | (low_128m & overlay);
wire slot0     = (AM[19:16] == 4'h0);
wire duart_sp  = io_sp & slot0;
wire ide0_sp   = io_sp & (AM[19:16] == 4'h1);
wire ide1_sp   = io_sp & (AM[19:16] == 4'h2);
wire reg_sp    = io_sp & (AM[19:16] == 4'h3);
wire io_bad    = io_sp & (AM[19:18] != 2'b00);   // slots 4-F
wire ide_sp    = ide0_sp | ide1_sp;
wire unmapped  = mem & ~low_128m & ~rom_nat & ~io_sp & ~exp_sp;

wire iack_sp   = cpu_space & (AM[19:16] == 4'hF);
wire fpu_sp    = cpu_space & (AM[19:16] == 4'h2) & (AM[15:13] == 3'b001);
wire cpu_bad   = cpu_space & ~iack_sp & ~fpu_sp;   // bkpt ack, other CpIDs, reserved

wire as        = ~AS_n;

// ---------------------------------------------------------------- chip selects (combinational)
assign DRAM_SEL_n   = ~(as & dram_sp);
assign ROM_CE_n     = ~(as & rom_sp);
assign DUART_CS_n   = ~(as & duart_sp);
// FPU and expansion selects: each is ONE array pass of pin literals AND AS_n (MC68881/2 UM Fig. 10-5(a)
// "correct" late chip select; MC68030 EC note 14), so no decode node can lag AS and leave a runt select
// at the start of the next bus cycle. Written with library cells (cells.lib) so ABC cannot share or factor
// the decode with the rest of the logic (it did: with plain assigns fit1508 built FPU_CS_n = !AS_n & node).
// The fitter collapses each fanout-1 cell tree into the output macrocell: see timing.txt ("single pass").
wire nA19, nA18, nA16, nA15, nA14, nAS_f, nAS_e0, nAS_e1, nAS_e2, nAS_b0, nAS_b1, nAS_b2;
wire nFC2_e, nFC1_e, nFC0_e, nFC2_b, nFC1_b, nFC0_b;
(* keep *) INV xinvf0 (.A(A19), .QN(nA19));
(* keep *) INV xinvf1 (.A(A18), .QN(nA18));
(* keep *) INV xinvf2 (.A(A16), .QN(nA16));
(* keep *) INV xinvf3 (.A(A15), .QN(nA15));
(* keep *) INV xinvf4 (.A(A14), .QN(nA14));
(* keep *) INV xinvf5 (.A(AS_n), .QN(nAS_f));
// FPU_CS_n = !(FC=7 & A19:16=2 & A15:13=1 & AS): CPU space, coprocessor ID 1 (spec 2.3)
// (cells with >= 7 inputs are avoided: fit1508 rejects EDIF with a cell pin named "G")
wire fp0, fp1;
(* keep *) AND6 xgfp0 (.A(FC2), .B(FC1), .C(FC0), .D(nA19), .E(nA18), .F(A17), .Q(fp0));
(* keep *) AND5 xgfp1 (.A(nA16), .B(nA15), .C(nA14), .D(A13), .E(nAS_f), .Q(fp1));
(* keep *) NAND2 xgfpucs (.A(fp0), .B(fp1), .QN(FPU_CS_n));
// EXP_SEL_n / EXP_BUF_EN_n = !(A31:27=11111 & FC!=7 & AS): three product terms each, separate cells per pin
(* keep *) INV xinve0 (.A(AS_n), .QN(nAS_e0));
(* keep *) INV xinve1 (.A(AS_n), .QN(nAS_e1));
(* keep *) INV xinve2 (.A(AS_n), .QN(nAS_e2));
(* keep *) INV xinve3 (.A(FC2), .QN(nFC2_e));
(* keep *) INV xinve4 (.A(FC1), .QN(nFC1_e));
(* keep *) INV xinve5 (.A(FC0), .QN(nFC0_e));
wire es0, es1, es2, es0a, es1a, es2a;
(* keep *) AND6 xges0a (.A(A31), .B(A30), .C(A29), .D(A28), .E(A27), .F(nAS_e0), .Q(es0a));
(* keep *) AND2 xges0 (.A(es0a), .B(nFC2_e), .Q(es0));
(* keep *) AND6 xges1a (.A(A31), .B(A30), .C(A29), .D(A28), .E(A27), .F(nAS_e1), .Q(es1a));
(* keep *) AND2 xges1 (.A(es1a), .B(nFC1_e), .Q(es1));
(* keep *) AND6 xges2a (.A(A31), .B(A30), .C(A29), .D(A28), .E(A27), .F(nAS_e2), .Q(es2a));
(* keep *) AND2 xges2 (.A(es2a), .B(nFC0_e), .Q(es2));
(* keep *) NOR3 xgesel (.A(es0), .B(es1), .C(es2), .QN(EXP_SEL_n));
(* keep *) INV xinvb0 (.A(AS_n), .QN(nAS_b0));
(* keep *) INV xinvb1 (.A(AS_n), .QN(nAS_b1));
(* keep *) INV xinvb2 (.A(AS_n), .QN(nAS_b2));
(* keep *) INV xinvb3 (.A(FC2), .QN(nFC2_b));
(* keep *) INV xinvb4 (.A(FC1), .QN(nFC1_b));
(* keep *) INV xinvb5 (.A(FC0), .QN(nFC0_b));
wire eb0, eb1, eb2, eb0a, eb1a, eb2a;
(* keep *) AND6 xgeb0a (.A(A31), .B(A30), .C(A29), .D(A28), .E(A27), .F(nAS_b0), .Q(eb0a));
(* keep *) AND2 xgeb0 (.A(eb0a), .B(nFC2_b), .Q(eb0));
(* keep *) AND6 xgeb1a (.A(A31), .B(A30), .C(A29), .D(A28), .E(A27), .F(nAS_b1), .Q(eb1a));
(* keep *) AND2 xgeb1 (.A(eb1a), .B(nFC1_b), .Q(eb1));
(* keep *) AND6 xgeb2a (.A(A31), .B(A30), .C(A29), .D(A28), .E(A27), .F(nAS_b2), .Q(eb2a));
(* keep *) AND2 xgeb2 (.A(eb2a), .B(nFC0_b), .Q(eb2));
(* keep *) NOR3 xgebuf (.A(eb0), .B(eb1), .C(eb2), .QN(EXP_BUF_EN_n));
// IDE_CS0_n/IDE_CS1_n, IDE_DA2:0 and IDE_BUF_EN_n are registered: see the IDE block below.
// cache inhibit for ROM, I/O and expansion (glue is the only driver -> push-pull)
assign CIIN_n       = ~(as & (rom_sp | io_sp | exp_sp));

// ---------------------------------------------------------------- cycle counter
// cnt = number of CLK rising edges since AS_n was first seen low, minus one.
// It also implements the 128-clock bus timeout (spec 3.3).
reg        act;          // AS captured
reg  [6:0] cnt;
wire [6:0] cnt_n = act ? ((cnt == 7'd127) ? cnt : cnt + 7'd1) : 7'd0;

reg  iordy_s;            // IORDY synchronised
reg  dsack0_q, dsack1_q, avec_q, berr_q;      // assert flags = pin enables (async-cleared by AS_n)
reg  rd_q, wr_q, ior_q, iow_q;

// user-visible state
reg  timer_en, timer_pend, user_led, flash_we;
reg  nmi_pend;

wire rom_done   = rom_sp   & (cnt_n >= ROM_WS);
wire duart_done = duart_sp & (cnt_n >= DUART_WS);
wire reg_done   = reg_sp   & (cnt_n >= REG_WS);
wire ide_done   = ide_sp   & (cnt_n >= IDE_SETUP + IDE_PULSE) & iordy_s;
wire t_d0       = rom_done | duart_done | reg_done;
wire berr_set   = berr_fast | berr_to;
wire iack_done  = iack_sp  & (cnt_n >= IACK_WS);
wire berr_fast  = (unmapped | io_bad | cpu_bad) & (cnt_n >= BERR_WS);
wire berr_to    = (cnt == 7'd127);

// register write strobe: one clock, on the edge where DSACK first asserts
wire reg_wr     = as & reg_sp & ~R_W & (cnt_n == REG_WS);
wire [2:0] ia   = AL;          // IACK level / register select (A3:1)
wire iack_hit   = as & iack_sp & (cnt_n == IACK_WS);

// Per-cycle state: cleared asynchronously while AS_n is high (or at power-up reset).
wire cyc_clr = AS_n | ~PWR_RST_n;
always @(posedge CLK or posedge cyc_clr) begin
    if (cyc_clr) begin
        act <= 1'b0; cnt <= 7'd0;
        dsack0_q <= 1'b0; dsack1_q <= 1'b0; avec_q <= 1'b0; berr_q <= 1'b0;
        rd_q <= 1'b0; wr_q <= 1'b0; ior_q <= 1'b0; iow_q <= 1'b0;
    end else begin
        act <= ~AS_n;          // (= 1; written as ~AS_n because fit1508 rejects constant-driven nets)
        cnt <= cnt_n;
        // 8-bit ports: DSACK0 only; 16-bit IDE: DSACK1 only (spec 3.1)
        if (t_d0)      dsack0_q <= 1'b1;
        if (ide_done)  dsack1_q <= 1'b1;
        if (iack_done) avec_q   <= 1'b1;
        if (berr_set)  berr_q   <= 1'b1;
        // registered read/write strobes for flash and DUART (spec 3.2). Rev A.1: qualified with `act`, so the
        // earliest set is R2 (decode settled >= 1 clock); at R1 a stale decode of the previous cycle could still
        // be on the D input (FC -> D setup 22.5 ns) and give a DUART read strobe overlapping a stale DUART_CS_n.
        if (act & (rom_sp | (duart_sp & (cnt_n >= DUART_DLY))) &  R_W) rd_q <= 1'b1;
        if (act & ((rom_sp & flash_we) | (duart_sp & (cnt_n >= DUART_DLY))) & ~R_W) wr_q <= 1'b1;
        // IDE strobes: DIOR is held until AS_n negates (the CPU latches the data at the end of S4).
        // The release is the product term ~(ior_q & as), tPD1 max 7.5 ns, NOT the async clear of
        // ior_q (that STA arc is 19.5 ns and does not delay the pin). Do not end DIOR a clock early:
        // device t6 is only 5 ns. DIOW ends on the edge that asserts DSACK1, so write data (held by
        // the CPU only #25 = 7 ns after AS_n rises) stays valid >= t4 = 30 ns after DIOW- negates.
        if (ide_sp &  R_W & (cnt_n >= IDE_SETUP)) ior_q <= 1'b1;
        iow_q <= ide_sp & ~R_W & (cnt_n >= IDE_SETUP) & ~ide_done & ~dsack1_q;
    end
end
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) iordy_s <= 1'b1;
    else            iordy_s <= IDE_IORDY;

// Each shared (wire-OR) termination pin is driven only while its own flag is set: low while AS is
// asserted; when AS_n rises the pin is first driven high by the direct AS_n term, then released when the
// asynchronous clear of the flag propagates to the OE (active negation, spec 3.1). A single shared
// enable for all four pins made fit1508 v1918 abort with "INTERNAL ERROR", so the enables are per pin.
// NB (Yosys flow): the OE net must also feed logic (here the flag is the data term as well); a net that
// feeds only a TRI enable is deleted by `clean` (cells.lib names the pin EN, run_yosys.sh maps ENA).
assign DSACK0_n = dsack0_q ? ~(dsack0_q & as) : 1'bz;
assign DSACK1_n = dsack1_q ? ~(dsack1_q & as) : 1'bz;
assign AVEC_n   = avec_q   ? ~(avec_q   & as) : 1'bz;
assign BERR_n   = berr_q   ? ~(berr_q   & as) : 1'bz;

assign BUS_RD_n   = ~(rd_q & as);
assign BUS_WR_n   = ~(wr_q & ~DS_n);          // write data valid while DS_n low
assign IDE_DIOR_n = ~(ior_q & as);
assign IDE_DIOW_n = ~(iow_q & as);

// ---------------------------------------------------------------- IDE address / chip selects (ATA t1, t9)
// CS0/CS1 and DA2:0 are loaded once per bus cycle, at R2 (cnt 0 -> 1: the decode has been settled for >= 1
// clock), and held after the cycle: CS0/CS1 clear at the edge after the first edge that sampled AS_n high
// (>= ~40 ns after DIOx negates) or at the next cycle's load; DA only changes at the next IDE cycle's load.
// Neither the load nor the clear/hold terms switch on the AS_n pin itself at the AS-rising edge. The load enable is
// act & ~ld_q & ~AS_n: it is already 0 before AS_n rises, and when AS_n rises the direct AS_n literal (one pass)
// holds it at 0 while the asynchronous clears of act/ld_q propagate (AR -> Q -> feedback). The Rev A.1 draft
// used "every edge while AS_n low": that enable switched at the AS-rising edge and the timed sim (with derated
// delays) showed a static hazard clearing CS 3.7 ns after DIOR rose (t9 < 20).
// The IDE data buffers (IDE_BUF_EN_n) are enabled from R2 as well and cleared asynchronously by AS_n.
reg ide_cs0_q, ide_cs1_q, idle1, ide_buf_q, ld_q;
wire ide_ld = act & ~ld_q & ~AS_n;           // true at R2 only
reg [2:0] ide_da_q;
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) begin ide_cs0_q <= 1'b0; ide_cs1_q <= 1'b0; idle1 <= 1'b1; ide_da_q <= 3'd0; end
    else begin
        idle1 <= AS_n;
        if (ide_ld) begin
            ide_cs0_q <= ide0_sp; ide_cs1_q <= ide1_sp;
            if (ide_sp) ide_da_q <= AL;
        end else if (idle1) begin          // AS_n was high at the previous edge (no AS_n literal: no hazard)
            ide_cs0_q <= 1'b0; ide_cs1_q <= 1'b0;
        end
    end
always @(posedge CLK or posedge cyc_clr)
    if (cyc_clr) begin ide_buf_q <= 1'b0; ld_q <= 1'b0; end
    else begin         ide_buf_q <= act & ide_sp; ld_q <= act; end
assign IDE_CS0_n    = ~ide_cs0_q;
assign IDE_CS1_n    = ~ide_cs1_q;
assign IDE_BUF_EN_n = ~(ide_buf_q & as);   // registered assert (glitch-free), direct AS_n term for a fast release
assign {IDE_DA2, IDE_DA1, IDE_DA0} = ide_da_q;

// ---------------------------------------------------------------- 100 Hz timer + shared reset stretch
reg  [TW-1:0] div;
wire tick = (div == TIMER_DIV - 1);
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) div <= 0;
    else            div <= tick ? 0 : div + 1'b1;

// debounced buttons: sampled at 100 Hz, two consecutive low samples = pressed
reg [1:0] nmi_sh, wrst_sh;
reg       nmi_prev;
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) begin nmi_sh <= 2'b11; wrst_sh <= 2'b11; nmi_prev <= 1'b0; end
    else if (tick) begin
        nmi_sh  <= {nmi_sh[0], NMI_BTN_n};
        wrst_sh <= {wrst_sh[0], WARM_RST_BTN_n};
        nmi_prev <= (nmi_sh == 2'b00);
    end
wire nmi_press  = tick & (nmi_sh == 2'b00) & ~nmi_prev;   // new press (edge)
wire warm_press = (wrst_sh == 2'b00);

// warm reset: hold RESET_n/HALT_n for 1024..2047 clocks using div[9:0] (spec 7.2)
reg warm_rst, warm_armed;
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) begin warm_rst <= 1'b0; warm_armed <= 1'b0; end
    else if (warm_press & ~warm_rst) begin warm_rst <= 1'b1; warm_armed <= 1'b0; end
    else if (warm_rst) begin
        if (div[9:0] == 10'd0)                  warm_armed <= 1'b1;
        else if (warm_armed & (div[9:0] == 10'h3FF) & ~warm_press) begin
            warm_rst <= 1'b0; warm_armed <= 1'b0;
        end
    end

// ---------------------------------------------------------------- control registers (F003_0000, write-only)
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) begin
        timer_en <= 1'b0; timer_pend <= 1'b0; user_led <= 1'b0; flash_we <= 1'b0;
        overlay <= 1'b1; nmi_pend <= 1'b0;
    end else begin
        // timer
        if (reg_wr & (ia == 3'd0)) timer_en <= 1'b1;
        if (reg_wr & (ia == 3'd1)) timer_en <= 1'b0;
        if (tick & timer_en)                                   timer_pend <= 1'b1;
        else if ((reg_wr & (ia == 3'd2)) | (iack_hit & (ia == 3'd6))) timer_pend <= 1'b0;
        if (reg_wr & (ia == 3'd3)) user_led <= 1'b1;
        if (reg_wr & (ia == 3'd4)) user_led <= 1'b0;
        if (reg_wr & (ia == 3'd6)) flash_we <= 1'b1;
        if (reg_wr & (ia == 3'd7)) flash_we <= 1'b0;
        // overlay: set by warm reset, cleared by first E-region access or register write
        if (warm_rst)                                   overlay <= 1'b1;
        else if ((as & rom_nat) | (reg_wr & (ia == 3'd5))) overlay <= 1'b0;
        // NMI: edge from the debounced button, held until level-7 IACK
        if (nmi_press)                         nmi_pend <= 1'b1;
        else if (iack_hit & (ia == 3'd7))      nmi_pend <= 1'b0;
        if (warm_rst) begin flash_we <= 1'b0; timer_en <= 1'b0; timer_pend <= 1'b0; end
    end

// ---------------------------------------------------------------- interrupt priority encoder (registered, spec 3.5)
reg [2:0] ipl;
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) ipl <= 3'd0;
    else ipl <= nmi_pend     ? 3'd7 :
                timer_pend   ? 3'd6 :
                ~DUART_INT_n ? 3'd5 :
                ~NIC_INT_n   ? 3'd4 :
                IDE_INTRQ    ? 3'd3 :
                ~EXP_INT_n   ? 3'd2 : 3'd0;
assign {IPL2_n, IPL1_n, IPL0_n} = ~ipl;

// ---------------------------------------------------------------- reset outputs (spec 7.2)
wire glue_rst = ~PWR_RST_n | warm_rst;
// Open-drain emulation (external 1k pull-ups). The data input is written as
// ~glue_rst rather than 1'b0 because fit1508 v1918 aborts with "INTERNAL
// ERROR" when an output/OE is fed from a constant (GND) net.
assign RESET_n      = glue_rst ? ~glue_rst : 1'bz;
assign HALT_n       = glue_rst ? ~glue_rst : 1'bz;
wire   any_rst      = ~RESET_n;                   // PWR, warm or CPU RESET instruction
assign PERIPH_RST_n = ~any_rst;
assign DUART_RST    =  any_rst;

// ---------------------------------------------------------------- halted detector (STATUS_n low > 4 clocks)
reg [2:0] st_cnt;
always @(posedge CLK or negedge PWR_RST_n)
    if (!PWR_RST_n) st_cnt <= 3'd0;
    else if (STATUS_n) st_cnt <= 3'd0;
    else if (st_cnt != 3'd7) st_cnt <= st_cnt + 3'd1;
assign HALT_LED_n = ~(st_cnt == 3'd7);
assign LED_n      = ~user_led;


// ---------------------------------------------------------------- reserved SPI master pins (Rev B)
// SPI_HW_SCK/MOSI/MISO: pins 46/48/49 behind open solder jumpers (not in the Rev A logic).

endmodule
