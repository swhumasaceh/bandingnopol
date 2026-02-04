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
        width: 100%; 
    }
    
    /* Efek hover untuk semua tombol */
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #218838 !important;
        color: white !important;
    }

    /* Menghilangkan border bawaan streamlit saat diklik */
    .stButton > button:focus, .stDownloadButton > button:focus {
        box-shadow: none !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Bandingkan Nopol Selisih JR Aceh", layout="wide")
st.title("Aplikasi Perbandingan Nopol Selisih JR Aceh")

# --- CAPTION ---
st.caption("Pengecekan Selisih Nominal antara Data CERI dan Data Splitzing, pastikan seluruh data yang diupload sudah rapi, khususnya file txt splitzing ya!")
st.caption("Untuk file Excel CERI, masuk ke Monitoring > TIK > Penerimaan Per Nopol > Pilih Samsat dan Tanggal > Show ALL entries > Export")

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
        df_excel = pd.read_excel(excel_file, header=1)
        df_excel = df_excel.dropna(subset=['No Polisi'])
        df_excel['NOPOL_NORMALIZED'] = df_excel['No Polisi'].apply(normalize_nopol)
        for col in ['KD', 'SW', 'DD', 'Jumlah']:
            df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
        df_excel['POKOK_EXCEL'] = df_excel['KD'] + df_excel['SW']

    # 2. PROSES TXT (Jika ada)
    if txt_file is not None:
        content = txt_file.read().decode("utf-8", errors="ignore")
        lines = [l for l in content.splitlines() if "BL" in l]
        df_txt = pd.DataFrame(lines, columns=['RAW_TEXT'])
        df_txt['NOPOL_NORMALIZED'] = df_txt['RAW_TEXT'].apply(normalize_nopol)

        df_txt['POKOK_SW'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 90, 7))
        df_txt['DENDA_SW'] = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 97, 7))
        df_txt['POKOK_1']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 104, 7))
        df_txt['DENDA_1']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 111, 7))
        df_txt['POKOK_2']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 118, 7))
        df_txt['DENDA_2']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 125, 7))
        df_txt['POKOK_3']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 132, 7))
        df_txt['DENDA_3']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 139, 7))
        df_txt['POKOK_4']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 146, 7))
        df_txt['DENDA_4']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 153, 7))
        df_txt['PRORATA']  = df_txt['RAW_TEXT'].apply(lambda x: extract_fixed(x, 160, 7))

        kolom_pokok_txt = ['POKOK_SW', 'POKOK_1', 'POKOK_2', 'POKOK_3', 'POKOK_4', 'PRORATA']
        kolom_denda_txt = ['DENDA_SW', 'DENDA_1', 'DENDA_2', 'DENDA_3', 'DENDA_4']
        
        for col in (kolom_pokok_txt + kolom_denda_txt):
            df_txt[col] = pd.to_numeric(df_txt[col], errors='coerce').fillna(0)
        
        df_txt['TOTAL_POKOK_TXT'] = df_txt[kolom_pokok_txt].sum(axis=1)
        df_txt['TOTAL_DENDA_TXT'] = df_txt[kolom_denda_txt].sum(axis=1)
        df_txt['TOTAL_ALL_TXT'] = df_txt['TOTAL_POKOK_TXT'] + df_txt['TOTAL_DENDA_TXT']

    # 3. LOGIKA PERBANDINGAN
    if not df_excel.empty and not df_txt.empty:
        cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner').copy()
        hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])].copy()
        hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])].copy()
        cocok['SELISIH_CHECK'] = cocok['TOTAL_ALL_TXT'] - cocok['Jumlah']
    elif not df_excel.empty:
        hanya_excel = df_excel.copy()
    elif not df_txt.empty:
        hanya_txt = df_txt.copy()

    return cocok, hanya_excel, hanya_txt, df_txt, df_excel

# --- UI LOGIC ---
col1, col2 = st.columns(2)
with col1:
    excel_input = st.file_uploader("Upload Excel (CERI)", type=["xlsx"])
with col2:
    txt_input = st.file_uploader("Upload TXT (Splitzing)", type=["txt"])

