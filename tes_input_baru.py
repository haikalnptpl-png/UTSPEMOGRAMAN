"""Tes end-to-end: memastikan user BISA mengisi data baru sendiri.

Menutupi:
  1. Tambah pelanggan  -> pesan sukses tampil, data masuk DB
  2. Tambah kategori   -> pesan sukses tampil, data masuk DB
  3. Tambah layanan   -> pesan sukses tampil, data masuk DB
  4. Simpan nota      -> pesan sukses tampil, nota + detail masuk DB
  5. Validasi         -> data tidak valid ditolak dengan pesan jelas
  6. Ubah pelanggan   -> pesan sukses tampil, data berubah
  7. Hapus pelanggan  -> pesan sukses tampil, data hilang
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from streamlit.testing.v1 import AppTest

import database

VENV = Path(__file__).resolve().parent / ".laundryvenv" / "Scripts" / "python.exe"


def cari(els, label, ke=0):
    """Mengambil widget berdasarkan label (ke-n jika label sama)."""
    n = 0
    for e in els:
        if e.label == label:
            if n == ke:
                return e
            n += 1
    return None


def bersihkan():
    """Menghapus data uji agar DB kembali bersih."""
    for p in database.daftar_pelanggan():
        if p["nama_pelanggan"].startswith("TES-"):
            try:
                database.hapus_pelanggan(p["id_pelanggan"])
            except Exception:
                pass
    for k in database.daftar_kategori():
        if k["nama_kategori"].startswith("TES-"):
            try:
                database.hapus_kategori(k["id_kategori"])
            except Exception:
                pass
    for l in database.daftar_layanan():
        if l["kode_layanan"].startswith("TEST"):
            try:
                database.hapus_layanan(l["id_layanan"])
            except Exception:
                pass


def buka(menu):
    at = AppTest.from_file("app.py", default_timeout=60)
    at.run()
    at.radio[0].set_value(menu).run()
    return at


def cek(nama, kondisi, detail=""):
    print(f"  [{'OK  ' if kondisi else 'FAIL'}] {nama}{(' — ' + detail) if detail else ''}")
    if not kondisi:
        cek.gagal += 1
    return kondisi


cek.gagal = 0


def main() -> None:
    bersihkan()
    print("=" * 62)
    print("  TES: USER MENGISI DATA BARU SENDIRI")
    print("=" * 62)

    # ---------------------------------------------------- 1. TAMBAH PELANGGAN
    print("\n[1] Tambah Pelanggan baru")
    at = buka("👥  Data Pelanggan")
    cari(at.text_input, "Nama Pelanggan *", 0).set_value("TES-Pelanggan Baru")
    cari(at.text_input, "Nomor HP * (angka saja)", 0).set_value("081777888999")
    cari(at.text_input, "Alamat *", 0).set_value("Jl. Uji Coba No. 1")
    [b for b in at.button if "Simpan Pelanggan" in b.label][0].click()
    at.run()

    cek("pesan sukses tampil", bool(at.success), at.success[0].value if at.success else "tidak ada")
    cek("tidak ada error", not at.error, at.error[0].value if at.error else "")
    di_db = [p for p in database.daftar_pelanggan() if p["nama_pelanggan"] == "TES-Pelanggan Baru"]
    cek("tersimpan di DB", len(di_db) == 1, f"no_hp={di_db[0]['no_hp']}" if di_db else "tidak ditemukan")
    cek("nomor HP tersimpan benar", bool(di_db) and di_db[0]["no_hp"] == "081777888999")

    # ---------------------------------------------------- 2. VALIDASI
    print("\n[2] Validasi input tidak valid")
    at = buka("👥  Data Pelanggan")
    cari(at.text_input, "Nama Pelanggan *", 0).set_value("TES-Dobel")
    cari(at.text_input, "Nomor HP * (angka saja)", 0).set_value("081777888999")  # kembar
    cari(at.text_input, "Alamat *", 0).set_value("Jl. Kembar")
    [b for b in at.button if "Simpan Pelanggan" in b.label][0].click()
    at.run()
    cek("no HP kembar ditolak", bool(at.error), at.error[0].value if at.error else "tidak ada error")
    cek("data kembar tidak masuk DB",
        len([p for p in database.daftar_pelanggan() if p["nama_pelanggan"] == "TES-Dobel"]) == 0)

    at = buka("👥  Data Pelanggan")
    cari(at.text_input, "Nama Pelanggan *", 0).set_value("TES-Kosong")
    cari(at.text_input, "Nomor HP * (angka saja)", 0).set_value("123")
    cari(at.text_input, "Alamat *", 0).set_value("Jl. Pendek")
    [b for b in at.button if "Simpan Pelanggan" in b.label][0].click()
    at.run()
    cek("no HP terlalu pendek ditolak", bool(at.error), at.error[0].value if at.error else "tidak ada error")

    # ---------------------------------------------------- 3. TAMBAH KATEGORI
    print("\n[3] Tambah Kategori baru")
    at = buka("🧺  Kategori & Layanan")
    cari(at.text_input, "Nama Kategori *", 0).set_value("TES-Kategori Baru")
    cari(at.text_input, "Keterangan (opsional)", 0).set_value("Kategori untuk uji coba")
    [b for b in at.button if "Simpan Kategori" in b.label][0].click()
    at.run()
    cek("pesan sukses tampil", bool(at.success), at.success[0].value if at.success else "tidak ada")
    cek("kategori masuk DB",
        len([k for k in database.daftar_kategori() if k["nama_kategori"] == "TES-Kategori Baru"]) == 1)

    # ---------------------------------------------------- 4. TAMBAH LAYANAN
    print("\n[4] Tambah Layanan baru (dengan kategori TES)")
    at = buka("🧺  Kategori & Layanan")
    cari(at.text_input, "Kode Layanan *", 0).set_value("TEST01")
    cari(at.text_input, "Nama Layanan *", 0).set_value("TES-Layanan Baru")
    cari(at.text_input, "Satuan *", 0).set_value("kg")
    cari(at.number_input, "Harga Satuan (Rp) *", 0).set_value(12000)
    [b for b in at.button if "Simpan Layanan" in b.label][0].click()
    at.run()
    cek("pesan sukses tampil", bool(at.success), at.success[0].value if at.success else "tidak ada")
    lay = [l for l in database.daftar_layanan() if l["kode_layanan"] == "TEST01"]
    cek("layanan masuk DB", len(lay) == 1,
        f"tarif={lay[0]['tarif_per_kg']} kategori={lay[0]['id_kategori']}" if lay else "tidak ditemukan")
    cek("harga satuan benar", bool(lay) and lay[0]["tarif_per_kg"] == 12000)
    cek("layanan punya id_kategori", bool(lay) and lay[0]["id_kategori"] is not None)

    # ---------------------------------------------------- 5. SIMPAN NOTA
    print("\n[5] Simpan nota baru di Kasir")
    at = buka("🛒  Kasir")
    cari(at.number_input, "Berat (kg) *", 0).set_value(2.5)
    [b for b in at.button if "Tambah" in b.label and "pelanggan" not in b.label.lower()][0].click()
    at.run()
    keranjang = at.session_state.get("keranjang", [])
    cek("item masuk keranjang", len(keranjang) == 1,
        f"{keranjang[0]['nama_layanan']} {keranjang[0]['berat']}kg" if keranjang else "kosong")

    [b for b in at.button if "SIMPAN NOTA" in b.label][0].click()
    at.run()
    cek("pesan sukses nota tampil", any("berhasil disimpan" in s.value for s in at.success),
        at.success[0].value if at.success else "tidak ada")
    nota_baru = [t for t in database.daftar_nota() if t["kode_nota"].startswith("NOTA-0")]
    cek("nota tersimpan di DB", len(nota_baru) >= 1)

    # ---------------------------------------------------- 6. UBAH PELANGGAN
    print("\n[6] Ubah data pelanggan")
    if di_db:
        pid = di_db[0]["id_pelanggan"]
        at = buka("👥  Data Pelanggan")
        sb = [s for s in at.selectbox if s.label == "Pilih pelanggan"][0]
        sb.set_value(pid)
        at.run()
        # form Ubah = occurrence ke-1 dari label "Nama Pelanggan *"
        ubah = [t for t in at.text_input if t.label == "Nama Pelanggan *"][1]
        ubah.set_value("TES-Pelanggan Diubah")
        at.run()
        [b for b in at.button if "Simpan Perubahan" in b.label][0].click()
        at.run()
        cek("pesan sukses ubah tampil", bool(at.success), at.success[0].value if at.success else "tidak ada")
        p2 = database.pelanggan_ber_id(pid)
        cek("data berubah di DB", p2 and p2["nama_pelanggan"] == "TES-Pelanggan Diubah",
            p2["nama_pelanggan"] if p2 else "-")

    # ---------------------------------------------------- 7. HAPUS PELANGGAN
    print("\n[7] Hapus pelanggan")
    if di_db:
        pid = di_db[0]["id_pelanggan"]
        at = buka("👥  Data Pelanggan")
        sb = [s for s in at.selectbox if s.label == "Pilih pelanggan"]
        sb[1].set_value(pid)   # occurrence ke-1 = form Hapus
        at.run()
        cek_box = [c for c in at.checkbox if "yakin" in c.label.lower()]
        if cek_box:
            cek_box[0].set_value(True)
            at.run()
        [b for b in at.button if "Hapus Pelanggan" in b.label][0].click()
        at.run()
        cek("pesan sukses hapus tampil", bool(at.success), at.success[0].value if at.success else "tidak ada")
        cek("pelanggan hilang dari DB", database.pelanggan_ber_id(pid) is None)

    # ---------------------------------------------------- 8. HAPUS KATEGORI
    print("\n[8] Hapus kategori & layanan uji")
    at = buka("🧺  Kategori & Layanan")
    for l in list(database.daftar_layanan()):
        if l["kode_layanan"] == "TEST01":
            try:
                database.hapus_layanan(l["id_layanan"])
            except Exception:
                pass
    for k in list(database.daftar_kategori()):
        if k["nama_kategori"] == "TES-Kategori Baru":
            try:
                database.hapus_kategori(k["id_kategori"])
            except Exception:
                pass
    cek("kategori uji terhapus",
        len([k for k in database.daftar_kategori() if k["nama_kategori"] == "TES-Kategori Baru"]) == 0)

    # ---------------------------------------------------- RINGKASAN
    bersihkan()
    print()
    print("=" * 62)
    if cek.gagal == 0:
        print(f"  ✅ SEMUA TES LULUS — user bisa mengisi data baru sendiri")
    else:
        print(f"  ❌ {cek.gagal} TES GAGAL")
    print("=" * 62)
    r = database.ringkasan()
    print(f"  DB akhir: {r['jumlah_transaksi']} nota, {r['jumlah_pelanggan']} pelanggan, "
          f"{r['jumlah_layanan']} layanan, omzet {r['total_pendapatan']}")


if __name__ == "__main__":
    main()
