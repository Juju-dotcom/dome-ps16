"""Dôme PS-16, version « photo » (validée par les 3 vérificateurs du 27/09) : modèle complet + contrôle d'interpénétration.
- 40 triangles ASA à ras, languette/rainure sur les arêtes, 3 bossages d'insert M3 aux coins
- 15 étoiles de sommet + 10 demi-étoiles d'équateur (PETG-CF), vissées M3x8 dans les inserts
- 16 capsules LED vissées (2 inserts chacune), étoile Luxeon SW-01 prise dedans
- rebord d'équateur + 5 oreilles sur 5 tours de guidage ; jupe 10 pans ; planche 700 x 900
- boîtier de façade (OLED, 3 boutons, LED d'état, interrupteur ; DB37, jack, USB-B à l'arrière) avec l'électronique réelle
- plateau tournant (NEMA 17 sous la planche, MOT-H-04, moyeu, disque Ø160), tour caméra au port oblique, bouchon au zénith
Repère O (centre objet) ; monde = O + 60 mm en z (dessus de la planche à z = 0)."""
import json, numpy as np, trimesh
from manifold3d import Manifold as M, OpType
import dome_gen as D
from dome_gen import P, H, V, T as T0, unit, frame, place, cyl, box, slab, fnormal, cent, LED, PORT_FACE, U_PORT, E1_PORT, TOP, eq_edges, PIN_EDGES, w_out, is_eq

