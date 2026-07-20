import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import google.generativeai as genai
from geopy.geocoders import Nominatim
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Analisis Aset Properti Pro",
    page_icon="🏢",
    layout="wide"
)

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

# --- 2. SESSION STATE ---
if 'buffer_laporan' not in st.session_state: 
    st.session_state.buffer_laporan = []

# --- 3. SISTEM LOGIN MULTI-USER & ASISTEN SIDEBAR ---
st.title("🏢 Sistem Analisis & Appraisal Aset Properti")
st.write("Aplikasi internal untuk generate laporan analisis lingkungan, estimasi harga, dan aksesibilitas sebuah aset secara mendalam.")
st.markdown("---")

# DAFTAR AKUN PENGGUNA (Bisa kamu tambah atau ubah passwordnya bebas)
DATABASE_USER = {
    "najwa": {"password": "kuncijatim", "role": "admin", "nama": "Admin Pusat (Kamu)"},
    "1234": {"password": "jatimakmur", "role": "user", "nama": "Dafa"},
    "friska": {"password": "jatimakmur", "role": "user", "nama": "Friska"},
}

# Inisialisasi status login di memori browser
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.nama_user = ""

# TAMPILAN FORM LOGIN
if not st.session_state.is_logged_in:
    st.sidebar.subheader("🔐 Login Sistem Internal")
    input_user = st.sidebar.text_input("Username:")
    input_pass = st.sidebar.text_input("Password:", type="password")
    
    if st.sidebar.button("Masuk / Login", type="primary", use_container_width=True):
        if input_user in DATABASE_USER and DATABASE_USER[input_user]["password"] == input_pass:
            st.session_state.is_logged_in = True
            st.session_state.username = input_user
            st.session_state.role = DATABASE_USER[input_user]["role"]
            st.session_state.nama_user = DATABASE_USER[input_user]["nama"]
            st.rerun()
        else:
            st.sidebar.error("❌ Username atau Password salah!")
            
    st.warning("⚠️ Silakan login terlebih dahulu di menu sebelah kiri untuk mengakses sistem appraisal.")
    st.stop()
else:
    # TAMPILAN JIKA SUDAH LOGIN DI SIDEBAR
    st.sidebar.success(f"👤 **{st.session_state.nama_user}**\n\n🎯 Role: **{st.session_state.role.upper()}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.is_logged_in = False
        st.rerun()

# ==========================================================
# --- ASISTEN PARAFRASE & TANYA AI DI SIDEBAR ---
# ==========================================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Asisten Parafrase AI")
st.sidebar.write("Rapikan kalimat kasar atau tanya AI tanpa meninggalkan halaman edit.")

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
    height=120, 
    placeholder="Contoh: Tanah ini bentuknya ngantong dan lokasinya agak masuk ke dalam gg..."
)

if st.sidebar.button("⚡ Proses AI Sekarang", type="primary", use_container_width=True):
    if not teks_input_sidebar.strip():
        st.sidebar.warning("⚠️ Ketik teksnya dulu ya!")
    else:
        with st.sidebar.status("⏳ AI sedang berpikir..."):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                if "Parafrase" in opsi_ai_sidebar:
                    prompt_sidebar = f"Ubah teks berikut menjadi bahasa laporan kedinasan yang sangat formal, profesional, baku, dan cocok untuk dokumen appraisal properti resmi: '{teks_input_sidebar}'"
                elif "Tata Bahasa" in opsi_ai_sidebar:
                    prompt_sidebar = f"Perbaiki tata bahasa, struktur kalimat, dan EYD dari teks berikut agar baku dan enak dibaca tanpa mengubah maksud aslinya: '{teks_input_sidebar}'"
                elif "Ringkas" in opsi_ai_sidebar:
                    prompt_sidebar = f"Buat ringkasan yang padat, lugas, dan langsung pada inti informasi penting dari teks berikut: '{teks_input_sidebar}'"
                else:
                    prompt_sidebar = f"Jawab pertanyaan berikut secara singkat, padat, dan profesional dalam konteks penilaian dan optimalisasi aset properti: '{teks_input_sidebar}'"
                
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
    st.sidebar.markdown("💡 **Hasil AI (Klik ikon copas di kanan kotak):**")
    st.sidebar.code(st.session_state.hasil_sidebar, language="text")
    if st.sidebar.button("🗑️ Bersihkan Hasil", use_container_width=True):
        del st.session_state.hasil_sidebar
        st.rerun()

