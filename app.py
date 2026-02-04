import streamlit as st
import pandas as pd
import re
import time

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
# Ini rahasianya supaya data tidak hilang saat halaman rerun/refresh
@st.cache_data(show_spinner=False)
def proses_data_audit(excel_file, txt_file):
    # 1. PROSES EXCEL
    df_excel = pd.read_excel(excel_file, header=1)
    df_excel = df_excel.dropna(subset=['No Polisi'])
    df_excel['NOPOL_NORMALIZED'] = df_excel['No Polisi'].apply(normalize_nopol)
    
    for col in ['KD', 'SW', 'DD', 'Jumlah']:
        df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
    df_excel['POKOK_EXCEL'] = df_excel['KD'] + df_excel['SW']

    # 2. PROSES TXT
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
    semua_kolom_txt = kolom_pokok_txt + kolom_denda_txt

    for col in semua_kolom_txt:
        df_txt[col] = pd.to_numeric(df_txt[col], errors='coerce').fillna(0)
    
    df_txt['TOTAL_POKOK_TXT'] = df_txt[kolom_pokok_txt].sum(axis=1)
    df_txt['TOTAL_DENDA_TXT'] = df_txt[kolom_denda_txt].sum(axis=1)
    df_txt['TOTAL_ALL_TXT'] = df_txt['TOTAL_POKOK_TXT'] + df_txt['TOTAL_DENDA_TXT']

    # 3. LOGIKA PERBANDINGAN
    cocok = df_excel.merge(df_txt, on='NOPOL_NORMALIZED', how='inner').copy()
    hanya_excel = df_excel[~df_excel['NOPOL_NORMALIZED'].isin(df_txt['NOPOL_NORMALIZED'])].copy()
    hanya_txt = df_txt[~df_txt['NOPOL_NORMALIZED'].isin(df_excel['NOPOL_NORMALIZED'])].copy()
    cocok['SELISIH_CHECK'] = cocok['TOTAL_ALL_TXT'] - cocok['Jumlah']

    return cocok, hanya_excel, hanya_txt, df_txt, df_excel

# --- UI LOGIC ---
col1, col2 = st.columns(2)
with col1:
    excel_input = st.file_uploader("Upload Excel (CERI)", type=["xlsx"])
with col2:
    txt_input = st.file_uploader("Upload TXT (Splitzing)", type=["txt"])

# Inisialisasi status proses agar data tidak hilang saat klik download
if 'proses_selesai' not in st.session_state:
    st.session_state.proses_selesai = False

if excel_input and txt_input:
    # Jika tombol ditekan, ubah status menjadi True
    if st.button("Proses Data", use_container_width=True):
        st.session_state.proses_selesai = True
    
    # Tampilkan hasil hanya jika tombol sudah pernah diklik
    if st.session_state.proses_selesai:
        # Spinner hanya muncul saat pertama kali hitung, selanjutnya ambil dari cache
        with st.spinner('Menyelaraskan data...'):
            cocok, hanya_excel, hanya_txt, df_txt, df_excel = proses_data_audit(excel_input, txt_input)

        # --- 4. TAMPILAN DASHBOARD ---
        st.subheader("📊 Ringkasan Perbandingan Data")
        
        gap_nopol = len(df_txt) - len(df_excel)
        gap_pokok = df_txt['TOTAL_POKOK_TXT'].sum() - df_excel['POKOK_EXCEL'].sum()
        gap_denda = df_txt['TOTAL_DENDA_TXT'].sum() - df_excel['DD'].sum()
        gap_total = df_txt['TOTAL_ALL_TXT'].sum() - df_excel['Jumlah'].sum()

        m0, m1, m2, m3 = st.columns(4)
        m0.metric("Total Nopol", f"{len(df_txt)} Unit", f"Selisih Nopol: {gap_nopol}", delta_color="inverse")
        m1.metric("Total Pokok", f"Rp {df_txt['TOTAL_POKOK_TXT'].sum():,.0f}", f"Selisih: Rp {gap_pokok:,.0f}", delta_color="inverse")
        m2.metric("Total Denda", f"Rp {df_txt['TOTAL_DENDA_TXT'].sum():,.0f}", f"Selisih: Rp {gap_denda:,.0f}", delta_color="inverse")
        m3.metric("Grand Total", f"Rp {df_txt['TOTAL_ALL_TXT'].sum():,.0f}", f"Selisih: Rp {gap_total:,.0f}", delta_color="inverse")
        
        st.divider()

        # --- 5. TAMPILAN TAB ---
        tab1, tab2, tab3 = st.tabs(["✅ Ada di Keduanya", "⚠️ Ada di CERI saja", "⚠️ Ada di Splitzing saja"])

        with tab1:
            st.subheader("✅ Data ditemukan di CERI dan Splitzing")
            
            list_selisih = cocok[cocok['SELISIH_CHECK'] != 0]
            if not list_selisih.empty:
                st.error("🚨 **Ditemukan Perbedaan Nominal pada Nopol berikut:**")
                for _, row in list_selisih.iterrows():
                    st.write(f"👉 **{row['No Polisi']}** - Selisih: Rp {row['SELISIH_CHECK']:,.0f}")
            else:
                st.success("🎉 Tidak ada perbedaan nominal pada nopol yang cocok.")
            
            st.divider()

            def highlight_diff(row):
                return ['background-color: #ffcccc' if row.SELISIH_CHECK != 0 else '' for _ in row]

            df_display = cocok.drop(columns=['RAW_TEXT'], errors='ignore')
            st.dataframe(df_display.style.apply(highlight_diff, axis=1), use_container_width=True)
            st.metric("Total Nominal Cocok (TXT)", f"Rp {cocok['TOTAL_ALL_TXT'].sum():,.0f}")

        with tab2:
            st.subheader("⚠️ Ada di CERI (Excel) Tapi Tidak Ada di TXT")
            st.dataframe(hanya_excel, use_container_width=True)
            st.divider()
            st.subheader("💰 Rekapitulasi (Hanya di Excel)")
            e1, e2, e3 = st.columns(3)
            e1.metric("Pokok (KD+SW)", f"Rp {hanya_excel['POKOK_EXCEL'].sum():,.0f}")
            e2.metric("Denda (DD)", f"Rp {hanya_excel['DD'].sum():,.0f}")
            e3.metric("Total (Jumlah)", f"Rp {hanya_excel['Jumlah'].sum():,.0f}")

        with tab3:
            st.subheader("⚠️ Ada di Splitzing (TXT) Tapi Tidak Ada di Excel")
            
            # --- FITUR DOWNLOAD TXT ---
            if not hanya_txt.empty:
                txt_output = "\n".join(hanya_txt['RAW_TEXT'].tolist())
                st.download_button(
                    label="📥 Download Baris TXT Asli (Data Selisih)",
                    data=txt_output,
                    file_name="selisih_splitzing_only.txt",
                    mime="text/plain"
                )
            
            st.divider()
            st.dataframe(hanya_txt.drop(columns=['RAW_TEXT'], errors='ignore'), use_container_width=True)
            st.divider()
            st.subheader("💰 Rekapitulasi (Hanya di TXT)")
            t1, t2, t3 = st.columns(3)
            t1.metric("Total Pokok", f"Rp {hanya_txt['TOTAL_POKOK_TXT'].sum():,.0f}")
            t2.metric("Total Denda", f"Rp {hanya_txt['TOTAL_DENDA_TXT'].sum():,.0f}")
            t3.metric("Grand Total", f"Rp {hanya_txt['TOTAL_ALL_TXT'].sum():,.0f}")