T = 3.0; ZO = D.Z_O; Z = np.array([0, 0, 1.0])
BIG = M.cube((3000, 3000, 3000), True)
def U(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    return M.batch_boolean(ms, OpType.Add) if ms else M()
def keep(m, n, d): return m.trim_by_plane(tuple(unit(n)), float(d))
BOSS_UP, BOSS_R, INS_R, INS_D = 4.5, 5.5, 2.0, 6.5       # bossage 7,5 mm total, trou d'insert Ø4,0 x 6,5
ARM_T, ARM_W = 3.0, 10.0
CORNER_IN = 17.0                                         # insert à 17 mm du sommet sur la bissectrice (≥ 8 mm du bord)
apex = int(np.argmax(V[:, 2]))
faces_of = {}
for i, f in enumerate(H):
    for v in f: faces_of.setdefault(v, []).append(i)
d0 = {i: fnormal(H[i]) @ P[H[i][0]] for i in range(len(H))}
nrm = {i: fnormal(H[i]) for i in range(len(H))}
wedge = {i: M.hull_points([(0, 0, 0)] + [tuple(2.2*P[j]) for j in H[i]]) for i in range(len(H))}

def corner_pts(i):
    """centres des bossages d'insert aux coins (sur le plan extérieur du panneau)"""
    f, n = H[i], nrm[i]; c = P[f].mean(0); out = {}
    for v in f:
        if v == apex: continue
        d = c - P[v]; d -= (d @ n)*n; d = unit(d)
        out[v] = P[v] + CORNER_IN*d + T*n
    return out
CORN = {i: corner_pts(i) for i in range(len(H))}
ZEN_R = 53.0
zen_pts = {}
for i in TOP:     # un insert par face du sommet, au milieu angulaire de la face, r = 53
    c = P[H[i]].mean(0); a = np.arctan2(c[1], c[0]); n = nrm[i]
    xy = np.array([ZEN_R*np.cos(a), ZEN_R*np.sin(a), 0.0]); z = (d0[i] + T - n[:2] @ xy[:2])/n[2]
    zen_pts[i] = np.array([xy[0], xy[1], z])
port_pts = [(D.d0 if False else None) for _ in range(0)]
PV = [unit(P[j] - (P[j] @ U_PORT)*U_PORT) for j in H[PORT_FACE]]
port_pts = [(d0[PORT_FACE] + T)*nrm[PORT_FACE] + 53.0*v for v in PV]

def boss(n, p, h=BOSS_UP): return place(M.cylinder(h + 0.5, BOSS_R, BOSS_R, 32).translate((0, 0, -0.5)), frame(n), p)
def ins_hole(n, p, h=BOSS_UP): return place(M.cylinder(INS_D + 0.2, INS_R, INS_R, 24).translate((0, 0, h - INS_D)), frame(n), p)

def led_frame(i):
    u = cent[i]; n = nrm[i]; s0 = d0[i]/(u @ n); so = (d0[i] + T)/(u @ n); return u, n, s0, so, frame(u)
POD_EAR = 21.0
def pod_ears(i):
    u, n, s0, so, Fr = led_frame(i)
    out = []
    for s in (1, -1):
        p = so*u + s*POD_EAR*Fr[:, 1]; p = p - ((p @ n) - (d0[i] + T))*n
        out.append(p)
    return out

def _eaz(e): m = (P[e[0]] + P[e[1]])/2; return np.degrees(np.arctan2(m[1], m[0])) % 360
HANDLE_EDGES = [min((e for e in eq_edges if e not in PIN_EDGES), key=lambda e: abs(((_eaz(e) - a) + 180) % 360 - 180)) for a in (198, 342)]
def handle_pts(e):
    a, b = e; c = (P[a] + P[b])/2 + w_out(a, b)*(T + 14.0); c[2] = 3.0; t = unit(np.cross(Z, w_out(a, b)))
    return [c + 24*t, c - 24*t]
def handle(e):
    a, b = e; w = w_out(a, b); t = unit(np.cross(Z, w)); c0 = (P[a] + P[b])/2 + w*(T + 14.0); c0[2] = 10.0
    R_ = np.column_stack([t, w, Z])
    blk = lambda x0, x1, y0, y1: place(M.cube((x1 - x0, y1 - y0, 12)).translate((x0, y0, 0)), R_, c0)
    hnd = U([blk(-30, -18, -6, 52), blk(18, 30, -6, 52), blk(-30, 30, 40, 52)])
    hnd = hnd - U([place(M.cylinder(30, 1.7, 1.7, 20).translate((0, 0, -5)), np.eye(3), p) for p in handle_pts(e)])
    return hnd, [(Z, p + np.array([0, 0, 19.0])) for p in handle_pts(e)]

# ---------------- panneaux ----------------
def panel(i):
    f, n, dd = H[i], nrm[i], d0[i]
    w = wedge[i]; body = slab(w, n, dd, dd + T)
    for a, b in zip(f, f[1:] + f[:1]):
        c3 = [j for j in f if j not in (a, b)][0]; m = unit(np.cross(P[a], P[b])); m = m if m @ P[c3] > 0 else -m
        body = keep(body, m, 0.1)
    adds, cuts = [], []
    # languette / rainure sur les arêtes intérieures
    for a, b in zip(f, f[1:] + f[:1]):
        if is_eq(a) and is_eq(b): continue
        j = [k for k in range(len(H)) if k != i and a in H[k] and b in H[k]]
        if not j: continue
        j = j[0]; owner = min(i, j); o = owner
        m = unit(np.cross(P[a], P[b])); c3 = [x for x in H[o] if x not in (a, b)][0]; m = m if m @ P[c3] > 0 else -m
        e = unit(P[b] - P[a]); lo, hi = e @ P[a] + 16, e @ P[b] - 16
        if lo > hi: lo, hi = hi, lo
        def strip(m0, m1, s0_, s1_, pad):
            r = keep(keep(BIG, m, m0), -m, -m1)
            r = slab(r, nrm[o], d0[o] + s0_, d0[o] + s1_)
            return keep(keep(r, e, lo - pad), -e, -(hi + pad))
        if o == i: adds.append(strip(-1.0, 0.1, 0.0, 1.5, 0.0))          # lèvre : moitié intérieure, passe 1 mm sous le voisin
        else: cuts.append(strip(-1.2, 0.3, -0.4, 1.7, 0.2))            # feuillure du voisin (jeu 0,2 mm), ouverte vers l'intérieur : pose radiale
    # bossages d'insert aux coins
    for v, p in CORN[i].items():
        adds.append(boss(n, p)); cuts.append(ins_hole(n, p))
    # rebord d'équateur (appui sur la jupe) + oreille de tour
    for a, b in zip(f, f[1:] + f[:1]):
        if is_eq(a) and is_eq(b):
            ek = D.edge_key(a, b); c3 = [x for x in f if x not in (a, b)][0]
            fl = slab(keep(keep(w, Z, 0.0), -Z, -3.0), n, dd, dd + T + 24)
            adds.append(fl)
            if ek in PIN_EDGES:
                c = (P[a] + P[b])/2 + w_out(a, b)*(T + 42.0); c[2] = 0
                lug = M.hull_points([tuple(c + dz + dr) for dz in ([0, 0, 0], [0, 0, 3]) for dr in
                                     [unit(np.cross(Z, w_out(a, b)))*s*17 + w_out(a, b)*t for s in (1, -1) for t in (-44, 14)]])
                lug = lug - place(M.cylinder(10, 10.6, 10.6, 48).translate((0, 0, -2)), np.eye(3), c)
                adds.append(lug)
    for a, b in zip(f, f[1:] + f[:1]):
        if is_eq(a) and is_eq(b) and D.edge_key(a, b) in HANDLE_EDGES:
            for p in handle_pts(D.edge_key(a, b)):
                adds.append(place(M.cylinder(7.0, BOSS_R, BOSS_R, 32), np.eye(3), p)); cuts.append(place(M.cylinder(INS_D + 0.2, INS_R, INS_R, 24).translate((0, 0, 7.0 - INS_D)), np.eye(3), p))
    if i in TOP:
        cuts.append(cyl(Z, 0, 420, 40.0)); adds.append(boss(n, zen_pts[i])); cuts.append(ins_hole(n, zen_pts[i]))
    if i == PORT_FACE:
        cuts.append(cyl(U_PORT, 0, 420, 40.0))
        for p in port_pts: adds.append(boss(n, p)); cuts.append(ins_hole(n, p))
    if i in LED:
        u, n_, s0, so, Fr = led_frame(i)
        cuts.append(cyl(u, s0 - 1, so + 0.2, 6.5, 4.0))
        for p in pod_ears(i): adds.append(boss(n, p)); cuts.append(ins_hole(n, p))
    body = U([body] + adds)
    if cuts: body = body - U(cuts)
    return body

# ---------------- étoiles de sommet ----------------
def arm(i, v_pt, p):
    """barre plate posée sur le dessus des bossages de la face i, du moyeu au bossage p"""
    n = nrm[i]; base = d0[i] + T + BOSS_UP
    def at(q): return q + (base - q @ n)*n
    a0, a1 = at(v_pt), at(p)
    pts = []
    for q in (a0, a1):
        for k in range(16):
            ang = 2*np.pi*k/16; Fr = frame(n)
            r = q + ARM_W/2*(np.cos(ang)*Fr[:, 0] + np.sin(ang)*Fr[:, 1])
            pts += [tuple(r), tuple(r + ARM_T*n)]
    return M.hull_points(pts)
def star(v):
    vh = unit(P[v]); arms, holes, screws = [], [], []
    eq = is_eq(v)
    hub_c = P[v] + vh*(T + BOSS_UP + 1.5) + (np.array([0, 0, 12.0]) if eq else 0)
    for i in faces_of[v]:
        if v not in CORN[i]: continue
        p = CORN[i][v]; q = p + BOSS_UP*nrm[i]
        arms.append(arm(i, hub_c, q))
        holes.append(place(M.cylinder(20, 1.7, 1.7, 20).translate((0, 0, -5)), frame(nrm[i]), q))
        screws.append((nrm[i], q + ARM_T*nrm[i]))
    hub = place(M.cylinder(ARM_T + 1.0, 8 if not eq else 6, 8 if not eq else 6, 32).translate((0, 0, -0.5)), frame(vh), hub_c)
    s = U(arms + [hub]) - U(holes)
    # rien sous les bossages voisins
    return s, screws

# ---------------- capsule LED (pièce séparée) + étoile LED réelle ----------------
def pod(i):
    u, n, s0, so, Fr = led_frame(i)
    sf = so + D.GAP; st = sf + D.STAR_T; top = st + 3.0
    ring = cyl(u, so - 1, top, 16) - cyl(u, so - 2, st, 10.9)
    ring = ring - cyl(u, st - 0.1, top + 1, 6.0)
    # 10 oct. : plus de colonnes sous l'étoile (elle ne pouvait pas entrer). 4 tétons Ø2,7 qui descendent de la paroi du dessus
    # jusqu'à 1 mm sous l'étoile : l'étoile entre par le côté panneau, tétons dans ses encoches, et se colle à l'époxy au bout des tétons.
    ring = ring + U([cyl(u, sf - 1.0, st + 0.1, 1.35, off=o, seg=20) for o in D.NOTCH])
    ring = ring - U([box(u, 9.5, 17, -1.7, 1.7, so - 2, st), box(u, -17, -9.5, -1.7, 1.7, so - 2, st)])
    ears, holes, screws = [], [], []
    for p in pod_ears(i):
        q = p + BOSS_UP*n
        ears.append(M.hull_points([tuple(x) for x in [q + r*frame(n)[:, 0]*np.cos(a) + r*frame(n)[:, 1]*np.sin(a) + h*n
                                                         for a in np.linspace(0, 2*np.pi, 16, endpoint=False) for r in (5.5,) for h in (0, 2.5)]] +
                                  [tuple(so*u + (p - so*u)*0.45 + h*u + 5*frame(u)[:, 0]*s) for h in (BOSS_UP, top - so) for s in (1, -1)]))
        holes.append(place(M.cylinder(20, 1.7, 1.7, 20).translate((0, 0, -5)), frame(n), q))
        holes.append(place(M.cylinder(6, 3.3, 3.3, 24), frame(n), q + 2.5*n))      # dégagement de tête
        screws.append((n, q + 2.5*n))
    b = U([ring] + ears) - U(holes)
    b = b - keep(BIG, -n, -(d0[i] + T + 0.02))          # rien sous la face extérieure du panneau
    b = b - U([boss(n, p) for p in pod_ears(i)])        # ni dans les bossages
    # étoile LED Luxeon (hexagone 19,9 plats) + lentille
    Fr = frame(u)
    hexa = place(M.cylinder(D.STAR_T, 10.45/np.cos(np.radians(30))*np.cos(np.radians(30)), 10.45, 6).rotate((0, 0, 30)).translate((0, 0, sf)), Fr)
    hexa = hexa - U([cyl(u, sf - 1, sf + 3, 1.6, off=o, seg=16) for o in D.NOTCH])
    lens = place(M.sphere(1.5, 24).translate((0, 0, sf - 1.2)) + M.cylinder(1.2, 2.25, 2.25, 4).translate((0, 0, sf - 1.2)), Fr)
    return b, hexa, lens, screws

# ---------------- adaptateurs, tour, bouchon (repris, fixations sur inserts) ----------------
def adapters(panels_union):
    az_ = cyl(Z, 240, D.S_TOP, 47.5) + U([place(M.cylinder(D.S_TOP - 4 - 240, 7, 7, 32).translate((0, 0, 240)), np.eye(3), p*np.array([1, 1, 0])) for p in zen_pts.values()])
    under = U([slab(wedge[i], nrm[i], 0.0, d0[i] + T + 0.05) for i in TOP])
    az_ = az_ - under - panels_union - cyl(Z, 0, 420, 40.0) - U([place(M.cylinder(420, 1.7, 1.7, 20), np.eye(3), p*np.array([1, 1, 0])) for p in zen_pts.values()])
    az_ = az_ - U([place(M.cylinder(420, 3.1, 3.1, 24).translate((0, 0, D.S_TOP - 9)), np.eye(3), p*np.array([1, 1, 0])) for p in zen_pts.values()])
    az_ = az_ - U(D.tower_holes(Z, np.array([1.0, 0, 0]), D.S_TOP - 14, D.S_TOP + 1, 1.3))
    # jeu de 0,4 mm autour des bossages d'insert (appui seulement sur le dessus du bossage, là où la vis serre) : 10 oct.
    az_ = az_ - U([place(M.cylinder(BOSS_UP + 0.5, BOSS_R + 0.4, BOSS_R + 0.4, 32).translate((0, 0, -0.5)), frame(nrm[i]), p) for i, p in zen_pts.items()])
    so = d0[PORT_FACE] + T
    ap = cyl(U_PORT, so, D.S_TOP, 47.5, e1=E1_PORT) + U([place(M.cylinder(D.S_TOP - 4 - so, 7, 7, 32).translate((0, 0, so)), frame(U_PORT), 53*v) for v in PV])
    ap = ap - panels_union - cyl(U_PORT, 0, 420, 40.0)
    for v in PV: ap = ap - place(M.cylinder(420, 1.7, 1.7, 20), frame(U_PORT), 53*v) - place(M.cylinder(420, 3.1, 3.1, 24).translate((0, 0, D.S_TOP - 9)), frame(U_PORT), 53*v)
    ap = ap - U(D.tower_holes(U_PORT, E1_PORT, D.S_TOP - 14, D.S_TOP + 1, 1.3))
    ap = ap - U([place(M.cylinder(BOSS_UP + 0.5, BOSS_R + 0.4, BOSS_R + 0.4, 32).translate((0, 0, -0.5)), frame(nrm[PORT_FACE]), p) for p in port_pts])
    return az_, ap

# ---------------- jupe (sans trou : étanche) + tours de guidage ----------------
def skirt(k):
    a, b = eq_edges[k]; p, q = P[a], P[b]
    ns = unit(((p + q)/2)*np.array([1, 1, 0])); ds = ns @ p; lo, hi = -ZO, 0.0
    wd = M.hull_points([(0, 0, lo - 5), (0, 0, hi + 5)] + [tuple(2.2*np.array([v[0], v[1], z])) for v in (p, q) for z in (lo - 5, hi + 5)])
    zs = lambda m, z0, z1: m.trim_by_plane((0, 0, 1), z0).trim_by_plane((0, 0, -1), -z1)
    parts = [zs(slab(wd, ns, ds, ds + T), lo, hi - 3.2), zs(slab(wd, ns, ds, ds + T + 27), hi - 6.2, hi - 3.2), zs(slab(wd, ns, ds, ds + T + 20), lo, lo + 3)]
    for v in (p, q):
        o = q if v is p else p; m = unit(np.cross(Z, v)); m = m if m @ o > 0 else -m
        parts.append(zs(slab(keep(keep(wd, m, 0.1), -m, -3.0), ns, ds, ds + T + 12), lo, hi - 3.2))
    body = U(parts); w = w_out(a, b)
    for lam in (0.25, 0.75):
        c = p + lam*(q - p) + w*(T + 11); c[2] = lo
        body = body - place(M.cylinder(20, 2.75, 2.75, 24, True), np.eye(3), c)                  # Ø5,5 : ± 0,6 mm de réglage (10 oct.)
        body = body - place(M.cylinder(10, 6.0, 6.0, 32), np.eye(3), (c[0], c[1], hi - 8.0))      # accès tournevis Ø12 dans la tablette (10 oct.)
        WOOD.append(np.array([c[0], c[1], lo + 3.0]))
    return body
def tower_post(e):
    a, b = e; c = (P[a] + P[b])/2 + w_out(a, b)*(T + 42.0); c[2] = -ZO
    post = M.cylinder(ZO + 36, 10, 10, 48).translate((0, 0, 0)) + M.cylinder(8, 10, 5, 48).translate((0, 0, ZO + 36))
    fins = U([M.cube((34, 3, ZO - 8)).translate((-17, -1.5, 0)).rotate((0, 0, ang)) for ang in (0, 90)])
    base = M.cylinder(4, 20, 20, 48)
    t = place(post + fins + base, np.eye(3), c)
    for ang in (45, 135, 225, 315):
        h = c + 15*np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang)), 0])
        t = t - place(M.cylinder(12, 2.75, 2.75, 20).translate((0, 0, -1)), np.eye(3), h); WOOD.append(h + np.array([0, 0, 4.0]))   # Ø5,5 (10 oct.)
    return t