# --- 4. TAB SETUP ---
tab1, tab2, tab3 = st.tabs(["🚀 1. Generate", "📝 2. Review & Edit", "💾 3. Database"])

# ==========================================
# --- TAB 1: GENERATE ---
# ==========================================
with tab1:
    st.header("Generate Laporan Baru")
    
    col1, col2 = st.columns(2)
    with col1:
        alamat_aset = st.text_input(
            "📍 Alamat Lengkap Aset:", 
            value="", 
            placeholder="Contoh: Ds. Awang-awang, Kec. Mojosari, Kab. Mojokerto"
        )
        koordinat_lat = st.number_input(
            "🌐 Latitude (Garis Lintang):", 
            value=None, 
            format="%.6f", 
            placeholder="Contoh: -7.xxxxxx"
        )
        koordinat_lng = st.number_input(
            "🌐 Longitude (Garis Bujur):", 
            value=None, 
            format="%.6f", 
            placeholder="Contoh: 112.xxxxxx"
        )

    with col2:
        informasi_tambahan = st.text_area(
            "📝 Catatan Kondisi Lapangan & Informasi Tambahan (Opsional):", 
            value="", 
            placeholder="Contoh: Berada di pinggir jalan raya, bentuk tanah ngantong, ada sisa bangunan...",
            height=130
        )

    st.markdown("---")

    if st.button("🚀 Generate Laporan Analisis Mendalam", type="primary", use_container_width=True):
        if not alamat_aset or koordinat_lat is None or koordinat_lng is None:
            st.error("⚠️ Mohon lengkapi Alamat Lengkap dan Koordinat (Latitude & Longitude) terlebih dahulu!")
            st.stop()
            
        with st.spinner("⏳ Memindai koordinat satelit, melacak nama jalan & wilayah, serta menyusun tabel analisis..."):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            except Exception as e:
                st.error(f"❌ API Key Error: {e}")
                st.stop()

            # LANGKAH 1: GEOLOCATION
            try:
                geolocator = Nominatim(user_agent="appraisal_aset_djkn_pro", timeout=10)
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

            # LANGKAH 2: PROMPT MASTER ANTI-HALUSINASI & ANTI-BAHASA INGGRIS
            prompt = f"""
            Kamu adalah Penilai Aset Negara (Appraiser) DJKN/KPKNL. Tugasmu membuat laporan analisis aset properti yang LUGAS, REALISTIS, DAN MEMBUMI (hindari bahasa akademis tinggi, ganti dengan bahasa sehari-hari yang profesional).

            DATA TARGET ASET:
            - Alamat/Lokasi: {alamat_aset}
            - Koordinat Titik: {koordinat_lat}, {koordinat_lng}
            - Catatan Lapangan: {informasi_tambahan if informasi_tambahan else "Tidak ada catatan khusus."}
            
            DATA VALIDASI SATELIT (NYATA DARI PETA - ACUAN MUTLAK):
            - {info_validasi_peta}

            INSTRUKSI TEKNIS DAN FORMAT LAPORAN (WAJIB DIPATUHI):
            1. BAHASA LUGAS & ANALISIS JALAN ASLI: Karena data satelit mengungkap aset berada di jalan "{nama_jalan_asli}", kamu WAJIB menganalisis berdasarkan kelas jalan tersebut! Perkirakan lebarnya secara logis dan jelaskan dampaknya terhadap nilai komersial aset!
            2. ANTI HALUSINASI JARAK POI: Aset ini berada di {kecamatan_asli}, {kabupaten_asli}. JANGAN memanipulasi jarak! Jika fasilitas seperti Mall atau Rumah Sakit terdekat letaknya di pusat kota yang berjarak 15 km atau 30 km dari {kecamatan_asli}, tuliskan jujur 15 km atau 30 km! Carikan fasilitas yang BENAR-BENAR REAL di sekitar wilayah tersebut.
            3. ANTI BIAS HUNIAN: Nilai potensi komersial, perdagangan, jasa, gudang, atau lelang.
            4. PEMISAH BAB: Untuk keperluan tampilan website, WAJIB taruh kode ini tepat di antara setiap bab/bagian laporan:
               ---SECTION---

            SUSUN LAPORAN DENGAN URUTAN PERSIS SEPERTI INI:

            ### 💰 ESTIMASI HARGA PASAR (INDIKATIF)
            - **Estimasi Harga Tanah:** Rp [X] - Rp [Y] per m² (Penjelasan singkat pasaran harga tanah di sekitar lokasi/kecamatan ini).
            - **Estimasi Harga Bangunan:** Rp [X] - Rp [Y] per m² (Jika ada bangunan/puing jelaskan, jika tanah kosong jelaskan biaya bangun standar per m² di area ini).
            - *Disclaimer Resmi:* Angka di atas merupakan estimasi awal berbasis data analitis AI untuk gambaran kasar, bukan merupakan nilai limit lelang atau nilai appraisal resmi. Diperlukan survei dan penilaian fisik langsung di lapangan.

            ---SECTION---

            ### 🏘️ KARAKTERISTIK DAN DINAMIKA KAWASAN
            - **Klasifikasi & Tata Ruang Kawasan:** (Jelaskan dengan bahasa lugas apakah area ini kawasan perdagangan, permukiman, industri, atau campuran).
            - **Penggerak Ekonomi Lokal:** (Bisnis atau aktivitas ekonomi apa yang ramai dan hidup di area sekitar koordinat ini).
            - **Analisis Lingkungan & Sosial:** (Kondisi keamanan dan lingkungan sekitarnya).

            ---SECTION---

            ### 🛣️ EVALUASI AKSESIBILITAS DAN KONEKTIVITAS
            - **Kondisi Akses Mikro (Jalan Depan Aset):** (WAJIB BERDASARKAN DATA SATELIT: Sebutkan nama jalan "{nama_jalan_asli}". Jelaskan perkiraan lebarnya dalam meter berdasarkan kelas jalan tersebut, apakah truk berat/kendaraan roda empat bisa simpangan, dan kondisi fisik perkerasannya).
            - **Konektivitas Makro & Titik Macet:** (Jalur penghubung ke jalan utama/arteri serta titik macet di jam sibuk).

            ---SECTION---

            ### 📍 PEMETAAN FASILITAS TERDEKAT (POI)
            (Wajib tampilkan MINIMAL 3 FASILITAS untuk setiap kategori dalam bentuk TABEL MARKDOWN. Ingat: Jangan manipulasi jarak! Jika jauh, tulis jauh. Gunakan format tabel 5 kolom ini untuk KETIGA-ENAM kategori):

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
            2. **Alasan Potensi:** Mengapa potensial? (Sebutkan keunggulan utama berdasarkan fakta analisis di atas, APA PUN ALASANNYA yang logis).
            3. **Rekomendasi Skema Optimalisasi:** Berdasarkan karakteristik tersebut, apa skema pengelolaan yang paling direkomendasikan? (Secara tegas pilih skemanya: **Penjualan Lelang**, **Penyewaan Komersial (Sewa)**, atau **Kerja Sama Pemanfaatan (KSP)**).
            
            Hindari bahasa yang terlalu berbunga-bunga, langsung pada kesimpulan strategis yang meyakinkan pimpinan.)

            PERINGATAN KERAS: JANGAN TULIS PROSES BERPIKIRMU! JANGAN TULIS TEKS BAHASA INGGRIS APA PUN!
            LANGSUNG KELUARKAN LAPORAN DALAM BAHASA INDONESIA SEKARANG JUGA, DIAWALI PERSIS DENGAN TEKS:
            ### 💰 ESTIMASI HARGA PASAR (INDIKATIF)
            """

            # EXECUTE GEMINI DENGAN PRIORITAS OTOMATIS & ANTI-ERROR
            config_patuh = {"temperature": 0.2} # Menggunakan format dictionary agar 100% cocok di semua versi library
            
            # Memindai daftar model resmi yang aktif di akun API Key kamu
            semua_model = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Mengurutkan agar model Gemini 1.5 (Flash/Pro) diprioritaskan duluan
            model_kandidat = sorted([m for m in semua_model if not any(x in m.lower() for x in ['tts', 'audio', 'vision', 'embedding', 'aqa', 'imagen'])], key=lambda x: ('1.5' in x, 'flash' in x), reverse=True)
            
            response = None
            pesan_error_terakhir = "Tidak ada model yang kompatibel."
            
            for nama_model in model_kandidat:
                try:
                    model = genai.GenerativeModel(model_name=nama_model, generation_config=config_patuh)
                    res = model.generate_content(prompt)
                    if res and res.text:
                        response = res
                        break 
                except Exception as e:
                    pesan_error_terakhir = str(e)
                    continue

            # MENAMPILKAN HASIL
            if response and response.text:
                st.success("✅ Laporan Berhasil Disusun!")
                
                # BERSIHKAN TEKS DARI CURHATAN BAHASA INGGRIS SEBELUM SIMPAN KE SESSION
                teks_laporan = response.text
                if "### 💰 ESTIMASI HARGA PASAR" in teks_laporan:
                    teks_laporan = "### 💰 ESTIMASI HARGA PASAR" + teks_laporan.split("### 💰 ESTIMASI HARGA PASAR")[1]
                
                st.session_state.hasil_ai = teks_laporan
                st.session_state.temp_info_peta = info_validasi_peta
                
                with st.container(border=True):
                    st.markdown("### 📌 IDENTITAS & LOKASI ASET")
                    st.write(f"**Alamat Lengkap:** {alamat_aset}")
                    st.write(f"**Validasi Peta Satelit:** {info_validasi_peta}")
                    st.write("**Koordinat GPS (Klik ikon di kanan kotak untuk copas):**")
                    st.code(f"{koordinat_lat}, {koordinat_lng}", language="text")
                    
                    col_map, col_sat, col_earth = st.columns(3)
                    url_maps = f"https://www.google.com/maps/search/?api=1&query={koordinat_lat},{koordinat_lng}"
                    url_satelit = f"https://www.google.com/maps/search/?api=1&query={koordinat_lat},{koordinat_lng}&basemap=satellite"
                    url_earth = f"https://earth.google.com/web/search/{koordinat_lat}%2C+{koordinat_lng}"
                    
                    with col_map: st.link_button("🗺️ Peta Jalan (Pin)", url_maps, use_container_width=True)
                    with col_sat: st.link_button("🛰️ Satelit (Pin Merah)", url_satelit, use_container_width=True)
                    with col_earth: st.link_button("🌍 Google Earth 3D", url_earth, use_container_width=True)

                bagian_laporan = teks_laporan.split("---SECTION---")
                for bagian in bagian_laporan:
                    teks_bersih = bagian.strip()
                    if teks_bersih and not teks_bersih.startswith("```"):
                        with st.container(border=True):
                            st.markdown(teks_bersih)
            else:
                st.error(f"❌ Gagal memproses laporan. Detail Error dari Server Google: {pesan_error_terakhir}")

    # TOMBOL SIMPAN KE REVIEW
    if "hasil_ai" in st.session_state:
        st.divider()
        nama_aset = st.text_input("📝 Beri Nama untuk Aset Ini (Agar mudah dicari di Tab Review):", value=alamat_aset, key="nama_aset_review")
        
        if st.button("📥 Simpan ke Review & Edit", type="secondary", use_container_width=True):
            if not nama_aset.strip():
                st.warning("Mohon isi Nama Aset terlebih dahulu.")
            else:
                hasil_ai = st.session_state.hasil_ai
                bagian = hasil_ai.split("---SECTION---")
                
                estimasi = bagian[0].strip() if len(bagian) > 0 else ""
                karakteristik = bagian[1].strip() if len(bagian) > 1 else ""
                akses = bagian[2].strip() if len(bagian) > 2 else ""
                poi = bagian[3].strip() if len(bagian) > 3 else ""
                swot = bagian[4].strip() if len(bagian) > 4 else ""
                rekomendasi = bagian[5].strip() if len(bagian) > 5 else ""
                kesimpulan = bagian[6].strip() if len(bagian) > 6 else ""

                st.session_state.buffer_laporan.append({
                    "nama": nama_aset,
                    "lat": koordinat_lat,
                    "lng": koordinat_lng,
                    "data": {
                        "estimasi": estimasi,
                        "karakteristik": karakteristik,
                        "akses": akses,
                        "poi": poi,
                        "swot": swot,
                        "rekomendasi": rekomendasi,
                        "kesimpulan": kesimpulan
                    }
                })
                st.success("✅ Berhasil disimpan ke Review! Silakan buka Tab 2 (Review & Edit) di atas.")

