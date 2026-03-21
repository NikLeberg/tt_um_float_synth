<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Explain how your project works

## How to test

Well, it simply calculates `y = a * b`, but _fast_.

- Input `a` i.e. `ui_in[7:0]` can be driven from either the demo board DIP switches, PMOD connector or from the [TT Commander](commander.tinytapeout.com).
- Input `b` i.e. `uio_in[7:0]` can only be driven from PMOD or TT Commander.
- Output `y` i.e. `uo_out[7:0]` can be observed on the seven segment display. Although the number will not make any sence. Better observe it on PMOD or TT Commander.

As a quick test you may drive `a` and `b` with `0b00110000`, which is _0.5_ in float. The result on `y` should be `0b00101000` or _0.25_ in float.

The data format is a very limited 8-bit floating point number. Known as `1.4.3` or `E4M3`. Meaning it has 1 sign bit, 4 exponent bits and 3 mantissa bits. It can represent numbers from _-480_ to _+480_ with varying accuracy.

|| Sign | Exponent | Mantissa |
|---|---|---|---|
| Bits | 0 | 0000 | 000 |
| `a` mapping | `ui_in[7]` | `ui_in[6:3]` | `ui_in[2:0]` |
| `b` mapping | `uio_in[7]` | `uio_in[6:3]` | `uio_in[2:0]` |
| `y` mapping | `uo_out[7]` | `uo_out[6:3]` | `uo_out[2:0]` |

To save on resources, the underlying `IEEE.float_pkg` has been configured to:
- round towards zero (truncate)
- saturate on overflow (no infinity)
- but nonetheless: handle subnormals

This effectively results in the following representable number ranges:

| Exponent (biased) | Exponent (unbiased) | Range | ULP (Accuracy) |
|---|---|---|---|
|  0 (subnormal) | −6 (fixed) | [0.0, 0.013671875] | 2⁻⁹ = 0.001953125 |
|  1 | −6 | [0.015625, 0.029296875] | 2⁻⁹ = 0.001953125 |
|  2 | −5 | [0.03125, 0.05859375] | 2⁻⁸ = 0.00390625 |
|  3 | −4 | [0.0625, 0.1171875] | 2⁻⁷ = 0.0078125 |
|  4 | −3 | [0.125, 0.234375] | 2⁻⁶ = 0.015625 |
|  5 | −2 | [0.25, 0.46875] | 2⁻⁵ = 0.03125 |
|  6 | −1 | [0.5, 0.9375] | 2⁻⁴ = 0.06250 |
|  7 |  0 | [1.0, 1.875] | 2⁻³ = 0.12500 |
|  8 | +1 | [2.0, 3.75] | 2⁻² = 0.25 |
|  9 | +2 | [4.0, 7.5] | 2⁻¹ = 0.5 |
| 10 | +3 | [8.0, 15.0] | 2⁰ = 1.0 |
| 11 | +4 | [16.0, 30.0] | 2¹ = 2.0 |
| 12 | +5 | [32.0, 60.0] | 2² = 4.0 |
| 13 | +6 | [64.0, 120.0] | 2³ = 8.0 |
| 14 | +7 | [128.0, 240.0] | 2⁴ = 16.0 |
| 15 | +8 | [256.0, 480.0] | 2⁵ = 32.0 |

Of course all the representable values may also be negative. But they have been omitted here for clarity.

To generate a valid number you can use Spencer Williams [Floating Point Number Converter](https://sw23.github.io/fp-conv/). Setup a custom format with: Sign: _True_, Exponent: _4_, Mantissa: _3_, Has Inf: _False_, Has Nan: _False_ and at the very bottom, Rounding Mode: _Toward Zero (truncate)_. Input your desired decimal value and it tells you the binary or hexadecimal representation. You may also fiddle with the bits directly and see what the resulting floating point number is.

![Screenshot of settings for Spence Williams Floating Point Number Converter](fp_conv.png)

As the main goal of the project was to retime the lazily written HDL for optimal delay, the clock can be as high as _100 MHz_. But the poor little IO pads will probably not like that very much. Something like _50 MHz_ should be fine. Use way less (or even single clock it) to see the pipelining in action.
