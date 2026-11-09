sistem administrasi transaksi operasional  - ULTRA LAUNDRY
menggunakan streamlit (virtual environment ada di laundryvenv)
database menggunakan sqlite
buat sesuai dengan transaksi laundry pada umumnya yang sesuai
tidak perlu halaman login
single user
untuk perancangan dan panduan ada di file  [text](<Kelompok 1_Ultra Laundry..pdf>) 
tolong buatkan tampilan web nya jauh lebih bagus, modern, rapi dan cantik
gunakan set_page_config dengan layout wide dan beri icon lucu di judul browser
gunakan sidebar yang rapi untuk navigasi ke 4 menu: beranda, data pelanggan, kategori & layanan, kasir
di halaman beranda percantik dengan st.metric untuk menampilkan ringkasan omzet dan jumlah nota
form input tolong dirapikan menggunakan st.columns atau st.tabs agar desainnya tidak kaku
semua tabel data tampilkan menggunakan st.dataframe agar cantik dan interaktif
beri warna notifikasi st.success atau st.error yang jelas setiap kali simpan data
tolong pisahkan kodenya jadi dua file yaitu database.py dan app.py
untuk database wajib patuhi revisi erd ini:
tabel layanan ditaruh di bawah kategori (layanan punya id_kategori)
tabel pelanggan set nomor hp wajib unik
tabel detail transaksi jadikan id_transaksi dan id_layanan sebagai primary key gabungan
jangan masukkan id_kategori ke detail transaksi karena sudah diwakili oleh layanan
wajib buat kolom harga_satuan di detail transaksi yang isinya dicopy otomatis dari tarif saat nota dibuat
jangan buat kolom total bayar di tabel transaksi karena totalnya harus dihitung dinamis
di menu kasir buatkan sistem keranjang pakai st.session_state sebelum data disimpan ke database