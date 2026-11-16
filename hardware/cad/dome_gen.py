"""Dôme géodésique 2V imprimable (PETG noir) pour le banc de stéréophotométrie.
Unités : mm. Repère « O » : origine au centre de référence de l'objet (= centre du dôme), z vers le haut.
Dans le monde, O est à Z_O = 60 mm au-dessus du dessus de la planche de base (plateau tournant : dessus à z = 36).

Pièces verrouillées (fiches) :
  - LED Luxeon Star SW-01 (SABER 2) : étoile hexagonale 19,9 (plats) x 20,8 mm, PCB 1,6 mm, lentille 2,55 mm,
    4 encoches R1,6 à (±8,225 ; ±4,75), plots P3 (+) à (7,9 ; 0) et P7 (-) à (-7,9 ; 0).
  - Caméra LUCID Triton 29 x 29 x 45 mm ; objectif Fujinon HF25XA-5M Ø29,5 x 46,5 (bagues + vis ≈ Ø40).
  - Face avant de l'objectif à 408 mm de O (champ 126 x 106 mm, centre optique à 399 mm).
"""
import os, json, numpy as np, trimesh
from manifold3d import Manifold as M
from geo import geodesic2v
from manifold3d import OpType
OPADD = OpType.Add

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl"); os.makedirs(OUT, exist_ok=True)
R = 300.0            # rayon des sommets (face intérieure)
T = 2.5              # épaisseur des panneaux
F = 2.5              # épaisseur des brides
HF, HF_EQ = 10.0, 24.0   # hauteur des brides (arêtes / équateur)
Z_O = 60.0
BOSS_R, POCKET_R, GAP, STAR_T = 15.0, 10.9, 2.4, 1.6
NOTCH = [(8.225, 4.75), (-8.225, 4.75), (8.225, -4.75), (-8.225, -4.75)]
CAM_FRONT, LENS_L = 408.0, 46.5
PORT_BORE = 40.0     # rayon du trou des ports
S_TOP = 310.0        # dessus des adaptateurs de port (même distance pour les deux ports)
SEG = 72
Z = np.array([0, 0, 1.0])

def unit(v): v = np.asarray(v, float); return v/np.linalg.norm(v)
def frame(u, e1=None):
    u = unit(u)
    if e1 is None:
        e1 = np.cross(Z, u) if np.linalg.norm(np.cross(Z, u)) > 1e-6 else np.array([1.0, 0, 0])
    e1 = unit(e1 - (e1 @ u)*u); e2 = np.cross(u, e1)
    return np.column_stack([e1, e2, u])
def place(m, Rm, t=(0, 0, 0)):
    return m.transform(np.hstack([Rm, np.asarray(t, float).reshape(3, 1)]).tolist())
def cyl(u, s0, s1, r0, r1=None, off=(0, 0), e1=None, seg=SEG):
    c = M.cylinder(s1 - s0, r0, r0 if r1 is None else r1, seg).translate((off[0], off[1], s0))
    return place(c, frame(u, e1))
def box(u, x0, x1, y0, y1, s0, s1, e1=None):
    b = M.cube((x1 - x0, y1 - y0, s1 - s0)).translate((x0, y0, s0))
    return place(b, frame(u, e1))
def union(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    return M.batch_boolean(ms, OPADD) if ms else M()
def slab(m, n, a, b): return m.trim_by_plane(tuple(n), a).trim_by_plane(tuple(-np.asarray(n)), -b)

# ---------------- géométrie de base ----------------
V, H = geodesic2v()
P = V*R
apex = int(np.argmax(V[:, 2]))
cent = {i: unit(P[f].mean(0)) for i, f in enumerate(H)}
el = {i: np.degrees(np.arcsin(c[2])) for i, c in cent.items()}
az = {i: np.degrees(np.arctan2(c[1], c[0])) % 360 for i, c in cent.items()}
def fnormal(f):
    n = unit(np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]])); return n if n @ P[f].mean(0) > 0 else -n
is_eq = lambda i: abs(V[i, 2]) < 1e-9
PORT_FACE = min((i for i in cent if abs(el[i] - 52.6) < 0.5), key=lambda i: abs(((az[i] - 18) + 180) % 360 - 180))
U_PORT = fnormal(H[PORT_FACE])            # face équilatérale : normale = direction du centre
TOP = [i for i, f in enumerate(H) if apex in f]

