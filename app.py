"""app.py — Antarmuka Sistem Administrasi Transaksi ULTRA LAUNDRY.

Aplikasi Streamlit (layout wide) dengan 4 menu navigasi:

    1. Beranda            — ringkasan omzet, jumlah nota, dan grafik
    2. Data Pelanggan    — CRUD pelanggan + penelusuran riwayat transaksinya
    3. Kategori & Layanan — CRUD kategori dan layanan (harga satuan)
    4. Kasir             — keranjang (session_state) -> simpan nota

Seluruh perhitungan total dilakukan secara dinamis dari tabel
``detail_transaksi``; tidak ada kolom total yang disimpan di database.
"""

from __future__ import annotations

import base64
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

import database

# ---------------------------------------------------------------- konfigurasi

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"
LOGO_URI = (
    "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    if LOGO_PATH.exists()
    else ""
)
LOGO_IMG_HTML = (
    f'<img src="{LOGO_URI}" alt="Ultra Laundry" '
    'style="width:100%;height:100%;object-fit:contain;border-radius:14px;display:block;background:#fff" />'
    if LOGO_URI
    else "🧺"
)
LOGO_HERO_HTML = (
    f'<img class="hero-logo" src="{LOGO_URI}" alt="Logo Ultra Laundry" />'
    if LOGO_URI
    else '<div class="hero-emoji">🏠</div>'
)

# Identitas tim pengembang (ditampilkan pada halaman Beranda).
TIM = {
    "nama": "Team 1",
    "anggota": [
        ("Deyra Taftiar M. B", "4.52.24.3.06"),
        ("Haikal Ronaldo Napitupulu", "4.52.24.3.10"),
        ("Latifa Nafiah Putri", "4.52.24.3.14"),
        ("Revalia Apria Sisviyanti", "4.52.24.3.23"),
    ],
    "dosen": "",
}

st.set_page_config(
    page_title="Ultra Laundry",
    page_icon=Image.open(LOGO_PATH) if LOGO_PATH.exists() else "🧺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------- gaya/CSS

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --ul-primary:   #2563EB;
    --ul-primary-d:#1D4ED8;
    --ul-accent:    #06B6D4;
    --ul-ink:       #0F172A;
    --ul-muted:     #64748B;
    --ul-line:      #E2E8F0;
    --ul-bg:        #F8FAFC;
}

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif; }

/* ---------- Latar aplikasi ---------- */
.stApp {
    background:
        radial-gradient(1100px 520px at 12% -12%, rgba(37,99,235,.10), transparent 60%),
        radial-gradient(900px 480px at 92% -6%, rgba(6,182,212,.12), transparent 62%),
        var(--ul-bg);
}
.block-container { padding-top: 2.1rem; padding-bottom: 3rem; max-width: 1400px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1B36 0%, #10254A 55%, #0E2A4D 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E2E8F0; }
[data-testid="stSidebarUserInfo"] { display: none; }
[data-testid="stSidebar"] hr { border-color: rgba(226,232,240,.18); }

.brand {
    display: flex; align-items: center; gap: .75rem;
    padding: .2rem 0 .9rem 0;
}
.brand-logo {
    width: 46px; height: 46px; flex: 0 0 46px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.45rem; border-radius: 14px;
    background: linear-gradient(135deg, var(--ul-primary), var(--ul-accent));
    box-shadow: 0 8px 20px rgba(37,99,235,.45);
}
.brand-text { line-height: 1.15; }
.brand-name { font-weight: 800; font-size: 1.06rem; letter-spacing: .2px; color: #fff; }
.brand-sub  { font-size: .72rem; color: #93C5FD; letter-spacing: .12em; text-transform: uppercase; }

/* Navigasi radio di sidebar */
[data-testid="stSidebar"] [role="radiogroup"] { gap: .3rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: .58rem .8rem; border-radius: 12px;
    transition: background .16s ease, transform .16s ease;
    cursor: pointer; font-weight: 600; font-size: .93rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.08); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, var(--ul-primary), var(--ul-accent));
    color: #fff !important; box-shadow: 0 6px 16px rgba(37,99,235,.42);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: #fff !important; }
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stMarkdownContainer"] p {
    font-size: .93rem;
}
[data-testid="stSidebar"] .stCaption { color: #94A3B8 !important; }

/* ---------- Hero / judul halaman ---------- */
.hero {
    display: flex; align-items: center; gap: 1rem;
    background: linear-gradient(120deg, #1D4ED8 0%, #2563EB 45%, #06B6D4 100%);
    border-radius: 20px; padding: 1.35rem 1.6rem;
    box-shadow: 0 16px 38px rgba(37,99,235,.28);
    margin-bottom: 1.35rem;
}
.hero-emoji {
    font-size: 2.4rem; line-height: 1;
    background: rgba(255,255,255,.18);
    padding: .6rem .75rem; border-radius: 16px;
    border: 1px solid rgba(255,255,255,.28);
}
.hero-title { font-weight: 800; font-size: 1.5rem; color: #fff; line-height: 1.2; }
.hero-desc  { color: rgba(255,255,255,.88); font-size: .88rem; margin-top: .2rem; }

/* ---------- Kartu metric ---------- */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid var(--ul-line);
    border-radius: 18px;
    padding: 1.05rem 1.15rem 1rem 1.15rem;
    box-shadow: 0 6px 20px rgba(15,23,42,.06);
    transition: transform .16s ease, box-shadow .16s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 32px rgba(15,23,42,.11);
}
[data-testid="stMetricLabel"] p { font-size: .78rem; font-weight: 600; color: var(--ul-muted) !important; text-transform: uppercase; letter-spacing: .05em; }
[data-testid="stMetricValue"] { font-size: 1.62rem !important; font-weight: 800 !important; color: var(--ul-ink) !important; }
[data-testid="stMetricDelta"] { font-size: .8rem !important; }

/* ---------- Sub-judul section ---------- */
.section-title {
    display: flex; align-items: center; gap: .55rem;
    font-weight: 700; font-size: 1.03rem; color: var(--ul-ink);
    margin: .35rem 0 .6rem 0;
}
.section-title span.bar {
    display: inline-block; width: 5px; height: 20px; border-radius: 4px;
    background: linear-gradient(180deg, var(--ul-primary), var(--ul-accent));
}

/* ---------- Panel nota ---------- */
.nota {
    background: #FFFFFF; border: 1px solid var(--ul-line);
    border-radius: 18px; padding: 1.25rem 1.4rem;
    box-shadow: 0 8px 26px rgba(15,23,42,.07);
}
.nota-head {
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 2px dashed var(--ul-line); padding-bottom: .8rem; margin-bottom: .9rem;
}
.nota-kode { font-weight: 800; font-size: 1.2rem; color: var(--ul-ink); }
.nota-total { font-weight: 800; font-size: 1.35rem; color: var(--ul-primary); }
.nota-meta { font-size: .85rem; color: var(--ul-muted); line-height: 1.55; }
.nota-kaki { margin-top: .9rem; padding-top: .8rem; border-top: 2px dashed var(--ul-line);
             font-size: .8rem; color: var(--ul-muted); text-align: center; }

/* ---------- Badge ---------- */
.badge {
    display: inline-block; padding: .16rem .6rem; border-radius: 999px;
    font-size: .73rem; font-weight: 700; letter-spacing: .02em;
}
.badge-ok   { background: #DCFCE7; color: #15803D; }
.badge-off  { background: #F1F5F9; color: #64748B; }

/* ---------- Tombol ---------- */
.stButton > button {
    border-radius: 11px; font-weight: 700; border: 1px solid transparent;
    transition: transform .14s ease, box-shadow .14s ease, filter .14s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(37,99,235,.22); }
/* tombol primary mengikuti tema biru aplikasi */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--ul-primary), var(--ul-primary-d));
    border-color: transparent;
    box-shadow: 0 6px 16px rgba(37,99,235,.32);
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--ul-primary-d), var(--ul-primary));
    box-shadow: 0 10px 22px rgba(37,99,235,.42);
}
.stDownloadButton > button { border-radius: 11px; font-weight: 700; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--ul-line); }
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0; font-weight: 700; font-size: .9rem; padding: .5rem .95rem;
}
.stTabs [aria-selected="true"] { color: var(--ul-primary) !important; }

