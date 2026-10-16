@echo off
rem Levanta los servicios de las capas de los mini-TPs y los deja corriendo (una ventana por servicio).
rem Usa el Python del .venv directamente (no depende de "activate"). No modifica el codigo de los mini-TPs.
cd /d "%~dp0..\.."
set PY=.venv\Scripts\python.exe

if not exist common\artifacts\model.pkl (
  echo Generando artefactos del modelo...
  %PY% common\train_model.py
)

start "REST sin seguridad  :8001 (TP1)" cmd /k %PY% -m uvicorn mini_tps.tp1_rest.api:app --port 8001
start "REST SEGURO         :8007 (TP7)" cmd /k "set MODEL_SOURCE=local&& %PY% -m uvicorn tp_integrador.api_segura.api_segura:app --port 8007"
start "GraphQL             :8002 (TP2)" cmd /k %PY% -m uvicorn mini_tps.tp2_graphql.server:app --port 8002
start "gRPC                :50051 (TP3)" cmd /k %PY% mini_tps\tp3_grpc\server.py

echo.
echo Servicios levantandose (unos segundos). URLs:
echo   REST sin seguridad : http://localhost:8001/docs
echo   REST SEGURO        : http://localhost:8007/docs   (Authorize: analista/analista123)
echo   GraphQL (GraphiQL) : http://localhost:8002/graphql
echo   gRPC               : localhost:50051  (probar con mini_tps\servicios\probar_grpc.bat)
echo Para apagar todo: mini_tps\servicios\parar.bat
