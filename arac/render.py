#!/usr/bin/env python3
"""sayilar/*.json dosyalarından gazete sayfalarını üretir.

Çıktı (repo kökü):
  index.html          en son sayı
  sayi/<tarih>.html   her sayı
  arsiv.html          bütün sayıların listesi
Bağımlılık yok; yalnız Python 3 standart kütüphanesi.
"""
from __future__ import annotations
import json
import sys
from datetime import date
from html import escape
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
SAYILAR = KOK / "sayilar"
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
KANAL = "https://www.youtube.com/@cihatecicek"


def tirnak(metin: str) -> str:
    """Düz çift tırnakları sırayla “ ” yapar."""
    parcalar = str(metin).split('"')
    out = parcalar[0]
    for i, p in enumerate(parcalar[1:]):
        out += ("“" if i % 2 == 0 else "”") + p
    return out


def e(metin) -> str:
    return escape(str(metin), quote=True)


def yaz(metin) -> str:
    """Okunacak metin: tırnakları düzelt, sonra kaçır."""
    return e(tirnak(metin))


def uzun_tarih(iso: str) -> str:
    g = date.fromisoformat(iso)
    return f"{g.day} {AYLAR[g.month - 1]} {g.year} {GUNLER[g.weekday()]}"


def saniye(zaman: str) -> int:
    toplam = 0
    for parca in zaman.split(":"):
        toplam = toplam * 60 + int(parca)
    return toplam


def video_linki(video: str, zaman: str | None = None) -> str:
    url = f"https://www.youtube.com/watch?v={video}"
    return f"{url}&t={saniye(zaman)}s" if zaman else url


def zaman_etiketi(parca: dict) -> str:
    if not parca.get("video") or not parca.get("zaman"):
        return ""
    return (f'<a class="zaman" href="{e(video_linki(parca["video"], parca["zaman"]))}" '
            f'target="_blank" rel="noopener">▶ Videoda {e(parca["zaman"])}</a>')


def paragraflar(metinler: list[str]) -> str:
    return "".join(f"<p>{yaz(p)}</p>" for p in metinler)


def kunye(s: dict) -> str:
    return f"""
<header class="kunye">
  <div class="kunye-ust">
    <span class="k-sol">Yıl 1 · Sayı {e(s["sayi"])}</span>
    <a class="k-tarih" href="{{kok}}arsiv.html" title="Eski sayılar">{e(uzun_tarih(s["tarih"]))}</a>
    <span class="k-sag">Ücretsizdir · Sponsoru yoktur</span>
  </div>
  <h1 class="ad"><a href="{{kok}}index.html">Günlük Leşber</a></h1>
  <div class="kunye-alt">
    <span>YATİYAD'ın gayriresmî yayın organıdır</span>
    <span class="slogan">Gün altın, gün gümüş</span>
  </div>
</header>"""


def piyasa(s: dict) -> str:
    if not s.get("piyasa"):
        return ""
    hucreler = "".join(
        f'<div class="hucre"><span class="p-ad">{e(p["ad"])}</span>'
        f'<span class="p-deger">{e(p["deger"])}</span>'
        f'<span class="p-degisim {yon(p.get("degisim", ""))}">{e(p.get("degisim", ""))}</span></div>'
        for p in s["piyasa"])
    not_ = f'<p class="p-not">{e(s["piyasa_not"])}</p>' if s.get("piyasa_not") else ""
    return (f'<section class="piyasa" aria-label="Piyasa"><div class="p-baslik">Piyasa</div>{hucreler}</section>'
            f'{not_}')


def yon(degisim: str) -> str:
    return "artis" if degisim.startswith("▲") else "dusus" if degisim.startswith("▼") else ""


