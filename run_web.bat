@echo off
title AI Short-Form Video Studio (9:16)
echo ======================================================================
echo    Starting AI Short-Form Comparison Video Studio (9:16 Vertical)
echo ======================================================================
echo.
echo  [Local URL]     http://localhost:8501
echo  [Wi-Fi / LAN]   http://192.168.0.101:8501
echo.
echo  Press Ctrl+C to stop the server at any time.
echo ======================================================================
echo.
python -m streamlit run web_app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
pause
