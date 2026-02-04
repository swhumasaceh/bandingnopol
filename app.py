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
    # --- 1. PEMBACAAN DATA ---
    df_excel = pd.read_excel(excel_file, header=1)
    df_excel['NOPOL_NORMALIZED'] = df_excel['No Polisi'].apply(normalize_nopol)

    content = txt_file.read().decode("utf-8", errors="ignore")
    lines = content.splitlines()
    data_lines = [l for l in lines if "BL" in l] # Ambil baris yang ada plat nomor saja
    df_txt = pd.DataFrame(data_lines, columns=['RAW_TEXT'])
    df_txt['NOPOL_NORMALIZED'] = df_txt['RAW_TEXT'].apply(normalize_nopol)

    # --- 2. DEFINISI DAFTAR KOLOM (WAJIB) ---
    kolom_pokok_txt = ['POKOK_SW', 'POKOK_1', 'POKOK_2', 'POKOK_3', 'POKOK_4', 'PRORATA']
    kolom_denda_txt = ['DENDA_SW', 'DENDA_1', 'DENDA_2', 'DENDA_3', 'DENDA_4']
    semua_kolom_txt = kolom_pokok_txt + kolom_denda_txt

    # --- 3. EKSTRAKSI KOLOM DARI TXT (SOLUSI KEYERROR) ---
    # Kita pecah RAW_TEXT menjadi kolom-kolom tarif berdasarkan posisi karakter
    df_txt['POKOK_SW']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 90, 7))
    df_txt['DENDA_SW']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 97, 7))
    df_txt['POKOK_1']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 104, 7))
    df_txt['DENDA_1']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 111, 7))
    df_txt['POKOK_2']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 118, 7))
    df_txt['DENDA_2']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 125, 7))
    df_txt['POKOK_3']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 132, 7))
    df_txt['DENDA_3']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 139, 7))
    df_txt['POKOK_4']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 146, 7))
    df_txt['DENDA_4']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 153, 7))
    df_txt['PRORATA']   = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 160, 7))

    # --- 4. KONVERSI KE NUMERIK ---
    # Excel
    for col in ['KD', 'SW', 'DD', 'Jumlah']:
        if col in df_excel.columns:
            df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
    df_excel['POKOK_EXCEL'] = df_excel['KD'] + df_excel['SW']

    # TXT
    for col in semua_kolom_txt:
        df_txt[col] = pd.to_numeric(df_txt[col], errors='coerce').fillna(0)

    # --- 5. PERHITUNGAN RINGKASAN & SELISIH ---
    total_pokok_ex = df_excel['POKOK_EXCEL'].sum()
    total_denda_ex = df_excel['DD'].sum()
    total_jumlah_ex = df_excel['Jumlah'].sum()

    total_pokok_txt = df_txt[kolom_pokok_txt].sum().sum()
    total_denda_txt = df_txt[kolom_denda_txt].sum().sum()
    total_jumlah_txt = total_pokok_txt + total_denda_txt

    gap_pokok = total_pokok_txt - total_pokok_ex
    gap_denda = total_denda_txt - total_denda_ex
    gap_jumlah = total_jumlah_txt - total_jumlah_ex

    # --- 6. TAMPILAN DASHBOARD ---
    st.subheader("📊 Ringkasan Perbandingan Data")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pokok", f"Rp {total_pokok_txt:,.0f}", f"Gap: Rp {gap_pokok:,.0f}", delta_color="inverse")
    c2.metric("Total Denda", f"Rp {total_denda_txt:,.0f}", f"Gap: Rp {gap_denda:,.0f}", delta_color="inverse")
    c3.metric("Total Jumlah", f"Rp {total_jumlah_txt:,.0f}", f"Gap: Rp {gap_jumlah:,.0f}", delta_color="inverse")

    # --- 7. TAMPILAN TAB ---
    # (Lanjutkan dengan kode merge data cocok, hanya_excel, dan hanya_txt seperti sebelumnya)
    cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner')
    hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])]
    hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])]
        
    tab1, tab2, tab3 = st.tabs([
        "⚠️ Ada di Splitzing saja",
        "⚠️ Ada di CERI saja",
        "✅ Ada di Keduanya"
    ])

    with tab1:
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

    with tab2:
        st.subheader("⚠️ Data hanya ada di CERI")
        st.dataframe(hanya_excel)
        st.divider()
        st.subheader("💰 Rekapitulasi (Hanya di Excel)")
        m_ex1, m_ex2, m_ex3 = st.columns(3)
        m_ex1.metric("Pokok (KD+SW)", f"Rp {hanya_excel['POKOK_EXCEL'].sum():,.0f}")
        m_ex2.metric("Denda (DD)", f"Rp {hanya_excel['DD'].sum():,.0f}")
        m_ex3.metric("Total", f"Rp {hanya_excel['Jumlah'].sum():,.0f}")

    with tab3:
        st.subheader("✅ Data ditemukan di CERI dan Splitzing")
        st.dataframe(cocok)
        
        st.divider()
        st.subheader("💰 Rekapitulasi Tarif (Data Cocok)")
        
        # Tampilan angka besar untuk data yang cocok
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Total Pokok Cocok", f"Rp {total_pokok_cocok:,.0f}")
        mc2.metric("Total Denda Cocok", f"Rp {total_denda_cocok:,.0f}")
        mc3.metric("Grand Total Cocok", f"Rp {grand_total_cocok:,.0f}")
        
        st.write("**Detail Akumulasi per Kolom (Cocok):**")
        st.table(cocok[semua_kolom].sum().to_frame(name='Total (Rp)'))







