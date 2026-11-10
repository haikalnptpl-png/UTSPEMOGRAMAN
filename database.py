"""database.py — Lapisan data untuk Sistem Administrasi Transaksi ULTRA LAUNDRY.

Modul ini menangani seluruh akses ke basis data SQLite:

  * pembuatan skema sesuai ERD revisi,
  * pengisian data awal (kategori, layanan, pelanggan, dan transaksi contoh),
  * operasi CRUD untuk setiap entitas,
  * query pelaporan untuk halaman Beranda.

Aturan skema revisi yang diterapkan di sini:

  1. Tabel ``layanan`` berada di bawah ``kategori`` (layanan memiliki ``id_kategori``).
  2. Nomor HP pada ``pelanggan`` bersifat UNIQUE.
  3. ``detail_transaksi`` memakai primary key gabungan ``(id_transaksi, id_layanan)``.
  4. ``detail_transaksi`` tidak lagi memuat ``id_kategori`` (sudah diwakili layanan).
  5. ``detail_transaksi`` menyimpan ``harga_satuan`` yang disalin dari tarif saat nota dibuat.
  6. Tabel ``transaksi`` tidak menyimpan total bayar — total dihitung secara dinamis.

Foreign key SQLite diaktifkan pada setiap koneksi supaya aturan referensi
(nama lain: ``ON DELETE RESTRICT``) benar-benar ditegakkan oleh mesin database.
"""

from __future__ import annotations

import math
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

# ------------------------------------------------------------------ konfigurasi

BASE_DIR = Path(__file__).resolve().parent
NAMA_DB = "laundry.db"
PATH_DB = BASE_DIR / NAMA_DB


# ------------------------------------------------------------------- utilitas

def bulat(nilai: float) -> int:
    """Pembulatan ke rupiah penuh (setengah ke atas)."""
    return int(math.floor(float(nilai) + 0.5))


