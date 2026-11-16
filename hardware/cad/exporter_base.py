"""Réexporte platine_moteur, jupe, tour_guidage et plateau_tournant (corrections du 10 oct.) dans l'orientation des anciens STL.
L'orientation est retrouvée en recalant l'ancienne pièce du modèle sur l'ancien STL (trimesh.registration.mesh_other)."""
import sys, os, numpy as np, trimesh
import dome_gen as D, dome_photo as DP
sys.path.insert(0, sys.argv[1]); import ancien_base as OLD
IMP = os.path.expanduser('~/Desktop/Biomed/Dome_PS16_impression')
new_parts, _ = DP.build(); old_parts, _ = OLD.build()
jobs = [('platine_moteur', 'platine_moteur', '2_Premieres_pieces_PETG-CF/platine_moteur.stl'),
        ('jupe_0', 'jupe', '4_Production_ASA/c_Base/jupe (x10).stl'),
        ('tour_guidage_0', 'tour_guidage', '4_Production_ASA/c_Base/tour_guidage (x5).stl'),
        ('plateau_tournant', 'plateau_tournant', '4_Production_ASA/c_Base/plateau_tournant.stl')]
for key, nom, rel in jobs:
    old_stl = trimesh.load(os.path.join('sauvegarde_2026-10-10/base', os.path.basename(rel)))
    old_m, new_m = D.to_tm(old_parts[key]), D.to_tm(new_parts[key])
    T, cost = trimesh.registration.mesh_other(old_m, old_stl, samples=800, scale=False, icp_first=10, icp_final=60)
    new_stl = new_m.copy(); new_stl.apply_transform(T)
    dz = new_stl.bounds[0][2]
    print(f'{nom} : recalage {cost:.4f} mm ; ancien fond z = {old_stl.bounds[0][2]:.3f}, nouveau = {dz:.3f} ; '
          f'taille {np.round(new_stl.extents, 1)} (avant {np.round(old_stl.extents, 1)}) ; volume {new_stl.volume/1000:.1f} (avant {old_stl.volume/1000:.1f}) cm³ ; étanche {new_stl.is_watertight}')
    assert cost < 0.05, 'recalage raté'
    new_stl.apply_translation((0, 0, -dz))
    new_stl.export(os.path.join(IMP, rel))
