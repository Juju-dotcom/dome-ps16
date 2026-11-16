# 6. Final assembly and first power-up

## 6.1 Enclosure under the board

1. With the dome off, lay the board on its side on a cloth.
2. The shell goes against the underside, centred at (−155, +55): x from −235 to −75, y from
   −70 to +180. Connector wall toward the left edge of the board, centre wall toward the motor,
   front end toward the console.
3. Mark the 4 holes through the top of the shell, drill 9 mm blind pilot holes, feed all the
   hanging wires through their entries, then screw the shell on from inside with 4 wood screws.
4. Do the inside wiring (section 5.5) and leave the lid hanging open for the tests.

## 6.2 Dome and camera

1. Put the dome on the guide towers (lift it by the knob, never by the capsules).
2. Pass the harness over the edge of the board and plug the male DB37 into the plate.
3. Camera: M12 cable from the camera to the **PoE** port of the injector, Ethernet from the
   **Data** port to the computer. Open LUCID Arena; the camera should show up.

## 6.3 First power-up

Do this in order, with the lid open so you can measure.

1. Pull the TMC2209 out of its headers. USB unplugged, power switch off.
2. Plug in the 12 V supply and press the switch: the white ring lights up.
3. Measure 12 V at T1, then the UBEC output. **If the UBEC is above 5.3 V, switch everything
   off.**
4. After a minute, touch the LM317 heatsink and the fuse. Warm is fine, hot is not.
5. Only now plug in the USB. Open the serial monitor (115200 baud) and wait for
   `EVT BOOT dome_ps16 ... oled=1`.
6. Switch off, put the TMC2209 back (motor already in T6) and switch on again.

From now on: USB first, then 12 V. Always remove the TMC2209 or cut the 12 V before touching
the motor wires.

## 6.4 Tests

| Command | What to check |
|---|---|
| `TEST BOUTONS` | press START and NEXT 3 times each, then STOP once; the counts are printed at the end |
| `TEST OLED` | three test screens, 2 s each; the OLED should draw well under 50 mA on its 3.3 V wire |
| `TEST WS` | status LED red, green, blue, white |
| `LED 1` … `LED 16` | note which capsule lights for each number; 1.25 V across R1 every time |
| `HOME` | the turntable finds the flag and stops on it |
| `ROT 360`, `GOTO 90`, `GOTO 0` | full turn, then absolute moves |
| `TRIG` | one frame in Arena |
| `SEQ 300` | 16 LEDs in a row and 16 frames |

If the turntable turns the wrong way, change `DIR_INVERSE` or `HOME_DIR` in the firmware. If
`HOME` doesn't find the flag, run `TEST CAPTEUR` again and check `HOME_ACTIVE_LEVEL`.

**Arena settings for the trigger:** PixelFormat `BayerRG12`, TriggerSelector `FrameStart`,
TriggerMode `On`, TriggerSource `Line0`, TriggerActivation `RisingEdge`, and keep the Line0
threshold low (2.5 V). If no frame arrives, check the green wire on DB37 pin 36 and R5.

## 6.5 Close the lid

When every test passes, check that no wire is pinched between the lid and the shell, then
screw the lid on with 4 x M3 x 8 into the inserts, in a cross pattern.
