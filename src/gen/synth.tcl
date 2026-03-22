# SPDX-License-Identifier: MIT

yosys -import

# Load VHDL design into Yosys.
ghdl --std=08 --no-formal -gN_STAGES=$::env(N_STAGES) $::env(TOP)

# Do a generic but full synthesis.
synth -flatten

# Legalize FFs for ABC. Only FF with init state 0 and driven by the same "clock
# domain" built from clk+arst+srst can be represented in ABC. Otherwise yosys
# must partition netlist into different clock domains which prevents
# optimization on a global level.
dfflegalize -cell \$_DFF_P_ 0

# Invoke ABC with exposed FFs and run customized retiming script.
abc -dff -script retime.abc
opt -full -purge
stat

# Save to synthesized Verilog netlist.
write_verilog $::env(TOP).v
