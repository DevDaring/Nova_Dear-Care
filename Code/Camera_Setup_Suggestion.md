# OVX8B on RDK S100: solving the missing ISP calibration crisis

**The OVX8B stereo cameras fail because the RDK S100's `hobot-camera` v4.0.4 package ships the sensor driver but deliberately excludes all seven ISP calibration libraries — and no public source for these files exists.** This is not a bug but a scoping decision: the S100 chip derives from D-Robotics' Journey 6 automotive platform, and OVX8B (OmniVision OX08B40) is an automotive ADAS sensor whose calibration libraries are only distributed through the commercial J6 SDK under NDA or via camera module vendors like SENSING Intelligence. The most actionable workarounds are switching to the `libovx8b.so` non-standard driver, using CIM raw capture to bypass ISP entirely, or contacting D-Robotics directly for the calibration files. Below is a complete analysis of every avenue investigated.

## Why the calibration libraries are missing — and where they actually live

The RDK S100 officially supports only three MIPI camera sensors: **IMX219, SC230AI, and SC132GS**. OVX8B does not appear anywhere in D-Robotics' compatibility tables, documentation, GitHub repos, or community forums. The Camera Expansion Board documentation at developer.d-robotics.cc explicitly lists only these sensors plus generic GMSL cameras.

The `libovx8bstd.so` driver exists in the package as a carryover from the S100 chip's automotive lineage. The S100 shares the Nash BPU architecture with the Journey 5/6 automotive processors, and the full J6 SDK includes OVX8B support with all calibration libraries. D-Robotics' release notes explicitly distinguish between the open RDK OS (free, for robotics developers) and the "commercial version" that "offers more comprehensive feature support, deeper hardware capability exposure" — the ISP calibration files for automotive sensors fall squarely into the commercial tier.

The calibration library naming reveals the specificity of what's missing. In `lib_CL_OX8GB_L121_067_L.so`, **"CL" and "CW" denote different lens/module configurations** (likely different vendors or FOV types), **"OX8GB"** is the internal sensor code for OX08B40, **"L121" and "A120"** are lens identifiers (probably indicating ~120° FOV variants), **"067"/"065"** are calibration revision numbers, and **"_L"** likely indicates linear mode. Each library contains proprietary ISP tuning data — AWB, AE, CCM, LSC, noise profiles, gamma curves — specific to a particular sensor+lens+module combination. These cannot be fabricated or substituted from another sensor's calibration.

Camera module vendors like **SENSING Intelligence** (sensing-world.com) produce OX08B40+GW5300 ISP GMSL2 modules specifically for Horizon J3/J5 platforms, confirming the calibration data exists within the D-Robotics ecosystem. Yanding also manufactures RD-OX08B-GMSL-Hxx modules for the same platforms. The calibration `.so` files would typically be provided by the camera module manufacturer as part of their integration package.

## Workaround 1: switch to `libovx8b.so` — the most promising quick fix

The system ships two OVX8B drivers: `libovx8bstd.so` (156KB) and `libovx8b.so` (132KB). The **24KB size difference strongly suggests `libovx8b.so` omits the calibration-dependent code path** — it likely uses built-in default ISP parameters or operates in a simplified mode that does not require `dlopen()` of external calibration shared libraries.

To attempt this switch, three approaches exist in order of increasing invasiveness:

- **Modify the camera configuration JSON** (typically under `/etc/hobot/` or a similar path) to reference `libovx8b.so` instead of `libovx8bstd.so`. The `hbn_camera_create()` API reads these configuration files to determine which sensor driver `.so` to load.
- **Symlink replacement**: Rename `libovx8bstd.so` to `libovx8bstd.so.bak` and create a symlink `libovx8bstd.so → libovx8b.so`. This forces the pipeline to load the alternative driver without config changes.
- **Direct rename**: Copy `libovx8b.so` over `libovx8bstd.so` as a last resort.

Image quality with the non-standard driver will likely be degraded (no lens-specific corrections, generic color tuning), but the pipeline should initialize and produce usable frames. This is the fastest path to getting streaming data from the OVX8B sensors.

## Workaround 2: CIM raw capture bypasses ISP entirely

The RDK S100 SDK supports **CIM (Camera Interface Module) direct capture**, which sits before the ISP in the pipeline and outputs raw Bayer data without any ISP processing. This completely sidesteps the `hbn_camera_create()` call and its calibration requirement.

The SDK includes a **`sample_cim` example program** that demonstrates CIM-only streaming. Install it with `apt install hobot-multimedia-samples` (or the S100 equivalent package). The full S100 HBN pipeline is: Serdes → MIPI → **CIM** → ISP → YNR → PYM → GDC → STITCH. By stopping at CIM, you get raw sensor data without any ISP involvement.

Additionally, the SDK documents a **YUV bypass pipeline**: `serdes(yuv) → mipi → cim → pym`, which skips ISP entirely when input is already YUV. If your OVX8B camera module has an onboard ISP (like the GW5300 found in SENSING modules) that outputs YUV, this pipeline path avoids the calibration issue completely.

For programmatic access, instead of `hbn_camera_create()`, use the lower-level **`hbn_vnode_*` APIs** to construct a pipeline containing only the CIM node. This gives you standard HBN framework integration without triggering the ISP module check that causes error -65666.

## Workaround 3: V4L2 direct capture for standard Linux compatibility

The RDK S100 kernel (6.1.112-rt43) exposes **V4L2 interfaces for CIM, ISP, YNR, PYM, and GDC modules**. V4L2 device nodes at `/dev/video*` provide standard Linux camera API access. To explore this path:

