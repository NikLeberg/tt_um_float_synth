# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

from fp8_ref_model import fp8_mul
from scoreboard import Scoreboard

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PIPELINE_DEPTH = 8+1 # number of flip-flop stages in the DUT, update if RTL changes


# ---------------------------------------------------------------------------
# Helper coroutines
# ---------------------------------------------------------------------------

async def drive_inputs(dut, scoreboard):
    """Drive all 256x256 input combinations, one pair per clock cycle.

    Also pushes the expected result into the scoreboard on every cycle
    so the monitor can check outputs as they emerge from the pipeline.
    """
    for a in range(256):
        for b in range(256):
            await RisingEdge(dut.clk)
            dut.ui_in.value  = a
            dut.uio_in.value = b
            expected = fp8_mul(a, b)
            scoreboard.enqueue(a, b, expected)


async def monitor_outputs(dut, scoreboard, total_inputs):
    """Sample DUT output every cycle, starting after the pipeline has filled.

    Waits PIPELINE_DEPTH cycles for the first valid output, then checks
    one result per cycle for all total_inputs cycles.
    """
    # Wait for the pipeline to fill before checking anything
    await ClockCycles(dut.clk, PIPELINE_DEPTH)

    for _ in range(total_inputs):
        await RisingEdge(dut.clk)
        scoreboard.check(dut.uo_out.value)


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_fp8_mul_exhaustive(dut):
    dut._log.info("Start fp8 multiplier exhaustive test")

    # -- Clock --
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # -- Reset --
    dut._log.info("Reset")
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)   # one clean cycle after reset release

    # -- Run --
    dut._log.info("Driving all 256x256 input combinations")
    scoreboard   = Scoreboard(dut)
    total_inputs = 256 * 256    # 65 536

    # Launch driver and monitor as concurrent coroutines
    driver_task  = cocotb.start_soon(drive_inputs(dut, scoreboard))
    monitor_task = cocotb.start_soon(monitor_outputs(dut, scoreboard, total_inputs))

    # Wait for both to complete
    await driver_task
    await monitor_task

    # Drain the remaining pipeline cycles so the last outputs are checked
    await ClockCycles(dut.clk, PIPELINE_DEPTH)

    # -- Results --
    scoreboard.finalise()
    dut._log.info("fp8 multiplier exhaustive test complete")