@contextmanager
def koneksi():
    """Membuka koneksi SQLite dengan foreign key aktif."""
    conn = sqlite3.connect(PATH_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _baris(rows) -> list[dict]:
    """Mengubah kumpulan sqlite3.Row menjadi list of dict."""
    return [dict(r) for r in rows]


# --------------------------------------------------------------------- skema

SKEMA = """
CREATE TABLE IF NOT EXISTS kategori (
    id_kategori   INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_kategori TEXT NOT NULL UNIQUE COLLATE NOCASE
                  CHECK (length(trim(nama_kategori)) > 0),
    keterangan    TEXT
);

CREATE TABLE IF NOT EXISTS layanan (
    id_layanan   INTEGER PRIMARY KEY AUTOINCREMENT,
    kode_layanan TEXT NOT NULL UNIQUE COLLATE NOCASE
                 CHECK (length(trim(kode_layanan)) > 0),
    nama_layanan TEXT NOT NULL
                 CHECK (length(trim(nama_layanan)) > 0),
    satuan       TEXT NOT NULL DEFAULT 'kg'
                 CHECK (length(trim(satuan)) > 0),
    tarif_per_kg INTEGER NOT NULL
                 CHECK (typeof(tarif_per_kg) = 'integer' AND tarif_per_kg >= 0),
    id_kategori  INTEGER NOT NULL
                 REFERENCES kategori(id_kategori) ON DELETE RESTRICT,
    aktif        INTEGER NOT NULL DEFAULT 1
                 CHECK (aktif IN (0, 1))
);

CREATE TABLE IF NOT EXISTS pelanggan (
    id_pelanggan  INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_pelanggan TEXT NOT NULL
                  CHECK (length(trim(nama_pelanggan)) > 0),
    no_hp         TEXT NOT NULL UNIQUE COLLATE NOCASE
                  CHECK (length(trim(no_hp)) > 0),
    alamat        TEXT NOT NULL DEFAULT '-'
                  CHECK (length(trim(alamat)) > 0)
);

CREATE TABLE IF NOT EXISTS transaksi (
    id_transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
    kode_nota    TEXT NOT NULL UNIQUE COLLATE NOCASE
                 CHECK (length(trim(kode_nota)) > 0),
    tanggal      TEXT NOT NULL
                 CHECK (date(tanggal) IS NOT NULL AND date(tanggal) = tanggal),
    id_pelanggan INTEGER NOT NULL
                 REFERENCES pelanggan(id_pelanggan) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS detail_transaksi (
    id_transaksi INTEGER NOT NULL
                 REFERENCES transaksi(id_transaksi) ON DELETE CASCADE,
    id_layanan   INTEGER NOT NULL
                 REFERENCES layanan(id_layanan) ON DELETE RESTRICT,
    berat        REAL NOT NULL CHECK (berat > 0),
    harga_satuan INTEGER NOT NULL
                 CHECK (typeof(harga_satuan) = 'integer' AND harga_satuan >= 0),
    PRIMARY KEY (id_transaksi, id_layanan)
);

CREATE INDEX IF NOT EXISTS idx_transaksi_tanggal ON transaksi(tanggal);
CREATE INDEX IF NOT EXISTS idx_transaksi_pelanggan ON transaksi(id_pelanggan);
CREATE INDEX IF NOT EXISTS idx_layanan_kategori ON layanan(id_kategori);
CREATE INDEX IF NOT EXISTS idx_detail_layanan ON detail_transaksi(id_layanan);
"""


def inisialisasi() -> None:
    """Membuat skema bila belum ada dan mengisi data awal bila tabel masih kosong."""
    with koneksi() as conn:
        conn.executescript(SKEMA)
        kosong = conn.execute("SELECT COUNT(*) FROM kategori").fetchone()[0] == 0
        if kosong:
            isi_data_awal(conn)


# --------------------------------------------------------------- data awal

def isi_data_awal(conn: sqlite3.Connection) -> None:
    """Mengisi kategori, layanan, pelanggan, dan transaksi contoh.

    Total pendapatan data contoh = Rp117.000 dari 4 transaksi, sesuai
    hasil rekap yang dipakai pada dokumentasi proyek.
    """
    kategori = [
        ("Pakaian", "Cucian baju, kemeja, celana, dan pakaian harian"),
        ("Karpet", "Cucian karpet lantai dan permadani ruangan"),
        ("Boneka", "Cucian boneka berbagai ukuran"),
        ("Selimut", "Cucian selimut tidur dan bedcover"),
        ("Sprei", "Cucian sprei, bed sheet, dan sarung bantal/guling"),
    ]
    id_kategori: dict[str, int] = {}
    for nama, ket in kategori:
        cur = conn.execute(
            "INSERT INTO kategori (nama_kategori, keterangan) VALUES (?, ?)", (nama, ket)
        )
        id_kategori[nama] = cur.lastrowid

    # (kode, nama layanan, satuan, tarif per kg, kategori induk)
    layanan = [
        ("LYN01-PAK", "Cuci Komplit Reguler", "kg", 7000, "Pakaian"),
        ("LYN02-PAK", "Cuci Komplit Express", "kg", 10000, "Pakaian"),
        ("LYN03-PAK", "Cuci Kering", "kg", 5000, "Pakaian"),
        ("LYN04-KAR", "Cuci Karpet Reguler", "kg", 9000, "Karpet"),
        ("LYN05-KAR", "Cuci Karpet Express", "kg", 13000, "Karpet"),
        ("LYN06-KAR", "Cuci Karpet Kering", "kg", 6000, "Karpet"),
        ("LYN07-BON", "Cuci Boneka Reguler", "kg", 12000, "Boneka"),
        ("LYN08-BON", "Cuci Boneka Express", "kg", 16000, "Boneka"),
        ("LYN09-BON", "Cuci Boneka Kering", "kg", 9000, "Boneka"),
        ("LYN10-SEL", "Cuci Selimut Reguler", "kg", 8000, "Selimut"),
        ("LYN11-SEL", "Cuci Selimut Express", "kg", 11000, "Selimut"),
        ("LYN12-SEL", "Cuci Selimut Kering", "kg", 7000, "Selimut"),
        ("LYN13-SPR", "Cuci Sprei Reguler", "kg", 8000, "Sprei"),
        ("LYN14-SPR", "Cuci Sprei Express", "kg", 11000, "Sprei"),
        ("LYN15-SPR", "Cuci Sprei Kering", "kg", 6000, "Sprei"),
    ]
    id_layanan: dict[str, int] = {}
    for kode, nama, satuan, tarif, induk in layanan:
        cur = conn.execute(
            """INSERT INTO layanan
                   (kode_layanan, nama_layanan, satuan, tarif_per_kg, id_kategori, aktif)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (kode, nama, satuan, tarif, id_kategori[induk]),
        )
        id_layanan[kode] = cur.lastrowid

    pelanggan = [
        ("Nadine Azzahra", "081234567891", "Jl. Banjarsari Selatan No. 12"),
        ("Rayhan Mahendra", "085712343345", "Kost Griya Tembalang Blok A3"),
        ("Ziva Maharani", "082198765433", "Perum Bukit Diponegoro C-15"),
        ("Daffa Pratama", "081345678904", "Jl. Gondang Raya No. 28"),
        ("Reva Anindya", "081257689011", "Jl. Papandayan No. 35, Kota Semarang"),
    ]
    id_pelanggan: list[int] = []
    for nama, hp, alamat in pelanggan:
        cur = conn.execute(
            "INSERT INTO pelanggan (nama_pelanggan, no_hp, alamat) VALUES (?, ?, ?)",
            (nama, hp, alamat),
        )
        id_pelanggan.append(cur.lastrowid)

    # (kode nota, tanggal, index pelanggan, [(kode layanan, berat)])
    transaksi = [
        ("NOTA-001", "2026-10-12", 0, [("LYN01-PAK", 5.0)]),
        ("NOTA-002", "2026-10-13", 1, [("LYN02-PAK", 4.0)]),
        ("NOTA-003", "2026-10-14", 2, [("LYN06-KAR", 5.0)]),
        ("NOTA-004", "2026-10-14", 3, [("LYN07-BON", 1.0)]),
    ]
    tarif_layanan = {l[0]: l[3] for l in layanan}
    for kode, tgl, idx_pel, item in transaksi:
        cur = conn.execute(
            "INSERT INTO transaksi (kode_nota, tanggal, id_pelanggan) VALUES (?, ?, ?)",
            (kode, tgl, id_pelanggan[idx_pel]),
        )
        id_trx = cur.lastrowid
        for kode_lay, berat in item:
            conn.execute(
                """INSERT INTO detail_transaksi
                       (id_transaksi, id_layanan, berat, harga_satuan)
                   VALUES (?, ?, ?, ?)""",
                (id_trx, id_layanan[kode_lay], berat, tarif_layanan[kode_lay]),
            )


# ------------------------------------------------------------------- kategori

def daftar_kategori() -> list[dict]:
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT k.id_kategori, k.nama_kategori, k.keterangan,
                      COUNT(l.id_layanan) AS jumlah_layanan
                 FROM kategori k
                 LEFT JOIN layanan l ON l.id_kategori = k.id_kategori
                GROUP BY k.id_kategori
                ORDER BY k.nama_kategori"""
        ))


