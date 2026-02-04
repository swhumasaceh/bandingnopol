import streamlit as st
import pandas as pd
import re
import time

# --- CUSTOM CSS UNTUK TOMBOL HIJAU ---
st.markdown("""
    <style>
    /* Menargetkan semua tombol (Proses Data & Download) */
    .stButton > button, .stDownloadButton > button {
        background-color: #28a745 !important; /* Warna hijau */
        color: white !important;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        transition: 0.3s;
        width: 100%; /* Agar tombol Proses Data tetap selebar kontainer */
    }
    
    /* Efek hover untuk semua tombol */
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #218838 !important;
        color: white !important;
    }

    /* Menghilangkan border merah/biru bawaan streamlit saat diklik */
    .stButton > button:focus, .stDownloadButton > button:focus {
        box-shadow: none !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Bandingkan Nopol Selisih JR Aceh", layout="wide")
st.title("Aplikasi Perbandingan Nopol Selisih JR Aceh")

# --- CAPTION ---
[cite_start]st.caption("Pengecekan Selisih Nominal antara Data CERI dan Data Splitzing, pastikan seluruh data yang diupload sudah rapi, khususnya file txt splitzing ya! [cite: 5]")
[cite_start]st.caption("Untuk file Excel CERI, masuk ke Monitoring > TIK > Penerimaan Per Nopol > Pilih Samsat dan Tanggal > Show ALL entries > Export [cite: 5]")

st.divider()

# --- FUNGSI TOOLS ---
def extract_fixed(text, start, length):
    try:
        val = text[start-1:start-1+length].strip()
        return val if val else "0"
    except:
        return "0"

def normalize_nopol(text):
    if pd.isna(text): return None
    text = str(text).upper()
    match = re.search(r'BL\s*-?\s*\d{1,4}\s*-?\s*[A-Z]{1,3}', text)
    if match:
        return re.sub(r'[^A-Z0-9]', '', match.group())
    return None

# --- FUNGSI PROSES DENGAN CACHE ---
@st.cache_data(show_spinner=False)
def proses_data_audit(excel_file, txt_file):
    df_excel = pd.DataFrame()
    df_txt = pd.DataFrame()
    cocok = pd.DataFrame()
    hanya_excel = pd.DataFrame()
    hanya_txt = pd.DataFrame()

    # 1. PROSES EXCEL (Jika ada)
    if excel_file is not None:
        [cite_start]df_excel = pd.read_excel(excel_file, header=1) [cite: 5]
        [cite_start]df_excel = df_excel.dropna(subset=['No Polisi']) [cite: 5]
        [cite_start]df_excel['NOPOL_NORMALIZED'] = df_excel['No Polisi'].apply(normalize_nopol) [cite: 5]
        
        for col in ['KD', 'SW', 'DD', 'Jumlah']:
            [cite_start]df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0) [cite: 5]
        [cite_start]df_excel['POKOK_EXCEL'] = df_excel['KD'] + df_excel['SW'] [cite: 5]

    # 2. PROSES TXT (Jika ada)
    if txt_file is not None:
        [cite_start]content = txt_file.read().decode("utf-8", errors="ignore") [cite: 5]
        [cite_start]lines = [l for l in content.splitlines() if "BL" in l] [cite: 5]
        [cite_start]df_txt = pd.DataFrame(lines, columns=['RAW_TEXT']) [cite: 5]
        [cite_start]df_txt['NOPOL_NORMALIZED'] = df_txt['RAW_TEXT'].apply(normalize_nopol) [cite: 5]

        [cite_start]df_txt['POKOK_SW'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 90, 7)) [cite: 5]
        [cite_start]df_txt['DENDA_SW'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 97, 7)) [cite: 5]
        [cite_start]df_txt['POKOK_1']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 104, 7)) [cite: 5]
        [cite_start]df_txt['DENDA_1']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 111, 7)) [cite: 5]
        [cite_start]df_txt['POKOK_2']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 118, 7)) [cite: 5]
        [cite_start]df_txt['DENDA_2']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 125, 7)) [cite: 5]
        [cite_start]df_txt['POKOK_3']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 132, 7)) [cite: 5]
        [cite_start]df_txt['DENDA_3']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 139, 7)) [cite: 5]
        [cite_start]df_txt['POKOK_4']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 146, 7)) [cite: 5]
        [cite_start]df_txt['DENDA_4']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 153, 7)) [cite: 5]
        [cite_start]df_txt['PRORATA']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 160, 7)) [cite: 5]

        [cite_start]kolom_pkk = ['POKOK_SW', 'POKOK_1', 'POKOK_2', 'POKOK_3', 'POKOK_4', 'PRORATA'] [cite: 5]
        [cite_start]kolom_dnd = ['DENDA_SW', 'DENDA_1', 'DENDA_2', 'DENDA_3', 'DENDA_4'] [cite: 5]
        for col in (kolom_pkk + kolom_dnd):
            [cite_start]df_txt[col] = pd.to_numeric(df_txt[col], errors='coerce').fillna(0) [cite: 5]
        
        [cite_start]df_txt['TOTAL_POKOK_TXT'] = df_txt[kolom_pkk].sum(axis=1) [cite: 5]
        [cite_start]df_txt['TOTAL_DENDA_TXT'] = df_txt[kolom_dnd].sum(axis=1) [cite: 5]
        [cite_start]df_txt['TOTAL_ALL_TXT'] = df_txt['TOTAL_POKOK_TXT'] + df_txt['TOTAL_DENDA_TXT'] [cite: 5]

    # 3. LOGIKA PERBANDINGAN
    if not df_excel.empty and not df_txt.empty:
        [cite_start]cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner').copy() [cite: 5]
        [cite_start]hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])].copy() [cite: 5]
        [cite_start]hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])].copy() [cite: 5]
        [cite_start]cocok['SELISIH_CHECK'] = cocok['TOTAL_ALL_TXT'] - cocok['Jumlah'] [cite: 5]
    elif not df_excel.empty:
        [cite_start]hanya_excel = df_excel.copy() [cite: 5]
    elif not df_txt.empty:
        [cite_start]hanya_txt = df_txt.copy() [cite: 5]

    return cocok, hanya_excel, hanya_txt, df_txt, df_excel

# --- UI LOGIC ---
col1, col2 = st.columns(2)
with col1:
    [cite_start]excel_input = st.file_uploader("Upload Excel (CERI)", type=["xlsx"]) [cite: 5]
with col2:
    [cite_start]txt_input = st.file_uploader("Upload TXT (Splitzing)", type=["txt"]) [cite: 5]

[cite_start]if 'file_excel_name' not in st.session_state: st.session_state.file_excel_name = None [cite: 5]
[cite_start]if 'file_txt_name' not in st.session_state: st.session_state.file_txt_name = None [cite: 5]
[cite_start]if 'proses_selesai' not in st.session_state: st.session_state.proses_selesai = False [cite: 5]

[cite_start]current_excel_name = excel_input.name if excel_input else None [cite: 5]
[cite_start]current_txt_name = txt_input.name if txt_input else None [cite: 5]

if current_excel_name != st.session_state.file_excel_name or current_txt_name != st.session_state.file_txt_name:
    [cite_start]st.session_state.proses_selesai = False [cite: 5]
    [cite_start]st.session_state.file_excel_name = current_excel_name [cite: 5]
    [cite_start]st.session_state.file_txt_name = current_txt_name [cite: 5]
    [cite_start]st.cache_data.clear() [cite: 5]

if excel_input or txt_input:
    [cite_start]if st.button("Cari Selisih", use_container_width=True): [cite: 5]
        [cite_start]st.session_state.proses_selesai = True [cite: 5]
    
    if st.session_state.proses_selesai:
        with st.spinner('Memproses data...'):
            [cite_start]cocok, hanya_excel, hanya_txt, df_txt, df_excel = proses_data_audit(excel_input, txt_input) [cite: 5]

        if not excel_input: st.warning("⚠️ Data CERI (Excel) belum diunggah.")
        if not txt_input: st.warning("⚠️ Data Splitzing (TXT) belum diunggah.")

        # --- DASHBOARD DENGAN SELISIH (GAP) ---
        st.subheader("📊 Ringkasan Perbandingan Data")
        
        # Hitung Nilai Nominal (handle jika dataframe kosong)
        sum_txt = df_txt['TOTAL_ALL_TXT'].sum() if not df_txt.empty else 0
        sum_excel = df_excel['Jumlah'].sum() if not df_excel.empty else 0
        
        # Hitung Selisih (Gap)
        gap_nopol = len(df_txt) - len(df_excel)
        gap_total = sum_txt - sum_excel

        m0, m1, m2, m3 = st.columns(4)
        # Menambahkan parameter delta untuk menampilkan selisih di ringkasan
        m0.metric("Total Nopol (TXT)", f"{len(df_txt)} Unit", f"Selisih: {gap_nopol}")
        m1.metric("Total Pokok (TXT)", f"Rp {df_txt['TOTAL_POKOK_TXT'].sum():,.0f}" if not df_txt.empty else "Rp 0")
        m2.metric("Total Denda (TXT)", f"Rp {df_txt['TOTAL_DENDA_TXT'].sum():,.0f}" if not df_txt.empty else "Rp 0")
        m3.metric("Grand Total (TXT)", f"Rp {sum_txt:,.0f}", f"Gap vs CERI: Rp {gap_total:,.0f}", delta_color="inverse")
        
        st.divider()

        # --- TABEL DETAIL ---
        tab1, tab2, tab3 = st.tabs(["1. Ada di Keduanya", "2. Ada di CERI saja", "3. [cite_start]Ada di Splitzing saja"]) [cite: 5]

        with tab1:
            [cite_start]st.subheader("✅ Data ditemukan di CERI dan Splitzing") [cite: 5]
            if not cocok.empty:
                [cite_start]list_selisih = cocok[cocok['SELISIH_CHECK'] != 0] [cite: 5]
                if not list_selisih.empty:
                    [cite_start]st.error(f"🚨 **Ditemukan Perbedaan Nominal pada {len(list_selisih)} Nopol.**") [cite: 5]
                
                def highlight_diff(row):
                    [cite_start]return ['background-color: #ffcccc' if row.SELISIH_CHECK != 0 else '' for _ in row] [cite: 5]

                [cite_start]df_display = cocok.drop(columns=['RAW_TEXT'], errors='ignore') [cite: 5]
                [cite_start]st.dataframe(df_display.style.apply(highlight_diff, axis=1), use_container_width=True) [cite: 5]
                [cite_start]st.metric("Total Nominal Cocok (TXT)", f"Rp {cocok['TOTAL_ALL_TXT'].sum():,.0f}") [cite: 5]
            else:
                st.info("Unggah kedua file untuk melihat perbandingan.")

        with tab2:
            [cite_start]st.subheader("⚠️ Ada di CERI (Excel) Tapi Tidak Ada di Splitzing") [cite: 5]
            [cite_start]st.dataframe(hanya_excel, use_container_width=True) [cite: 5]
            if not hanya_excel.empty:
                [cite_start]st.divider() [cite: 5]
                [cite_start]st.subheader("💰 Rekapitulasi (Hanya di Excel)") [cite: 5]
                [cite_start]e1, e2, e3 = st.columns(3) [cite: 5]
                [cite_start]e1.metric("Pokok (KD+SW)", f"Rp {hanya_excel['POKOK_EXCEL'].sum():,.0f}") [cite: 5]
                [cite_start]e2.metric("Denda (DD)", f"Rp {hanya_excel['DD'].sum():,.0f}") [cite: 5]
                [cite_start]e3.metric("Total (Jumlah)", f"Rp {hanya_excel['Jumlah'].sum():,.0f}") [cite: 5]

        with tab3:
            [cite_start]st.subheader("⚠️ Ada di Splitzing (Txt) Tapi Tidak Ada di CERI (Excel)") [cite: 5]
            if not hanya_txt.empty:
                [cite_start]txt_output = "\n".join(hanya_txt['RAW_TEXT'].tolist()) [cite: 5]
                [cite_start]st.download_button( [cite: 5]
                    [cite_start]label="Download File Splitzing (Khusus Nopol Selisih)", [cite: 5]
                    [cite_start]data=txt_output, [cite: 5]
                    [cite_start]file_name="selisih_splitzing_only.txt", [cite: 5]
                    [cite_start]mime="text/plain" [cite: 5]
                )
            
            [cite_start]st.divider() [cite: 5]
            [cite_start]st.dataframe(hanya_txt.drop(columns=['RAW_TEXT'], errors='ignore'), use_container_width=True) [cite: 5]
            if not hanya_txt.empty:
                [cite_start]st.divider() [cite: 5]
                [cite_start]st.subheader("💰 Rekapitulasi (Nominal Splitzing Saja)") [cite: 5]
                [cite_start]t1, t2, t3 = st.columns(3) [cite: 5]
                [cite_start]t1.metric("Total Pokok", f"Rp {hanya_txt['TOTAL_POKOK_TXT'].sum():,.0f}") [cite: 5]
                [cite_start]t2.metric("Total Denda", f"Rp {hanya_txt['TOTAL_DENDA_TXT'].sum():,.0f}") [cite: 5]
                [cite_start]t3.metric("Grand Total", f"Rp {hanya_txt['TOTAL_ALL_TXT'].sum():,.0f}") [cite: 5]

# --- FOOTER STATIS ---
st.write("") 
st.divider() 
st.markdown(
    """
    <div style="text-align: center; color: #999; font-size: 12px; padding-bottom: 20px;">
        [cite_start]Project 2026 oleh Muhammad Hafiz R - Aplikasi Monitoring Selisih Nopol [cite: 5]
    </div>
    """, 
    unsafe_allow_html=True
)
