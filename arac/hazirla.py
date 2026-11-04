#!/usr/bin/env python3
"""Günün videolarını bulur, altyazılarını çeker, ajana hazır metin basar.

Hermes cron'unun ön betiği olarak çalışır; çıktısı ajanın istemine eklenir.
Kullanım: python3 hazirla.py [--tarih YYYY-AA-GG]

İlk satır her zaman "DURUM: <KOD>" olur:
  HAZIR                  altyazılar hazır, ajan sayıyı yazsın
  VIDEO_YOK              bugün yayın yok
  ZATEN_YAYINLANDI       bugünün sayısı bütün videolarla yayında
  ALTYAZI_HAZIR_DEGIL    yayın sürüyor ya da altyazı henüz düşmedi
  SON_DENEME_BASARISIZ   günün son denemesinde de altyazı yok
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from altyazi import temizle  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
HAM = KOK / "_ham"
SAYILAR = KOK / "sayilar"
KANAL_ID = "UCHExW8VqaE0a3W0kwSe_BXg"
RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={KANAL_ID}"
TZ = ZoneInfo("Europe/Istanbul")
SON_DENEME_SAATI = 15
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def calistir(komut: list[str], zaman_asimi: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(komut, capture_output=True, text=True, timeout=zaman_asimi)


def bugunun_videolari(tarih: str) -> list[dict]:
    istek = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0 (gunluk-lesber)"})
    xml = urllib.request.urlopen(istek, timeout=30).read()
    kok = ET.fromstring(xml)
    videolar = []
    for giris in kok.findall("a:entry", NS):
        yayin = datetime.fromisoformat(giris.findtext("a:published", namespaces=NS))
        if yayin.astimezone(TZ).date().isoformat() != tarih:
            continue
        videolar.append({
            "id": giris.findtext("yt:videoId", namespaces=NS),
            "baslik": giris.findtext("a:title", namespaces=NS).strip(),
            "yayin": yayin.astimezone(TZ).strftime("%H:%M"),
        })
    return sorted(videolar, key=lambda v: v["yayin"])


def sure_yaz(saniye: float | None) -> str:
    if not saniye:
        return ""
    s = int(saniye)
    sa, kalan = divmod(s, 3600)
    dk, sn = divmod(kalan, 60)
    return f"{sa}:{dk:02d}:{sn:02d}" if sa else f"{dk:02d}:{sn:02d}"


def altyazi_cek(video: dict) -> dict:
    """Altyazıyı indirir; video sözlüğüne durum, süre ve metin yolunu ekler."""
    HAM.mkdir(exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video['id']}"
    sonuc = calistir([
        "yt-dlp", "--skip-download", "--no-simulate", "--no-warnings",
        "--write-auto-subs", "--write-subs", "--sub-langs", "tr", "--sub-format", "vtt",
        "--print", "%(live_status)s|%(duration)s",
        "-o", str(HAM / "%(id)s.%(ext)s"), url,
    ])
    satir = (sonuc.stdout.strip().splitlines() or ["|"])[0]
    canli, _, sure = satir.partition("|")
    video["canli"] = canli
    video["sure"] = sure_yaz(float(sure)) if sure not in ("", "NA", "None") else ""
    vtt = HAM / f"{video['id']}.tr.vtt"
    if canli in ("is_live", "is_upcoming") or not vtt.exists():
        video["hazir"] = False
        video["hata"] = sonuc.stderr.strip()[-300:]
        return video
    metin = HAM / f"{video['id']}.txt"
    metin.write_text(temizle(str(vtt)), encoding="utf-8")
    video["hazir"] = True
    video["metin"] = str(metin)
    return video


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tarih", default=datetime.now(TZ).date().isoformat())
    tarih = ap.parse_args().tarih
    simdi = datetime.now(TZ)

    calistir(["git", "-C", str(KOK), "pull", "-q", "--ff-only"], 120)
    calistir(["yt-dlp", "-U"], 180)  # YouTube değişikliklerine karşı her gün güncelle

    videolar = bugunun_videolari(tarih)
    if not videolar:
        print(f"DURUM: VIDEO_YOK\nTARIH: {tarih}")
        return 0

    sayi_yolu = SAYILAR / f"{tarih}.json"
    yapilan = set()
    if sayi_yolu.exists():
        yapilan = {v["id"] for v in json.loads(sayi_yolu.read_text(encoding="utf-8")).get("videolar", [])}
    if all(v["id"] in yapilan for v in videolar):
        print(f"DURUM: ZATEN_YAYINLANDI\nTARIH: {tarih}")
        return 0

    videolar = [altyazi_cek(v) for v in videolar]
    hazirlar = [v for v in videolar if v["hazir"]]
    if not hazirlar:
        kod = "SON_DENEME_BASARISIZ" if simdi.hour >= SON_DENEME_SAATI else "ALTYAZI_HAZIR_DEGIL"
        print(f"DURUM: {kod}\nTARIH: {tarih}")
        for v in videolar:
            print(f"- {v['id']} | {v['baslik']} | canlı durumu: {v['canli']} | {v.get('hata', '')}")
        return 0

    onceki = [p for p in SAYILAR.glob("*.json") if p.stem < tarih]
    sayi_no = len(onceki) + 1
    meta = {"tarih": tarih, "sayi": sayi_no,
            "videolar": [{k: v[k] for k in ("id", "baslik", "sure")} for v in hazirlar]}
    (HAM / f"{tarih}-meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("DURUM: HAZIR")
    print(f"TARIH: {tarih}")
    print(f"SAYI: {sayi_no}")
    print(f"YAZILACAK DOSYA: {sayi_yolu}")
    print("VIDEOLAR (JSON'daki \"videolar\" alanına aynen koy):")
    print(json.dumps(meta["videolar"], ensure_ascii=False))
    bekleyen = [v for v in videolar if not v["hazir"]]
    if bekleyen:
        print("NOT: Şu videoların altyazısı henüz yok, bu sayıya girmeyecek: "
              + ", ".join(v["baslik"] for v in bekleyen))
    for v in hazirlar:
        print(f"\n===== ALTYAZI · video {v['id']} · \"{v['baslik']}\" · süre {v['sure']} =====")
        print("Satır başındaki [dk:sn] o paragrafın videodaki başlangıç anıdır.\n")
        print(Path(v["metin"]).read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
