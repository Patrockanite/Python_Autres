import subprocess
import os
import re
import json
import requests
import websocket
import time
import shutil
from traitement_whisper_traduction_V2 import lancer_whisper, traduire_srt

DOSSIER_SORTIE = r"C:\Tim_Pierce_Audios"
CHROME_DEBUG = "http://127.0.0.1:9222"


def verifier_ou_lancer_chrome():
    """
    Vérifie si le Chrome dédié Tim Pierce est accessible sur le port 9222.
    S'il ne l'est pas, le lance automatiquement.
    """

    try:
        response = requests.get(
            f"{CHROME_DEBUG}/json",
            timeout=2
        )

        if response.status_code == 200:
            print("Chrome Tim Pierce déjà ouvert.")
            return True

    except requests.RequestException:
        pass

    print("Chrome Tim Pierce non détecté.")
    print("Lancement de Chrome...")

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profil_path = r"C:\Tim_Pierce_Chrome"

    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--remote-allow-origins=http://127.0.0.1:9222",
        f"--user-data-dir={profil_path}"
    ]

    try:
        subprocess.Popen(cmd)
    except OSError as e:
        print("Impossible de lancer Chrome.")
        print(e)
        return False

    # On laisse quelques secondes à Chrome pour démarrer
    for _ in range(10):
        time.sleep(1)

        try:
            response = requests.get(
                f"{CHROME_DEBUG}/json",
                timeout=2
            )

            if response.status_code == 200:
                print("Chrome Tim Pierce lancé avec succès.")
                return True

        except requests.RequestException:
            pass

    print("Chrome ne répond pas sur le port 9222.")
    return False


def nettoyer_nom_fichier(nom):
    """Supprime les caractères interdits dans les noms de fichiers Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', nom).strip()


def trouver_page_tim_pierce():
    """Recherche une leçon Tim Pierce parmi les onglets Chrome ouverts."""

    try:
        tabs = requests.get(
            f"{CHROME_DEBUG}/json",
            timeout=5
        ).json()

    except requests.RequestException:
        print()
        print("Impossible de communiquer avec Chrome.")
        print("Vérifie que le Chrome dédié Tim Pierce est ouvert.")
        return None

    for tab in tabs:
        url = tab.get("url", "")

        if "timpierce.com/products/" in url and "/posts/" in url:
            return tab

    return None

def attendre_page_tim_pierce():
    """
    Attend que l'utilisateur ouvre une leçon Tim Pierce dans Chrome.
    """

    print()
    print("En attente d'une leçon Tim Pierce...")
    print("Ouvre la leçon que tu souhaites récupérer dans Chrome.")
    print()

    while True:
        page = trouver_page_tim_pierce()

        if page is not None:
            print("Leçon détectée.")
            return page

        time.sleep(1)

def trouver_titre_lecon(html):
    """Recherche le titre de la leçon Kajabi."""

    match = re.search(
        r'<h1[^>]*class="[^"]*post-body-title[^"]*"[^>]*>(.*?)</h1>',
        html,
        re.DOTALL
    )

    if match:
        titre = re.sub(r'<[^>]+>', '', match.group(1))
        titre = re.sub(r'\s+', ' ', titre).strip()
        return titre

    return None


def recuperer_html(page):
    """Récupère le HTML de l'onglet Chrome authentifié."""

    ws = websocket.create_connection(
        page["webSocketDebuggerUrl"]
    )

    requete = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True
        }
    }

    ws.send(json.dumps(requete))

    while True:
        reponse = json.loads(ws.recv())

        if reponse.get("id") == 1:
            ws.close()

            try:
                return reponse["result"]["result"]["value"]

            except KeyError:
                return None


def trouver_wistia_id(html):
    """Recherche l'identifiant de la vidéo Wistia dans le HTML."""

    match = re.search(
        r'wistia_async_([a-zA-Z0-9]{10})',
        html
    )

    if match:
        return match.group(1)

    return None


