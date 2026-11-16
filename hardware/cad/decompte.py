"""Décompte automatique de la quincaillerie à partir du modèle (source unique pour le guide de montage).
Produit :
  - nomenclature_modele.json : chaque insert, chaque vis (de quelle pièce vers quelle pièce), les vis à bois par groupe,
    les voisins de chaque triangle (qui porte la lèvre, qui se pose par-dessus), les étoiles et les panneaux qu'elles tiennent ;
  - ../manuel/assemblage_manuel.glb : le modèle avec les inserts et les vis regroupés par pièce (pour la visionneuse par étapes).
Lancer : ~/.venvs/dome3d/bin/python decompte.py   (dans ce dossier)"""
import os, json, collections, numpy as np, trimesh
import dome_gen as D
import dome_photo as DP
from manifold3d import Manifold as M
from dome_gen import P, H, V, LED, PORT_FACE, TOP, PIN_EDGES, eq_edges, is_eq, edge_key, cent, el, az
from dome_photo import CORN, zen_pts, port_pts, pod_ears, handle_pts, HANDLE_EDGES, faces_of, nrm, apex, Z, place, frame, BOSS_UP, U

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(HERE, '..', 'manuel'); os.makedirs(OUTD, exist_ok=True)
INS_L, INS_RO = 5.7, 2.3          # insert M3 x 5,7, Ø ext. 4,6

parts, screws = DP.build()
n_model_screws = len(screws)

# ---------- inserts et vis M3 (taggés) ----------
inserts, vis = [], []             # inserts : (pièce qui le reçoit, normale, point de la face extérieure du panneau)
def add(host, src, n, p, L, kind='M3'):
    inserts.append((host, n, p)) if host else None
    vis.append(dict(de=src, dans=host, L=L, n=n, p=p))
for v in range(len(V)):
    if V[v, 2] < -1e-9 or v == apex or v not in faces_of: continue
    sname = ('etoile_' if not is_eq(v) else 'demi_etoile_') + f'{v:02d}'
    for i in faces_of[v]:
        if v not in CORN[i]: continue
        p = CORN[i][v]; add(f'panneau_{i:02d}', sname, nrm[i], p, 8.0)
for i in LED:
    for p in pod_ears(i): add(f'panneau_{i:02d}', f'capsule_{i:02d}', nrm[i], p, 8.0)
for i, p in zen_pts.items(): add(f'panneau_{i:02d}', 'adaptateur_zenith', nrm[i], p, 8.0)
for p in port_pts: add(f'panneau_{PORT_FACE:02d}', 'adaptateur_oblique', nrm[PORT_FACE], p, 8.0)
handle_panel = {}
for k, e in enumerate(HANDLE_EDGES):
    host = [i for i, f in enumerate(H) if e[0] in f and e[1] in f][0]; handle_panel[k] = host
    for p in handle_pts(e):
        inserts.append((f'panneau_{host:02d}', Z, p + np.array([0, 0, 7.0 - BOSS_UP])))
        vis.append(dict(de=f'poignee_{k}', dans=f'panneau_{host:02d}', L=16.0, n=Z, p=p))
for n, p, L in DP.DRIVE_SCREWS:
    vis.append(dict(de='platine_moteur' if L == 8.0 else 'plateau_tournant', dans='moteur' if L == 8.0 else 'moyeu', L=L, n=n, p=p))
assert len(vis) == n_model_screws, (len(vis), n_model_screws)
# vis hors modèle (trous Ø2,6 autotaraudés et caméra) : comptées à part
extra = [dict(de='tour_camera', dans='adaptateur_oblique', L=16.0, nb=3, note='trous Ø2,6 dans l’adaptateur, vissage direct dans le plastique'),
         dict(de='bouchon_zenith', dans='adaptateur_zenith', L=16.0, nb=3, note='trous Ø2,6 dans l’adaptateur, vissage direct dans le plastique'),
         dict(de='camera_Triton', dans='tour_camera', L=8.0, nb=4, note='4 trous M3 du dessous de la caméra ; PAS plus long que 8 mm')]

# ---------- vis à bois par groupe ----------
wood_heads = {}
def count_wood(fn, key):
    DP.WOOD.clear(); DP.FEET_UP.clear(); fn()
    wood_heads[key] = ([h.copy() for h in DP.WOOD], [h.copy() for h in DP.FEET_UP])
    return len(DP.WOOD) + len(DP.FEET_UP)
