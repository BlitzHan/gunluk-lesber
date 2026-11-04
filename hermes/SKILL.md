---
name: gunluk-lesber
description: "Use when the Günlük Leşber cron runs: turn Cihat E. Çiçek's morning live stream subtitles into that day's 80s-newspaper issue and publish it to GitHub Pages."
version: 1.0.0
metadata:
  hermes:
    tags: [gunluk-lesber, youtube, gazete, github-pages, cron]
---

# Günlük Leşber

Cihat E. Çiçek (YouTube @cihatecicek) her sabah canlı yayın yapıyor. Bu iş, o günün yayınını
altyazısından okuyup 80'ler gazetesi gibi bir sayfaya döker ve
https://blitzhan.github.io/gunluk-lesber/ adresinde yayınlar.

Repo: `/root/gunluk-lesber` (GitHub: BlitzHan/gunluk-lesber). Tasarım sabit; sen yalnız
`sayilar/<tarih>.json` dosyasını yazarsın, sayfayı betik üretir.

## Adımlar

1. İstemin başındaki betik çıktısının ilk satırına bak (`DURUM: ...`):
   - `VIDEO_YOK`, `ZATEN_YAYINLANDI`, `ALTYAZI_HAZIR_DEGIL` → yalnızca `[SILENT]` yaz, başka hiçbir şey yapma.
   - `SON_DENEME_BASARISIZ` → tek satır yaz: "Günlük Leşber: bugünün yayınının altyazısı gelmedi, sayı çıkmadı." ve bitir.
   - `HAZIR` → devam et.
2. Önce örnek sayıyı oku: `/root/gunluk-lesber/sayilar/2026-11-04.json`. Tonu, uzunluğu, alıntı sıklığını ondan al
   (içeriğini kopyalama). Sonra altyazıyı baştan sona oku. Konuları çıkar, her konunun başladığı `[dk:sn]` işaretini not et.
3. `YAZILACAK DOSYA` yoluna aşağıdaki biçimde JSON yaz (dosya yazma aracıyla).
4. Terminalde çalıştır: `python3 /root/gunluk-lesber/arac/yayinla.py <TARIH>`
   - `DENETİM GEÇMEDİ` derse listelenen her hatayı düzelt: rakamı altyazıdaki haline getir ya da cümleden çıkar;
     bulunamayan alıntıyı altyazıdaki sözlere çevir ya da tırnağı kaldırıp aktarım cümlesi yap. Sonra tekrar çalıştır.
   - En fazla 3 deneme. Hâlâ geçmiyorsa hatalı haberi ya da maddeyi tamamen sil ve tekrar dene.
   - `YAYINDA` görünce bitti.
5. Son cevabın Telegram'a gider. Biçim:

```
📰 Günlük Leşber · <gün ay yıl>
<MANŞET>
• <haber başlığı>
• <haber başlığı>
• <haber başlığı>
https://blitzhan.github.io/gunluk-lesber/sayi/<TARIH>.html
```

Yayınlanamadıysa ilk satıra `[CRON_FAILURE]` koy ve kısa sebebi yaz.

## Yazı kuralları (en önemlisi)

- **Tek kaynak altyazı.** Altyazıda olmayan hiçbir bilgi, rakam, isim, tarih ya da yorum ekleme. Kendi bilgini katma,
  "uzmanlar diyor ki" gibi şeyler yazma. Yorum varsa Çiçek'in yorumudur ve ona atfedilir.
- **Rakamlar:** Otomatik altyazı rakamları bozabilir. Bir rakam çelişkiliyse ya da anlamsızsa video başlığındakini kullan;
  başlıkta da yoksa o rakamı yazma. Tahmin etme, yuvarlayıp uydurma.
- **Tırnak içi = söylediği söz.** Dolgu sesleri ("eee", "yani", tekrarlar) atılabilir, kelime değiştirilmez, eklenmez.
  Kendi özetini asla tırnak içine koyma. Başlıkta tırnak kullanacaksan içindeki söz altyazıda geçmeli.
- **Söylenti ve iddia** ("söyleniyor", "Twitter'da gördüm") → "Çiçek'in aktardığı iddiaya göre ..." diye yaz.
- **Bariz altyazı hataları** yalnız özel isimlerde düzeltilebilir (ör. "tunik" → TÜİK, "SFK" → SPK). Emin değilsen o ismi kullanma.
- **Üslup onun üslubu:** Başlıklar kısa ve çarpıcı, onun deyimleriyle ("gidirik oldu", "leşber", "hava hadisleri").
  Haber metni sade gazete Türkçesi, araya onun sözleri tırnakla girer. Kendini anlatma, okura seslenme.
