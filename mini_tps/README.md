# Mini-TPs

Ejercicios de *Operaciones de Aprendizaje Automático II* que exploraron alternativas para servir, entrenar y almacenar el mismo modelo de riesgo de ACV (accidente cerebrovascular). Todos usan el modelo y el preprocesamiento de [`common/`](../common/), así que sus resultados se pueden comparar. No forman parte del sistema productivo: de ellos, el TP integrador toma solo la API REST segura (TP1 + TP7) y el data lake (TP6). Ver [../tp_integrador/README.md](../tp_integrador/README.md).

## Los siete mini-TPs

| Mini-TP | Qué hace | Cómo correrlo | Detalle |
| --- | --- | --- | --- |
| TP1 — REST | API FastAPI con contrato Pydantic | `python -m uvicorn mini_tps.tp1_rest.api:app --port 8001` | [README](tp1_rest/README.md) |
| TP2 — GraphQL | Metadatos del modelo con esquema GraphQL (Strawberry) y comparación contra REST | `python -m uvicorn mini_tps.tp2_graphql.server:app --port 8002` | [README](tp2_graphql/README.md) |
| TP3 — gRPC | Contrato `.proto`, unary y server streaming, comparación de latencia | `python mini_tps/tp3_grpc/server.py` | [README](tp3_grpc/README.md) |
| TP4 — Streaming | Inferencia online sobre un flujo, métricas por ventana, drift y alerta | notebook | [README](tp4_streaming/README.md) |
| TP5 — Federado | FedAvg IID y non-IID frente al modelo centralizado | notebook | [README](tp5_federado/README.md) |
| TP6 — Data lake | Zonas y versión en MinIO, servir el modelo desde el lake | notebook (requiere MinIO) | [README](tp6_datalake/README.md) |
| TP7 — Seguridad | JWT con roles, validación, rate limiting, auditoría | notebook | [README](tp7_seguridad/README.md) |

> Los mini-TPs usan el modelo de `common/`, entrenado con el preprocesamiento original (SMOTE antes del split). Por eso sus métricas (F1 ≈ 0,97) no son comparables con las del champion del integrador, cuyo ETL separa el test antes de aplicar SMOTE (F1 0,11 sobre el test real). Ver "Límites conocidos" en el [README general](../README.md).

Todos los comandos se corren desde la raíz del repo, con el entorno de Python activo y `common/artifacts/` generado (`python common/train_model.py`).

## Levantarlos como servicios

Para explorarlos desde el navegador sin correr los notebooks:

```powershell
mini_tps\servicios\servir.bat        # una ventana por servicio
mini_tps\servicios\probar_grpc.bat   # cliente de prueba gRPC (unary + streaming)
mini_tps\servicios\parar.bat         # apaga todo
```

| Servicio | URL |
| --- | --- |
| REST sin seguridad (TP1) | http://localhost:8001/docs |
| REST seguro (TP7) | http://localhost:8007/docs (`analista/analista123`, `admin/admin123`, `invitado/invitado123`) |
| GraphQL (TP2) | http://localhost:8002/graphql |
| gRPC (TP3) | `localhost:50051` |

El REST seguro de este script corre con `MODEL_SOURCE=local`: usa el modelo de `common/`, sin necesidad del stack. Su código vive en [`tp_integrador/api_segura/`](../tp_integrador/api_segura/), porque es la misma API que se integra.

### Modo champion (GraphQL y gRPC)

`mini_tps\servicios\servir_champion.bat` levanta GraphQL y gRPC sirviendo el champion de MLflow en lugar del modelo local, en puertos distintos para que convivan con los de arriba.

> **Requiere el stack del integrador arriba** (`tp_integrador/stack`: MLflow en :5000 y MinIO en :9000) y el champion registrado. Si MLflow no responde, cada servicio termina a los ~10 segundos con un mensaje claro.

| Servicio | URL | Cliente de prueba |
| --- | --- | --- |
| GraphQL (champion) | http://localhost:8012/graphql | GraphiQL |
| gRPC (champion) | `localhost:50052` | `.venv\Scripts\python.exe mini_tps\servicios\probar_grpc_champion.py` |

Se reconocen porque `model_name` termina en `(champion MLflow)`. Un champion nuevo se ve al reiniciar esos servicios.

## Recorrido completo

```powershell
mini_tps\demo_todos\demo.bat            # todos los mini-TPs de punta a punta
mini_tps\demo_todos\demo.bat --rapido   # omite los notebooks pesados (TP4, TP5, TP6)
```

Termina con `Fin:`. El paso del data lake (TP6) necesita MinIO en `localhost:9000`; si no está, lo omite. Detalle en [demo_todos/README.md](demo_todos/README.md).