/* ---------- Tabel ---------- */
[data-testid="stDataFrame"] {
    border-radius: 14px; overflow: hidden;
    border: 1px solid var(--ul-line);
    box-shadow: 0 4px 16px rgba(15,23,42,.05);
}

/* ---------- Input ---------- */
[data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label, [data-testid="stDateInput"] label {
    font-weight: 700; font-size: .82rem; color: var(--ul-ink);
}

/* ---------- Info / pesan ---------- */
[data-testid="stAlert"] { border-radius: 14px; border: 1px solid transparent; }
[data-testid="stAlertContainer"] { border-radius: 14px; }

/* ---------- Logo di hero ---------- */
.hero-logo {
    width: 54px; height: 54px; flex: 0 0 54px;
    border-radius: 14px; object-fit: contain;
    background: #fff; padding: 4px;
    border: 1px solid rgba(255,255,255,.30);
    box-shadow: 0 6px 16px rgba(0,0,0,.16);
}

/* ---------- Kartu ber-border (st.container border=True) ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
    border-color: var(--ul-line);
    box-shadow: 0 4px 16px rgba(15,23,42,.05);
}

/* ---------- Responsif: tablet & HP ---------- */
@media (max-width: 900px) {
    .block-container { padding-top: 1.5rem; padding-left: 1.1rem; padding-right: 1.1rem; }
    .hero { padding: 1.1rem 1.25rem; gap: .8rem; }
    .hero-title { font-size: 1.3rem; }
}
@media (max-width: 640px) {
    .block-container { padding-top: 1.1rem; padding-left: .8rem; padding-right: .8rem; padding-bottom: 2rem; }
    .hero { flex-direction: column; align-items: flex-start; gap: .55rem;
            padding: 1rem 1.1rem; border-radius: 16px; margin-bottom: 1rem; }
    .hero-emoji { font-size: 1.9rem; padding: .45rem .6rem; }
    .hero-logo { width: 46px; height: 46px; flex-basis: 46px; }
    .hero-title { font-size: 1.18rem; }
    .hero-desc  { font-size: .82rem; }
    [data-testid="stMetric"] { padding: .85rem .95rem; border-radius: 14px; }
    [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
    [data-testid="stMetricLabel"] p { font-size: .72rem; }
    .section-title { font-size: .95rem; }
    .nota { padding: 1rem 1.05rem; border-radius: 14px; }
    .nota-kode { font-size: 1.05rem; }
    .nota-total { font-size: 1.15rem; }
    .stTabs [data-baseweb="tab"] { padding: .45rem .65rem; font-size: .82rem; }
    [data-testid="stColumn"] { margin-bottom: .35rem; }
}

/* ---------- Kartu keterangan tim ---------- */
.tim-card {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #FFFFFF 0%, #F3F8FF 100%);
    border: 1px solid var(--ul-line); border-radius: 20px;
    padding: 1.4rem 1.5rem; box-shadow: 0 10px 30px rgba(15,23,42,.07);
}
.tim-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, var(--ul-primary), var(--ul-accent));
}
.tim-head {
    display: flex; justify-content: space-between; align-items: center;
    gap: 1rem; flex-wrap: wrap; margin-bottom: 1.15rem;
}
.tim-title { font-weight: 800; font-size: 1.12rem; color: var(--ul-ink); }
.tim-sub { font-size: .82rem; color: var(--ul-muted); margin-top: .15rem; }
.tim-badge {
    background: linear-gradient(135deg, var(--ul-primary), var(--ul-accent));
    color: #fff; font-weight: 800; font-size: .85rem; letter-spacing: .03em;
    padding: .4rem .95rem; border-radius: 999px;
    box-shadow: 0 6px 16px rgba(37,99,235,.32);
}
.tim-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .8rem; }
.tim-member {
    display: flex; align-items: center; gap: .7rem;
    background: #fff; border: 1px solid var(--ul-line);
    border-radius: 14px; padding: .8rem .85rem;
    transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
}
.tim-member:hover {
    transform: translateY(-3px); border-color: #BFDBFE;
    box-shadow: 0 10px 24px rgba(37,99,235,.14);
}
.tim-avatar {
    width: 42px; height: 42px; flex: 0 0 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: .95rem; color: #fff;
    background: linear-gradient(135deg, var(--ul-primary), var(--ul-accent));
    box-shadow: 0 5px 14px rgba(37,99,235,.3);
}
.tim-info { min-width: 0; }
.tim-nama { font-weight: 700; font-size: .88rem; color: var(--ul-ink); line-height: 1.25; }
.tim-nim {
    font-size: .76rem; color: var(--ul-muted); margin-top: .15rem;
    font-variant-numeric: tabular-nums; letter-spacing: .02em;
}
.tim-dosen {
    margin-top: 1.15rem; padding-top: .95rem; border-top: 1px dashed var(--ul-line);
    font-size: .92rem; color: var(--ul-ink);
}
.tim-dosen-label { font-weight: 700; }
.tim-dosen-nama { color: var(--ul-muted); }
@media (max-width: 640px) {
    .tim-card { padding: 1.1rem 1.15rem; border-radius: 16px; }
    .tim-title { font-size: 1.02rem; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ utilitas

def rupiah(nilai) -> str:
    """Format angka menjadi mata uang Rupiah, mis. 117000 -> 'Rp117.000'."""
    try:
        return f"Rp{int(round(float(nilai))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp0"


def format_berat(nilai) -> str:
    """Format berat, buang angka nol di belakang koma."""
    try:
        return f"{float(nilai):g} kg"
    except (TypeError, ValueError):
        return "0 kg"


def html_tim() -> str:
    """Membangun kartu keterangan tim (Team 1) untuk halaman Beranda."""
    anggota_html = ""
    for nama, nim in TIM["anggota"]:
        inisial = "".join(kata[0] for kata in nama.split()[:2]).upper()
        anggota_html += f"""
          <div class="tim-member">
            <div class="tim-avatar">{inisial}</div>
            <div class="tim-info">
              <div class="tim-nama">{nama}</div>
              <div class="tim-nim">NIM {nim}</div>
            </div>
          </div>"""
    dosen = TIM["dosen"] or "—"
    return f"""
    <div class="tim-card">
      <div class="tim-head">
        <div>
          <div class="tim-title">👥 Keterangan Tim</div>
          <div class="tim-sub">Pengembang Sistem Administrasi Transaksi Ultra Laundry</div>
        </div>
        <div class="tim-badge">{TIM['nama']}</div>
      </div>
      <div class="tim-grid">{anggota_html}
      </div>
      <div class="tim-dosen">
        <span class="tim-dosen-label">Dosen Pengampu:</span>
        <span class="tim-dosen-nama">{dosen}</span>
      </div>
    </div>"""


def pesan_database(e: Exception) -> str:
    """Menerjemahkan galat SQLite menjadi kalimat yang mudah dipahami."""
    teks = str(e)
    if "UNIQUE" in teks.upper():
        return "Data sudah ada — kode layanan, nama kategori, atau nomor HP kembar."
    if "FOREIGN KEY" in teks.upper():
        return "Data masih dipakai oleh nota lama, jadi tidak bisa dihapus."
    if "CHECK" in teks.upper():
        return "Isian tidak memenuhi aturan database (kosong, negatif, atau format salah)."
    return f"Database menolak data: {e}"


def bersihkan_keranjang() -> None:
    st.session_state.keranjang = []


# --------------------------------------------------------- pesan flash

def flash(pesan: str, jenis: str = "success") -> None:
    """Menyimpan pesan notifikasi agar tetap tampil setelah st.rerun().

    Perintah ``st.rerun()`` menghapus seluruh elemen yang sudah dirender,
    termasuk ``st.success``/``st.error``. Karena itu pesannya disimpan dulu di
    ``session_state`` lalu ditampilkan lagi pada render berikutnya.
    """
    st.session_state.flash = (pesan, jenis)


def tampilkan_flash() -> None:
    """Menampilkan pesan flash yang tersimpan (jika ada) lalu membersihkannya."""
    data = st.session_state.pop("flash", None)
    if not data:
        return
    pesan, jenis = data
    if jenis == "error":
        st.error(pesan)
    elif jenis == "warning":
        st.warning(pesan)
    elif jenis == "info":
        st.info(pesan)
    else:
        st.success(pesan)


# -------------------------------------------------------------------- sidebar

def bangun_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="brand">
              <div class="brand-logo">{LOGO_IMG_HTML}</div>
              <div class="brand-text">
                <div class="brand-name">ULTRA LAUNDRY</div>
                <div class="brand-sub">Administrasi Transaksi</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("**🧭 NAVIGASI**")
        menu = st.radio(
            "Menu utama",
            [
                "🏠  Beranda",
                "👥  Data Pelanggan",
                "🧺  Kategori & Layanan",
                "🛒  Kasir",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            """
            <div style="font-size:.78rem;color:#94A3B8;line-height:1.6">
                <b>Ultra Laundry</b><br>
                Sistem Administrasi Transaksi<br>
               Database · <code>laundry.db</code><br><br>
                <span style="color:#64748B">Data tersimpan otomatis di SQLite
                dan tetap ada walau aplikasi ditutup.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return menu


# ------------------------------------------------------------------- BERANDA

def halaman_beranda() -> None:
    tampilkan_flash()
    st.markdown(
        f"""
        <div class="hero">
          {LOGO_HERO_HTML}
          <div>
            <div class="hero-title">Dashboard Ultra Laundry</div>
            <div class="hero-desc">Ringkasan omzet, transaksi, dan aktivitas laundry hari ini.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r = database.ringkasan()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            "💰 Total Omzet",
            rupiah(r["total_pendapatan"]),
            delta=f"{rupiah(r['pendapatan_hari_ini'])} hari ini",
            delta_color="off",
            border=True,
        )
    with k2:
        st.metric(
            "🧾 Jumlah Nota",
            f"{r['jumlah_transaksi']:,}".replace(",", "."),
            delta=f"{r['transaksi_hari_ini']} nota hari ini",
            delta_color="off",
            border=True,
        )
    with k3:
        st.metric(
            "👥 Jumlah Pelanggan",
            f"{r['jumlah_pelanggan']:,}".replace(",", "."),
            border=True,
        )
    with k4:
        st.metric(
            "🧺 Layanan Aktif",
            f"{r['jumlah_layanan']:,}".replace(",", "."),
            delta=f"{r['jumlah_kategori']} kategori",
            delta_color="off",
            border=True,
        )

    st.markdown("")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("⚖️ Total Berat Dicuci", f"{r['total_berat']:g} kg", border=True)
    with s2:
        st.metric("📊 Rata-rata per Nota", rupiah(r["rata_rata_nota"]), border=True)
    with s3:
        st.metric("📅 Nota Hari Ini", f"{r['transaksi_hari_ini']}", border=True)

    st.markdown("")
    st.markdown(
        '<div class="section-title"><span class="bar"></span>📅 Omzet per Rentang Waktu</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        hari_ini = date.today()
        awal_db, akhir_db = database.rentang_tanggal_transaksi()
        if "omzet_range" not in st.session_state:
            st.session_state.omzet_range = (hari_ini - timedelta(days=29), hari_ini)

        pr1, pr2, pr3, pr4 = st.columns(4)
        with pr1:
            if st.button("7 Hari", width="stretch", key="omzet_7"):
                st.session_state.omzet_range = (hari_ini - timedelta(days=6), hari_ini)
        with pr2:
            if st.button("30 Hari", width="stretch", key="omzet_30"):
                st.session_state.omzet_range = (hari_ini - timedelta(days=29), hari_ini)
        with pr3:
            if st.button("Bulan Ini", width="stretch", key="omzet_bulan"):
                st.session_state.omzet_range = (hari_ini.replace(day=1), hari_ini)
        with pr4:
            if st.button("Semua Data", width="stretch", key="omzet_semua"):
                if awal_db and akhir_db:
                    st.session_state.omzet_range = (
                        date.fromisoformat(awal_db), date.fromisoformat(akhir_db)
                    )

        rentang = st.date_input(
            "Pilih rentang tanggal", key="omzet_range", format="DD/MM/YYYY"
        )
        if isinstance(rentang, (tuple, list)):
            mulai, sampai = rentang[0], rentang[-1]
        else:
            mulai = sampai = rentang
        if mulai > sampai:
            mulai, sampai = sampai, mulai

        omzet = database.omzet_rentang(mulai.isoformat(), sampai.isoformat())
        st.caption(
            f"Menampilkan omzet **{mulai.strftime('%d %b %Y')}** – **{sampai.strftime('%d %b %Y')}**."
        )
        o1, o2, o3, o4 = st.columns(4)
        with o1:
            st.metric("💰 Omzet Rentang", rupiah(omzet["total_pendapatan"]), border=True)
        with o2:
            st.metric(
                "🧾 Jumlah Nota",
                f"{omzet['jumlah_transaksi']:,}".replace(",", "."),
                border=True,
            )
        with o3:
            st.metric("⚖️ Total Berat", f"{omzet['total_berat']:g} kg", border=True)
        with o4:
            st.metric("📊 Rata-rata / Nota", rupiah(omzet["rata_rata_nota"]), border=True)

        harian_rentang = database.pendapatan_per_hari_rentang(
            mulai.isoformat(), sampai.isoformat()
        )
        if harian_rentang:
            df = pd.DataFrame(harian_rentang).rename(
                columns={"tanggal": "Tanggal", "total": "Pendapatan (Rp)"}
            )
            st.line_chart(
                df.set_index("Tanggal")["Pendapatan (Rp)"], height=220, color="#2563EB"
            )
        else:
            st.info(
                "Tidak ada transaksi pada rentang ini. Coba preset **Semua Data** "
                "atau pilih rentang tanggal lain."
            )

    st.markdown("")
    st.markdown(
        '<div class="section-title"><span class="bar"></span>📊 Pendapatan & Aktivitas</div>',
        unsafe_allow_html=True,
    )

    g1, g2 = st.columns([1, 1])

    with g1:
        with st.container(border=True):
            st.markdown("**Pendapatan per Kategori**")
            per_kategori = database.pendapatan_per_kategori()
            if per_kategori:
                df = pd.DataFrame(per_kategori).rename(
                    columns={"nama_kategori": "Kategori", "total": "Pendapatan (Rp)", "berat": "Berat (kg)"}
                )
                df["Pendapatan (Rp)"] = df["Pendapatan (Rp)"].astype(float)
                st.bar_chart(df.set_index("Kategori")["Pendapatan (Rp)"], height=265, color="#2563EB")
            else:
                st.info("Belum ada transaksi untuk ditampilkan.")

    with g2:
        with st.container(border=True):
            st.markdown("**Pendapatan per Layanan**")
            per_layanan = database.pendapatan_per_layanan()
            if per_layanan:
                df = pd.DataFrame(per_layanan).rename(
                    columns={
                        "nama_layanan": "Layanan",
                        "nama_kategori": "Kategori",
                        "total": "Pendapatan (Rp)",
                        "berat": "Berat (kg)",
                    }
                )
                st.dataframe(
                    df[["Layanan", "Kategori", "Berat (kg)", "Pendapatan (Rp)"]],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Berat (kg)": st.column_config.NumberColumn(format="%.1f kg"),
                        "Pendapatan (Rp)": st.column_config.NumberColumn(format="Rp %.0f"),
                    },
                )
            else:
                st.info("Belum ada layanan yang terjual.")

    with st.container(border=True):
        st.markdown("**Tren Pendapatan 14 Hari Terakhir**")
        harian = database.pendapatan_per_hari(14)
        if harian:
            df = pd.DataFrame(harian).rename(columns={"tanggal": "Tanggal", "total": "Pendapatan (Rp)"})
            st.line_chart(df.set_index("Tanggal")["Pendapatan (Rp)"], height=250, color="#06B6D4")
        else:
            st.info("Belum ada transaksi pada periode ini.")

    st.markdown("")
    t1, t2 = st.columns([1, 1])

    with t1:
        with st.container(border=True):
            st.markdown("**🕒 5 Transaksi Terbaru**")
            terbaru = database.transaksi_terbaru(5)
            if terbaru:
                df = pd.DataFrame(terbaru).rename(
                    columns={
                        "kode_nota": "Kode Nota",
                        "tanggal": "Tanggal",
                        "nama_pelanggan": "Pelanggan",
                        "total": "Total",
                    }
                )
                df["Total"] = df["Total"].apply(rupiah)
                st.dataframe(
                    df[["Kode Nota", "Tanggal", "Pelanggan", "Total"]],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("Belum ada transaksi.")

    with t2:
        with st.container(border=True):
            st.markdown("**🏆 Pelanggan Teratas**")
            teratas = database.pelanggan_teratas()
            if teratas:
                df = pd.DataFrame(teratas).rename(
                    columns={
                        "nama_pelanggan": "Pelanggan",
                        "no_hp": "No. HP",
                        "jumlah_nota": "Jumlah Nota",
                        "total": "Total",
                    }
                )
                df["Total"] = df["Total"].apply(rupiah)
                st.dataframe(
                    df[["Pelanggan", "No. HP", "Jumlah Nota", "Total"]],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("Belum ada pelanggan yang bertransaksi.")

    st.markdown("")
    st.markdown(html_tim(), unsafe_allow_html=True)


# ------------------------------------------------------- HALAMAN DATA PELANGGAN

def halaman_pelanggan() -> None:
    tampilkan_flash()
    st.markdown(
        """
        <div class="hero">
          <div class="hero-emoji">👥</div>
          <div>
            <div class="hero-title">Data Pelanggan</div>
            <div class="hero-desc">Kelola identitas pelanggan dan menelusuri riwayat transaksinya.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_daftar, tab_tambah, tab_ubah, tab_hapus, tab_riwayat = st.tabs(
        ["📋 Daftar Pelanggan", "➕ Tambah", "✏️ Ubah", "🗑️ Hapus", "🧾 Riwayat Transaksi"]
    )

    # ------------------------------------------------------------- daftar
    with tab_daftar:
        cari = st.text_input(
            "🔍 Cari pelanggan (nama atau nomor HP)", key="cari_pelanggan", placeholder="Ketik nama / no. HP ..."
        )
        data = database.daftar_pelanggan(cari)
        st.markdown(
            '<div class="section-title"><span class="bar"></span>'
            f'Daftar Pelanggan ({len(data)})</div>',
            unsafe_allow_html=True,
        )
        if data:
            df = pd.DataFrame(data).rename(
                columns={
                    "id_pelanggan": "ID",
                    "nama_pelanggan": "Nama Pelanggan",
                    "no_hp": "No. HP",
                    "alamat": "Alamat",
                    "jumlah_nota": "Jumlah Nota",
                    "total_belanja": "Total Belanja",
                }
            )
            df["Total Belanja"] = df["Total Belanja"].apply(rupiah)
            st.dataframe(
                df[["ID", "Nama Pelanggan", "No. HP", "Alamat", "Jumlah Nota", "Total Belanja"]],
                hide_index=True,
                width="stretch",
                column_config={"ID": st.column_config.NumberColumn(format="%d")},
            )
            st.download_button(
                "⬇️ Unduh daftar pelanggan (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                file_name="daftar_pelanggan.csv",
                mime="text/csv",
            )
        else:
            st.info("Belum ada data pelanggan. Gunakan tab **Tambah** untuk mendaftarkan pelanggan baru.")

    # -------------------------------------------------------------- tambah
    with tab_tambah:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Tambah Pelanggan Baru</div>',
            unsafe_allow_html=True,
        )
        with st.form("form_tambah_pelanggan", clear_on_submit=True, border=False):
            c1, c2 = st.columns(2)
            nama = c1.text_input(
                "Nama Pelanggan *", placeholder="Contoh: Nadine Azzahra", key="tp_nama"
            )
            no_hp = c2.text_input(
                "Nomor HP * (angka saja)", placeholder="Contoh: 081234567891", key="tp_hp"
            )
            alamat = st.text_input(
                "Alamat *", placeholder="Contoh: Jl. Banjarsari Selatan No. 12", key="tp_alamat"
            )
            st.markdown("")
            simpan = st.form_submit_button("💾 Simpan Pelanggan", type="primary")
        if simpan:
            if not nama.strip() or not no_hp.strip() or not alamat.strip():
                st.error("Nama, nomor HP, dan alamat wajib diisi.")
            elif not no_hp.strip().isdigit() or not 10 <= len(no_hp.strip()) <= 14:
                st.error("Nomor HP harus berupa angka dan terdiri dari 10 sampai 14 digit.")
            else:
                try:
                    database.tambah_pelanggan(nama, no_hp, alamat)
                    flash(f"✅ Pelanggan **{nama.strip()}** berhasil disimpan.")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"❌ Gagal menyimpan: {pesan_database(e)}")

    # --------------------------------------------------------------- ubah
    with tab_ubah:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Ubah Data Pelanggan</div>',
            unsafe_allow_html=True,
        )
        semua = database.daftar_pelanggan()
        if not semua:
            st.info("Belum ada pelanggan yang dapat diubah.")
        else:
            peta_pel_ubah = {d["id_pelanggan"]: f'{d["nama_pelanggan"]} · {d["no_hp"]}' for d in semua}
            idx = st.selectbox(
                "Pilih pelanggan", list(peta_pel_ubah), format_func=lambda i: peta_pel_ubah[i], key="ubah_pelanggan_pilih"
            )
            lama = database.pelanggan_ber_id(idx)
            with st.form("form_ubah_pelanggan", border=False):
                c1, c2 = st.columns(2)
                # key unik per pelanggan agar isi form ikut berubah saat
                # pelanggan yang dipilih diganti.
                nama = c1.text_input(
                    "Nama Pelanggan *", value=lama["nama_pelanggan"], key=f"up_nama_{idx}"
                )
                no_hp = c2.text_input("Nomor HP *", value=lama["no_hp"], key=f"up_hp_{idx}")
                alamat = st.text_input("Alamat *", value=lama["alamat"], key=f"up_alamat_{idx}")
                st.markdown("")
                simpan = st.form_submit_button("💾 Simpan Perubahan", type="primary")
            if simpan:
                if not nama.strip() or not no_hp.strip() or not alamat.strip():
                    st.error("Nama, nomor HP, dan alamat wajib diisi.")
                elif not no_hp.strip().isdigit() or not 10 <= len(no_hp.strip()) <= 14:
                    st.error("Nomor HP harus berupa angka dan terdiri dari 10 sampai 14 digit.")
                else:
                    try:
                        database.ubah_pelanggan(idx, nama, no_hp, alamat)
                        flash("✅ Data pelanggan berhasil diperbarui.")
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"❌ Gagal memperbarui: {pesan_database(e)}")

    # -------------------------------------------------------------- hapus
    with tab_hapus:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Hapus Pelanggan</div>',
            unsafe_allow_html=True,
        )
        st.warning("Pelanggan yang masih memiliki nota transaksi **tidak bisa dihapus** (aturan ON DELETE RESTRICT).")
        semua = database.daftar_pelanggan()
        if not semua:
            st.info("Belum ada pelanggan yang dapat dihapus.")
        else:
            peta_pel_hapus = {d["id_pelanggan"]: f'{d["nama_pelanggan"]} · {d["no_hp"]}' for d in semua}
            idx = st.selectbox("Pilih pelanggan", list(peta_pel_hapus), format_func=lambda i: peta_pel_hapus[i], key="hapus_pelanggan_pilih")
            info = database.pelanggan_ber_id(idx)
            st.caption(f"{info['nama_pelanggan']} — {info['no_hp']} — {info['alamat']}")
            yakin = st.checkbox("Ya, saya yakin ingin menghapus pelanggan ini")
            if st.button("🗑️ Hapus Pelanggan", type="primary"):
                if not yakin:
                    st.error("Centang kotak konfirmasi terlebih dahulu.")
                else:
                    try:
                        if database.hapus_pelanggan(idx):
                            flash("✅ Pelanggan berhasil dihapus.")
                            st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"❌ Gagal menghapus: {pesan_database(e)}")

    # ------------------------------------------------------------ riwayat
    with tab_riwayat:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Riwayat Transaksi Pelanggan</div>',
            unsafe_allow_html=True,
        )
        semua = database.daftar_pelanggan()
        if not semua:
            st.info("Belum ada pelanggan.")
        else:
            peta_pel_riwayat = {d["id_pelanggan"]: f'{d["nama_pelanggan"]} · {d["no_hp"]}' for d in semua}
            idx = st.selectbox("Pilih pelanggan", list(peta_pel_riwayat), format_func=lambda i: peta_pel_riwayat[i], key="riwayat_pelanggan_pilih")
            riwayat = database.riwayat_pelanggan(idx)
            if riwayat:
                df = pd.DataFrame(riwayat).rename(
                    columns={
                        "kode_nota": "Kode Nota",
                        "tanggal": "Tanggal",
                        "total": "Total",
                        "total_berat": "Total Berat (kg)",
                        "jumlah_item": "Jumlah Item",
                    }
                )
                df["Total"] = df["Total"].apply(rupiah)
                m1, m2, m3 = st.columns(3)
                m1.metric("Jumlah Nota", len(riwayat), border=True)
                m2.metric("Total Berat", f"{sum(r['total_berat'] for r in riwayat):g} kg", border=True)
                m3.metric("Total Belanja", rupiah(sum(r["total"] for r in riwayat)), border=True)
                st.markdown("")
                st.dataframe(
                    df[["Kode Nota", "Tanggal", "Jumlah Item", "Total Berat (kg)", "Total"]],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("Pelanggan ini belum memiliki transaksi.")


# ------------------------------------------------ HALAMAN KATEGORI & LAYANAN

def halaman_kategori_layanan() -> None:
    tampilkan_flash()
    st.markdown(
        """
        <div class="hero">
          <div class="hero-emoji">🧺</div>
          <div>
            <div class="hero-title">Kategori & Layanan</div>
            <div class="hero-desc">Master data jenis cucian beserta harga satuan per kilogram.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_kat, tab_lay = st.tabs(["🗂️ Kategori Cucian", "🏷️ Layanan & Harga"])

    # ------------------------------------------------------------ kategori
    with tab_kat:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Kategori Cucian</div>',
            unsafe_allow_html=True,
        )
        data = database.daftar_kategori()
        if data:
            df = pd.DataFrame(data).rename(
                columns={
                    "id_kategori": "ID",
                    "nama_kategori": "Nama Kategori",
                    "keterangan": "Keterangan",
                    "jumlah_layanan": "Jumlah Layanan",
                }
            )
            st.dataframe(
                df[["ID", "Nama Kategori", "Keterangan", "Jumlah Layanan"]],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("Belum ada kategori.")

        t_k1, t_k2, t_k3 = st.tabs(["➕ Tambah", "✏️ Ubah", "🗑️ Hapus"])

        with t_k1:
            with st.form("form_tambah_kategori", clear_on_submit=True, border=False):
                c1, c2 = st.columns(2)
                nama = c1.text_input("Nama Kategori *", placeholder="Contoh: Pakaian", key="tk_nama")
                ket = c2.text_input("Keterangan (opsional)", placeholder="Contoh: Cucian pakaian harian", key="tk_ket")
                st.markdown("")
                simpan = st.form_submit_button("💾 Simpan Kategori", type="primary")
            if simpan:
                if not nama.strip():
                    st.error("Nama kategori wajib diisi.")
                else:
                    try:
                        database.tambah_kategori(nama, ket)
                        flash(f"✅ Kategori **{nama.strip()}** berhasil disimpan.")
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"❌ Gagal menyimpan: {pesan_database(e)}")

        with t_k2:
            if not data:
                st.info("Belum ada kategori untuk diubah.")
            else:
                peta_kat_ubah = {d["id_kategori"]: d["nama_kategori"] for d in data}
                idx = st.selectbox("Pilih kategori", list(peta_kat_ubah), format_func=lambda i: peta_kat_ubah[i], key="ubah_kat_pilih")
                lama = database.kategori_ber_id(idx)
                with st.form("form_ubah_kategori", border=False):
                    c1, c2 = st.columns(2)
                    nama = c1.text_input("Nama Kategori *", value=lama["nama_kategori"], key=f"uk_nama_{idx}")
                    ket = c2.text_input("Keterangan", value=lama["keterangan"] or "", key=f"uk_ket_{idx}")
                    st.markdown("")
                    simpan = st.form_submit_button("💾 Simpan Perubahan", type="primary")
                if simpan:
                    if not nama.strip():
                        st.error("Nama kategori wajib diisi.")
                    else:
                        try:
                            database.ubah_kategori(idx, nama, ket)
                            flash("✅ Kategori berhasil diperbarui.")
                            st.rerun()
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Gagal memperbarui: {pesan_database(e)}")

        with t_k3:
            st.warning("Kategori yang masih memiliki layanan **tidak bisa dihapus** (ON DELETE RESTRICT).")
            if not data:
                st.info("Belum ada kategori untuk dihapus.")
            else:
                peta_kat_hapus = {d["id_kategori"]: d["nama_kategori"] for d in data}
                idx = st.selectbox("Pilih kategori", list(peta_kat_hapus), format_func=lambda i: peta_kat_hapus[i], key="hapus_kat_pilih")
                yakin = st.checkbox("Ya, saya yakin ingin menghapus kategori ini")
                if st.button("🗑️ Hapus Kategori", type="primary"):
                    if not yakin:
                        st.error("Centang kotak konfirmasi terlebih dahulu.")
                    else:
                        try:
                            if database.hapus_kategori(idx):
                                flash("✅ Kategori berhasil dihapus.")
                                st.rerun()
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Gagal menghapus: {pesan_database(e)}")

    # ------------------------------------------------------------ layanan
    with tab_lay:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Daftar Layanan & Harga</div>',
            unsafe_allow_html=True,
        )
        data = database.daftar_layanan()
        if data:
            df = pd.DataFrame(data).rename(
                columns={
                    "id_layanan": "ID",
                    "kode_layanan": "Kode",
                    "nama_layanan": "Nama Layanan",
                    "nama_kategori": "Kategori",
                    "satuan": "Satuan",
                    "tarif_per_kg": "Harga Satuan",
                    "aktif": "Status",
                }
            )
            df["Harga Satuan"] = df["Harga Satuan"].apply(rupiah)
            df["Status"] = df["Status"].map(lambda v: "🟢 Aktif" if v == 1 else "⚪ Nonaktif")
            st.dataframe(
                df[["ID", "Kode", "Nama Layanan", "Kategori", "Satuan", "Harga Satuan", "Status"]],
                hide_index=True,
                width="stretch",
            )
            st.caption("💡 Perubahan harga hanya berlaku untuk nota baru. Nota lama memakai harga saat nota dibuat.")
        else:
            st.info("Belum ada layanan.")

        kategori_tersedia = database.daftar_kategori()
        t_l1, t_l2, t_l3 = st.tabs(["➕ Tambah", "✏️ Ubah", "🗑️ Hapus / Nonaktifkan"])

        with t_l1:
            if not kategori_tersedia:
                st.info("Tambahkan kategori terlebih dahulu.")
            else:
                peta_kat_tambah = {d["id_kategori"]: d["nama_kategori"] for d in kategori_tersedia}
                with st.form("form_tambah_layanan", clear_on_submit=True, border=False):
                    c1, c2, c3 = st.columns(3)
                    kode = c1.text_input("Kode Layanan *", placeholder="LYN13-PAK", key="tl_kode")
                    nama = c2.text_input("Nama Layanan *", placeholder="Cuci Sepatu Reguler", key="tl_nama")
                    satuan = c3.selectbox(
                        "Satuan *", ["kg", "pcs"], index=0, key="tl_satuan",
                        help="Pilih kg (per kilogram) atau pcs (per satuan, mis. boneka/selimut/sprei).",
                    )
                    c4, c5 = st.columns([1, 2])
                    id_kat = c4.selectbox("Kategori *", list(peta_kat_tambah), format_func=lambda i: peta_kat_tambah[i], key="tl_kategori")
                    tarif = c5.number_input("Harga Satuan (Rp) *", min_value=0, step=500, value=7000, key="tl_tarif")
                    st.markdown("")
                    simpan = st.form_submit_button("💾 Simpan Layanan", type="primary")
                if simpan:
                    if not kode.strip() or not nama.strip() or not satuan.strip():
                        st.error("Kode, nama layanan, dan satuan wajib diisi.")
                    else:
                        try:
                            database.tambah_layanan(kode, nama, satuan, int(tarif), id_kat)
                            flash(f"✅ Layanan **{nama.strip()}** berhasil disimpan.")
                            st.rerun()
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Gagal menyimpan: {pesan_database(e)}")

        with t_l2:
            if not data:
                st.info("Belum ada layanan untuk diubah.")
            else:
                peta_lay_ubah = {d["id_layanan"]: f'{d["kode_layanan"]} · {d["nama_layanan"]} ({d["nama_kategori"]})' for d in data}
                idx = st.selectbox("Pilih layanan", list(peta_lay_ubah), format_func=lambda i: peta_lay_ubah[i], key="ubah_lay_pilih")
                lama = database.layanan_ber_id(idx)
                with st.form("form_ubah_layanan", border=False):
                    c1, c2, c3 = st.columns(3)
                    kode = c1.text_input("Kode Layanan *", value=lama["kode_layanan"], key=f"ul_kode_{idx}")
                    nama = c2.text_input("Nama Layanan *", value=lama["nama_layanan"], key=f"ul_nama_{idx}")
                    satuan = c3.selectbox(
                        "Satuan *", ["kg", "pcs"],
                        index=1 if lama["satuan"] == "pcs" else 0,
                        key=f"ul_satuan_{idx}",
                        help="Pilih kg (per kilogram) atau pcs (per satuan, mis. boneka/selimut/sprei).",
                    )
                    c4, c5 = st.columns([1, 2])
                    peta_kat_ubah_lay = {d["id_kategori"]: d["nama_kategori"] for d in kategori_tersedia}
                    id_kat = c4.selectbox(
                        "Kategori *", list(peta_kat_ubah_lay),
                        index=list(peta_kat_ubah_lay).index(lama["id_kategori"]) if lama["id_kategori"] in peta_kat_ubah_lay else 0,
                        format_func=lambda i: peta_kat_ubah_lay[i],
                        key=f"ul_kategori_{idx}",
                    )
                    tarif = c5.number_input("Harga Satuan (Rp) *", min_value=0, step=500, value=int(lama["tarif_per_kg"]), key=f"ul_tarif_{idx}")
                    st.markdown("")
                    simpan = st.form_submit_button("💾 Simpan Perubahan", type="primary")
                if simpan:
                    if not kode.strip() or not nama.strip() or not satuan.strip():
                        st.error("Kode, nama layanan, dan satuan wajib diisi.")
                    else:
                        try:
                            database.ubah_layanan(idx, kode, nama, satuan, int(tarif), id_kat)
                            flash("✅ Layanan berhasil diperbarui.")
                            st.rerun()
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Gagal memperbarui: {pesan_database(e)}")

        with t_l3:
            st.warning("Layanan yang sudah dipakai nota lama **tidak bisa dihapus**. Gunakan status **Nonaktif** untuk "
                       "menghentikan layanan tanpa merusak riwayat.")
            if not data:
                st.info("Belum ada layanan.")
            else:
                peta_lay_hapus = {d["id_layanan"]: f'{d["kode_layanan"]} · {d["nama_layanan"]} ({d["nama_kategori"]})' for d in data}
                idx = st.selectbox("Pilih layanan", list(peta_lay_hapus), format_func=lambda i: peta_lay_hapus[i], key="hapus_lay_pilih")
                info = database.layanan_ber_id(idx)
                c1, c2 = st.columns(2)
                status = c1.radio(
                    "Status layanan",
                    ["🟢 Aktif", "⚪ Nonaktif"],
                    index=0 if info["aktif"] == 1 else 1,
                    horizontal=True,
                    key=f"status_lay_{idx}",
                )
                yakin = c2.checkbox("Ya, saya yakin ingin menghapus layanan ini", key=f"yakin_lay_{idx}")
                if st.button("🗑️ Hapus Layanan", type="primary"):
                    if not yakin:
                        st.error("Centang kotak konfirmasi terlebih dahulu.")
                    else:
                        try:
                            if database.hapus_layanan(idx):
                                st.success("✅ Layanan berhasil dihapus.")
                                st.rerun()
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Gagal menghapus: {pesan_database(e)}")
                if st.button("💾 Simpan Status", width="stretch"):
                    baru = 1 if status.startswith("🟢") else 0
                    database.set_aktif_layanan(idx, bool(baru))
                    flash(f"✅ Status layanan diubah menjadi **{status}**.")
                    st.rerun()


# --------------------------------------------------------------------- KASIR

def tampilkan_nota(kode_nota: str) -> None:
    """Menampilkan struk nota lengkap beserta total yang dihitung dinamis."""
    info = database.info_nota(kode_nota)
    if not info:
        return
    rincian = database.rincian_nota(kode_nota)
    total = sum(r["subtotal"] for r in rincian)
    total_berat = sum(r["berat"] for r in rincian)

    baris = "".join(
        f"""
        <tr>
          <td style="padding:6px 10px 6px 0">{r['nama_kategori']}</td>
          <td style="padding:6px 10px 6px 0">{r['nama_layanan']}</td>
          <td style="padding:6px 10px 6px 0;text-align:right">{r['berat']:g} {r['satuan']}</td>
          <td style="padding:6px 10px 6px 0;text-align:right">{rupiah(r['harga_satuan'])}</td>
          <td style="padding:6px 0;text-align:right;font-weight:700">{rupiah(r['subtotal'])}</td>
        </tr>"""
        for r in rincian
    )

    st.markdown(
        f"""
        <div class="nota">
          <div class="nota-head">
            <div>
              <div class="nota-kode">🧾 NOTA {info['kode_nota']}</div>
              <div class="nota-meta">
                Tanggal &nbsp;: {info['tanggal']}<br>
                Pelanggan : {info['nama_pelanggan']} ({info['no_hp']})<br>
                Alamat &nbsp;&nbsp;&nbsp;: {info['alamat']}
              </div>
            </div>
            <div style="text-align:right">
              <div class="nota-total">{rupiah(total)}</div>
              <div class="nota-meta">{total_berat:g} kg · {len(rincian)} item</div>
            </div>
          </div>
          <table style="width:100%;border-collapse:collapse;font-size:.87rem;color:#0F172A">
            <thead>
              <tr style="text-align:left;color:#64748B;font-size:.76rem;text-transform:uppercase;letter-spacing:.04em">
                <th style="padding:4px 10px 8px 0">Kategori</th>
                <th style="padding:4px 10px 8px 0">Layanan</th>
                <th style="padding:4px 10px 8px 0;text-align:right">Berat</th>
                <th style="padding:4px 10px 8px 0;text-align:right">Harga/kg</th>
                <th style="padding:4px 0 8px 0;text-align:right">Subtotal</th>
              </tr>
            </thead>
            <tbody>{baris}</tbody>
          </table>
          <div class="nota-kaki">
            ULTRA LAUNDRY · Sistem Administrasi Transaksi ·<br>
            Simpan nota ini sebagai bukti pembayaran — terima kasih sudah laundry di Ultra Laundry! 🧺
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def halaman_kasir() -> None:
    tampilkan_flash()
    st.markdown(
        """
        <div class="hero">
          <div class="hero-emoji">🛒</div>
          <div>
            <div class="hero-title">Kasir — Transaksi Baru</div>
            <div class="hero-desc">Pilih pelanggan, pilih layanan, tentukan berat, lalu simpan nota.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "keranjang" not in st.session_state:
        bersihkan_keranjang()

    tab_kasir, tab_riwayat = st.tabs(["🛒 Nota Baru", "🧾 Riwayat Transaksi"])

    # -------------------------------------------------------------- kasir
    with tab_kasir:
        pelanggan = database.daftar_pelanggan()
        kategori = database.daftar_kategori()
        layanan = database.daftar_layanan_aktif()

        if not pelanggan:
            st.warning("⚠️ Belum ada pelanggan. Daftarkan pelanggan dulu di menu **Data Pelanggan**.")
            return
        if not kategori:
            st.warning("⚠️ Belum ada kategori. Tambahkan kategori dulu di menu **Kategori & Layanan**.")
            return
        if not layanan:
            st.warning("⚠️ Belum ada layanan aktif. Tambahkan layanan dulu di menu **Kategori & Layanan**.")
            return

        # -- Bagian 1: data nota
        st.markdown(
            '<div class="section-title"><span class="bar"></span>1️⃣ Data Nota</div>',
            unsafe_allow_html=True,
        )
        peta_pelanggan = {p["id_pelanggan"]: f'{p["nama_pelanggan"]} · {p["no_hp"]}' for p in pelanggan}
        p1, p2, p3 = st.columns([3, 2, 2])
        with p1:
            id_pelanggan = st.selectbox(
                "Pelanggan *", list(peta_pelanggan), format_func=lambda i: peta_pelanggan[i]
            )
        with p2:
            tanggal = st.date_input("Tanggal *", value=date.today())
        with p3:
            kode_nota = st.text_input("Kode Nota *", value=database.kode_nota_berikutnya())

        # -- Bagian 2: tambah cucian
        st.markdown(
            '<div class="section-title"><span class="bar"></span>2️⃣ Tambah Cucian ke Keranjang</div>',
            unsafe_allow_html=True,
        )
        peta_kategori = {k["id_kategori"]: k["nama_kategori"] for k in kategori}
        id_kategori = st.selectbox(
            "Kategori Cucian *", list(peta_kategori), format_func=lambda i: peta_kategori[i]
        )

        layanan_kategori = [l for l in layanan if l["id_kategori"] == id_kategori]
        if not layanan_kategori:
            st.warning(f"Tidak ada layanan aktif pada kategori **{peta_kategori[id_kategori]}**.")
        else:
            peta_layanan = {
                l["id_layanan"]: f'{l["nama_layanan"]} — {rupiah(l["tarif_per_kg"])}/{l["satuan"]}'
                for l in layanan_kategori
            }
            b1, b2, b3 = st.columns([3, 2, 1.6])
            meta_layanan = {l["id_layanan"]: l for l in layanan_kategori}
            with b1:
                id_layanan = st.selectbox(
                    "Layanan *",
                    list(peta_layanan),
                    format_func=lambda i: peta_layanan[i],
                    key=f"kasir_layanan_{id_kategori}",
                )
            with b2:
                berat = st.number_input(
                    "Berat (kg) *", min_value=0.0, step=0.5, value=1.0, format="%.1f"
                )
            with b3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                tambah = st.button("➕ Tambah", type="primary", width="stretch")

            if tambah:
                if berat <= 0:
                    st.error("❌ Berat harus lebih dari 0 kg.")
                else:
                    info_layanan = meta_layanan[id_layanan]
                    # Kombinasi kategori + layanan yang sama digabung beratnya.
                    for item in st.session_state.keranjang:
                        if item["id_layanan"] == id_layanan:
                            item["berat"] += float(berat)
                            st.info(
                                f"ℹ️ Berat layanan **{info_layanan['nama_layanan']}** digabung "
                                f"menjadi {item['berat']:g} kg."
                            )
                            break
                    else:
                        st.session_state.keranjang.append(
                            {
                                "id_layanan": id_layanan,
                                "nama_layanan": info_layanan["nama_layanan"],
                                "kategori": peta_kategori[id_kategori],
                                "satuan": info_layanan["satuan"],
                                "tarif": info_layanan["tarif_per_kg"],
                                "berat": float(berat),
                            }
                        )
                        st.success(
                            f"✅ **{info_layanan['nama_layanan']}** ({berat:g} kg) "
                            "ditambahkan ke keranjang."
                        )
                    st.rerun()

        # -- Bagian 3: keranjang
        st.markdown(
            '<div class="section-title"><span class="bar"></span>3️⃣ Keranjang Nota</div>',
            unsafe_allow_html=True,
        )
        keranjang = st.session_state.keranjang

        if not keranjang:
            st.info("🛒 Keranjang masih kosong. Tambahkan jenis cucian terlebih dahulu.")
        else:
            total = sum(i["berat"] * i["tarif"] for i in keranjang)
            total_berat = sum(i["berat"] for i in keranjang)

            df = pd.DataFrame(keranjang).rename(
                columns={
                    "kategori": "Kategori",
                    "nama_layanan": "Layanan",
                    "berat": "Berat (kg)",
                    "satuan": "Satuan",
                    "tarif": "Harga/kg",
                }
            )
            df["Berat (kg)"] = df["Berat (kg)"].astype(float)
            df["Harga/kg"] = df["Harga/kg"].apply(rupiah)
            df["Subtotal"] = [i["berat"] * i["tarif"] for i in keranjang]
            df["Subtotal"] = df["Subtotal"].apply(rupiah)

            st.dataframe(
                df[["Kategori", "Layanan", "Berat (kg)", "Harga/kg", "Subtotal"]],
                hide_index=True,
                width="stretch",
                column_config={"Berat (kg)": st.column_config.NumberColumn(format="%.1f")},
            )

            s1, s2, s3 = st.columns([1, 1, 2])
            with s1:
                st.metric("Total Berat", f"{total_berat:g} kg", border=True)
            with s2:
                st.metric("Jumlah Item", len(keranjang), border=True)
            with s3:
                st.markdown(
                    f"""
                    <div style="background:linear-gradient(120deg,#1D4ED8,#06B6D4);
                                border-radius:16px;padding:1.05rem 1.3rem;color:#fff;
                                display:flex;align-items:center;justify-content:space-between">
                      <div>
                        <div style="font-size:.76rem;letter-spacing:.06em;text-transform:uppercase;opacity:.85">
                          Total Tagihan</div>
                        <div style="font-size:1.05rem;font-weight:600">Berat × tarif saat nota dibuat</div>
                      </div>
                      <div style="font-size:1.85rem;font-weight:800">{rupiah(total)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("")
            a1, a2, a3 = st.columns([1, 1, 2])
            with a1:
                if st.button("🗑️ Kosongkan Keranjang", width="stretch"):
                    bersihkan_keranjang()
                    st.rerun()
            with a2:
                if st.button("❌ Hapus Item Terakhir", width="stretch"):
                    if st.session_state.keranjang:
                        st.session_state.keranjang.pop()
                    st.rerun()
            with a3:
                simpan = st.button("💾 SIMPAN NOTA", type="primary", width="stretch")

            if simpan:
                if not kode_nota.strip():
                    st.error("❌ Kode nota wajib diisi.")
                elif not st.session_state.keranjang:
                    st.error("❌ Nota wajib memuat minimal satu baris cucian.")
                else:
                    try:
                        database.simpan_transaksi(
                            kode_nota.strip().upper(),
                            tanggal.isoformat(),
                            id_pelanggan,
                            [
                                {"id_layanan": i["id_layanan"], "berat": i["berat"]}
                                for i in st.session_state.keranjang
                            ],
                        )
                        bersihkan_keranjang()
                        st.session_state.nota_baru = kode_nota.strip().upper()
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"❌ Gagal menyimpan nota: {pesan_database(e)}")
                    except ValueError as e:
                        st.error(f"❌ Gagal menyimpan nota: {e}")

    # -- notifikasi nota tersimpan (setelah rerun)
    nota_baru = st.session_state.pop("nota_baru", None)
    if nota_baru:
        st.success(f"✅ Nota **{nota_baru}** berhasil disimpan.")
        tampilkan_nota(nota_baru)
        st.download_button(
            "⬇️ Unduh Nota (TXT)",
            _nota_teks(nota_baru),
            file_name=f"nota_{nota_baru}.txt",
            mime="text/plain",
        )

    # ------------------------------------------------------------ riwayat
    with tab_riwayat:
        st.markdown(
            '<div class="section-title"><span class="bar"></span>Riwayat Semua Nota</div>',
            unsafe_allow_html=True,
        )
        cari = st.text_input("🔍 Cari nota (kode atau nama pelanggan)", key="cari_nota", placeholder="Ketik kode nota / nama ...")
        nota = database.daftar_nota(cari)
        if nota:
            df = pd.DataFrame(nota).rename(
                columns={
                    "id_transaksi": "ID",
                    "kode_nota": "Kode Nota",
                    "tanggal": "Tanggal",
                    "nama_pelanggan": "Pelanggan",
                    "no_hp": "No. HP",
                    "total": "Total",
                    "total_berat": "Total Berat (kg)",
                    "jumlah_item": "Item",
                }
            )
            df["Total"] = df["Total"].apply(rupiah)
            st.dataframe(
                df[["ID", "Kode Nota", "Tanggal", "Pelanggan", "No. HP", "Item", "Total Berat (kg)", "Total"]],
                hide_index=True,
                width="stretch",
            )
            pilihan = st.selectbox(
                "Lihat rincian nota",
                [n["kode_nota"] for n in nota],
                format_func=lambda k: f'{k} — {next(x["nama_pelanggan"] for x in nota if x["kode_nota"] == k)}',
            )
            tampilkan_nota(pilihan)
            st.download_button(
                "⬇️ Unduh riwayat transaksi (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                file_name="riwayat_transaksi.csv",
                mime="text/csv",
            )
        else:
            st.info("Belum ada transaksi yang cocok.")


def _nota_teks(kode_nota: str) -> str:
    """Mengubah struk nota menjadi teks biasa untuk diunduh."""
    info = database.info_nota(kode_nota)
    rincian = database.rincian_nota(kode_nota)
    total = sum(r["subtotal"] for r in rincian)
    garis = "=" * 58
    isi = [
        garis,
        "ULTRA LAUNDRY",
        "Sistem Administrasi Transaksi",
        garis,
        f"Kode Nota   : {info['kode_nota']}",
        f"Tanggal     : {info['tanggal']}",
        f"Pelanggan   : {info['nama_pelanggan']} ({info['no_hp']})",
        f"Alamat      : {info['alamat']}",
        garis,
        f"{'Kategori':<12}{'Layanan':<22}{'Berat':>8}{'Subtotal':>14}",
        "-" * 58,
    ]
    for r in rincian:
        isi.append(
            f"{r['nama_kategori']:<12}{r['nama_layanan']:<22}"
            f"{r['berat']:g} {r['satuan']:<4}{rupiah(r['subtotal']):>14}"
        )
    isi += [
        "-" * 58,
        f"{'TOTAL':<42}{rupiah(total):>14}",
        garis,
        "Terima kasih sudah laundry di Ultra Laundry!",
    ]
    return "\n".join(isi)


# ------------------------------------------------------------------- routing

def main() -> None:
    database.inisialisasi()
    menu = bangun_sidebar()

    if menu.startswith("🏠"):
        halaman_beranda()
    elif menu.startswith("👥"):
        halaman_pelanggan()
    elif menu.startswith("🧺"):
        halaman_kategori_layanan()
    else:
        halaman_kasir()


if __name__ == "__main__":
    main()