def kategori_ber_id(id_kategori: int) -> dict | None:
    with koneksi() as conn:
        row = conn.execute(
            "SELECT * FROM kategori WHERE id_kategori = ?", (id_kategori,)
        ).fetchone()
        return dict(row) if row else None


def tambah_kategori(nama: str, keterangan: str | None = None) -> int:
    with koneksi() as conn:
        cur = conn.execute(
            "INSERT INTO kategori (nama_kategori, keterangan) VALUES (?, ?)",
            (nama.strip(), (keterangan or "").strip() or None),
        )
        return cur.lastrowid


def ubah_kategori(id_kategori: int, nama: str, keterangan: str | None = None) -> bool:
    with koneksi() as conn:
        cur = conn.execute(
            "UPDATE kategori SET nama_kategori = ?, keterangan = ? WHERE id_kategori = ?",
            (nama.strip(), (keterangan or "").strip() or None, id_kategori),
        )
        return cur.rowcount > 0


def hapus_kategori(id_kategori: int) -> bool:
    """Menghapus kategori. Ditolak bila masih dipakai layanan."""
    with koneksi() as conn:
        cur = conn.execute("DELETE FROM kategori WHERE id_kategori = ?", (id_kategori,))
        return cur.rowcount > 0


# -------------------------------------------------------------------- layanan

