/*
 * Copyright (c) 2026 Niklaus Leuenberger
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_float_synth_nikleberg (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Instantiate the 8-bit floating point multiplier
  fmul8 float_multiplier_inst (
    .clk(clk),
    .a(ui_in),
    .b(uio_in),
    .y(uo_out)
  );

  // Set unused bidirectional pins to high-impedance/input mode
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, rst_n, 1'b0};

endmodule
