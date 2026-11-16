"""Réexporte les 2 adaptateurs de port (orientation d'impression d'origine) après l'ajout du jeu autour des bossages (10 oct.)."""
import sys, numpy as np, trimesh
import dome_gen as D, dome_photo as DP
from dome_photo import BOSS_R, BOSS_UP, zen_pts, port_pts, nrm, place, frame, U, M, Z
from dome_gen import U_PORT, E1_PORT, PORT_FACE
OUT = sys.argv[1]
parts, _ = DP.build()
def ring(n, p, r):   # couronne autour du bossage, sous son dessus
    return place(M.cylinder(BOSS_UP, r, r, 48), frame(n), p) - place(M.cylinder(BOSS_UP + 1, BOSS_R, BOSS_R, 48).translate((0, 0, -0.5)), frame(n), p)
for name, bosses in (('adaptateur_zenith', [(nrm[i], p) for i, p in zen_pts.items()]), ('adaptateur_oblique', [(nrm[PORT_FACE], p) for p in port_pts])):
    m = parts[name]
    gap = sum((m ^ ring(n, p, BOSS_R + 0.35)).volume() for n, p in bosses)
    seat = sum((m ^ place(M.cylinder(0.3, BOSS_R - 0.5, BOSS_R - 0.5, 32).translate((0, 0, BOSS_UP)), frame(n), p)).volume() for n, p in bosses)
    t = D.to_tm(m)
    R = np.diag([1.0, -1.0, -1.0]) if name == 'adaptateur_zenith' else frame(U_PORT, E1_PORT).T   # zénith : dessus à plat ; oblique : dessous à plat
    T = np.eye(4); T[:3, :3] = R; t.apply_transform(T)
    t.apply_translation(-np.array([(t.bounds[0][0] + t.bounds[1][0])/2, (t.bounds[0][1] + t.bounds[1][1])/2, t.bounds[0][2]]))
    old = trimesh.load(f'sauvegarde_2026-10-10/{name}.stl')
    print(f'{name} : matière dans le jeu de 0,35 mm = {gap:.2f} mm³ (doit être 0) ; appui sur le dessus des bossages = {seat:.1f} mm³ (doit être > 0) ; '
          f'taille {np.round(t.extents, 1)} (avant {np.round(old.extents, 1)}) ; volume {t.volume/1000:.1f} cm³ (avant {old.volume/1000:.1f})')
    t.export(f'{OUT}/{name}.stl')
