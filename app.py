import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Bandingkan NOPOL", layout="wide")

st.title("🔍 Aplikasi Perbandingan NOPOL")

def normalize_nopol(text):
    if pd.isna(text):
        return None
    text = str(text).upper()
    match = re.search(r'BL\s*-?\s*\d{1,4}\s*-?\s*[A-Z]{1,3}', text)
    if match:
        return re.sub(r'[^A-Z0-9]', '', match.group())
    return None

col1, col2 = st.columns(2)

with col1:
    excel_file = st.file_uploader("Upload Excel (CERI)", type=["xlsx"])

with col2:
    txt_file = st.file_uploader("Upload TXT (Splitzing)", type=["txt"])

if excel_file and txt_file:
    df_excel = pd.read_excel(excel_file, header=1)
    df_excel['NOPOL_NORMALIZED'] = df_excel['No Polisi'].apply(normalize_nopol)

    lines = txt_file.read().decode("utf-8", errors="ignore").splitlines()
    df_txt = pd.DataFrame(lines, columns=['RAW_TEXT'])
    df_txt['NOPOL_NORMALIZED'] = df_txt['RAW_TEXT'].apply(normalize_nopol)
    df_txt = df_txt.dropna(subset=['NOPOL_NORMALIZED'])

    cocok = df_excel[df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])]
    hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])]
    hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])]

    st.subheader("📊 Ringkasan")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Excel", len(df_excel))
    c2.metric("Total TXT", len(df_txt))
    c3.metric("Cocok", len(cocok))

    tab1, tab2, tab3 = st.tabs([
        "✅ Cocok",
        "⚠️ Ada di Excel saja",
        "⚠️ Ada di TXT saja"
    ])

    with tab1:
        st.dataframe(cocok)

    with tab2:
        st.dataframe(hanya_excel)

    with tab3:

        st.dataframe(hanya_txt)