# ==========================================
# --- TAB 2: REVIEW & EDIT ---
# ==========================================
with tab2:
    st.header("📝 Review & Refinement Laporan")
    if not st.session_state.buffer_laporan:
        st.info("💡 Belum ada laporan di Buffer. Silakan Generate dan Pindahkan dulu dari Tab 1.")
    else:
        idx = st.selectbox(
            "🏢 Pilih Aset yang Ingin Direview/Diedit:", 
            range(len(st.session_state.buffer_laporan)), 
            format_func=lambda x: st.session_state.buffer_laporan[x]['nama']
        )
        aset = st.session_state.buffer_laporan[idx]
        
        # FUNGSI EDIT BOX DENGAN KOTAK RAPI, TANPA JUDUL GANDA, & TOMBOL BATAL (X)
        def edit_box(field_key, index):
            unique_key = f"{field_key}_{index}"
            backup_key = f"{field_key}_backup_{index}"
            
            if unique_key not in st.session_state:
                st.session_state[unique_key] = aset['data'].get(field_key, "")
            if backup_key not in st.session_state:
                st.session_state[backup_key] = st.session_state[unique_key]
            
            with st.container(border=True):
                col1, col2 = st.columns([0.93, 0.07])
                with col1:
                    if st.session_state.get(f"is_edit_{unique_key}", False):
                        st.session_state[unique_key] = st.text_area(
                            "✏️ Mode Edit (Ubah teks di bawah ini):", 
                            value=st.session_state[unique_key], 
                            height=180,
                            label_visibility="collapsed"
                        )
                    else:
                        st.markdown(st.session_state[unique_key])
                
                with col2:
                    if not st.session_state.get(f"is_edit_{unique_key}", False):
                        if st.button("✏️", key=f"edit_{unique_key}", help="Edit bagian ini", use_container_width=True):
                            st.session_state[f"is_edit_{unique_key}"] = True
                            st.session_state[backup_key] = st.session_state[unique_key]
                            st.rerun()
                    else:
                        if st.button("✅", key=f"save_{unique_key}", help="Simpan Editan", use_container_width=True):
                            st.session_state[f"is_edit_{unique_key}"] = False
                            st.session_state[backup_key] = st.session_state[unique_key]
                            st.rerun()
                        if st.button("❌", key=f"cancel_{unique_key}", help="Batal Edit", use_container_width=True):
                            st.session_state[f"is_edit_{unique_key}"] = False
                            st.session_state[unique_key] = st.session_state[backup_key]
                            st.rerun()
                            
            return st.session_state[unique_key]

        st.markdown(f"### 📑 Memoles Laporan: **{aset['nama']}**")
        st.write("Silakan klik ikon **Pensil (✏️)** di pojok kanan setiap kotak untuk mengedit per bagian. Klik **(✅)** untuk simpan, atau **(❌)** untuk batal.")
        
        estimasi_final = edit_box("estimasi", idx)
        karakteristik_final = edit_box("karakteristik", idx)
        akses_final = edit_box("akses", idx)
        poi_final = edit_box("poi", idx)
        swot_final = edit_box("swot", idx)
        rekomendasi_final = edit_box("rekomendasi", idx)
        kesimpulan_final = edit_box("kesimpulan", idx)
        
        st.divider()
        st.markdown("### 🏁 Finalisasi & Kirim Data")
        st.write("Jika semua kotak di atas sudah fiks dan selesai kamu edit, tekan tombol di bawah agar datanya siap disimpan permanen di Tab 3:")
        
        if st.button("💾 Simpan Perubahan & Kirim ke Tab 3", type="primary", use_container_width=True):
            aset['data']['estimasi'] = estimasi_final
            aset['data']['karakteristik'] = karakteristik_final
            aset['data']['akses'] = akses_final
            aset['data']['poi'] = poi_final
            aset['data']['swot'] = swot_final
            aset['data']['rekomendasi'] = rekomendasi_final
            aset['data']['kesimpulan'] = kesimpulan_final
            
            st.success("🎉 Laporan berhasil diperbarui dan dikirim! Silakan buka **Tab 3 (Database & Export)** di atas untuk mengunduh CSV atau simpan ke GSheet.")