def daftar_layanan() -> list[dict]:
    """Seluruh layanan beserta kategori induknya."""
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT l.id_layanan, l.kode_layanan, l.nama_layanan, l.satuan,
                      l.tarif_per_kg, l.id_kategori, l.aktif, k.nama_kategori
                 FROM layanan l
                 JOIN kategori k ON k.id_kategori = l.id_kategori
                ORDER BY k.nama_kategori, l.nama_layanan"""
        ))


def daftar_layanan_aktif() -> list[dict]:
    """Hanya layanan aktif — inilah yang muncul pada pilihan di menu Kasir."""
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT l.id_layanan, l.kode_layanan, l.nama_layanan, l.satuan,
                      l.tarif_per_kg, l.id_kategori, l.aktif, k.nama_kategori
                 FROM layanan l
                 JOIN kategori k ON k.id_kategori = l.id_kategori
                WHERE l.aktif = 1
                ORDER BY k.nama_kategori, l.nama_layanan"""
        ))


def layanan_ber_id(id_layanan: int) -> dict | None:
    with koneksi() as conn:
        row = conn.execute(
            """SELECT l.*, k.nama_kategori
                 FROM layanan l JOIN kategori k ON k.id_kategori = l.id_kategori
                WHERE l.id_layanan = ?""",
            (id_layanan,),
        ).fetchone()
        return dict(row) if row else None


