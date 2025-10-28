# Programme de changement de casse

# Demande un texte à l'utilisateur
# Programme de changement de casse

def transformer(texte, choix):
    if choix == "1":
        return texte.upper()
    elif choix == "2":
        return texte.lower()
    elif choix == "3":
        return texte.title()
    elif choix == "4":
        return texte.capitalize()
    else:
        return None

def copier_dans_presse_papiers(texte):
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(texte)
        r.update()
        r.destroy()
        return True
    except Exception:
        return False

while True:
    texte = input("Entrez un texte : ")

    print("\nChoisissez une transformation :")
    print("1 - Tout en MAJUSCULES")
    print("2 - Tout en minuscules")
    print("3 - Première lettre de chaque mot en majuscule")
    print("4 - Première lettre de la phrase en majuscule")

    choix = input("Votre choix (1/2/3/4) : ")
    resultat = transformer(texte, choix)

    if resultat is None:
        print("Choix invalide.\n")
        continue

    print("\nRésultat :")
    print(resultat)

    # Proposer de sauvegarder
    save = input("\nSauvegarder dans un fichier (o/n) ? ").strip().lower()
    if save == "o":
        nom = input("Nom du fichier (ex: resultat.txt) : ").strip() or "resultat.txt"
        with open(nom, "w", encoding="utf-8") as f:
            f.write(resultat)
        print(f"✔ Enregistré dans '{nom}'")

    # Proposer de copier dans le presse-papiers
    clip = input("Copier dans le presse-papiers (o/n) ? ").strip().lower()
    if clip == "o":
        ok = copier_dans_presse_papiers(resultat)
        print("✔ Copié dans le presse-papiers" if ok else "✖ Impossible de copier (tkinter indisponible)")

    # Encore ?
    again = input("\nRefaire une transformation (o/n) ? ").strip().lower()
    if again != "o":
        break

input("\nAppuyez sur Entrée pour fermer...")

