import streamlit as st
import pandas as pd
import re
import time

@st.cache_data
def load_samsat_ref():
    try:
        df = pd.read_csv("samsat_ref.csv", names=['NamaSamsat', 'KodeExcel'], dtype=str)
        return df
    except:
        return pd.DataFrame(columns=['NamaSamsat', 'KodeExcel'])

df_ref_samsat = load_samsat_ref()

def extract_header_info(first_line, df_ref):
    try:
        tgl_raw = first_line[0:8]
        tgl_formatted = f"{tgl_raw[:2]}-{tgl_raw[2:4]}-{tgl_raw[4:]}"
        
        kode_splitzing = first_line[8:14].strip()
        
        suffix_target = kode_splitzing[-3:]
        
        match = df_ref[df_ref['KodeExcel'].astype(str).str.endswith(suffix_target)]
        
        if not match.empty:
            nama_samsat = match.iloc[0]['NamaSamsat']
        else:
            nama_samsat = "Unit Tidak Terdaftar"
            
        return tgl_formatted, kode_splitzing, nama_samsat
    except:
        return "00-00-0000", "000000", "Data Tidak Valid"

# CSS buttonnya biar hijau
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
st.title("Aplikasi Perbandingan Nopol Selisih Samsat - JR Aceh")

# --- CAPTION ---
st.caption("Pengecekan Selisih Nominal antara Data CERI dan Data Splitzing. Panduan lengkap bisa dilihat [DISINI](https://drive.google.com/drive/folders/1SvolTT-7_WGORXME0pzZTiiUWBGmMXTJ?usp=drive_link).")
st.caption("Pastikan seluruh data yang diupload sudah rapi, khususnya file txt splitzing yang didownload dari Aplikasi Samsat!")
st.caption("Untuk file Excel CERI, masuk ke Monitoring > TIK > [Penerimaan Per Nopol](https://ceri.jasaraharja.co.id/monitoring/sw_penerimaan_per_nopol) > Pilih Samsat dan Tanggal > Export")

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
def proses_data_audit_v2(excel_file, txt_file, df_ref):
    df_excel = pd.DataFrame()
    df_txt = pd.DataFrame()
    cocok = pd.DataFrame()
    hanya_excel = pd.DataFrame()
    hanya_txt = pd.DataFrame()
    info_header = {"tgl": "-", "kode": "-", "nama": "-"} # Inisialisasi awal

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
        raw_content = txt_file.getvalue().decode("utf-8", errors="ignore")
        lines_all = raw_content.splitlines()
        
        if lines_all:
            tgl, kd, nm = extract_header_info(lines_all[0], df_ref_samsat)
            info_header = {"tgl": tgl, "kode": kd, "nama": nm}
        
        lines_data = [l for l in lines_all if "BL" in l]
        df_txt = pd.DataFrame(lines_data, columns=['RAW_TEXT'])

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
        semua_kolom_txt = kolom_pokok_txt + kolom_denda_txt

        for col in semua_kolom_txt:
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

    return cocok, hanya_excel, hanya_txt, df_txt, df_excel, info_header

# --- UI LOGIC ---
col1, col2 = st.columns(2)
with col1:
    excel_input = st.file_uploader("Upload Excel (CERI)", type=["xlsx", "xlx"])
with col2:
    txt_input = st.file_uploader("Upload TXT/DAT (Splitzing)", type=["txt", "dat"])

# --- LOGIKA AUTO-RESET SAAT UPLOAD BARU ---
if 'file_excel_name' not in st.session_state: st.session_state.file_excel_name = None
if 'file_txt_name' not in st.session_state: st.session_state.file_txt_name = None
if 'proses_selesai' not in st.session_state: st.session_state.proses_selesai = False

# [cite_start]Cek apakah nama file yang diupload berbeda dengan yang ada di memori [cite: 37]
current_excel_name = excel_input.name if excel_input else None
current_txt_name = txt_input.name if txt_input else None