# ---------------- choix des LED (16 sur 18) ----------------
grp = lambda e: sorted([i for i in cent if abs(el[i] - e) < 0.5], key=lambda i: az[i])
def ps_score(ids, cams):
    rng = np.random.default_rng(1); N = rng.normal(size=(6000, 3)); N /= np.linalg.norm(N, axis=1, keepdims=True)
    L = np.array([cent[i] for i in ids]); tot = []
    for v in cams:
        g = []
        for n in N[N @ v > 0.1]:
            m = L @ n > 0.05
            if m.sum() < 3: g.append(1e3); continue
            Mi = np.linalg.inv(L[m].T @ L[m]); Pp = np.eye(3) - np.outer(n, n); g.append(np.sqrt(np.trace(Pp @ Mi @ Pp)))
        tot.append(np.percentile(g, 95))
    return max(tot)
base = grp(10.8) + grp(40.1)
LED = min((base + [k] for k in grp(72.5)), key=lambda ids: ps_score(ids, [Z, U_PORT]))

# ---------------- panneaux ----------------
def edge_key(a, b): return (a, b) if a < b else (b, a)
eq_edges = sorted({edge_key(a, b) for f in H for a, b in zip(f, f[1:] + f[:1]) if is_eq(a) and is_eq(b)},
                  key=lambda e: np.degrees(np.arctan2(*(P[e[0]] + P[e[1]])[[1, 0]])) % 360)
PIN_EDGES = set(eq_edges[0::2])
def w_out(a, b):
    p, q = P[a], P[b]; e = unit(q - p); mid = (p + q)/2; return unit(mid - (mid @ e)*e)
def pin_xy(e):
    a, b = e; return (P[a] + P[b])/2 + w_out(a, b)*(T + 0.55*HF_EQ)

zen_bolts = []   # 5 vis des panneaux du haut vers l'adaptateur zénith
nb = [j for f in (H[i] for i in TOP) for j in f if j != apex]
edge_az = sorted({round(np.degrees(np.arctan2(P[j, 1], P[j, 0])) % 360, 3) for j in nb})
zen_bolt_az = [a + 36.0 for a in edge_az]
PORT_V = [unit(P[j] - (P[j] @ U_PORT)*U_PORT) for j in H[PORT_FACE]]   # directions des sommets dans le plan
E1_PORT = PORT_V[0]

def panel(i):
    f = H[i]; n = fnormal(f); d0 = n @ P[f[0]]
    wedge = M.hull_points([(0, 0, 0)] + [tuple(2.2*P[j]) for j in f])
    parts = [slab(wedge, n, d0, d0 + T)]
    cuts = []
    for a, b in zip(f, f[1:] + f[:1]):
        c3 = [j for j in f if j not in (a, b)][0]
        m = unit(np.cross(P[a], P[b])); m = m if m @ P[c3] > 0 else -m
        eq = is_eq(a) and is_eq(b); hf = HF_EQ if eq else HF
        fl = slab(wedge.trim_by_plane(tuple(m), 0.0).trim_by_plane(tuple(-m), -F), n, d0, d0 + T + hf)
        parts.append(fl)
        ek = edge_key(a, b); p, q = P[ek[0]], P[ek[1]]; w = w_out(*ek)
        if eq:
            if ek in PIN_EDGES:
                c = pin_xy(ek); cuts.append(place(M.cylinder(40, 4.3, 4.3, 48, True), frame(Z), c))
        else:
            for lam in (0.3, 0.7):
                c = p + lam*(q - p) + w*(T + 0.5*hf)
                cuts.append(place(M.cylinder(30, 1.7, 1.7, 24, True), frame(m), c))
    body = union(parts)
    info = dict(id=i, el=round(el[i], 1), az=round(az[i], 1), led=None, port=None)
    if i in LED:
        u = cent[i]; s0 = d0/(u @ n); so = (d0 + T)/(u @ n); sf = so + GAP; st = sf + STAR_T
        body = body + cyl(u, s0 + 0.5, st, BOSS_R)
        body = body - cyl(u, so, st + 1, POCKET_R)
        body = body + union([cyl(u, so - 0.5, sf, 2.3, off=o, seg=24) for o in NOTCH] +
                            [cyl(u, sf - 0.1, sf + STAR_T - 0.2, 1.35, off=o, seg=20) for o in NOTCH])
        cuts += [cyl(u, s0 - 1, so + 0.2, 6.5, 4.0),
                 box(u, POCKET_R - 1, BOSS_R + 1, -1.6, 1.6, so, st + 1), box(u, -BOSS_R - 1, -POCKET_R + 1, -1.6, 1.6, so, st + 1)]
        cuts += [cyl(u, st - 9, st + 1, 1.25, off=(0, s*12.95), seg=20) for s in (1, -1)]
        info['led'] = dict(emitter=((sf - 0.6)*u + np.array([0, 0, Z_O])).round(2).tolist(), dist_O=round(sf - 0.6, 1),
                           axis=u.round(4).tolist())
    if i in TOP:   # port zénith
        cuts.append(cyl(Z, 0, 420, PORT_BORE))
        cuts.append(cyl(Z, 0, 420, 62).trim_by_plane(tuple(n), d0 + T + 0.01))     # pas de bride sous l'adaptateur
        for a in zen_bolt_az:
            r = 53.0; cuts.append(cyl(Z, 200, 420, 1.7, off=(r*np.cos(np.radians(a)), r*np.sin(np.radians(a))), seg=20))
        info['port'] = 'zénith'
    if i == PORT_FACE:
        cuts.append(cyl(U_PORT, 0, 420, PORT_BORE))
        for v in PORT_V:
            o = 53.0*v; cuts.append(place(M.cylinder(420, 1.7, 1.7, 20), frame(U_PORT), o))
        info['port'] = 'oblique'
    if cuts: body = body - union(cuts)
    return body, info