def tambah_layanan(kode: str, nama: str, satuan: str, tarif: int,
                    id_kategori: int) -> int:
    with koneksi() as conn:
        cur = conn.execute(
            """INSERT INTO layanan
                   (kode_layanan, nama_layanan, satuan, tarif_per_kg, id_kategori, aktif)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (kode.strip().upper(), nama.strip(), satuan.strip() or "kg", int(tarif), id_kategori),
        )
        return cur.lastrowid


def ubah_layanan(id_layanan: int, kode: str, nama: str, satuan: str,
                 tarif: int, id_kategori: int) -> bool:
    with koneksi() as conn:
        cur = conn.execute(
            """UPDATE layanan
                  SET kode_layanan = ?, nama_layanan = ?, satuan = ?,
                      tarif_per_kg = ?, id_kategori = ?
                WHERE id_layanan = ?""",
            (kode.strip().upper(), nama.strip(), satuan.strip() or "kg",
             int(tarif), id_kategori, id_layanan),
        )
        return cur.rowcount > 0


def set_aktif_layanan(id_layanan: int, aktif: bool) -> bool:
    """Mengaktifkan/menonaktifkan layanan.

    Layanan nonaktif tidak muncul pada pilihan transaksi baru, tetapi tetap
    tampil pada nota lama.
    """
    with koneksi() as conn:
        cur = conn.execute(
            "UPDATE layanan SET aktif = ? WHERE id_layanan = ?",
            (1 if aktif else 0, id_layanan),
        )
        return cur.rowcount > 0


def hapus_layanan(id_layanan: int) -> bool:
    """Menghapus layanan. Ditolak bila layanan sudah dipakai nota lama."""
    with koneksi() as conn:
        cur = conn.execute("DELETE FROM layanan WHERE id_layanan = ?", (id_layanan,))
        return cur.rowcount > 0


# ------------------------------------------------------------------- pelanggan

def daftar_pelanggan(cari: str = "") -> list[dict]:
    with koneksi() as conn:
        if cari.strip():
            pola = f"%{cari.strip()}%"
            sql = """SELECT p.id_pelanggan, p.nama_pelanggan, p.no_hp, p.alamat,
                            COUNT(t.id_transaksi) AS jumlah_nota,
                            COALESCE(SUM(d.subtotal), 0) AS total_belanja
                       FROM pelanggan p
                       LEFT JOIN transaksi t ON t.id_pelanggan = p.id_pelanggan
                       LEFT JOIN (SELECT id_transaksi, SUM(berat * harga_satuan) AS subtotal
                                    FROM detail_transaksi GROUP BY id_transaksi) d
                              ON d.id_transaksi = t.id_transaksi
                      WHERE p.nama_pelanggan LIKE ? OR p.no_hp LIKE ?
                      GROUP BY p.id_pelanggan
                      ORDER BY p.nama_pelanggan"""
            return _baris(conn.execute(sql, (pola, pola)))
        sql = """SELECT p.id_pelanggan, p.nama_pelanggan, p.no_hp, p.alamat,
                        COUNT(t.id_transaksi) AS jumlah_nota,
                        COALESCE(SUM(d.subtotal), 0) AS total_belanja
                   FROM pelanggan p
                   LEFT JOIN transaksi t ON t.id_pelanggan = p.id_pelanggan
                   LEFT JOIN (SELECT id_transaksi, SUM(berat * harga_satuan) AS subtotal
                                FROM detail_transaksi GROUP BY id_transaksi) d
                          ON d.id_transaksi = t.id_transaksi
                  GROUP BY p.id_pelanggan
                  ORDER BY p.nama_pelanggan"""
        return _baris(conn.execute(sql))


def pelanggan_ber_id(id_pelanggan: int) -> dict | None:
    with koneksi() as conn:
        row = conn.execute(
            "SELECT * FROM pelanggan WHERE id_pelanggan = ?", (id_pelanggan,)
        ).fetchone()
        return dict(row) if row else None


def tambah_pelanggan(nama: str, no_hp: str, alamat: str) -> int:
    with koneksi() as conn:
        cur = conn.execute(
            "INSERT INTO pelanggan (nama_pelanggan, no_hp, alamat) VALUES (?, ?, ?)",
            (nama.strip(), no_hp.strip(), alamat.strip() or "-"),
        )
        return cur.lastrowid


def ubah_pelanggan(id_pelanggan: int, nama: str, no_hp: str, alamat: str) -> bool:
    with koneksi() as conn:
        cur = conn.execute(
            """UPDATE pelanggan
                  SET nama_pelanggan = ?, no_hp = ?, alamat = ?
                WHERE id_pelanggan = ?""",
            (nama.strip(), no_hp.strip(), alamat.strip() or "-", id_pelanggan),
        )
        return cur.rowcount > 0


def hapus_pelanggan(id_pelanggan: int) -> bool:
    """Menghapus pelanggan. Ditolak bila pelanggan masih punya nota."""
    with koneksi() as conn:
        cur = conn.execute("DELETE FROM pelanggan WHERE id_pelanggan = ?", (id_pelanggan,))
        return cur.rowcount > 0


# ------------------------------------------------------------------ transaksi

def kode_nota_berikutnya() -> str:
    """Menghasilkan kode nota berikutnya, mis. NOTA-005."""
    with koneksi() as conn:
        row = conn.execute(
            """SELECT kode_nota FROM transaksi
                WHERE kode_nota LIKE 'NOTA-%'
                ORDER BY CAST(SUBSTR(kode_nota, 6) AS INTEGER) DESC LIMIT 1"""
        ).fetchone()
        if not row:
            return "NOTA-001"
        angka = row["kode_nota"].split("-")[-1]
        try:
            return f"NOTA-{int(angka) + 1:03d}"
        except ValueError:
            return f"NOTA-{datetime.now().strftime('%d%m%Y-%H%M%S')}"


def simpan_transaksi(kode_nota: str, tanggal: str, id_pelanggan: int,
                     items: list[dict]) -> int:
    """Menyimpan satu nota beserta seluruh baris detailnya sebagai satu kesatuan.

    ``items`` berisi dict ``{"id_layanan": int, "berat": float}``.
    Berat untuk layanan yang sama digabung, dan ``harga_satuan`` disalin dari
    tarif layanan saat nota dibuat sehingga kenaikan tarif tidak mengubah
    nota lama.
    """
    if not items:
        raise ValueError("Nota harus memiliki minimal satu baris cucian.")

    # Gabungkan baris dengan layanan sama.
    gabung: dict[int, float] = {}
    for item in items:
        gabung[item["id_layanan"]] = gabung.get(item["id_layanan"], 0.0) + float(item["berat"])

    with koneksi() as conn:
        cur = conn.execute(
            """INSERT INTO transaksi (kode_nota, tanggal, id_pelanggan)
               VALUES (?, ?, ?)""",
            (kode_nota.strip().upper(), tanggal, id_pelanggan),
        )
        id_transaksi = cur.lastrowid
        for id_layanan, berat in gabung.items():
            if berat <= 0:
                raise ValueError("Berat harus lebih dari 0 kg.")
            tarif = conn.execute(
                "SELECT tarif_per_kg FROM layanan WHERE id_layanan = ?", (id_layanan,)
            ).fetchone()
            if tarif is None:
                raise ValueError("Layanan tidak ditemukan.")
            conn.execute(
                """INSERT INTO detail_transaksi
                       (id_transaksi, id_layanan, berat, harga_satuan)
                   VALUES (?, ?, ?, ?)""",
                (id_transaksi, id_layanan, berat, tarif["tarif_per_kg"]),
            )
        return id_transaksi


def daftar_nota(cari: str = "") -> list[dict]:
    """Daftar seluruh nota beserta total yang dihitung dinamis."""
    with koneksi() as conn:
        dasar = """SELECT t.id_transaksi, t.kode_nota, t.tanggal,
                          p.nama_pelanggan, p.no_hp,
                          COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total,
                          COALESCE(SUM(d.berat), 0) AS total_berat,
                          COUNT(d.id_layanan) AS jumlah_item
                     FROM transaksi t
                     JOIN pelanggan p ON p.id_pelanggan = t.id_pelanggan
                     LEFT JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi"""
        if cari.strip():
            pola = f"%{cari.strip()}%"
            sql = dasar + """ WHERE t.kode_nota LIKE ? OR p.nama_pelanggan LIKE ?
                             GROUP BY t.id_transaksi
                             ORDER BY t.tanggal DESC, t.id_transaksi DESC"""
            return _baris(conn.execute(sql, (pola, pola)))
        sql = dasar + """ GROUP BY t.id_transaksi
                         ORDER BY t.tanggal DESC, t.id_transaksi DESC"""
        return _baris(conn.execute(sql))


def info_nota(kode_nota: str) -> dict | None:
    """Header nota: kode, tanggal, dan data pelanggan."""
    with koneksi() as conn:
        row = conn.execute(
            """SELECT t.id_transaksi, t.kode_nota, t.tanggal,
                      p.nama_pelanggan, p.no_hp, p.alamat
                 FROM transaksi t JOIN pelanggan p ON p.id_pelanggan = t.id_pelanggan
                WHERE t.kode_nota = ?""",
            (kode_nota.strip().upper(),),
        ).fetchone()
        return dict(row) if row else None


def rincian_nota(kode_nota: str) -> list[dict]:
    """Baris-baris cucian pada satu nota beserta subtotal."""
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT d.id_layanan, l.kode_layanan, l.nama_layanan, l.satuan,
                      k.nama_kategori, d.berat, d.harga_satuan,
                      d.berat * d.harga_satuan AS subtotal
                 FROM detail_transaksi d
                 JOIN transaksi t ON t.id_transaksi = d.id_transaksi
                 JOIN layanan l ON l.id_layanan = d.id_layanan
                 JOIN kategori k ON k.id_kategori = l.id_kategori
                WHERE t.kode_nota = ?
                ORDER BY d.id_layanan""",
            (kode_nota.strip().upper(),),
        ))


