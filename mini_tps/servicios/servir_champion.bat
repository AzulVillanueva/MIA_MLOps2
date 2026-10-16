@echo off
rem Levanta GraphQL (TP2) y gRPC (TP3) sirviendo el modelo CHAMPION de MLflow (una ventana por servicio).
rem REQUIERE el stack del integrador arriba (tp_integrador/stack: MLflow :5000, MinIO :9000) y el champion registrado.
rem Usa puertos distintos a servir.bat, asi pueden convivir ambos: 8012 y 50052.
rem Si MLflow no responde, cada servicio termina a los ~10 s con un mensaje claro.
cd /d "%~dp0..\.."
set PY=.venv\Scripts\python.exe

start "GraphQL champion     :8012" cmd /k %PY% -m uvicorn mini_tps.servicios.graphql_champion:app --port 8012
start "gRPC champion        :50052" cmd /k %PY% mini_tps\servicios\grpc_champion.py

echo.
echo Cargando el champion desde MLflow (unos segundos). URLs:
echo   GraphQL champion : http://localhost:8012/graphql
echo   gRPC champion    : localhost:50052  (probar con:  .venv\Scripts\python.exe mini_tps\servicios\probar_grpc_champion.py)
echo Para apagar: mini_tps\servicios\parar.bat
