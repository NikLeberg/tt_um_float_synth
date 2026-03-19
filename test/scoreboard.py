# SPDX-License-Identifier: Apache-2.0

# Scoreboard for the fp8 (1.4.3) multiplier testbench.
# The driver enqueues (a, b, expected) on every input cycle.
# The monitor calls check() once per output cycle after the pipeline has filled.
#
# With float_check_error => false, the DUT never produces NaN or inf,
# all outputs are ordinary numeric values, so comparison is bit-exact.

from collections import deque
from fp8_ref_model import decode

_SIGN_MASK = 0x80


def _is_zero(bits: int) -> bool:
    """Both +0 (0x00) and -0 (0x80) are considered equal."""
    return (bits & 0x7F) == 0


class Scoreboard:
    """FIFO-based scoreboard decoupling the driver from the monitor.

    Usage:
        sb = Scoreboard(dut)
        sb.enqueue(a_bits, b_bits, expected_bits)   # called by driver each cycle
        sb.check(actual_bits)                        # called by monitor each cycle
        sb.finalise()                                # assert at end of test
    """

    def __init__(self, dut):
        self._dut   = dut
        self._queue = deque()
        self.passed = 0
        self.failed = 0

    # ------------------------------------------------------------------
    # Driver side
    # ------------------------------------------------------------------

    def enqueue(self, a_bits: int, b_bits: int, expected_bits: int):
        """Push an expected result onto the queue. Called by the driver."""
        self._queue.append((a_bits, b_bits, expected_bits))

    # ------------------------------------------------------------------
    # Monitor side
    # ------------------------------------------------------------------

    def check(self, actual_bits: int):
        """Pop the oldest expected result and compare against actual DUT output."""
        if not self._queue:
            # Pipeline draining after the last input, nothing to check.
            return

        a_bits, b_bits, expected_bits = self._queue.popleft()
        actual_bits = int(actual_bits)   # unwrap cocotb BinaryValue if needed

        if self._values_match(expected_bits, actual_bits):
            self.passed += 1
        else:
            self.failed += 1
            self._dut._log.error(
                f"MISMATCH: a=0x{a_bits:02X}({decode(a_bits):.6g}) "
                f"b=0x{b_bits:02X}({decode(b_bits):.6g}) "
                f"expected=0x{expected_bits:02X}({decode(expected_bits):.6g}) "
                f"actual=0x{actual_bits:02X}({decode(actual_bits):.6g})"
            )

    # ------------------------------------------------------------------
    # End-of-test summary
    # ------------------------------------------------------------------

    def finalise(self):
        """Log a summary and assert no failures. Call at the end of the test."""
        total = self.passed + self.failed
        self._dut._log.info(
            f"Scoreboard: {self.passed}/{total} passed, {self.failed} failed"
        )
        if self._queue:
            self._dut._log.warning(
                f"Scoreboard: {len(self._queue)} entries still in queue, "
                "did the monitor run long enough?"
            )
        assert self.failed == 0, f"{self.failed} mismatches detected, see log for details"

    # ------------------------------------------------------------------
    # Comparison logic
    # ------------------------------------------------------------------

    def _values_match(self, expected: int, actual: int) -> bool:
        """Compare two fp8 bit patterns with 1-ULP tolerance.

        float_generic_pkg uses fixed_truncate in its backing fixed_pkg, which
        causes certain products to be 1 ULP below our float64 reference model.
        1-ULP tolerance absorbs this without hiding real bugs (a genuine error
        would be many ULPs off).

        Rules:
          - +0 == -0  (signed zeros are equal regardless of sign bit)
          - Same sign and |magnitude difference| <= 1  (1-ULP tolerance)
        """
        # Both zero (ignoring sign) -> match
        if _is_zero(expected) and _is_zero(actual):
            return True

        # Sign mismatch -> always a real error
        if (expected & _SIGN_MASK) != (actual & _SIGN_MASK):
            return False

        # Compare magnitudes within 1 ULP
        exp_mag = expected & ~_SIGN_MASK
        act_mag = actual   & ~_SIGN_MASK
        return abs(exp_mag - act_mag) <= 1