def riwayat_pelanggan(id_pelanggan: int) -> list[dict]:
    """Riwayat seluruh nota milik satu pelanggan."""
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT t.kode_nota, t.tanggal,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total,
                      COALESCE(SUM(d.berat), 0) AS total_berat,
                      COUNT(d.id_layanan) AS jumlah_item
                 FROM transaksi t
                 LEFT JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                WHERE t.id_pelanggan = ?
                GROUP BY t.id_transaksi
                ORDER BY t.tanggal DESC, t.id_transaksi DESC""",
            (id_pelanggan,),
        ))


def hapus_nota(kode_nota: str) -> bool:
    """Menghapus nota beserta seluruh baris detailnya (ON DELETE CASCADE)."""
    with koneksi() as conn:
        cur = conn.execute(
            "DELETE FROM transaksi WHERE kode_nota = ?", (kode_nota.strip().upper(),)
        )
        return cur.rowcount > 0


# ------------------------------------------------------------------- laporan

def ringkasan() -> dict:
    """Angka-angka ringkas untuk halaman Beranda.

    Seluruh nilai dihitung dari rincian transaksi, tidak ada yang disimpan.
    """
    with koneksi() as conn:
        row = conn.execute(
            """SELECT COUNT(t.id_transaksi) AS jumlah_transaksi,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total_pendapatan,
                      COALESCE(SUM(d.berat), 0) AS total_berat
                 FROM transaksi t
                 LEFT JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi"""
        ).fetchone()
        pelanggan = conn.execute("SELECT COUNT(*) FROM pelanggan").fetchone()[0]
        layanan = conn.execute("SELECT COUNT(*) FROM layanan WHERE aktif = 1").fetchone()[0]
        kategori = conn.execute("SELECT COUNT(*) FROM kategori").fetchone()[0]

        hari_ini = date.today().isoformat()
        harian = conn.execute(
            """SELECT COUNT(DISTINCT t.id_transaksi) AS jml,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total
                 FROM transaksi t
                 LEFT JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                WHERE t.tanggal = ?""",
            (hari_ini,),
        ).fetchone()

    jml_transaksi = row["jumlah_transaksi"] or 0
    total_pendapatan = bulat(row["total_pendapatan"] or 0)
    return {
        "jumlah_transaksi": jml_transaksi,
        "total_pendapatan": total_pendapatan,
        "total_berat": round(row["total_berat"] or 0, 1),
        "jumlah_pelanggan": pelanggan,
        "jumlah_layanan": layanan,
        "jumlah_kategori": kategori,
        "transaksi_hari_ini": harian["jml"] or 0,
        "pendapatan_hari_ini": bulat(harian["total"] or 0),
        "rata_rata_nota": bulat(total_pendapatan / jml_transaksi) if jml_transaksi else 0,
    }


def pendapatan_per_kategori() -> list[dict]:
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT k.nama_kategori,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total,
                      COALESCE(SUM(d.berat), 0) AS berat
                 FROM detail_transaksi d
                 JOIN layanan l ON l.id_layanan = d.id_layanan
                 JOIN kategori k ON k.id_kategori = l.id_kategori
                GROUP BY k.id_kategori
                ORDER BY total DESC"""
        ))


