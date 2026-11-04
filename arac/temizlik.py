#!/usr/bin/env python3
"""VDS'in şişmemesi için haftalık temizlik (Hermes no-agent cron'u çalıştırır).

- _ham/ içindeki altyazı dosyaları: 14 günden eskiler silinir
- Bu işin Hermes cron çıktıları (içinde tam altyazı var): 30 günden eskiler silinir
- Git deposu sıkıştırılır (git gc), yt-dlp önbelleği boşaltılır
- Disk %85'i geçerse uyarı basar (Telegram'a gider); her şey yolundaysa hiçbir şey basmaz
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HAM = KOK / "_ham"
HERMES = Path.home() / ".hermes"
HAM_GUN = 14
CIKTI_GUN = 30
DISK_ESIK = 85


def eskileri_sil(klasor: Path, gun: int) -> tuple[int, int]:
    if not klasor.exists():
        return 0, 0
    sinir = time.time() - gun * 86400
    adet = bayt = 0
    for f in klasor.iterdir():
        if f.is_file() and f.stat().st_mtime < sinir:
            bayt += f.stat().st_size
            f.unlink()
            adet += 1
    return adet, bayt


def is_klasorleri() -> list[Path]:
    """Adında 'Leşber' geçen cron işlerinin çıktı klasörleri."""
    try:
        isler = json.loads((HERMES / "cron" / "jobs.json").read_text(encoding="utf-8"))["jobs"]
    except (OSError, KeyError, ValueError):
        return []
    return [HERMES / "cron" / "output" / j["id"] for j in isler if "Leşber" in (j.get("name") or "")]


def main() -> None:
    eskileri_sil(HAM, HAM_GUN)
    for klasor in is_klasorleri():
        eskileri_sil(klasor, CIKTI_GUN)
    subprocess.run(["git", "-C", str(KOK), "gc", "--auto", "--quiet"], capture_output=True)
    subprocess.run(["yt-dlp", "--rm-cache-dir"], capture_output=True)

    disk = shutil.disk_usage("/")
    oran = disk.used / disk.total * 100
    if oran >= DISK_ESIK:
        boyut = subprocess.run(["du", "-xsh", "/root/.hermes", "/root/gunluk-lesber", "/var/log", "/tmp"],
                               capture_output=True, text=True).stdout
        print(f"⚠️ VDS diski %{oran:.0f} dolu ({disk.free / 1e9:.1f} GB boş kaldı).\n"
              f"Büyük klasörler:\n{boyut}")


if __name__ == "__main__":
    main()
