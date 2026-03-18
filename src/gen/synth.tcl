# SPDX-License-Identifier: MIT

yosys -import

# Load VHDL design into Yosys.
ghdl --std=08 --no-formal -gN_STAGES=$::env(N_STAGES) $::env(TOP)

# Do some minimal optimization.
opt -full -purge
wreduce
opt -full -purge

# Save to pre processed Verilog.
write_verilog $::env(TOP).v
