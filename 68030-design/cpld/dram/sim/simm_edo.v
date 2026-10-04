`timescale 1ns/1ps
// Behavioural 72-pin 60 ns EDO SIMM (Micron MT8D432/MT16D832-6 X, datasheet timing table) with timing checks.
// Two sides: side 0 = RAS0 (DQ1-16) + RAS2 (DQ17-32), side 1 = RAS1 + RAS3.  CASn = byte lane n (CAS0 = DQ1-8
// = D7:0 ... CAS3 = DQ25-32 = D31:24).  OE is tied low inside the module -> early write only.
// Memory is sparse: index = {side, row[3:0], col[9:0]} (the testbench keeps its addresses in that space and
// separately checks the latched row/column against the spec 5.2 mapping via exp_row/exp_col).
module simm_edo(
    input  [11:0] MA,
    input  RAS0_n, RAS1_n, RAS2_n, RAS3_n,
    input  CAS0_n, CAS1_n, CAS2_n, CAS3_n,
    input  WE_n,
    inout  [31:0] DQ
);
// EDO -6 (ns)
real tRAC=60, tCAC=15, tAA=30, tRCD=14, tRP=40, tRASmin=60, tRASmax=10000, tCASmin=10, tCP=10;
real tASR=0, tRAH=10, tASC=0, tCAH=10, tCSR=5, tCHR=10, tOFF=15, tWCS=0, tWCH=10, tRPC=5;
integer errors=0, n_cbr0=0, n_cbr1=0, n_rd=0, n_wr=0;
real tras_f[0:1], tras_r[0:1], tcas_f[0:3], tcas_r[0:3], tma, twe_f, twe_r;
real ref_last[0:1], ref_maxgap[0:1];
reg  cbr_act[0:1];
reg  ref_ok_check;               // set by the tb when init is over: check refresh gaps from then on
string cah_s;
real min_tRAS, min_tRP, min_tRCD, min_tRAH, min_tASC, min_tCAH, min_tCP, min_tCAS, min_tCSR, min_tCHR, min_tWCS, min_tWCH;
reg  [11:0] row[0:1], col;
reg  row_open[0:1];
reg  col_seen[0:1];              // a CAS fell since RAS fell (for tRAH vs tCAH classification)
reg  [7:0] mem0[0:32767], mem1[0:32767], mem2[0:32767], mem3[0:32767];
reg  [31:0] dout; reg [3:0] den; reg [3:0] dx; real tval[0:3], toff[0:3];   // lane drive enable / lane is X (not yet valid)
integer k;
// expected row/col for the current CPU access (driven by the tb)
reg [11:0] exp_row, exp_col; reg exp_side; reg exp_valid;
real t_rst_rel = 0, t_first_ras = -1; integer n_cbr_before0 = -1, n_cbr_before1 = -1;
initial begin
    for (k=0;k<2;k=k+1) begin tras_f[k]=-1e9; tras_r[k]=-1e9; row_open[k]=0; cbr_act[k]=0; ref_last[k]=-1; ref_maxgap[k]=0; col_seen[k]=0; end
    for (k=0;k<4;k=k+1) begin tcas_f[k]=-1e9; tcas_r[k]=-1e9; end
    tma=-1e9; twe_f=-1e9; twe_r=-1e9; den=0; dx=0; dout=0; ref_ok_check=0; exp_valid=0;
    min_tRAS=1e9; min_tRP=1e9; min_tRCD=1e9; min_tRAH=1e9; min_tASC=1e9; min_tCAH=1e9; min_tCP=1e9; min_tCAS=1e9;
    min_tCSR=1e9; min_tCHR=1e9; min_tWCS=1e9; min_tWCH=1e9;
    for (k=0;k<32768;k=k+1) begin mem0[k]=8'hxx; mem1[k]=8'hxx; mem2[k]=8'hxx; mem3[k]=8'hxx; end
end
genvar g;
generate for (g=0; g<4; g=g+1) begin : lane
    assign DQ[8*g+7:8*g] = den[g] ? (dx[g] ? 8'hxx : dout[8*g+7:8*g]) : 8'hzz;
end endgenerate

wire [1:0] ras = {~RAS1_n, ~RAS0_n};
wire [3:0] cas = {~CAS3_n, ~CAS2_n, ~CAS1_n, ~CAS0_n};
task err(input [8*48-1:0] msg, input real v, input real lim);
    begin errors=errors+1; if (errors<40) $display("%t SIMM TIMING ERROR %0s: %0.2f ns (limit %0.2f)", $realtime, msg, v, lim); end
endtask
// RAS pairs must match (RAS0==RAS2, RAS1==RAS3) within 3 ns of each other
always @(RAS0_n or RAS2_n) if (RAS0_n !== RAS2_n) begin #3; if (RAS0_n !== RAS2_n) err("RAS0/RAS2 differ", 3, 0); end
always @(RAS1_n or RAS3_n) if (RAS1_n !== RAS3_n) begin #3; if (RAS1_n !== RAS3_n) err("RAS1/RAS3 differ", 3, 0); end

function [14:0] idx(input s, input [11:0] r, input [11:0] c); idx = {s, r[3:0], c[9:0]}; endfunction

task ras_fall(input integer s);
    real d; begin
    d = $realtime - tras_r[s]; if (d < min_tRP) min_tRP = d; if (d < tRP) err("tRP", d, tRP);
    tras_f[s] = $realtime; col_seen[s] = 0;
    if (t_first_ras < 0) begin t_first_ras = $realtime;
        if ($realtime - t_rst_rel < 100000) err("first RAS < 100 us after reset release", $realtime - t_rst_rel, 100000); end
    if (cas != 0) begin                       // CAS-before-RAS refresh
        cbr_act[s] = 1;
        for (k=0;k<4;k=k+1) if (cas[k]) begin d=$realtime-tcas_f[k]; if (d<min_tCSR) min_tCSR=d; if (d<tCSR) err("tCSR (CBR)",d,tCSR); end
        if (cas != 4'hf) err("CBR with not all CAS low", 0, 0);
        if (WE_n !== 1'b1) err("WE low at CBR RAS fall (WCBR test mode)", 0, 0);
        if (s==0) n_cbr0=n_cbr0+1; else n_cbr1=n_cbr1+1;
        if (ref_last[s] >= 0 && ref_ok_check) begin d=$realtime-ref_last[s]; if (d>ref_maxgap[s]) ref_maxgap[s]=d; if (d>15625) err("refresh gap (per side)", d, 15625); end
        ref_last[s] = $realtime;
    end else begin
        cbr_act[s] = 0; row_open[s] = 1;
        if (n_cbr_before0 < 0) begin n_cbr_before0 = n_cbr0; n_cbr_before1 = n_cbr1;
            if (n_cbr0 < 8 || n_cbr1 < 8) err("< 8 init refresh cycles per side before first access", n_cbr0 < n_cbr1 ? n_cbr0 : n_cbr1, 8); end
        d = $realtime - tma; if (d < tASR) err("tASR", d, tASR);
        row[s] = MA;
        if (exp_valid) begin
            if (s !== exp_side) begin err("wrong side (RAS) for the address", 0, 0); end
            if (MA !== exp_row) begin err("row address mismatch", 0, 0); $display("   row %h exp %h", MA, exp_row); end
        end else err("normal RAS cycle outside a DRAM access", 0, 0);
    end
    end
endtask
task ras_rise(input integer s);
    real d; begin
    d = $realtime - tras_f[s]; if (tras_f[s] > 0) begin if (d<min_tRAS) min_tRAS=d; if (d < tRASmin) err("tRAS min", d, tRASmin); if (d > tRASmax) err("tRAS max", d, tRASmax); end
    // CBR: a CAS still low when RAS rises has been held at least this long after RAS fell (tCHR)
    if (cbr_act[s]) for (k=0;k<4;k=k+1) if (cas[k]) begin if (d<min_tCHR) min_tCHR=d; if (d<tCHR) err("tCHR", d, tCHR); end
    tras_r[s] = $realtime; row_open[s] = 0;
    end
endtask
always @(negedge RAS0_n) ras_fall(0);
always @(negedge RAS1_n) ras_fall(1);
always @(posedge RAS0_n) ras_rise(0);
always @(posedge RAS1_n) ras_rise(1);

// data output control: lane on while (RAS low or CAS low) after a read CAS; off tOFF after both high
task cas_fall(input integer i);
    real d, tv; integer s; begin
    d = $realtime - tcas_r[i]; if (d<min_tCP) min_tCP=d; if (d < tCP) err("tCP", d, tCP);
    tcas_f[i] = $realtime;
    s = (ras[0]) ? 0 : (ras[1]) ? 1 : -1;
    if (s >= 0 && !cbr_act[s]) begin
        d = $realtime - tras_f[s]; if (d<min_tRCD) min_tRCD=d; if (d < tRCD) err("tRCD", d, tRCD);
        d = $realtime - tma; if (d<min_tASC) min_tASC=d; if (d < tASC) err("tASC", d, tASC);
        col = MA; col_seen[s] = 1;
        if (exp_valid && MA !== exp_col) begin err("column address mismatch", 0, 0); $display("   col %h exp %h", MA, exp_col); end
        if (!WE_n) begin                                  // early write
            d = $realtime - twe_f; if (d<min_tWCS) min_tWCS=d; if (d < tWCS) err("tWCS (early write)", d, tWCS);
            if (^DQ[8*i+:8] === 1'bx) err("write data not valid at CAS fall", 0, 0);
            case (i) 0: mem0[idx(s,row[s],MA)] = DQ[7:0]; 1: mem1[idx(s,row[s],MA)] = DQ[15:8];
                     2: mem2[idx(s,row[s],MA)] = DQ[23:16]; 3: mem3[idx(s,row[s],MA)] = DQ[31:24]; endcase
            n_wr = n_wr + 1;
        end else begin                                    // read: X until tRAC/tCAC/tAA all met
            tv = tras_f[s] + tRAC; if ($realtime + tCAC > tv) tv = $realtime + tCAC; if (tma + tAA > tv) tv = tma + tAA;
            case (i) 0: dout[7:0] = mem0[idx(s,row[s],MA)]; 1: dout[15:8] = mem1[idx(s,row[s],MA)];
                     2: dout[23:16] = mem2[idx(s,row[s],MA)]; 3: dout[31:24] = mem3[idx(s,row[s],MA)]; endcase
            den[i] = 1; dx[i] = 1; tval[i] = tv; toff[i] = 1e18; n_rd = n_rd + 1;
        end
    end
    end
endtask
task cas_rise(input integer i);
    real d; begin
    d = $realtime - tcas_f[i]; if (d<min_tCAS) min_tCAS=d; if (d < tCASmin) err("tCAS", d, tCASmin);
    if ((ras[0] && cbr_act[0]) || (ras[1] && cbr_act[1])) begin
        if (ras[0] && cbr_act[0]) begin d=$realtime-tras_f[0]; if (d<min_tCHR) min_tCHR=d; if (d<tCHR) err("tCHR", d, tCHR); end
        if (ras[1] && cbr_act[1]) begin d=$realtime-tras_f[1]; if (d<min_tCHR) min_tCHR=d; if (d<tCHR) err("tCHR", d, tCHR); end
    end
    tcas_r[i] = $realtime;
    end
endtask
always @(negedge CAS0_n) cas_fall(0);  always @(posedge CAS0_n) cas_rise(0);
always @(negedge CAS1_n) cas_fall(1);  always @(posedge CAS1_n) cas_rise(1);
always @(negedge CAS2_n) cas_fall(2);  always @(posedge CAS2_n) cas_rise(2);
always @(negedge CAS3_n) cas_fall(3);  always @(posedge CAS3_n) cas_rise(3);
// EDO turn-off: tOFF after the later of RAS and CAS goes high
integer kp;
always #0.25 for (kp=0;kp<4;kp=kp+1) begin
    if (den[kp] && dx[kp] && $realtime >= tval[kp]) dx[kp] = 0;
    if (den[kp] && !cas[kp] && ras==0 && toff[kp] > 1e17) toff[kp] = $realtime + tOFF;   // EDO: later of RAS/CAS high
    if (den[kp] && (cas[kp] || ras!=0)) toff[kp] = 1e18;
    if (den[kp] && $realtime >= toff[kp]) begin den[kp]=0; dx[kp]=0; toff[kp] = 1e18; end
end
// address hold checks
always @(MA) begin : mach
    real d; integer s;
    for (s=0;s<2;s=s+1) if (ras[s] && !cbr_act[s] && !col_seen[s]) begin
        d=$realtime-tras_f[s]; if (d<min_tRAH) min_tRAH=d; if (d < tRAH) err("tRAH", d, tRAH); end
    for (s=0;s<4;s=s+1) if (cas[s] && (ras[0]||ras[1]) && !(cbr_act[0]||cbr_act[1])) begin
        d=$realtime-tcas_f[s]; if (d<min_tCAH) min_tCAH=d; if (d < tCAH) err("tCAH", d, tCAH); end
    tma = $realtime;
end
always @(negedge WE_n) twe_f = $realtime;
always @(posedge WE_n) begin : wech
    real d; for (k=0;k<4;k=k+1) if (cas[k] && (ras[0]||ras[1])) begin d=$realtime-tcas_f[k]; if (d<min_tWCH) min_tWCH=d; if (d<tWCH) err("tWCH", d, tWCH); end
    twe_r = $realtime; end
task report;
    begin
    $display("SIMM model: %0d reads, %0d writes (lane strobes), CBR side0 %0d side1 %0d, timing errors %0d", n_rd, n_wr, n_cbr0, n_cbr1, errors);
    if (min_tCAH > 1e8) cah_s = "n/a(col held to CAS high)"; else cah_s = $sformatf("%.1f", min_tCAH);
    $display("  min tRAS %.1f tRP %.1f tRCD %.1f tRAH %.1f tASC %.1f tCAH %s tCP %.1f tCAS %.1f tCSR %.1f tCHR %.1f tWCS %.1f tWCH %.1f",
             min_tRAS,min_tRP,min_tRCD,min_tRAH,min_tASC,cah_s,min_tCP,min_tCAS,min_tCSR,min_tCHR,min_tWCS,min_tWCH);
    $display("  init: first RAS %.1f us after reset release; CBR cycles before first access: side0 %0d side1 %0d", (t_first_ras-t_rst_rel)/1000.0, n_cbr_before0, n_cbr_before1);
    $display("  max refresh gap per side (after init): side0 %.1f ns side1 %.1f ns (limit 15625)", ref_maxgap[0], ref_maxgap[1]);
    end
endtask
endmodule
