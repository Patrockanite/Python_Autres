# MajusculeClipboard.py
# Transforme un texte en MAJUSCULE et copie dans le presse-papiers

import tkinter as tk

# Demande du texte
texte = input("Entrez un texte : ")

# Conversion en majuscule
resultat = texte.upper()
print("\nRésultat :", resultat)

# Copie dans le presse-papiers
try:
    r = tk.Tk()
    r.withdraw()  # Masquer la fenêtre Tkinter
    r.clipboard_clear()
    r.clipboard_append(resultat)
    r.update()  # Nécessaire pour valider la copie
    r.destroy()
    print("✔ Copié dans le presse-papiers")
except Exception as e:
    print("✖ Impossible de copier dans le presse-papiers :", e)

# Pause pour éviter que la fenêtre se ferme immédiatement
input("\nAppuyez sur Entrée pour fermer...")
