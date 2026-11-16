# Wiring reference

Both boards are cut from SB830 solderable breadboards. Columns are numbered from the left,
starting at the 5th column of holes (the first 4 are the vertical bars). In each column, holes
a–e are connected together and so are f–j. R0–R2 are the top rails, R3–R5 the bottom ones.

## Arduino Mega pins

| Pin | Function | Goes to |
|---|---|---|
| D2 | STEP | motor board 10a |
| D3 | DIR | motor board 11a |
| D4 | EN (active low) | motor board 4a |
| D5 | camera trigger | LED board 36j → R5 330 Ω → DB37 pin 36 |
| D6 | WS2812 data | status LED (330 Ω in series at the module) |
| D7 / D8 / D9 | START / NEXT / STOP buttons | console, to ground when pressed (internal pull-ups) |
| D10 | OLED RST | through the 330 Ω divider (3.33 V high) |
| D18 | end-stop signal | motor board 18a → T7.3 |
| D20 / D21 | SDA / SCL | OLED (I2C, 0x3C) |
| D22–D29 | LEDs 1–8 | LED board 1a–8a (U2 inputs) |
| D30–D37 | LEDs 9–16 | LED board 11a–18a (U3 inputs) |
| 3.3V | OLED VCC | |
| 5V (x2) | motor board logic + end-stop | 10j and R2:12 |
| GND | single ground to the LED board | R4:9 |

## LED board (114 x 47 mm)

| Part | Holes | Notes |
|---|---|---|
| U2 ULN2803A (LEDs 1–8) | pin 1 at 1e … pin 9 at 9e, pin 10 at 9f … pin 18 at 1f | in an 18-pin socket, notch toward column 1 |
| U3 ULN2803A (LEDs 9–16) | pin 1 at 11e … pin 9 at 19e, pin 10 at 19f … pin 18 at 11f | same |
| T1 12 V input | 21a (GND), 23a (+12 V) | |
| F1 2 A slow fuse | 26e, 28e | radial, 5.08 mm pitch |
| T2 to power switch | 31a (to C), 33a (from NO), 35a (GND to ring LED−) | |
| C1 0.1 µF | 33d, 35d | |
| U1 LM317T | 26j ADJ, 27j OUT, 28j IN | heatsink toward the bottom edge, nylon screw |
| R1 3.9 Ω 2 W | 27g, 26g | sets 0.32 A |
| R5 330 Ω | 36h, 37h | camera trigger |

| Jumper | From | To | Net |
|---|---|---|---|
| PA | 23e | 26b | +12 V in → fuse |
| PB | 28b | 31e | fuse → switch |
| PC | 33e | 33f | switched 12 V across the centre gap |
| PD | 33g | 28g | switched 12 V → LM317 IN |
| PE | 21e | 19d | GND → U3 pin 9 |
| G1 | 9a | R2:9 | GND (U2 pin 9) |
| G2 | 19a | R2:19 | GND (U3 pin 9) |
| G3 | 35e | R4:35 | GND |
| G4 | 21d | R4:22 | GND |

Outside wires: cathodes 1–8 at 1j–8j, 9–16 at 11j–18j, common anode at 26h, camera trigger at
37f, switched 12 V out at 33h (UBEC) and 33i (motor board T5), ground at R4:9 (Mega),
R4:10 (DB37 pin 37), R4:36 (UBEC) and R4:37 (motor board).

## Motor board (86 x 47 mm)

The TMC2209 sits in two 8-pin female headers. Control row in column c, power row in column f:

| Row | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|
| c | EN | MS1 | MS2 | PDN | UART | NC | STEP | DIR |
| f | VM | GND | 2B | 2A | 1A | 1B | VIO | GND |

| Part | Holes |
|---|---|
| C2 100 µF | + R3:12, − R4:12 |
| T5 12 V in | 23f (+12 V), 25f (GND) |
| T6 motor | 14f, 16f, 18f, 20f |
| T7 end-stop | 14d (5 V), 16d (GND), 18d (signal) |

| Jumper | From | To | Net |
|---|---|---|---|
| M1 | 4j | R3:4 | VM → 12 V rail |
| M2 | 23j | R3:23 | T5 → 12 V rail |
| M3 | 11j | R4:11 | GND |
| M4 | 5j | R4:5 | GND |
| M5 | 25j | R4:25 | GND |
| M6 | 6a | R2:6 | MS2 → 5 V |
| M7 | 5a | R2:5 | MS1 → 5 V |
| M8 | 8a | R1:8 | PDN/UART → GND |
| M9 | 14a | R2:14 | 5 V → end-stop |
| M10 | 16a | R1:16 | GND → end-stop |
| M11 | R1:2 | R4:2 | top GND rail ↔ bottom GND rail |
| MP1 | 6g | 14h | 2B → T6.1 |
| MP2 | 7h | 16i | 2A → T6.2 |
| MP3 | 8i | 18j | 1A → T6.3 |
| MP4 | 9j | 20h | 1B → T6.4 |

MS1 and MS2 both high gives 16 microsteps (3200 steps per turn). Vref is set to 1.40 V,
about 1.0 A RMS.

## DB37

Pin k on the female (enclosure) connects straight to pin k on the male (dome harness).

| Pin | Signal | Enclosure side | Dome side | Wire inside the base |
|---|---|---|---|---|
| 1–8 | cathodes LED 1–8 | U2 outputs (1j–8j) | LED 1–8 black wire | 310, 310, 310, 300, 300, 290, 290, 280 mm |
| 9–16 | cathodes LED 9–16 | U3 outputs (11j–18j) | LED 9–16 black wire | 270, 270, 260, 260, 250, 250, 240, 240 mm |
| 17 | common anode | 26h (LM317 output) | white anode trunk | 210 mm |
| 18–35 | spare | | | |
| 36 | camera trigger | 37f (after R5) | GPIO green (pin 8, Line0) | 170 mm |
| 37 | ground | R4:10 | GPIO blue (pin 6, opto GND) | 260 mm |

Cathode colours: blue for LEDs 4, 5, 10, 13, 16; yellow for 1, 2, 3, 8, 12, 15; green for 6, 7,
9, 11, 14.

**Dome harness, cathode extension per LED** (spliced onto the 200 mm pigtail):

| LED | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mm | 1060 | 620 | 310 | 730 | 1170 | 890 | 760 | 560 | 480 | 530 | 640 | 850 | 970 | 1100 | 1070 | 860 |

Anode trunk: 3330 mm of white wire. Camera GPIO cable: cut at 1290 mm from the M8 plug.

## Camera GPIO cable (LUCID M8, 8 pins)

Colours by pin: 1 red, 2 brown, 3 orange, 4 purple, 5 black, 6 blue, 7 yellow, 8 green.
Only green (Line0, opto-isolated input, 2.5–24 V) and blue (opto ground) are used.
**Never connect red (pin 1, VAUX 12–24 V).** Cut the other six short and insulate them.
