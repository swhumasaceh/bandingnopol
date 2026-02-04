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
    # 1. BACA DATA (KODE LAMA KAMU)
    df_excel = pd.read_excel(excel_file, header=1)
    df_excel['NOPOL_NORMALIZED'] = df_excel['No Polisi'].apply(normalize_nopol)

    lines = txt_file.read().decode("utf-8", errors="ignore").splitlines()
    # ... (proses extract_fixed kamu) ...

    # 2. DEFINISIKAN LIST KOLOM TARIF TXT
    kolom_pokok_txt = ['POKOK_SW', 'POKOK_1', 'POKOK_2', 'POKOK_3', 'POKOK_4', 'PRORATA']
    kolom_denda_txt = ['DENDA_SW', 'DENDA_1', 'DENDA_2', 'DENDA_3', 'DENDA_4']
    semua_kolom_txt = kolom_pokok_txt + kolom_denda_txt

    # 3. KONVERSI & BUAT KOLOM POKOK EXCEL (WAJIB DI SINI)
    for col in ['KD', 'SW', 'DD', 'Jumlah']:
        if col in df_excel.columns:
            df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
    
    # Membuat kolom POKOK_EXCEL sebelum di-sum (untuk menghindari KeyError)
    df_excel['POKOK_EXCEL'] = df_excel['KD'] + df_excel['SW']

    # 4. KONVERSI TARIF TXT KE ANGKA
    for col in semua_kolom_txt:
        if col in df_txt.columns:
            df_txt[col] = pd.to_numeric(df_txt[col], errors='coerce').fillna(0)

    # 5. PROSES PERBANDINGAN (MERGE & FILTER)
    cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner').copy()
    hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])].copy()
    hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])].copy()

    # 6. HITUNG TOTAL UNTUK RINGKASAN (METRIC)
    # Excel totals
    total_data_ex = len(df_excel)
    total_pokok_ex = df_excel['POKOK_EXCEL'].sum()
    total_denda_ex = df_excel['DD'].sum()
    total_jumlah_ex = df_excel['Jumlah'].sum()

    # TXT totals
    total_data_txt = len(df_txt)
    total_pokok_txt = df_txt[kolom_pokok_txt].sum().sum()
    total_denda_txt = df_txt[kolom_denda_txt].sum().sum()
    total_jumlah_txt = total_pokok_txt + total_denda_txt

    # Gap (TXT - Excel)
    gap_data = total_data_txt - total_data_ex
    gap_pokok = total_pokok_txt - total_pokok_ex
    gap_denda = total_denda_txt - total_denda_ex
    gap_jumlah = total_jumlah_txt - total_jumlah_ex

    # 7. TAMPILKAN RINGKASAN DI BAGIAN ATAS
    st.subheader("📊 Ringkasan Perbandingan Data")
    
    st.metric(
        label="Total Data (Nopol)", 
        value=f"{total_data_txt} Unit", 
        delta=f"Selisih: {gap_data} Unit vs Excel"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pokok", f"Rp {total_pokok_txt:,.0f}", f"Gap: Rp {gap_pokok:,.0f}", delta_color="inverse")
    c2.metric("Total Denda", f"Rp {total_denda_txt:,.0f}", f"Gap: Rp {gap_denda:,.0f}", delta_color="inverse")
    c3.metric("Total Jumlah", f"Rp {total_jumlah_txt:,.0f}", f"Gap: Rp {gap_jumlah:,.0f}", delta_color="inverse")

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