# ---------------- adaptateurs, tour caméra, bouchon ----------------
def tower_holes(u, e1, s0, s1, r, rad=43.5):
    return [cyl(u, s0, s1, r, off=(rad*np.cos(np.radians(a)), rad*np.sin(np.radians(a))), e1=e1, seg=20) for a in (90, 210, 330)]

def _under(ids, extra=0.2):
    return union([slab(M.hull_points([(0, 0, 0)] + [tuple(2.2*P[j]) for j in H[i]]), fnormal(H[i]), 0, fnormal(H[i]) @ P[H[i][0]] + T + extra) for i in ids])

def adapter_zenith():
    lugs = [(53*np.cos(np.radians(a)), 53*np.sin(np.radians(a))) for a in zen_bolt_az]
    a = cyl(Z, 240, S_TOP, 47.5) + union([cyl(Z, 240, S_TOP - 4, 7, off=o, seg=32) for o in lugs])
    a = a - _under(TOP) - cyl(Z, 0, 420, PORT_BORE)
    cuts = []
    for o in lugs: cuts += [cyl(Z, 200, 420, 1.7, off=o, seg=20), cyl(Z, S_TOP - 9, 420, 3.1, off=o, seg=24)]
    cuts += tower_holes(Z, np.array([1.0, 0, 0]), S_TOP - 14, S_TOP + 1, 1.3)
    return a - union(cuts)

def adapter_port():
    d0 = U_PORT @ P[H[PORT_FACE][0]]; so = d0 + T; F_ = frame(U_PORT, E1_PORT)
    a = cyl(U_PORT, so, S_TOP, 47.5, e1=E1_PORT) + union([place(M.cylinder(S_TOP - 4 - so, 7, 7, 32).translate((0, 0, so)), frame(U_PORT), 53*v) for v in PORT_V])
    cuts = [cyl(U_PORT, 0, 420, PORT_BORE)]
    for v in PORT_V:
        cuts += [place(M.cylinder(420, 1.7, 1.7, 20), frame(U_PORT), 53*v), place(M.cylinder(420, 3.1, 3.1, 24).translate((0, 0, S_TOP - 9)), frame(U_PORT), 53*v)]
    cuts += tower_holes(U_PORT, E1_PORT, S_TOP - 14, S_TOP + 1, 1.3)
    return a - union(cuts)

C_RING = 7.9     # la bague de monture C dépasse de 7,9 mm devant le boîtier (dessin LUCID Triton)
def tower():
    """Tour caméra (repère local, axe z = axe optique, z = distance à O). Identique pour les deux ports.
    La caméra est vissée par ses 4 trous M3 du dessous (36 x 20 mm, dessin LUCID), comme le recommande LUCID."""
    u = Z; e1 = np.array([1.0, 0, 0])
    s_seat = CAM_FRONT + LENS_L             # appui de l'objectif sur la bague C
    s_body = s_seat + C_RING                # face avant du boîtier de la caméra
    t = cyl(u, S_TOP, S_TOP + 5, 48) - cyl(u, S_TOP - 1, S_TOP + 6, 35.0)
    t = t - union(tower_holes(u, e1, S_TOP - 1, S_TOP + 6, 1.7))
    legs = [place(M.cube((8, 10, s_body - 5 - (S_TOP + 5))).translate((34, -5, S_TOP + 5)),
                  np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])) for a in np.radians([30, 150, 270])]
    ring = cyl(u, s_body - 5, s_body, 42) - cyl(u, s_body - 6, s_body + 1, 16.0)
    L = 44.0
    sleeve = box(u, -20.5, 20.5, -20.5, 20.5, s_body, s_body + L) - box(u, -14.8, 14.8, -14.8, 14.8, s_body - 1, s_body + L + 1)
    t = union([t, ring, sleeve] + legs)
    Fy = frame(np.array([0, -1.0, 0]))
    holes = []
    for ax in (3.0, 39.0):
        for x in (-10.0, 10.0):
            holes.append(place(M.cylinder(12, 1.7, 1.7, 20), Fy, (x, -13.0, s_body + ax)))      # passage M3
            holes.append(place(M.cylinder(3, 3.3, 3.3, 24), Fy, (x, -19.3, s_body + ax)))       # lamage : tête à 4,8 mm du boîtier -> vis M3x8 = 3,2 mm de filet (dessin : 3,5 min à l'avant, 4,5 à l'arrière)
    return t - union(holes)

