# Bill of materials

Everything I bought (or already had) to build the Dome PS-16. Quantities are the quantities **used** in the dome. Supplier part numbers are the ones I ordered with, in Canada (ABRA Electronics, Amazon, Bambu Lab, Home Depot). Equivalent parts from other suppliers should work.

## Camera and lights

| Qty | Part | Supplier / ref | Notes |
|---:|---|---|---|
| 1 | LUCID Triton TRI050S-CC, 5 MP colour industrial camera | LUCID Vision Labs | Raw Bayer images, triggered by the Arduino |
| 1 | Fujinon HF25XA-5M lens, 25 mm | Fujifilm | |
| 1 | LUCID M12 → RJ45 cable (2 m) | LUCID | Camera data |
| 1 | LUCID M8 8-pin GPIO cable (5 m, open wires) | LUCID | Camera trigger |
| 1 | PoE injector 802.3af | Amazon | Powers the camera |
| 1 | Ethernet cable Cat6, 6 ft | ABRA UTP6-6-RED | |
| 16 | Luxeon SW-01-T7 white LED on star board | — | 16 used (18 bought) |

## Electronics

| Qty | Part | Supplier / ref | Notes |
|---:|---|---|---|
| 1 | Arduino Mega 2560 R3 | ABRA A000067 | Controls everything |
| 1 | USB A-B cable | ABRA CAB-650-100 | |
| 1 | Panel-mount round USB-B socket + 30 cm extension | ABRA 4216-ADA | |
| 1 | 12 V 3 A power supply | ABRA DC-1203-2.1 | |
| 1 | Panel-mount 2.1 mm DC jack | ABRA CON-DC-PJ-2.1 | |
| 1 | 2.1 mm jack to screw terminal adapter | ABRA 368-ADA | For bench tests |
| 1 | 2 A slow-blow radial fuse (Littelfuse 382) | ABRA FUSE-382-T2A | Soldered on the board, in series with +12 V |
| 1 | LM317T adjustable regulator (TO-220) | ABRA LM317T | Constant-current source for the LEDs (~320 mA) |
| 1 | 3.9 Ω 2 W resistor | ABRA R2W-3.9 | Sets the LED current with the LM317 |
| 1 | TO-220 heatsink + insulator + thermal paste | ABRA 531102B02500, TP0006, PRT-09599 | |
| 2 | ULN2803A Darlington array (8 channels) | ABRA ULN2803A | Switch the 16 LEDs |
| 2 | 18-pin DIP socket | ABRA 18LP | |
| 2 | 100 µF 35 V electrolytic capacitor | ABRA 100R35 | |
| 1 | 0.1 µF ceramic capacitors (pack of 10) | ABRA 753-ADA | |
| 1 | 330 Ω 1/4 W resistors (pack of 10) | ABRA R1/4-330 | |
| 2 | Breadboard-pattern solder board with 4 mounting holes | ABRA SB830 | Cut to 114 × 47 and 86 × 47 mm |
| 1 | UBEC 5 V 3 A step-down regulator | ABRA 1385-ADA | Powers only the status LED |
| 1 | WS2812 addressable LED module (pack of 10) | ABRA LED-BB-10 | Status light |
| 1 | Waveshare 1.3" OLED display, 64 × 128 | ABRA WAVE-18179 | Front panel, on the 3.3 V of the Mega |
| 1 | 16 mm latching switch, white ring, 12 V | ABRA PBS-LED-1624WH-L | Power switch |
| 3 | 12 mm momentary push buttons (red, yellow, green) | ABRA PBS-DS427-M-RD / -Y / -GN | |
| 1 | DB37 male + female solder connectors + hood | ABRA DB37P, DB37S, HOOD37 | Dome ↔ enclosure connection |
| 16 | JST-PH 2.0 mm male + female pairs with 20 cm wire | ABRA CON-JST-PH-MF2 | One per LED |
| — | Female headers 36 pins, 2.54 mm (pack of 5) | ABRA 598-ADA | |
| — | Male-male jumpers 8" (pack of 40) | ABRA 758-ADA | |
| — | KF301 screw terminals, 5.08 mm (2, 3 and 4 positions) | ABRA TB-KF301-100 | |
| — | 22 AWG stranded wire, 6 colours | ABRA 22HST-25-KIT | |
| — | Black heat shrink assortment | ABRA HTSHRINK160BK | |

## Turntable

| Qty | Part | Supplier / ref | Notes |
|---:|---|---|---|
| 1 | NEMA 17 stepper motor, 1.7 A | ABRA JK42HS40-1704 | |
| 1 | TMC2209 stepper driver | ABRA 3D-TMC2209 | 3,200 microsteps per turn |
| 1 | Optical endstop (fork) | ABRA 3D-E-005 | Home position |
| 1 | Pololu aluminium hub for 5 mm shaft, M3 (pack of 2) | ABRA 1998-POLOLU | |
| 1 | PTFE sheet 200 × 200 × 5 mm | Amazon | Turntable surface |

## Calibration

| Qty | Part | Supplier / ref | Notes |
|---:|---|---|---|
| 1 | Glass calibration checkerboard 100 × 100 mm | Amazon (Aurorad) | Camera calibration and camera poses |
| 1 | 2" (50.8 mm) precision steel ball | Amazon (G25) | Mirror ball for the LED directions |
| 1 | Digital caliper | Amazon | Size of the reconstructed objects |

## Structure and hardware

| Qty | Part | Supplier / ref | Notes |
|---:|---|---|---|
| ~2.9 spools | Black ASA filament | Bambu Lab | Dome panels and enclosure |
| ~0.8 spool | Black PETG-CF filament | Bambu Lab | Connectors, LED capsules, feet, camera parts |
| ~0.4 spool | Black PLA filament | Bambu Lab | Calibration holders |
| 1 | Black melamine panel 5/8" (15.9 mm), cut to 700 × 920 mm | Home Depot | Base |
| ~3.3 m | Black iron-on melamine edge banding | Home Depot | |
| 60 | #8 × 5/8" pan head wood screws | Home Depot | |
| 159 | M3 heat-set inserts, L 5.7 mm, Ø 4.6 mm | Amazon | |
| 163 | M3 × 8 pan head screws | Amazon | |
| — | M3 screw assortment (8/10/12/16/20 mm) | Amazon | |
| — | M3 nylon standoff kit | ABRA S-M3-KITC | |
| — | Stainless M2/M3/M4 screw assortment | ABRA SC-H-M-SS-KIT | |
| ~2.4 m | Black adhesive EPDM foam, 25 × 3 mm | Amazon | Light seal between dome and base |
| ~0.6 m² | Black adhesive flocked paper | Amazon | Inside of the dome, kills reflections |
| 6 | Adhesive rubber pads | Amazon | |
| 1 | 5-minute epoxy | Home Depot | |
| 1 | Isopropyl alcohol | Home Depot | |

## Tools

3D printer (I used a Bambu Lab X2D with AMS 2 Pro), soldering iron, solder and flux, wire stripper, multimeter, and a computer to run the capture.