# ---------------- planche, pieds, plateau tournant ----------------
BOARD = dict(x=700.0, y0=-560.0, y1=360.0, t=15.9)   # mélamine noire Uniboard 5/8 po
WOOD = []   # têtes des vis à bois n° 8 x 5/8 po (pointe dans la planche)
def board():
    b = M.cube((BOARD['x'], BOARD['y1'] - BOARD['y0'], BOARD['t'])).translate((-BOARD['x']/2, BOARD['y0'], -ZO - BOARD['t']))
    b = b - M.cube((46, 46, 40), True).translate((0, 0, -ZO - BOARD['t']/2))
    return b
FOOT_H = 35.0          # le moteur dépasse de 40 - 15,9 = 24 mm sous la planche -> pieds de 35 mm (11 mm de garde)
FEET_UP = []           # vis à bois vissées par-dessous (tête dans un lamage du pied)
def feet():
    pts = [(-310, -520), (310, -520), (-310, 320), (310, 320), (-310, -100), (310, -100)]; out = []   # 6 pieds : portée 420 mm
    z1 = -ZO - BOARD['t']; z0 = z1 - FOOT_H
    for x, y in pts:
        f = M.cylinder(FOOT_H, 20, 20, 48).translate((x, y, z0))
        for dx in (-10, 10):
            f = f - M.cylinder(8, 2.25, 2.25, 20).translate((x + dx, y, z1 - 7)) - M.cylinder(FOOT_H - 6 + 1, 4.6, 4.6, 24).translate((x + dx, y, z0 - 1))
            FEET_UP.append(np.array([x + dx, y, z1 - 6.0]))
        out.append(f)
    return out