def port_cap():
    c = cyl(Z, 0, 4, 48) - union(tower_holes(Z, np.array([1.0, 0, 0]), -1, 5, 1.7))
    return c

def led_cap():
    c = M.cylinder(2.2, BOSS_R, BOSS_R, SEG) - M.cylinder(5, 6.0, 6.0, 40).translate((0, 0, -1))
    c = c - union([M.cylinder(5, 1.7, 1.7, 20).translate((0, s*12.95, -1)) for s in (1, -1)])
    return c + (M.cylinder(0.6, 10.3, 10.3, SEG) - M.cylinder(1, 8.0, 8.0, SEG).translate((0, 0, -0.2))).translate((0, 0, -0.6))

# ---------------- jupe (10 pièces) ----------------
def skirt(k):
    a, b = eq_edges[k]; p, q = P[a], P[b]
    ns = unit(((p + q)/2)*np.array([1, 1, 0])); ds = ns @ p
    lo, hi = -Z_O, 0.0
    wedge = M.hull_points([(0, 0, lo - 5), (0, 0, hi + 5)] + [tuple(2.2*np.array([v[0], v[1], z])) for v in (p, q) for z in (lo - 5, hi + 5)])
    zslab = lambda m, z0, z1: m.trim_by_plane((0, 0, 1), z0).trim_by_plane((0, 0, -1), -z1)
    parts = [zslab(slab(wedge, ns, ds, ds + T), lo, hi),
             zslab(slab(wedge, ns, ds, ds + T + HF_EQ), hi - F, hi),
             zslab(slab(wedge, ns, ds, ds + T + 20), lo, lo + F)]
    cuts = []; w = w_out(a, b)
    for v in (p, q):
        o = [x for x in (p, q) if x is not v][0]
        m = unit(np.cross(Z, v)); m = m if m @ o > 0 else -m
        parts.append(zslab(slab(wedge.trim_by_plane(tuple(m), 0).trim_by_plane(tuple(-m), -F), ns, ds, ds + T + 12), lo, hi))
        for z in (-20, -40):
            cuts.append(place(M.cylinder(30, 1.7, 1.7, 20, True), frame(m), unit(v*np.array([1, 1, 0]))*(R + T + 6) + np.array([0, 0, z])))
    for lam in (0.25, 0.75):
        c = p + lam*(q - p) + w*(T + 11); c[2] = lo; cuts.append(place(M.cylinder(20, 2.25, 2.25, 24, True), frame(Z), c))
    body = union(parts)
    kind = 'simple'
    if eq_edges[k] in PIN_EDGES:
        c = pin_xy(eq_edges[k]); c[2] = hi
        body = body + place(M.cylinder(12, 4.0, 4.0, 40), frame(Z), c) + place(M.cylinder(4, 4.0, 1.5, 40), frame(Z), c + np.array([0, 0, 12]))
        kind = 'goupille'
    if k == 1:
        e = unit(q - p); mid = (p + q)/2 + ns*(T/2) + np.array([0, 0, -30])
        cuts.append(place(M.cube((56, 12, 20), True), np.column_stack([e, Z, ns]), mid))
        for s in (1, -1):
            cuts.append(place(M.cylinder(20, 1.6, 1.6, 20, True), np.column_stack([e, Z, ns]), mid + s*31.75*e))
        kind = 'DB37'
    return body - union(cuts), kind

def turntable():
    d = M.cylinder(5, 80, 80, 128) - M.cylinder(3.2, 9.7, 9.7, 48).translate((0, 0, -0.1)) - M.cylinder(20, 2.6, 2.6, 24).translate((0, 0, -1))
    return d

