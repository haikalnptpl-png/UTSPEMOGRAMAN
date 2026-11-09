"""Skrip bantu: beri nama variabel dict unik pada setiap selectbox.

Bug: satu variabel (mis. ``peta``) dipakai ulang untuk beberapa dict berbeda
dalam satu fungsi. Closure ``lambda i: peta[i]`` menangkap *cell* yang sama,
sehingga semua selectbox ikut memakai nilai ``peta`` terakhir — labelnya tertukar
(mis. "Pilih kategori" menampilkan label layanan).

Perbaikan: setiap selectbox memakai nama varianya sendiri.
"""

import io

P = "app.py"

# (nama lama, nama baru, occurrence ke-berapa dalam file, baris konteks)
RENAMED = [
    # halaman_pelanggan
    ("peta", "peta_pel_ubah", 1),
    ("peta", "peta_pel_hapus", 2),
    ("peta", "peta_pel_riwayat", 3),
    # halaman_kategori_layanan
    ("peta", "peta_kat_ubah", 4),
    ("peta", "peta_kat_hapus", 5),
    ("peta", "peta_lay_ubah", 6),
    ("peta", "peta_lay_hapus", 7),
    # --- below: dipakai pada selectbox kategori di form tambah/ubah layanan
    ("peta_k", "peta_kat_tambah", 1),
    ("peta_k", "peta_kat_ubah_lay", 2),
]


def main() -> None:
    s = io.open(P, encoding="utf-8").read()
    lines = s.split("\n")

    # Kumpulkan baris yang perlu diubah per-nama-lama.
    target = {}
    for idx, line in enumerate(lines):
        stripped = line.strip()
        for lama, baru, occurrence in RENAMED:
            if stripped.startswith(f"{lama} = {{") and lama not in target:
                target[lama] = []
            if stripped.startswith(f"{lama} = {{"):
                target[lama].append(idx)

    for lama, baru, occurrence in RENAMED:
        idxs = target.get(lama, [])
        if len(idxs) < occurrence:
            print(f"LEWAT: {lama} occurrence {occurrence} (cuma {len(idxs)})")
            continue
        i = idxs[occurrence - 1]
        baris = lines[i]
        # ganti hanya kemunculan nama pada baris definisi dict
        lines[i] = baris.replace(f"{lama} = {{", f"{baru} = {{", 1)

    s = "\n".join(lines)

    # Sekarang ganti pemakaian di dalam format_func untuk tiap selectbox.
    # Dicocokkan lewat key widget agar tidak tertukar.
    pairs = [
        # ubah pelanggan
        ('"Pilih pelanggan", list(peta), format_func=lambda i: peta[i], key="ubah_pelanggan_pilih"',
         '"Pilih pelanggan", list(peta_pel_ubah), format_func=lambda i: peta_pel_ubah[i], key="ubah_pelanggan_pilih"'),
        ('idx = st.selectbox("Pilih pelanggan", list(peta), format_func=lambda i: peta[i], key="hapus_pelanggan_pilih")',
         'idx = st.selectbox("Pilih pelanggan", list(peta_pel_hapus), format_func=lambda i: peta_pel_hapus[i], key="hapus_pelanggan_pilih")'),
        ('idx = st.selectbox("Pilih pelanggan", list(peta), format_func=lambda i: peta[i], key="riwayat_pelanggan_pilih")',
         'idx = st.selectbox("Pilih pelanggan", list(peta_pel_riwayat), format_func=lambda i: peta_pel_riwayat[i], key="riwayat_pelanggan_pilih")'),
        # ubah kategori
        ('idx = st.selectbox("Pilih kategori", list(peta), format_func=lambda i: peta[i], key="ubah_kat_pilih")',
         'idx = st.selectbox("Pilih kategori", list(peta_kat_ubah), format_func=lambda i: peta_kat_ubah[i], key="ubah_kat_pilih")'),
        # hapus kategori
        ('idx = st.selectbox("Pilih kategori", list(peta), format_func=lambda i: peta[i], key="hapus_kat_pilih")',
         'idx = st.selectbox("Pilih kategori", list(peta_kat_hapus), format_func=lambda i: peta_kat_hapus[i], key="hapus_kat_pilih")'),
        # tambah layanan: kategori
        ('id_kat = c4.selectbox("Kategori *", list(peta_k), format_func=lambda i: peta_k[i], key="tl_kategori")',
         'id_kat = c4.selectbox("Kategori *", list(peta_kat_tambah), format_func=lambda i: peta_kat_tambah[i], key="tl_kategori")'),
        # ubah layanan
        ('idx = st.selectbox("Pilih layanan", list(peta), format_func=lambda i: peta[i], key="ubah_lay_pilih")',
         'idx = st.selectbox("Pilih layanan", list(peta_lay_ubah), format_func=lambda i: peta_lay_ubah[i], key="ubah_lay_pilih")'),
        ('idx = st.selectbox("Pilih layanan", list(peta), format_func=lambda i: peta[i], key="hapus_lay_pilih")',
         'idx = st.selectbox("Pilih layanan", list(peta_lay_hapus), format_func=lambda i: peta_lay_hapus[i], key="hapus_lay_pilih")'),
        # ubah layanan: kategori (peta_k occurrence kedua)
        ('format_func=lambda i: peta_k[i],',
         'format_func=lambda i: peta_kat_ubah_lay[i],'),
        ('list(peta_k),', 'list(peta_kat_ubah_lay),'),
    ]
    for a, b in pairs:
        if a not in s:
            print("LEWAT:", a[:75].replace("\n", " "))
            continue
        s = s.replace(a, b, 1)

    io.open(P, "w", encoding="utf-8").write(s)
    print("selesai")


if __name__ == "__main__":
    main()
