@echo off
chcp 65001 > nul
echo ========================================
echo    RapFlow - Chinese Rap Lyrics Platform
echo ========================================
echo.
echo Starting Streamlit app...
python -m streamlit run app.py --server.port 8501 --server.headless true
pause
