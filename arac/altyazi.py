#!/usr/bin/env python3
"""YouTube otomatik altyazısını (VTT) zaman damgalı düz metne çevirir.

Kullanım: python3 altyazi.py video.tr.vtt > video.txt
Çıktı: her ~30 saniyede bir [dk:sn] işaretli paragraflar.
"""
import re
import sys

ARALIK = 30  # saniye


def saniye(ts: str) -> int:
    s, d, n = ts.split(":")
    return int(s) * 3600 + int(d) * 60 + int(n)


def etiket(sn: int) -> str:
    s, kalan = divmod(sn, 3600)
    d, n = divmod(kalan, 60)
    return f"{s}:{d:02d}:{n:02d}" if s else f"{d:02d}:{n:02d}"


def temizle(yol: str) -> str:
    satirlar = open(yol, encoding="utf-8").read().splitlines()
    parcalar, son, an = [], "", 0
    for satir in satirlar:
        m = re.match(r"(\d\d:\d\d:\d\d)\.\d+ -->", satir)
        if m:
            an = saniye(m.group(1))
            continue
        if not satir.strip() or satir.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        metin = re.sub(r"<[^>]+>", "", satir).strip()
        if metin and metin != son:
            parcalar.append((an, metin))
            son = metin

    cikti, blok, blok_basi = [], [], None
    for an, metin in parcalar:
        if blok_basi is None:
            blok_basi = an
        if an - blok_basi >= ARALIK and blok:
            cikti.append(f"[{etiket(blok_basi)}] " + " ".join(blok))
            blok, blok_basi = [], an
        blok.append(metin)
    if blok:
        cikti.append(f"[{etiket(blok_basi)}] " + " ".join(blok))
    return "\n".join(cikti)


if __name__ == "__main__":
    print(temizle(sys.argv[1]))
