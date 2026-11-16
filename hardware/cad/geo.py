"""Géodésique 2V (icosaèdre, sommet en haut) : faces de l'hémisphère."""
import numpy as np
def icosa():
    p = (1 + 5**0.5)/2
    V = np.array([[-1,p,0],[1,p,0],[-1,-p,0],[1,-p,0],[0,-1,p],[0,1,p],[0,-1,-p],[0,1,-p],[p,0,-1],[p,0,1],[-p,0,-1],[-p,0,1]], float)
    F = [[0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],[1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
         [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],[4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]]
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    # tourner pour mettre le sommet 0 au zénith
    a = V[0]; z = np.array([0, 0, 1.0]); v = np.cross(a, z); c = a @ z; s = np.linalg.norm(v)
    K = np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    Rm = np.eye(3) + K + K@K*((1-c)/s**2)
    return V @ Rm.T, F
def geodesic2v(full=False):
    V, F = icosa(); V = list(V); cache = {}
    def mid(i, j):
        k = tuple(sorted((i, j)))
        if k not in cache:
            m = V[i] + V[j]; V.append(m/np.linalg.norm(m)); cache[k] = len(V) - 1
        return cache[k]
    F2 = []
    for a, b, c in F:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        F2 += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
    V = np.array(V)
    # tourner autour de z pour qu'un sommet de l'équateur soit à l'azimut 0
    eq = [i for i in range(len(V)) if abs(V[i, 2]) < 1e-9]
    a0 = np.arctan2(V[eq[0], 1], V[eq[0], 0])
    c, s = np.cos(-a0), np.sin(-a0); Rz = np.array([[c,-s,0],[s,c,0],[0,0,1]])
    V = V @ Rz.T
    if full: return V, F2
    H = [f for f in F2 if V[f].mean(0)[2] > 1e-6]
    # orienter chaque face vers l'extérieur
    H = [f if np.dot(np.cross(V[f[1]]-V[f[0]], V[f[2]]-V[f[0]]), V[f].mean(0)) > 0 else [f[0], f[2], f[1]] for f in H]
    return V, H
if __name__ == "__main__":
    V, H = geodesic2v()
    print(len(H), "faces dans l'hémisphère")
    el = lambda p: np.degrees(np.arcsin(p[2]/np.linalg.norm(p)))
    az = lambda p: np.degrees(np.arctan2(p[1], p[0])) % 360
    rows = []
    for i, f in enumerate(H):
        c = V[f].mean(0); e = [np.linalg.norm(V[f[k]] - V[f[(k+1)%3]]) for k in range(3)]
        n = np.cross(V[f[1]]-V[f[0]], V[f[2]]-V[f[0]]); n /= np.linalg.norm(n)
        rin = 2*0.5*np.linalg.norm(np.cross(V[f[1]]-V[f[0]], V[f[2]]-V[f[0]]))/sum(e)
        rows.append((round(el(c), 1), round(az(c), 1), i, [round(x*300, 1) for x in e], round(rin*300, 1)))
    for r in sorted(rows): print(r)
