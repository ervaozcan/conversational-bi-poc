#  Conversational BI Assistant (PoC)

Doğal dil sorgularını SQL sorgularına, dinamik iş zekası grafiklerine ve otomatik analitik içgörülere dönüştüren LLM destekli Konuşmalı BI (İş Zekası) asistanı.

Bu proje; teknik SQL bilgisine ihtiyaç duymadan veri setleriyle doğal dilde sohbet edilmesini, anlık analitik sorgular çalıştırılmasını, otomatik KPI kartları üretilmesini ve sonuçların dışa aktarılmasını sağlar.

---

##  Temel Özellikler

- **Doğal Dil ile SQL & Analiz:** Kullanıcı sorularını ANSI SQL (DuckDB) sorgularına çevirerek veritabanını otomatik sorgular.
- **Dinamik KPI Kartları:** Sorgu sonuçlarından ID ve kod sütunlarını ayrıştırarak ciro, adet ve kayıt sayısı gibi kritik metrikleri otomatik hesaplar.
- **Etkileşimli Görselleştirme:** Veri tipine en uygun grafik türünü (Bar, Çizgi, Pasta) belirleyerek Plotly ile render eder.
- **Veri Dışa Aktarma (Export):** Üretilen grafiklerin arkasındaki filtrelenmiş veriyi tek tıkla **Excel (`.xlsx`)** veya **CSV** formatında indirir.
- **Hızlı Öneri Butonları:** Sık sorulan bölgesel, kategori ve satış odaklı analizleri tek tıkla tetikleyen hazır promptlar sunar.
- **Aksiyon Alınabilir İçgörüler:** Her sorgu sonucunda öne çıkan trendleri, tepe noktalarını ve analizi derinleştirecek takip sorularını listeler.
- **Esnek Veri Yükleme:** Sol menüden CSV veya Excel (`.xlsx`, `.xls`) dosyası yükleyerek anında özel veri setlerini analiz etme imkânı tanır.
- **Hata Toleransı (Resilience):** API kota aşımları ve anlık sunucu yoğunluklarında (`503`, `429`) otomatik bekleme ve yeniden deneme (exponential backoff) uygular.

---

##  Proje Mimarisi

```text
conversational-bi-poc/
├── ai/
│   ├── agent.py            # Gemini LLM istemcisi, Retry mantığı ve Tool Calling
│   └── prompts.py          # Sistem promptları ve analitik içgörü kuralları
├── data/
│   └── sales_data.csv      # Varsayılan satış verisi
├── providers/
│   ├── base.py             # Veri sağlayıcı soyut arayüzü (Interface)
│   ├── local_duckdb.py     # DuckDB tabanlı yerel SQL motoru
│   └── qlik_cloud.py       # Qlik Cloud genişletme arayüzü
├── .env                    # API anahtarları (Git takibi dışı)
├── .gitignore              # Gizli dosyalar ve önbellek filtreleri
├── app.py                  # Streamlit arayüzü, KPI paneli ve indirme butonları
├── requirements.txt        # Python bağımlılıkları
└── README.md