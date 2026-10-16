@echo off
rem API segura "endurecida": TLS (HTTPS) + rate limiting compartido en Redis, con DOS instancias.
rem  - Redis corre en un contenedor Docker (redis-demo, puerto 6379).
rem  - Dos instancias de la API (8443 y 8444) comparten el mismo contador: el limite vale para ambas.
rem  - Certificado autofirmado (el navegador avisara; es solo demo).
rem Sirve el champion de MLflow (como servir.bat): REQUIERE el stack de tp_integrador/stack arriba, y Docker para Redis.
rem Se puede usar junto a tp_integrador\servir.bat (puertos distintos).
cd /d "%~dp0..\.."
set PY=.venv\Scripts\python.exe

docker start redis-demo >nul 2>&1 || docker run -d --name redis-demo -p 6379:6379 redis:7-alpine >nul
if not exist tp_integrador\api_segura\certs\cert.pem %PY% tp_integrador\api_segura\generar_cert.py

start "REST SEGURO TLS+Redis  :8443" cmd /k "set REDIS_URL=redis://localhost:6379/0&& %PY% -m uvicorn tp_integrador.api_segura.api_segura:app --port 8443 --ssl-keyfile tp_integrador\api_segura\certs\key.pem --ssl-certfile tp_integrador\api_segura\certs\cert.pem"
start "REST SEGURO TLS+Redis  :8444" cmd /k "set REDIS_URL=redis://localhost:6379/0&& %PY% -m uvicorn tp_integrador.api_segura.api_segura:app --port 8444 --ssl-keyfile tp_integrador\api_segura\certs\key.pem --ssl-certfile tp_integrador\api_segura\certs\cert.pem"

echo.
echo Levantando dos instancias HTTPS con rate limit compartido en Redis:
echo   https://localhost:8443/docs   y   https://localhost:8444/docs   (aceptar la advertencia del certificado)
echo   Authorize: analista/analista123. Las consultas a CUALQUIERA de las dos cuentan en el mismo limite.
echo Para apagar: tp_integrador\parar.bat   (y "docker stop redis-demo" para Redis)
