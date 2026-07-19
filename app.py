import streamlit as st
import google.generativeai as genai
from geopy.geocoders import Nominatim  # <-- ALAT PELACAK JALAN SATELIT

# 1. KONFIGURASI HALAMAN WEBSITE
st.set_page_config(
    page_title="Sistem Analisis Aset Negara",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Sistem Analisis & Appraisal Aset Properti")
st.write("Aplikasi internal untuk generate laporan analisis lingkungan, estimasi harga, dan fasilitas aset secara mendalam.")
st.markdown("---")

# 2. SISTEM KEAMANAN (PIN RAHASIA)
pin_rahasia = st.sidebar.text_input("🔐 Masukkan PIN Internal:", type="password")

if pin_rahasia != "ASET123":
    st.warning("⚠️ Silakan masukkan PIN Internal yang benar di menu sebelah kiri untuk membuka form analisis.")
    st.stop()

st.sidebar.success("✅ PIN Benar! Akses diberikan.")

# 3. FORM INPUT BERSIH (SUDAH DIPERBAIKI VALUE=NONE)
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
        
    with st.spinner("⏳ Memindai koordinat satelit, melacak nama jalan depan aset, dan menyusun laporan..."):
        
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        except:
            st.error("❌ API Key belum dipasang di pengaturan rahasia Streamlit Cloud.")
            st.stop()

        # =====================================================================
        # LANGKAH 1: PYTHON MELACAK NAMA JALAN DARI KOORDINAT (REVERSE GEOCODING)
        # =====================================================================
        try:
            geolocator = Nominatim(user_agent="appraisal_aset_djkn_app", timeout=10)
            lokasi_nyata = geolocator.reverse(f"{koordinat_lat}, {koordinat_lng}", exactly_one=True)
            data_peta = lokasi_nyata.raw['address']
            
            # Mengambil nama jalan asli, kecamatan, kabupaten dari data satelit
            nama_jalan_asli = data_peta.get('road', data_peta.get('pedestrian', data_peta.get('suburb', 'Jalan Utama/Lokal di koordinat ini')))
            kecamatan_asli = data_peta.get('suburb', data_peta.get('city_district', data_peta.get('village', 'Kecamatan setempat')))
            kabupaten_asli = data_peta.get('city', data_peta.get('county', 'Kabupaten/Kota setempat'))
            
            info_validasi_peta = f"Jalan Depan Aset: '{nama_jalan_asli}' | Wilayah: {kecamatan_asli}, {kabupaten_asli}"
        except Exception as e:
            nama_jalan_asli = "Jalan Raya/Lokal di koordinat ini"
            info_validasi_peta = f"Koordinat GPS: {koordinat_lat}, {koordinat_lng} (Gunakan pemetaan internal AI)"

        # =====================================================================
        # LANGKAH 2: DATA NAMA JALAN ASLI DISUAPKAN KE DALAM PROMPT GEMINI
        # =====================================================================
        prompt = f"""
        TULIS LANGSUNG LAPORAN DI BAWAH INI. JANGAN MENULIS PROSES BERPIKIR (THOUGHTS), JANGAN MENGULANG INSTRUKSI, DAN JANGAN MENULIS TEKS BAHASA INGGRIS APAPUN DI LUAR LAPORAN. LANGSUNG MULAI DARI JUDUL BAB PERTAMA YAITU "### 💰 ESTIMASI HARGA PASAR (INDIKATIF)".

        Kamu adalah Penilai Aset Negara (Appraiser) DJKN/KPKNL. Tugasmu membuat laporan analisis aset properti yang LUGAS, REALISTIS, DAN MEMBUMI (mudah dipahami pimpinan, hindari kata-kata akademis yang terlalu tinggi, ganti dengan bahasa sehari-hari yang profesional seperti 'pergeseran dari lahan pertanian menjadi permukiman, ruko, atau gudang kecil').

        DATA TARGET ASET:
        - Alamat/Lokasi: {alamat_aset}
        - Koordinat Titik: {koordinat_lat}, {koordinat_lng}
        - Catatan Lapangan: {informasi_tambahan if informasi_tambahan else "Tidak ada catatan khusus, analisis berdasarkan pemetaan koordinat."}
        
        DATA VALIDASI SATELIT (NYATA DARI PETA - WAJIB DIJADIKAN ACUAN UTAMA):
        - {info_validasi_peta}

        INSTRUKSI TEKNIS DAN FORMAT LAPORAN (WAJIB DIPATUHI):
        1. BAHASA LUGAS & ANALISIS JALAN YANG BENAR: Karena data satelit sudah mengungkap bahwa aset berada di jalan "{nama_jalan_asli}", kamu WAJIB menganalisis aset berdasarkan kelas jalan tersebut! Jika "{nama_jalan_asli}" adalah jalan raya antar-kecamatan/arteri, JANGAN sebut ini sebagai jalan desa yang sempit! Perkirakan lebarnya secara logis (misal jalan utama 8-12 meter, bisa simpangan truk tronton/kontainer) dan jelaskan bagaimana dampak visibilitas jalan "{nama_jalan_asli}" terhadap nilai komersial aset!
        2. NO SUGARCOATING: Beberkan kelemahan riil (macet, jalan sempit, rawan banjir, dll).
        3. ANTI BIAS HUNIAN: Jangan terlalu fokus menilai cocok/tidaknya untuk rumah tinggal. Nilai potensi komersial, perdagangan, jasa, gudang, atau lelang.
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
        (Sebutkan nama fasilitas nyata di sekitar koordinat. JANGAN MENEBAK JARAK ANGKA TANPA PERINGATAN. Gunakan format persis ini):
        - **[Nama Fasilitas]** (~[X] km | Motor: ~[X] menit, Mobil: ~[Y] menit) *[Estimasi AI, double check pada tautan]* - [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+FASILITAS+GANTI+SPASI+DENGAN+PLUS])
        
        (Kelompokkan menjadi: A. Pendidikan, B. Perbelanjaan & Niaga, C. Fasilitas Kesehatan, D. Akses Tol & Transportasi, E. Tempat Ibadah, F. Area Publik).

        ---SECTION---

        ### ⚖️ ANALISIS KRITIS POTENSI & RISIKO (SWOT SINGKAT)
        - **Kekuatan & Nilai Jual Utama (Strengths):** (2-3 keunggulan aset yang nyata dan logis, utamakan posisi dan visibilitas di "{nama_jalan_asli}").
        - **Kelemahan & Risiko Aset (Weaknesses & Risks):** (2-3 kelemahan kritis secara jujur tanpa sugarcoating).

        ---SECTION---

        ### 🎯 REKOMENDASI PEMANFAATAN OPTIMAL (HIGHEST AND BEST USE)
        - **Opsi Pemanfaatan PALING MUNGKIN (Top 2-3 Opsi):** (Rekomendasi selain hunian, misal untuk perdagangan, jasa, ruko, atau gudang skala kecil beserta alasannya).
        - **Opsi Pemanfaatan PALING TIDAK MUNGKIN (1 Opsi):** (1 opsi yang tidak cocok beserta alasan logisnya).

        ---SECTION---

        ### 📝 KESIMPULAN AKHIR
        (Buat 1 paragraf kesimpulan eksekutif yang lugas, padat, dan langsung pada intinya. Wajib merangkum 3 hal berikut dalam alur yang natural:
        1. **Potensi:** Secara keseluruhan, aset ini paling potensial dikembangkan sebagai apa? (misal: properti komersial, pergudangan, retail, jasa, dll).
        2. **Alasan Potensi:** Mengapa potensial? (Sebutkan keunggulan utama aset ini berdasarkan fakta analisis di atas, APA PUN ALASANNYA yang paling logis—misalnya karena posisinya di "{nama_jalan_asli}" yang aktif, dekat simpul tol, visibilitas tinggi, pertumbuhan kawasan yang pesat, atau akses yang mendukung).
        3. **Rekomendasi Skema Optimalisasi:** Berdasarkan karakteristik tersebut, apa skema pengelolaan yang paling direkomendasikan untuk negara/pemilik? (Secara tegas pilih dan sebutkan skemanya, misalnya: dioptimalkan melalui skema **Penjualan Lelang**, **Penyewaan Komersial (Sewa)**, atau **Kerja Sama Pemanfaatan (KSP)**).
        
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
            
            # --- KOTAK 1: IDENTITAS & LINK GPS YANG SUDAH ADA PINPOINT MERAH ---
            with st.container(border=True):
                st.markdown("### 📌 IDENTITAS & LOKASI ASET")
                st.write(f"**Alamat Lengkap:** {alamat_aset}")
                st.write(f"**Validasi Peta Satelit:** {info_validasi_peta}")
                
                st.write("**Koordinat GPS (Klik ikon di kanan kotak untuk copas):**")
                st.code(f"{koordinat_lat}, {koordinat_lng}", language="text")
                
                # Link Google Earth dengan gabungan /search/ (pin merah) + /@/ (zoom kamera 3D)
                col_map, col_earth = st.columns(2)
                url_maps = f"https://www.google.com/maps?q={koordinat_lat},{koordinat_lng}"
                url_earth = f"https://earth.google.com/web/search/{koordinat_lat},{koordinat_lng}/@{koordinat_lat},{koordinat_lng},1000a,800d,35y,0h,0t,0r"
                
                with col_map:
                    st.link_button("🗺️ Buka di Google Maps", url_maps, use_container_width=True)
                with col_earth:
                    st.link_button("🌍 Buka di Google Earth (Ada Pin Merahnya)", url_earth, use_container_width=True)

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
