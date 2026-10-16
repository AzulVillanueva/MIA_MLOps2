@echo off
rem Levanta la API REST segura (TP1 + TP7) sirviendo el modelo CHAMPION de MLflow, en el puerto 8009.
rem Requiere el stack Docker arriba (MLflow :5000, MinIO :9000) y el champion registrado.
cd /d "%~dp0.."
set PY=.venv\Scripts\python.exe

start "REST SEGURO champion :8009" cmd /k "set MODEL_SOURCE=mlflow&& %PY% -m uvicorn tp_integrador.api_segura.api_segura:app --port 8009"

echo.
echo Cargando el champion desde MLflow (unos segundos). URLs:
echo   Swagger : http://localhost:8009/docs
echo   Usuarios de demo (Authorize): analista/analista123  admin/admin123  invitado/invitado123
echo Para apagar: tp_integrador\parar.bat
