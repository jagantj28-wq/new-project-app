@echo off
title FarmTwin Server
echo ====================================================
echo ?? Starting FarmTwin Digital Twin & Micro-Climate Simulator
echo ====================================================
cd /d "%~dp0"
start http://127.0.0.1:8000
.\.venv\Scripts\python.exe run.py
pause
