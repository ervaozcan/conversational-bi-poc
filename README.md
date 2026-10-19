# Conversational BI Assistant (PoC)

Doğal dil sorgularını SQL sorgularına ve dinamik iş zekası grafiklerine dönüştüren, LLM destekli Konuşmalı BI (İş Zekası) asistanı.

Bu proje; kullanıcıların teknik SQL bilgisine ihtiyaç duymadan veri setleriyle sohbet etmelerini, anlık analitik sorgular çalıştırmalarını ve otomatik görselleştirmeler (Bar, Line, Pie) üretmelerini sağlar.

---

## Özellikler

- **Doğal Dil ile Analiz:** Soruları analiz ederek otomatik ANSI SQL sorguları üretir.
- **Dinamik Görselleştirme:** Sorgu sonucuna en uygun grafik türünü (Bar, Çizgi, Pasta) belirler ve Plotly ile etkileşimli olarak çizer.
- **Esnek Veri Kaynağı:** Varsayılan satış verisinin yanı sıra kullanıcı tarafından yüklenen CSV veya Excel (`.xlsx`, `.xls`) dosyalarını anında analiz eder.
- **Hafıza ve Bağlam:** Önceki soruları ve sonuçları sohbet geçmişinde tutarak bağlamsal analiz imkânı sunar.
- **Genişletilebilir Veri Katmanı:** `BaseDataProvider` mimarisi sayesinde yerel DuckDB motorundan Qlik Cloud REST/Engine API entegrasyonuna hazır yapı.

---

## Proje Mimarisi

```text
conversational-bi-poc/
├── ai/
│   ├── agent.py            # Gemini LLM ve Tool Calling yönetimi
│   └── prompts.py          # Sistem promptları ve şema şablonları
├── data/
│   └── sales_data.csv      # Varsayılan örnek veri seti
├── providers/
│   ├── base.py             # Veri sağlayıcı soyut sınıfı (Interface)
│   ├── local_duckdb.py     # DuckDB tabanlı yerel SQL motoru
│   └── qlik_cloud.py       # Qlik Cloud API entegrasyon katmanı
├── .env                    # API anahtarları (Gizli)
├── app.py                  # Streamlit arayüzü ve dashboard paneli
├── requirements.txt        # Proje bağımlılıkları
└── README.md
