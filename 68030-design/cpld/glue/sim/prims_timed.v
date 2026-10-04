`timescale 1ns/1ps
// Timed models of the fit1508 timing-model primitives for the glue timed post-fit sim (delays from sdf2v.py).
// Gates use TRANSPORT delays (non-blocking intra-assignment delay), so a runt/glitch produced by unequal path
// delays propagates to the pins instead of being swallowed (the DRAM sim uses inertial delays).
// +derate: every instance scales its delay by a random factor in [tb.dmin, 1.0] (default 0.5; +dmin=<pct>),
// a stand-in for the unspecified minimum delays of the ATF1508AS (datasheet gives maxima only) [ASSUMPTION].
// The global clock path (CLK pin -> register CLK inputs, marked ND=1 by sdf2v.py) is not derated, so the
// derating does not invent register-to-register clock skew.
// The flip-flop checks setup/hold (and AR-release recovery, using tSU) and on a violation resolves to a random
// choice of old/new value (crude metastability model) and logs it.
`define DERATE(T,t) real t; initial begin t = T; #0.001; if ($test$plusargs("derate") && ND == 0) t = T*(tb.dmin + (1.0-tb.dmin)*($unsigned($random(tb.sd))%1001)/1000.0); end
module AND1(output reg Q, input A1); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1) Q <= #(tp) A1; initial begin #0.002; Q <= #(tp) A1; end endmodule
module OR1(output reg Q, input A1); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1) Q <= #(tp) A1; initial begin #0.002; Q <= #(tp) A1; end endmodule
module AND2(output reg Q, input A1, A2); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2) Q <= #(tp) A1 & A2; initial begin #0.002; Q <= #(tp) A1 & A2; end endmodule
module OR2(output reg Q, input A1, A2); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2) Q <= #(tp) A1 | A2; initial begin #0.002; Q <= #(tp) A1 | A2; end endmodule
module AND3(output reg Q, input A1, A2, A3); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3) Q <= #(tp) A1 & A2 & A3; initial begin #0.002; Q <= #(tp) A1 & A2 & A3; end endmodule
module OR3(output reg Q, input A1, A2, A3); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3) Q <= #(tp) A1 | A2 | A3; initial begin #0.002; Q <= #(tp) A1 | A2 | A3; end endmodule
module AND4(output reg Q, input A1, A2, A3, A4); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4) Q <= #(tp) A1 & A2 & A3 & A4; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4; end endmodule
module OR4(output reg Q, input A1, A2, A3, A4); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4) Q <= #(tp) A1 | A2 | A3 | A4; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4; end endmodule
module AND5(output reg Q, input A1, A2, A3, A4, A5); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5) Q <= #(tp) A1 & A2 & A3 & A4 & A5; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5; end endmodule
module OR5(output reg Q, input A1, A2, A3, A4, A5); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5) Q <= #(tp) A1 | A2 | A3 | A4 | A5; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5; end endmodule
module AND6(output reg Q, input A1, A2, A3, A4, A5, A6); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6; end endmodule
module OR6(output reg Q, input A1, A2, A3, A4, A5, A6); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6; end endmodule
module AND7(output reg Q, input A1, A2, A3, A4, A5, A6, A7); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7; end endmodule
module OR7(output reg Q, input A1, A2, A3, A4, A5, A6, A7); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7; end endmodule
module AND8(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8; end endmodule
module OR8(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8; end endmodule
module AND9(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9; end endmodule
module OR9(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9; end endmodule
module AND10(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10; end endmodule
module OR10(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10; end endmodule
module AND11(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11; end endmodule
module OR11(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11; end endmodule
module AND12(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12; end endmodule
module OR12(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12; end endmodule
module AND13(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13; end endmodule
module OR13(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13; end endmodule
module AND14(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14; end endmodule
module OR14(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14; end endmodule
module AND15(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15; end endmodule
module OR15(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15; end endmodule
module AND16(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15 or A16) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16; end endmodule
module OR16(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15 or A16) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16; end endmodule
module AND17(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15 or A16 or A17) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16 & A17; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16 & A17; end endmodule
module OR17(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15 or A16 or A17) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17; end endmodule
module AND18(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15 or A16 or A17 or A18) Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16 & A17 & A18; initial begin #0.002; Q <= #(tp) A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16 & A17 & A18; end endmodule
module OR18(output reg Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2 or A3 or A4 or A5 or A6 or A7 or A8 or A9 or A10 or A11 or A12 or A13 or A14 or A15 or A16 or A17 or A18) Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17 | A18; initial begin #0.002; Q <= #(tp) A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17 | A18; end endmodule
module XOR2(output reg Q, input A1, A2); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A1 or A2) Q <= #(tp) A1 ^ A2; initial begin #0.002; Q <= #(tp) A1 ^ A2; end endmodule
module INV(output reg QN, input A); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial QN = 1'b1; always @(A) QN <= #(tp) ~A; initial begin #0.002; QN <= #(tp) ~A; end endmodule
module BUF(output reg Q, input A); parameter real TP = 0; parameter ND = 0; `DERATE(TP,tp) initial Q = 1'b0; always @(A) Q <= #(tp) A; initial begin #0.002; Q <= #(tp) A; end endmodule
module TRI(output Q, input A, input EN);
parameter real TA = 0, TEN = 0; parameter ND = 0; `DERATE(TA,ta) `DERATE(TEN,ten)
reg a_d = 1'b0, en_d = 1'b0;
always @(A) a_d <= #(ta) A; initial begin #0.002; a_d <= #(ta) A; end
always @(EN) en_d <= #(ten) EN; initial begin #0.002; en_d <= #(ten) EN; end
assign Q = en_d ? a_d : 1'bz;
endmodule
module BIBUF(output Q, input A, input EN, inout PAD);
parameter real TA = 0, TEN = 0; parameter ND = 0; `DERATE(TA,ta) `DERATE(TEN,ten)
reg a_d = 1'b0, en_d = 1'b0;
always @(A) a_d <= #(ta) A; initial begin #0.002; a_d <= #(ta) A; end
always @(EN) en_d <= #(ten) EN; initial begin #0.002; en_d <= #(ten) EN; end
assign PAD = en_d ? a_d : 1'bz;
endmodule
module DFFEARS(output reg Q, input D, CLK, AR, AS, CE);
parameter real TCQ = 0, TAR = 0, TAS = 0, TSU = 0, THD = 0; parameter ND = 0;
`DERATE(TCQ,tcq) `DERATE(TAR,tar) `DERATE(TAS,tas)
real tD = -1.0e9, tC = -1.0e9, tRel = -1.0e9;
integer nsu = 0, nhd = 0;
reg nv;
initial Q = 1'b0;                       // ATF15xx registers power up cleared
always @(D or CE) begin
    tD = $realtime;
    if ($realtime - tC < THD && $realtime > 1.0 && !AR && !AS) begin
        nhd = nhd + 1; tb.n_hold = tb.n_hold + 1;
        if (nhd <= 3) $display("%t TIMING HOLD %m (D changed %.2f ns after CLK)", $realtime, $realtime - tC);
    end
end
always @(negedge AR or negedge AS) tRel = $realtime;
always @(posedge CLK) begin
    tC = $realtime;
    if (!AR && !AS && CE) begin
        nv = D;
        if (($realtime - tD < TSU || $realtime - tRel < TSU) && $realtime > 1.0) begin
            nsu = nsu + 1; tb.n_setup = tb.n_setup + 1;
            if (nsu <= 3) $display("%t TIMING SETUP/RECOVERY %m (D %.2f / AR,AS release %.2f ns before CLK)", $realtime, $realtime - tD, $realtime - tRel);
            if ($random(tb.sd) & 1) nv = Q;
        end
        Q <= #(tcq) nv;
    end
end
always @(posedge AR) Q <= #(tar) 1'b0;
always @(posedge AS) Q <= #(tas) 1'b1;
endmodule
