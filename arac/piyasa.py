#!/usr/bin/env python3
"""Piyasa bandını gerçek fiyatlarla doldurur (Yahoo Finance, anahtarsız).

Kullanım: python3 piyasa.py sayilar/2026-11-04.json
Sayının tarihi bugünse anlık fiyat, geçmiş bir günse o günün kapanışı yazılır.
Gram altın ve gram gümüş, ons fiyatı ile dolar kurundan hesaplanır.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Istanbul")
ONS_GRAM = 31.1035
SEMBOLLER = {"altin": "GC=F", "gumus": "SI=F", "brent": "BZ=F", "dolar": "USDTRY=X", "btc": "BTC-USD"}


def kapanislar(sembol: str, tarih: date) -> tuple[float, float | None]:
    """O tarihteki (ya da öncesindeki son) kapanış ve bir önceki kapanış."""
    bas = int(datetime.combine(tarih - timedelta(days=10), datetime.min.time(), timezone.utc).timestamp())
    son = int(datetime.combine(tarih + timedelta(days=1), datetime.min.time(), timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sembol}"
           f"?interval=1d&period1={bas}&period2={son}")
    istek = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    veri = json.load(urllib.request.urlopen(istek, timeout=30))["chart"]["result"][0]
    ofset = veri["meta"].get("gmtoffset", 0)
    gunler = []
    for ts, kapanis in zip(veri.get("timestamp", []), veri["indicators"]["quote"][0]["close"]):
        if kapanis is None:
            continue
        gun = datetime.fromtimestamp(ts + ofset, timezone.utc).date()
        if gun <= tarih:
            gunler.append((gun, kapanis))
    if not gunler:
        raise ValueError(f"{sembol} için {tarih} verisi yok")
    onceki = gunler[-2][1] if len(gunler) > 1 else None
    return gunler[-1][1], onceki


def tr_sayi(deger: float, ondalik: int) -> str:
    metin = f"{deger:,.{ondalik}f}"
    return metin.replace(",", "X").replace(".", ",").replace("X", ".")


def degisim(simdi: float, once: float | None) -> str:
    if not once:
        return ""
    oran = (simdi - once) / once * 100
    isaret = "▲" if oran > 0.05 else "▼" if oran < -0.05 else "•"
    return f"{isaret} %{tr_sayi(abs(oran), 1)}"


def piyasa(tarih: date) -> tuple[list[dict], str]:
    f = {ad: kapanislar(s, tarih) for ad, s in SEMBOLLER.items()}
    kur, kur_once = f["dolar"]
    altin, altin_once = f["altin"]
    gumus, gumus_once = f["gumus"]
    gram = lambda ons, k: ons * k / ONS_GRAM  # noqa: E731
    gram_altin_once = gram(altin_once, kur_once) if altin_once and kur_once else None
    gram_gumus_once = gram(gumus_once, kur_once) if gumus_once and kur_once else None
    satirlar = [
        ("Ons altın", f"{tr_sayi(altin, 0)} $", degisim(altin, altin_once)),
        ("Gram altın", f"{tr_sayi(gram(altin, kur), 0)} TL", degisim(gram(altin, kur), gram_altin_once)),
        ("Ons gümüş", f"{tr_sayi(gumus, 2)} $", degisim(gumus, gumus_once)),
        ("Gram gümüş", f"{tr_sayi(gram(gumus, kur), 2)} TL", degisim(gram(gumus, kur), gram_gumus_once)),
        ("Dolar", f"{tr_sayi(kur, 2)} TL", degisim(kur, kur_once)),
        ("Brent petrol", f"{tr_sayi(f['brent'][0], 2)} $", degisim(*f["brent"])),
        ("Bitcoin", f"{tr_sayi(f['btc'][0], 0)} $", degisim(*f["btc"])),
    ]
    simdi = datetime.now(TZ)
    zaman = f"saat {simdi:%H:%M}" if tarih >= simdi.date() else "günün kapanışı"
    not_ = f"Yahoo Finance, {zaman}. Gram fiyatlar ons ve dolar kurundan hesaplanır; değişim önceki güne göre."
    return [{"ad": a, "deger": d, "degisim": c} for a, d, c in satirlar], not_


def guncelle(yol: Path) -> None:
    sayi = json.loads(yol.read_text(encoding="utf-8"))
    sayi["piyasa"], sayi["piyasa_not"] = piyasa(date.fromisoformat(sayi["tarih"]))
    yol.write_text(json.dumps(sayi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        guncelle(Path(p))
        print(f"Piyasa güncellendi: {p}")
