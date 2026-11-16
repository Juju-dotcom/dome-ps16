# 4. Base

The base is a decagonal 5/8 in black melamine board (322 mm apothem, with 5 round ears for
the guide towers) on six 80 mm printed feet. The motor sits in a 46 x 46 mm window at the
centre, the enclosure hangs underneath, and a ring of 10 printed skirt segments carries the
dome. Five guide towers go through the ears of the dome so it can be lifted straight up and
set back in the same place.

Coordinates below are in mm from the board centre, x to the right and y toward the back, seen
from above. The front is the flat side where the console skirt goes.

## 4.1 Cut the board

1. Print `hardware/board/baseboard_outline.svg` at 100 % on letter paper, tiled, and check the
   50 mm control line on each sheet. Tape the sheets together and tape the template to the board,
   at least 10 mm from every edge.
2. Before removing the template, mark every screw position with a nail through the paper:
   skirt (20), guide towers (20), motor plate (4), plus the corners of the motor window,
   the end-stop hole at (60, −8) and the console cable slot (x −15 to 15, y −302.5 to −292.5).
3. Put painter's tape over the cut line and cut just outside it with a jigsaw, fine laminate
   blade, slow speed. File to the line.
4. Iron on black edge banding (cotton setting, no steam), small pieces around the ears.
5. Cut the 46 x 46 mm motor window: Ø10 holes in the corners, jigsaw between them, file to
   46.0 mm (never more than 46.5, the motor plate only overlaps by 13 mm).
6. Drill the Ø6 end-stop hole at (60, −8) and the 30 x 10 mm console slot (two Ø10 holes at
   x = ±10, y = −297.5, then saw between them).

Pilot holes are always Ø3 mm and **blind**: put tape on the bit at 10–12 mm. The board is
15.9 mm thick, and a hole that goes through lets light into the dome.

## 4.2 Feet

Six feet on a 285 mm radius every 60°, starting on the x axis, with two screws per foot 10 mm
either side of the centre. They are screwed from underneath through a deep counterbore, so you
need a screwdriver with a shaft of at least 115 mm. A rubber pad goes under each foot. If the
board rocks, add a layer of tape between one foot and its pad.

## 4.3 Motor and turntable

1. The NEMA 17 shaft is round. File a 0.5 mm flat on the last 10 mm (tape around the base of
   the shaft to keep filings out of the motor).
2. Motor plate on the motor face with 4 x M3 x 8 (31 mm spacing). Nothing longer, the thread in
   the motor is only 4 mm deep.
3. Drop the motor into the window, cable toward the left (enclosure side), and screw the plate
   to the board with 4 wood screws at (±30, ±30).
4. Pololu hub on the shaft, set screw on the flat, top of the hub 24 mm above the motor face.
5. Turntable on the hub with 4 x M3 x 10 in the counterbores, tightened in a cross pattern.
   Spin it by hand: runout should stay under 0.5 mm. If not, rotate the plate a quarter turn
   on the hub and try again.

## 4.4 Zero sensor

1. The optical fork is mounted flat on the board on two nylon standoffs (6 or 8 mm, depending
   on how deep the beam is in the slot), with M3 x 20 screws from below and nylon nuts on top.
   The slot is centred 68.5 mm from the axis on the x axis.
2. Pass the cable down through the Ø6 hole, then fill the hole with 5-minute epoxy from the top.
3. The flag is an M2 x 20 screw pushed down through the turntable at 68.5 mm from the axis,
   head in its counterbore and an M2 nut underneath (a drop of epoxy on the thread). Turn the
   turntable so the flag passes through the middle of the slot.
4. Run the motor and sensor cables flat under the board toward the enclosure's centre wall
   (around x = −75, y = +85), taped every 10 cm. About 0.40 m is needed for the motor and 0.53 m
   for the sensor.

## 4.5 Skirt and guide towers

The dome itself is the jig for the towers, so it must be finished before this step.

1. Lay the 10 skirt segments in a ring around the turntable, ends touching (18° cuts), with the
   console segment at the front over the cable slot. The inside face of each wall is at
   285.3 mm from the axis, which is 205.3 mm from the turntable edge. Measure 4 segments
   and push the whole ring until they match.
2. Set a guide tower behind every second segment, rod axis at 330.3 mm from the centre.
3. Lower the dome, camera tower on the right, so its 5 ears drop over the 5 rods. Check that
   the same width of skirt shelf shows all around.
4. Trace the outline of every skirt foot and tower base in pencil, then lift the dome straight up.
5. Drill and screw the skirt (2 screws per segment through the Ø12 access holes, 20 total),
   then the towers (4 screws each, 20 total). The Ø5.5 holes give about ±0.6 mm of adjustment.
6. Stick 3 mm EPDM foam (25 mm wide strips, ends cut at 18°) on 9 of the 10 skirt shelves. The
   console segment gets its strip after the console faceplate is installed.
7. Put the dome back and lift it 120 mm three times. The ears should slide along the rods
   without rubbing. If one rubs, loosen that tower, let the ear centre it and retighten.

## 4.6 Calibration fixtures

The three PLA fixtures sit on the turntable and centre themselves on it:

- `ptfe_base` (Ø166 x 15 mm) carries the 200 x 200 x 5 mm PTFE plate.
- `ptfe_riser_ring` (40 mm) goes on top of the base to raise the PTFE plate to a second height.
- `mirror_ball_ring` holds the 2 in chrome ball at the centre of the base.

Only one ball on the turntable at a time.
