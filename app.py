import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import google.generativeai as genai
from geopy.geocoders import Nominatim

# --- KONFIGURASI KONEKSI ---
st.set_page_config(page_title="Appraiser Dashboard Pro", layout="wide")

def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict)
        return gspread.authorize(creds)
    except: return None

# --- SESSION STATE ---
if 'buffer_laporan' not in st.session_state: st.session_state.buffer_laporan = []

st.title("🏢 Appraiser Dashboard Pro")

# --- TAB SETUP ---
tab1, tab2, tab3 = st.tabs(["🚀 1. Generate", "📝 2. Review & Edit", "💾 3. Database"])

# --- TAB 1: GENERATE ---
with tab1:
    st.header("Generate Laporan Baru")

# 1. KONFIGURASI HALAMAN WEBSITE
st.title("🏢 Sistem Analisis & Appraisal Aset Properti")
st.write("Aplikasi internal untuk generate laporan analisis lingkungan, estimasi harga, dan fasilitas aset secara mendalam.")
st.markdown("---")

# 2. SISTEM KEAMANAN (PIN RAHASIA)
pin_rahasia = st.sidebar.text_input("🔐 Masukkan PIN Internal:", type="password")

if pin_rahasia != "ASET123":
    st.warning("⚠️ Silakan masukkan PIN Internal yang benar di menu sebelah kiri untuk membuka form analisis.")
    st.stop()

st.sidebar.success("✅ PIN Benar! Akses diberikan.")

# 3. FORM INPUT BERSIH
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

