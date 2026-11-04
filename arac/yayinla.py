#!/usr/bin/env python3
"""Sayıyı denetler, sayfaları üretir, GitHub'a yükler.

Kullanım: python3 yayinla.py 2026-11-04
Denetim hatası varsa hiçbir şey yüklenmez; hatalar basılır, çıkış kodu 1.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
SITE = "https://blitzhan.github.io/gunluk-lesber/"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(KOK), *args], capture_output=True, text=True)


def main() -> int:
    if len(sys.argv) != 2:
        print("Kullanım: yayinla.py YYYY-AA-GG")
        return 2
    tarih = sys.argv[1]
    sayi = KOK / "sayilar" / f"{tarih}.json"
    if not sayi.exists():
        print(f"Dosya yok: {sayi}")
        return 1

    git("pull", "-q", "--ff-only")
    piyasa = subprocess.run([sys.executable, str(KOK / "arac" / "piyasa.py"), str(sayi)],
                            capture_output=True, text=True)
    if piyasa.returncode != 0:  # piyasa verisi gelmezse sayı yine çıkar, bant boş kalır
        print("UYARI: piyasa verisi alınamadı: " + piyasa.stderr.strip()[-300:])

    kontrol = subprocess.run([sys.executable, str(KOK / "arac" / "kontrol.py"), str(sayi)],
                             capture_output=True, text=True)
    if kontrol.returncode != 0:
        print("DENETİM GEÇMEDİ, YÜKLENMEDİ.\n" + kontrol.stdout + kontrol.stderr)
        return 1

    render = subprocess.run([sys.executable, str(KOK / "arac" / "render.py")], capture_output=True, text=True)
    if render.returncode != 0:
        print("Sayfa üretilemedi:\n" + render.stdout + render.stderr)
        return 1

    git("add", "sayilar", "sayi", "index.html", "arsiv.html")
    if not git("status", "--porcelain").stdout.strip():
        print(f"Değişiklik yok, zaten yayında: {SITE}")
        return 0
    no = json.loads(sayi.read_text(encoding="utf-8")).get("sayi", "?")
    git("-c", "user.name=Hermes", "-c", "user.email=hermes@localhost",
        "commit", "-q", "-m", f"Sayı {no}: {tarih}")
    git("pull", "-q", "--rebase")
    itme = git("push", "-q", "origin", "main")
    if itme.returncode != 0:
        print("GitHub'a yüklenemedi:\n" + itme.stderr)
        return 1
    print(f"YAYINDA: {SITE}sayi/{tarih}.html (sayfa 1-2 dakikada güncellenir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
