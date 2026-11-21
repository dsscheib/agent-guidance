# Embedded firmware and hardware profile

Adopt explicitly in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md) before treating these rules as binding. Applies to microcontroller/processor firmware and electronics or mechanical design files in the repository.

## Record in `PROJECT_PROFILE.md` before implementation
- **Targets:** Exact MCU/processor part number and variant, clock source, flash/RAM limits, and supported board revisions.
- **Toolchains & probes:** Compiler/assembler, linker, build tool, programmer/debug probe, simulator, and EDA/CAD tool versions.
- **Authoritative hardware sources:** Datasheets, reference manuals, errata revisions, schematics, and mechanical specs.

## Command inventory & `agent-team` hardware kits
- **Development gates:** Firmware cross-build (report flash/RAM usage against recorded budgets), formatter/static checks, host-side unit tests (hardware-independent logic only), and EDA/CAD rule checks—including `python3 tools/kicad/verify.py --project .` or `FreeCADCmd tools/freecad/inspect_model.py` when `agent-team` kits are installed.
- **Release gates:** BOM/parts availability checks (if configured); substitute device resource budgets (flash, RAM, stack depth, worst-case interrupt latency, power) for server load budgets.
- **Ungated (manual approval only):** Bench/HIL tests, `fabrication_export.py`, G-code generation, and flashing commands must stay ungated (`—`) so `--verify` never executes them automatically.
- Propose `Proposed: Not applicable: <reason>` for browser smoke (unless serving a web UI), DB migrations, and server soak.

## Approval-only actions and hardware evidence
- **Never without explicit per-operation approval:** Flashing/programming any device (build from a committed revision only and record revision + image checksum), writing fuses/option bytes/lock bits/bootloaders (state exact values and recovery path first), applying power or connecting equipment near mains/high-energy circuits, or ordering/uploading boards or parts.
- **Cite datasheets:** Take register addresses, bit fields, timing, voltage limits, and pinouts from recorded datasheets/schematics and cite document + section. Keep one source of truth for pins; report firmware-vs-schematic mismatches instead of silently changing either.
- **Host tests ≠ bench proof:** Passing builds, host tests, simulators, or ERC/DRC never prove timing, peripheral behavior, electrical correctness, or safety certification. Record unverified hardware behavior in [docs/OPEN_WORK.md](../docs/OPEN_WORK.md).

## Release
Identify the committed revision, image checksum, map/listing file, supported board revisions, and bench evidence (plus design revision, fabrication outputs, and dated BOM availability for hardware releases).