# 4. TOMBOL EKSEKUSI
if st.button("🚀 Generate Laporan Analisis Mendalam", type="primary", use_container_width=True):
    if not alamat_aset or koordinat_lat is None or koordinat_lng is None:
        st.error("⚠️ Mohon lengkapi Alamat Lengkap dan Koordinat (Latitude & Longitude) terlebih dahulu!")
        st.stop()
        
    with st.spinner("⏳ Memindai koordinat satelit, melacak nama jalan & wilayah, serta menyusun tabel analisis..."):
        
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        except:
            st.error("❌ API Key belum dipasang di pengaturan rahasia Streamlit Cloud.")
            st.stop()

        # =====================================================================
        # LANGKAH 1: PYTHON MELACAK NAMA JALAN & WILAYAH DARI SATELIT
        # =====================================================================
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

        # =====================================================================
        # LANGKAH 2: PROMPT MASTER DENGAN FULL TABEL (POI & SWOT)
        # =====================================================================
        prompt = f"""
        TULIS LANGSUNG LAPORAN DI BAWAH INI. JANGAN MENULIS PROSES BERPIKIR (THOUGHTS), JANGAN MENGULANG INSTRUKSI, DAN JANGAN MENULIS TEKS BAHASA INGGRIS APAPUN DI LUAR LAPORAN. LANGSUNG MULAI DARI JUDUL BAB PERTAMA YAITU "### 💰 ESTIMASI HARGA PASAR (INDIKATIF)".

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
        """

        # MESIN AUTO-RETRY ANTI GAGAL
        semua_model = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_kandidat = [m for m in semua_model if not any(x in m.lower() for x in ['tts', 'audio', 'vision', 'embedding', 'aqa', 'imagen'])]
        
        response = None
        for nama_model in model_kandidat:
            try:
                model = genai.GenerativeModel(nama_model)
                response = model.generate_content(prompt)
                break 
            except:
                continue

        # 5. MENAMPILKAN HASIL DENGAN UI KOTAK-KOTAK
        if response and response.text:
            st.success("✅ Laporan Berhasil Disusun!")
            
            # SIMPAN HASIL AI KE SESSION
            st.session_state.hasil_ai = response.text
            
            # --- KOTAK 1: IDENTITAS & LINK PETA SATELIT ANTI-GAGAL ---
            with st.container(border=True):
                st.markdown("### 📌 IDENTITAS & LOKASI ASET")
                st.write(f"**Alamat Lengkap:** {alamat_aset}")
                st.write(f"**Validasi Peta Satelit:** {info_validasi_peta}")
                
                st.write("**Koordinat GPS (Klik ikon di kanan kotak untuk copas):**")
                st.code(f"{koordinat_lat}, {koordinat_lng}", language="text")
                
                # KITA BUAT 3 TOMBOL SEJAJAR: PETA JALAN, PETA SATELIT (PIN PASTI MUNCUL), & EARTH
                col_map, col_sat, col_earth = st.columns(3)
                
                # 1. Link Maps Standar (Peta Jalan + Pin)
                url_maps = f"https://www.google.com/maps/search/?api=1&query={koordinat_lat},{koordinat_lng}"
                
                # 2. Link Maps Satelit (SAMA KEK EARTH, TAPI PIN MERAH 1000% PASTI NANCAP!)
                url_satelit = f"https://www.google.com/maps/search/?api=1&query={koordinat_lat},{koordinat_lng}&basemap=satellite"
                
                # 3. Link Earth (Sudah ditambah simbol '%2C+' standar resmi Earth)
                url_earth = f"https://earth.google.com/web/search/{koordinat_lat}%2C+{koordinat_lng}"
                
                with col_map:
                    st.link_button("🗺️ Peta Jalan (Pin)", url_maps, use_container_width=True)
                with col_sat:
                    st.link_button("🛰️ Satelit (Pin Merah)", url_satelit, use_container_width=True)
                with col_earth:
                    st.link_button("🌍 Google Earth 3D", url_earth, use_container_width=True)

            # --- KOTAK 2 SAMPAI SELESAI: HASIL ANALISIS AI ---
            teks_laporan = response.text
            if "### 💰 ESTIMASI HARGA PASAR" in teks_laporan:
                teks_laporan = "### 💰 ESTIMASI HARGA PASAR" + teks_laporan.split("### 💰 ESTIMASI HARGA PASAR")[1]

            bagian_laporan = teks_laporan.split("---SECTION---")
            
            for bagian in bagian_laporan:
                teks_bersih = bagian.strip()
                if teks_bersih and not teks_bersih.startswith("```"):
                    with st.container(border=True):
                        st.markdown(teks_bersih)
                        
        else:
            st.error("❌ Gagal memproses laporan. Silakan coba lagi.")
         
    # TOMBOL SIMPAN KE REVIEW
    if "hasil_ai" in st.session_state:

    st.divider()

    nama_aset = st.text_input(
        "📝 Nama Aset",
        key="nama_aset_review"
    )
    if st.button(
        "📥 Simpan ke Review",
        type="secondary",
        use_container_width=True
    ):

        if not nama_aset.strip():
            st.warning("Mohon isi Nama Aset terlebih dahulu.")
        else:

            hasil_ai = st.session_state.hasil_ai
            
            bagian = hasil_ai.split("---SECTION---")

            estimasi = bagian[0] if len(bagian) > 0 else ""
            karakteristik = bagian[1] if len(bagian) > 1 else ""
            akses = bagian[2] if len(bagian) > 2 else ""
            poi = bagian[3] if len(bagian) > 3 else ""
            swot = bagian[4] if len(bagian) > 4 else ""
            rekomendasi = bagian[5] if len(bagian) > 5 else ""
            kesimpulan = bagian[6] if len(bagian) > 6 else ""

            st.session_state.buffer_laporan.append({
                "nama": nama_aset,
                "lat": koordinat_lat,
                "lng": koordinat_lng,
                "data": {
                    "estimasi harga": estimasi,
                    "karakteristik": karakteristik,
                    "akses": akses,
                    "poi": poi,
                    "swot": swot,
                    "rekomendasi": rekomendasi,
                    "kesimpulan": kesimpulan
                }
            })

            st.success("✅ Berhasil disimpan ke Review!")