- **Canlı yaz, tekrar etme:** "Çiçek'in aktardığına göre" kalıbını bir haberde en fazla bir kez kullan.
  Her haberde ve manşette en az bir doğrudan alıntı (tırnak içinde onun sözü) olsun; tadı alıntılardan gelir.
- **Başlıklar** cümle düzeninde yazılır ("Altın 4.000 dolara dayandı"), her kelime büyük harfle başlamaz.
- **Alan değerine etiket yazma:** `ust` alanına "Sürmanşet:" gibi bir şey ekleme, yalnız metni yaz.
- **Rakamlara birim yaz:** "50,74 dolar", "6.400 lira". Birimini bilmediğin rakamı yazma.
- **Köşe** en az 3 paragraf ve 150 kelime: o günkü kişisel anlatısından (hedefleri, alışkanlıkları, anıları, kedileri),
  onun ağzından. Yayında kişisel bir şey yoksa en uzun kendi yorum bölümünü birinci şahıs derle.
- **Yatırım tavsiyesi verme.** Altın, fon, borsa görüşleri "Çiçek'e göre" diye aktarılır.
- Kişilere ya da gruplara yönelik etnik, dini laf sokmalarını alma; siyasi eleştiri kalabilir.
- Yayın içi küçük anlar (kıyafeti, masadaki eşya) haber yapılmaz; istersen "kisa"ya bir madde olarak girer.

## JSON biçimi

Bütün metinler Türkçe. `zaman` o konunun videoda başladığı an (`dk:sn` ya da `sa:dk:sn`), altyazıdaki işaretlerden.
`video` o konunun geçtiği videonun id'si. Videolar alanını betik çıktısındaki `VIDEOLAR` satırından aynen kopyala.

```json
{
  "tarih": "2026-11-04",
  "sayi": 1,
  "videolar": [{"id": "...", "baslik": "...", "sure": "37:20"}],
  "manset": {
    "video": "...", "zaman": "02:06",
    "ust": "3-6 kelimelik üst başlık",
    "baslik": "2-6 kelimelik manşet (sayfada büyük harfe çevrilir)",
    "spot": "Bir cümle, içinde onun bir sözü tırnakla olabilir.",
    "metin": ["3-4 paragraf, her biri en çok 70 kelime"]
  },
  "kose": {
    "video": "...", "zaman": "00:02",
    "baslik": "Köşe başlığı",
    "metin": ["3-4 paragraf, BİRİNCİ TEKİL ŞAHIS, yalnızca onun yayındaki kendi cümleleri (dolgu atılmış). Kişisel konu seç: hedefleri, alışkanlıkları, anıları."]
  },
  "haberler": [
    {"video": "...", "zaman": "13:30", "kategori": "Altın · Gümüş",
     "baslik": "Başlık", "spot": "Tek cümle", "metin": ["2 paragraf, her biri en çok 70 kelime"]}
  ],
  "kisa": [{"video": "...", "zaman": "21:47", "metin": "Bir-iki cümlelik kısa haber"}],
  "soz": {"video": "...", "zaman": "11:56", "metin": "Günün en akılda kalan sözü, birebir"},
  "ilan": {"video": "...", "zaman": "15:04", "baslik": "...", "metin": "...", "not": "..."}
}
```

- `haberler`: 5-8 haber, en önemlisi başta (ilk haber geniş basılır). Manşetteki konuyu tekrar etme.
- `kisa` ("Hava Hadisleri" kutusu): 4-8 madde, haber olmaya yetmeyen konular.
- `piyasa` alanını **yazma**: bant (ons/gram altın, ons/gram gümüş, dolar, Brent, Bitcoin) yayınlarken betik tarafından
  gerçek fiyatlarla doldurulur. Yayında okuduğu fiyatlar haber metninde geçebilir.
- `ilan`: Yalnız kendisi bir şey tanıtırsa (ör. kendi kitabı). Yoksa alanı hiç yazma.
- Kategori örnekleri: Altın · Gümüş, Borsa, Para piyasası, Enflasyon, Dünya, Siyaset, Lüzumsuz işler ekonomisi.

## Elle çalıştırma

```
python3 /root/gunluk-lesber/arac/hazirla.py --tarih 2026-11-04   # altyazıyı çek
python3 /root/gunluk-lesber/arac/yayinla.py 2026-11-04           # denetle, üret, yükle
```
