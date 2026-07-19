import streamlit as st
import google.generativeai as genai

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

# 3. FORM INPUT BERSIH (TANPA CONTOH PRIBADI)
col1, col2 = st.columns(2)

with col1:
    alamat_aset = st.text_input(
        "📍 Alamat Lengkap Aset:", 
        value="", 
        placeholder="Contoh: Jl. Ahmad Yani No. 123, Surabaya"
    )
    koordinat_lat = st.number_input(
        "🌐 Latitude (Garis Lintang):", 
        value=None, 
        format="%.6f", 
        help="Masukkan koordinat Latitude, contoh: -7.250445"
    )
    koordinat_lng = st.number_input(
        "🌐 Longitude (Garis Bujur):", 
        value=None, 
        format="%.6f", 
        help="Masukkan koordinat Longitude, contoh: 112.768845"
    )

with col2:
    informasi_tambahan = st.text_area(
        "📝 Catatan Kondisi Lapangan & Informasi Tambahan:", 
        value="", 
        placeholder="Contoh: Tanah kosong, kondisi berumput, berada di tepi jalan utama...",
        height=130
    )

st.markdown("---")

# 4. TOMBOL EKSEKUSI
if st.button("🚀 Generate Laporan Analisis Mendalam", type="primary", use_container_width=True):
    # Validasi input tidak boleh kosong
    if not alamat_aset or koordinat_lat is None or koordinat_lng is None:
        st.error("⚠️ Mohon lengkapi Alamat Lengkap dan Koordinat (Latitude & Longitude) terlebih dahulu!")
        st.stop()
        
    with st.spinner("⏳ AI sedang melakukan self-correction, kalkulasi harga pasar, dan menyusun laporan terstruktur..."):
        
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        except:
            st.error("❌ API Key belum dipasang di pengaturan rahasia Streamlit Cloud.")
            st.stop()

        # PROMPT MASTER: GABUNGAN METRIK SPESIFIK, LINK RUTE, ANTI-BIAS, & UI KOTAK
        prompt = f"""
        JANGAN mengulangi instruksi atau input data ini dalam hasil laporanmu. Langsung mulai tulis laporan dari judul bab pertama.

        Kamu adalah seorang Penilai Aset Negara (Appraiser) dan Analis Properti Senior dari DJKN/KPKNL yang sangat berpengalaman, kritis, dan realistis. Tugasmu adalah menyusun LAPORAN HASIL ANALISIS ASET yang mendalam (deep), teknis, dan objektif berdasarkan koordinat dan data lapangan.

        DATA TARGET ASET:
        - Alamat/Lokasi: {alamat_aset}
        - Koordinat Titik: {koordinat_lat}, {koordinat_lng}
        - Informasi Tambahan & Kondisi Lapangan: {informasi_tambahan}

        INSTRUKSI KRISIAL (WAJIB DIPATUHI):
        1. **NO SUGARCOATING (JANGAN DIBAIK-BAIKIN):** Bersikaplah objektif dan brutal. Jika ada kelemahan seperti macet parah, risiko banjir, rawan konflik perbatasan lahan, polusi suara, atau posisi akses yang sulit, BEBERKAN SEJUJURNYA. Jangan gunakan bahasa marketing yang berlebihan.
        2. **KEDALAMAN DATA FASILITAS (METRIK SPESIFIK & LINK RUTE):** 
           - Wajib menyebutkan NAMA SPESIFIK fasilitas nyata yang ada di sekitar area tersebut berdasarkan pemetaan koordinat. JANGAN mengarang nama umum.
           - Wajib menyertakan estimasi JARAK (km) dan WAKTU TEMPUH (Motor vs Mobil) dengan memperhitungkan kemacetan riil.
           - Karena angka jarak dari AI bersifat prediktif, tambahkan keterangan bahwa itu adalah ESTIMASI dan wajib verifikasi ulang melalui link rute.
           - **FORMAT WAJIB PER POIN FASILITAS (Ikuti persis struktur ini):**
             `- **[Nama Fasilitas]** (~[X] km | Motor: ~[X] menit, Mobil: ~[Y] menit) *[Estimasi AI, double check pada tautan]* - [🗺️ Lihat Rute](https://www.google.com/maps/dir/?api=1&origin={koordinat_lat},{koordinat_lng}&destination=[NAMA+FASILITAS+GANTI+SPASI+DENGAN+PLUS])`
        3. **HAPUS BIAS HUNIAN:** JANGAN berulang-ulang menekankan mengapa aset cocok atau tidak cocok untuk rumah tinggal (residensial). Evaluasilah secara luas dari sudut pandang komersial, gudang, retail, logistik, atau lelang BMN.
        4. **FORMAT UI KOTAK-KOTAK:** Agar sistem website kami bisa menyajikan laporanmu ke dalam kotak visual terpisah, kamu WAJIB menyisipkan kata sandi ini tepat di antara setiap bab/bagian di bawah ini:
           ---SECTION---

        SUSUN LAPORAN DENGAN URUTAN BAB DAN STRUKTUR PERSIS SEPERTI INI:

        ### 💰 ESTIMASI HARGA PASAR (INDIKATIF)
        - **Estimasi Harga Tanah:** Rp [X] - Rp [Y] per m² (Berikan penjelasan analisis singkat mengapa rentang harga pasar ini logis untuk kawasan tersebut).
        - **Estimasi Harga Bangunan:** Rp [X] - Rp [Y] per m² (Jika ada bangunan/puing, jelaskan estimasi nilainya atau biaya bangun standar di area ini).
        - *Disclaimer Resmi:* Angka di atas merupakan estimasi awal berbasis data analitis AI untuk gambaran kasar, bukan merupakan nilai limit lelang atau nilai appraisal resmi. Diperlukan survei dan penilaian fisik langsung di lapangan.

        ---SECTION---

        ### 🏘️ KARAKTERISTIK DAN DINAMIKA KAWASAN
        - **Klasifikasi & Tata Ruang Kawasan:** (Jelaskan secara spesifik peruntukan kawasan ini apakah koridor komersial, pemukiman padat, industri, atau campuran. Sebutkan karakter lingkungan sekitarnya).
        - **Penggerak Ekonomi Lokal:** (Jelaskan roda ekonomi riil di area ini, apa jenis usaha yang potensial hidup dan apa yang mati).
        - **Analisis Lingkungan & Sosial:** (Jelaskan kondisi keamanan, interaksi dengan warga sekitar, serta identifikasi potensi gangguan lingkungan seperti kebisingan lalu lintas, getaran, atau polusi).

        ---SECTION---

        ### 🛣️ EVALUASI AKSESIBILITAS DAN KONEKTIVITAS
        - **Kondisi Akses Mikro (Jalan Depan Aset):** (Jelaskan nama jalan, perkiraan lebar jalan dalam meter, kapasitas muatan kendaraan apakah bisa masuk truk tronton/kontainer, serta kondisi fisik perkerasan jalan).
        - **Konektivitas Makro & Titik Macet:** (Jalur penghubung ke jalan arteri/nasional. WAJIB jelaskan titik-titik kemacetan lokal yang sering terjadi di sekitar aset pada jam sibuk yang dapat mengurangi nilai jual/sewa aset).

        ---SECTION---

        ### 📍 PEMETAAN FASILITAS TERDEKAT (POI)
        (Lacak fasilitas nyata di sekitar koordinat aset. Sajikan minimal 3-4 tempat per kategori dengan FORMAT WAJIB yang menyertakan estimasi jarak, waktu motor vs mobil, warning double check, dan link Lihat Rute):

        * **A. Fasilitas Pendidikan:**
          (Sebutkan SD, SMP, SMA, atau Kampus terdekat menggunakan format wajib di atas)
        * **B. Pusat Perbelanjaan & Niaga:**
          (Sebutkan Pasar Tradisional, Mall, Supermarket, atau Pusat Grosir terdekat menggunakan format wajib di atas)
        * **C. Fasilitas Kesehatan:**
          (Sebutkan RSUD, RS Swasta, Klinik, atau Puskesmas terdekat menggunakan format wajib di atas)
        * **D. Akses Tol & Simpul Transportasi:**
          (Sebutkan Gerbang Tol, Terminal, atau Stasiun terdekat menggunakan format wajib di atas)
        * **E. Tempat Ibadah:**
          (Sebutkan Masjid, Gereja, atau tempat ibadah utama terdekat menggunakan format wajib di atas)
        * **F. Area Publik & Destinasi Wisata:**
          (Sebutkan Alun-alun, taman kota, atau pusat rekreasi/wisata terdekat menggunakan format wajib di atas)

        ---SECTION---

        ### ⚖️ ANALISIS KRITIS POTENSI & RISIKO (SWOT SINGKAT)
        - **Kekuatan & Nilai Jual Utama (Strengths):** (Sebutkan 2-3 keunggulan mutlak aset ini).
        - **Kelemahan & Risiko Aset (Weaknesses & Risks):** (Sebutkan 2-3 kelemahan kritis secara jujur tanpa sugarcoating, misalnya biaya pembersihan puing, kemacetan akses depan, atau risiko lingkungan lainnya).

        ---SECTION---

        ### 🎯 REKOMENDASI PEMANFAATAN OPTIMAL (HIGHEST AND BEST USE)
        - **Opsi Pemanfaatan PALING MUNGKIN (Top 2-3 Opsi):** (Berikan rekomendasi peruntukan paling logis dan menguntungkan selain hunian, misal untuk dilelang komersial, disewakan untuk gudang/retail, atau dipecah, beserta alasan logisnya).
        - **Opsi Pemanfaatan PALING TIDAK MUNGKIN (1 Opsi):** (Sebutkan 1 opsi pemanfaatan yang paling tidak cocok/berguna untuk aset ini beserta alasannya).

        ---SECTION---

        ### 📝 KESIMPULAN AKHIR
        (Berikan 1 paragraf kesimpulan eksekutif yang tegas, padat, dan langsung pada kesimpulan strategis untuk pimpinan mengenai keputusan pemanfaatan/lelang aset ini).
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

        # 5. MENAMPILKAN HASIL DENGAN UI KOTAK-KOTAK (BOX CONTAINERS)
        if response and response.text:
            st.success("✅ Laporan Berhasil Disusun!")
            
            # --- KOTAK 1: IDENTITAS ASET & LINK GPS (Dibuat native dengan Python) ---
            with st.container(border=True):
                st.markdown("### 📌 IDENTITAS & LOKASI ASET")
                st.write(f"**Alamat Lengkap:** {alamat_aset}")
                
                st.write("**Koordinat GPS (Klik ikon di kanan kotak untuk copas):**")
                # Fitur rahasia: st.code punya tombol copas otomatis!
                st.code(f"{koordinat_lat}, {koordinat_lng}", language="text")
                
                # Membuat tombol link asli yang bisa diklik
                col_map, col_earth = st.columns(2)
                url_maps = f"https://www.google.com/maps?q={koordinat_lat},{koordinat_lng}"
                url_earth = f"https://earth.google.com/web/search/{koordinat_lat},{koordinat_lng}"
                
                with col_map:
                    st.link_button("🗺️ Buka di Google Maps", url_maps, use_container_width=True)
                with col_earth:
                    st.link_button("🌍 Buka di Google Earth", url_earth, use_container_width=True)

            # --- KOTAK 2 SAMPAI SELESAI: HASIL ANALISIS AI ---
            # Python memotong laporan AI berdasarkan kata sandi "---SECTION---"
            bagian_laporan = response.text.split("---SECTION---")
            
            for bagian in bagian_laporan:
                teks_bersih = bagian.strip()
                if teks_bersih: # Pastikan kotaknya tidak kosong
                    with st.container(border=True):
                        st.markdown(teks_bersih)
                        
        else:
            st.error("❌ Gagal memproses laporan. Silakan coba lagi.")