# --- TAB 2: REVIEW & EDIT ---
with tab2:
    st.header("📝 Review & Edit Laporan")
    if not st.session_state.buffer_laporan:
        st.info("Belum ada laporan di Buffer. Silakan Generate dan Pindahkan dulu.")
    else:
        # Pilih aset
        idx = st.selectbox("Pilih Aset:", range(len(st.session_state.buffer_laporan)), 
                           format_func=lambda x: st.session_state.buffer_laporan[x]['nama'])
        aset = st.session_state.buffer_laporan[idx]
        
        # Fungsi edit box dengan KEY UNIK (menggunakan index aset agar tidak bentrok)
        def edit_box(label, field_key, index):
            # Key unik untuk setiap field setiap aset
            unique_key = f"{field_key}_{index}"
            
            # Ambil data dari aset['data'] kalau belum ada di session
            if unique_key not in st.session_state:
                st.session_state[unique_key] = aset['data'].get(field_key, "")
            
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                # Cek apakah sedang mode edit
                if st.session_state.get(f"is_edit_{unique_key}", False):
                    st.session_state[unique_key] = st.text_area(label, value=st.session_state[unique_key], height=100)
                else:
                    st.markdown(f"**{label}**")
                    st.write(st.session_state[unique_key])
            with col2:
                if not st.session_state.get(f"is_edit_{unique_key}", False):
                    if st.button("✏️", key=f"edit_{unique_key}"):
                        st.session_state[f"is_edit_{unique_key}"] = True
                        st.rerun()
                else:
                    if st.button("✅", key=f"save_{unique_key}"):
                        st.session_state[f"is_edit_{unique_key}"] = False
                        st.rerun()
            
            return st.session_state[unique_key]

        # Panggil edit box untuk tiap kolom & simpan hasilnya ke variabel sementara
        identitas_final = edit_box("Identitas", "identitas", idx)
        karakteristik_final = edit_box("Karakteristik", "karakteristik", idx)
        akses_final = edit_box("Akses", "akses", idx)
        poi_final = edit_box("POI", "poi", idx)
        swot_final = edit_box("SWOT", "swot", idx)
        rekomendasi_final = edit_box("Rekomendasi", "rekomendasi", idx)
        kesimpulan_final = edit_box("Kesimpulan", "kesimpulan", idx)

# --- TAB 3: DATABASE & EXPORT ---
with tab3:
    st.header("💾 Simpan ke Database")
    
    # Tombol Simpan ke GSheet
    if st.session_state.buffer_laporan and st.button("Simpan Permanen ke GSheet"):
        try:
            client = get_gspread_client()
            sheet = client.open("Database_Aset_Negara").sheet1
            
            # Row data (menggunakan variabel final dari Tab 2)
            row_data = [
                len(sheet.get_all_values()), # ID sederhana
                aset['nama'],
                aset['lat'],
                aset['lng'],
                identitas_final,
                karakteristik_final,
                akses_final,
                poi_final,
                swot_final,
                rekomendasi_final,
                kesimpulan_final
            ]
            
            sheet.append_row(row_data)
            st.success(f"Berhasil simpan aset {aset['nama']} ke GSheet!")
        except Exception as e:
            st.error(f"Gagal simpan: {e}")

    # Logika Export CSV
    st.divider()
    st.subheader("📥 Export Data")
    
    # Menyiapkan data untuk CSV
    data_for_csv = []
    for i, item in enumerate(st.session_state.buffer_laporan):
        data_for_csv.append({
            "Nama_Aset": item['nama'],
            "Lat": item['lat'],
            "Lng": item['lng'],
            "Identitas": st.session_state.get(f"identitas_{i}", item['data']['identitas']),
            "Karakteristik": st.session_state.get(f"karakteristik_{i}", item['data']['karakteristik']),
            "Akses": st.session_state.get(f"akses_{i}", item['data']['akses']),
            "POI": st.session_state.get(f"poi_{i}", item['data']['poi']),
            "SWOT": st.session_state.get(f"swot_{i}", item['data']['swot']),
            "Rekomendasi": st.session_state.get(f"rekomendasi_{i}", item['data']['rekomendasi']),
            "Kesimpulan": st.session_state.get(f"kesimpulan_{i}", item['data']['kesimpulan'])
        })
    
    if data_for_csv:
        df_export = pd.DataFrame(data_for_csv)
        csv = df_export.to_csv(index=False).encode('utf-8')

    )
else:
    st.info("Belum ada data untuk diexport.")
    
    st.download_button(
        label="📥 Download CSV untuk Canva Bulk Create",
        data=csv,
        file_name="laporan_aset_canva.csv",
        mime="text/csv",
    )
