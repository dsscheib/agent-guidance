# Optional embedded firmware and hardware profile

Kind: Profile. Status: Not selected. Adopt explicitly in PROJECT_PROFILE.md before treating these rules as binding. It applies to firmware for a microcontroller or processor, and to electronics design files (schematics, boards, parts lists) kept in the same repository. It names no toolchain, language or vendor.

## Record before implementation
PROJECT_PROFILE.md's stack row names, from the owner or the repository, never by assumption:
- Each target: processor or microcontroller part number and variant, clock source, memory sizes, and the board revision it runs on.
- Toolchain and versions (compiler or assembler, linker, build tool), the flashing or programming tool and debug probe, and any emulator or simulator.
- The authoritative sources for hardware facts: datasheets, reference manuals and errata by revision, and the schematic that defines pin assignments.
- Electronics design tool and version, when design files are in the repository.

## Command inventory for this profile
Map the inventory's rows to the project; do not invent the commands:
- **Build:** the cross-build that produces the firmware image. Report image size against the flash and RAM limits recorded in the profile.
- **Format and static checks:** the formatter, compiler warnings treated as errors where adopted, and a static analyzer.
- **Unit tests:** host-side tests of hardware-independent logic (parsers, state machines, protocol framing, arithmetic). They do not exercise peripherals, timing or interrupts.
- **Design checks:** when design files are present, the design tool's electrical and layout rule checks as a Development gate, and a parts-availability check, if the project has one, as a Release gate.
- **Hardware-in-the-loop or bench tests:** a row without a Gate, run only by a person or with explicit approval, because it flashes or powers hardware.

Rows that normally do not apply here, to propose as "Proposed: Not applicable: <reason>" for the owner to decide: browser and accessibility smoke (unless the device serves a web interface), migration and recovery (unless the device keeps persistent data across firmware updates), and performance or soak in the server sense. Propose resource budgets (flash, RAM, stack depth, worst-case interrupt latency, power) as the device's performance budgets instead. Primary journeys are the device's observable behaviors, such as power-on, a command over the serial port or a button press.

## Actions that need explicit approval
Treat each of these as outward and possibly irreversible under AGENTS.md rule 3, approved for its stated scope only:
- Flashing or programming any device, including over a bootloader. Flash only an image built from a committed revision, and record that revision and the image checksum.
- Writing fuses, option bytes, lock or security bits, or replacing a bootloader. These can make a device unrecoverable; state the exact values and the recovery path before asking.
- Applying power, connecting test equipment, or any work near mains or high-energy circuits.
- Ordering parts or boards, or sending design files to a fabricator.

## Hardware facts and evidence
- Take register addresses, bit fields, timing, voltage limits and pinouts from the recorded datasheets, reference manuals and schematic, and cite the document and section. Never invent them; when the sources disagree or are silent, ask (AGENTS.md rule 4).
- Keep one source of truth for pin assignments. When firmware and the schematic disagree, report it rather than changing either to match.
- A passing build, host test or simulator run is evidence only of what it exercises. A change to timing, interrupts, peripherals, power modes or memory layout stays unverified until bench evidence exists; record that gap in OPEN_WORK.
- Design rule checks are necessary, not proof of electrical correctness or safety. Never claim safety or regulatory certification.

## Release
A firmware release identifies the committed revision, the image and its checksum, the map or listing file, the target and board revisions it supports, and the bench evidence for the changes it contains. A hardware release identifies the design revision, the fabrication outputs and the parts list with the availability check's date.
