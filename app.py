import streamlit as st
import google.generativeai as genai

# 1. KONFIGURASI HALAMAN WEBSITE
st.set_page_content(
    page_title="Sistem Analisis Aset Negara",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Sistem Analisis & Appraisal Aset Properti")
st.write("Aplikasi internal untuk generate laporan analisis lingkungan, aksesibilitas, dan fasilitas aset secara mendalam.")
st.markdown("---")

# 2. SISTEM KEAMANAN (PIN / PASSWORD RAHASIA)
# Supaya kalau link bocor, orang luar tetap ga bisa pakai kuota API kamu!
pin_rahasia = st.sidebar.text_input("🔐 Masukkan PIN Internal:", type="password")

if pin_rahasia != "ASET123": # <-- Kamu bisa ganti password "ASET123" sesuka hatimu
    st.warning("⚠️ Silakan masukkan PIN Internal yang benar di menu sebelah kiri untuk membuka form analisis.")
    st.stop() # Menghentikan aplikasi supaya orang luar ga bisa lanjut

st.sidebar.success("✅ PIN Benar! Akses diberikan.")

# 3. FORM INPUT DI LAYAR WEBSITE (BERSAMAAN & RAPI)
col1, col2 = st.columns(2)

with col1:
    alamat_aset = st.text_input("📍 Alamat Lengkap Aset:", "Desa Medaeng, Kec. Waru, Kab. Sidoarjo, Jawa Timur")
    koordinat_lat = st.number_input("🌐 Latitude (Garis Lintang):", value=-7.355073, format="%.6f")
    koordinat_lng = st.number_input("🌐 Longitude (Garis Bujur):", value=112.710424, format="%.6f")

with col2:
    informasi_tambahan = st.text_area(
        "📝 Catatan Kondisi Lapangan & Informasi Tambahan:", 
        "Tanah kosong eks BDL seluas 3.068 m2. Berada satu hamparan dengan SHM lain. Posisi di tepi jalan raya utama, berdekatan dengan kompleks Brimob Medaeng. Kondisi bangunan lama sudah runtuh dan tertutup rumput liar. Aset sudah dipasang plang dan minim risiko okupasi ilegal.",
        height=130
    )

st.markdown("---")

# 4. TOMBOL EKSEKUSI
if st.button("🚀 Generate Laporan Analisis Mendalam", type="primary", use_container_width=True):
    with st.spinner("⏳ Gemini sedang memetakan koordinat, melacak fasilitas, dan menyusun laporan appraisal..."):
        
        # MENGAMBIL API KEY DARI BRANKAS RAHASIA STREAMLIT
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        except:
            st.error("❌ API Key belum dipasang di pengaturan rahasia Streamlit Cloud.")
            st.stop()

        # INSTRUKSI PROMPT DEEP APPRAISAL (Sama persis seperti yang kita rancang tadi)
        prompt = f"""
        Kamu adalah seorang Penilai Aset Negara (Appraiser) dan Analis Properti Senior dari DJKN/KPKNL yang sangat berpengalaman, kritis, dan realistis. Tugasmu adalah menyusun LAPORAN HASIL ANALISIS ASET yang mendalam (deep), teknis, dan objektif berdasarkan koordinat dan data lapangan.

        DATA TARGET ASET:
        - Alamat/Lokasi: {alamat_aset}
        - Koordinat Titik: {koordinat_lat}, {koordinat_lng}
        - Informasi Tambahan & Kondisi Lapangan: {informasi_tambahan}

        INSTRUKSI KRISIAL (WAJIB DIPATUHI):
        1. **NO SUGARCOATING (JANGAN DIBAIK-BAIKIN):** Bersikaplah objektif dan brutal. Jika ada kelemahan seperti macet parah, risiko banjir, rawan konflik perbatasan lahan, polusi suara, atau posisi akses yang sulit, BEBERKAN SEJUJURNYA. Jangan gunakan bahasa marketing yang berlebihan.
        2. **KEDALAMAN DATA FASILITAS (METRIK SPESIFIK):** 
           - Wajib menyebutkan NAMA SPESIFIK fasilitas nyata yang ada di sekitar area tersebut (berdasarkan pemetaan koordinat {koordinat_lat}, {koordinat_lng}). JANGAN mengarang nama umum.
           - Wajib menyertakan estimasi JARAK dalam Kilometer (km).
           - Wajib membedakan waktu tempuh antara SEPEDA MOTOR dan MOBIL dengan memperhitungkan kondisi kemacetan riil di kawasan tersebut.
           - Format wajib per poin: `- [Nama Fasilitas] (~[X] km | Motor: ~[X] menit, Mobil: ~[Y] menit)`

        SUSUN LAPORAN DENGAN FORMAT HEADER DAN STRUKTUR BERIKUT:

        _____________________________
        LAPORAN HASIL ANALISIS ASET
        =======================================

        **1. KARAKTERISTIK DAN DINAMIKA KAWASAN**
        - **Klasifikasi & Tata Ruang Kawasan:** (Jelaskan secara spesifik peruntukan kawasan ini apakah koridor komersial, pemukiman padat, atau campuran. Sebutkan karakter lingkungan sekitarnya).
        - **Penggerak Ekonomi Lokal:** (Jelaskan roda ekonomi riil di area ini, apa jenis usaha yang hidup dan apa yang mati).
        - **Analisis Lingkungan & Sosial:** (Jelaskan kondisi keamanan, interaksi dengan warga sekitar, serta identifikasi potensi gangguan lingkungan seperti kebisingan lalu lintas, getaran, atau polusi).

        **2. EVALUASI AKSESIBILITAS DAN KONEKTIVITAS**
        - **Kondisi Akses Mikro (Jalan Depan Aset):** (Jelaskan nama jalan, perkiraan lebar jalan dalam meter, kapasitas muatan kendaraan apakah bisa masuk truk tronton/kontainer, serta kondisi fisik perkerasan jalan).
        - **Konektivitas Makro & Titik Macet:** (Jelaskan penghubung ke jalur nasional/arteri. WAJIB jelaskan titik-titik kemacetan lokal yang sering terjadi di sekitar aset pada jam sibuk yang dapat mengurangi nilai jual/sewa aset).

        **3. PEMETAAN FASILITAS TERDEKAT (POI)**
        (Lacak fasilitas nyata di sekitar koordinat aset dan sajikan dengan format: `- Nama Fasilitas (~Jarak km | Motor: ~X menit, Mobil: ~Y menit)`. Sebutkan minimal 3-4 tempat per kategori jika tersedia):

        * **A. Fasilitas Pendidikan:**
          (Sebutkan SD, SMP, SMA, atau Kampus terdekat beserta metrik jarak dan waktunya)
        * **B. Pusat Perbelanjaan & Niaga:**
          (Sebutkan Pasar Tradisional, Mall, Supermarket, atau Pusat Grosir terdekat)
        * **C. Fasilitas Kesehatan:**
          (Sebutkan RSUD, RS Swasta, Klinik, atau Puskesmas terdekat)
        * **D. Akses Tol & Simpul Transportasi:**
          (Sebutkan Gerbang Tol, Terminal, atau Stasiun terdekat)
        * **E. Tempat Ibadah:**
          (Sebutkan Masjid, Gereja, atau tempat ibadah utama terdekat)
        * **F. Area Publik & Destinasi Wisata:**
          (Sebutkan Alun-alun, taman kota, atau pusat rekreasi/wisata terdekat)

        **4. ANALISIS KRITIS POTENSI & RISIKOS (SWOT Singkat)**
        - **Kekuatan & Nilai Jual Utama (Strengths):** (Sebutkan 2-3 keunggulan mutlak aset ini)
        - **Kelemahan & Risiko Aset (Weaknesses & Risks):** (Sebutkan 2-3 kelemahan kritis, misalnya biaya pembersihan puing bangunan runtuh, kemacetan akses depan, atau risiko lingkungan lainnya yang perlu diwaspadai pimpinan)

        **5. REKOMENDASI PEMANFAATAN OPTIMAL (HIGHEST AND BEST USE)**
        (Berikan rekomendasi peruntukan paling logis dan menguntungkan untuk negara/pemilik aset berdasarkan analisis kritis di atas, apakah cocok untuk dilelang komersial, disewakan untuk gudang/retail, atau dipecah. Berikan kesimpulan akhir yang padat dan tegas).
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

        # 5. MENAMPILKAN HASIL DI WEBSITE
        if response and response.text:
            st.success("✅ Laporan Berhasil Disusun!")
            st.markdown(response.text)
        else:
            st.error("❌ Gagal memproses laporan. Silakan coba lagi.")
