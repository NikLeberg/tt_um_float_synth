# SPDX-License-Identifier: Apache-2.0

# Reference model for 8-bit floating point (1.4.3) multiplication.
# Matches the behavior of David Bishop's float_generic_pkg configured as:
#   float_exponent_width => 4
#   float_fraction_width => 3
#   float_round_style    => round_zero  (truncate toward zero)
#   float_denormalize    => true        (subnormals supported)
#   float_check_error    => false       (no NaN/inf special cases, exp=15 is
#                                        treated as an ordinary exponent value)

import math

EXP_BITS        = 4
FRAC_BITS       = 3
BIAS            = (1 << (EXP_BITS - 1)) - 1   # 7
MAX_EXP         = (1 << EXP_BITS) - 1          # 15
MAX_FINITE_BITS = 0x77                          # 0 1110 111 = 240.0 (largest encodable value)


def decode(bits: int) -> float:
    """Decode an 8-bit fp8 (1.4.3) value to a Python float.

    Bit layout:  [7] sign | [6:3] exponent | [2:0] mantissa

    float_check_error => false means exp=15 is NOT treated as inf/NaN.
    All 256 bit patterns decode as ordinary numeric values:

      exp=0  -> subnormal: (-1)^s * 2^(1-BIAS) * 0.frac
      exp>0  -> normal:    (-1)^s * 2^(exp-BIAS) * 1.frac
               (exp=15 gives 2^8 * 1.frac = 256..480, which saturates on re-encode)
    """
    assert 0 <= bits <= 255, "Input must be an 8-bit value"

    sign = (bits >> 7) & 1
    exp  = (bits >> FRAC_BITS) & ((1 << EXP_BITS) - 1)
    frac = bits & ((1 << FRAC_BITS) - 1)

    if exp == 0:
        # zero or subnormal, no implicit leading 1
        mantissa = frac / (1 << FRAC_BITS)
        value = (2 ** (1 - BIAS)) * mantissa
    else:
        # normal, includes exp=15, no special case
        mantissa = 1.0 + frac / (1 << FRAC_BITS)
        value = (2 ** (exp - BIAS)) * mantissa

    return -value if sign else value


def encode(value: float) -> int:
    """Encode a Python float to an 8-bit fp8 (1.4.3) bit pattern.

    Rounding mode: round_zero (truncate toward zero, matching float_generic_pkg).
    Overflow:      saturate to MAX_FINITE_BITS (matching fixed_saturate).
    Subnormals:    supported (float_denormalize=true).
    No NaN/inf output, float_check_error=false means the library never produces them.
    """
    sign = 0
    if math.copysign(1.0, value) < 0:
        sign = 1
        value = -value

    # --- zero ---
    if value == 0.0:
        return sign << 7

    # --- overflow: saturate to largest encodable value (240.0) ---
    # exp=15 values (256..480) are valid inputs but their product can exceed 240,
    # so we saturate. The max representable with exp<=14 is 240.0.
    if value > 240.0:
        return (sign << 7) | MAX_FINITE_BITS

    # --- subnormal range: value < 2^(1-BIAS) = 2^-6 ---
    min_normal = 2.0 ** (1 - BIAS)   # 0.015625
    if value < min_normal:
        frac_real = value / min_normal       # in [0, 1)
        frac = int(frac_real * (1 << FRAC_BITS))  # truncate toward zero
        frac = min(frac, (1 << FRAC_BITS) - 1)
        return (sign << 7) | frac

    # --- normal range ---
    exp_unbiased = math.floor(math.log2(value))
    exp_biased   = exp_unbiased + BIAS

    # Guard: should be covered by overflow check above
    if exp_biased >= MAX_EXP:
        return (sign << 7) | MAX_FINITE_BITS

    # Extract fractional bits, truncating toward zero (round_zero)
    mantissa_real = value / (2.0 ** exp_unbiased)  # in [1.0, 2.0)
    frac_real     = mantissa_real - 1.0             # in [0.0, 1.0)
    frac          = int(frac_real * (1 << FRAC_BITS))
    frac          = min(frac, (1 << FRAC_BITS) - 1)

    return (sign << 7) | (exp_biased << FRAC_BITS) | frac


def fp8_mul(a_bits: int, b_bits: int) -> int:
    """Multiply two fp8 values and return the fp8 result bit pattern."""
    a = decode(a_bits)
    b = decode(b_bits)
    return encode(a * b)


# ---------------------------------------------------------------------------
# Self-tests, run this file directly to verify the model on known values
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    def check(desc, got, expected):
        status = "PASS" if got == expected else "FAIL"
        print(f"  [{status}] {desc}: got 0x{got:02X}, expected 0x{expected:02X}")

    print("=== decode spot checks ===")
    # exp=15 values now decode as normal numbers
    # 0x78 = 0 1111 000: exp=15, frac=0 -> 2^(15-7) * 1.0 = 256.0
    v = decode(0x78)
    print(f"  0x78 decodes to {v} (expected 256.0): {'PASS' if v == 256.0 else 'FAIL'}")
    # 0xFF = 1 1111 111: exp=15, frac=7 -> -2^8 * 1.875 = -480.0
    v = decode(0xFF)
    print(f"  0xFF decodes to {v} (expected -480.0): {'PASS' if v == -480.0 else 'FAIL'}")

    print("\n=== multiplication spot checks ===")
    check("1.0 * 1.0 = 1.0",    fp8_mul(0x38, 0x38), 0x38)
    check("2.0 * 2.0 = 4.0",    fp8_mul(0x40, 0x40), 0x48)
    check("-1.0 * 1.0 = -1.0",  fp8_mul(0xB8, 0x38), 0xB8)
    check("0.0 * 2.0 = 0.0",    fp8_mul(0x00, 0x40), 0x00)
    check("240.0 * 2.0 saturates", fp8_mul(0x77, 0x40), 0x77)

    # exp=15 inputs: 0xFC = 1 1111 100 -> -2^8 * 1.5 = -384.0
    # 0x25 = 0 0100 101: exp=4, frac=5 -> 2^(4-7) * 1.625 = 0.203125
    # product = -384 * 0.203125 = -78.0
    # encode(-78): sign=1, exp=6 (78 is between 64 and 128), frac = (78/64 - 1)*8 = 1.75 truncated = 1
    # -> 1 1101 001 = 0xE9
    check("0xFC * 0x25 = 0xE9", fp8_mul(0xFC, 0x25), 0xE9)

    print("\n=== full round-trip encode(decode(x)) for all 256 values ===")
    # With float_check_error=false, exp=15 values decode to 256..480
    # which are above 240 so they re-encode as saturated (0x77/0xF7), not a round-trip.
    # All exp<15 values should round-trip exactly.
    fails = []
    for b in range(256):
        exp_field = (b >> FRAC_BITS) & 0xF
        if exp_field == MAX_EXP:
            continue   # exp=15 values intentionally don't round-trip (they saturate)
        rt = encode(decode(b))
        if rt != b:
            fails.append((b, rt))
    if fails:
        for orig, got in fails:
            print(f"  [FAIL] 0x{orig:02X} -> 0x{got:02X}")
    else:
        print("  [PASS] all exp<15 values round-trip correctly")
