`timescale 1ns/1ps
// Behavioural models of the ATF15xx fitter's timing-model primitives (for post-fit sim only)
module AND1(output Q, input A1);
assign Q = A1;
specify
  (A1 => Q) = 0;
endspecify
endmodule
module OR1(output Q, input A1);
assign Q = A1;
specify
  (A1 => Q) = 0;
endspecify
endmodule
module AND2(output Q, input A1, A2);
assign Q = A1 & A2;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
endspecify
endmodule
module OR2(output Q, input A1, A2);
assign Q = A1 | A2;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
endspecify
endmodule
module AND3(output Q, input A1, A2, A3);
assign Q = A1 & A2 & A3;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
endspecify
endmodule
module OR3(output Q, input A1, A2, A3);
assign Q = A1 | A2 | A3;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
endspecify
endmodule
module AND4(output Q, input A1, A2, A3, A4);
assign Q = A1 & A2 & A3 & A4;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
endspecify
endmodule
module OR4(output Q, input A1, A2, A3, A4);
assign Q = A1 | A2 | A3 | A4;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
endspecify
endmodule
module AND5(output Q, input A1, A2, A3, A4, A5);
assign Q = A1 & A2 & A3 & A4 & A5;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
endspecify
endmodule
module OR5(output Q, input A1, A2, A3, A4, A5);
assign Q = A1 | A2 | A3 | A4 | A5;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
endspecify
endmodule
module AND6(output Q, input A1, A2, A3, A4, A5, A6);
assign Q = A1 & A2 & A3 & A4 & A5 & A6;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
endspecify
endmodule
module OR6(output Q, input A1, A2, A3, A4, A5, A6);
assign Q = A1 | A2 | A3 | A4 | A5 | A6;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
endspecify
endmodule
module AND7(output Q, input A1, A2, A3, A4, A5, A6, A7);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
endspecify
endmodule
module OR7(output Q, input A1, A2, A3, A4, A5, A6, A7);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
endspecify
endmodule
module AND8(output Q, input A1, A2, A3, A4, A5, A6, A7, A8);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
endspecify
endmodule
module OR8(output Q, input A1, A2, A3, A4, A5, A6, A7, A8);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
endspecify
endmodule
module AND9(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
endspecify
endmodule
module OR9(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
endspecify
endmodule
module AND10(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
endspecify
endmodule
module OR10(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
endspecify
endmodule
module AND11(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
endspecify
endmodule
module OR11(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
endspecify
endmodule
module AND12(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
endspecify
endmodule
module OR12(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
endspecify
endmodule
module AND13(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
endspecify
endmodule
module OR13(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
endspecify
endmodule
module AND14(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
endspecify
endmodule
module OR14(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
endspecify
endmodule
module AND15(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
endspecify
endmodule
module OR15(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
endspecify
endmodule
module AND16(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
  (A16 => Q) = 0;
endspecify
endmodule
module OR16(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
  (A16 => Q) = 0;
endspecify
endmodule
module AND17(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16 & A17;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
  (A16 => Q) = 0;
  (A17 => Q) = 0;
endspecify
endmodule
module OR17(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
  (A16 => Q) = 0;
  (A17 => Q) = 0;
endspecify
endmodule
module AND18(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18);
assign Q = A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9 & A10 & A11 & A12 & A13 & A14 & A15 & A16 & A17 & A18;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
  (A16 => Q) = 0;
  (A17 => Q) = 0;
  (A18 => Q) = 0;
endspecify
endmodule
module OR18(output Q, input A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18);
assign Q = A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17 | A18;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
  (A3 => Q) = 0;
  (A4 => Q) = 0;
  (A5 => Q) = 0;
  (A6 => Q) = 0;
  (A7 => Q) = 0;
  (A8 => Q) = 0;
  (A9 => Q) = 0;
  (A10 => Q) = 0;
  (A11 => Q) = 0;
  (A12 => Q) = 0;
  (A13 => Q) = 0;
  (A14 => Q) = 0;
  (A15 => Q) = 0;
  (A16 => Q) = 0;
  (A17 => Q) = 0;
  (A18 => Q) = 0;
endspecify
endmodule
module XOR2(output Q, input A1, A2);
assign Q = A1 ^ A2;
specify
  (A1 => Q) = 0;
  (A2 => Q) = 0;
endspecify
endmodule
module INV(output QN, input A);
assign QN = ~A;
specify
  (A => QN) = 0;
endspecify
endmodule
module BUF(output Q, input A);
assign Q = A;
specify
  (A => Q) = 0;
endspecify
endmodule
module TRI(output Q, input A, input EN);
assign Q = EN ? A : 1'bz;
specify
  (A => Q) = 0;
  (EN => Q) = 0;
endspecify
endmodule
module BIBUF(output Q, input A, input EN, inout PAD);
assign PAD = EN ? A : 1'bz;
// Q is tied to PAD in the fitter netlist
endmodule
module DFFEARS(output reg Q, input D, CLK, AR, AS, CE);
always @(posedge CLK or posedge AR or posedge AS)
  if (AR) Q <= 1'b0; else if (AS) Q <= 1'b1; else if (CE) Q <= D;
specify
  (posedge CLK => (Q +: D)) = 0;
  (posedge AR => (Q +: 1'b0)) = 0;
  (posedge AS => (Q +: 1'b1)) = 0;
  $setup(D, posedge CLK, 0);
  $hold(posedge CLK, D, 0);
endspecify
endmodule
