# flv_to_html.py
# Usage 1 (fichier) :  glisser-déposer un .flv sur ce script, ou:
#   python flv_to_html.py "C:\Videos\clip.flv"
# Usage 2 (dossier) :   traite tous les .flv d'un dossier:
#   python flv_to_html.py "C:\Videos"

import os
import sys
import glob
from pathlib import Path
import ffmpeg

def convert_flv_to_mp4(in_path: Path) -> Path:
    """Tente un remux (copy) sinon réencode en H.264/AAC. Renvoie le chemin du .mp4."""
    out_mp4 = in_path.with_suffix(".mp4")
    # 1) tentative sans réencodage
    try:
        (
            ffmpeg
            .input(str(in_path))
            .output(str(out_mp4), c="copy", movflags="+faststart")
            .overwrite_output()
            .run(quiet=True)
        )
        # probe pour s'assurer que le fichier est lisible
        ffmpeg.probe(str(out_mp4))
        print(f"[OK] {in_path.name} -> {out_mp4.name} (remux sans perte)")
        return out_mp4
    except Exception:
        pass

    # 2) fallback réencodage
    (
        ffmpeg
        .input(str(in_path))
        .output(
            str(out_mp4),
            vcodec="libx264",
            acodec="aac",
            crf=20,
            preset="fast",
            movflags="+faststart"
        )
        .overwrite_output()
        .run(quiet=False)
    )
    print(f"[OK] {in_path.name} -> {out_mp4.name} (réencodé)")
    return out_mp4

def make_poster(mp4_path: Path) -> Path | None:
    """Extrait une image de prévisualisation à 1s. Renvoie le .jpg ou None si échec."""
    poster = mp4_path.with_suffix(".jpg")
    try:
        (
            ffmpeg
            .input(str(mp4_path), ss=1)
            .output(str(poster), vframes=1)
            .overwrite_output()
            .run(quiet=True)
        )
        return poster
    except Exception:
        return None

def write_html(mp4_path: Path, poster_path: Path | None):
    """Crée un HTML minimal pour lecture navigateur."""
    html_path = mp4_path.with_suffix(".html")
    poster_attr = f' poster="{poster_path.name}"' if poster_path and poster_path.exists() else ""
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{mp4_path.stem}</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{{margin:0;padding:2rem;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif;background:#0f1214;color:#e6e6e6}}
    .wrap{{max-width:960px;margin:0 auto}}
    h1{{font-size:1.1rem;font-weight:600;margin:0 0 1rem;opacity:.9}}
    .card{{background:#151a1f;border:1px solid #222832;border-radius:16px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.35)}}
    video{{width:100%;height:auto;border-radius:12px;display:block;outline:none}}
    .meta{{margin-top:.75rem;font-size:.9rem;opacity:.8}}
    a{{color:#8ab4f8;text-decoration:none}}
    a:hover{{text-decoration:underline}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Lecture : {mp4_path.name}</h1>
    <div class="card">
      <video controls preload="metadata"{poster_attr}>
        <source src="{mp4_path.name}" type="video/mp4">
        Votre navigateur ne peut pas lire cette vidéo.
      </video>
      <div class="meta">
        Fichier MP4 : <strong>{mp4_path.name}</strong><br>
        Ouvrez ce fichier directement dans votre navigateur (double-clic ou glisser-déposer).
      </div>
    </div>
  </div>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    print(f"[HTML] Généré -> {html_path.name}")

def process_one(input_path: Path):
    if not input_path.exists():
        print(f"[SKIP] Introuvable: {input_path}")
        return
    if input_path.is_dir():
        flvs = sorted([Path(p) for ext in ("*.flv","*.FLV") for p in glob.glob(str(input_path / ext))])
        if not flvs:
            print(f"[INFO] Aucun .flv trouvé dans: {input_path}")
            return
        for flv in flvs:
            mp4 = convert_flv_to_mp4(flv)
            poster = make_poster(mp4)
            write_html(mp4, poster)
    else:
        if input_path.suffix.lower() != ".flv":
            print(f"[WARN] {input_path.name} n'est pas un .flv, tentative quand même…")
        mp4 = convert_flv_to_mp4(input_path)
        poster = make_poster(mp4)
        write_html(mp4, poster)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n  - FICHIER: python flv_to_html.py \"C:\\Videos\\clip.flv\"\n  - DOSSIER: python flv_to_html.py \"C:\\Videos\" (traite tous les .flv)")
        sys.exit(0)

    for arg in sys.argv[1:]:
        process_one(Path(arg))