DRIVE_SCREWS = []      # (normale, tête, longueur) des vis M3 du moteur et du plateau
HUB_BC = 6.35          # moyeu Pololu 1998 (dessin officiel) : Ø19 x 5, alésage Ø5, 4 x M3 à 6,35 mm de l'axe
def drive():
    zb = -ZO   # dessus de la planche
    DRIVE_SCREWS.clear()
    motor = M.cube((42.3, 42.3, 40), True).translate((0, 0, zb - 20)) + M.cylinder(24, 2.5, 2.5, 24).translate((0, 0, zb))
    motor = motor + M.cylinder(2, 11, 11, 32).translate((0, 0, zb))                      # centrage Ø22 x 2 (norme NEMA 17)
    # platine imprimée (PETG-CF) : remplace le MOT-H-04 ; 4 vis M3x8 dans le moteur (entraxe NEMA 17 : 31 mm)
    plate = M.cube((72, 72, 4)).translate((-36, -36, zb)) - M.cylinder(10, 12, 12, 40).translate((0, 0, zb - 1))   # 72 x 72 (10 oct.) : vis à bois loin du trou 46 x 46
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = 15.5*sx, 15.5*sy
            plate = plate - M.cylinder(10, 1.7, 1.7, 16).translate((x, y, zb - 1))
            motor = motor - M.cylinder(5, 1.5, 1.5, 16).translate((x, y, zb - 5))       # taraudage M3 du moteur (4,5 mm)
            DRIVE_SCREWS.append((Z, np.array([x, y, zb + 4.0]), 8.0))
            x, y = 30*sx, 30*sy
            plate = plate - M.cylinder(10, 2.25, 2.25, 20).translate((x, y, zb - 1)); WOOD.append(np.array([x, y, zb + 4.0]))
    # moyeu Pololu 1998 sur l'arbre (vis de pression) : dessus du moyeu à zb + 24
    hub = M.cylinder(5, 9.5, 9.5, 40).translate((0, 0, zb + 19)) - M.cylinder(7, 2.55, 2.55, 24).translate((0, 0, zb + 18))
    hb = [(HUB_BC*np.cos(a), HUB_BC*np.sin(a)) for a in np.radians([45, 135, 225, 315])]
    for x, y in hb: hub = hub - M.cylinder(7, 1.5, 1.5, 16).translate((x, y, zb + 18))
    # plateau Ø160 x 12 posé sur le moyeu : 4 vis M3x10 dans le moyeu (têtes noyées), dégagement Ø6 x 4 pour un arbre plus long
    disk = M.cylinder(12, 80, 80, 128).translate((0, 0, zb + 24)) - M.cylinder(4, 3.0, 3.0, 24).translate((0, 0, zb + 23.9)) \
        - M.cylinder(14, 1.1, 1.1, 16).translate((68.5, 0, zb + 23)) - M.cylinder(3, 2.2, 2.2, 24).translate((68.5, 0, zb + 33.6))   # lamage de la tête M2 (10 oct.)
    for x, y in hb:
        disk = disk - M.cylinder(14, 1.7, 1.7, 16).translate((x, y, zb + 23)) - M.cylinder(9, 3.3, 3.3, 24).translate((x, y, zb + 28))
        DRIVE_SCREWS.append((Z, np.array([x, y, zb + 28.0]), 10.0))
    sensor = M.cube((33, 10, 11)).translate((52, -5, zb + 6)) - M.cube((5, 12, 8)).translate((66, -6, zb + 9.5))
    flag = M.cylinder(20, 1.0, 1.0, 12).translate((68.5, 0, zb + 13.6)) + M.cylinder(2.0, 1.9, 1.9, 16).translate((68.5, 0, zb + 33.6)) \
        + M.cylinder(1.6, 2.0, 2.0, 6).translate((68.5, 0, zb + 22.3))   # vis M2x20 tête en haut + écrou M2 sous le plateau (10 oct.)
    return dict(moteur=motor, platine_moteur=plate, moyeu=hub, plateau_tournant=disk, capteur_zero=sensor, drapeau=flag)

