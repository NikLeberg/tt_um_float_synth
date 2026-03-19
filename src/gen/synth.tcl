# SPDX-License-Identifier: MIT

yosys -import

# Load VHDL design into Yosys.
ghdl --std=08 --no-formal -gN_STAGES=$::env(N_STAGES) $::env(TOP)

# Do a generic but full synthesis.
synth -flatten

# Legalize FFs for ABC.
dfflegalize -cell \$_DFF_P_ 0

# Invoke ABC with exposed FFs and run customized retiming script.
abc -dff -script retime.abc
opt -full -purge
stat

write_json dump.json

# Save to synthesized Verilog netlist.
write_verilog $::env(TOP).v