# ---------------- export ----------------
def to_tm(m):
    mm = m.to_mesh(); return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)
def lay_flat(m, n):
    """tourne la pièce pour que n (normale extérieure) pointe vers +z, puis pose z min = 0"""
    Rm = frame(n).T; mm = place(m, Rm); bb = mm.bounding_box(); return mm.translate((-(bb[0] + bb[3])/2, -(bb[1] + bb[4])/2, -bb[2]))
def export(m, name): to_tm(m).export(os.path.join(OUT, name)); return m.volume()

if __name__ == "__main__":
    world = lambda m: m.translate((0, 0, Z_O))
    assembly, table, vol = [], [], {}
    for i in range(len(H)):
        body, info = panel(i)
        tag = f"P{i:02d}_el{info['el']:.0f}_az{info['az']:03.0f}" + ("_LED" if info['led'] else "") + (f"_port-{info['port']}" if info['port'] else "")
        vol[tag] = export(lay_flat(body, fnormal(H[i])), tag + ".stl"); assembly.append(('panneau', world(body))); table.append(dict(piece=tag, **info))
    kinds = {}
    for k in range(10):
        body, kind = skirt(k); assembly.append(('jupe', world(body)))
        if kind not in kinds:
            ns = unit(((P[eq_edges[k][0]] + P[eq_edges[k][1]])/2)*np.array([1, 1, 0]))
            vol[f"jupe_{kind}"] = export(lay_flat(body, ns), f"jupe_{kind}.stl"); kinds[kind] = 0
        kinds[kind] += 1
    az_ = adapter_zenith(); ap = adapter_port(); tw = tower(); pc = port_cap(); lc = led_cap(); tt = turntable()
    vol['adaptateur_zenith'] = export(place(az_, np.diag([1, -1, -1])).translate((0, 0, S_TOP)), "adaptateur_zenith.stl")
    vol['adaptateur_oblique'] = export(lay_flat(ap, -U_PORT), "adaptateur_oblique.stl")
    vol['tour_camera'] = export(tw.translate((0, 0, -S_TOP)), "tour_camera.stl")
    vol['bouchon_port'] = export(pc, "bouchon_port.stl")
    vol['capuchon_LED'] = export(lc.translate((0, 0, 0.6)), "capuchon_LED.stl")
    vol['plateau_tournant'] = export(tt, "plateau_tournant.stl")
    assembly += [('adaptateur', world(az_)), ('adaptateur', world(ap)), ('bouchon', world(pc.translate((0, 0, S_TOP)))),
                 ('tour', world(place(tw, frame(U_PORT, E1_PORT)))), ('plateau', tt.translate((0, 0, 28)))]
    for i in LED:
        f = H[i]; n = fnormal(f); u = cent[i]; st = (n @ P[f[0]] + T)/(u @ n) + GAP + STAR_T
        assembly.append(('capuchon', world(place(lc, frame(u), st*u))))
    json.dump(dict(parts=table, eq_pin_edges=len(PIN_EDGES), led_faces=LED, port_face=PORT_FACE, volumes_mm3=vol, skirt_kinds=kinds),
              open(os.path.join(OUT, "..", "pieces.json"), "w"), indent=1, ensure_ascii=False)
    sc = trimesh.Scene()
    for k, (kind, m) in enumerate(assembly): sc.add_geometry(to_tm(m), node_name=f"{kind}_{k}", geom_name=f"{kind}_{k}")
    sc.export(os.path.join(OUT, "..", "assemblage.glb"))
    counts = dict(capuchon_LED=len(LED)); qty = {**{t['piece']: 1 for t in table}, 'jupe_goupille': kinds.get('goupille', 0), 'jupe_simple': kinds.get('simple', 0),
           'jupe_DB37': kinds.get('DB37', 0), 'adaptateur_zenith': 1, 'adaptateur_oblique': 1, 'tour_camera': 1, 'bouchon_port': 1, 'capuchon_LED': len(LED), 'plateau_tournant': 1}
    tot = sum(vol[k]*qty[k] for k in vol)
    print(f"LED sur les faces {LED} ; port oblique : face {PORT_FACE} (él. {el[PORT_FACE]:.1f}°, az. {az[PORT_FACE]:.1f}°)")
    print(f"volume total {tot/1000:.0f} cm³ -> {tot*1.27e-3:.0f} g de PETG plein ({len(vol)} fichiers STL, {sum(qty.values())} pièces)")
