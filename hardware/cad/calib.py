# Supports de calibration (PLA noir) : coiffes centrées sur le plateau tournant Ø160
# Repère O (centre de l'objet) ; dessus du plateau tournant à z = -ZO + 36 = -24.
import os, json, numpy as np, manifold3d as m3
import dome_gen as D, dome_photo as DP
from dome_gen import M
ZO = DP.ZO; Z_DISK = -ZO + 36.0
R_BALL = 25.4            # bille chrome 2 po
PTFE = (200.0, 200.0, 5.0)   # COYOUCO 200 x 200 x 5 (Amazon B0DKJN6KH7)
GLASS = (100.0, 100.0, 3.0)   # damier Aurorad 100 x 100 ; épaisseur à mesurer (3 mm supposés)

def cyl(z0, z1, r, seg=128): return M.cylinder(z1 - z0, r, r, seg).translate((0, 0, z0))
def cap(z_rest, z_top, r_in_skirt, r_out, plate=3.0, skirt=6.0):
    """coiffe : jupe qui descend autour de la pièce du dessous (centrage), paroi, plateau du dessus"""
    c = cyl(z_rest - skirt, z_top, r_out) - cyl(z_rest - skirt - 1, z_rest, r_in_skirt)
    if z_top - plate > z_rest + 0.5: c = c - cyl(z_rest - 0.01, z_top - plate, r_out - 7.0)
    return c

def jigs():
    j, load = {}, {}
    # A : socle PTFE bas (dessus du PTFE à z = -10)
    a_top = -15.0
    j['socle_ptfe'] = cap(Z_DISK, a_top, 80.5, 83.0)
    load['socle_ptfe'] = M.cube(PTFE, True).translate((0, 0, a_top + PTFE[2]/2))
    # B : rehausse de 35 mm posée sur A (dessus du PTFE à z = +25)
    b_top = a_top + 35.0
    j['rehausse_ptfe'] = cap(a_top, b_top, 83.5, 86.0, skirt=5.0)
    load['rehausse_ptfe'] = M.cube(PTFE, True).translate((0, 0, b_top + PTFE[2]/2))
    # C : nid de bille (3 sièges Ø24 : centre et ±35 mm) ; une bille à la fois (charge du moteur)
    n_top = Z_DISK + 4.0; r_seat = 12.0
    nest = cap(Z_DISK, n_top, 80.5, 83.0, plate=4.0)
    for x in (-35.0, 0.0, 35.0): nest = nest - M.cylinder(10, r_seat, r_seat, 64).translate((x, 0, Z_DISK - 1))
    j['nid_bille'] = nest
    zc = n_top + np.sqrt(R_BALL**2 - r_seat**2)
    load['nid_bille'] = m3.Manifold.sphere(R_BALL, 96).translate((0, 0, zc))
    # D : support du damier (poche 100,8 x 100,8 x 1,5 + 2 encoches pour les doigts)
    d_top = -3.5
    dam = cap(Z_DISK, d_top, 80.5, 83.0) - M.cube((100.8, 100.8, 3), True).translate((0, 0, d_top))
    for x in (-50.4, 50.4): dam = dam - M.cylinder(10, 9, 9, 48).translate((x, 0, d_top - 6))
    j['support_damier'] = dam
    load['support_damier'] = M.cube(GLASS, True).translate((0, 0, d_top - 1.5 + GLASS[2]/2))
    return j, load, zc

if __name__ == "__main__":
    parts, _ = DP.build()
    j, load, zc = jigs()
    disk = parts['plateau_tournant']
    fixed = DP.U([parts[k] for k in parts if k not in ('plateau_tournant', 'moyeu', 'drapeau', 'moteur', 'vis', 'vis_bois')])
    res = {}
    for k in j:
        stack = j[k] + (j['socle_ptfe'] if k == 'rehausse_ptfe' else M.cube((0.01, 0.01, 0.01)).translate((0, 0, -500)))
        r = dict(vs_plateau=round((j[k] ^ disk).volume(), 2),
                 vs_socle=round((j['rehausse_ptfe'] ^ j['socle_ptfe']).volume(), 2) if k == 'rehausse_ptfe' else 0.0,
                 charge_vs_support=round((load[k] ^ j[k]).volume(), 2),
                 charge_vs_plateau=round((load[k] ^ disk).volume(), 2))
        # la charge tourne avec le plateau : balayage de 0 à 90° (symétrie du carré)
        worst = 0.0
        for a in range(0, 91, 15):
            worst = max(worst, ((load[k].rotate((0, 0, a)) + stack.rotate((0, 0, a))) ^ fixed).volume())
        r['vs_dome_en_rotation'] = round(worst, 2)
        res[k] = r
    print(json.dumps(res, indent=1))
    print(f"centre de la bille à z = {zc:+.1f} mm de O (bas de la bille à {zc - R_BALL - Z_DISK:.1f} mm au-dessus du plateau)")
    print(f"PTFE : dessus à z = {-15 + 5:+.0f} (socle) et {20 + 5:+.0f} (socle + rehausse) ; damier : dessus à ≈ {-3.5 - 1.5 + GLASS[2]:+.1f} mm")
    out = os.path.join('stl_final', 'PLA'); os.makedirs(out, exist_ok=True)
    vol = {}
    for k, m in j.items():
        D.to_tm(D.lay_flat(m, -D.Z if k != 'nid_bille' else -D.Z)).export(os.path.join(out, k + '.stl'))
        vol[k] = round(m.volume()/1000, 1); print(k, [round(x) for x in np.array(m.bounding_box()[3:]) - np.array(m.bounding_box()[:3])], vol[k], 'cm³')
    json.dump(dict(checks=res, vol_cm3=vol, ball_center_z=round(zc, 2)), open('calib_data.json', 'w'), ensure_ascii=False)
    # export pour la visionneuse
    import trimesh
    sc = trimesh.Scene()
    for k, m in list(j.items()) + [('charge_' + k, v) for k, v in load.items()]:
        sc.add_geometry(D.to_tm(m.translate((0, 0, ZO))), node_name=k, geom_name=k)
    sc.export('calib.glb')
