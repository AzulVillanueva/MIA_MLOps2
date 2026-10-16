# Recorrido por todos los mini-TPs

Corre de punta a punta los siete mini-TPs sobre el mismo modelo de riesgo de ACV (accidente cerebrovascular), en local y sin Docker. No es el TP integrador: este recorrido sirve para ver las alternativas exploradas una detrás de otra. El TP integrador (stack con Airflow, MLflow y MinIO) está en [../../tp_integrador/](../../tp_integrador/README.md).

```
REST seguro (TP1 + TP7) → GraphQL (TP2) → gRPC (TP3) → Streaming (TP4) → Federado (TP5) → Data lake (TP6)
```

## Cómo correrlo

Desde la raíz del repo, con el entorno de Python activo (`pip install -r requirements.txt`):

```powershell
mini_tps\demo_todos\demo.bat            # recorrido completo (los notebooks de TP4 y TP5 tardan 1-3 minutos)
mini_tps\demo_todos\demo.bat --rapido   # omite la ejecución de notebooks y muestra los resultados guardados
```

O directamente: `python mini_tps/demo_todos/run_demo.py [--rapido]`. En Windows conviene `demo.bat`, que llama a `.venv\Scripts\python.exe` sin depender de `activate`.

Cada paso imprime un encabezado y el recorrido termina con `Fin:`. Si falta `common/artifacts/model.pkl`, lo genera. El paso del data lake (TP6) necesita MinIO en `localhost:9000` (ver el [README del TP6](../tp6_datalake/README.md)); si no está, lo informa y sigue.

## Qué corre en cada paso

| Paso | Mini-TP | Qué ejecuta |
| --- | --- | --- |
| 1 + 7 | REST seguro | notebook del TP7 (JWT, roles, validación, rate limit, auditoría) |
| 2 | GraphQL | levanta el servidor en :8002 y corre el cliente |
| 3 | gRPC | levanta el servidor en :50051 y corre el cliente (unary + streaming) |
| 4 | Streaming | notebook del TP4 |
| 5 | Federado | notebook del TP5 |
| 6 | Data lake | notebook del TP6 (si hay MinIO) |
