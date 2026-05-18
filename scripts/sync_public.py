"""Salin aset static ke public/ sebelum deploy (opsional, untuk dev lokal)."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static"
DST = ROOT / "public" / "static"

if SRC.exists():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    fav = SRC / "favicon.svg"
    if fav.exists():
        shutil.copy2(fav, ROOT / "public" / "favicon.svg")
    print("Synced static -> public/static")
else:
    print("Folder static/ tidak ada — gunakan public/static langsung.")
