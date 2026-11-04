#!/usr/bin/env python3
"""Sayı JSON'unu altyazıya karşı denetler: uydurma rakam ve alıntı yakalar.

Kullanım: python3 kontrol.py sayilar/2026-11-04.json
Altyazı metinleri _ham/<video_id>.txt, süreler _ham/<tarih>-meta.json'dan okunur.
Hata yoksa "TAMAM" basar ve 0 döner; varsa her hatayı bir satırda basar ve 1 döner.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HAM = KOK / "_ham"
ZORUNLU = ["tarih", "sayi", "videolar", "manset", "kose", "haberler", "kisa", "soz"]
SAYI_RE = re.compile(r"\d[\d.,]*\d|\d")
TIRNAK_RE = re.compile(r"[\"“”](.+?)[\"“”]")


def kucult(metin: str) -> str:
    return metin.replace("I", "ı").replace("İ", "i").lower()


def kokler(metin: str) -> list[str]:
    """Kelimeleri ilk 5 harfe indirir; Türkçe ekler eşleşmeyi bozmasın."""
    return [k[:5] for k in re.findall(r"[a-zçğıöşü0-9]+", kucult(metin))]


def sayi_normal(t: str) -> str:
    return re.sub(r"[.,]", "", t).rstrip("0") or "0"


def saniye(zaman: str) -> int:
    toplam = 0
    for p in zaman.split(":"):
        toplam = toplam * 60 + int(p)
    return toplam


def metinleri_gez(dugum, yol=""):
    """JSON içindeki okunacak metinleri (yol, metin) olarak verir."""
    atla = {"id", "video", "zaman", "tarih", "sure", "videolar", "piyasa", "piyasa_not"}
    if isinstance(dugum, dict):
        for k, v in dugum.items():
            if k not in atla:
                yield from metinleri_gez(v, f"{yol}.{k}" if yol else k)
    elif isinstance(dugum, list):
        for i, v in enumerate(dugum):
            yield from metinleri_gez(v, f"{yol}[{i}]")
    elif isinstance(dugum, str):
        yield yol, dugum


def zamanli_parcalari_gez(dugum, yol=""):
    if isinstance(dugum, dict):
        if "zaman" in dugum or "video" in dugum:
            yield yol, dugum
        for k, v in dugum.items():
            if isinstance(v, (dict, list)) and k != "videolar":
                yield from zamanli_parcalari_gez(v, f"{yol}.{k}" if yol else k)
    elif isinstance(dugum, list):
        for i, v in enumerate(dugum):
            yield from zamanli_parcalari_gez(v, f"{yol}[{i}]")


def alinti_var_mi(alinti: str, kelimeler: list[str], esik: float = 0.7) -> bool:
    aranan = kokler(alinti)
    if len(aranan) < 3:
        return True
    pencere = len(aranan) * 2 + 5
    hedef = set(aranan)
    for i in range(0, max(1, len(kelimeler) - len(aranan) + 1)):
        parca = set(kelimeler[i:i + pencere])
        if len(hedef & parca) / len(hedef) >= esik:
            return True
    return False


def denetle(yol: Path) -> list[str]:
    hatalar: list[str] = []
    try:
        s = json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError as h:
        return [f"JSON bozuk: {h}"]

    for alan in ZORUNLU:
        if alan not in s:
            hatalar.append(f"Eksik alan: {alan}")
    if hatalar:
        return hatalar
    if not isinstance(s["haberler"], list) or not (3 <= len(s["haberler"]) <= 10):
        hatalar.append("haberler 3 ile 10 arasında olmalı")

    meta_yolu = HAM / f"{s['tarih']}-meta.json"
    sureler = {}
    if meta_yolu.exists():
        sureler = {v["id"]: v.get("sure", "") for v in json.loads(meta_yolu.read_text(encoding="utf-8"))["videolar"]}

    metin, basliklar = "", ""
    for v in s["videolar"]:
        txt = HAM / f"{v['id']}.txt"
        if not txt.exists():
            hatalar.append(f"Altyazı yok: {txt}")
            continue
        metin += "\n" + txt.read_text(encoding="utf-8")
        basliklar += " " + v.get("baslik", "")
        sureler.setdefault(v["id"], v.get("sure", ""))
    if hatalar:
        return hatalar

    govde = re.sub(r"\[\d+:\d\d(:\d\d)?\]", " ", metin)  # zaman işaretleri sayı sayılmasın
    kaynak_sayilar = set()
    kaynak_gruplar = set()
    for t in SAYI_RE.findall(govde + " " + basliklar):
        kaynak_sayilar.add(sayi_normal(t))
        kaynak_gruplar.update(g for g in re.split(r"[.,]", t) if g)
    kaynak_kelimeler = kokler(govde)
    tarih_parcalari = set(s["tarih"].split("-")) | {str(int(p)) for p in s["tarih"].split("-")}

    for alan, deger in metinleri_gez(s):
        for t in SAYI_RE.findall(deger):
            if len(re.sub(r"\D", "", t)) < 2 or t in tarih_parcalari or alan.startswith("sayi"):
                continue
            gruplar = [g for g in re.split(r"[.,]", t) if g]
            if sayi_normal(t) in kaynak_sayilar or all(g in kaynak_gruplar for g in gruplar):
                continue
            hatalar.append(f"RAKAM altyazıda yok: '{t}' ({alan})")
        if alan.startswith("kose"):
            continue  # köşe zaten onun cümleleri; tırnak denetimi haber alıntıları için
        for alinti in TIRNAK_RE.findall(deger):
            if not alinti_var_mi(alinti, kaynak_kelimeler):
                hatalar.append(f"ALINTI altyazıda bulunamadı: \"{alinti}\" ({alan})")

    video_idleri = {v["id"] for v in s["videolar"]}
    for alan, parca in zamanli_parcalari_gez(s):
        vid, zaman = parca.get("video") or s["videolar"][0]["id"], parca.get("zaman")
        if vid not in video_idleri:
            hatalar.append(f"Bilinmeyen video: {vid} ({alan})")
            continue
        if not zaman or not re.fullmatch(r"\d+:\d\d(:\d\d)?", zaman):
            hatalar.append(f"Zaman biçimi bozuk: {zaman!r} ({alan})")
            continue
        sure = sureler.get(vid)
        if sure and saniye(zaman) > saniye(sure):
            hatalar.append(f"Zaman video süresini aşıyor: {zaman} > {sure} ({alan})")
    return hatalar


def main() -> int:
    hatalar = denetle(Path(sys.argv[1]))
    if not hatalar:
        print("TAMAM")
        return 0
    print(f"{len(hatalar)} HATA:")
    for h in hatalar:
        print(f"- {h}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
