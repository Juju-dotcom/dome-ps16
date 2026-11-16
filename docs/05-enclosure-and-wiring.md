# 5. Enclosure, console and wiring

The electronics live in a printed enclosure (250 x 160 x 62 mm) screwed under the base board.
The three boards lie flat on the lid, held only by four L-shaped corners, so the whole block
comes out with the lid. The console (OLED, three buttons, power switch, status LED) is a
faceplate under the front skirt segment.

Worst case the electronics dissipate about 5 W. With the vented shell the air inside reaches
about 38 °C, about 45 °C with the closed one (LM317 around 80 °C, limit 125 °C). Both work.

## 5.1 Enclosure shell

The shell has four bosses for M3 inserts (lid screws) and four holes on top for wood screws.

- **Connector wall** (faces the left edge of the board): Ø11.2 hole for the 12 V jack, a
  70 x 22 window to reach the Mega's USB port, and a 34 x 12 entry for the DB37 wires.
- **Centre wall**: 24 x 10 entry for the motor and end-stop cables.
- **Front end**: 30 x 10 entry for the console wires.

Once the DB37 wires are soldered at both ends, the connector no longer fits through the
34 x 12 entry. Turn that entry into a slot open at the bottom (two saw cuts from the lower
edge of the shell) so the wires slide in from below.

1. Set 4 heat-set inserts in the bosses (same method as the dome).
2. Mount the 12 V panel jack and find the centre, sleeve and switch tags with a meter.

## 5.2 DB37 plate

The DB37 is the only disconnect between the dome and the electronics.

1. Cut 19 wires of 22 AWG, labelled at both ends: cathodes 1–16 (240–310 mm, colour-coded:
   blue for LEDs 4, 5, 10, 13, 16; yellow for 1, 2, 3, 8, 12, 15; green for 6, 7, 9, 11, 14),
   anode (pin 17), camera trigger (pin 36) and ground (pin 37). Lengths per pin are in
   [wiring.md](wiring.md).
2. Solder them into the solder cups of the female DB37. The pin numbers are moulded in the
   plastic next to the cups.
3. Fit the DB37 into the D cut-out of the plate from behind, cups facing in, with 2 x M3 + nuts.
   Only the metal D goes through, the flat flange rests behind the plate. The D is a trapezoid:
   the wide side goes with the wide side of the cut-out. If it doesn't go in, scrape the
   elephant-foot bulge and the corners of the cut-out with a cutter or a file, never force it.
4. Screw the plate under the board at (−261, 177) and (−277, 128) with 2 wood screws
   (9 mm blind pilot holes, a skirt screw is only 18 mm away).

## 5.3 Console faceplate

Work on the faceplate on a cloth, face down, before it goes on the skirt.

- **Power switch** (Ø16.2, bottom left). Bridge NO to the LED terminal on the switch itself,
  then solder three wires: C (920 mm), NO (920 mm) and the ring LED− (930 mm). They go to T2 on
  the LED board. NC is unused.
- **Buttons** (green START, yellow NEXT, red STOP, left to right). The 12 mm holes are a bit
  tight; open them with a 1/2 in bit turned by hand or a round file, never with a soldering
  iron. One wire per button (to D7, D8, D9) plus a common ground. On the Mega side each wire
  ends in half of a male jumper wire.
- **Status LED**: one WS2812 module glued with epoxy behind the Ø5.2 hole above the switch,
  with a 330 Ω in series on DIN and a 100 µF across 5 V/GND. Data goes to D6, power comes from
  the UBEC (never from the Mega).
- **OLED** (Waveshare 1.3 in, SH1107): it ships in SPI mode. Move the 4.7 kΩ resistor on the
  back from the `0` side to the `1` side for I2C. Tie GND, CS and DC together to ground, VCC to
  the Mega's **3.3 V** (the display tops out at 3.6 V). RST goes through a divider from D10
  (330 Ω in series, then 2 x 330 Ω to ground), which gives 3.33 V when D10 is high. The module
  sits in a 3 mm frame behind the 34 x 18 window, held by two strips of black electrical tape.
  Twist SDA and SCL with a ground wire, they are about 0.8 m long.

## 5.4 Boards on the lid

1. Keep the motor board, Mega and LED board connected as on the bench and lay the block
   (about 160 x 120 mm) flat between the L-corners of the lid (166 x 126 mm). No standoffs,
   no screws in the boards.
2. Turn it so the Mega's USB port faces the large window of the connector wall.
3. The LM317 heatsink is the tallest part (about 38 mm). Nothing may be higher, there are only
   15 mm left under the shell.
4. UBEC: thick short wires are the 12 V input, thin long wires the 5 V output. Check the
   output on the bench (4.75–5.25 V; above 5.3 V it would kill the WS2812), then stick it flat
   next to the block with double-sided tape.

## 5.5 Inside wiring

With the shell screwed under the board (section 6.1) and the lid held just below it:

1. Pass the wires through their entries: console through the front, motor and end-stop
   through the centre wall, DB37 through the connector wall slot. Leave enough slack to open
   the lid.
2. Ground first: LED board R4 to the Mega, to T5 GND on the motor board, to the UBEC and to
   DB37 pin 37.
3. 12 V: jack → T1, T2 → power switch (the three wires from 5.3), LED board → T5 and → UBEC.
4. Solder the 19 DB37 wires to the LED board (see section 2.8 for the holes).
5. Plug in D22–D37, then D2–D10, D18, D20, D21, 3.3V and the two 5V pins.
6. Screw the motor into T6 (coil 1 on 1–2, coil 2 on 3–4) and the end-stop into T7
   (V → 1, G → 2, S → 3). Nothing is soldered there.
7. Bend each jumper flat right above its plastic housing and bundle them with electrical tape.
   Nothing above the heatsink.

The 5 V of the UBEC is never connected to the Mega. The red VAUX wire of the camera GPIO cable
is never connected to anything.

## 5.6 Dome harness

There is no connector at the LEDs; the DB37 is the only place the dome unplugs.

1. Cut off the JST connectors, keeping the 200 mm pigtails.
2. Splice a cathode extension (same colour code as 5.2) onto the black wire of each pigtail,
   with heat shrink. Lengths per LED are in [wiring.md](wiring.md); count about 12.6 m of wire
   for the cathodes alone.
3. One white common anode trunk (3.33 m) with the red wire of every LED spliced onto it at
   that LED's height.
4. Camera GPIO cable (M8, 8 pins) cut to 1290 mm from the plug. Keep green (pin 8, Line0) and
   blue (pin 6, opto ground), insulate the rest.
5. On the male DB37: cathodes on pins 1–16, anode on 17, green on 36, blue on 37. Close the hood.

The harness leaves the dome over the rim at azimuth 152°, right above the DB37 plate, and
drops in front of the skirt. It never goes through the skirt wall, so there is no hole to
seal. Leave 150 mm of slack so the dome can be lifted 120 mm, and always unplug the DB37 and
the camera cable before lifting.

## 5.7 Console on the skirt

1. Lift the dome about 50 mm (one person holds it by the knob).
2. Feed the console wires through the slot in the console skirt segment and the slot in the
   board.
3. Slide the faceplate under the shelf of the console segment and fix it with 2 x M3 x 8
   through the countersunk holes at x = ±67.
4. Stick the last foam strip on that shelf. It covers the screw heads.
