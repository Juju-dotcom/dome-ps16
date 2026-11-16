"""Réexporte les 16 capsules LED après la correction du 10 oct. (l'étoile entre par le côté panneau) et vérifie le chemin d'entrée."""
import sys, os, numpy as np, trimesh
import dome_gen as D, dome_photo as DP
from dome_photo import led_frame, frame
from dome_gen import LED
DIR2, DIR3 = sys.argv[1], sys.argv[2]
parts, _ = DP.build()
worst = 0.0
for i in LED:
    cap, star = parts[f'capsule_{i:02d}'], parts[f'etoile_LED_{i:02d}']
    u = led_frame(i)[0]
    # l'étoile sort vers le panneau (-u) par pas de 0,25 mm jusqu'à 5 mm : aucun contact permis
    hit = max((cap ^ star.translate(tuple(-d*u))).volume() for d in np.arange(0.0, 5.01, 0.25))
    worst = max(worst, hit)
    t = D.to_tm(cap)
    R = np.diag([1.0, -1.0, -1.0]) @ frame(u).T          # paroi du dessus à plat sur le plateau
    T = np.eye(4); T[:3, :3] = R; t.apply_transform(T)
    t.apply_translation(-np.array([(t.bounds[0][0] + t.bounds[1][0])/2, (t.bounds[0][1] + t.bounds[1][1])/2, t.bounds[0][2]]))
    old = trimesh.load(f'sauvegarde_2026-10-10/capsules/capsule_{i:02d}.stl')
    out = DIR2 if i == 1 else DIR3
    t.export(os.path.join(out, f'capsule_{i:02d}.stl'))
    print(f'capsule_{i:02d} : contact pendant l’entrée {hit:.3f} mm³ ; taille {np.round(sorted(t.extents), 1)} (avant {np.round(sorted(old.extents), 1)}) ; '
          f'volume {t.volume/1000:.2f} cm³ (avant {old.volume/1000:.2f}) ; étanche {t.is_watertight}')
print('pire contact pendant l’entrée :', round(worst, 3), 'mm³ (doit être 0)')