wood = collections.OrderedDict()
wood['jupe (2 par pan × 10)'] = count_wood(lambda: [DP.skirt(k) for k in range(10)], 'visbois__jupe')
wood['tours de guidage (4 par tour × 5)'] = count_wood(lambda: [DP.tower_post(e) for e in sorted(PIN_EDGES)], 'visbois__tour_guidage')
wood['platine du moteur'] = count_wood(DP.drive, 'visbois__platine_moteur')
wood['boîtier'] = count_wood(DP.enclosure, 'visbois__boitier')
wood['pieds (2 par pied × 6, vissées par-dessous)'] = count_wood(DP.feet, 'visbois__pied')
DP.WOOD.clear(); DP.FEET_UP.clear(); parts2, _ = DP.build()      # remet WOOD / FEET_UP dans l'état du modèle complet

# ---------- triangles : voisins, lèvres, particularités ----------
ring_of = lambda i: round(el[i], 1)
panels = {}
for i, f in enumerate(H):
    nb_lip, nb_over = [], []
    for a, b in zip(f, f[1:] + f[:1]):
        if is_eq(a) and is_eq(b): continue
        j = [k for k in range(len(H)) if k != i and a in H[k] and b in H[k]]
        if not j: continue
        j = j[0]
        (nb_lip if i < j else nb_over).append(f'panneau_{j:02d}')
    eqe = [edge_key(a, b) for a, b in zip(f, f[1:] + f[:1]) if is_eq(a) and is_eq(b)]
    feats = []
    if i in TOP: feats.append('1 insert pour l’adaptateur zénith')
    if i == PORT_FACE: feats.append('port oblique : 3 inserts pour l’adaptateur oblique')
    if i in LED: feats.append(f'LED : 2 inserts pour capsule_{i:02d}')
    if eqe: feats.append('rebord d’équateur (appui sur la jupe)')
    if eqe and eqe[0] in PIN_EDGES: feats.append(f'oreille pour tour_guidage_{sorted(PIN_EDGES).index(eqe[0])}')
    for k, e in enumerate(HANDLE_EDGES):
        if eqe and eqe[0] == e: feats.append(f'2 inserts pour poignee_{k}')
    ins_here = [x for x in inserts if x[0] == f'panneau_{i:02d}']
    panels[f'panneau_{i:02d}'] = dict(elevation_deg=round(float(el[i]), 1), azimut_deg=round(float(az[i]), 1),
        dossier='a_Triangles_sans_support' if i < 20 else 'b_Triangles_avec_supports',
        inserts=len(ins_here), porte_la_levre_pour=nb_lip, se_pose_sur_la_levre_de=nb_over, particularites=feats)
stars = {}
for v in range(len(V)):
    if V[v, 2] < -1e-9 or v == apex or v not in faces_of: continue
    sname = ('etoile_' if not is_eq(v) else 'demi_etoile_') + f'{v:02d}'
    tgt = [x['dans'] for x in vis if x['de'] == sname]
    stars[sname] = dict(vis_M3x8=len(tgt), panneaux=sorted(tgt), elevation_deg=round(float(np.degrees(np.arcsin(V[v, 2]/np.linalg.norm(V[v])))), 1))
# ordre : chaque panneau doit venir après tous ses voisins de numéro plus petit (lèvre en dessous) -> vrai pour l’ordre 00 -> 39
order_ok = all(int(o[-2:]) < int(k[-2:]) for k, p in panels.items() for o in p['se_pose_sur_la_levre_de'])