def telecharger_audio(wistia_id, nom_lecon):
    """Télécharge uniquement la piste audio de la vidéo Wistia."""

    url = (
        f"https://fast.wistia.com/embed/medias/"
        f"{wistia_id}.m3u8"
    )

    nom_lecon = nettoyer_nom_fichier(nom_lecon)

    fichier_sortie = os.path.join(
        DOSSIER_SORTIE,
        f"{nom_lecon}.aac"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", url,
        "-vn",
        "-c:a", "copy",
        fichier_sortie
    ]

    print()
    print("Téléchargement de l'audio...")
    print(f"Identifiant Wistia : {wistia_id}")
    print(f"Flux HLS           : {url}")
    print(f"Fichier de sortie  : {fichier_sortie}")
    print()

    try:
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError:
        print()
        print("Erreur pendant le téléchargement avec FFmpeg.")
        return False

    print()
    print("Téléchargement terminé.")
    print(f"Audio enregistré dans : {fichier_sortie}")

    return fichier_sortie

def telecharger_video(wistia_id, nom_lecon):
    """Télécharge automatiquement la meilleure vidéo ne dépassant pas 540p."""

    url = (
        f"https://fast.wistia.com/embed/medias/"
        f"{wistia_id}.m3u8"
    )

    nom_lecon = nettoyer_nom_fichier(nom_lecon)

    fichier_sortie = os.path.join(
        DOSSIER_SORTIE,
        f"{nom_lecon}.mp4"
    )

    print()
    print("Analyse des qualités vidéo disponibles...")

    # Analyse du manifeste HLS avec ffprobe
    cmd_probe = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_programs",
        url
    ]

    try:
        resultat = subprocess.run(
            cmd_probe,
            capture_output=True,
            text=True,
            check=True
        )

        donnees = json.loads(resultat.stdout)

    except (subprocess.CalledProcessError, json.JSONDecodeError):
        print("Impossible d'analyser les flux vidéo.")
        return False

    candidats = []

    for programme in donnees.get("programs", []):
        video = None
        audio = None

        for stream in programme.get("streams", []):
            if stream.get("codec_type") == "video":
                video = stream

            elif stream.get("codec_type") == "audio":
                audio = stream

        if video and audio:
            hauteur = video.get("height", 0)

            if hauteur <= 540:
                candidats.append(
                    (
                        hauteur,
                        video["index"],
                        audio["index"]
                    )
                )

    if not candidats:
        print("Aucune qualité vidéo inférieure ou égale à 540p trouvée.")
        return False

    # Choix de la meilleure résolution <= 540p
    hauteur, index_video, index_audio = max(
        candidats,
        key=lambda x: x[0]
    )

    print(
        f"Qualité sélectionnée : "
        f"{hauteur}p "
        f"(vidéo #{index_video}, audio #{index_audio})"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", url,
        "-map", f"0:{index_video}",
        "-map", f"0:{index_audio}",
        "-c", "copy",
        fichier_sortie
    ]

    print()
    print(f"Téléchargement de la vidéo {hauteur}p...")
    print(f"Fichier de sortie : {fichier_sortie}")
    print()

    try:
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError:
        print()
        print("Erreur pendant le téléchargement de la vidéo.")
        return False

    print()
    print("Téléchargement vidéo terminé.")
    print(f"Vidéo enregistrée dans : {fichier_sortie}")

    return fichier_sortie

def creer_sous_titres(fichier_audio):
    """Transcrit l'audio avec Whisper puis traduit le SRT avec DeepL."""

    print()
    print("=== Création des sous-titres ===")
    print()

    try:
        # Whisper crée le SRT anglais
        fichier_srt_en = lancer_whisper(
            fichier_audio,
            langue="en"
        )

        # Construction du nom du SRT français
        base = os.path.splitext(fichier_srt_en)[0]
        fichier_srt_fr = base + "_FR.srt"

        # Traduction DeepL
        traduire_srt(
            fichier_srt_en,
            fichier_srt_fr
        )

        print()
        print("Sous-titrage français terminé.")
        print(f"Fichier SRT : {fichier_srt_fr}")

        return fichier_srt_fr

    except subprocess.CalledProcessError as e:
        print()
        print("Erreur pendant le traitement Whisper.")
        print(e)
        return False

    except Exception as e:
        print()
        print("Erreur pendant la création des sous-titres.")
        print(e)
        return False

