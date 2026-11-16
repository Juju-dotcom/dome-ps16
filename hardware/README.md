# Hardware

All parts were printed on a Bambu X2D, 0.4 mm nozzle, textured PEI plate, 0.20 mm layers.
The STLs are already oriented for printing, so don't rotate them or use auto-orient.

## Printed parts

| File | Qty | Material | Walls / infill | Notes |
|---|---|---|---|---|
| `stl/dome/panel_00` to `panel_19` | 1 each | ASA | 4 / 15 % | no supports, 5 mm brim, ironing on top |
| `stl/dome/panel_20` to `panel_39` | 1 each | ASA | 4 / 15 % | tree supports, 5 mm brim |
| `stl/dome/hub_*` | 1 each (15) | PETG-CF | 4 / 25 % | tree supports, dry the filament first |
| `stl/dome/rim_hub_*` | 1 each (10) | PETG-CF | 4 / 25 % | tree supports |
| `stl/dome/led_capsule_*` | 1 each (16) | PETG-CF | 4 / 25 % | the number is the panel it goes on |
| `stl/dome/camera_adapter_zenith` | 1 | PETG-CF | 4 / 25 % | |
| `stl/dome/camera_adapter_oblique` | 1 | PETG-CF | 4 / 25 % | |
| `stl/dome/top_cap_knob` | 1 | PETG-CF | 5 / 30 % | used to lift the dome |
| `stl/base/skirt_segment` | 9 | ASA | 4 / 20 % | 5 mm brim |
| `stl/base/skirt_segment_console` | 1 | ASA | 4 / 20 % | replaces one skirt segment, holds the console |
| `stl/base/console_faceplate` | 1 | ASA | 4 / 20 % | face down, no supports |
| `stl/base/guide_tower` | 5 | ASA | 4 / 40 % | |
| `stl/base/turntable` | 1 | ASA | 4 / 50 % | 5 mm brim |
| `stl/base/motor_plate` | 1 | PETG-CF | 4 / 25 % | |
| `stl/base/foot_80mm` | 6 | PETG-CF | 4 / 25 % | |
| `stl/camera/camera_tower` | 1 | PETG-CF | 6 / 25 % | 8 mm brim; check the bridges over the 2 windows |
| `stl/camera/lens_window_cover` | 2 | PETG-CF | 4 / 25 % | clips over the lens adjustment windows |
| `stl/enclosure/enclosure_shell_vented` or `_closed` | 1 | ASA | 4 / 20 % | 3 mm brim max (the part is 250 mm on a 256 mm bed) |
| `stl/enclosure/enclosure_lid` | 1 | ASA | 4 / 20 % | |
| `stl/enclosure/db37_plate` | 1 | ASA | 4 / 20 % | |
| `stl/calibration/*` | 1 each | PLA | 3 / 15 % | only needed for calibration |
| `stl/test/test_corner_A`, `_B` | 1 each | ASA | 4 / 15 % | print first to check the lip fit and the insert holes |

ASA needs the enclosure door closed and an exhaust fan. Print 2 or 3 plates while
watching before letting it run overnight.

Approximate filament use: 2.9 kg ASA, 0.8 kg PETG-CF, 0.4 kg PLA.

## Base board

`board/baseboard_outline.dxf` (and `.svg`) is a 1:1 template for the 5/8 in melamine
board. Print it on paper, tape it to the board and cut along the line.

## Bill of materials

See [`bom.csv`](bom.csv). Supplier references are the ones I ordered (mostly from ABRA
Electronics in Montreal), but any equivalent part works. Screw and insert counts come from
the CAD model, so buy about 10 % extra.