# ---------------- boîtier de façade + électronique ----------------
BX = dict(w=250.0, d=150.0, h=86.0, y_back=-372.0)
def enclosure():
    x0, x1 = -BX['w']/2, BX['w']/2; y1 = BX['y_back']; y0 = y1 - BX['d']; zb = -ZO; zt = zb + BX['h']
    outer = M.cube((BX['w'], BX['d'], BX['h'])).translate((x0, y0, zb))
    inner = M.cube((BX['w'] - 6, BX['d'] - 6, BX['h'] - 3)).translate((x0 + 3, y0 + 3, zb + 3))
    shell = outer - inner
    front = y0
    cuts = [M.cube((34, 8, 18)).translate((-95, front - 1, zb + 50)),                        # fenêtre OLED
            *[M.cylinder(8, 6.1, 6.1, 32).rotate((90, 0, 0)).translate((x, front + 6, zb + 30)) for x in (-60, -35, -10)],   # 3 boutons 12 mm
            M.cylinder(8, 8.1, 8.1, 32).rotate((90, 0, 0)).translate((80, front + 6, zb + 45)),                                # interrupteur 16 mm
            M.cylinder(8, 2.6, 2.6, 24).rotate((90, 0, 0)).translate((40, front + 6, zb + 62)),                                # LED d'état
            M.cube((56, 8, 12)).translate((-28, y1 - 4, zb + 40)),                                                            # DB37 (arrière)
            *[M.cylinder(8, 1.6, 1.6, 16).rotate((90, 0, 0)).translate((s*31.75, y1 + 2, zb + 46)) for s in (1, -1)],
            M.cylinder(8, 5.6, 5.6, 32).rotate((90, 0, 0)).translate((75, y1 + 2, zb + 40)),                                  # jack DC
            M.cylinder(8, 15.1, 15.1, 48).rotate((90, 0, 0)).translate((-80, y1 + 2, zb + 42))]                              # USB-B rond 4216-ADA : trou Ø30 (fiche Adafruit)
    for x, y in ((-115, y0 + 12), (115, y0 + 12), (-115, y1 - 12), (115, y1 - 12)):
        cuts.append(M.cylinder(10, 2.25, 2.25, 20).translate((x, y, zb - 1))); WOOD.append(np.array([x, y, zb + 3.0]))
    shell = shell - U(cuts)
    lid = M.cube((BX['w'], BX['d'], 3)).translate((x0, y0, zt)) - M.cube((BX['w'] - 40, 60, 5)).translate((x0 + 20, y0 + 45, zt - 1)) if False else M.cube((BX['w'], BX['d'], 3)).translate((x0, y0, zt))
    parts = {'boitier': shell, 'couvercle_boitier': lid}
    # électronique réelle (dimensions des fiches)
    mega = M.cube((101.5, 53.3, 1.6)).translate((-110, y0 + 60, zb + 10))
    mega_hdr = M.cube((80, 2.5, 8.5)).translate((-100, y0 + 60 + 50, zb + 11.6)) + M.cube((80, 2.5, 8.5)).translate((-100, y0 + 61, zb + 11.6))
    usb_b = M.cube((16, 12, 11)).translate((-116, y0 + 95, zb + 11.6))
    parts['arduino_mega'] = mega + mega_hdr + usb_b
    parts['carte_LED'] = M.cube((110, 47, 1.6)).translate((0, y0 + 90, zb + 10))
    parts['ULN2803'] = M.cube((23, 7, 4)).translate((15, y0 + 105, zb + 11.6)) + M.cube((23, 7, 4)).translate((45, y0 + 105, zb + 11.6))
    parts['LM317_dissipateur'] = M.cube((35, 12.7, 38)).translate((70, y0 + 100, zb + 11.6))
    parts['carte_moteur'] = M.cube((70, 40, 1.6)).translate((0, y0 + 20, zb + 10))
    parts['TMC2209'] = M.cube((15.2, 20.3, 12)).translate((20, y0 + 30, zb + 11.6))
    MEGA_HOLES = [(13.97, 2.54), (15.24, 50.8), (66.04, 7.62), (66.04, 35.56), (90.17, 50.8), (96.52, 2.54)]   # trous officiels Arduino Mega 2560 (mm, coin USB)
    parts['entretoises'] = U([M.cylinder(7, 2.8, 2.8, 16).translate((x, y, zb + 3)) for x, y in
                               [(-110 + hx, y0 + 60 + hy) for hx, hy in MEGA_HOLES] + [(4, y0 + 94), (106, y0 + 94), (4, y0 + 133), (106, y0 + 133), (4, y0 + 24), (66, y0 + 24), (4, y0 + 56), (66, y0 + 56)]])
    # OLED WAVE-18179 (module 30 x 39,5, zone active 14,7 x 29,4 en portrait) monté tourné de 90° : zone active 29,4 x 14,7 dans la fenêtre 34 x 18
    parts['oled'] = M.cube((39.5, 4, 30)).translate((-97.75, front + 3.2, zb + 44)) + M.cube((34, 1.6, 18)).translate((-95, front + 1.6, zb + 50))
    parts['regulateur_5V'] = M.cube((50, 25, 12)).translate((72, y0 + 32, zb + 3))   # UBEC 1385-ADA (enveloppe gaine comprise), ruban double face
    parts['boutons'] = U([M.cylinder(24, 5.9, 5.9, 32).rotate((90, 0, 0)).translate((x, front + 20, zb + 30)) + M.cylinder(3, 8, 8, 32).rotate((90, 0, 0)).translate((x, front, zb + 30)) for x in (-60, -35, -10)])
    parts['interrupteur'] = M.cylinder(30, 7.9, 7.9, 32).rotate((90, 0, 0)).translate((80, front + 28, zb + 45)) + M.cylinder(2.5, 9.5, 9.5, 32).rotate((90, 0, 0)).translate((80, front, zb + 45))
    parts['led_etat'] = M.cylinder(12, 2.5, 2.5, 24).rotate((90, 0, 0)).translate((40, front + 10, zb + 62)) + M.cube((10, 3, 10)).translate((35, front + 10, zb + 57))
    parts['db37_femelle'] = M.cube((69, 1, 12.5)).translate((-34.5, y1, zb + 40)) + M.cube((54, 8, 10)).translate((-27, y1 - 7, zb + 41))
    parts['jack_dc'] = M.cylinder(14, 5.4, 5.4, 32).rotate((90, 0, 0)).translate((75, y1 + 3, zb + 40)) + M.cylinder(2, 7.5, 7.5, 6).rotate((90, 0, 0)).translate((75, y1 + 2, zb + 40))
    parts['usb_b_panneau'] = M.cylinder(22, 14.9, 14.9, 48).rotate((90, 0, 0)).translate((-80, y1 + 3, zb + 42)) + M.cylinder(2, 17.5, 17.5, 48).rotate((90, 0, 0)).translate((-80, y1 + 2, zb + 42))
    return parts

