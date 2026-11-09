# 🧺 ULTRA LAUNDRY
### Sistem Administrasi Transaksi Operasional

Aplikasi Streamlit + SQLite untuk mengelola operasional laundry: data pelanggan,
kategori & layanan beserta tarifnya, serta transaksi kasir lengkap dengan nota.

---

## 🚀 Cara Menjalankan

### Opsi 1 — Langsung buka di browser (paling praktis) ⭐
Buka file **`ultralaundry.html`** dengan double-click. Tidak perlu Python,
tidak perlu server, tidak perlu install apa pun. Data tersimpan di `localStorage`
browser dan tetap ada walau tab ditutup.

### Opsi 2 — Aplikasi Streamlit (versi penuh dengan database SQLite)

```bash
# Windows
jalankan.bat

# atau manual:
source .laundryvenv/Scripts/activate        # Windows (Git Bash)
# .laundryvenv\Scripts\activate             # Windows (CMD/PowerShell)
streamlit run app.py
```

Aplikasi terbuka di browser pada **http://localhost:8501**.
Data disimpan otomatis di file **`laundry.db`** (SQLite) di folder yang sama.

> Tidak ada halaman login — sistem ini dipakai single user.

---

## 📁 Struktur File

| File | Isi |
|---|---|
| **`ultralaundry.html`** | **Versi web mandiri** — buka langsung di browser, data di `localStorage` |
| `app.py` | Antarmuka Streamlit: 4 menu, form, tabel, dan nota |
| `database.py` | Lapisan data SQLite: skema tabel, seed data, CRUD, query pelaporan |
| `laundry.db` | Basis data SQLite (dibuat otomatis saat pertama dijalankan) |
| `.streamlit/config.toml` | Konfigurasi tema (warna tombol, latar, font) |
| `jalankan.bat` | Launcher cepat untuk versi Streamlit (Windows) |
| `migrasi_skema.py` | Skrip migrasi satu kali dari skema lama → skema revisi |
| `suntik_data_html.py` | Sinkronkan data `laundry.db` → `ultralaundry.html` |
| `laundry_backup_lama.db` | Cadangan data sebelum migrasi |

### Perbedaan kedua versi

| | `ultralaundry.html` | Streamlit (`app.py`) |
|---|---|---|
| Perlu Python | ❌ tidak | ✅ ya |
| Penyimpanan | `localStorage` browser | SQLite (`laundry.db`) |
| Bisa dibuka double-click | ✅ | ❌ |
| Shared antar komputer | ❌ | ✅ (kalau folder-nya dipindah) |

---

## 🧭 Menu Navigasi

### 1. 🏠 Beranda
Ringkasan operasional dengan `st.metric`: total omzet, jumlah nota, jumlah pelanggan,
layanan aktif, total berat dicuci, rata-rata per nota, dan nota hari ini.
Dilengkapi grafik pendapatan per kategori, per layanan, tren 14 hari, 5 transaksi
terbaru, dan pelanggan teratas. **Semua angka dihitung dinamis** dari
`detail_transaksi` — tidak ada total yang disimpan di database.

### 2. 👥 Data Pelanggan
5 tab: Daftar (dengan pencarian & unduh CSV), Tambah, Ubah, Hapus, dan Riwayat
Transaksi. Nomor HP **wajib unik** dan divalidasi 10–14 digit.

### 3. 🧺 Kategori & Layanan
Master data dua tingkat. Kategori (Pakaian, Karpet, Boneka, Selimut) memiliki
**layanan anak** dengan tarif per kg. Layanan dapat di-nonaktifkan (tidak muncul
di pilihan transaksi baru, tetapi nota lama tetap utuh).

### 4. 🛒 Kasir
Alur 3 langkah berstruktur:
1. **Data Nota** — pilih pelanggan, tanggal, kode nota (otomatis `NOTA-XXX`)
2. **Tambah Cucian** — pilih kategori → layanan → berat → tombol **➕ Tambah**
3. **Keranjang** — berat layanan yang sama otomatis **digabung**, total dihitung
   otomatis, lalu tekan **💾 SIMPAN NOTA**

