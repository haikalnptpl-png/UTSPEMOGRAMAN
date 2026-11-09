@echo off
REM ============================================================
REM  ULTRA LAUNDRY - Sistem Administrasi Transaksi
REM  Menjalankan aplikasi Streamlit
REM ============================================================
cd /d "%~dp0"

echo.
echo   ==============================================
echo     ULTRA LAUNDRY - Sistem Administrasi Transaksi
echo   ==============================================
echo.

if exist ".laundryvenv\Scripts\python.exe" (
    echo [1/2] Mengaktifkan virtual environment...
    call ".laundryvenv\Scripts\activate.bat"
    echo [2/2] Menjalankan Streamlit...
    echo.
    echo     Aplikasi akan terbuka di http://localhost:8501
    echo     Tekan Ctrl+C untuk menghentikan.
    echo.
    python -m streamlit run app.py
) else (
    echo [PERINGATAN] Virtual environment ".laundryvenv" tidak ditemukan!
    echo.
    echo Jalankan perintah berikut untuk membuatnya:
    echo     python -m venv .laundryvenv
    echo     .laundryvenv\Scripts\pip install streamlit
    echo.
    pause
)

endlocal