def pendapatan_per_layanan() -> list[dict]:
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT l.nama_layanan, k.nama_kategori,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total,
                      COALESCE(SUM(d.berat), 0) AS berat
                 FROM detail_transaksi d
                 JOIN layanan l ON l.id_layanan = d.id_layanan
                 JOIN kategori k ON k.id_kategori = l.id_kategori
                GROUP BY l.id_layanan
                ORDER BY total DESC"""
        ))


def pelanggan_teratas() -> list[dict]:
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT p.nama_pelanggan, p.no_hp,
                      COUNT(t.id_transaksi) AS jumlah_nota,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total
                 FROM pelanggan p
                 JOIN transaksi t ON t.id_pelanggan = p.id_pelanggan
                 JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                GROUP BY p.id_pelanggan
                ORDER BY total DESC"""
        ))


def transaksi_terbaru(batas: int = 5) -> list[dict]:
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT t.kode_nota, t.tanggal, p.nama_pelanggan,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total
                 FROM transaksi t
                 JOIN pelanggan p ON p.id_pelanggan = t.id_pelanggan
                 LEFT JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                GROUP BY t.id_transaksi
                ORDER BY t.tanggal DESC, t.id_transaksi DESC
                LIMIT ?""",
            (batas,),
        ))


def pendapatan_per_hari(jumlah_hari: int = 14) -> list[dict]:
    """Pendapatan harian untuk grafik tren pada halaman Beranda."""
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT t.tanggal,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total
                 FROM transaksi t
                 JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                WHERE t.tanggal >= date('now', ?)
                GROUP BY t.tanggal
                ORDER BY t.tanggal""",
            (f"-{jumlah_hari} days",),
        ))


