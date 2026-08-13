import subprocess
import os
import sys
import time
import requests

# Pour affichage UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 🔑 Remplace par ta propre clé API DeepL
CLE_API_DEEPL = 'clé perso à renseigner:fx'

def lancer_whisper(fichier_entree, langue="en"):
    dossier = os.path.dirname(fichier_entree)
    nom_fichier = os.path.splitext(os.path.basename(fichier_entree))[0]
    cmd = [
        "whisper",
        fichier_entree,
        "--model", "medium",
        "--language", langue,
        "--output_format", "srt",
        "--output_dir", os.path.join(dossier, "sorties")
    ]
    print("📼 Lancement de Whisper...")
    subprocess.run(cmd, check=True)
    print("✅ Transcription terminée.")
    return os.path.join(dossier, "sorties", f"{nom_fichier}.srt")

def traduire_srt(fichier_srt_entree, fichier_srt_sortie, source_lang="EN",
    target_lang="FR"):
    with open(fichier_srt_entree, "r", encoding="utf-8") as f:
        lignes = f.readlines()

    buffer_texte = ""
    blocs = []
    for ligne in lignes:
        if ligne.strip().isdigit() or "-->" in ligne or ligne.strip() == "":
            if buffer_texte:
                blocs.append(buffer_texte.strip())
                buffer_texte = ""
            blocs.append(ligne.strip())
        else:
            buffer_texte += " " + ligne.strip()

    if buffer_texte:
        blocs.append(buffer_texte.strip())

    print("🌐 Traduction en cours via DeepL...")
    resultat = []
    for bloc in blocs:
        if bloc == "" or bloc.isdigit() or "-->" in bloc:
            resultat.append(bloc)
        else:
            try:
                reponse = requests.post(
                    "https://api-free.deepl.com/v2/translate",
                     headers={
                        "Authorization": f"DeepL-Auth-Key {CLE_API_DEEPL}"
                    },
                    data={
                        "text": bloc,
                        "source_lang": source_lang,
                        "target_lang": target_lang
                    },
                    timeout=30
                )
                if reponse.status_code == 200:
                    traduction = reponse.json()["translations"][0]["text"]
                    resultat.append(traduction)
                else:
                    print("⚠️ Erreur HTTP :", reponse.status_code)
                    resultat.append(bloc)
            except Exception as e:
                print("❌ Erreur DeepL :", e)
                resultat.append(bloc)
        time.sleep(1.2)  # Respect du quota gratuit

    with open(fichier_srt_sortie, "w", encoding="utf-8") as f:
        for ligne in resultat:
            f.write(ligne + "\n")

    print("✅ Traduction terminée :", fichier_srt_sortie)

def main():
    if len(sys.argv) >= 2:
        chemin_video = sys.argv[1]
    else:
        chemin_video = input("📂 Chemin vers la vidéo (.mp4) : ").strip()

    if not os.path.isfile(chemin_video):
        print("❌ Fichier non trouvé :", chemin_video)
        return

    fichier_srt_entree = lancer_whisper(chemin_video)
    base = os.path.splitext(fichier_srt_entree)[0]
    fichier_srt_sortie = base + "_FR.srt"
    traduire_srt(fichier_srt_entree, fichier_srt_sortie)

if __name__ == "__main__":
    main()
