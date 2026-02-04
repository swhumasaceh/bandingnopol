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
    # --- Perhitungan untuk tab 'Ada di Keduanya' ---
    # Gunakan .copy() agar aman saat memanipulasi kolom
    cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner').copy()
    
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

    # Konversi kolom keuangan di dataframe 'cocok'
    for col in semua_kolom:
        if col in cocok.columns:
            cocok[col] = pd.to_numeric(cocok[col], errors='coerce').fillna(0)

    # Hitung total per baris untuk data yang cocok
    cocok['TOTAL_POKOK'] = cocok[kolom_pokok].sum(axis=1)
    cocok['TOTAL_DENDA'] = cocok[kolom_denda].sum(axis=1)
    cocok['GRAND_TOTAL'] = cocok['TOTAL_POKOK'] + cocok['TOTAL_DENDA']

    # Hitung total akhir untuk ringkasan tab cocok
    total_pokok_cocok = cocok['TOTAL_POKOK'].sum()
    total_denda_cocok = cocok['TOTAL_DENDA'].sum()
    grand_total_cocok = cocok['GRAND_TOTAL'].sum()

    # ===============================
    # TAMPILAN DASHBOARD
    # ===============================

    st.subheader("📊 Ringkasan Perbandingan Data")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Excel", len(df_excel))
    c2.metric("Total TXT", len(df_txt))
    c3.metric("Cocok", len(cocok))

    # ===============================
    # 1. PERHITUNGAN TOTAL RINGKASAN
    # ===============================
    
    # Total dari Excel (CERI)
    total_data_ex = len(df_excel)
    total_pokok_ex = df_excel['POKOK_EXCEL'].sum()
    total_denda_ex = df_excel['DD'].sum()
    total_jumlah_ex = df_excel['Jumlah'].sum()

    # Total dari TXT (Splitzing)
    total_data_txt = len(df_txt)
    total_pokok_txt = df_txt[kolom_pokok_txt].sum().sum()
    total_denda_txt = df_txt[kolom_denda_txt].sum().sum()
    total_jumlah_txt = total_pokok_txt + total_denda_txt

    # 2. HITUNG SELISIH (GAP) - (TXT dikurangi Excel)
    gap_data = total_data_txt - total_data_ex
    gap_pokok = total_pokok_txt - total_pokok_ex
    gap_denda = total_denda_txt - total_denda_ex
    gap_jumlah = total_jumlah_txt - total_jumlah_ex

    # ===============================
    # 2. TAMPILAN DASHBOARD METRIC
    # ===============================
    st.subheader("📊 Ringkasan Perbandingan Data")
    
    # Baris Pertama: Jumlah Data
    st.metric(
        label="Total Data (Nopol)", 
        value=f"{total_data_txt} Kendaraan", 
        delta=f"Selisih: {gap_data} Nopol vs Excel",
        delta_color="normal"
    )

    # Baris Kedua: Nominal Rupiah
    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        label="Total Pokok (TXT)", 
        value=f"Rp {total_pokok_txt:,.0f}", 
        delta=f"Gap: Rp {gap_pokok:,.0f}",
        delta_color="inverse"
    )
    
    col2.metric(
        label="Total Denda (TXT)", 
        value=f"Rp {total_denda_txt:,.0f}", 
        delta=f"Gap: Rp {gap_denda:,.0f}",
        delta_color="inverse"
    )
    
    col3.metric(
        label="Grand Total (TXT)", 
        value=f"Rp {total_jumlah_txt:,.0f}", 
        delta=f"Gap: Rp {gap_jumlah:,.0f}",
        delta_color="inverse"
    )
    
    st.divider()

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
        st.subheader("⚠️ Data hanya ada di CERI (Excel)")
        
        # --- LOGIKA PERHITUNGAN KHUSUS EXCEL ---
        # 1. Pastikan kolom Excel dikonversi ke numerik agar bisa dijumlahkan
        kolom_hitung_excel = ['KD', 'SW', 'DD', 'Jumlah']
        for col in kolom_hitung_excel:
            if col in hanya_excel.columns:
                hanya_excel[col] = pd.to_numeric(hanya_excel[col], errors='coerce').fillna(0)
        
        # 2. Hitung Pokok (KD + SW) per baris
        if 'KD' in hanya_excel.columns and 'SW' in hanya_excel.columns:
            hanya_excel['TOTAL_POKOK_EX'] = hanya_excel['KD'] + hanya_excel['SW']
        else:
            hanya_excel['TOTAL_POKOK_EX'] = 0

        # 3. Hitung Grand Total untuk metrik dashboard
        total_pokok_ex = hanya_excel['TOTAL_POKOK_EX'].sum()
        total_denda_ex = hanya_excel['DD'].sum() if 'DD' in hanya_excel.columns else 0
        total_jumlah_ex = hanya_excel['Jumlah'].sum() if 'Jumlah' in hanya_excel.columns else 0
        
        # --- TAMPILAN ---
        st.dataframe(hanya_excel)
        
        st.divider()
        st.subheader("💰 Rekapitulasi Tarif (Hanya di Excel)")
        
        # Tampilan metrik angka besar
        m_ex1, m_ex2, m_ex3 = st.columns(3)
        m_ex1.metric("Total Pokok (KD+SW)", f"Rp {total_pokok_ex:,.0f}")
        m_ex2.metric("Total Denda (DD)", f"Rp {total_denda_ex:,.0f}")
        m_ex3.metric("Grand Total (Jumlah)", f"Rp {total_jumlah_ex:,.0f}")

        # Tabel rincian akumulasi
        rekap_ex = pd.DataFrame({
            "Kategori": ["Pokok (KD+SW)", "Denda (DD)", "Total Keseluruhan"],
            "Nilai": [total_pokok_ex, total_denda_ex, total_jumlah_ex]
        })
        st.table(rekap_ex.set_index("Kategori"))

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