Keranjang disimpan di `st.session_state` dan baru ditulis ke database saat nota
disimpan. Tersedia struk nota cetak (HTML) dan unduh nota (.TXT) / riwayat (.CSV).

---

## 🗄️ ERD (Sudah Direvisi)

```
KATEGORI ──1:N──> LAYANAN ──1:N──┐
    ▲                              │
    └──────────────────────────────┼──> DETAIL_TRANSAKSI ──N:1──> TRANSAKSI
                    (lewat layanan)│        PK: (id_transaksi,     │
PELANGGAN ──1:N──> TRANSAKSI      │             id_layanan)      │
    no_hp UNIQUE                   └── harga_satuan (salinan tarif)
```

| Tabel | Kolom | Catatan |
|---|---|---|
| `kategori` | id_kategori, nama_kategori, keterangan | `nama_kategori` UNIQUE |
| `layanan` | id_layanan, kode_layanan, nama_layanan, satuan, tarif_per_kg, **id_kategori**, aktif | `kode_layanan` UNIQUE, FK ke kategori |
| `pelanggan` | id_pelanggan, nama_pelanggan, **no_hp**, alamat | `no_hp` UNIQUE |
| `transaksi` | id_transaksi, kode_nota, tanggal, id_pelanggan | `kode_nota` UNIQUE, **tanpa kolom total** |
| `detail_transaksi` | id_transaksi, id_layanan, berat, **harga_satuan** | **PK gabungan (id_transaksi, id_layanan)** |

Aturan revisi yang diterapkan:
- ✅ Layanan berada di bawah kategori (memiliki `id_kategori`)
- ✅ Nomor HP pelanggan UNIQUE
- ✅ `detail_transaksi` memakai PK gabungan `id_transaksi` + `id_layanan`
- ✅ `id_kategori` **tidak** ada di `detail_transaksi` (sudah diwakili layanan)
- ✅ `harga_satuan` disalin otomatis dari tarif saat nota dibuat
- ✅ **Tidak ada** kolom total bayar di `transaksi` — total dihitung dinamis

---

## ✅ Aturan Bisnis yang Divalidasi

| Aturan | Perilaku |
|---|---|
| Berat ≤ 0 | Ditolak |
| Nomor HP bukan angka / < 10 digit | Ditolak |
| Nomor HP kembar | Ditolak (UNIQUE) |
| Kode nota kembar | Ditolak (UNIQUE) |
| Kode layanan / nama kategori kembar | Ditolak (UNIQUE) |
| Hapus layanan yang dipakai nota lama | Ditolak (ON DELETE RESTRICT) |
| Hapus pelanggan yang punya nota | Ditolak (ON DELETE RESTRICT) |
| Hapus kategori yang punya layanan | Ditolak (ON DELETE RESTRICT) |
| Berat layanan sama dalam 1 nota | Digabung otomatis |
| Nota tanpa baris | Ditolak |
| Kenaikan tarif | Nota lama **tidak** berubah (harga tersimpan di baris detail) |

---

## 🧪 Verifikasi Otomatis

```bash
# Cek semua halaman tanpa error
python -m pytest test_app.py -v        # atau gunakan AppTest
```

Foreign key SQLite (`PRAGMA foreign_keys = ON`) selalu aktif, sehingga seluruh
aturan referensi benar-benar ditegakkan oleh mesin database — bukan sekadar
validasi di antarmuka.

---

## 👥 Kelompok 1

| Nama | NIM |
|---|---|
| Deyra Taftiar M.B | 4.52.24.3.06 |
| Haikal Ronaldo Napitupulu | 4.52.24.3.11 |
| Latifa Nafiah Putri | 4.52.24.3.14 |
| Revalia Apria Sisviyanti | 4.52.24.3.23 |

**Mata Kuliah:** Pemograman Bisnis & Perancangan Sistem Administrasi
**Dosen Pengampu:** Dwi Budi Santoso, S.Kom., M.Kom
