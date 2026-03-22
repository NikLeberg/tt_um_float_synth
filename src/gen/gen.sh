#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -e
set -x # local command echo

# Restart this script inside docker container with GHDL tooling.
if [ -z "$IN_DOCKER" ]; then
    docker run --rm -it \
        --env IN_DOCKER=1 \
        --volume $(realpath ..):/work \
        --workdir /work/gen \
        --entrypoint bash \
        -u ubuntu \
        ghcr.io/nikleberg/formal:2026-03-09 \
        -c "./gen.sh"

    exit 0
fi

# Analyze VHDL sources.
ghdl -a --std=08 ../vhdl/float8_pkg.vhd
ghdl -a --std=08 ../vhdl/fadd8.vhd
ghdl -a --std=08 ../vhdl/fmul8.vhd

# Synthesize to optimized but highlevel Verilog.
TOP=fadd8 N_STAGES=6 yosys -m ghdl -c synth.tcl
TOP=fmul8 N_STAGES=6 yosys -m ghdl -c synth.tcl