def finaliser_fichiers(fichier_audio, fichier_video, fichier_srt_fr):
    """
    Place le SRT français à côté du MP4 avec le même nom de base,
    puis supprime les fichiers intermédiaires.
    """

    if not fichier_video or not os.path.isfile(fichier_video):
        print("Vidéo introuvable : nettoyage annulé.")
        return False

    if not fichier_srt_fr or not os.path.isfile(fichier_srt_fr):
        print("SRT français introuvable : nettoyage annulé.")
        return False

    # Le SRT final porte exactement le même nom que le MP4
    base_video = os.path.splitext(fichier_video)[0]
    fichier_srt_final = base_video + ".srt"

    try:
        # Déplacement et renommage du SRT français
        shutil.move(
            fichier_srt_fr,
            fichier_srt_final
        )

        print()
        print(f"SRT français final : {fichier_srt_final}")

        # Suppression de l'AAC
        if fichier_audio and os.path.isfile(fichier_audio):
            os.remove(fichier_audio)
            print("Fichier AAC intermédiaire supprimé.")

        # Le SRT anglais porte le même nom que le SRT FR,
        # mais sans le suffixe _FR
        if fichier_srt_fr.lower().endswith("_fr.srt"):
            fichier_srt_en = fichier_srt_fr[:-7] + ".srt"

            if os.path.isfile(fichier_srt_en):
                os.remove(fichier_srt_en)
                print("SRT anglais intermédiaire supprimé.")

        print("Nettoyage terminé.")

        return fichier_srt_final

    except OSError as e:
        print()
        print("Erreur pendant la finalisation des fichiers :")
        print(e)
        return False

def main():

    os.makedirs(DOSSIER_SORTIE, exist_ok=True)

    print()
    print("=== Tim Pierce Audios ===")
    print()

    if not verifier_ou_lancer_chrome():
        return

    # Recherche de la leçon ouverte dans Chrome
    page = trouver_page_tim_pierce()

    if page is None:
        page = attendre_page_tim_pierce()

    print()
    print("Leçon détectée :")
    print(page["url"])

    # Récupération du HTML
    html = recuperer_html(page)

    if html is None:
        print("Impossible de récupérer le contenu de la page.")
        return

    # Recherche de Wistia
    wistia_id = trouver_wistia_id(html)

    if wistia_id is None:
        print("Aucune vidéo Wistia trouvée dans cette leçon.")
        return

    print()
    print(f"Vidéo Wistia détectée : {wistia_id}")

    # Recherche automatique du titre de la leçon
    nom_lecon = trouver_titre_lecon(html)

    if nom_lecon:
        print(f"Titre de la leçon       : {nom_lecon}")
    else:
        print("Titre de la leçon introuvable.")
        nom_lecon = input("Nom de la leçon : ").strip()

    if not nom_lecon:
        nom_lecon = wistia_id

    ## Téléchargement audio
    fichier_audio = telecharger_audio(
        wistia_id,
        nom_lecon
    )

    if not fichier_audio:
        print("Impossible de récupérer l'audio.")
        return


    # Téléchargement vidéo de travail
    fichier_video = telecharger_video(
        wistia_id,
        nom_lecon
    )

    if not fichier_video:
        print()
        print("La vidéo n'a pas pu être récupérée.")
        print("Le sous-titrage va néanmoins être effectué.")


    # Whisper + DeepL
    fichier_srt_fr = creer_sous_titres(
        fichier_audio
    )

    if not fichier_srt_fr:
        print()
        print("Échec de la création des sous-titres.")
        return

    # Rangement et nettoyage des fichiers
    fichier_srt_final = finaliser_fichiers(
        fichier_audio,
        fichier_video,
        fichier_srt_fr
    )

    if not fichier_srt_final:
        print()
        print("Le traitement est terminé, mais le nettoyage a échoué.")
        return

    print()
    print("========================================")
    print("TRAITEMENT TERMINÉ")
    print("========================================")
    print()
    print(f"Vidéo : {fichier_video}")
    print(f"SRT FR : {fichier_srt_final}")

if __name__ == "__main__":
    main()