@echo off
rem Cliente de prueba gRPC (unary + streaming) contra el servidor levantado por servir.bat.
cd /d "%~dp0..\.."
".venv\Scripts\python.exe" mini_tps\tp3_grpc\client.py
