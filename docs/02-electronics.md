# 2. Electronics

Two boards are cut from SB830 solderable breadboards: the **LED board** (power input, LM317
current source, two ULN2803) and the **motor board** (TMC2209 + end-stop). Hole names below
use the breadboard labels: column number + row letter (`26h`), and `R0`–`R5` for the rails.
The full hole-by-hole layout is in [wiring.md](wiring.md).

Build and test one block at a time. Unplug the 12 V supply **and** the USB cable every time
you solder.

## 2.1 Cut the boards

1. Lay the SB830 copper side up, rails R0–R2 away from you, the end with the 4 vertical bars on
   the left. R4 is the rail row closest to you.
2. Check that R4 is continuous from column 1 to column 60. On some boards it is cut near
   column 32; if so, bridge R4 col 30 to col 34 with bare wire on the solder side.
3. Score and snap: board 1 at 114 mm from the left end (LED board), board 2 at 86 mm (motor
   board). Always cut between two columns, never through a row of holes. File the edge.
4. Drill the two right-hand mounting holes (Ø3.2–3.5 mm) in place of a rail hole: column 39 on
   the LED board, column 28 on the motor board, rails R1 and R4.

Wear a mask when cutting and filing; fiberglass dust is irritating.

## 2.2 12 V input and fuse (LED board)

1. Check the supply polarity with the 2.1 mm-to-terminal adapter. The centre pin should be +.
2. Solder T1 (2-pos terminal) at 21a/23a, the 2 A radial fuse at 26e/28e, T2 (3-pos) at
   31a/33a/35a.
3. Jumpers: PA 23e→26b, PB 28b→31e, PE 21e→19d, G4 21d→R4:22, G3 35e→R4:35. Leave
   19f–19j empty, it becomes the COM pin of the second ULN2803.
4. Put a temporary wire between T2 pins 1 and 2 (it stands in for the power switch).
5. Before powering: 33e to R4 must read open (> 1 MΩ). Powered: 12 V ± 0.6 V at T1 and at 33e.

Never connect the supply backwards. The LM317 and the TMC2209 have no reverse protection.

## 2.3 LM317 current source

The LED current is set by R1: I = 1.25 V / 3.9 Ω ≈ 0.32 A.

1. Mount the LM317T on its heatsink with thermal paste, the TO-220 insulator and a **nylon**
   M3 screw. The tab is connected to OUT, so check there is no continuity between the heatsink
   and any of the three pins.
2. Solder the LM317 at 26j (ADJ), 27j (OUT), 28j (IN), heatsink toward the bottom edge.
3. R1 (3.9 Ω, 2 W) standing at 27g/26g, C1 (0.1 µF) at 33d/35d, jumpers PC 33e→33f and
   PD 33g→28g. Hole 26h is now the common anode.
4. Test with one spare LED star: anode on 26h, cathode to R4 through the meter on the 10 A
   input. Expect **0.32 A ± 0.02**. Then measure across R1: **1.25 V** (1.20–1.30).

A bare LED star heats up quickly: 10 seconds on, 1 minute off. Never measure voltage with the
red lead still in the 10 A jack, that shorts R1.

## 2.4 LED pigtails

For each of the 16 stars: tin pads P3 (+) and P7 (−), solder the red wire of a JST-PH male
lead to P3 and the black one to P7, heat-shrink both joints, label the lead 1 to 16.
Light each one from the current source for a few seconds and note its forward voltage.
Expect 2.5 to 3.2 V at 0.32 A. Keep the two extra stars as spares.

## 2.5 ULN2803 drivers

1. Solder two 18-pin sockets: U2 with pin 1 at 1e, U3 with pin 1 at 11e, notch toward column 1.
2. Ground wires: G1 9a→R2:9 and G2 19a→R2:19. Nothing on 9f–9j or 19f–19j (pin 10 = COM).
3. Beep test without the chips: pin 9 of each socket must beep to R4, pin 10 must not.
   If pin 9 doesn't beep, check in order 9e→R2, R2→19a, 19a→21a, 21a→R4.