# ---------------- vis ----------------
def screw(n, head_pt, L=8.0):
    """vis M3 à tête cylindrique : tête Ø5,5 x 3 au-dessus, tige Ø3 x L dessous"""
    return place(M.cylinder(3.0, 2.75, 2.75, 20).translate((0, 0, 0)) + M.cylinder(L, 1.5, 1.5, 16).translate((0, 0, -L)), frame(n), head_pt)

def build():
    parts = {}
    for i in range(len(H)): parts[f'panneau_{i:02d}'] = panel(i)
    pu = U(list(parts.values()))
    screws = []
    for v in range(len(V)):
        if V[v, 2] < -1e-9 or v == apex or v not in faces_of: continue
        s, sc = star(v); parts[('etoile_' if not is_eq(v) else 'demi_etoile_') + f'{v:02d}'] = s; screws += sc
    for i in LED:
        b, hexa, lens, sc = pod(i); parts[f'capsule_{i:02d}'] = b; parts[f'etoile_LED_{i:02d}'] = hexa; parts[f'lentille_{i:02d}'] = lens; screws += sc
    az_, ap = adapters(pu); parts['adaptateur_zenith'] = az_; parts['adaptateur_oblique'] = ap
    for p in zen_pts.values(): screws.append((Z, np.array([p[0], p[1], D.S_TOP - 9])))
    for v in PV: screws.append((U_PORT, U_PORT*(D.S_TOP - 9) + 53*v))
    parts['tour_camera'] = place(D.tower(), frame(U_PORT, E1_PORT))
    parts['bouchon_zenith'] = D.port_cap().translate((0, 0, D.S_TOP))
    for k in range(10): parts[f'jupe_{k}'] = skirt(k)
    for k, e in enumerate(sorted(PIN_EDGES)): parts[f'tour_guidage_{k}'] = tower_post(e)
    for k, e in enumerate(HANDLE_EDGES):
        h, sc = handle(e); parts[f'poignee_{k}'] = h; screws += sc
    parts['planche'] = board()
    for k, f in enumerate(feet()): parts[f'pied_{k}'] = f
    parts.update(drive()); parts.update(enclosure())
    screws += [(n, p) for n, p, _ in DRIVE_SCREWS]
    parts['vis'] = U([screw(n, p, 16.0 if abs(p[2] - 22.0) < 1e-6 else 8.0) for n, p in screws[:-len(DRIVE_SCREWS)]] + [screw(n, p, L) for n, p, L in DRIVE_SCREWS])
    # vis à bois (tête Ø8 x 3, tige Ø4 x 16 dans un avant-trou de la planche)
    heads = [M.cylinder(3, 4, 4, 20).translate(tuple(h)) + M.cylinder(16, 2.0, 2.0, 16).translate((h[0], h[1], h[2] - 16)) for h in WOOD]
    heads += [M.cylinder(3, 4, 4, 20).translate((h[0], h[1], h[2] - 3)) + M.cylinder(16, 2.0, 2.0, 16).translate(tuple(h)) for h in FEET_UP]
    parts['vis_bois'] = U(heads)
    parts['planche'] = parts['planche'] - U([M.cylinder(12, 2.05, 2.05, 16).translate((h[0], h[1], -ZO - BOARD['t'] - 0.1)) for h in FEET_UP])
    parts['planche'] = parts['planche'] - U([M.cylinder(20, 2.05, 2.05, 16).translate((h[0], h[1], h[2] - 20)) for h in WOOD])
    return parts, screws

