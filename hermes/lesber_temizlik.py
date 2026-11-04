#!/usr/bin/env python3
"""Hermes no-agent cron'u: Günlük Leşber haftalık temizliği.
Kurulum: cp hermes/lesber_temizlik.py ~/.hermes/scripts/
Sorun yoksa hiçbir şey basmaz (mesaj gitmez); disk %85'i geçerse uyarı basar.
"""
import subprocess
import sys

s = subprocess.run([sys.executable, "/root/gunluk-lesber/arac/temizlik.py"], capture_output=True, text=True, timeout=900)
sys.stdout.write(s.stdout)
if s.returncode != 0:
    sys.stdout.write("Günlük Leşber temizliği hata verdi:\n" + s.stderr[-800:])