def manset(s: dict) -> str:
    m = s["manset"]
    resim = (f'<figure class="foto"><a href="{e(video_linki(m["video"]))}" target="_blank" rel="noopener">'
             f'<img src="https://i.ytimg.com/vi/{e(m["video"])}/hqdefault.jpg" alt="Günün yayınından kare" loading="lazy"></a>'
             f'<figcaption>Günün yayını · Fotoğraf: YouTube</figcaption></figure>')
    return f"""
<section class="manset">
  <div class="ust-baslik">{yaz(m["ust"])}</div>
  <h2 class="manset-baslik">{yaz(m["baslik"])}</h2>
  <p class="manset-spot">{yaz(m["spot"])}</p>
</section>
<div class="on-sayfa">
  <article class="manset-metin">
    {resim}
    <div class="sutunlu">{paragraflar(m["metin"])}</div>
    {zaman_etiketi(m)}
  </article>
  <aside class="kose">
    <div class="kose-etiket">Başkanın Köşesi</div>
    <h3>{yaz(s["kose"]["baslik"])}</h3>
    <div class="kose-yazar">Cihat E. Çiçek <small>YATİYAD Başkanı</small></div>
    {paragraflar(s["kose"]["metin"])}
    <p class="kose-not">Yayındaki sözlerinden derlenmiştir.</p>
    {zaman_etiketi(s["kose"])}
  </aside>
</div>"""


def haberler(s: dict) -> str:
    kartlar = []
    for h in s.get("haberler", []):
        spot = f'<p class="spot">{yaz(h["spot"])}</p>' if h.get("spot") else ""
        kartlar.append(f"""
  <article class="haber">
    <div class="kategori">{e(h["kategori"])}</div>
    <h3>{yaz(h["baslik"])}</h3>
    {spot}
    <div class="govde">{paragraflar(h["metin"])}</div>
    {zaman_etiketi(h)}
  </article>""")
    return f'<div class="haberler-cerceve"><section class="haberler">{"".join(kartlar)}</section></div>'


def alt_bant(s: dict) -> str:
    kisa = "".join(f"<li>{yaz(k['metin'])} {zaman_etiketi(k)}</li>" for k in s.get("kisa", []))
    soz = s.get("soz")
    soz_html = (f'<div class="soz"><div class="kutu-baslik">Günün Sözü</div>'
                f'<blockquote>“{yaz(soz["metin"])}”</blockquote>{zaman_etiketi(soz)}</div>') if soz else ""
    ilan = s.get("ilan")
    ilan_html = (f'<div class="ilan"><div class="ilan-ust">İlan</div><h4>{e(ilan["baslik"])}</h4>'
                 f'<p>{yaz(ilan["metin"])}</p><p class="ilan-not">{yaz(ilan.get("not", ""))}</p>'
                 f'{zaman_etiketi(ilan)}</div>') if ilan else ""
    return f"""
<section class="alt-bant">
  <div class="hava">
    <div class="kutu-baslik">Hava Hadisleri</div>
    <ul>{kisa}</ul>
  </div>
  <div class="yan">{soz_html}{ilan_html}</div>
</section>"""


def gezinti(s: dict) -> str:
    onceki, sonraki = s.get("_onceki"), s.get("_sonraki")
    sol = f'<a href="{{kok}}sayi/{e(onceki)}.html">‹ Önceki sayı</a>' if onceki else "<span></span>"
    sag = f'<a href="{{kok}}sayi/{e(sonraki)}.html">Sonraki sayı ›</a>' if sonraki else "<span></span>"
    return f'<nav class="gezinti">{sol}<a href="{{kok}}arsiv.html">Eski sayılar</a>{sag}</nav>'


def dip(s: dict) -> str:
    videolar = " · ".join(
        f'<a href="{e(video_linki(v["id"]))}" target="_blank" rel="noopener">{e(v["baslik"])}</a> ({e(v.get("sure", ""))})'
        for v in s["videolar"])
    return f"""
<footer class="dip">
  <p><strong>Kaynak:</strong> {videolar}</p>
  <p>Bu gazete <a href="{KANAL}" target="_blank" rel="noopener">Cihat E. Çiçek</a>'in canlı yayınından otomatik derlenmiştir; resmî değildir.
  Yazılanlar yayında söylenenlerdir; altyazıdan çıkarıldığı için rakamlarda hata olabilir, emin olmak için videoya bakın. Yatırım tavsiyesi değildir.</p>
</footer>"""


