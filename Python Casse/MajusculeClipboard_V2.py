# MajusculeClipboardLoop_win32.py
# Boucle : transforme en MAJUSCULES et copie dans le presse-papiers (Win32 API)
# Quitter : ligne vide, un espace, 'exit' ou 'quit'

import sys
import ctypes
from ctypes import wintypes

# --- Clipboard (Win32, CF_UNICODETEXT) ---
CF_UNICODETEXT = 13

user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

OpenClipboard = user32.OpenClipboard
OpenClipboard.argtypes = [wintypes.HWND]
OpenClipboard.restype = wintypes.BOOL

EmptyClipboard = user32.EmptyClipboard
EmptyClipboard.argtypes = []
EmptyClipboard.restype = wintypes.BOOL

SetClipboardData = user32.SetClipboardData
SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
SetClipboardData.restype = wintypes.HANDLE

GetClipboardData = user32.GetClipboardData  # pas utilisé, mais dispo
CloseClipboard = user32.CloseClipboard
CloseClipboard.argtypes = []
CloseClipboard.restype = wintypes.BOOL

GlobalAlloc = kernel32.GlobalAlloc
GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
GlobalAlloc.restype = wintypes.HGLOBAL

GlobalLock = kernel32.GlobalLock
GlobalLock.argtypes = [wintypes.HGLOBAL]
GlobalLock.restype = wintypes.LPVOID

GlobalUnlock = kernel32.GlobalUnlock
GlobalUnlock.argtypes = [wintypes.HGLOBAL]
GlobalUnlock.restype = wintypes.BOOL

GMEM_MOVEABLE = 0x0002

def copy_to_clipboard_unicode(text: str) -> bool:
    """
    Copie 'text' dans le presse-papiers Windows en CF_UNICODETEXT (UTF-16 LE + NUL).
    Retourne True si OK, False sinon.
    """
    # CF_UNICODETEXT attend du UTF-16-LE terminé par deux octets NUL (wchar_t 0)
    data = (text + '\x00').encode('utf-16-le')
    h_global = GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not h_global:
        return False

    lp_global = GlobalLock(h_global)
    if not lp_global:
        return False

    # Copie les octets dans le bloc alloué
    ctypes.memmove(lp_global, data, len(data))
    GlobalUnlock(h_global)

    # Ouvre le presse-papiers, le vide et pose la donnée
    if not OpenClipboard(None):
        return False
    try:
        if not EmptyClipboard():
            return False
        if not SetClipboardData(CF_UNICODETEXT, h_global):
            return False
        # Attention: ne pas libérer h_global après SetClipboardData (le système en devient propriétaire)
        h_global = None
    finally:
        CloseClipboard()
    return True

# --- Logic sortie ---
def doit_quitter(s: str) -> bool:
    s_raw = s  # pour détecter espace isolé
    s_stripped = s.strip().lower()
    return (s_raw == "" or s_raw == " " or s_stripped in {"exit", "quit"})

print("=== Convertisseur en MAJUSCULES (Windows, presse-papiers fiable) ===")
print("Saisissez vos lignes ; elles sont copiées dans le presse-papiers.")
print("Quitter : Entrée (ligne vide) / espace / 'exit' / 'quit'.\n")

while True:
    try:
        texte = input("Texte : ")
    except EOFError:
        break

    if doit_quitter(texte):
        print("\nFin du programme. 👋")
        break

    resultat = texte.upper()
    print("Résultat :", resultat)

    if copy_to_clipboard_unicode(resultat):
        print("✔ Copié dans le presse-papiers\n")
    else:
        print("✖ Échec de la copie dans le presse-papiers.\n")

# Garde la fenêtre ouverte si lancé par double-clic
try:
    input("Appuyez sur Entrée pour fermer...")
except Exception:
    pass