# ==========================================
# --- TAB 3: DATABASE & EXPORT ---
# ==========================================
with tab3:
    st.header("💾 Pusat Database & Export Aset")
    
    if not st.session_state.buffer_laporan:
        st.info("💡 Belum ada data aset yang siap di-export. Selesaikan laporan di Tab 1 & Tab 2 terlebih dahulu.")
    else:
        st.subheader("📑 Daftar Aset Siap Simpan / Export")
        
        data_for_csv = []
        for i, item in enumerate(st.session_state.buffer_laporan):
            data_for_csv.append({
                "Nama_Aset": item['nama'],
                "Lat": item['lat'],
                "Lng": item['lng'],
                "Estimasi": st.session_state.get(f"estimasi_{i}", item['data']['estimasi']),
                "Karakteristik": st.session_state.get(f"karakteristik_{i}", item['data']['karakteristik']),
                "Akses": st.session_state.get(f"akses_{i}", item['data']['akses']),
                "POI": st.session_state.get(f"poi_{i}", item['data']['poi']),
                "SWOT": st.session_state.get(f"swot_{i}", item['data']['swot']),
                "Rekomendasi": st.session_state.get(f"rekomendasi_{i}", item['data']['rekomendasi']),
                "Kesimpulan": st.session_state.get(f"kesimpulan_{i}", item['data']['kesimpulan'])
            })
        
        df_export = pd.DataFrame(data_for_csv)
        st.dataframe(df_export[["Nama_Aset", "Lat", "Lng"]], use_container_width=True)
        st.markdown("---")
        
        # 1. TOMBOL SIMPAN KE GSHEET (DENGAN STEMPEL USERNAME)
        st.subheader("☁️ Simpan ke Cloud Database (Google Sheets)")
        st.write(f"Tekan tombol ini untuk menambahkan seluruh aset di atas ke database atas nama **{st.session_state.username}**:")
        
        if st.button("🚀 Simpan Permanen ke Google Sheets", type="primary", use_container_width=True):
            try:
                client = get_gspread_client()
                if client:
                    sheet = client.open("Database_Aset_Negara").sheet1
                    with st.spinner("⏳ Mengirim data ke server Google Sheets..."):
                        existing_data = sheet.get_all_values()
                        start_id = len(existing_data)
                        
                        for idx_row, row_dict in enumerate(data_for_csv):
                            # MENYELIPKAN USERNAME SAAT PENYIMPANAN KE GSHEET
                            row_data = [
                                start_id + idx_row,
                                st.session_state.username, # <--- STEMPEL PEMILIK DATA
                                row_dict["Nama_Aset"],
                                row_dict["Lat"],
                                row_dict["Lng"],
                                row_dict["Estimasi"],
                                row_dict["Karakteristik"],
                                row_dict["Akses"],
                                row_dict["POI"],
                                row_dict["SWOT"],
                                row_dict["Rekomendasi"],
                                row_dict["Kesimpulan"]
                            ]
                            sheet.append_row(row_data)
                            
                    st.success("🎉 Berhasil! Semua aset di atas telah sukses disimpan ke Google Sheets atas nama akunmu!")
            except Exception as e:
                st.error(f"❌ Gagal simpan ke GSheet: {e}")

        # 2. FITUR MELIHAT LIVE DATABASE DENGAN FILTER PRIVASI (RBAC)
        with st.expander("📖 Klik di sini untuk melihat Isi Live Database Google Sheets"):
            try:
                client_view = get_gspread_client()
                if client_view:
                    sheet_view = client_view.open("Database_Aset_Negara").sheet1
                    records = sheet_view.get_all_records()
                    if records:
                        df_records = pd.DataFrame(records)
                        
                        # --- LOGIKA FILTER PRIVASI (ADMIN VS USER BIASA) ---
                        if st.session_state.role == "admin":
                            st.info("👑 **Mode Admin:** Menampilkan seluruh data aset dari semua appraiser.")
                            st.dataframe(df_records, use_container_width=True)
                        else:
                            st.info(f"👤 **Mode Appraiser:** Hanya menampilkan data aset yang disimpan oleh akunmu (**{st.session_state.username}**).")
                            if 'Username' in df_records.columns:
                                df_filtered = df_records[df_records['Username'] == st.session_state.username]
                                st.dataframe(df_filtered, use_container_width=True)
                            else:
                                st.warning("⚠️ Kolom 'Username' belum ditambahkan di Google Sheet. Admin melihat semua data.")
                    else:
                        st.write("Database di Google Sheets masih kosong (baru ada baris judul).")
            except Exception as e_view:
                st.write(f"Belum bisa memuat database: {e_view}")

        st.markdown("---")

        # 3. TOMBOL DOWNLOAD EXCEL & CSV (CANVA READY)
        st.subheader("📥 Unduh File untuk Laporan Manual & Canva")
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Format CSV (Canva Bulk Create Ready)",
                data=csv_data,
                file_name=f"laporan_aset_{st.session_state.username}_canva.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_dl2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Data Appraisal')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Unduh Format Excel (.xlsx) untuk Arsip Kantor",
                data=excel_data,
                file_name=f"laporan_aset_{st.session_state.username}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
