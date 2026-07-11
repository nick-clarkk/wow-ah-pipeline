@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python ingest.py >> logs\ingest_log.txt 2>&1