# --- LOGIKA AUTO-RESET ---
if 'file_excel_name' not in st.session_state: st.session_state.file_excel_name = None
if 'file_txt_name' not in st.session_state: st.session_state.file_txt_name = None
if 'proses_selesai' not in st.session_state: st.session_state.proses_selesai = False

current_excel_name = excel_input.name if excel_input else None
current_txt_name = txt_input.name if txt_input else None

if current_excel_name != st.session_state.file_excel_name or current_txt_name != st.session_state.file_txt_name:
    st.session_state.proses_selesai = False
    st.session_state.file_excel_name = current_excel_name
    st.session_state.file_txt_name = current_txt_name
    st.cache_data.clear()

# Tombol muncul jika minimal salah satu file diupload
if excel_input or txt_input:
    if st.button("Proses Data", use_container_width=True):
        st.session_state.proses_selesai = True
    
    if st.session_state.proses_selesai:
        with st.spinner('Memproses data...'):
            cocok, hanya_excel, hanya_txt, df_txt, df_excel = proses_data_audit(excel_input, txt_input)

        if not excel_input: st.warning("⚠️ Data CERI (Excel) belum diunggah.")
        if not txt_input: st.warning("⚠️ Data Splitzing (TXT) belum diunggah.")

        # --- 4. DASHBOARD ---
        st.subheader("📊 Ringkasan Perbandingan Data")
        
        sum_txt = df_txt['TOTAL_ALL_TXT'].sum() if not df_txt.empty else 0
        sum_excel = df_excel['Jumlah'].sum() if not df_excel.empty else 0
        gap_total = sum_txt - sum_excel

        m0, m1, m2, m3 = st.columns(4)
        m0.metric("Total Nopol (TXT)", f"{len(df_txt)} Unit")
        m1.metric("Total Pokok (TXT)", f"Rp {df_txt['TOTAL_POKOK_TXT'].sum():,.0f}" if not df_txt.empty else "Rp 0")
        m2.metric("Total Denda (TXT)", f"Rp {df_txt['TOTAL_DENDA_TXT'].sum():,.0f}" if not df_txt.empty else "Rp 0")
        m3.metric("Grand Total (TXT)", f"Rp {sum_txt:,.0f}", f"Gap vs Excel: Rp {gap_total:,.0f}", delta_color="inverse")
        
        st.divider()

        # --- 5. TAMPILAN TAB ---
        tab1, tab2, tab3 = st.tabs(["✅ Ada di Keduanya", "⚠️ Ada di CERI saja", "⚠️ Ada di Splitzing saja"])

        with tab1:
            if not cocok.empty:
                list_selisih = cocok[cocok['SELISIH_CHECK'] != 0]
                if not list_selisih.empty:
                    st.error(f"🚨 Ditemukan Perbedaan Nominal pada {len(list_selisih)} Nopol.")
                def highlight_diff(row):
                    return ['background-color: #ffcccc' if row.SELISIH_CHECK != 0 else '' for _ in row]
                st.dataframe(cocok.drop(columns=['RAW_TEXT'], errors='ignore').style.apply(highlight_diff, axis=1), use_container_width=True)
            else:
                st.info("Unggah kedua file untuk melihat perbandingan.")

        with tab2:
            st.dataframe(hanya_excel, use_container_width=True)
            if not hanya_excel.empty:
                st.metric("Total (Hanya Excel)", f"Rp {hanya_excel['Jumlah'].sum():,.0f}")

        with tab3:
            if not hanya_txt.empty:
                txt_output = "\n".join(hanya_txt['RAW_TEXT'].tolist())
                st.download_button(label="📥 Download Baris TXT Asli", data=txt_output, file_name="selisih.txt", mime="text/plain")
            st.dataframe(hanya_txt.drop(columns=['RAW_TEXT'], errors='ignore'), use_container_width=True)

# --- FOOTER STATIS ---
st.write("") 
st.divider() 
st.markdown(
    """
    <div style="text-align: center; color: #999; font-size: 12px; padding-bottom: 20px;">
        Project 2026 oleh Muhammad Hafiz R - Aplikasi Monitoring Selisih Nopol
    </div>
    """, 
    unsafe_allow_html=True
)
