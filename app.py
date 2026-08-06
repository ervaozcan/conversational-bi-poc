import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from providers.local_duckdb import LocalDuckDBProvider
from ai.agent import BIAgent
st.session_state.provider = LocalDuckDBProvide

load_dotenv()

st.set_page_config(page_title="Conversational BI Dashboard", layout="wide")
st.title("📊 Conversational BI Assistant (Qlik Ready)")

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
            st.dataframe(st.session_state.current_df)