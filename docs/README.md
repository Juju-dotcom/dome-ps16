# Assembly guide

An interactive 3D version of this guide is in [build_guide/index.html](build_guide/index.html).

Follow the sections in order. The electronics are built and tested on the bench before the
dome is finished, so a wiring mistake is found while everything is still easy to reach.

1. [Printing](01-printing.md)
2. [Electronics](02-electronics.md): cut the boards, build and test one block at a time
3. [Dome](03-dome.md): inserts, shell, light test, flocked lining, LED capsules, camera
4. [Base](04-base.md): board, feet, motor, zero sensor, skirt and guide towers
5. [Enclosure, console and wiring](05-enclosure-and-wiring.md)
6. [Final assembly and first power-up](06-final-assembly.md)

[wiring.md](wiring.md) has every hole, jumper and pin in one place.

## Tools

Soldering iron (and a fine tip for the OLED), heat-set insert tip, multimeter with a 10 A
input, digital caliper, 2.5 mm and 1.5 mm hex keys, jigsaw with a fine laminate blade, drill
with Ø3, Ø6, Ø10 and 1/2 in bits, long screwdriver (115 mm shaft for the feet), files, utility
knife, household iron for the edge banding, painter's and masking tape.

## Safety

- Only one LED is ever on, and the firmware turns it off after 10 s. Before a capsule is
  mounted, a bare star gets hot within seconds. Don't look into a lit LED up close.
- Never plug or unplug the stepper motor with 12 V on; the TMC2209 doesn't survive it.
- The OLED is 3.3 V only.
- Unplug both the 12 V supply and USB before soldering.
- ASA fumes: print with the enclosure closed and an exhaust fan, and ventilate when setting
  inserts.
