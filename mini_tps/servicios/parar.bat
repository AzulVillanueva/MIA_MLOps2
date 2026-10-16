@echo off
rem Cierra los servicios de los mini-TPs: REST 8001, REST seguro 8007, GraphQL 8002 y 8012, gRPC 50051 y 50052.
for %%P in (8001 8007 8002 50051 8012 50052) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do taskkill /PID %%I /F >nul 2>&1
)
taskkill /FI "WINDOWTITLE eq REST sin seguridad*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq REST SEGURO         *" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq GraphQL*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq gRPC*" /F >nul 2>&1
echo Servicios de los mini-TPs detenidos.
