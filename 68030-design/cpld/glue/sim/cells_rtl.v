// Behavioural models of the atf15xx_yosys cells.lib cells instantiated directly in glue.v (RTL sim only;
// Yosys reads cells.lib itself). Pin names follow cells.lib.
`timescale 1ns/1ps
module INV  (input A, output QN); assign QN = ~A; endmodule
module AND2 (input A, B, output Q); assign Q = A & B; endmodule
module AND5 (input A, B, C, D, E, output Q); assign Q = A & B & C & D & E; endmodule
module AND6 (input A, B, C, D, E, F, output Q); assign Q = A & B & C & D & E & F; endmodule
module NAND2(input A, B, output QN); assign QN = ~(A & B); endmodule
module NOR3 (input A, B, C, output QN); assign QN = ~(A | B | C); endmodule
