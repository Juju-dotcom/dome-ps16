#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
À TESTER SUR LA TOUR WINDOWS.
Écrit sur le Mac, sans caméra ni Arduino. Vérifié seulement avec un FAUX port série qui
rejoue la sortie du programme Arduino simulé et une FAUSSE caméra : le protocole série et
la copie des images fonctionnent, mais RIEN n'a tourné avec la vraie caméra (noms de
fonctions arena_api écrits de mémoire, voir les mentions « NON VERIFIE »).

Ce que fait le script (une séance d'acquisition du dôme PS-16) :
  1. ouvre le port série du Mega (115200 bauds) et attend son redémarrage ;
  2. règle la caméra LUCID Triton (Arena SDK, arena_api) :
        PixelFormat = BayerRG12, ExposureAuto = Off, ExposureTime = pose,
        TriggerSelector = FrameStart, TriggerSource = Line0,
        TriggerActivation = RisingEdge, TriggerMode = On ;
  3. démarre le flux, puis envoie « SEQ <pose_ms> <attente_ms> » à l'Arduino ;
  4. à chaque ligne « IMG k » reçue, prend l'image dans la caméra et l'enregistre
     brute (16 bits, valeurs 0..4095) : led_01.npy ... led_16.npy (+ .tiff si demandé) ;
  5. écrit meta.json (réglages, maximum de chaque image, part de pixels saturés) ;
  6. envoie toujours « OFF » à la fin, même en cas d'erreur.

Installation (Windows) :
    pip install pyserial numpy            (tifffile en option : pip install tifffile)
    arena_api : se pose depuis le « wheel » du SDK Arena (dossier Python de l'installation
    d'Arena SDK, mode Developer), pas depuis PyPI.

Exemples :
    python pc_exemple.py --port COM3 --pose-ms 300
    python pc_exemple.py --port COM3 --pose-ms 300 --vues 10 --rot-deg 36 --home --tiff
    python pc_exemple.py --port COM3 --sans-camera        (teste seulement le port série)

Poids : une image BayerRG12 non emballée de la TRI050S-CC fait 2448 x 2048 x 2 octets,
soit 10 Mo. Une séance de 16 LED = 160 Mo ; 10 vues = 1,6 Go (vérifie l'espace disque).

Noms de noeuds Arena : ceux de la demande (PixelFormat, ExposureAuto, ExposureTime,
TriggerSelector, TriggerMode, TriggerSource, TriggerActivation) sont des noms GenICam
standard. Tout autre nom est marqué « NON VERIFIE » dans le code.
"""

import argparse
import ctypes
import datetime
import json
import sys
import time
from pathlib import Path

import numpy as np

try:
    import serial  # pyserial
except ImportError:
    sys.exit("pyserial manque : pip install pyserial")

NB_LED = 16
BAUDS = 115200
SATURATION_12_BITS = 4095


# ----------------------------------------------------------------------------
# Série : une commande, une réponse « OK <CMD> ... » ou « ERR <CMD> ... »
# ----------------------------------------------------------------------------
def lire_ligne(ser):
    """Lit une ligne (texte) ou renvoie None si rien n'est arrivé (timeout court du port)."""
    brut = ser.readline()
    if not brut:
        return None
    return brut.decode("ascii", errors="replace").strip()


def ouvrir_serie(port):
    ser = serial.Serial(port, BAUDS, timeout=0.05)
    # Ouvrir le port redémarre le Mega (DTR) : on attend sa ligne « EVT BOOT ».
    fin = time.time() + 6.0
    boot = False
    while time.time() < fin and not boot:
        ligne = lire_ligne(ser)
        if ligne and ligne.startswith("EVT BOOT"):
            print("Arduino :", ligne)
            boot = True
    if not boot:
        print("Pas de ligne EVT BOOT (la carte n'a peut-etre pas redemarre) : on continue.")
    ser.reset_input_buffer()
    return ser


def commande(ser, cmd, delai_s=5.0, afficher_evt=True):
    """Envoie une commande et attend sa réponse finale. Renvoie la ligne « OK ... ».
    Lève RuntimeError sur « ERR ... » ou si le délai est dépassé."""
    nom = cmd.split()[0].upper()
    ser.write((cmd + "\n").encode("ascii"))
    fin = time.time() + delai_s
    while time.time() < fin:
        ligne = lire_ligne(ser)
        if ligne is None:
            continue
        if ligne.startswith(("OK " + nom, "ERR " + nom, "ERR ?")):
            if ligne.startswith("OK"):
                return ligne
            raise RuntimeError(ligne)
        if afficher_evt and ligne and not ligne.startswith("#"):
            print("   (arduino)", ligne)
    raise RuntimeError("Délai dépassé pour la commande : " + cmd)


# ----------------------------------------------------------------------------
# Caméra LUCID (arena_api)
# ----------------------------------------------------------------------------
def _noeud(nodemap, nom):
    """Renvoie le noeud « nom ». get_node(str) est la forme des exemples Arena ;
    si la version renvoie un dictionnaire, on prend la clé."""
    n = nodemap.get_node(nom)
    if isinstance(n, dict):
        n = n[nom]
    return n


def regler(nodemap, nom, valeur, obligatoire=True):
    """Écrit un noeud puis relit sa valeur. Si obligatoire est faux, une erreur n'arrête pas le script."""
    try:
        noeud = _noeud(nodemap, nom)
        noeud.value = valeur
        relu = noeud.value
        print(f"   {nom} = {relu}")
        return relu
    except Exception as e:  # noqa: BLE001 : on veut tout rattraper ici
        if obligatoire:
            raise RuntimeError(f"Impossible de régler {nom} = {valeur!r} : {e}") from e
        print(f"   (ignoré) {nom} : {e}")
        return None


def regler_camera(device, pose_ms):
    nm = device.nodemap
    print("Réglage de la caméra :")
    regler(nm, "PixelFormat", "BayerRG12")           # brut 12 bits, réponse linéaire
    regler(nm, "ExposureAuto", "Off")
    regler(nm, "ExposureTime", float(pose_ms) * 1000.0)   # en microsecondes
    regler(nm, "TriggerSelector", "FrameStart")
    regler(nm, "TriggerSource", "Line0")
    regler(nm, "TriggerActivation", "RisingEdge")
    regler(nm, "TriggerMode", "On")                  # en dernier : la caméra attend l'impulsion
    # --- réglages facultatifs, noms NON VERIFIES sur la TRI050S-CC (ignorés si absents) ---
    regler(nm, "GainAuto", "Off", obligatoire=False)           # nom GenICam standard, NON VERIFIE
    try:
        # NON VERIFIE : noms vus dans les exemples LUCID, de mémoire.
        tl = device.tl_stream_nodemap
        regler(tl, "StreamAutoNegotiatePacketSize", True, obligatoire=False)
        regler(tl, "StreamPacketResendEnable", True, obligatoire=False)
    except Exception as e:  # noqa: BLE001
        print("   (ignoré) tl_stream_nodemap :", e)


def prendre_image(device, delai_ms):
    """Attend l'image déclenchée. Le paramètre timeout de get_buffer est celui que je
    crois exister : NON VERIFIE. S'il manque, on appelle sans délai (peut bloquer)."""
    try:
        return device.get_buffer(timeout=delai_ms)
    except TypeError:
        return device.get_buffer()


def buffer_vers_numpy(buf):
    """Copie l'image brute dans un tableau uint16 (hauteur, largeur), valeurs 0..4095.
    Attend BayerRG12 non emballé : 16 bits par pixel, les 12 bits utiles dans les bits bas."""
    w, h, bpp = int(buf.width), int(buf.height), int(buf.bits_per_pixel)
    if bpp != 16:
        raise RuntimeError(
            f"bits_per_pixel = {bpp}, attendu 16 pour BayerRG12 non emballé. "
            "Vérifie le PixelFormat dans ArenaView."
        )
    adresse = ctypes.cast(buf.pdata, ctypes.c_void_p).value
    brut = ctypes.string_at(adresse, w * h * 2)
    return np.frombuffer(brut, dtype="<u2").reshape(h, w).copy()


# ----------------------------------------------------------------------------
# Enregistrement
# ----------------------------------------------------------------------------
def enregistrer(dossier, k, image, tiff):
    np.save(dossier / f"led_{k:02d}.npy", image)
    if tiff:
        try:
            import tifffile
            tifffile.imwrite(dossier / f"led_{k:02d}.tiff", image)
        except ImportError:
            print("   tifffile absent : pip install tifffile (le .npy est enregistré)")


def acquerir_sequence(ser, device, pose_ms, attente_ms, dossier, tiff, delai_image_ms):
    """Envoie SEQ et enregistre une image à chaque « IMG k ». Renvoie la liste des résumés."""
    dossier.mkdir(parents=True, exist_ok=True)
    resumes = []
    ser.write(f"SEQ {pose_ms} {attente_ms}\n".encode("ascii"))
    limite = time.time() + NB_LED * (pose_ms + attente_ms + 400) / 1000.0 + 30.0
    while True:
        if time.time() > limite:
            raise RuntimeError("La séquence ne se termine pas (délai dépassé).")
        ligne = lire_ligne(ser)
        if ligne is None:
            continue
        if ligne.startswith("IMG "):
            k = int(ligne.split()[1])
            if device is None:
                print(f"   LED {k:2d} : (sans caméra)")
                continue
            buf = prendre_image(device, delai_image_ms)
            try:
                image = buffer_vers_numpy(buf)
            finally:
                device.requeue_buffer(buf)           # toujours rendre le tampon à la caméra
            part_sat = float((image >= SATURATION_12_BITS).mean())
            resume = {"led": k, "max": int(image.max()), "part_saturee": part_sat,
                      "largeur": int(image.shape[1]), "hauteur": int(image.shape[0]),
                      "fichier": f"led_{k:02d}.npy"}
            resumes.append(resume)
            enregistrer(dossier, k, image, tiff)
            avert = "  <-- SATURATION : réduis la pose" if part_sat > 0.001 else ""
            print(f"   LED {k:2d} : max {resume['max']:4d}, saturés {100 * part_sat:.3f} %{avert}")
        elif ligne.startswith("OK SEQ"):
            print("Arduino :", ligne)
            return resumes
        elif ligne.startswith("ERR"):
            raise RuntimeError(ligne)
        elif ligne and not ligne.startswith("#"):
            print("   (arduino)", ligne)


# ----------------------------------------------------------------------------
# Programme principal
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Acquisition des 16 images du dôme PS-16")
    ap.add_argument("--port", required=True, help="port série du Mega, ex. COM3")
    ap.add_argument("--pose-ms", type=int, default=300, help="pose = ExposureTime (ms), aussi envoyée à SEQ")
    ap.add_argument("--attente-ms", type=int, default=50, help="LED allumée -> déclenchement (ms)")
    ap.add_argument("--vues", type=int, default=1, help="nombre de vues (rotation entre deux vues)")
    ap.add_argument("--rot-deg", type=float, default=0.0, help="rotation du plateau entre deux vues (degrés)")
    ap.add_argument("--home", action="store_true", help="HOME (capteur zéro) avant la première vue")
    ap.add_argument("--sortie", default="captures", help="dossier de sortie")
    ap.add_argument("--tiff", action="store_true", help="écrire aussi des .tiff 16 bits (tifffile)")
    ap.add_argument("--delai-image-ms", type=int, default=3000, help="délai d'attente d'une image (ms)")
    ap.add_argument("--sans-camera", action="store_true", help="teste seulement le port série")
    args = ap.parse_args()

    horodatage = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    racine = Path(args.sortie) / horodatage

    ser = ouvrir_serie(args.port)
    device = None
    system = None
    meta = {
        "date": horodatage, "pose_ms": args.pose_ms, "attente_ms": args.attente_ms,
        "exposure_time_us": args.pose_ms * 1000.0, "pixel_format": "BayerRG12",
        "motif_bayer": "RGGB (BayerRG)", "rot_deg": args.rot_deg, "vues": [],
    }
    try:
        print(commande(ser, "STATUS"))
        commande(ser, "OFF")

        if not args.sans_camera:
            from arena_api.system import system as _system  # import tardif : --sans-camera n'en a pas besoin
            system = _system
            infos = system.device_infos
            if not infos:
                raise RuntimeError("Aucune caméra trouvée (PoE branché ? ArenaView fermé ?)")
            print("Caméra :", infos[0])
            device = system.create_device(device_infos=infos[0])[0]
            regler_camera(device, args.pose_ms)
            device.start_stream()

        if args.home:
            print(commande(ser, "HOME", delai_s=40.0))

        for v in range(args.vues):
            print(f"--- Vue {v + 1}/{args.vues} ---")
            dossier = racine / f"vue_{v:02d}"
            resumes = acquerir_sequence(ser, device, args.pose_ms, args.attente_ms,
                                        dossier, args.tiff, args.delai_image_ms)
            meta["vues"].append({"dossier": dossier.name, "images": resumes})
            if v < args.vues - 1 and args.rot_deg:
                print(commande(ser, f"ROT {args.rot_deg}", delai_s=30.0))
        if not args.sans_camera:
            racine.mkdir(parents=True, exist_ok=True)
            (racine / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print("Enregistré dans", racine.resolve())
    finally:
        try:
            print(commande(ser, "OFF", delai_s=3.0))     # LED éteintes quoi qu'il arrive
        except Exception as e:  # noqa: BLE001
            print("OFF a échoué :", e)
        if device is not None:
            try:
                device.stop_stream()
                regler(device.nodemap, "TriggerMode", "Off", obligatoire=False)
            except Exception as e:  # noqa: BLE001
                print("Arrêt caméra :", e)
        if system is not None:
            try:
                system.destroy_device()
            except Exception as e:  # noqa: BLE001
                print("destroy_device :", e)
        ser.close()


if __name__ == "__main__":
    main()
