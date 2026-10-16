# Mini-TP 4 — Modelo sobre un flujo de eventos (Sesión 4)

Aplica el modelo de stroke (el mismo de `common/`) sobre un **flujo de eventos** en vez de pedidos sueltos: inferencia online por evento, métricas por ventana, detección de drift y alerta, y comparación contra scoring en batch.

## Entregable

**[`mini_tp4_resuelto.ipynb`](mini_tp4_resuelto.ipynb)** — corre de punta a punta sin Kafka: el flujo se simula con una `queue.Queue` y hilos productor/consumidor.

## Qué hace el notebook

1. **Modelo:** carga `common/artifacts/model.pkl` y `data_dict.json` (busca `common/` desde la raíz del repo o desde esta carpeta).
2. **Flujo:** 800 eventos tomados del dataset real; en la segunda mitad se aumentan edad y glucosa para introducir un cambio de distribución.
3. **Consumidor:** puntúa cada evento y calcula por ventana throughput (ev/s), latencia p95 y drift.
4. **Drift y alerta:** desplazamiento de la media de `age` respecto de la original, medido en desvíos estándar; alerta si supera el umbral (0.45).
5. **Streaming vs batch:** puntúa los mismos 800 eventos con `predict_batch` y compara tiempos, más una reflexión escrita.
6. **(Opcional)** instrucciones para reemplazar la cola por un topic de Kafka (Redpanda en Docker).

## Resultados (última corrida guardada en el notebook)

| Métrica | Valor |
|---|---|
| Eventos | 800 |
| Throughput por ventana | ≈ 700 ev/s |
| Latencia p95 por ventana | 19–24 ms |
| Latencia p95 global (800 eventos) | 24,3 ms (varía por corrida) |
| Drift de la edad (desvíos estándar) | de 0,02 a 0,32; umbral de alerta 0,45, no cruzado en esta corrida |
| Streaming vs batch | 18,5 ms por evento en streaming frente a 0,05 ms por evento en batch |

## Cómo correr

Requiere que existan los artefactos del modelo:

```bash
python common/train_model.py     # solo la primera vez
```

Luego abrir el notebook con el kernel del entorno (`mlops2`) y ejecutar todas las celdas. No requiere servicios externos.