if __name__ == "__main__":
    import time; t0 = time.time()
    parts, screws = build()
    print(f"{len(parts)} objets, {len(screws)} vis, {time.time() - t0:.1f} s")
    # ---- contrôle d'interpénétration : toutes les paires dont les boîtes se touchent ----
    names = list(parts); bb = {k: np.array(parts[k].bounding_box()) for k in names}
    ok_pairs = {('vis', x) for x in names}      # vis dans leurs trous : testées à part
    bad, tested = [], 0
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            A, B = names[a], names[b]
            if 'vis' in (A, B) or 'vis_bois' in (A, B): continue
            ba, bb_ = bb[A], bb[B]
            if np.any(ba[3:] < bb_[:3] - 0.01) or np.any(bb_[3:] < ba[:3] - 0.01): continue
            tested += 1
            v = (parts[A] ^ parts[B]).volume()
            if v > 0.5: bad.append((A, B, round(v, 1)))
    # vis : la tige doit être dans le vide (trou d'insert), la tête sur sa pièce -> on mesure le recouvrement vis/tout le reste
    rest = U([parts[k] for k in names if k not in ('vis', 'vis_bois')])
    vs = (parts['vis'] ^ rest).volume(); vb = (parts['vis_bois'] ^ rest).volume()
    # rien ne doit dépasser vers l'intérieur du dôme (sauf l'air des ouvertures)
    inner = U([keep(wedge[i], -nrm[i], -(d0[i] - 0.05)) for i in range(len(H))]) - keep(BIG, -Z, -0.0) if False else U([keep(wedge[i], -nrm[i], -(d0[i] - 0.05)) for i in range(len(H))])
    inner = keep(inner, Z, 0.0)
    intr = [(k, round((parts[k] ^ inner).volume(), 1)) for k in names if k not in ('plateau_tournant', 'moyeu', 'drapeau', 'moteur') and (parts[k] ^ inner).volume() > 0.5]
    # champ de la caméra (pyramide réelle 126 x 106 mm -> objectif Ø29,5 à 408 mm) aux 2 ports, tour en place
    def fov(u, e1):
        F_ = frame(u, e1); pts = [F_ @ np.array([sx*63.0, sy*53.0, 0.0]) for sx in (-1, 1) for sy in (-1, 1)]
        pts += [F_ @ np.array([14.75*np.cos(a), 14.75*np.sin(a), D.CAM_FRONT]) for a in np.linspace(0, 2*np.pi, 24, endpoint=False)]
        return M.hull_points([tuple(p) for p in pts])
    solid = U([parts[k] for k in names if k not in ('tour_camera', 'bouchon_zenith', 'plateau_tournant', 'moyeu', 'drapeau', 'moteur', 'capteur_zero')])
    tw_z = D.tower()
    fov_res = {}
    for nm_, u, e1, twr in (("oblique", U_PORT, E1_PORT, parts['tour_camera']), ("zenith", Z, np.array([1.0, 0, 0]), tw_z)):
        worst = max((fov(u, D.frame(u, e1) @ np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0])) ^ (solid + twr)).volume() for a in range(0, 180, 15))
        fov_res[nm_] = round(worst, 2)
    # visée des LED vers 8 points du volume objet
    blocked = 0
    for i in LED:
        e = ((d0[i] + T)/(cent[i] @ nrm[i]) + D.GAP - 0.6)*cent[i]
        for tgt in ([0, 0, -24], [60, 0, 0], [-60, 0, 0], [0, 60, 0], [0, -60, 0], [0, 0, 50], [45, 45, 30], [-45, -45, -20]):
            d = np.array(tgt, float) - e; L = np.linalg.norm(d)
            ray = place(M.cylinder(L - 12, 0.6, 0.6, 8), frame(d), e + 6*d/L)
            if (ray ^ (solid - U([parts[f'lentille_{i:02d}'], parts[f'etoile_LED_{i:02d}']]))).volume() > 0.01: blocked += 1
    # soulever le dôme de 120 mm : doit sortir des tours sans rien accrocher
    dome_keys = [k for k in names if k.startswith(('panneau', 'etoile', 'demi_etoile', 'capsule', 'etoile_LED', 'lentille', 'adaptateur', 'tour_camera', 'bouchon', 'poignee'))]
    fixed_keys = [k for k in names if k not in dome_keys and k not in ('vis', 'vis_bois')]
    lifted = U([parts[k] for k in dome_keys]).translate((0, 0, 120))
    lift_clash = (lifted ^ U([parts[k] for k in fixed_keys])).volume()
    print(f"champ caméra (recouvrement max, mm³) : {fov_res} ; rayons de LED bloqués : {blocked}/128 ; dôme soulevé de 120 mm : accrochage {lift_clash:.1f} mm³")
    low = min(parts[k].bounding_box()[2] for k in names if not k.startswith('pied'))
    floor_ = min(parts[k].bounding_box()[2] for k in names if k.startswith('pied'))
    print(f"table : dessous des pieds à z = {floor_ + ZO:.1f} mm ; point le plus bas hors pieds à z = {low + ZO:.1f} mm -> garde {low - floor_:.1f} mm")
    print(f"paires testées : {tested} ; interpénétrations : {len(bad)}")
    for x in bad[:20]: print("  XX", x)
    print(f"vis M3 en recouvrement : {vs:.1f} mm³ ; vis à bois en recouvrement : {vb:.1f} mm³ ({len(WOOD)} vis à bois)")
    print("pièces qui dépassent à l'intérieur du dôme :", intr if intr else "aucune")
    # ---- export ----
    sc = trimesh.Scene()
    for k, m in parts.items():
        t = D.to_tm(m.translate((0, 0, ZO))); sc.add_geometry(t, node_name=k, geom_name=k)
    sc.export("photo_assemblage.glb")
    vol = {k: round(parts[k].volume()/1000, 1) for k in names}
    json.dump(dict(table_clearance=round(low - floor_, 1), n_wood=len(WOOD) + len(FEET_UP), wood_overlap=vb, fov=fov_res, led_blocked=blocked, lift_clash=lift_clash, bad=bad, tested=tested, screw_overlap=vs, intrusions=intr, n_screws=len(screws), volumes_cm3=vol,
                   leds=[(((d0[i] + T)/(cent[i] @ nrm[i]) + D.GAP - 0.6)*cent[i] + [0, 0, ZO]).round(1).tolist() for i in LED],
                   port=U_PORT.round(5).tolist(), e1=E1_PORT.round(5).tolist()), open("photo_data.json", "w"), ensure_ascii=False)
    print(f"export OK ({time.time() - t0:.1f} s)")
