@echo off
rem Lanza la demo con el Python del .venv, sin depender de "activate"
rem (si la carpeta se movio, activate apunta a una ruta vieja y "python" cae en Anaconda).
rem Uso:  mini_tps\demo_todos\demo.bat            (demo completa)
rem       mini_tps\demo_todos\demo.bat --rapido   (omite notebooks pesados)
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" mini_tps\demo_todos\run_demo.py %*
