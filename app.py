import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import google.generativeai as genai
from geopy.geocoders import Nominatim
from io import BytesIO
import re

# ==========================================
# --- 1. KONFIGURASI HALAMAN & TEMA FUTURISTIK ---
# ==========================================
st.set_page_config(
    page_title="OPTIMA - AI Asset Intelligence",
    page_icon="⚡",
    layout="wide"
)

# CUSTOM CSS: UNIVERSAL FUTURISTIC CORPORATE (100% ADAPTIVE DARK & LIGHT MODE)
st.markdown("""
<style>
    /* 1. DESAIN KARTU KACA FUTURISTIK (UNIVERSAL GLASSMORPHISM) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(130, 140, 150, 0.08) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1.5px solid #d4af37 !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 20px rgba(212, 175, 55, 0.15) !important;
        padding: 18px !important;
        margin-bottom: 20px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(212, 175, 55, 0.35) !important;
        border-color: #f59e0b !important;
    }

    /* 2. TYPOGRAPHY & HERO BRANDING */
    h1, h2 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    h3, h4 {
        color: #d4af37 !important; 
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #d4af37;
        padding-bottom: 8px;
        margin-bottom: 14px;
        text-transform: uppercase;
    }

    /* 3. TOMBOL SCI-FI CORPORATE (GOLD & NAVY) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0b2545 0%, #1a4980 50%, #d4af37 100%) !important;
        color: #ffffff !important;
        border: 1px solid #d4af37 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(11, 37, 69, 0.3);
    }
    
    button[kind="primary"]:hover {
        opacity: 0.95;
        transform: scale(1.01);
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.6) !important;
    }
    
    button[kind="secondary"] {
        background: transparent !important;
        border: 1.5px solid #d4af37 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="secondary"]:hover {
        background: rgba(212, 175, 55, 0.15) !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.3) !important;
    }

    /* 4. TABS & EXPANDER YANG ELEGAN */
    .streamlit-expanderHeader {
        background: rgba(130, 140, 150, 0.08) !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"GSpread Error: {e}")
        return None

# FUNGSI PEMBERSIH JUDUL BAB (Agar Tidak Ganda di Excel/GSheet)
def clean_section_body(text):
    if not text:
        return ""
    lines = text.strip().split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip().startswith('#'):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return '\n'.join(lines).strip()

# ==========================================
# --- 2. SESSION STATE & DRAFT LOKAL ---
# ==========================================
if 'buffer_laporan' not in st.session_state: 
    st.session_state.buffer_laporan = []

if 'laporan_aktif' not in st.session_state:
    st.session_state.laporan_aktif = None

if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "najwa": {"password": "kuncijatim", "role": "admin", "nama": "Admin Pusat (Kamu)"},
        "1234": {"password": "jatimakmur", "role": "user", "nama": "Dafa"},
        "friska": {"password": "jatimakmur", "role": "user", "nama": "Friska"},
    }

if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.nama_user = ""

# ==========================================
# --- 3. SISTEM LOGIN & OPTIMA BRANDING ---
# ==========================================
# HERO SECTION BRANDING OPTIMA
st.markdown("<h3 style='text-align: center; color: #d4af37; margin-bottom: 0px; border-bottom: none;'>⚡ OPTIMA : AI ASSET INTELLIGENCE</h3>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-size: 2.8em; margin-top: 0px;'>Analyze. Value. Optimize.</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em; opacity: 0.85; margin-bottom: 25px;'>Platform Intelijen & Optimalisasi Pemanfaatan Aset Negara Berbasis Artificial Intelligence — DJKN / KPKNL</p>", unsafe_allow_html=True)
st.markdown("---")

if not st.session_state.is_logged_in:
    st.sidebar.subheader("🔐 Login Sistem OPTIMA")
    input_user = st.sidebar.text_input("Username:")
    input_pass = st.sidebar.text_input("Password:", type="password")
    
    if st.sidebar.button("Masuk / Login", type="primary", use_container_width=True):
        user_clean = input_user.strip().lower()
        pass_clean = input_pass.strip()
        
        if user_clean in st.session_state.users_db and st.session_state.users_db[user_clean]["password"] == pass_clean:
            st.session_state.is_logged_in = True
            st.session_state.username = user_clean
            st.session_state.role = st.session_state.users_db[user_clean]["role"]
            st.session_state.nama_user = st.session_state.users_db[user_clean]["nama"]
            st.rerun()
        else:
            st.sidebar.error("❌ Username atau Password salah!")
            
    st.warning("⚠️ Silakan login terlebih dahulu di menu sebelah kiri untuk mengakses platform OPTIMA.")
    st.stop()
else:
    with st.sidebar.container(border=True):
        st.markdown(f"👤 **{st.session_state.nama_user}**")
        badge_color = "#d4af37" if st.session_state.role == "admin" else "#3b82f6"
        st.markdown(f"🎯 Role: <span style='background-color:{badge_color}; color:#fff; padding:3px 10px; border-radius:20px; font-size:0.8em; font-weight:bold; letter-spacing:0.5px;'>{st.session_state.role.upper()}</span>", unsafe_allow_html=True)
    
    with st.sidebar.expander("⚙️ Pengaturan Akun (Ganti Username)"):
        new_usn_input = st.text_input("Username Baru:", placeholder="Ketik username baru...")
        confirm_pass_input = st.text_input("Konfirmasi Password Saat Ini:", type="password")
        
        if st.button("Simpan & Sync GSheet", type="primary", use_container_width=True):
            old_usn = st.session_state.username
            new_usn = new_usn_input.strip().lower()
            pass_conf = confirm_pass_input.strip()
            
            if not new_usn or not pass_conf:
                st.warning("Isi username baru dan password!")
            elif new_usn == old_usn:
                st.warning("Username baru sama dengan yang lama.")
            elif new_usn in st.session_state.users_db:
                st.error("Username sudah dipakai orang lain!")
            elif st.session_state.users_db[old_usn]["password"] != pass_conf:
                st.error("❌ Password konfirmasi salah!")
            else:
                with st.spinner("⏳ Menyinkronkan database GSheet..."):
                    try:
                        user_data = st.session_state.users_db.pop(old_usn)
                        st.session_state.users_db[new_usn] = user_data
                        st.session_state.username = new_usn
                        
                        client = get_gspread_client()
                        if client:
                            sheet = client.open("Database_Aset_Negara").sheet1
                            all_vals = sheet.get_all_values()
                            headers = [h.strip().lower() for h in all_vals[0]]
                            if 'username' in headers:
                                col_idx = headers.index('username') + 1
                                col_vals = sheet.col_values(col_idx)
                                for r_idx, val in enumerate(col_vals):
                                    if r_idx > 0 and str(val).strip().lower() == old_usn:
                                        sheet.update_cell(r_idx + 1, col_idx, new_usn)
                        
                        st.success(f"✅ Berhasil ganti username ke '{new_usn}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal sync GSheet: {e}")
        
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.is_logged_in = False
        st.rerun()

# ==========================================================
# --- ASISTEN OPTIMA DI SIDEBAR ---
# ==========================================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 OPTIMA Assistant")
st.sidebar.write("Asisten intelijen AI untuk memoles narasi atau konsultasi keputusan HBU.")

opsi_ai_sidebar = st.sidebar.selectbox(
    "Pilih Mode Asisten:", 
    [
        "✨ Parafrase (Bahasa Kedinasan)", 
        "🔍 Perbaiki Tata Bahasa (EYD)", 
        "📉 Buat Lebih Ringkas & Padat", 
        "💬 Tanya Bebas ke AI"
    ]
)

teks_input_sidebar = st.sidebar.text_area(
    "Ketik teks / pertanyaanmu di sini:", 
    height=110, 
    placeholder="Contoh: Mengapa aset ini lebih disarankan untuk sewa daripada dilelang?"
)

if st.sidebar.button("⚡ Proses AI Sekarang", type="primary", use_container_width=True):
    if not teks_input_sidebar.strip():
        st.sidebar.warning("⚠️ Ketik teksnya dulu ya!")
    else:
        with st.sidebar.status("⏳ OPTIMA AI sedang berpikir..."):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                if "Parafrase" in opsi_ai_sidebar:
                    prompt_sidebar = f"Ubah teks berikut menjadi bahasa laporan kedinasan yang sangat formal, profesional, baku, dan cocok untuk dokumen appraisal properti resmi: '{teks_input_sidebar}'"
                elif "Tata Bahasa" in opsi_ai_sidebar:
                    prompt_sidebar = f"Perbaiki tata bahasa, struktur kalimat, dan EYD dari teks berikut agar baku dan enak dibaca tanpa mengubah maksud aslinya: '{teks_input_sidebar}'"
                elif "Ringkas" in opsi_ai_sidebar:
                    prompt_sidebar = f"Buat ringkasan yang padat, lugas, dan langsung pada inti informasi penting dari teks berikut: '{teks_input_sidebar}'"
                else:
                    prompt_sidebar = f"Jawab pertanyaan berikut secara singkat, padat, dan profesional dalam konteks penilaian dan optimalisasi aset properti (HBU): '{teks_input_sidebar}'"
                
                semua_model = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model_kandidat = sorted([m for m in semua_model if not any(x in m.lower() for x in ['tts', 'audio', 'vision', 'embedding', 'aqa', 'imagen'])], key=lambda x: ('flash' in x, '1.5' in x), reverse=True)
                
                res_sidebar = None
                for nama_model in model_kandidat:
                    try:
                        model_sidebar = genai.GenerativeModel(model_name=nama_model)
                        res = model_sidebar.generate_content(prompt_sidebar)
                        if res and res.text:
                            res_sidebar = res
                            break
                    except: continue
                
                if res_sidebar and res_sidebar.text:
                    st.session_state.hasil_sidebar = res_sidebar.text
                else:
                    st.sidebar.error("❌ Gagal mendapatkan respons AI.")
            except Exception as e:
                st.sidebar.error(f"❌ Error AI: {e}")

if "hasil_sidebar" in st.session_state:
    st.sidebar.markdown("💡 **Hasil OPTIMA Assistant:**")
    with st.sidebar.container(border=True):
        st.sidebar.markdown(st.session_state.hasil_sidebar)
    with st.sidebar.expander("📋 Klik di sini untuk Copas Teks"):
        st.text_area(
            "Blok teks di bawah ini (Ctrl+A -> Ctrl+C):", 
            value=st.session_state.hasil_sidebar, 
            height=120, 
            label_visibility="collapsed"
        )
    if st.sidebar.button("🗑️ Bersihkan Hasil", use_container_width=True):
        del st.session_state.hasil_sidebar
        st.rerun()

# ==========================================
# --- 4. NAVIGASI MODUL (TAHAP 1 FOKUS TAB 1) ---
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚡ 1. Intelligence Generator", "📝 2. Review & Refinement Center (Next)", "📈 3. Asset Repository (Next)"])

# ==========================================
# --- TAB 1: INTELLIGENCE GENERATOR ---
# ==========================================
with tab1:
    st.markdown("### 🔍 Parameter Input & Lokasi Aset")
    
    col1, col2 = st.columns(2)
    with col1:
        alamat_aset = st.text_input(
            "📍 Alamat Lengkap Aset:", 
            value=st.session_state.laporan_aktif['alamat'] if st.session_state.laporan_aktif else "", 
            placeholder="Contoh: Ds. Awang-awang, Kec. Mojosari, Kab. Mojokerto"
        )
        koordinat_lat = st.number_input(
            "🌐 Latitude (Garis Lintang):", 
            value=st.session_state.laporan_aktif['lat'] if st.session_state.laporan_aktif else None, 
            format="%.6f", 
            placeholder="Contoh: -7.xxxxxx"
        )
        koordinat_lng = st.number_input(
            "🌐 Longitude (Garis Bujur):", 
            value=st.session_state.laporan_aktif['lng'] if st.session_state.laporan_aktif else None, 
            format="%.6f", 
            placeholder="Contoh: 112.xxxxxx"
        )

    with col2:
        informasi_tambahan = st.text_area(
            "📝 Catatan Kondisi Lapangan & Informasi Tambahan (Opsional):", 
            value="", 
            placeholder="Contoh: Berada di pinggir jalan raya utama, bentuk tanah ngantong, ada sisa bangunan lama...",
            height=130
        )

    st.markdown("---")

    if st.button("⚡ Generate OPTIMA Analysis & Score", type="primary", use_container_width=True):
        if not alamat_aset or koordinat_lat is None or koordinat_lng is None:
            st.error("⚠️ Mohon lengkapi Alamat Lengkap dan Koordinat (Latitude & Longitude) terlebih dahulu!")
            st.stop()
            
        with st.spinner("⏳ Memindai satelit, menghitung OPTIMA Score, & meracik rekomendasi HBU..."):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            except Exception as e:
                st.error(f"❌ API Key Error: {e}")
                st.stop()

            try:
                geolocator = Nominatim(user_agent="optima_asset_intelligence", timeout=10)
                lokasi_nyata = geolocator.reverse(f"{koordinat_lat}, {koordinat_lng}", exactly_one=True)
                data_peta = lokasi_nyata.raw['address']
                
                nama_jalan_asli = data_peta.get('road', data_peta.get('pedestrian', data_peta.get('suburb', 'Jalan Utama/Lokal di koordinat ini')))
                kecamatan_asli = data_peta.get('suburb', data_peta.get('city_district', data_peta.get('village', 'Kecamatan setempat')))
                kabupaten_asli = data_peta.get('city', data_peta.get('county', 'Kabupaten/Kota setempat'))
                
                info_validasi_peta = f"Jalan Depan Aset: '{nama_jalan_asli}' | Wilayah: {kecamatan_asli}, {kabupaten_asli}"
            except Exception as e:
                nama_jalan_asli = "Jalan Raya/Lokal di koordinat ini"
                kecamatan_asli = "Kecamatan setempat"
                kabupaten_asli = "Kabupaten setempat"
                info_validasi_peta = f"Koordinat GPS: {koordinat_lat}, {koordinat_lng} (Gunakan pemetaan internal AI)"

            # PROMPT MASTER OPTIMA DENGAN PENAMBAHAN METRIK SKOR & CONFIDENCE
            prompt = f"""
            Kamu adalah Penilai Aset Negara (Appraiser) dan AI Asset Intelligence Senior di DJKN/KPKNL. Tugasmu membuat laporan analisis aset properti dan menghitung kelayakan pemanfaatannya (OPTIMA Score).

            DATA TARGET ASET:
            - Alamat/Lokasi: {alamat_aset}
            - Koordinat Titik: {koordinat_lat}, {koordinat_lng}
            - Catatan Lapangan: {informasi_tambahan if informasi_tambahan else "Tidak ada catatan khusus."}
            - Data Peta Satelit: {info_validasi_peta}

            INSTRUKSI TEKNIS DAN FORMAT LAPORAN (WAJIB DIPATUHI):
            1. BAHASA LUGAS & ANALISIS JALAN ASLI: Menganalisis berdasarkan kelas jalan "{nama_jalan_asli}". Jelaskan dampaknya terhadap nilai komersial aset dengan bahasa membumi dan profesional.
            2. ANTI HALUSINASI JARAK POI: Aset ini di {kecamatan_asli}, {kabupaten_asli}. Jangan manipulasi jarak! Tuliskan jarak riil apa adanya.
            3. ANTI BIAS HUNIAN: Nilai potensi komersial, perdagangan, jasa, ruko, gudang, wisata, atau lelang.
            4. PEMISAH BAB: Untuk keperluan parsing, WAJIB taruh kode ini tepat di antara setiap bab/bagian laporan:
               ---SECTION---

            SUSUN LAPORAN DENGAN URUTAN PERSIS SEPERTI INI:

            ### ⭐ OPTIMA SCORE & CONFIDENCE METER
            - **OPTIMA Score:** [Tulis angka saja antara 50 sampai 98, contoh: 86]
            - **Kategori Potensi:** [Pilih salah satu: Potensi Tinggi / Potensi Menengah / Potensi Spesifik]
            - **Rekomendasi Utama:** [Pilih salah satu tegas: SEWA KOMERSIAL / KERJA SAMA PEMANFAATAN (KSP) / PENJUALAN LELANG]
            - **Confidence Sewa:** [Angka probabilitas %, misal: 85]
            - **Confidence KSP:** [Angka probabilitas %, misal: 70]
            - **Confidence Lelang:** [Angka probabilitas %, misal: 40]
            - **Analisis Singkat Skor:** (1-2 kalimat mengapa aset ini mendapatkan skor dan probabilitas tersebut berdasarkan lokasinya).

            ---SECTION---

            ### 💰 ESTIMASI HARGA PASAR (INDIKATIF)
            - **Estimasi Harga Tanah:** Rp [X] - Rp [Y] per m² (Penjelasan singkat pasaran harga tanah di sekitar lokasi ini).
            - **Estimasi Harga Bangunan:** Rp [X] - Rp [Y] per m² (Jika ada bangunan/puing jelaskan, jika tanah kosong jelaskan biaya bangun standar per m² di area ini).
            - *Disclaimer Resmi:* Angka di atas merupakan estimasi awal berbasis data analitis AI untuk gambaran kasar, bukan merupakan nilai limit lelang atau nilai appraisal resmi. Diperlukan survei dan penilaian fisik langsung di lapangan.

            ---SECTION---

            ### 🏘️ KARAKTERISTIK DAN DINAMIKA KAWASAN
            - **Klasifikasi & Tata Ruang Kawasan:** (Jelaskan apakah area ini kawasan perdagangan, permukiman, industri, wisata, atau campuran).
            - **Penggerak Ekonomi Lokal:** (Bisnis atau aktivitas ekonomi apa yang ramai dan hidup di area sekitar koordinat ini).
            - **Analisis Lingkungan & Sosial:** (Kondisi keamanan dan lingkungan sekitarnya).

            ---SECTION---

            ### 🛣️ EVALUASI AKSESIBILITAS DAN KONEKTIVITAS
            - **Kondisi Akses Mikro (Jalan Depan Aset):** (Sebutkan nama jalan "{nama_jalan_asli}". Jelaskan perkiraan lebarnya dalam meter berdasarkan kelas jalan tersebut, apakah truk berat/kendaraan roda empat bisa simpangan, dan kondisi fisik perkerasannya).
            - **Konektivitas Makro & Titik Macet:** (Jalur penghubung ke jalan utama/arteri serta titik macet di jam sibuk).

            ---SECTION---

            ### 📍 PEMETAAN FASILITAS TERDEKAT (POI)
            (Wajib tampilkan MINIMAL 3 FASILITAS untuk setiap kategori dalam bentuk TABEL MARKDOWN 5 kolom):

            #### A. Fasilitas Pendidikan
            | Nama Fasilitas | Estimasi Jarak | ETA Motor | ETA Mobil | Link Rute |
            | :--- | :---: | :---: | :---: | :---: |
            | [Nama Sekolah/Kampus 1] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Sekolah/Kampus 2] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Sekolah/Kampus 3] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |

            #### B. Pusat Perbelanjaan & Niaga
            | Nama Fasilitas | Estimasi Jarak | ETA Motor | ETA Mobil | Link Rute |
            | :--- | :---: | :---: | :---: | :---: |
            | [Nama Pasar/Mall/Supermarket 1] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Pasar/Mall/Supermarket 2] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Pasar/Mall/Supermarket 3] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |

            #### C. Fasilitas Kesehatan
            | Nama Fasilitas | Estimasi Jarak | ETA Motor | ETA Mobil | Link Rute |
            | :--- | :---: | :---: | :---: | :---: |
            | [Nama RS/Puskesmas/Klinik 1] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama RS/Puskesmas/Klinik 2] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama RS/Puskesmas/Klinik 3] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |

            #### D. Akses Tol & Simpul Transportasi
            | Nama Fasilitas | Estimasi Jarak | ETA Motor | ETA Mobil | Link Rute |
            | :--- | :---: | :---: | :---: | :---: |
            | [Nama Gerbang Tol/Terminal/Stasiun 1] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Gerbang Tol/Terminal/Stasiun 2] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Gerbang Tol/Terminal/Stasiun 3] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |

            #### E. Tempat Ibadah
            | Nama Fasilitas | Estimasi Jarak | ETA Motor | ETA Mobil | Link Rute |
            | :--- | :---: | :---: | :---: | :---: |
            | [Nama Masjid/Gereja/Vihara 1] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Masjid/Gereja/Vihara 2] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Masjid/Gereja/Vihara 3] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |

            #### F. Area Publik & Destinasi Wisata
            | Nama Fasilitas | Estimasi Jarak | ETA Motor | ETA Mobil | Link Rute |
            | :--- | :---: | :---: | :---: | :---: |
            | [Nama Alun-alun/Taman/Wisata 1] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Alun-alun/Taman/Wisata 2] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |
            | [Nama Alun-alun/Taman/Wisata 3] | ~[X] km | ~[X] menit | ~[Y] menit | [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+TEMPAT+GANTI+SPASI+PLUS]) |

            ---SECTION---

            ### ⚖️ ANALISIS KRITIS POTENSI & RISIKO (SWOT RINGKAS)
            | 💪 Kekuatan & Peluang (Strengths & Opportunities) | ⚠️ Kelemahan & Risiko (Weaknesses & Threats) |
            | :--- | :--- |
            | [Poin 1 SO]: ....................... | [Poin 1 WT]: ....................... |
            | [Poin 2 SO]: ....................... | [Poin 2 WT]: ....................... |
            | [Poin 3 SO]: ....................... | [Poin 3 WT]: ....................... |

            ---SECTION---

            ### 🎯 REKOMENDASI PEMANFAATAN OPTIMAL (HIGHEST AND BEST USE)
            - **Opsi Pemanfaatan PALING MUNGKIN (Top 2-3 Opsi):** (Rekomendasi selain hunian, misal untuk perdagangan, jasa, ruko, atau gudang skala kecil beserta alasannya).
            - **Opsi Pemanfaatan PALING TIDAK MUNGKIN (1 Opsi):** (1 opsi yang tidak cocok beserta alasan logisnya).

            ---SECTION---

            ### 📝 KESIMPULAN AKHIR
            (Buat 1 paragraf kesimpulan eksekutif yang lugas, padat, dan langsung pada intinya. Wajib merangkum 3 hal berikut dalam alur yang natural:
            1. **Potensi:** Secara keseluruhan, aset ini paling potensial dikembangkan sebagai apa?
            2. **Alasan Potensi:** Mengapa potensial? (Sebutkan keunggulan utama berdasarkan fakta analisis di atas).
            3. **Rekomendasi Skema Optimalisasi:** Secara tegas pilih skemanya: **Penjualan Lelang**, **Penyewaan Komersial (Sewa)**, atau **Kerja Sama Pemanfaatan (KSP)**).

            PERINGATAN KERAS: JANGAN TULIS PROSES BERPIKIRMU! JANGAN TULIS TEKS BAHASA INGGRIS APA PUN!
            LANGSUNG KELUARKAN LAPORAN DALAM BAHASA INDONESIA SEKARANG JUGA, DIAWALI PERSIS DENGAN TEKS:
            ### ⭐ OPTIMA SCORE & CONFIDENCE METER
            """

            config_patuh = {"temperature": 0.2}
            semua_model = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_kandidat = sorted([m for m in semua_model if not any(x in m.lower() for x in ['tts', 'audio', 'vision', 'embedding', 'aqa', 'imagen'])], key=lambda x: ('1.5' in x, 'flash' in x), reverse=True)
            
            response = None
            pesan_error_terakhir = "Tidak ada model yang kompatibel."
            
            for nama_model in model_kandidat:
                try:
                    model = genai.GenerativeModel(model_name=nama_model, generation_config=config_patuh)
                    res = model.generate_content(prompt)
                    if res and res.text and "---SECTION---" in res.text:
                        response = res
                        break 
                except Exception as e:
                    pesan_error_terakhir = str(e)
                    continue

            if response and response.text:
                teks_laporan = response.text
                if "### ⭐ OPTIMA SCORE & CONFIDENCE METER" in teks_laporan:
                    teks_laporan = "### ⭐ OPTIMA SCORE & CONFIDENCE METER" + teks_laporan.split("### ⭐ OPTIMA SCORE & CONFIDENCE METER")[1]
                
                bagian = teks_laporan.split("---SECTION---")
                
                # FUNGSI PARSING ANGKA SKOR & CONFIDENCE DARI TEKS AI
                def extract_val(text, label, default="0"):
                    try:
                        match = re.search(r'\*\*' + label + r'\*\*:\s*([^\n]+)', text, re.IGNORECASE)
                        return match.group(1).strip() if match else default
                    except: return default

                def extract_num(text, label, default=0):
                    val = extract_val(text, label)
                    nums = re.findall(r'\d+', val)
                    return int(nums[0]) if nums else default

                skor_teks = clean_section_body(bagian[0]) if len(bagian) > 0 else ""
                
                st.session_state.laporan_aktif = {
                    "alamat": alamat_aset,
                    "lat": koordinat_lat,
                    "lng": koordinat_lng,
                    "info_peta": info_validasi_peta,
                    # Skor dan Metrik
                    "optima_score": extract_num(skor_teks, "OPTIMA Score", 80),
                    "optima_kategori": extract_val(skor_teks, "Kategori Potensi", "Potensi Menengah"),
                    "optima_rekomendasi": extract_val(skor_teks, "Rekomendasi Utama", "SEWA KOMERSIAL"),
                    "conf_sewa": extract_num(skor_teks, "Confidence Sewa", 70),
                    "conf_ksp": extract_num(skor_teks, "Confidence KSP", 60),
                    "conf_lelang": extract_num(skor_teks, "Confidence Lelang", 40),
                    "analisis_skor": clean_section_body(skor_teks),
                    # Bagian Laporan
                    "estimasi": clean_section_body(bagian[1]) if len(bagian) > 1 else "",
                    "karakteristik": clean_section_body(bagian[2]) if len(bagian) > 2 else "",
                    "akses": clean_section_body(bagian[3]) if len(bagian) > 3 else "",
                    "poi": clean_section_body(bagian[4]) if len(bagian) > 4 else "",
                    "swot": clean_section_body(bagian[5]) if len(bagian) > 5 else "",
                    "rekomendasi": clean_section_body(bagian[6]) if len(bagian) > 6 else "",
                    "kesimpulan": clean_section_body(bagian[7]) if len(bagian) > 7 else "",
                }
                st.success("✅ OPTIMA Asset Intelligence Berhasil Selesai Dihitung!")
            else:
                st.error(f"❌ Gagal memproses laporan. Detail Error: {pesan_error_terakhir}")

    # TAMPILAN DASHBOARD HERO & KARTU HASIL AI
    if st.session_state.laporan_aktif:
        lap = st.session_state.laporan_aktif
        
        # 1. HERO CARD : OPTIMA SCORE & CONFIDENCE METER (PALING ATAS)
        with st.container(border=True):
            st.markdown("### ⭐ OPTIMA EXECUTIVE SUMMARY & SCORE")
            
            col_skor, col_rekom = st.columns([0.35, 0.65])
            with col_skor:
                st.markdown(f"<div style='text-align: center; padding: 10px; border: 2px dashed #d4af37; border-radius: 12px;'>"
                            f"<span style='font-size: 0.9em; opacity: 0.8;'>OPTIMA SCORE</span><br>"
                            f"<span style='font-size: 3.5em; font-weight: 800; color: #d4af37;'>{lap['optima_score']}</span><br>"
                            f"<span style='font-size: 0.9em; font-weight: bold;'>{lap['optima_kategori']}</span>"
                            f"</div>", unsafe_allow_html=True)
            
            with col_rekom:
                st.markdown(f"#### 🎯 REKOMENDASI TERBAIK : **{lap['optima_rekomendasi']}**")
                st.write("**Probabilitas Kelayakan Skema (Confidence Meter):**")
                
                # Progress Bar untuk setiap skema
                st.write(f"🏢 **Sewa Komersial ({lap['conf_sewa']}%)**")
                st.progress(min(max(lap['conf_sewa'], 0), 100) / 100)
                
                st.write(f"🤝 **Kerja Sama Pemanfaatan / KSP ({lap['conf_ksp']}%)**")
                st.progress(min(max(lap['conf_ksp'], 0), 100) / 100)
                
                st.write(f"🔨 **Penjualan Lelang ({lap['conf_lelang']}%)**")
                st.progress(min(max(lap['conf_lelang'], 0), 100) / 100)
            
            st.divider()
            st.markdown("#### 💡 Analisis Kelayakan Skor:")
            st.markdown(lap['analisis_skor'])

        # 2. IDENTITAS & LOKASI ASET
        with st.container(border=True):
            st.markdown("### 📌 IDENTITAS & LOKASI ASET")
            st.write(f"**Alamat Lengkap:** {lap['alamat']}")
            st.write(f"**Validasi Peta Satelit:** {lap['info_peta']}")
            st.write("**Koordinat GPS:**")
            st.code(f"{lap['lat']}, {lap['lng']}", language="text")
            
            col_map, col_sat, col_earth = st.columns(3)
            url_maps = f"https://www.google.com/maps/search/?api=1&query={lap['lat']},{lap['lng']}"
            url_satelit = f"https://www.google.com/maps/search/?api=1&query={lap['lat']},{lap['lng']}&basemap=satellite"
            url_earth = f"https://earth.google.com/web/search/{lap['lat']}%2C+{lap['lng']}"
            
            with col_map: st.link_button("🗺️ Peta Jalan (Pin)", url_maps, use_container_width=True)
            with col_sat: st.link_button("🛰️ Satelit (Pin Merah)", url_satelit, use_container_width=True)
            with col_earth: st.link_button("🌍 Google Earth 3D", url_earth, use_container_width=True)

        # 3. KARTU NARASI PER BAB
        with st.container(border=True):
            st.markdown("### 💰 ESTIMASI HARGA PASAR (INDIKATIF)")
            st.markdown(lap['estimasi'])
        with st.container(border=True):
            st.markdown("### 🏘️ KARAKTERISTIK DAN DINAMIKA KAWASAN")
            st.markdown(lap['karakteristik'])
        with st.container(border=True):
            st.markdown("### 🛣️ EVALUASI AKSESIBILITAS DAN KONEKTIVITAS")
            st.markdown(lap['akses'])
        with st.container(border=True):
            st.markdown("### 📍 PEMETAAN FASILITAS TERDEKAT (POI) [CONTEKAN READ-ONLY]")
            st.markdown(lap['poi'])
        with st.container(border=True):
            st.markdown("### ⚖️ ANALISIS KRITIS POTENSI & RISIKO (SWOT) [CONTEKAN READ-ONLY]")
            st.markdown(lap['swot'])
        with st.container(border=True):
            st.markdown("### 🎯 REKOMENDASI PEMANFAATAN OPTIMAL (HIGHEST AND BEST USE)")
            st.markdown(lap['rekomendasi'])
        with st.container(border=True):
            st.markdown("### 📝 KESIMPULAN AKHIR")
            st.markdown(lap['kesimpulan'])

        st.divider()
        nama_aset = st.text_input("📝 Beri Nama untuk Aset Ini (Agar mudah dicari di Tab Review):", value=lap['alamat'], key="nama_aset_review")
        
        col_btn1, col_btn2 = st.columns([0.8, 0.2])
        with col_btn1:
            if st.button("📥 Simpan ke Review & Edit", type="secondary", use_container_width=True):
                if not nama_aset.strip():
                    st.warning("Mohon isi Nama Aset terlebih dahulu.")
                else:
                    st.session_state.buffer_laporan.append({
                        "nama": nama_aset,
                        "lat": lap['lat'],
                        "lng": lap['lng'],
                        # Menyimpan skor dan probabilitas
                        "optima_score": lap['optima_score'],
                        "optima_kategori": lap['optima_kategori'],
                        "optima_rekomendasi": lap['optima_rekomendasi'],
                        "conf_sewa": lap['conf_sewa'],
                        "conf_ksp": lap['conf_ksp'],
                        "conf_lelang": lap['conf_lelang'],
                        "data": {
                            "estimasi": lap['estimasi'],
                            "karakteristik": lap['karakteristik'],
                            "akses": lap['akses'],
                            "rekomendasi": lap['rekomendasi'],
                            "kesimpulan": lap['kesimpulan'],
                            "poi_contekan": lap['poi'],
                            "swot_contekan": lap['swot']
                        }
                    })
                    st.success("✅ Berhasil disimpan ke Review! Pengerjaan Modul 2 akan kita lanjutkan setelah verifikasi Tahap 1 ini.")
        with col_btn2:
            if st.button("🗑️ Hapus Draft", use_container_width=True):
                st.session_state.laporan_aktif = None
                st.rerun()

# ==========================================
# --- TAB 2 & TAB 3 (PLACEHOLDER TAHAP SELANJUTNYA) ---
# ==========================================
with tab2:
    st.info("💡 **Modul 2: Review & Refinement Center** sedang dalam tahap sinkronisasi arsitektur OPTIMA. Kita akan membangun antarmukanya setelah Modul 1 terverifikasi.")

with tab3:
    st.info("💡 **Modul 3: Executive Dashboard & Asset Repository** akan kita bangun dengan 4 KPI Cards (Total Aset, Sewa, KSP, Lelang) di tahap akhir.")
