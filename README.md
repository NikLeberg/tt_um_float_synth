![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Float Synth
This project is based on the Tiny Tapeout [ttihp_verilog-template](https://github.com/TinyTapeout/ttihp-verilog-template) targeting the experimental `IHP0p4` shuttle. Read the [float_synth project documentation](docs/info.md) for more information.


## What is Tiny Tapeout?
Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get your digital and analog designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.


## How To Build

### In the Cloud
Tiny Tapeout is fully integrated into GitHub Actions. You may simply fork this repository and the CI Actions will generate the rest.

### Locally
> [!NOTE]
> The following is based on TTs docs about [local hardening](https://www.tinytapeout.com/guides/local-hardening/) and assume you run this inside a devcontainer with e.g. VsCode.

1. Generate Verilog

    Tiny Tapeout works best with Verilog. But this project is based on VHDL. Run the generator script from `src/gen` which will analyze the designs from `src/vhdl` with GHDL, do some pre-synthesis with Yosys+ABC and output to `src/gen` the (sadly very unreadable) Verilog netlist.

    ```
    cd src/gen
    ./gen.sh
    ```

2. Generate Configs

    This generates the combined librelane configuration from [`src/config.json`](src/config.json) and the IHP26a specific settings.

    ```
    ./tt/tt_tool.py --ihp --create-user-config
    ```

2. Run Librelane

    One command to rule it all. The following will run the _classic_ librelane flow on the design. Any hard errors like e.g. timing violations will stop the flow. The full _run_ will be generated into [`run/wokwi`](run/wokwi) where you may inspect the reports of the various steps.

    ```
    ./tt/tt_tool.py --ihp --harden
    ```


## Links

### Similar Projects:
- My own _bigger brother_ project, also named `float_synth`, but targeting FPGAs: [NikLeberg/float_synth](https://github.com/NikLeberg/float_synth)
- Swiss Army Knife of arithmetic cores: [FloPoCo](https://flopoco.org/)
- On this very same TT shuttle:
  - Systolic array of bfloat16: [Essenceia/Systolic_Array_with_DFT_v2](https://github.com/Essenceia/Systolic_Array_with_DFT_v2)
  - 8-bit SEM floating point multiplier: [DelosReyesJordan/ttihp26a-FP8-SEM-Multiplier](https://github.com/DelosReyesJordan/ttihp26a-FP8-SEM-Multiplier)
  - 8-bit Posit MAC Unit: [RipunjayS109/posit_mac](https://github.com/RipunjayS109/posit_mac)
  - OCP MXFP8 Streaming MAC Unit: [chatelao/ttihp-fp8-mul](https://github.com/chatelao/ttihp-fp8-mul)

### Further Documentation
- [Tiny Tapeout FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)

## License
[Apache-2.0](LICENSE) © [NikLeberg](https://github.com/NikLeberg).