1. Run `v4l2-ctl --list-devices` to enumerate available capture endpoints
2. Run `media-ctl -p` to visualize the full media pipeline topology
3. Identify the CIM V4L2 node, which should provide raw Bayer output
4. Capture frames using standard V4L2 `VIDIOC_REQBUFS` / `VIDIOC_QBUF` / `VIDIOC_DQBUF` calls

The CIM V4L2 node captures raw sensor data without requiring ISP calibration. This gives you a standard, portable capture interface compatible with GStreamer, OpenCV, and other V4L2 consumers.

## Hardware configuration: DIP switches and MCLK

**The OX08B40 requires external MCLK** — it has no internal oscillator. The Camera Expansion Board provides a **24MHz active crystal oscillator** on-board, routed through SW2200 DIP switch to Pin 5 of the MIPI connectors. Correct settings for OVX8B:

- **SW2200 (both switches): Set to MCLK position** — routes the 24MHz clock to the camera connectors. The OX08B40's internal PLL requires XVCLK to be active before I2C communication or streaming can begin. The officially supported cameras (IMX219, SC230AI, SC132GS) all use LPWM mode, so this is a critical change.
- **SW2201 (both switches): Set to 1.8V position** — the OX08B40 uses 1.8V DOVDD (digital I/O) and MIPI CSI-2 D-PHY is inherently 1.8V signaling. Verify your specific camera module's schematic, as some modules include level shifters presenting 3.3V externally.

The **"mipi mclk is not configed" warning** is partially critical. While the 24MHz clock comes from the expansion board's oscillator (not the SoC), the SoC's corresponding MCLK pin needs proper pinctrl configuration in the device tree to avoid driving conflicts. If the SoC pin is in an undefined state, it could interfere with the external oscillator signal.

## Device tree modifications to resolve the MCLK warning

The RDK S100 supports **device tree overlays** via `/boot/config.txt` `dtoverlay` directives. Three resolution paths for the MCLK pinctrl issue:

**Option A — Diff and switch DTBs**: Decompile both available DTBs with `dtc -I dtb -O dts` and diff them. The 503-byte difference between `rdk-s100-v1-2.dtb` and `rdk-s100-v1-21.dtb` may represent MCLK pinctrl additions or different camera configurations. Try switching to the alternate DTB.

**Option B — Create a device tree overlay** to add MCLK pinctrl to the MIPI host nodes. The overlay structure would look like:

```dts
/dts-v1/;
/plugin/;
/ {
    fragment@0 {
        target = <&mipi_host0>;
        __overlay__ {
            pinctrl-names = "default";
            pinctrl-0 = <&pinctrl_mipi0_mclk>;
        };
    };
};
```

The exact phandle references depend on the S100 SoC's pinctrl definitions in the base DTB. Decompiling the DTB will reveal the available pinctrl groups.

**Option C — Direct DTB modification**: Decompile, edit, recompile, and replace the DTB in `/boot/`. This is the most reliable but least reversible approach.

## The EEPROM problem and what it means

The camera module EEPROM being **partially programmed (only 2 bytes)** is a compounding issue. The `libovx8bstd.so` driver reads EEPROM data (typically at I2C address 0x50/0x51 on the same bus) to identify the module type and select the matching calibration library. With only 2 bytes, the driver cannot construct a valid calibration filename, contributing to the `HBN_STATUS_CAM_MOD_CHECK_ERROR`.

You can inspect EEPROM contents with `i2cdump -y <bus> 0x50` to see what's stored. However, even if you programmed the EEPROM with valid module identification, the corresponding calibration `.so` file must exist on the system — which brings you back to the core problem.

**Do not attempt to reprogram the EEPROM to match OVX3C or AR0820 calibrations.** ISP calibration is sensor+lens specific. Using wrong calibration would produce severely corrupted images with incorrect color matrices, lens shading correction, noise profiles, and HDR processing.

## How to get official help and the actual calibration files

D-Robotics provides several support channels where this issue can be reported:

- **Developer Community Portal**: https://developer.d-robotics.cc/en — the primary hub for posting technical issues. Navigate to the forum section and create a post describing the missing calibration libraries.
- **GitHub Issues**: File an issue at https://github.com/D-Robotics/x5-hobot-camera/issues (the closest public camera driver repository). No S100-specific camera repo exists yet, but this is the right project scope.
- **Discord**: D-Robotics has an official community Discord server announced via their LinkedIn page. Search their LinkedIn (linkedin.com/company/d-robotics) for the invite link.
- **Commercial SDK access**: The release notes indicate "please contact FAE for access" for the commercial version. D-Robotics FAEs (Field Application Engineers) can provide the full automotive sensor calibration packages.
- **Camera module vendor**: If you purchased the OVX8B modules from SENSING Intelligence, Yanding, or another vendor, they should provide platform-specific calibration libraries as part of their camera integration package.

## Conclusion

The core issue is a support boundary: **OVX8B is an automotive sensor that sits outside the RDK S100's official robotics-focused sensor support**. The driver's presence is an artifact of shared silicon heritage with the Journey 6 automotive platform, not an indication of full support. Three immediate actions will move things forward: first, try `libovx8b.so` as a drop-in replacement for `libovx8bstd.so`, since the smaller driver likely operates without calibration dependencies. Second, set **SW2200 to MCLK** and **SW2201 to 1.8V**, and resolve the device tree MCLK pinctrl by diffing available DTBs. Third, use `sample_cim` or V4L2 CIM-node capture for raw Bayer streaming that bypasses ISP entirely. For production-quality ISP-processed output, the calibration libraries must ultimately come from D-Robotics (via commercial SDK) or your camera module vendor — file the issue on their developer community to start that process.