def sayfa(baslik: str, govde: str, kok: str) -> str:
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{e(baslik)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=PT+Serif:ital,wght@0,400;0,700;1,400&family=Playfair+Display:ital,wght@1,900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{kok}stil.css">
</head>
<body>
<div class="olcek">
<div class="kagit-kap">
<div class="kagit">
{govde.replace("{kok}", kok)}
</div>
</div>
</div>
<nav class="olcek-cubugu" aria-label="Sayfa boyutu">
  <span>Boyut</span>
  <button type="button" data-z="1">%100</button>
  <button type="button" data-z="0.75">%75</button>
  <button type="button" data-z="0.5">%50</button>
</nav>
<script>
(function () {{
  var anahtar = "lesber-olcek";
  var dugmeler = document.querySelectorAll(".olcek-cubugu button");
  function uygula(z) {{
    document.documentElement.style.setProperty("--z", z);
    dugmeler.forEach(function (b) {{ b.setAttribute("aria-pressed", String(b.dataset.z === z)); }});
  }}
  var z = "1";
  try {{ z = localStorage.getItem(anahtar) || "1"; }} catch (e) {{}}
  uygula(z);
  dugmeler.forEach(function (b) {{
    b.addEventListener("click", function () {{
      uygula(b.dataset.z);
      try {{ localStorage.setItem(anahtar, b.dataset.z); }} catch (e) {{}}
    }});
  }});
}})();
</script>
</body>
</html>
"""


def sayi_sayfasi(s: dict, kok: str) -> str:
    govde = kunye(s) + piyasa(s) + manset(s) + haberler(s) + alt_bant(s) + gezinti(s) + dip(s)
    return sayfa(f"Günlük Leşber · {uzun_tarih(s['tarih'])}", govde, kok)


def arsiv_sayfasi(sayilar: list[dict]) -> str:
    satirlar = "".join(
        f'<li><a href="sayi/{e(s["tarih"])}.html"><span class="a-tarih">{e(uzun_tarih(s["tarih"]))}</span>'
        f'<span class="a-manset">{yaz(s["manset"]["baslik"])}</span></a></li>'
        for s in sayilar)
    govde = (kunye(sayilar[0]) +
             f'<section class="arsiv"><h2>Eski Sayılar</h2><ul>{satirlar}</ul></section>')
    return sayfa("Günlük Leşber · Arşiv", govde, "")


def main() -> int:
    sayilar = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(SAYILAR.glob("*.json"))]
    if not sayilar:
        print("sayilar/ boş", file=sys.stderr)
        return 1
    sayilar.sort(key=lambda s: s["tarih"])
    for no, s in enumerate(sayilar, 1):
        s["sayi"] = no  # sayı numarası tarih sırasından gelir
        s["_onceki"] = sayilar[no - 2]["tarih"] if no > 1 else None
        s["_sonraki"] = sayilar[no]["tarih"] if no < len(sayilar) else None
    sayilar.reverse()
    (KOK / "sayi").mkdir(exist_ok=True)
    for s in sayilar:
        (KOK / "sayi" / f"{s['tarih']}.html").write_text(sayi_sayfasi(s, "../"), encoding="utf-8")
    (KOK / "index.html").write_text(sayi_sayfasi(sayilar[0], ""), encoding="utf-8")
    (KOK / "arsiv.html").write_text(arsiv_sayfasi(sayilar), encoding="utf-8")
    print(f"{len(sayilar)} sayı üretildi; en son: {sayilar[0]['tarih']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
