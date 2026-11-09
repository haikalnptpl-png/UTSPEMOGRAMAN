"""Skrip bantu: beri key unik pada widget form kategori & layanan.

Tujuan: form "Tambah" dan form "Ubah" memakai label yang sama, sehingga
Streamlit menganggapnya widget yang sama dan nilai form "Ubah" ikut ter-reset
saat form "Tambah" disubmit. Key unik per-konteks 이를 pisahkan.
"""

import io

P = "app.py"

PAIRS = [
    # --- kategori: tambah
    ('nama = c1.text_input("Nama Kategori *", placeholder="Contoh: Pakaian")',
     'nama = c1.text_input("Nama Kategori *", placeholder="Contoh: Pakaian", key="tk_nama")'),
    ('ket = c2.text_input("Keterangan (opsional)", placeholder="Contoh: Cucian pakaian harian")',
     'ket = c2.text_input("Keterangan (opsional)", placeholder="Contoh: Cucian pakaian harian", key="tk_ket")'),
    # --- kategori: ubah
    ('nama = c1.text_input("Nama Kategori *", value=lama["nama_kategori"])',
     'nama = c1.text_input("Nama Kategori *", value=lama["nama_kategori"], key=f"uk_nama_{idx}")'),
    ('ket = c2.text_input("Keterangan", value=lama["keterangan"] or "")',
     'ket = c2.text_input("Keterangan", value=lama["keterangan"] or "", key=f"uk_ket_{idx}")'),
    # --- layanan: tambah
    ('kode = c1.text_input("Kode Layanan *", placeholder="LYN13")',
     'kode = c1.text_input("Kode Layanan *", placeholder="LYN13-PAK", key="tl_kode")'),
    ('nama = c2.text_input("Nama Layanan *", placeholder="Cuci Sepatu Reguler")',
     'nama = c2.text_input("Nama Layanan *", placeholder="Cuci Sepatu Reguler", key="tl_nama")'),
    ('satuan = c3.text_input("Satuan *", value="kg")',
     'satuan = c3.text_input("Satuan *", value="kg", key="tl_satuan")'),
    ('id_kat = c4.selectbox("Kategori *", list(peta_k), format_func=lambda i: peta_k[i])',
     'id_kat = c4.selectbox("Kategori *", list(peta_k), format_func=lambda i: peta_k[i], key="tl_kategori")'),
    ('tarif = c5.number_input("Harga Satuan (Rp) *", min_value=0, step=500, value=7000)',
     'tarif = c5.number_input("Harga Satuan (Rp) *", min_value=0, step=500, value=7000, key="tl_tarif")'),
    # --- layanan: ubah
    ('kode = c1.text_input("Kode Layanan *", value=lama["kode_layanan"])',
     'kode = c1.text_input("Kode Layanan *", value=lama["kode_layanan"], key=f"ul_kode_{idx}")'),
    ('nama = c2.text_input("Nama Layanan *", value=lama["nama_layanan"])',
     'nama = c2.text_input("Nama Layanan *", value=lama["nama_layanan"], key=f"ul_nama_{idx}")'),
    ('satuan = c3.text_input("Satuan *", value=lama["satuan"])',
     'satuan = c3.text_input("Satuan *", value=lama["satuan"], key=f"ul_satuan_{idx}")'),
    ('format_func=lambda i: peta_k[i],\n                    )\n                    tarif = c5.number_input("Harga Satuan (Rp) *", min_value=0, step=500, value=int(lama["tarif_per_kg"]))',
     'format_func=lambda i: peta_k[i],\n                        key=f"ul_kategori_{idx}",\n                    )\n                    tarif = c5.number_input("Harga Satuan (Rp) *", min_value=0, step=500, value=int(lama["tarif_per_kg"]), key=f"ul_tarif_{idx}")'),
    # --- selectbox kategori di form ubah kategori
    ('idx = st.selectbox("Pilih kategori", list(peta), format_func=lambda i: peta[i], key="ubah_kat_pilih")',
     'idx = st.selectbox("Pilih kategori", list(peta), format_func=lambda i: peta[i], key="ubah_kat_pilih")'),
    ('idx = st.selectbox("Pilih layanan", list(peta), format_func=lambda i: peta[i], key="ubah_lay_pilih")',
     'idx = st.selectbox("Pilih layanan", list(peta), format_func=lambda i: peta[i], key="ubah_lay_pilih")'),
]


def main() -> None:
    s = io.open(P, encoding="utf-8").read()
    for a, b in PAIRS:
        if a not in s:
            print("LEWAT:", a[:70].replace("\n", " "))
            continue
        s = s.replace(a, b, 1)
    io.open(P, "w", encoding="utf-8").write(s)
    print("selesai")


if __name__ == "__main__":
    main()