4. Insert both ULN2803A, notch toward column 1. A reversed ULN burns at power-up.

## 2.6 Arduino Mega and firmware

1. One ground wire only between the Mega and the LED board: Mega GND → R4:9.
2. LED outputs: D22–D29 to holes 1a–8a (U2 inputs), D30–D37 to holes 11a–18a (U3 inputs).
3. Flash `firmware/dome_ps16/dome_ps16.ino` (board: Arduino Mega 2560). Open the serial
   monitor at 115200 baud, newline line ending. You should see `EVT BOOT dome_ps16`.
4. With the spare star between 26h and output 1 (hole 1j), type `LED 1` then `OFF`. Repeat
   for outputs 8 (8j), 9 (11j) and 16 (18j).
5. Type `LED 1` and wait: the firmware turns it off after 10 s and prints `EVT LED_AUTOCUT 1`.

When an LED is on, its ULN output reads 1.0–1.6 V. When off, it rises above 5 V.

## 2.7 Motor board

1. Check the TMC2209 silkscreen. Control row: EN, MS1, MS2, (unused), UART, NC, STEP, DIR.
   Power row: VM, GND, 2B, 2A, 1A, 1B, VIO, GND.
2. Two 8-pin female headers at 4c–11c and 4f–11f. The module plugs in with EN at 4c and VM
   at 4f. If the silkscreen doesn't match, stop, a reversed module swaps VM and GND.
3. C2 (100 µF) on the rails: + to R3:12, − to R4:12.
4. Terminals: T5 (12 V in) at 23f/25f, T6 (motor, 4-pos) at 14f/16f/18f/20f, T7 (end-stop,
   3-pos) at 14d/16d/18d. The wire openings of T7 face the left edge, those of T6 the right.
5. Solder the jumpers M1–M11 and MP1–MP4 from [wiring.md](wiring.md).
6. Mega wires: D2 (STEP) → 10a, D3 (DIR) → 11a, D4 (EN) → 4a, D18 (end-stop) → 18a,
   5V → 10j and another 5V → R2:12, plus a ground between the Mega and T5 GND.
7. Plug in the module **without** the motor. Connect USB first (the firmware keeps the driver
   disabled), then 12 V on T5. Set Vref to **1.40 V** on the potentiometer screw, which is
   about 1.0 A RMS.
8. Power off. Find the two coils with the continuity tester and screw coil 1 into T6 pins 1–2,
   coil 2 into pins 3–4. Power on and type `ROT 360`. A tape mark on the shaft should come
   back to the same place.
9. Screw the optical fork into T7 (5V, GND, SIG). Type `TEST CAPTEUR` and block the slot:
   the Mega prints `etat=OCCULTE`. If it reads the opposite, change `HOME_ACTIVE_LEVEL` in the
   firmware.

Never plug or unplug the motor while 12 V is on, it kills the TMC2209. If the motor
vibrates without turning, swap the two wires of one coil.

## 2.8 Full bench test

Before anything goes in the enclosure, test everything on the table:

1. Solder the 19 wires of the female DB37 to the LED board. Pins 1–8 → 1j–8j, pins 9–16 →
   11j–18j, pin 17 (anode) → 26h, pin 37 (ground) → R4 col 10, pin 36 (camera) → 37f.
2. Camera trigger: R5 (330 Ω) standing between 36h and 37h, Mega D5 → 36j. The path is
   D5 → R5 → DB37 pin 36 → green wire of the camera GPIO cable.
3. Plug in the dome harness (section 5.6). Power order: 12 V first, then USB.
4. `LED 1` / `OFF` … `LED 16` / `OFF`: each LED lights alone, at 0.32 A.
5. `HOME` then `ROT 360`.
6. If the camera is connected, `TRIG` should give one frame in ArenaView (Line0, rising edge).

Only the LM317 heatsink should get warm.