def omzet_rentang(mulai: str, sampai: str) -> dict:
    """Ringkasan omzet untuk rentang tanggal tertentu (inklusif).

    ``mulai`` dan ``sampai`` berupa string ISO 'YYYY-MM-DD'. Seluruh nilai
    dihitung dinamis dari detail_transaksi, sama seperti ringkasan().
    """
    with koneksi() as conn:
        row = conn.execute(
            """SELECT COUNT(DISTINCT t.id_transaksi) AS jumlah_transaksi,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total_pendapatan,
                      COALESCE(SUM(d.berat), 0) AS total_berat
                 FROM transaksi t
                 LEFT JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                WHERE t.tanggal BETWEEN ? AND ?""",
            (mulai, sampai),
        ).fetchone()
    jml = row["jumlah_transaksi"] or 0
    total = bulat(row["total_pendapatan"] or 0)
    return {
        "jumlah_transaksi": jml,
        "total_pendapatan": total,
        "total_berat": round(row["total_berat"] or 0, 1),
        "rata_rata_nota": bulat(total / jml) if jml else 0,
    }


def pendapatan_per_hari_rentang(mulai: str, sampai: str) -> list[dict]:
    """Pendapatan harian dalam rentang tanggal (inklusif) untuk grafik omzet."""
    with koneksi() as conn:
        return _baris(conn.execute(
            """SELECT t.tanggal,
                      COALESCE(SUM(d.berat * d.harga_satuan), 0) AS total
                 FROM transaksi t
                 JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                WHERE t.tanggal BETWEEN ? AND ?
                GROUP BY t.tanggal
                ORDER BY t.tanggal""",
            (mulai, sampai),
        ))


def rentang_tanggal_transaksi() -> tuple[str | None, str | None]:
    """Tanggal transaksi terawal dan terakhir, untuk preset 'Semua Data'."""
    with koneksi() as conn:
        row = conn.execute(
            "SELECT MIN(tanggal) AS awal, MAX(tanggal) AS akhir FROM transaksi"
        ).fetchone()
    return row["awal"], row["akhir"]