# ---------- résumé ----------
cnt = collections.Counter((x['de'].rstrip('0123456789_'), x['L']) for x in vis)
by_len = collections.Counter(x['L'] for x in vis)
for e in extra: by_len[e['L']] += e['nb']
host_cnt = collections.Counter(h for h, _, _ in inserts)
out = dict(
    source='decompte.py (modèle dome_photo.py)', n_inserts=len(inserts), n_vis_M3_modele=n_model_screws,
    vis_M3_par_longueur_total={f'M3x{int(L)}': n for L, n in sorted(by_len.items())},
    vis_M3_hors_modele=extra, vis_bois=dict(wood), n_vis_bois=sum(wood.values()),
    vis_par_piece={f'{a} -> M3x{int(L)}': n for (a, L), n in sorted(cnt.items())},
    inserts_par_type={k: sum(1 for x in vis if x['dans'] and x['dans'].startswith('panneau') and x['de'].startswith(k))
                      for k in ('etoile_', 'demi_etoile_', 'capsule_', 'adaptateur_zenith', 'adaptateur_oblique', 'poignee_')},
    inserts_par_panneau=dict(sorted(host_cnt.items())),
    panneaux=panels, etoiles=stars, ordre_00_a_39_valide=order_ok,
    led_faces=[f'panneau_{i:02d}' for i in LED], port_oblique=f'panneau_{PORT_FACE:02d}', panneaux_du_haut=[f'panneau_{i:02d}' for i in TOP],
    tours_guidage={f'tour_guidage_{k}': [f'panneau_{i:02d}' for i, f in enumerate(H) if e[0] in f and e[1] in f] for k, e in enumerate(sorted(PIN_EDGES))},
    poignees={f'poignee_{k}': f'panneau_{h:02d}' for k, h in handle_panel.items()},
    noms_objets_glb=sorted(parts.keys()))
# groupes de la visionneuse : 'vis__<pièce vissée>' et 'ins__<panneau>' (nombre et longueur), vis à bois en un seul objet
gv = collections.defaultdict(lambda: dict(n=0, L=set()))
for x in vis: gv[x['de']]['n'] += 1; gv[x['de']]['L'].add(int(x['L']))
out['groupes_vis'] = {f'vis__{k}': dict(n=v['n'], type=f"M3x{min(v['L'])}") for k, v in sorted(gv.items())}
out['groupes_inserts'] = {f'ins__{k}': n for k, n in sorted(host_cnt.items())}
out['objets_glb_manuel'] = sorted([k for k in parts.keys() if k not in ('vis', 'vis_bois')] + list(out['groupes_vis']) + list(out['groupes_inserts']) + list(wood_heads))
out['groupes_vis_bois'] = {k: len(a) + len(b) for k, (a, b) in wood_heads.items()}
json.dump(out, open(os.path.join(HERE, 'nomenclature_modele.json'), 'w'), ensure_ascii=False, indent=1)

# ---------- GLB du manuel : inserts et vis regroupés par pièce ----------
ins_groups = collections.defaultdict(list)
for h, n, p in inserts:
    ins_groups[h].append(place(M.cylinder(INS_L, INS_RO, INS_RO, 16).translate((0, 0, BOSS_UP - INS_L)), frame(n), p))
vis_groups = collections.defaultdict(list)
for x in vis: vis_groups[x['de']].append(DP.screw(x['n'], x['p'], x['L']))
sc = trimesh.Scene()
for k, m in parts2.items():
    if k in ('vis', 'vis_bois'): continue
    sc.add_geometry(D.to_tm(m.translate((0, 0, D.Z_O))), node_name=k, geom_name=k)
for h, ms in ins_groups.items(): sc.add_geometry(D.to_tm(U(ms).translate((0, 0, D.Z_O))), node_name=f'ins__{h}', geom_name=f'ins__{h}')
for s, ms in vis_groups.items(): sc.add_geometry(D.to_tm(U(ms).translate((0, 0, D.Z_O))), node_name=f'vis__{s}', geom_name=f'vis__{s}')
for key, (wd, fu) in wood_heads.items():
    hs = [M.cylinder(3, 4, 4, 20).translate(tuple(h)) + M.cylinder(16, 2.0, 2.0, 16).translate((h[0], h[1], h[2] - 16)) for h in wd]
    hs += [M.cylinder(3, 4, 4, 20).translate((h[0], h[1], h[2] - 3)) + M.cylinder(16, 2.0, 2.0, 16).translate(tuple(h)) for h in fu]
    sc.add_geometry(D.to_tm(U(hs).translate((0, 0, D.Z_O))), node_name=key, geom_name=key)
sc.export(os.path.join(OUTD, 'assemblage_manuel.glb'))

print(f"inserts : {len(inserts)} ; vis M3 du modèle : {n_model_screws} ; vis à bois : {sum(wood.values())}")
print("inserts par type :", out['inserts_par_type'])
print("vis M3 par longueur (avec tour, bouchon, caméra) :", out['vis_M3_par_longueur_total'])
print("vis à bois :", dict(wood))
print("ordre 00 -> 39 valide :", order_ok)
print("étoiles :", {k: v['vis_M3x8'] for k, v in stars.items()})
print("export : nomenclature_modele.json et manuel/assemblage_manuel.glb")
