import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Bandingkan Nopol Selisih JR Aceh", layout="wide")

st.title("Aplikasi Perbandingan Nopol Selisih JR Aceh")

def extract_fixed(text, start, length):
    try:
        return text[start-1:start-1+length].strip()
    except:
        return None
        
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
    
    # NOPOL
    df_txt['NOPOL_NORMALIZED'] = df_txt['RAW_TEXT'].apply(normalize_nopol)
    
    # ===============================
    # EKSTRAK KOLOM BERDASARKAN POSISI
    # ===============================
    df_txt['KODE_SAMSAT'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 9, 6))
    df_txt['TAHUN_MATI'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 49, 8))
    df_txt['TAHUN_DATANG'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 75, 8))
    
    df_txt['POKOK_SW'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 90, 7))
    df_txt['DENDA_SW'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 97, 7))
    
    df_txt['POKOK_1'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 104, 7))
    df_txt['DENDA_1'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 111, 7))
    
    df_txt['POKOK_2'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 118, 7))
    df_txt['DENDA_2'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 125, 7))
    
    df_txt['POKOK_3'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 132, 7))
    df_txt['DENDA_3'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 139, 7))
    
    df_txt['POKOK_4'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 146, 7))
    df_txt['DENDA_4'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 153, 7))
    
    df_txt['PRORATA'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 160, 7))
    
    # bersihkan yang tidak punya nopol
    df_txt = df_txt.dropna(subset=['NOPOL_NORMALIZED'])
    df_txt = df_txt.drop(columns=['RAW_TEXT'])
    
    # ===============================
    # PERBANDINGAN DATA
    # ===============================
    
    # Cocok: Excel + detail TXT
    cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner')
    
    # Hanya di Excel
    hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])]
    
    # Hanya di TXT (Gunakan .copy() agar tidak error saat hitung tarif)
    hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])].copy()

    # ===============================
    # LOGIKA PERHITUNGAN TARIF
    # ===============================
    
    kolom_pokok = ['POKOK_SW', 'POKOK_1', 'POKOK_2', 'POKOK_3', 'POKOK_4', 'PRORATA']
    kolom_denda = ['DENDA_SW', 'DENDA_1', 'DENDA_2', 'DENDA_3', 'DENDA_4']
    semua_kolom = kolom_pokok + kolom_denda
    
    # Konversi ke numerik
    for col in semua_kolom:
        if col in hanya_txt.columns:
            hanya_txt[col] = pd.to_numeric(hanya_txt[col], errors='coerce').fillna(0)
    
    # Hitung total per baris
    hanya_txt['TOTAL_POKOK'] = hanya_txt[kolom_pokok].sum(axis=1)
    hanya_txt['TOTAL_DENDA'] = hanya_txt[kolom_denda].sum(axis=1)
    hanya_txt['GRAND_TOTAL'] = hanya_txt['TOTAL_POKOK'] + hanya_txt['TOTAL_DENDA']
    
    # Hitung total akhir
    total_pokok_akhir = hanya_txt['TOTAL_POKOK'].sum()
    total_denda_akhir = hanya_txt['TOTAL_DENDA'].sum()
    grand_total_semua = hanya_txt['GRAND_TOTAL'].sum()

    # ===============================
    # TAMPILAN DASHBOARD
    # ===============================

    st.subheader("📊 Ringkasan")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Excel", len(df_excel))
    c2.metric("Total TXT", len(df_txt))
    c3.metric("Cocok", len(cocok))

    tab1, tab2, tab3 = st.tabs([
        "✅ Ada di Keduanya",
        "⚠️ Ada di CERI saja",
        "⚠️ Ada di Splitzing saja"
    ])

    with tab1:
        st.dataframe(cocok)

    with tab2:
        st.dataframe(hanya_excel)

    with tab3:
        st.subheader("⚠️ Data hanya ada di Splitzing")
        st.dataframe(hanya_txt)
    
        st.divider()
        st.subheader("💰 Rekapitulasi Tarif Selisih")
    
        # Tampilan angka besar
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pokok", f"Rp {total_pokok_akhir:,.0f}")
        m2.metric("Total Denda", f"Rp {total_denda_akhir:,.0f}")
        m3.metric("Grand Total", f"Rp {grand_total_semua:,.0f}")
    
        st.write("**Detail Akumulasi per Kolom:**")
        st.table(hanya_txt[semua_kolom].sum().to_frame(name='Total (Rp)'))
