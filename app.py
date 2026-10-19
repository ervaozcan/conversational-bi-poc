import os
import io
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from providers.local_duckdb import LocalDuckDBProvider
from ai.agent import BIAgent

load_dotenv()

st.set_page_config(page_title="Conversational BI Dashboard", layout="wide")
st.title("📊 Conversational BI Assistant")

# --- SOL MENÜ: DOSYA YÜKLEME VE YÖNETİM ---
st.sidebar.header("📁 Veri Kaynağı")
uploaded_file = st.sidebar.file_uploader(
    "CSV veya Excel dosyası yükleyin", 
    type=["csv", "xlsx", "xls"]
)

active_data_path = "data/sales_data.csv"

if uploaded_file is not None:
    if st.session_state.get("last_uploaded_filename") != uploaded_file.name:
        os.makedirs("data", exist_ok=True)
        temp_path = "data/uploaded_temp.csv"
        
        if uploaded_file.name.endswith(".csv"):
            df_uploaded = pd.read_csv(uploaded_file)
        else:
            df_uploaded = pd.read_excel(uploaded_file)
            
        df_uploaded.to_csv(temp_path, index=False)
        st.session_state.last_uploaded_filename = uploaded_file.name
        st.session_state.uploaded_temp_path = temp_path
        st.sidebar.success(f"✅ Yüklendi: {uploaded_file.name}")
    
    active_data_path = st.session_state.get("uploaded_temp_path", "data/sales_data.csv")

# --- YENİ: GEÇMİŞİ VE GRAFİKLERİ TEMİZLEME BUTONU ---
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Sohbeti ve Paneli Sıfırla", use_container_width=True):
    st.session_state.messages = []
    st.session_state.charts_history = []
    st.rerun()

# --- VERİ KÜMESİ DEĞİŞTİĞİNDE SİSTEMİ YENİDEN BAŞLATMA ---
if "current_data_path" not in st.session_state or st.session_state.current_data_path != active_data_path:
    st.session_state.current_data_path = active_data_path
    st.session_state.provider = LocalDuckDBProvider(active_data_path)
    st.session_state.agent = BIAgent(st.session_state.provider)
    st.session_state.messages = []
    st.session_state.charts_history = []

# --- ARAYÜZ DÜZENİ ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("💬 Asistan ile Sohbet")
    
    # Sohbet Geçmişi Gösterimi
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- YENİ: HIZLI SORU BUTONLARI ---
    st.markdown("💡 **Örnek Sorular:**")
    prompt_cols = st.columns(3)
    quick_prompt = None
    
    if prompt_cols[0].button("📍 Bölgesel Siparişler", use_container_width=True):
        quick_prompt = "Bölgelere göre sipariş sayılarının dağılımını bar chart olarak göster."
    if prompt_cols[1].button("🏷️ Kategori Ciroları", use_container_width=True):
        quick_prompt = "Ürün kategorilerine göre toplam tutar dağılımını pie chart ile göster."
    if prompt_cols[2].button("🏆 En Çok Satanlar", use_container_width=True):
        quick_prompt = "En çok adet satan ilk 5 ürünü ve satış adetlerini bar chart olarak göster."

    # Kullanıcı girdisi (chat input veya tıklanan hızlı soru)
    typed_input = st.chat_input("Verilerinizle ilgili bir soru sorun...")
    user_input = quick_prompt if quick_prompt else typed_input
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Veri analiz ediliyor..."):
                try:
                    api_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                    response_text, df, chart_config = st.session_state.agent.chat(user_input, api_history)
                    
                    st.write(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    if df is not None and chart_config is not None:
                        st.session_state.charts_history.append({
                            "config": chart_config,
                            "df": df
                        })
                        st.rerun()
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        st.warning("⚠️ Google API dakikalık kullanım limitine ulaşıldı. Lütfen 1 dakika bekleyip sorunuzu tekrar sorun.")
                    else:
                        st.error(f"Sorgu işlenirken bir hata oluştu: {err_msg}")

with right_col:
    st.subheader("📈 Dinamik Dashboard Paneli")

    if st.session_state.charts_history:
        for idx, item in enumerate(st.session_state.charts_history):
            cfg = item["config"]
            df = item["df"]

            st.markdown(f"### {cfg['title']}")
            
            # KPI Kartları
            numeric_cols = [c for c in df.select_dtypes(include='number').columns if not any(x in c.upper() for x in ['ID', 'NO', 'KOD'])]
            kpi_cols = st.columns(3)
            kpi_cols[0].metric("Satır / Kayıt Sayısı", len(df))
            
            if len(numeric_cols) > 0:
                val1 = df[numeric_cols[0]].sum()
                kpi_cols[1].metric(f"Toplam {numeric_cols[0]}", f"{val1:,.2f}")
            if len(numeric_cols) > 1:
                val2 = df[numeric_cols[1]].sum()
                kpi_cols[2].metric(f"Toplam {numeric_cols[2]}", f"{val2:,.2f}")
            
            # Grafik
            if cfg["chart_type"] == "bar":
                fig = px.bar(df, x=cfg["x_column"], y=cfg["y_column"])
            elif cfg["chart_type"] == "line":
                fig = px.line(df, x=cfg["x_column"], y=cfg["y_column"])
            elif cfg["chart_type"] == "pie":
                fig = px.pie(df, names=cfg["x_column"], values=cfg["y_column"])

            st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
            
            # Ham Veri ve İndirme Butonları
            with st.expander(f"'{cfg['title']}' Ham Verisini Gör ve İndir"):
                st.dataframe(df)
                
                btn_col1, btn_col2 = st.columns(2)
                
                csv_data = df.to_csv(index=False).encode('utf-8')
                btn_col1.download_button(
                    label="📥 CSV Olarak İndir",
                    data=csv_data,
                    file_name=f"analiz_{idx}.csv",
                    mime="text/csv",
                    key=f"csv_btn_{idx}"
                )
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Veri')
                
                btn_col2.download_button(
                    label="📥 Excel Olarak İndir",
                    data=buffer.getvalue(),
                    file_name=f"analiz_{idx}.xlsx",
                    mime="application/vnd.ms-excel",
                    key=f"excel_btn_{idx}"
                )
            
            st.divider()
    else:
        st.info("Henüz bir grafik oluşturulmadı. Sol panelden soru sorarak veya yukarıdaki öneri butonlarına basarak görselleştirme isteyebilirsiniz.")