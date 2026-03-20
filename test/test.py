# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

from fp8_ref_model import fp8_mul
from scoreboard import Scoreboard

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PIPELINE_DEPTH = 8+1 # number of flip-flop stages in the DUT


# ---------------------------------------------------------------------------
# Helper coroutines
# ---------------------------------------------------------------------------

async def reset_dut(dut):
    """Do a reset cycle of the DUT and drive all inputs to zero.

    Reset is asserted for PIPELINE_DEPTH cycles, followed by a cycle with no
    asserted reset.
    """
    # -- Reset --
    dut._log.info("Reset")
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await dut.clk.rising_edge

async def monitor_outputs(dut, scoreboard, total_inputs):
    """Sample DUT output every cycle, starting after the pipeline has filled.

    Waits PIPELINE_DEPTH cycles for the first valid output, then checks
    one result per cycle for all total_inputs cycles.
    """
    # Wait for the pipeline to fill before checking anything
    await ClockCycles(dut.clk, PIPELINE_DEPTH)

    for _ in range(total_inputs):
        await dut.clk.rising_edge
        scoreboard.check(dut.uo_out.value)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_fp8_mul_smoke(dut):
    dut._log.info("Start fp8 multiplier smoke test")

    # Use https://sw23.github.io/fp-conv/ to generate hex values.
    # Settings: Sign=True, Exponent=4, Mantissa=3, Has Inf=False, Has NaN=False
    test_vectors = [
        #  a     b     y
        (0x00, 0x00, 0x00), #  0.0 *  0.0 =   0.0
        (0x00, 0x38, 0x00), #  0.0 *  1.0 =   0.0
        (0x38, 0x00, 0x00), #  1.0 *  0.0 =   0.0
        (0x38, 0x38, 0x38), #  1.0 *  1.0 =   1.0
        (0x30, 0x30, 0x28), #  0.5 *  0.5 =   0.25
        (0x40, 0x44, 0x4c), #  2.0 *  3.0 =   6.0
        (0xc4, 0xc0, 0x4c), # -3.0 * -2.0 =   6.0
        (0x4a, 0xca, 0xdc), #  5.0 * -5.0 = -24.0 (instead of -25.0)
        (0x4e, 0xc0, 0xd6), #  7.0 * -2.0 = -14.0
        (0xc0, 0x4e, 0xd6), # -7.0 *  2.0 = -14.0
        (0x50, 0x50, 0x68), #  8.0 *  8.0 =  64.0

        (0x08, 0x08, 0x00), # 0.015625    * 0.015625 = 0.0 (too small)
        (0x08, 0x38, 0x08), # 0.015625    * 1.0      = 0.015625
        (0x08, 0x30, 0x04), # 0.015625    * 0.5      = 0.0078125
        (0x01, 0x38, 0x01), # 0.001953125 * 1.0      = 0.001953125
    ]

    async def _drive_inputs(dut, scoreboard, test_vectors):
        """Drive a few selected input combinations.

        Also pushes the expected result into the scoreboard on every cycle
        so the monitor can check outputs as they emerge from the pipeline.
        """

        for i in range(len(test_vectors)):
            await dut.clk.rising_edge
            a, b, y = test_vectors[i]
            dut.ui_in.value  = a
            dut.uio_in.value = b
            expected = fp8_mul(a, b)
            scoreboard.enqueue(a, b, y)

    # -- Clock --
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # -- Reset --
    await reset_dut(dut)

    # -- Run --
    dut._log.info("Driving a small set of input combinations")
    scoreboard   = Scoreboard(dut)

    # Launch driver and monitor as concurrent coroutines
    driver_task  = cocotb.start_soon(_drive_inputs(dut, scoreboard, test_vectors))
    monitor_task = cocotb.start_soon(monitor_outputs(dut, scoreboard, len(test_vectors)))

    # Wait for both to complete
    await driver_task
    await monitor_task

    # -- Results --
    scoreboard.finalise()
    dut._log.info("fp8 multiplier smoke test complete")


# ---------------------------------------------------------------------------
# Exhaustive test
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_fp8_mul_exhaustive(dut):
    dut._log.info("Start fp8 multiplier exhaustive test")

    async def _drive_inputs(dut, scoreboard):
        """Drive all 256x256 input combinations, one pair per clock cycle.

        Also pushes the expected result into the scoreboard on every cycle
        so the monitor can check outputs as they emerge from the pipeline.
        """
        for a in range(256):
            for b in range(256):
                await dut.clk.rising_edge
                dut.ui_in.value  = a
                dut.uio_in.value = b
                expected = fp8_mul(a, b)
                scoreboard.enqueue(a, b, expected)

    # -- Clock --
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # -- Reset --
    await reset_dut(dut)

    # -- Run --
    dut._log.info("Driving all 256x256 input combinations")
    scoreboard   = Scoreboard(dut)
    total_inputs = 256 * 256    # 65 536

    # Launch driver and monitor as concurrent coroutines
    driver_task  = cocotb.start_soon(_drive_inputs(dut, scoreboard))
    monitor_task = cocotb.start_soon(monitor_outputs(dut, scoreboard, total_inputs))

    # Wait for both to complete
    await driver_task
    await monitor_task

    # -- Results --
    scoreboard.finalise()
    dut._log.info("fp8 multiplier exhaustive test complete")
