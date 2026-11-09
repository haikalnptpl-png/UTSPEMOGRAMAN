"""Skrip migrasi satu kali: skema lama -> skema revisi (ERD baru).

Skema lama:
  - layanan tanpa id_kategori (3 layanan generik: Reguler / Express / Kering)
  - detail_transaksi memakai PK (id_transaksi, id_kategori, id_layanan)

Skema baru:
  - layanan memiliki id_kategori (satu baris layanan per kategori)
  - detail_transaksi memakai PK gabungan (id_transaksi, id_layanan)

Data lama dipetakan ke layanan per-kategori yang tarifnya sama dengan
layanan generis aslinya, sehingga rekap historically tetap konsisten.
"""

import sqlite3
from pathlib import Path

PATH_DB = Path(__file__).resolve().parent / "laundry.db"

# key layanan lama -> (kode, nama, tarif) per kategori
LAYANAN_PER_KATEGORI = {
    1: ("LYN01", "Cuci Komplit Reguler", 7000),
    2: ("LYN04", "Cuci Karpet Reguler", 9000),
    3: ("LYN07", "Cuci Boneka Reguler", 12000),
    4: ("LYN10", "Cuci Selimut Reguler", 8000),
}


def main() -> None:
    conn = sqlite3.connect(PATH_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")

    lama = {r["name"]: r for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    print("Tabel lama:", list(lama))

    # ------------------------------------------------------------------ 1. kategori
    kategori_lama = [dict(r) for r in conn.execute("SELECT * FROM kategori")]
    conn.execute("DROP TABLE IF EXISTS kategori_baru")
    conn.execute(
        """CREATE TABLE kategori_baru (
            id_kategori   INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_kategori TEXT NOT NULL UNIQUE COLLATE NOCASE,
            keterangan    TEXT
        )"""
    )
    for k in kategori_lama:
        conn.execute(
            "INSERT INTO kategori_baru (id_kategori, nama_kategori, keterangan) VALUES (?, ?, ?)",
            (k["id_kategori"], k["nama_kategori"], k.get("keterangan")),
        )

    # ------------------------------------------------------------------ 2. layanan
    conn.execute("DROP TABLE IF EXISTS layanan_baru")
    conn.execute(
        """CREATE TABLE layanan_baru (
            id_layanan   INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_layanan TEXT NOT NULL UNIQUE COLLATE NOCASE,
            nama_layanan TEXT NOT NULL,
            satuan       TEXT NOT NULL DEFAULT 'kg',
            tarif_per_kg INTEGER NOT NULL,
            id_kategori  INTEGER NOT NULL REFERENCES kategori_baru(id_kategori) ON DELETE RESTRICT,
            aktif        INTEGER NOT NULL DEFAULT 1
        )"""
    )
    # peta: (id_kategori, id_layanan_lama) -> id_layanan_baru
    peta_layanan = {}
    # layanan generis lama -> id kategori representative
    generik = {r["id_layanan"]: r for r in conn.execute("SELECT * FROM layanan")}
    # tentukan kategori default per layanan lama lewat pemakaian di detail
    kategori_dari_layanan = {}
    for d in conn.execute("SELECT id_kategori, id_layanan FROM detail_transaksi"):
        kategori_dari_layanan.setdefault(d["id_layanan"], d["id_kategori"])

    # bangun layanan per kategori: 3 jenis (Reguler, Express, Kering) x 4 kategori
    # (kode, nama, tarif) untuk tiap kategori
    jenis_per_kategori = {
        1: [("LYN01-PAK", "Cuci Komplit Reguler", 7000),
            ("LYN02-PAK", "Cuci Komplit Express", 10000),
            ("LYN03-PAK", "Cuci Kering", 5000)],
        2: [("LYN04-KAR", "Cuci Karpet Reguler", 9000),
            ("LYN05-KAR", "Cuci Karpet Express", 13000),
            ("LYN06-KAR", "Cuci Karpet Kering", 6000)],
        3: [("LYN07-BON", "Cuci Boneka Reguler", 12000),
            ("LYN08-BON", "Cuci Boneka Express", 16000),
            ("LYN09-BON", "Cuci Boneka Kering", 9000)],
        4: [("LYN10-SEL", "Cuci Selimut Reguler", 8000),
            ("LYN11-SEL", "Cuci Selimut Express", 11000),
            ("LYN12-SEL", "Cuci Selimut Kering", 7000)],
    }
    # urutan jenis lama -> urutan baru (Reguler, Express, Kering)
    urut_kategori = [k["id_kategori"] for k in kategori_lama]

    # peta: (id_kategori, urutan_jenis 0/1/2) -> id_layanan_baru
    id_layanan_baru = {}
    for id_kat in urut_kategori:
        for urutan, (kode_baru, nama_baru, tarif) in enumerate(jenis_per_kategori.get(
            id_kat,
            [(f"LYN-X-{id_kat}", "Cuci Reguler", 7000),
             (f"LYN-E-{id_kat}", "Cuci Express", 10000),
             (f"LYN-K-{id_kat}", "Cuci Kering", 5000)],
        )):
            cur = conn.execute(
                """INSERT INTO layanan_baru
                       (kode_layanan, nama_layanan, satuan, tarif_per_kg, id_kategori, aktif)
                   VALUES (?, ?, 'kg', ?, ?, 1)""",
                (kode_baru, nama_baru, tarif, id_kat),
            )
            id_layanan_baru[(id_kat, urutan)] = cur.lastrowid

    # ------------------------------------------------------------------ 3. pelanggan
    conn.execute("DROP TABLE IF EXISTS pelanggan_baru")
    conn.execute(
        """CREATE TABLE pelanggan_baru (
            id_pelanggan  INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_pelanggan TEXT NOT NULL,
            no_hp         TEXT NOT NULL UNIQUE COLLATE NOCASE,
            alamat        TEXT NOT NULL DEFAULT '-'
        )"""
    )
    for p in conn.execute("SELECT * FROM pelanggan"):
        conn.execute(
            "INSERT INTO pelanggan_baru (id_pelanggan, nama_pelanggan, no_hp, alamat) VALUES (?, ?, ?, ?)",
            (p["id_pelanggan"], p["nama"], p["no_hp"], p["alamat"]),
        )

    # ------------------------------------------------------------------ 4. transaksi
    conn.execute("DROP TABLE IF EXISTS transaksi_baru")
    conn.execute(
        """CREATE TABLE transaksi_baru (
            id_transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_nota    TEXT NOT NULL UNIQUE COLLATE NOCASE,
            tanggal      TEXT NOT NULL,
            id_pelanggan INTEGER NOT NULL REFERENCES pelanggan_baru(id_pelanggan) ON DELETE RESTRICT
        )"""
    )
    for t in conn.execute("SELECT * FROM transaksi"):
        conn.execute(
            "INSERT INTO transaksi_baru (id_transaksi, kode_nota, tanggal, id_pelanggan) VALUES (?, ?, ?, ?)",
            (t["id_transaksi"], t["kode_nota"], t["tanggal"], t["id_pelanggan"]),
        )

    # ------------------------------------------------------------------ 5. detail
    conn.execute("DROP TABLE IF EXISTS detail_transaksi_baru")
    conn.execute(
        """CREATE TABLE detail_transaksi_baru (
            id_transaksi INTEGER NOT NULL REFERENCES transaksi_baru(id_transaksi) ON DELETE CASCADE,
            id_layanan   INTEGER NOT NULL REFERENCES layanan_baru(id_layanan) ON DELETE RESTRICT,
            berat        REAL NOT NULL CHECK (berat > 0),
            harga_satuan INTEGER NOT NULL,
            PRIMARY KEY (id_transaksi, id_layanan)
        )"""
    )
    # peta layanan lama -> urutan jenis (0=Reguler, 1=Express, 2=Kering)
    lama_ke_jenis = {}
    for lid, row in generik.items():
        nama = row["nama_layanan"]
        if "Reguler" in nama:
            lama_ke_jenis[lid] = 0
        elif "Express" in nama:
            lama_ke_jenis[lid] = 1
        else:
            lama_ke_jenis[lid] = 2

    for d in conn.execute("SELECT * FROM detail_transaksi"):
        id_kat = d["id_kategori"]
        urutan = lama_ke_jenis[d["id_layanan"]]
        id_lay_baru = id_layanan_baru.get((id_kat, urutan))
        if id_lay_baru is None:
            print("  ! lewati detail karena layanan tak dikenal:", dict(d))
            continue
        conn.execute(
            """INSERT INTO detail_transaksi_baru
                   (id_transaksi, id_layanan, berat, harga_satuan)
               VALUES (?, ?, ?, ?)""",
            (d["id_transaksi"], id_lay_baru, d["berat_kg"], d["tarif_satuan"]),
        )

    # ------------------------------------------------------------------ 6. tukar tabel
    # Buang view lama (bergantung pada kolom skema lama) sebelum tabel ditukar.
    for v in conn.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall():
        conn.execute(f"DROP VIEW IF EXISTS {v['name']}")

    for nama in ("detail_transaksi", "transaksi", "layanan", "pelanggan", "kategori"):
        conn.execute(f"DROP TABLE IF EXISTS {nama}")
    conn.execute("ALTER TABLE kategori_baru RENAME TO kategori")
    conn.execute("ALTER TABLE layanan_baru RENAME TO layanan")
    conn.execute("ALTER TABLE pelanggan_baru RENAME TO pelanggan")
    conn.execute("ALTER TABLE transaksi_baru RENAME TO transaksi")
    conn.execute("ALTER TABLE detail_transaksi_baru RENAME TO detail_transaksi")

    # ------------------------------------------------------------------ 7. view baru
    conn.execute(
        """CREATE VIEW IF NOT EXISTS v_rincian_transaksi AS
           SELECT t.kode_nota, t.tanggal, p.nama_pelanggan,
                  k.nama_kategori, l.nama_layanan, d.berat AS berat_kg,
                  d.harga_satuan AS tarif_satuan,
                  CAST(ROUND(d.berat * d.harga_satuan) AS INTEGER) AS subtotal
             FROM detail_transaksi d
             JOIN transaksi t ON t.id_transaksi = d.id_transaksi
             JOIN pelanggan p ON p.id_pelanggan = t.id_pelanggan
             JOIN layanan   l ON l.id_layanan   = d.id_layanan
             JOIN kategori  k ON k.id_kategori  = l.id_kategori"""
    )
    conn.execute(
        """CREATE VIEW IF NOT EXISTS v_nilai_nota AS
           SELECT t.id_transaksi, t.kode_nota, t.tanggal, p.nama_pelanggan,
                  SUM(CAST(ROUND(d.berat * d.harga_satuan) AS INTEGER)) AS total_bayar
             FROM transaksi t
             JOIN pelanggan p        ON p.id_pelanggan = t.id_pelanggan
             JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
            GROUP BY t.id_transaksi, t.kode_nota, t.tanggal, p.nama_pelanggan"""
    )

    # indeks pendukung
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transaksi_tanggal ON transaksi(tanggal)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transaksi_pelanggan ON transaksi(id_pelanggan)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_layanan_kategori ON layanan(id_kategori)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_detail_layanan ON detail_transaksi(id_layanan)")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n--- Hasil ---")
    for t in ("kategori", "layanan", "pelanggan", "transaksi", "detail_transaksi"):
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:20} {n} baris")
    total = conn.execute(
        "SELECT COALESCE(SUM(berat * harga_satuan), 0) FROM detail_transaksi"
    ).fetchone()[0]
    print(f"{'Total pendapatan':20} Rp{int(total):,}".replace(",", "."))
    conn.close()


if __name__ == "__main__":
    main()
