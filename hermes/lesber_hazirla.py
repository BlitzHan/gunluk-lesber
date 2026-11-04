#!/usr/bin/env python3
"""Hermes cron ön betiği: repodaki hazirla.py'yi çalıştırır, çıktısını ajana verir.
Kurulum: cp hermes/lesber_hazirla.py ~/.hermes/scripts/
"""
import subprocess
import sys

sonuc = subprocess.run([sys.executable, "/root/gunluk-lesber/arac/hazirla.py", *sys.argv[1:]],
                       capture_output=True, text=True, timeout=1500)
sys.stdout.write(sonuc.stdout)
if sonuc.returncode != 0:
    sys.stdout.write("\nDURUM: BETIK_HATASI\n" + sonuc.stderr[-1500:])
