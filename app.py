
'''import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from providers.local_duckdb import LocalDuckDBProvider
from ai.agent import BIAgent

load_dotenv()

st.set_page_config(page_title="Conversational BI Dashboard", layout="wide")
st.title("📊 Conversational BI Assistant")

if "provider" not in st.session_state:
    st.session_state.provider = LocalDuckDBProvider("data/sales_data.csv")
    st.session_state.agent = BIAgent(st.session_state.provider)
    st.session_state.messages = []
    st.session_state.current_df = None
    st.session_state.current_chart = None

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("💬 Asistan ile Sohbet")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            

    user_input = st.chat_input("Verilerinizle ilgili bir soru sorun...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Veri analiz ediliyor..."):
                api_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                response_text, df, chart_config = st.session_state.agent.chat(user_input, api_history)
                
                st.write(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                if df is not None:
                    st.session_state.current_df = df
                if chart_config is not None:
                    st.session_state.current_chart = chart_config

with right_col:
    st.subheader("📈 Dinamik Dashboard Paneli")

    if st.session_state.current_chart and st.session_state.current_df is not None:
        cfg = st.session_state.current_chart
        df = st.session_state.current_df

        st.markdown(f"### {cfg['title']}")
        
        if cfg["chart_type"] == "bar":
            fig = px.bar(df, x=cfg["x_column"], y=cfg["y_column"])
        elif cfg["chart_type"] == "line":
            fig = px.line(df, x=cfg["x_column"], y=cfg["y_column"])
        elif cfg["chart_type"] == "pie":
            fig = px.pie(df, names=cfg["x_column"], values=cfg["y_column"])

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Henüz bir grafik oluşturulmadı. Sol panelden soru sorarak veri görselleştirmesi isteyebilirsiniz.")

    if st.session_state.current_df is not None:
        with st.expander("Son Sorgunun Ham Verisini Gör"):
            st.dataframe(st.session_state.current_df) '''

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from providers.local_duckdb import LocalDuckDBProvider
from ai.agent import BIAgent

load_dotenv()

st.set_page_config(page_title="Conversational BI Dashboard", layout="wide")
st.title("📊 Conversational BI Assistant")

# --- SOL MENÜ: DOSYA YÜKLEME ALANI ---
st.sidebar.header("📁 Veri Kaynağı Yükle")
uploaded_file = st.sidebar.file_uploader(
    "Analiz etmek istediğiniz CSV veya Excel dosyasını seçin", 
    type=["csv", "xlsx", "xls"]
)

active_data_path = "data/sales_data.csv"  # Varsayılan dosya

# Dosya yükleme optimizasyonu: Sadece yeni bir dosya yüklendiğinde diske yazar
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
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Verilerinizle ilgili bir soru sorun...")
    
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
            
            if cfg["chart_type"] == "bar":
                fig = px.bar(df, x=cfg["x_column"], y=cfg["y_column"])
            elif cfg["chart_type"] == "line":
                fig = px.line(df, x=cfg["x_column"], y=cfg["y_column"])
            elif cfg["chart_type"] == "pie":
                fig = px.pie(df, names=cfg["x_column"], values=cfg["y_column"])

            st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
            
            with st.expander(f"'{cfg['title']}' Ham Verisini Gör"):
                st.dataframe(df)
            
            st.divider()
    else:
        st.info("Henüz bir grafik oluşturulmadı. Sol panelden soru sorarak veri görselleştirmesi isteyebilirsiniz.")