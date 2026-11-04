# Günlük Leşber

Cihat E. Çiçek'in sabah canlı yayınlarından otomatik derlenen, 80'ler gazetesi görünümlü günlük sayfa.
Resmî değildir; her haber videodaki dakikasına bağlanır. Kaynak kanal: https://www.youtube.com/@cihatecicek

- `sayilar/<tarih>.json` — o günün sayısı (içerik yalnız altyazıdan)
- `arac/altyazi.py` — YouTube altyazısını zaman damgalı metne çevirir
- `arac/render.py` — JSON'dan `index.html`, `sayi/<tarih>.html`, `arsiv.html` üretir
- Her sabah Hermes Agent (VDS) üretir ve buraya yükler.
