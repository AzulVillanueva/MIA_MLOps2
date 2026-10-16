@echo off
rem Cierra la API segura del integrador (8009) y las instancias endurecidas (8443, 8444).
for %%P in (8009 8443 8444) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do taskkill /PID %%I /F >nul 2>&1
)
taskkill /FI "WINDOWTITLE eq REST SEGURO champion*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq REST SEGURO TLS*" /F >nul 2>&1
echo Servicios del integrador detenidos.