if current_excel_name != st.session_state.file_excel_name or current_txt_name != st.session_state.file_txt_name:
    st.session_state.proses_selesai = False  # Reset tampilan ke awal
    st.session_state.file_excel_name = current_excel_name
    st.session_state.file_txt_name = current_txt_name
    st.cache_data.clear() # Bersihkan cache agar data benar-benar baru

# Tombol muncul jika minimal salah satu file diupload
if excel_input or txt_input:
    if st.button("Cari Selisih", use_container_width=True):
        st.session_state.proses_selesai = True
    
    if st.session_state.proses_selesai:
        with st.spinner('Memproses data...'):
            cocok, hanya_excel, hanya_txt, df_txt, df_excel, info_h = proses_data_audit(excel_input, txt_input, df_ref_samsat)

        # [cite_start]Menampilkan peringatan jika salah satu file absen [cite: 39]
        if not excel_input: st.warning("⚠️ Data CERI (Excel) belum diunggah. Menampilkan data Splitzing saja.")
        if not txt_input: st.warning("⚠️ Data Splitzing (TXT) belum diunggah. Menampilkan data CERI saja.")

        # --- 4. TAMPILAN DASHBOARD ---
        st.subheader("Ringkasan Analisa Perbandingan Data")
        st.caption("Nominal yang tertulis pada ringkasan adalah Total Pengurangan Splitzing dan Excel, jadi harus double check ya!")

        if txt_input is not None:
            st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;">
                    Tanggal Penetapan: <b>{info_h['tgl']}</b> | Kode Samsat: <b>{info_h['kode']}</b> | 
                    <span style="background-color: #e0e0e0; padding: 2px 8px; border-radius: 5px;">Nama Samsat: <b>{info_h['nama']}</b></span>
                </div>
            """, unsafe_allow_html=True)
        
        sum_txt = df_txt['TOTAL_ALL_TXT'].sum() if not df_txt.empty else 0
        sum_excel = df_excel['Jumlah'].sum() if not df_excel.empty else 0
        
        # [cite_start]Hitung Gap/Selisih [cite: 40]
        gap_nopol = len(df_txt) - len(df_excel)
        gap_pokok = (df_txt['TOTAL_POKOK_TXT'].sum() if not df_txt.empty else 0) - (df_excel['POKOK_EXCEL'].sum() if not df_excel.empty else 0)
        gap_denda = (df_txt['TOTAL_DENDA_TXT'].sum() if not df_txt.empty else 0) - (df_excel['DD'].sum() if not df_excel.empty else 0)
        gap_total = sum_txt - sum_excel

        m0, m1, m2, m3 = st.columns(4)
        m0.metric("Total Nopol (Splitzing)", f"{len(df_txt)} Unit", f"Selisih: {gap_nopol}", delta_color="inverse")
        m1.metric("Total Pokok (Splitzing)", f"Rp {df_txt['TOTAL_POKOK_TXT'].sum():,.0f}" if not df_txt.empty else "Rp 0", f"Selisih: Rp {gap_pokok:,.0f}", delta_color="inverse")
        m2.metric("Total Denda (Splitzing)", f"Rp {df_txt['TOTAL_DENDA_TXT'].sum():,.0f}" if not df_txt.empty else "Rp 0", f"Selisih: Rp {gap_denda:,.0f}", delta_color="inverse")
        m3.metric("Grand Total (Splitzing)", f"Rp {sum_txt:,.0f}", f"Selisih vs Excel: Rp {gap_total:,.0f}", delta_color="inverse")
        
        st.divider()

        # [cite_start]--- 5. TAMPILAN TAB --- [cite: 41]
        tab1, tab2, tab3 = st.tabs(["Ada di Keduanya", "Perlu Dihapus", "Perlu Dipush"])

        with tab1:
            st.subheader("Berikut Data yang ditemukan di CERI dan Splitzing")
            if not cocok.empty:
                list_selisih = cocok[cocok['SELISIH_CHECK'] != 0]
                if not list_selisih.empty:
                    st.error(f"🚨 **Ditemukan Perbedaan Nominal pada {len(list_selisih)} Nopol berikut:**")
                    for _, row in list_selisih.iterrows():
                        st.write(f"👉 **{row['No Polisi']}** - Selisih: Rp {row['SELISIH_CHECK']:,.0f}")
                else:
                    st.success("Tidak ada perbedaan nominal pada nopol ini (tidak ada yang perlu update data)")
                
                st.divider()
                def highlight_diff(row):
                    return ['background-color: #ffcccc' if row.SELISIH_CHECK != 0 else '' for _ in row]

                df_display = cocok.drop(columns=['RAW_TEXT'], errors='ignore')
                st.dataframe(df_display.style.apply(highlight_diff, axis=1), use_container_width=True)
                st.metric("Total Nominal Cocok (splitzing)", f"Rp {cocok['TOTAL_ALL_TXT'].sum():,.0f}")
            else:
                st.info("Unggah kedua file untuk melihat perbandingan data yang cocok.")

        with tab2:
            st.subheader("⚠️ Ada di CERI (Excel) Tapi Tidak Ada di Splitzing / Data perlu dihapus")
            st.dataframe(hanya_excel, use_container_width=True)
            if not hanya_excel.empty:
                st.divider()
                st.subheader("💰 Rekapitulasi (Hanya di Excel)")
                e1, e2, e3 = st.columns(3)
                e1.metric("Pokok (KD+SW)", f"Rp {hanya_excel['POKOK_EXCEL'].sum():,.0f}")
                e2.metric("Denda (DD)", f"Rp {hanya_excel['DD'].sum():,.0f}")
                e3.metric("Total (Jumlah)", f"Rp {hanya_excel['Jumlah'].sum():,.0f}")

        with tab3:
            st.subheader("⚠️ Ada di Splitzing (Txt) Tapi Tidak Ada di CERI (Excel) / Data perlu dipush")
            st.caption("Setelah download file splitzing di bawah ini, mohon dapat diupload pada [Drive ini](https://drive.google.com/drive/folders/1jb8aJkv73abKVgRFo4EROmTB2uoHqu53?usp=drive_link). Jangan lupa ubah nama filenya menjadi Nama Samsat dan Tanggalnya.")
            if not hanya_txt.empty:
                txt_output = "\n".join(hanya_txt['RAW_TEXT'].tolist())
                st.download_button(
                    label="Download File Splitzing (Nopol Selisih Saja)",
                    data=txt_output,
                    file_name="selisih_splitzing_only.txt",
                    mime="text/plain"
                )
            
            st.divider()
            st.dataframe(hanya_txt.drop(columns=['RAW_TEXT'], errors='ignore'), use_container_width=True)
            if not hanya_txt.empty:
                st.divider()
                st.subheader("💰 Rekapitulasi (Nominal Selisih Saja berdasarkan Splitzing)")
                t1, t2, t3 = st.columns(3)
                t1.metric("Total Pokok", f"Rp {hanya_txt['TOTAL_POKOK_TXT'].sum():,.0f}")
                t2.metric("Total Denda", f"Rp {hanya_txt['TOTAL_DENDA_TXT'].sum():,.0f}")
                t3.metric("Grand Total", f"Rp {hanya_txt['TOTAL_ALL_TXT'].sum():,.0f}")

# --- FOOTER STATIS (SELALU MUNCUL DI AKHIR HALAMAN) ---
st.write("") 
st.divider() 
st.markdown(
    """
    <div style="text-align: center; color: #999; font-size: 12px; padding-bottom: 20px;">
        2026 Muhammad Hafiz R - Aplikasi Monitoring Selisih Nopol
    </div>
    """,
    unsafe_allow_html=True
)





